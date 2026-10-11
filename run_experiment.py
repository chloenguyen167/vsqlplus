#!/usr/bin/env python3
"""Chay thuc nghiem V-SQL + cac cai tien tren BIRD mini-dev voi qwen3 (Ollama). Chi dung thu vien chuan.

Vi du:
  python run_experiment.py --data minidev/MINIDEV/mini_dev_sqlite.json \
      --db-root minidev/MINIDEV/dev_databases --model qwen3:8b --out results/qwen3_8b
"""
import argparse
import json
import threading
import time
from collections import defaultdict
from pathlib import Path

from vsql import report
from vsql.db import run_sql, tables_in_sql
from vsql.llm import OllamaLLM
from vsql.pipeline import METHODS, DbCtx, run_item, score


def parse_args(argv=None):
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--data", required=True, help="mini_dev_sqlite.json")
    a.add_argument("--db-root", required=True, help="thu muc dev_databases")
    a.add_argument("--out", default="results/run")
    a.add_argument("--methods", default="all", help="all hoac danh sach: " + ",".join(METHODS))
    a.add_argument("--model", default="qwen3:8b")
    a.add_argument("--host", default="http://localhost:11434")
    a.add_argument("--num-ctx", type=int, default=16384)
    a.add_argument("--num-predict", type=int, default=800, help="paper: 800")
    a.add_argument("--think", action="store_true", help="bat che do suy luan cua qwen3 (mac dinh tat)")
    a.add_argument("--limit", type=int, default=0, help="chi chay N cau dau (thu nhanh)")
    a.add_argument("--sample", type=int, default=0, help="lay mau phan tang N cau theo (db, do kho), co dinh theo --seed")
    a.add_argument("--seed", type=int, default=0)
    a.add_argument("--qids", default="", help="file JSON danh sach question_id can chay")
    a.add_argument("--db", default="", help="chi chay cac db_id nay (phan cach dau phay)")
    a.add_argument("--no-evidence", dest="evidence", action="store_false", help="khong dua evidence cua BIRD vao prompt")
    a.add_argument("--samples", type=int, default=3, help="so gia tri mau moi cot trong prompt")
    a.add_argument("--depth", type=int, default=2, help="do sau noi FK khi sinh view tu dong")
    a.add_argument("--max-cols", type=int, default=60, help="so cot toi da cua mot view tu dong")
    a.add_argument("--infer-fk", action="store_true", help="suy them FK theo ten cot cho DB thieu khai bao")
    a.add_argument("--oracle-max-fan", type=int, default=3)
    a.add_argument("--views-dir", default="views_manual", help="view viet tay <db_id>.sql (thay cho view oracle)")
    a.add_argument("--topk", type=int, default=5, help="so view/bang giu lai o hybrid_ret")
    a.add_argument("--retriever", default="bm25", choices=["bm25", "embed", "hybrid"])
    a.add_argument("--embed-model", default="nomic-embed-text")
    a.add_argument("--no-prune", action="store_true", help="khong cat cac JOIN thua khi viet lai tat dinh")
    a.add_argument("--timeout", type=float, default=30.0)
    a.add_argument("--workers", type=int, default=1, help="so luong goi Ollama song song (can OLLAMA_NUM_PARALLEL >= workers)")
    a.add_argument("--no-prefetch", action="store_true", help="goi LLM tuan tu theo tung cau (cham hon, khong dung lai cache tien to)")
    a.add_argument("--views-only", action="store_true", help="chi sinh + kiem tra view, khong goi LLM")
    a.add_argument("--retrieval-sweep", action="store_true", help="do do phu truy xuat theo k, khong goi LLM")
    return a.parse_args(argv)


def stratified_sample(data, n, seed=0):
    """Lay mau giu ti le (db_id, difficulty) cua tap goc; tra ve theo thu tu goc."""
    import random
    rnd, groups = random.Random(seed), defaultdict(list)
    for it in data:
        groups[(it["db_id"], it.get("difficulty"))].append(it)
    keep = set()
    for k in sorted(groups, key=str):
        g = groups[k]
        keep |= {it["question_id"] for it in rnd.sample(g, min(len(g), round(n * len(g) / len(data))))}
    return [it for it in data if it["question_id"] in keep]


class _Pending(Exception):
    pass


class _Recorder:
    """LLM gia: tra ket qua neu da co trong cache, neu chua thi ghi lai prompt va dung cau do."""
    def __init__(self, llm):
        self.llm, self.todo = llm, []

    def chat(self, prompt, meta=None):
        r = self.llm.cached(prompt)
        if r is None:
            self.todo.append(prompt)
            raise _Pending
        return r

    def embed(self, *a):
        return self.llm.embed(*a)


def prefetch(llm, jobs, ctxs, args, out):
    """Goi truoc moi prompt con thieu, theo tung vong (vong 1 = giai doan 1, vong 2 = giai doan 2).
    Prompt duoc sap xep theo thu tu chu de cac prompt chung tien to (cung schema/view) dung lien nhau:
    Ollama dung lai KV cache cua tien to nen nhanh hon nhieu. Ket qua tung cau KHONG doi (cung prompt, temperature 0)."""
    for rnd in range(1, 4):
        rec = _Recorder(llm)
        for method, it in jobs:
            try:
                run_item(method, it, ctxs[it["db_id"]], rec, args)
            except _Pending:
                pass
        todo = sorted(set(rec.todo))
        if not todo:
            return
        n, w = len(todo), max(1, args.workers)
        chunks = [todo[i * n // w:(i + 1) * n // w] for i in range(w)]   # moi luong mot doan lien tiep -> giu tien to
        state = dict(done=0, t0=time.time())
        lock = threading.Lock()

        def work(chunk):
            for p in chunk:
                llm.chat(p)
                with lock:
                    state["done"] += 1
                    d, el = state["done"], time.time() - state["t0"]
                    (out / "prefetch_progress.json").write_text(json.dumps(
                        dict(round=rnd, done=d, total=n, elapsed=el, eta=el / d * (n - d), updated=time.time())))
                    if d % 20 == 0 or d == n:
                        print(f"[prefetch vong {rnd}] {d}/{n}  con lai ~{el / d * (n - d) / 60:.0f} phut", flush=True)

        print(f"[prefetch vong {rnd}] {n} prompt can goi LLM, {w} luong", flush=True)
        ths = [threading.Thread(target=work, args=(c,)) for c in chunks]
        for t in ths:
            t.start()
        for t in ths:
            t.join()


def main(argv=None, llm=None):
    args = parse_args(argv)
    out = Path(args.out)
    (out / "views").mkdir(parents=True, exist_ok=True)
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    for i, it in enumerate(data):
        it.setdefault("question_id", i)
    by_db = defaultdict(list)
    for it in data:
        by_db[it["db_id"]].append(it)             # view oracle nhin TOAN BO dap an cua DB, nhu paper
    if args.db:
        data = [it for it in data if it["db_id"] in args.db.split(",")]
    if args.sample:
        data = stratified_sample(data, args.sample, args.seed)
    if args.qids:
        keep = set(json.loads(Path(args.qids).read_text()))
        data = [it for it in data if it["question_id"] in keep]
    if args.limit:
        data = data[:args.limit]
    methods = list(METHODS) if args.methods == "all" else args.methods.split(",")

    ctxs, stats = {}, {}
    for db in sorted({it["db_id"] for it in data}):
        path = Path(args.db_root) / db / f"{db}.sqlite"
        print(f"[schema] {db}")
        c = ctxs[db] = DbCtx(db, path, [it["SQL"] for it in by_db[db]], args)
        for src, vs in c.views.items():
            (out / "views" / f"{db}.{src}.sql").write_text(
                "\n\n".join(f"-- origin={v.origin} row_preserving={v.row_preserving} check={v.verified}\n{v.ddl()}"
                            for v in vs) + "\n", encoding="utf-8")
        stats[db] = dict(tables=len(c.schema.tables), fks=sum(len(t.fks) for t in c.schema.tables.values()),
                         oracle=len(c.views["oracle"]), oracle_fan=sum(not v.row_preserving for v in c.views["oracle"]),
                         auto=len(c.views["auto"]), auto_rows_equal=sum(v.verified == "rows_equal" for v in c.views["auto"]))
        print("   ", stats[db])
    (out / "views_stats.json").write_text(json.dumps(stats, indent=1))
    if args.views_only:
        return

    if llm is None:
        llm = OllamaLLM(args.model, args.host, str(out / "llm_cache.sqlite"), args.num_ctx, args.num_predict, args.think)
    if args.retrieval_sweep:
        m = METHODS["hybrid_ret"]
        lines = ["k,full_coverage_pct,mean_table_recall_pct,mean_objects"]
        for k in range(1, 11):
            full = rec = nobj = 0
            for it in data:
                c = ctxs[it["db_id"]]
                vs, ts = c.objects(m)
                top = set(c.retriever(m, args, llm).rank(it["question"] + " " + (it.get("evidence") or ""))[:k])
                vs, ts = [v for v in vs if v.name in top], [t for t in ts if t in top]
                cov = c.coverage(vs, ts, tables_in_sql(it["SQL"], c.schema))
                full, rec, nobj = full + (cov == 1.0), rec + cov, nobj + len(vs) + len(ts)
            lines.append(f"{k},{100 * full / len(data):.1f},{100 * rec / len(data):.1f},{nobj / len(data):.2f}")
        (out / "retrieval_sweep.csv").write_text("\n".join(lines) + "\n")
        print("\n".join(lines))
        return

    (out / "config.json").write_text(json.dumps(vars(args), indent=1))
    if not args.no_prefetch and hasattr(llm, "cached"):
        jobs = []
        for method in methods:
            p = out / f"predictions_{method}.jsonl"
            done = {json.loads(l)["qid"] for l in p.read_text(encoding="utf-8").splitlines() if l.strip()} if p.exists() else set()
            jobs += [(method, it) for it in data if it["question_id"] not in done]
        prefetch(llm, jobs, ctxs, args, out)
    gold = {}
    for method in methods:
        p = out / f"predictions_{method}.jsonl"
        done = {json.loads(l)["qid"] for l in p.read_text(encoding="utf-8").splitlines() if l.strip()} if p.exists() else set()
        ok = n = 0
        with open(p, "a", encoding="utf-8") as f:
            for it in data:
                qid = it["question_id"]
                if qid in done:
                    continue
                c = ctxs[it["db_id"]]
                if qid not in gold:
                    rows, err, sec = run_sql(c.schema.path, it["SQL"], args.timeout * 4)
                    if err:
                        print(f"[CANH BAO] SQL dap an loi o qid={qid}: {err}")
                    gold[qid] = (rows, sec)
                rec = score(run_item(method, it, c, llm, args), *gold[qid], c.schema.path, args.timeout)
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
                f.flush()
                n, ok = n + 1, ok + rec["correct"]
                if n % 10 == 0:
                    print(f"[{method}] {n}/{len(data) - len(done)}  EX tam thoi = {100 * ok / n:.1f}")
    print(report.build(out))
    print(f"\nDa ghi: {out / 'summary.md'}, {out / 'summary.csv'}")


if __name__ == "__main__":
    main()
