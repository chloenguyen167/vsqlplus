#!/usr/bin/env python3
"""So sanh TA-SQL, V-SQL (dung theo paper) va V-SQL+ (cai tien) tren BIRD mini-dev, cung mot LLM chay qua Ollama.

Moi cau hoi duoc dinh danh theo VI TRI trong file du lieu (uid = 0..499), nen tinh du 500 cau nhu paper
(file mini_dev_sqlite.json co 2 cap ban ghi giong het nhau o question_id 137 va 138; bo danh gia chinh thuc cua BIRD
va Bang 2 cua paper (148/250/102) deu tinh ca hai, nen o day cung vay).

Vi du (tren Colab, xem notebooks/TASQL_VSQL_VSQLplus_Colab.ipynb):
  python run_compare.py --data minidev/MINIDEV/mini_dev_sqlite.json --db-root minidev/MINIDEV/dev_databases \
      --tables-json minidev/MINIDEV/dev_tables.json --tasql-meaning column_meaning.json \
      --model qwen3:8b --out results/cmp_qwen3_8b
"""
import argparse
import json
import threading
import time
from collections import defaultdict
from pathlib import Path

from vsql import report
from vsql import views as V
from vsql.db import run_sql, tables_in_sql
from vsql.llm import OllamaLLM, OpenAICompatLLM
from vsql.methods import ABLATIONS, MAIN, NOTES, DbCtx, load_meaning, load_tables_json, run_item, score


def parse_args(argv=None):
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--data", required=True)
    a.add_argument("--db-root", required=True)
    a.add_argument("--tables-json", default="", help="dev_tables.json (TA-SQL dung pk/fk tu day); mac dinh canh --data")
    a.add_argument("--tasql-meaning", default="", help="column_meaning.json cua TA-SQL (khong co: dung mo ta CSV)")
    a.add_argument("--out", default="results/cmp")
    a.add_argument("--methods", default="main",
                   help="main (tasql,vsql,vsqlplus) | all (+ ablation) | danh sach, vd: " + ",".join(MAIN + ABLATIONS + ["base"]))
    # LLM
    a.add_argument("--model", default="qwen3:8b")
    a.add_argument("--backend", default="ollama", choices=["ollama", "openai"])
    a.add_argument("--base-url", default="")
    a.add_argument("--api-key-env", default="OPENAI_API_KEY")
    a.add_argument("--rpm", type=float, default=0)
    a.add_argument("--host", default="http://localhost:11434")
    a.add_argument("--num-ctx", type=int, default=20480, help="du cho prompt dai nhat (view V-SQL ~14k token)")
    a.add_argument("--num-predict", type=int, default=800, help="paper: 800")
    a.add_argument("--think", action="store_true")
    a.add_argument("--workers", type=int, default=1, help="so luong goi Ollama song song (can OLLAMA_NUM_PARALLEL >= workers)")
    a.add_argument("--no-prefetch", action="store_true")
    a.add_argument("--retry-llm-errors", action="store_true",
                   help="thu lai cac prompt truoc do bi Ollama bao loi (mac dinh: giu cau tra loi rong da ghi nhan)")
    # du lieu
    a.add_argument("--limit", type=int, default=0)
    a.add_argument("--sample", type=int, default=0, help="lay mau phan tang N cau theo (db, do kho)")
    a.add_argument("--seed", type=int, default=0)
    a.add_argument("--db", default="")
    a.add_argument("--no-evidence", dest="evidence", action="store_false")
    a.add_argument("--samples", type=int, default=3, help="so gia tri mau moi cot trong prompt (base, V-SQL+)")
    a.add_argument("--vsql-evidence", default="query", choices=["query", "none"],
                   help="V-SQL: noi evidence vao {query} cua Hinh 4/5 (template giu nguyen) hoac khong dung evidence")
    a.add_argument("--no-infer-fk", action="store_true", help="khong suy them khoa ngoai (debit_card thieu khai bao)")
    # view
    a.add_argument("--depth", type=int, default=2)
    a.add_argument("--max-cols", type=int, default=60)
    # V-SQL+
    a.add_argument("--embed-model", default="nomic-embed-text")
    a.add_argument("--no-embed", action="store_true", help="chi dung BM25 (khong embedding)")
    a.add_argument("--all-max-objects", type=int, default=4, help="<= so doi tuong nay: dua het vao prompt")
    a.add_argument("--all-max-tokens", type=int, default=3500, help="schema <= so token nay: dua het vao prompt")
    a.add_argument("--k-cand", type=int, default=5, help="so doi tuong ung vien dua vao buoc bau chon")
    a.add_argument("--topk", type=int, default=4, help="so doi tuong giu lai khi khong bau chon")
    a.add_argument("--n-samples", type=int, default=4, help="so dummy SQL de bau chon (1 tham lam + N-1 mau)")
    a.add_argument("--sample-temp", type=float, default=0.7)
    a.add_argument("--max-fallback", type=int, default=2)
    a.add_argument("--timeout", type=float, default=30.0)
    a.add_argument("--views-only", action="store_true", help="chi sinh + kiem tra view (khong goi LLM)")
    a.add_argument("--selection-sweep", action="store_true", help="do do phu bang dap an cua buoc chon view (khong goi LLM sinh SQL)")
    return a.parse_args(argv)


def stratified_sample(data, n, seed=0):
    import random
    rnd, groups = random.Random(seed), defaultdict(list)
    for it in data:
        groups[(it["db_id"], it.get("difficulty"))].append(it)
    keep = set()
    for k in sorted(groups, key=str):
        g = groups[k]
        keep |= {it["uid"] for it in rnd.sample(g, min(len(g), round(n * len(g) / len(data))))}
    return [it for it in data if it["uid"] in keep]


class _Pending(Exception):
    pass


class _Recorder:
    """LLM gia cho buoc prefetch: tra ket qua neu da cache, neu chua thi ghi lai (prompt, tuy chon) va dung cau do."""

    def __init__(self, llm):
        self.llm, self.todo = llm, []

    def chat(self, prompt, meta=None, **opts):
        r = self.llm.cached(prompt, **opts)
        if r is None:
            self.todo.append((prompt, json.dumps(opts, sort_keys=True)))
            raise _Pending
        return r

    def chat_many(self, reqs):
        out, miss = [], False
        for p, _, o in reqs:
            r = self.llm.cached(p, **o)
            if r is None:
                self.todo.append((p, json.dumps(o, sort_keys=True)))
                miss = True
            out.append(r)
        if miss:
            raise _Pending
        return out

    def embed(self, *a):
        return self.llm.embed(*a)


def prefetch(llm, jobs, ctxs, args, out):
    """Goi truoc moi prompt con thieu theo tung vong (TA-SQL 3 vong, V-SQL 2, V-SQL+ toi da 4). Prompt sap theo thu tu chu
    de cac prompt chung tien to (cung schema) dung lien nhau -> Ollama dung lai KV cache. Ket qua tung cau KHONG doi."""
    for rnd in range(1, 10):
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
        chunks = [todo[i * n // w:(i + 1) * n // w] for i in range(w)]
        state = dict(done=0, t0=time.time())
        lock = threading.Lock()

        def work(chunk):
            for p, o in chunk:
                try:
                    llm.chat(p, **json.loads(o))
                except Exception as e:  # noqa: BLE001 - mot prompt loi khong duoc lam dung ca luong
                    print(f"[prefetch] loi o mot prompt, bo qua trong vong nay: {type(e).__name__}: {e}", flush=True)
                with lock:
                    state["done"] += 1
                    d, el = state["done"], time.time() - state["t0"]
                    (out / "prefetch_progress.json").write_text(json.dumps(
                        dict(round=rnd, done=d, total=n, elapsed=el, eta=el / d * (n - d), updated=time.time())))
                    if d % 25 == 0 or d == n:
                        print(f"[prefetch vong {rnd}] {d}/{n}  con lai ~{el / d * (n - d) / 60:.0f} phut", flush=True)

        print(f"[prefetch vong {rnd}] {n} prompt can goi LLM, {w} luong", flush=True)
        ths = [threading.Thread(target=work, args=(c,)) for c in chunks]
        for t in ths:
            t.start()
        for t in ths:
            t.join()


def load_data(args):
    data = json.loads(Path(args.data).read_text(encoding="utf-8"))
    for i, it in enumerate(data):
        it["uid"] = i
        it.setdefault("question_id", i)
    return data


def main(argv=None, llm=None):
    args = parse_args(argv)
    out = Path(args.out)
    (out / "views").mkdir(parents=True, exist_ok=True)
    data = load_data(args)
    by_db = defaultdict(list)
    for it in data:
        by_db[it["db_id"]].append(it["SQL"])           # view cua V-SQL (paper) nhin JOIN cua toan bo dap an DB
    if args.db:
        data = [it for it in data if it["db_id"] in args.db.split(",")]
    if args.sample:
        data = stratified_sample(data, args.sample, args.seed)
    if args.limit:
        data = data[:args.limit]
    methods = MAIN if args.methods == "main" else MAIN + ABLATIONS if args.methods == "all" else args.methods.split(",")
    for m in methods:
        if m not in NOTES:
            raise SystemExit(f"Phuong phap khong hop le: {m}")

    tj_path = args.tables_json or str(Path(args.data).with_name("dev_tables.json"))
    tables_json = load_tables_json(tj_path)
    meaning = load_meaning(args.tasql_meaning)
    if "tasql" in methods:
        print(f"[TA-SQL] dev_tables.json: {'co' if tables_json else 'KHONG CO'}; column_meaning.json: "
              f"{'co' if meaning else 'khong co -> dung mo ta CSV'}")
    ctxs, stats = {}, {}
    for db in sorted({it["db_id"] for it in data}):
        c = ctxs[db] = DbCtx(db, Path(args.db_root) / db, by_db[db], args, tables_json, meaning)
        for src, vs in (("oracle", c.oracle), ("auto", c.auto)):
            (out / "views" / f"{db}.{src}.sql").write_text(
                "\n\n".join(f"-- origin={v.origin} row_preserving={v.row_preserving} check={v.verified}\n{v.ddl()}"
                            for v in vs) + "\n", encoding="utf-8")
        stats[db] = dict(tables=len(c.schema.tables), fks=sum(len(t.fks) for t in c.schema.tables.values()),
                         inferred_fks=sum(f.source == "inferred" for t in c.schema.tables.values() for f in t.fks),
                         oracle=len(c.oracle), oracle_ok=sum(v.verified == "rows_equal" for v in c.oracle),
                         auto=len(c.auto), auto_ok=sum(v.verified == "rows_equal" for v in c.auto))
        print(f"[schema] {db} {stats[db]}", flush=True)
    (out / "views_stats.json").write_text(json.dumps(stats, indent=1))
    if args.views_only:
        return

    if llm is None:
        if args.backend == "openai":
            import os
            llm = OpenAICompatLLM(args.model, args.base_url, os.environ.get(args.api_key_env, ""),
                                  str(out / "llm_cache.sqlite"), args.num_predict, rpm=args.rpm)
        else:
            llm = OllamaLLM(args.model, args.host, str(out / "llm_cache.sqlite"), args.num_ctx, args.num_predict, args.think)

    if args.selection_sweep:
        return selection_sweep(data, ctxs, llm, args, out)
    if args.retry_llm_errors and hasattr(llm, "forget_errors"):
        print(f"[retry-llm-errors] xoa {llm.forget_errors()} cau tra loi loi khoi cache de thu lai")

    (out / "config.json").write_text(json.dumps(vars(args), indent=1))

    def done_uids(m):
        p = out / f"predictions_{m}.jsonl"
        return {json.loads(l)["uid"] for l in p.read_text(encoding="utf-8").splitlines() if l.strip()} if p.exists() else set()

    if not args.no_prefetch and hasattr(llm, "cached"):
        jobs = []
        for m in methods:
            done = done_uids(m)
            jobs += [(m, it) for it in data if it["uid"] not in done]
        prefetch(llm, jobs, ctxs, args, out)
    gold = {}
    for m in methods:
        done = done_uids(m)
        ok = n = 0
        with open(out / f"predictions_{m}.jsonl", "a", encoding="utf-8") as f:
            for it in data:
                if it["uid"] in done:
                    continue
                c = ctxs[it["db_id"]]
                if it["uid"] not in gold:
                    rows, err, sec = run_sql(c.path, it["SQL"], args.timeout * 10)
                    if err:
                        print(f"[CANH BAO] SQL dap an loi o uid={it['uid']}: {err}")
                    gold[it["uid"]] = (rows, sec)
                rec = score(run_item(m, it, c, llm, args), *gold[it["uid"]], c.path, args.timeout)
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
                f.flush()
                n, ok = n + 1, ok + rec["correct"]
                if n % 50 == 0:
                    print(f"[{m}] {n}/{len(data) - len(done)}  EX tam thoi = {100 * ok / n:.1f}", flush=True)
    for m in methods:
        p = out / f"predictions_{m}.jsonl"
        n_err = sum(json.loads(l).get("llm_errors", 0) > 0 for l in p.read_text(encoding="utf-8").splitlines() if l.strip())
        if n_err:
            print(f"[LOI LLM] {m}: {n_err} cau co it nhat mot loi goi LLM (tinh la sai). Xem /content/ollama.log; "
                  f"chay lai voi --retry-llm-errors de thu lai.")
    print(report.build(out, refs=[r for r in ("tasql", "vsql", "base") if r in methods]))
    print(f"\nDa ghi: {out / 'summary.md'}, {out / 'summary.csv'}")


def selection_sweep(data, ctxs, llm, args, out):
    """Do phu bang dap an cua buoc chon view V-SQL+ (truy hoi + lien ket gia tri, chua bau chon) theo k."""
    from vsql.linking import link_columns, link_values
    from vsql.methods import PlusIndex, _embedder, plus_rank
    lines = ["k,full_coverage_pct,n_questions_with_selection"]
    res = defaultdict(lambda: [0, 0])
    for it in data:
        c = ctxs[it["db_id"]]
        px = c.lazy("plus", lambda: PlusIndex(c, _embedder(llm, args)))
        if len(px.names) <= args.all_max_objects or px.est_tokens <= args.all_max_tokens:
            continue
        links = link_values(c.vindex, it["question"], it.get("evidence"))
        order, link = plus_rank(px, it, links, link_columns(c.schema, it["question"], it.get("evidence")))
        strong = [o for o in order if link.get(o, 0) >= 1.5][:2]
        gold = tables_in_sql(it["SQL"], c.schema)
        for k in range(1, 9):
            objs = list(dict.fromkeys(order[:k] + strong))
            cov = set()
            for o in objs:
                cov |= px.view[o].source_tables() if o in px.view else {o}
            res[k][0] += gold <= cov
            res[k][1] += 1
    for k in sorted(res):
        lines.append(f"{k},{100 * res[k][0] / max(1, res[k][1]):.1f},{res[k][1]}")
    (out / "selection_sweep.csv").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
