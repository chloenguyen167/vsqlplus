"""7 cau hinh thuc nghiem: tai hien V-SQL va 4 cai tien (tach rieng tung yeu to)."""
from pathlib import Path

from . import views as V
from .db import Schema, classify_error, references, run_sql, tables_in_sql
from .llm import extract_sql
from .retrieval import Retriever, object_doc

# views: nguon view | tables: bang goc dua vao prompt | stage2: cach dua dummy SQL ve bang goc
METHODS = {
    "base":       dict(views=None,     tables="all",      stage2=None,  note="Baseline 1 giai doan tren bang goc"),
    "vsql":       dict(views="oracle", tables="leftover", stage2="llm", note="TAI HIEN PAPER: view theo dap an + LLM tai tao"),
    "vsql_det":   dict(views="oracle", tables="leftover", stage2="det", note="CT1: viet lai tat dinh"),
    "auto_llm":   dict(views="auto",   tables="leftover", stage2="llm", note="CT2: view tu dong (giu LLM tai tao)"),
    "auto_det":   dict(views="auto",   tables="leftover", stage2="det", note="CT1+CT2"),
    "hybrid":     dict(views="auto",   tables="all",      stage2="det", note="CT1+CT2+CT3: schema lai"),
    "hybrid_ret": dict(views="auto",   tables="all",      stage2="det", retrieve=True, note="CT1+2+3+CT4: truy xuat view"),
}

P_BASE = """You are a SQLite expert. Write ONE SQLite query that answers the question using the database schema below.

### Database schema
{schema}

### Question
{question}
{evidence}
Return only the final SQL inside a ```sql code block."""

P_VIEW = """You are a SQLite expert. The database is exposed through the VIEWS below{and_tables}. A view already contains the columns of related lookup tables, so most questions need no JOIN. Query views exactly like ordinary tables. Use only the names listed below.
{rules}
### Schema
{schema}

### Question
{question}
{evidence}
Return only the final SQL inside a ```sql code block."""

R_HYBRID = """
Rules:
- Prefer a view when it already contains every column you need.
- Use a base table directly when the question is about the rows of that table itself (for example counting or listing entries of a lookup table), or when you aggregate over a one-to-many relation.
- You may join views and base tables on their key columns when one view is not enough.
"""

# Phan dai (dinh nghia view, bang goc) dat truoc cau hoi de cac prompt cung view chung tien to -> Ollama dung lai KV cache
P_RECON = """You are a SQLite expert. The draft SQL below answers the question, but it is written against VIEWS. Rewrite it into ONE equivalent SQLite query that uses ONLY the original base tables (no views), replacing each view by the joins in its definition.

### View definitions
{views}

### Base tables
{tables}

### Question
{question}
{evidence}
### Draft SQL (on views)
{dummy}

Return only the final SQL inside a ```sql code block."""


class DbCtx:
    def __init__(self, db_id, path, gold_sqls, args):
        self.schema = s = Schema(db_id, path, args.samples, args.infer_fk)
        self.n_samples = args.samples
        man = Path(args.views_dir) / f"{db_id}.sql" if args.views_dir else None
        if man and man.exists():
            oracle = V.manual_views(s, man)
        else:
            oracle = V.oracle_views(s, gold_sqls, args.oracle_max_fan)
        self.views = {"oracle": V.validate(s, oracle), "auto": V.validate(s, V.auto_views(s, args.depth, args.max_cols))}
        self._retr = {}

    def objects(self, m):
        """(views, tables) hien trong prompt cua cau hinh m, truoc khi truy xuat."""
        vs = self.views[m["views"]] if m["views"] else []
        ts = list(self.schema.tables) if m["tables"] == "all" else V.leftover_tables(self.schema, vs)
        return vs, ts

    def retriever(self, m, args, llm):
        key = (m["views"], m["tables"])
        if key not in self._retr:
            vs, ts = self.objects(m)
            docs = {v.name: object_doc(self.schema, v.name, [(c.name, c.table, c.col) for c in v.cols]) for v in vs}
            for t in ts:
                docs[t] = object_doc(self.schema, t, [(c.name, t, c.name) for c in self.schema.tables[t].columns])
            self._retr[key] = Retriever(docs, args.retriever, llm, args.embed_model)
        return self._retr[key]

    def coverage(self, vs, ts, gold_tables):
        have = set(ts).union(*[v.source_tables() for v in vs]) if vs else set(ts)
        return len(gold_tables & have) / len(gold_tables) if gold_tables else 1.0


def _schema_text(ctx, vs, ts):
    parts = [v.describe(ctx.schema, ctx.n_samples) for v in vs]
    parts += [ctx.schema.table_ddl(t, ctx.n_samples) for t in ts]
    return "\n\n".join(parts)


def run_item(method, item, ctx, llm, args):
    m = METHODS[method]
    q = item["question"]
    ev = f"\n### External knowledge\n{item['evidence']}\n" if args.evidence and item.get("evidence") else ""
    vs, ts = ctx.objects(m)
    gold_tables = tables_in_sql(item["SQL"], ctx.schema)
    if m.get("retrieve") and len(vs) + len(ts) > args.topk:
        top = set(ctx.retriever(m, args, llm).rank(q + " " + (item.get("evidence") or ""))[:args.topk])
        vs, ts = [v for v in vs if v.name in top], [t for t in ts if t in top]
    rec = dict(qid=item["question_id"], db_id=item["db_id"], difficulty=item.get("difficulty", "unknown"),
               method=method, n_objects=len(vs) + len(ts), coverage=ctx.coverage(vs, ts, gold_tables),
               calls=0, prompt_tokens=0, completion_tokens=0, llm_seconds=0.0, dummy_sql=None, views_used=[])

    def ask(prompt, stage):
        r = llm.chat(prompt, dict(qid=item["question_id"], stage=stage))
        rec["calls"] += 1
        for k in ("prompt_tokens", "completion_tokens"):
            rec[k] += r[k]
        rec["llm_seconds"] += r["seconds"]
        return extract_sql(r["text"])

    if not m["views"]:
        final = ask(P_BASE.format(schema=_schema_text(ctx, [], ts), question=q, evidence=ev), "base")
    else:
        hybrid = m["tables"] == "all"
        prompt = P_VIEW.format(schema=_schema_text(ctx, vs, ts), question=q, evidence=ev,
                               and_tables=" and base TABLES" if ts else "", rules=R_HYBRID if hybrid else "")
        dummy = rec["dummy_sql"] = ask(prompt, f"s1:{m['views']}:{m['tables']}")
        all_views = ctx.views[m["views"]]
        if not dummy:
            final = ""
        elif m["stage2"] == "det":
            final, rec["views_used"] = V.unfold(dummy, all_views, prune=not args.no_prune)
        else:
            used = [v for v in all_views if references(dummy, v.name)]
            rec["views_used"] = [v.name for v in used]
            if not used:
                final = dummy                               # dummy khong dung view nao -> da la SQL tren bang goc
            else:
                tabs = set().union(*[v.source_tables() for v in used]) | {t for t in ts if references(dummy, t)}
                final = ask(P_RECON.format(
                    question=q, evidence=ev, dummy=dummy, views="\n\n".join(v.ddl() for v in used),
                    tables="\n\n".join(ctx.schema.table_ddl(t, ctx.n_samples) for t in sorted(tabs))), "s2")
    rec["final_sql"] = final
    return rec


def score(rec, gold_rows, gold_seconds, db_path, timeout):
    rows, err, sec = run_sql(db_path, rec["final_sql"], timeout)
    rec["exec_seconds"], rec["gold_seconds"] = sec, gold_seconds
    rec["error"] = err
    rec["correct"] = bool(err is None and gold_rows is not None and set(rows) == set(gold_rows))
    if err is not None:
        rec["outcome"] = classify_error(err)
    elif rec["correct"]:
        rec["outcome"] = "correct"
    else:
        rec["outcome"] = "wrong_empty" if not rows else "wrong_result"
    return rec
