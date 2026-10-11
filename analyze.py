#!/usr/bin/env python3
"""Phan tich bo sung sau run_experiment.py: EX theo DB, theo so JOIN cua dap an, va loi o giai doan tai tao.

  python analyze.py results/q8 --data minidev/MINIDEV/mini_dev_sqlite.json
Ghi results/q8/analysis.md
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from vsql import report


def main():
    a = argparse.ArgumentParser()
    a.add_argument("out")
    a.add_argument("--data", required=True)
    args = a.parse_args()
    out = Path(args.out)
    res = report.load(out)
    qids = sorted(set.intersection(*[set(r) for r in res.values()]), key=str)
    data = {it.get("question_id", i): it for i, it in enumerate(json.loads(Path(args.data).read_text(encoding="utf-8")))}
    njoin = {q: len(re.findall(r"\bjoin\b", data[q]["SQL"], re.I)) for q in qids}
    ms = list(res)
    md = [f"# Phan tich bo sung ({len(qids)} cau)\n"]

    # EX theo DB
    dbs = sorted({res[ms[0]][q]["db_id"] for q in qids})
    md += ["## EX (%) theo database\n", "| DB | n | " + " | ".join(f"`{m}`" for m in ms) + " |", "|---|---|" + "---|" * len(ms)]
    for db in dbs:
        qs = [q for q in qids if res[ms[0]][q]["db_id"] == db]
        md.append(f"| {db} | {len(qs)} | " + " | ".join(
            f"{100 * sum(res[m][q]['correct'] for q in qs) / len(qs):.1f}" for m in ms) + " |")

    # EX theo so JOIN
    groups = defaultdict(list)
    for q in qids:
        groups[min(njoin[q], 3)].append(q)
    md += ["\n## EX (%) theo so JOIN trong SQL dap an\n", "| So JOIN | n | " + " | ".join(f"`{m}`" for m in ms) + " |",
           "|---|---|" + "---|" * len(ms)]
    for k in sorted(groups):
        qs = groups[k]
        md.append(f"| {k if k < 3 else '>=3'} | {len(qs)} | " + " | ".join(
            f"{100 * sum(res[m][q]['correct'] for q in qs) / len(qs):.1f}" for m in ms) + " |")

    # giai doan 2: LLM tai tao vs tat dinh (cung dummy SQL)
    md.append("\n## Giai doan 2: LLM tai tao so voi viet lai tat dinh (cung dummy SQL)\n")
    for llm_m, det_m in [("vsql", "vsql_det"), ("auto_llm", "auto_det")]:
        if llm_m not in res or det_m not in res:
            continue
        same = [q for q in qids if (res[llm_m][q]["dummy_sql"] or "") == (res[det_m][q]["dummy_sql"] or "")]
        only_llm = [q for q in same if res[llm_m][q]["correct"] and not res[det_m][q]["correct"]]
        only_det = [q for q in same if res[det_m][q]["correct"] and not res[llm_m][q]["correct"]]
        no_view = sum(1 for q in same if not res[det_m][q]["views_used"])
        err_llm = Counter(res[llm_m][q]["outcome"] for q in only_det)
        err_det = Counter(res[det_m][q]["outcome"] for q in only_llm)
        md += [f"### `{llm_m}` vs `{det_m}`\n",
               f"- Cau co cung dummy SQL: {len(same)}/{len(qids)}; trong do dummy SQL khong dung view nao: {no_view}",
               f"- Chi `{det_m}` dung: {len(only_det)} (loi cua `{llm_m}`: {dict(err_llm)})",
               f"- Chi `{llm_m}` dung: {len(only_llm)} (loi cua `{det_m}`: {dict(err_det)})",
               f"- Ty le cau goi LLM lan 2 o `{llm_m}`: "
               f"{100 * sum(res[llm_m][q]['calls'] > 1 for q in qids) / len(qids):.1f}%\n"]

    # ao giac schema theo cau hinh (so cau)
    hall = ("schema_column", "schema_table", "ambiguous_column")
    md += ["## So cau ao giac schema\n", "| Cau hinh | no such column | no such table | ambiguous | Tong |", "|---|---|---|---|---|"]
    for m in ms:
        c = Counter(res[m][q]["outcome"] for q in qids)
        md.append(f"| `{m}` | {c['schema_column']} | {c['schema_table']} | {c['ambiguous_column']} | {sum(c[h] for h in hall)} |")

    # oracle: tap cau dung chung / hop
    md.append("\n## Bo sung tu cac cau hinh (oracle union)\n")
    union = sum(any(res[m][q]["correct"] for m in ms) for q in qids)
    md.append(f"- Ty le cau co it nhat mot cau hinh dung: {100 * union / len(qids):.1f}%")
    allc = sum(all(res[m][q]["correct"] for m in ms) for q in qids)
    md.append(f"- Ty le cau moi cau hinh deu dung: {100 * allc / len(qids):.1f}%")

    (out / "analysis.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
