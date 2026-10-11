#!/usr/bin/env python3
"""Ap dung cai tien hau ky len predictions_*.jsonl da co (khong goi LLM).

  --fix          CT5 schema-guard: sua SQL loi theo schema that -> predictions_<m>_fix.jsonl
  --vote TEN=m1,m2,...   CT7 bo phieu theo ket qua thuc thi giua cac cau hinh -> predictions_TEN.jsonl
  --feedback m   CT8: cau van loi sau CT5 -> goi LLM 1 lan voi thong bao loi + cot chinh xac, roi CT5 lai
                 -> predictions_<m>_fb.jsonl (can Ollama, model lay tu config.json)
Vi du:
  python improve.py results/q08_500 --data minidev/MINIDEV/mini_dev_sqlite.json --db-root minidev/MINIDEV/dev_databases --fix
  python improve.py results/q08_500 ... --vote mrv=base_fix,auto_det_fix,hybrid_ret_fix
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import run_experiment as R
from vsql import report
from vsql import views as V
from vsql.db import run_sql, tables_in_sql
from vsql.llm import OllamaLLM, extract_sql

P_FIX = """You are a SQLite expert. The SQLite query below fails with an error. Fix it.

### Tables (use ONLY these exact table and column names; quote names with spaces or dashes using backticks)
{ddl}

### Question
{question}
{evidence}
### Failing query
{sql}

### Error
{err}

Write ONE corrected SQLite query (SQLite syntax: use strftime for dates, no YEAR()/MONTH()). Return only the SQL inside a ```sql code block."""
from vsql.pipeline import METHODS, DbCtx, score
from vsql.repair import repair


def load(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def resolver(ctx, method):
    """columns_of + danh sach ten hop le + tien to de bo, theo nguon view cua cau hinh."""
    src = METHODS.get(method, {}).get("views")
    vs = ctx.views.get(src, []) if src else []
    tabs = {t.lower(): [c.name for c in ctx.schema.tables[t].columns] for t in ctx.schema.tables}
    vcols = {v.name.lower(): [c.name for c in v.cols] for v in vs}

    def columns_of(name):
        n = name.lower()
        return vcols.get(n) or tabs.get(n)

    prefixes = sorted({j.alias for v in vs for j in v.joins} | set(ctx.schema.tables), key=len, reverse=True)
    return columns_of, list(ctx.schema.tables) + [v.name for v in vs], prefixes, fk_joiner(ctx.schema)


def fk_joiner(schema):
    """CT5b: tim bang T (khong co trong FROM) chua cot c, noi 1 buoc theo khoa ngoai voi mot bang trong FROM.
    Uu tien chieu N-1 (bang trong FROM tro toi T: khong nhan ban dong), sau do 1-N."""
    tabs = schema.tables

    def joiner(c, sc):
        present = {e[0].lower() for e in sc}
        for prefer_n1 in (True, False):
            for name, alias, _cols in sc:
                t = next((x for x in tabs if x.lower() == name.lower()), None)
                if not t:
                    continue
                ref = alias or name
                cands = []
                if prefer_n1:
                    cands = [(fk.ref_table, list(zip(fk.cols, fk.ref_cols))) for fk in tabs[t].fks]
                else:
                    cands = [(o, list(zip(fk.ref_cols, fk.cols))) for o in tabs for fk in tabs[o].fks if fk.ref_table == t]
                for other, pairs in cands:
                    if other.lower() in present:
                        continue
                    col = next((x.name for x in tabs[other].columns if x.name.lower() == c.lower()), None)
                    if col:
                        on = " AND ".join(f"{_qi(ref)}.{_qi(a)} = {{a}}.{_qi(b)}" for a, b in pairs)
                        return other, col, on
        return None
    return joiner


def _qi(n):
    import re as _re
    return n if _re.fullmatch(r"[A-Za-z_]\w*", n) else f"`{n}`"


def main():
    a = argparse.ArgumentParser()
    a.add_argument("out")
    a.add_argument("--data", required=True)
    a.add_argument("--db-root", required=True)
    a.add_argument("--methods", default="", help="mac dinh: moi cau hinh co trong thu muc (tru *_fix)")
    a.add_argument("--fix", action="store_true")
    a.add_argument("--vote", action="append", default=[])
    a.add_argument("--feedback", action="append", default=[])
    a.add_argument("--timeout", type=float, default=30.0)
    args = a.parse_args()
    out = Path(args.out)
    cfg = R.parse_args(["--data", args.data, "--db-root", args.db_root])
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    by_db = defaultdict(list)
    for it in data:
        by_db[it["db_id"]].append(it)
    ctxs = {}

    def ctx(db):
        if db not in ctxs:
            ctxs[db] = DbCtx(db, Path(args.db_root) / db / f"{db}.sqlite", [x["SQL"] for x in by_db[db]], cfg)
        return ctxs[db]

    gold_sql = {it["question_id"]: it["SQL"] for it in data}
    gold = {}

    def gold_of(q, c):
        if q not in gold:
            rows, err, sec = run_sql(c.schema.path, gold_sql[q], args.timeout * 4)
            gold[q] = (rows, sec)
        return gold[q]

    present = sorted(p.stem[len("predictions_"):] for p in out.glob("predictions_*.jsonl"))
    methods = args.methods.split(",") if args.methods else [m for m in present if not m.endswith("_fix") and m in METHODS]

    if args.fix:
        for m in methods:
            dst = out / f"predictions_{m}_fix.jsonl"
            done = {r["qid"] for r in load(dst)} if dst.exists() else set()
            n = fixed = 0
            with open(dst, "a", encoding="utf-8") as f:
                for r in load(out / f"predictions_{m}.jsonl"):
                    if r["qid"] in done:
                        continue
                    c = ctx(r["db_id"])
                    cols, names, pre, jn = resolver(c, m)
                    meta = METHODS.get(m, {})
                    if meta.get("stage2") == "det" and r.get("dummy_sql"):
                        # sua tren dummy SQL (ten view), mo rong CTE moi lan chay -> khong mat cot bi cat
                        vs = c.views[meta["views"]]
                        render = lambda s, vs=vs: V.unfold(s, vs, prune=True)[0]
                        dummy, steps = repair(r["dummy_sql"], c.schema.path, cols, names, pre, timeout=args.timeout,
                                              render=render, joiner=jn)
                        new = render(dummy) if steps else r["final_sql"]
                    elif meta.get("stage2") == "llm" and meta.get("views"):
                        # LLM tai tao chua bo het view (mo hinh nho hay de lai v_...): mo rong view con sot thanh CTE
                        vs = c.views[meta["views"]]
                        render = lambda s, vs=vs: V.unfold(s, vs, prune=False)[0]
                        fx, steps = repair(r["final_sql"], c.schema.path, cols, names, pre, timeout=args.timeout,
                                           render=render, joiner=jn)
                        new = render(fx) if fx else fx
                    else:
                        new, steps = repair(r["final_sql"], c.schema.path, cols, names, pre, timeout=args.timeout, joiner=jn)
                    rec = dict(r, method=f"{m}_fix", final_sql=new, repair_steps=steps)
                    rec = score(rec, *gold_of(r["qid"], c), c.schema.path, args.timeout)
                    f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
                    n, fixed = n + 1, fixed + bool(steps)
            print(f"[fix] {m}: {n} cau, sua {fixed}")

    if args.feedback:
        conf = json.loads((out / "config.json").read_text())
        llm = OllamaLLM(conf["model"], conf.get("host", "http://localhost:11434"), str(out / "llm_cache.sqlite"),
                        conf.get("num_ctx", 16384), conf.get("num_predict", 800), conf.get("think", False))
        items = {it["question_id"]: it for it in data}
    for m in args.feedback:
        src = load(out / f"predictions_{m}.jsonl")
        base_m = m[:-4] if m.endswith("_fix") else m
        dst = out / f"predictions_{m}_fb.jsonl"
        n = called = 0
        with open(dst, "w", encoding="utf-8") as f:
            for r in src:
                c = ctx(r["db_id"])
                rec = dict(r, method=f"{m}_fb")
                if r.get("error"):
                    it = items[r["qid"]]
                    tabs = sorted(tables_in_sql(r["final_sql"] or "", c.schema)) or list(c.schema.tables)
                    ev = f"\n### External knowledge\n{it['evidence']}\n" if it.get("evidence") else ""
                    prompt = P_FIX.format(ddl="\n\n".join(c.schema.table_ddl(t, c.n_samples) for t in tabs),
                                          question=it["question"], evidence=ev, sql=r["final_sql"], err=r["error"])
                    resp = llm.chat(prompt)
                    called += 1
                    cols, names, pre, jn = resolver(c, "base")
                    new, steps = repair(extract_sql(resp["text"]), c.schema.path, cols, names, pre, timeout=args.timeout,
                                        joiner=jn)
                    rec.update(final_sql=new, feedback=True, repair_steps=(r.get("repair_steps") or []) + steps,
                               calls=r["calls"] + 1, prompt_tokens=r["prompt_tokens"] + resp["prompt_tokens"],
                               completion_tokens=r["completion_tokens"] + resp["completion_tokens"],
                               llm_seconds=r["llm_seconds"] + resp["seconds"])
                rec = score(rec, *gold_of(r["qid"], c), c.schema.path, args.timeout)
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
                n += 1
        print(f"[feedback] {m}: {n} cau, goi LLM {called}")

    for spec in args.vote:
        name, srcs = spec.split("=", 1)
        srcs = srcs.split(",")
        preds = {s: {r["qid"]: r for r in load(out / f"predictions_{s}.jsonl")} for s in srcs}
        qids = set.intersection(*[set(p) for p in preds.values()])
        chosen = Counter()
        with open(out / f"predictions_{name}.jsonl", "w", encoding="utf-8") as f:
            for q in sorted(qids, key=str):
                c = ctx(preds[srcs[0]][q]["db_id"])
                votes, first_ok = Counter(), None
                keyed = {}
                for s in srcs:
                    sql = preds[s][q]["final_sql"]
                    rows, err, _ = run_sql(c.schema.path, sql, args.timeout) if sql else (None, "empty", 0)
                    if err is None and first_ok is None:
                        first_ok = s
                    if err is None and rows:
                        k = frozenset(rows)
                        votes[k] += 1
                        keyed.setdefault(k, s)            # nguon uu tien dau tien cho moi ket qua
                if votes:
                    top = max(votes.values())
                    pick = next(keyed[k] for k in sorted(keyed, key=lambda k: srcs.index(keyed[k])) if votes[k] == top)
                else:
                    pick = first_ok or srcs[0]
                chosen[pick] += 1
                base = preds[pick][q]
                rec = dict(base, method=name, voted_from=pick,
                           calls=sum(preds[s][q]["calls"] for s in srcs),
                           prompt_tokens=sum(preds[s][q]["prompt_tokens"] for s in srcs),
                           completion_tokens=sum(preds[s][q]["completion_tokens"] for s in srcs),
                           llm_seconds=sum(preds[s][q]["llm_seconds"] for s in srcs))
                rec = score(rec, *gold_of(q, c), c.schema.path, args.timeout)
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        print(f"[vote] {name}: {dict(chosen)}")


if __name__ == "__main__":
    main()
