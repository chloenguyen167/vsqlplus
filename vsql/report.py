"""Tong hop metric tu predictions_*.jsonl: EX + CI bootstrap, McNemar ghep cap, phan loai loi, chi phi."""
import csv
import json
import math
import random
from pathlib import Path

from .pipeline import METHODS

DIFFS = ["simple", "moderate", "challenging"]
OUTCOMES = ["schema_column", "schema_table", "ambiguous_column", "syntax", "no_sql", "timeout", "other_exec",
            "wrong_empty", "wrong_result"]


def load(out_dir):
    res = {}
    for m in METHODS:
        p = Path(out_dir) / f"predictions_{m}.jsonl"
        if p.exists():
            rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
            if rows:
                res[m] = {r["qid"]: r for r in rows}
    return res


def boot_ci(vals, n=2000, seed=0):
    """Khoang tin cay 95% bootstrap cua trung binh."""
    if not vals:
        return (float("nan"),) * 2
    rnd, k = random.Random(seed), len(vals)
    means = sorted(sum(rnd.choices(vals, k=k)) / k for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def mcnemar(b, c):
    """McNemar chinh xac (nhi thuc hai phia). b: chi A dung; c: chi B dung."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def _pct(x):
    return "-" if x != x else f"{100 * x:.1f}"


def build(out_dir, ref="vsql"):
    out_dir = Path(out_dir)
    res = load(out_dir)
    if not res:
        raise SystemExit("Khong co file predictions_*.jsonl")
    common = set.intersection(*[set(r) for r in res.values()])
    qids = sorted(common, key=str)
    md = [f"# Ket qua thuc nghiem V-SQL\n\nSo cau hoi chung cho moi cau hinh: **{len(qids)}**"
          + ("" if all(len(r) == len(qids) for r in res.values()) else
             "  (CANH BAO: cac cau hinh co so cau khac nhau; chi tinh tren phan giao)") + "\n"]
    rows_csv = []

    # ---- 1. EX
    md += ["## 1. Execution Accuracy (EX, %)\n",
           "| Cau hinh | Mo ta | Simple | Moderate | Challenging | Tong | CI 95% |", "|---|---|---|---|---|---|---|"]
    for m, r in res.items():
        ok = [int(r[q]["correct"]) for q in qids]
        by = {d: [int(r[q]["correct"]) for q in qids if r[q]["difficulty"] == d] for d in DIFFS}
        lo, hi = boot_ci(ok)
        cells = [f"{_pct(sum(v) / len(v)) if v else '-'} (n={len(v)})" for v in by.values()]
        md.append(f"| `{m}` | {METHODS[m]['note']} | " + " | ".join(cells)
                  + f" | **{_pct(sum(ok) / len(ok))}** | [{_pct(lo)}, {_pct(hi)}] |")
        rows_csv.append(dict(method=m, n=len(ok), ex=100 * sum(ok) / len(ok), ci_lo=100 * lo, ci_hi=100 * hi,
                             **{f"ex_{d}": (100 * sum(v) / len(v) if v else "") for d, v in by.items()}))

    # ---- 2. so sanh ghep cap
    if ref in res:
        md += [f"\n## 2. So sanh ghep cap voi `{ref}` (phuong phap cua paper)\n",
               "| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar |",
               "|---|---|---|---|---|---|"]
        for m, r in res.items():
            if m == ref:
                continue
            d = [int(r[q]["correct"]) - int(res[ref][q]["correct"]) for q in qids]
            b, c = d.count(-1), d.count(1)
            lo, hi = boot_ci(d)
            p = mcnemar(b, c)
            md.append(f"| `{m}` | {100 * sum(d) / len(d):+.1f} | [{100 * lo:+.1f}, {100 * hi:+.1f}] | {b} | {c} | {p:.3f} |")
            next(x for x in rows_csv if x["method"] == m).update(
                delta_vs_ref=100 * sum(d) / len(d), delta_lo=100 * lo, delta_hi=100 * hi, only_ref=b, only_this=c, mcnemar_p=p)
        md.append("\np < 0.05 moi coi la khac biet co y nghia thong ke; CI chua 0 nghia la chua ket luan duoc.")

    # ---- 3. loi
    md += ["\n## 3. Phan loai ket qua sai (% tren tong so cau)\n",
           "`schema_column` + `schema_table` + `ambiguous_column` = ao giac schema (dieu paper muon giam).\n",
           "| Cau hinh | " + " | ".join(OUTCOMES) + " | **Ao giac schema** |", "|---|" + "---|" * (len(OUTCOMES) + 1)]
    for m, r in res.items():
        cnt = {o: sum(1 for q in qids if r[q]["outcome"] == o) for o in OUTCOMES}
        hall = cnt["schema_column"] + cnt["schema_table"] + cnt["ambiguous_column"]
        md.append(f"| `{m}` | " + " | ".join(_pct(cnt[o] / len(qids)) for o in OUTCOMES)
                  + f" | **{_pct(hall / len(qids))}** |")
        next(x for x in rows_csv if x["method"] == m).update(
            schema_hallucination=100 * hall / len(qids), **{f"err_{o}": cnt[o] for o in OUTCOMES})

    # ---- 4. chi phi
    md += ["\n## 4. Chi phi (trung binh moi cau)\n",
           "| Cau hinh | So lan goi LLM | Token vao | Token ra | Giay LLM | So doi tuong schema | Do phu bang dap an | VES xap xi |",
           "|---|---|---|---|---|---|---|---|"]
    for m, r in res.items():
        avg = lambda k: sum(r[q][k] for q in qids) / len(qids)
        ves = sum(100 * math.sqrt(max(r[q]["gold_seconds"], 1e-4) / max(r[q]["exec_seconds"], 1e-4))
                  for q in qids if r[q]["correct"]) / len(qids)
        full = sum(1 for q in qids if r[q]["coverage"] == 1.0) / len(qids)
        md.append(f"| `{m}` | {avg('calls'):.2f} | {avg('prompt_tokens'):.0f} | {avg('completion_tokens'):.0f} | "
                  f"{avg('llm_seconds'):.1f} | {avg('n_objects'):.1f} | {_pct(full)} | {ves:.1f} |")
        next(x for x in rows_csv if x["method"] == m).update(
            calls=avg("calls"), prompt_tokens=avg("prompt_tokens"), completion_tokens=avg("completion_tokens"),
            llm_seconds=avg("llm_seconds"), n_objects=avg("n_objects"), full_coverage=100 * full, ves_approx=ves)
    md.append("\n- *Do phu bang dap an*: ti le cau ma moi bang trong SQL dap an deu nam trong schema dua cho LLM "
              "(< 100% o `hybrid_ret` la loi cua buoc truy xuat).\n- *VES xap xi*: sqrt(t_dap_an / t_du_doan) "
              "tren cau dung, do 1 lan chay nen chi mang tinh tham khao.")

    # ---- 5. doc ablation
    def ex(m):
        return 100 * sum(int(res[m][q]["correct"]) for q in qids) / len(qids) if m in res else None
    pairs = [("CT1 viet lai tat dinh (cung view, cung dummy SQL)", "vsql_det", "vsql"),
             ("CT2 view tu dong thay view theo dap an (cung LLM tai tao)", "auto_llm", "vsql"),
             ("CT1 tren view tu dong", "auto_det", "auto_llm"),
             ("CT3 schema lai (them bang goc)", "hybrid", "auto_det"),
             ("CT4 truy xuat top-k", "hybrid_ret", "hybrid"),
             ("Dong gop cua view so voi baseline 1 giai doan", "vsql", "base")]
    md += ["\n## 5. Dong gop rieng cua tung cai tien\n", "| Yeu to | So sanh | dEX |", "|---|---|---|"]
    for name, a, b in pairs:
        if ex(a) is not None and ex(b) is not None:
            md.append(f"| {name} | `{a}` - `{b}` | {ex(a) - ex(b):+.1f} |")

    vs = out_dir / "views_stats.json"
    if vs.exists():
        st = json.loads(vs.read_text())
        md += ["\n## 6. Thong ke view\n", "| DB | Bang | FK | View oracle (trong do co nhan ban dong) | View auto | View auto giu nguyen so dong |",
               "|---|---|---|---|---|---|"]
        for db, s in st.items():
            md.append(f"| {db} | {s['tables']} | {s['fks']} | {s['oracle']} ({s['oracle_fan']}) | {s['auto']} | {s['auto_rows_equal']} |")

    (out_dir / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    keys = []
    for r in rows_csv:
        keys += [k for k in r if k not in keys]
    with open(out_dir / "summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(rows_csv)
    return "\n".join(md)
