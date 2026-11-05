"""Bon phuong phap so sanh tren cung bo du lieu, cung LLM, cung cach cham:

  base      : mot lan goi, toan bo bang goc (doi chung zero-shot).
  tasql     : TA-SQL (Qu et al., ACL Findings 2024) - baseline ma paper V-SQL so sanh. Cai lai dung ma nguon chinh thuc:
              TASL (dummy SQL tren toan schema -> trich bang/cot) + TALOG (bieu dien ky hieu SR kieu pandas -> SQL).
              Prompt chep nguyen van (vsql/tasql_prompts.py).
  vsql      : V-SQL dung theo paper: view thiet ke tu cac phep JOIN cua SQL dap an (muc 6 cua paper), giai doan 1 sinh dummy
              SQL tren view bang prompt Hinh 4, giai doan 2 LLM khoi phuc ve bang goc bang prompt Hinh 5.
  vsqlplus  : cai tien (V-SQL+), ket hop 2 huong, giai doan 2 giu nguyen nhu paper:
              Huong 1 - sinh view tu dong tu khoa ngoai (chi noi N-1 khi khoa duoc tham chieu la duy nhat, kiem tra so dong,
                        suy them khoa ngoai thieu khai bao, ten cot sach, ghi nguon goc cot).
              Huong 2 - chon view dung bang truy hoi lai (BM25 + embedding), bo tro boi: truy hoi muc cot roi gop len view,
                        lien ket gia tri voi DB, bau chon nhieu mau, schema lai (quay ve bang goc khi LLM dung cot khong
                        co trong view), va CSDL nho thi dua het view vao prompt.
              Bien the: vsqlplus_all (chi huong 1), vsqlplus_novote, vsqlplus_novl, vsqlplus_nofb, vsqlplus_det.
"""
import difflib
import json
import re
from collections import Counter
from pathlib import Path

from . import autoview as A
from . import tasql_prompts as TP
from . import views as V
from .db import Schema, connect, qi, references, run_sql, tables_in_sql, classify_error
from .linking import HybridIndex, ValueIndex, link_columns, link_values, rrf
from .llm import extract_sql
from .meta import Descriptions, load_tables_json, table6_table, table6_view, table_ddl

NOTES = {
    "base": "Zero-shot 1 giai doan tren bang goc",
    "tasql": "TA-SQL (baseline cua paper): TASL dummy SQL + TALOG SR->SQL",
    "vsql": "V-SQL dung theo paper: view theo JOIN dap an, schema Bang 6, prompt Hinh 4 + Hinh 5",
    "vsqlplus": "V-SQL+ = huong 1 (sinh view tu dong) + huong 2 (chon view bang truy hoi lai); giai doan 2 nhu paper",
    "vsqlplus_all": "Chi huong 1: view tu dong, dua het view vao prompt (khong chon view)",
    "vsqlplus_novote": "V-SQL+ bo bau chon nhieu mau (huong 2)",
    "vsqlplus_novl": "V-SQL+ bo lien ket gia tri (huong 2)",
    "vsqlplus_nofb": "V-SQL+ bo schema lai (huong 2)",
    "vsqlplus_det": "V-SQL+ thay giai doan 2 bang giai ma tat dinh (ngoai de xuat, de doi chieu)",
}
MAIN = ["base", "tasql", "vsql", "vsqlplus"]
ABLATIONS = ["vsqlplus_all", "vsqlplus_novote", "vsqlplus_novl", "vsqlplus_nofb", "vsqlplus_det"]

# --------------------------------------------------------------------------- prompt
P_BASE = """You are an experienced database administrator, please answer "question" by ONE SQLite query with no explanation.

# db schema
{schema}

# question
{question}
{evidence}
Return only the SQL inside a ```sql code block."""

# V-SQL, Hinh 4 cua paper (nguyen van). Evidence cua BIRD (neu dung) nam trong {query}, khong them muc nao vao template.
P_VSQL_1 = """# target
You are an experienced database administrator, please answer "question" by sql with no explanation.
notice:
1. Do not alias the output fields
2. must avoid ambiguous column name by using table name and column name in the SQL statement. For example, use `table_name.column_name` instead of just `column_name`.
3. refer to "relevant db schema"
# relevant db schema
{relevant_db_schema}
# question
{query}"""

# V-SQL, Hinh 5 cua paper (nguyen van, ke ca loi chinh ta "foramt")
P_VSQL_2 = """# target
According to the "views schemas", "view query" and "relevant table schemas", restore the sql in "view query" to one used the original table query without explanation
notice:
1. SQL should contain "join" as little as possible.
2. table in "views schemas" should not be contained in output.
3. comply with the syntax of {db_type}.
4. must avoid ambiguous column name by using table name and column name in the SQL statement. For example, use `table_name.column_name` instead of just `column_name`.
# view schemas
{view_schemas}
# view query
Question: {query}
```sql
{dummy_sql}
```
# relevant table schemas
{table_schemas}
# foramt
```sql
{{sql}}
```"""

P_PLUS = """# target
You are an experienced database administrator, please answer "question" by ONE SQLite query with no explanation.
The schema contains VIEWS and TABLES. A view `v_<t>` has exactly one row per row of table <t> and already contains the
columns of the lookup tables of <t> (the comment of each column tells where it comes from), so most questions need no JOIN.
notice:
1. Query views exactly like tables. Use only the views, tables and columns listed in "relevant db schema".
2. To count or list the rows of a table that has no view, query that table directly.
3. must avoid ambiguous column name by using `name.column`; quote names with spaces or special characters by backticks.
4. Use the matched database values exactly as written (same spelling and case).
# relevant db schema
{schema}
{values}# question
{question}
{evidence}{note}
Return only the SQL inside a ```sql code block."""


def _ev(item, use):
    e = (item.get("evidence") or "").strip()
    return f"# evidence\n{e}\n" if use and e else ""


def first_statement(sql):
    """Cat cau lenh SQL dau tien (bo ';' va phan thua sau no, ngoai chuoi)."""
    if not sql:
        return ""
    q, i = None, 0
    while i < len(sql):
        ch = sql[i]
        if q:
            if ch == q:
                q = None
        elif ch in "'\"`":
            q = ch
        elif ch == ";":
            return sql[:i].strip()
        i += 1
    return sql.strip()


def clean(text):
    return first_statement(extract_sql(text))


def compile_error(path, sql):
    """Bien dich (EXPLAIN, khong chay) de bat loi ten bang/cot; None neu hop le."""
    if not sql:
        return "no_sql"
    con = connect(path)
    try:
        con.execute("EXPLAIN " + sql).fetchmany(1)
        return None
    except Exception as e:  # noqa: BLE001
        return str(e)
    finally:
        con.close()


# --------------------------------------------------------------------------- ngu canh moi DB
class DbCtx:
    def __init__(self, db_id, db_dir, gold_sqls, args, tables_json=None, tasql_meaning=None):
        self.db_id, self.args = db_id, args
        self.path = str(Path(db_dir) / f"{db_id}.sqlite")
        self.schema = s = Schema(db_id, self.path, args.samples, infer_fk=not args.no_infer_fk)
        self.desc = Descriptions(db_dir, s)
        self.gold_sqls = gold_sqls
        self.tj = (tables_json or {}).get(db_id)
        self.tasql_meaning = tasql_meaning
        self._cache = {}

    def lazy(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    # ---- view
    @property
    def oracle(self):
        return self.lazy("oracle", lambda: V.validate(self.schema, A.oracle_views(self.schema, self.gold_sqls)))

    @property
    def auto(self):
        a = self.args
        return self.lazy("auto", lambda: V.validate(self.schema, A.auto_views(self.schema, a.depth, a.max_cols)))

    @property
    def vindex(self):
        return self.lazy("vindex", lambda: ValueIndex(self.schema))

    def ddl(self, t):
        return table_ddl(self.schema, self.desc, t, self.args.samples)

    def coverage(self, tables, gold):
        return len(gold & set(tables)) / len(gold) if gold else 1.0


class Asker:
    """Goi LLM va cong don chi phi vao ban ghi."""

    def __init__(self, llm, rec, uid):
        self.llm, self.rec, self.uid = llm, rec, uid
        self.seen = set()

    def _acc(self, r, key=None):
        if key is not None:
            if key in self.seen:            # cung prompt + tuy chon da hoi trong cau nay: lay lai, khong ton them
                return
            self.seen.add(key)
        self.rec["calls"] += 1
        self.rec["prompt_tokens"] += r["prompt_tokens"]
        self.rec["completion_tokens"] += r["completion_tokens"]
        self.rec["llm_seconds"] += r["seconds"]

    def __call__(self, prompt, stage, **opts):
        r = self.llm.chat(prompt, dict(qid=self.uid, stage=stage), **opts)
        self._acc(r, (prompt, json.dumps(opts, sort_keys=True)))
        return r["text"]

    def many(self, reqs, stage):
        """reqs = [(prompt, opts)]; goi theo lo (de buoc prefetch gom du moi prompt con thieu trong mot vong)."""
        if hasattr(self.llm, "chat_many"):
            rs = self.llm.chat_many([(p, dict(qid=self.uid, stage=f"{stage}{i}"), o) for i, (p, o) in enumerate(reqs)])
        else:
            rs = [self.llm.chat(p, dict(qid=self.uid, stage=f"{stage}{i}"), **o) for i, (p, o) in enumerate(reqs)]
        for (p, o), r in zip(reqs, rs):
            self._acc(r, (p, json.dumps(o, sort_keys=True)))
        return [r["text"] for r in rs]


# --------------------------------------------------------------------------- base
def run_base(item, ctx, ask, rec, args):
    s = ctx.schema
    schema = "\n\n".join(ctx.ddl(t) for t in s.tables)
    rec["n_objects"] = len(s.tables)
    rec["schema_tables"] = list(s.tables)
    return clean(ask(P_BASE.format(schema=schema, question=item["question"], evidence=_ev(item, args.evidence)), "base"))


# --------------------------------------------------------------------------- TA-SQL
def _tasql_schema_dicts(ctx):
    """database_schema (TASL), pk/fk (dev_tables.json) theo dung dinh dang cua ma TA-SQL."""
    tj = ctx.tj
    tn, cn = tj["table_names_original"], tj["column_names_original"]
    pk, fk = {}, {}
    for idx in tj["primary_keys"]:
        if isinstance(idx, int):
            pk[str(tn[cn[idx][0]])] = [cn[idx][-1]]
        else:
            pk[str(tn[cn[idx[0]][0]])] = [cn[i][-1] for i in idx]
    for a, b in tj["foreign_keys"]:
        fk[f"{tn[cn[a][0]]}.{cn[a][-1]}"] = f"{tn[cn[b][0]]}.{cn[b][-1]}"
    schema_for_db = {t: {} for t in tn}
    meaning = ctx.tasql_meaning
    if meaning:
        for key, value in meaning.items():
            db, otn, ocn = key.split("|")
            if db == ctx.db_id and otn in schema_for_db:
                schema_for_db[otn][ocn] = value.replace("#", "").replace("\n", ",  ")
    else:                                   # khong co column_meaning.json: dung mo ta CSV cua BIRD
        for ti, c in cn[1:]:
            t = tn[ti]
            m = ctx.desc.get(t, c).get("raw", {})
            schema_for_db[t][c] = ", ".join(x for x in (m.get("name"), m.get("desc"), m.get("values")) if x)
    p = "{\n "
    for table_name, cols in schema_for_db.items():
        p += f"{table_name}:\n  " + "{\n\t"
        for c, txt in cols.items():
            p += f"{c}: {txt}" + "\n\t"
            p += "\n\t"
        p += "}\n "
    p += "}"
    return p, pk, fk


def _tasql_value_prompt(ctx, t, c, fmt):
    """Nhu TALOG._get_info_from_csv: cot text/date -> 'all possible values are [...]' (<=10) hoac 3 vi du.
    (Ban goc dung ORDER BY RANDOM(); o day lay theo thu tu tu nhien de ket qua tai lap duoc.)"""
    if fmt not in ("text", "date", "datetime"):
        return None
    rows, err, _ = run_sql(ctx.path, f"SELECT DISTINCT {qi(c)} FROM {qi(t)} WHERE {qi(c)} IS NOT NULL LIMIT 11", 30)
    if err or not rows or not isinstance(rows[0][0], str) or len(rows[0][0]) >= 50:
        return None
    vals = [r[0] for r in rows]
    if len(vals) <= 10:
        return f"all possible values are {vals}"
    return f"example values are {vals[:3]}"


def _tasql_column_description(ctx, sl):
    """TALOG.generate_schema_prompt"""
    items = {}
    for otn, ocn in sl:
        raw = ctx.desc.get(otn, ocn).get("raw", {})
        column_name, column_description = raw.get("name", ocn), raw.get("desc", "")
        column_type, value_description = raw.get("fmt", ""), raw.get("values", "")
        vp = ctx.lazy(("tavp", otn, ocn), lambda: _tasql_value_prompt(ctx, otn, ocn, column_type))
        tmp = f"{column_type}, the full column name is {column_name}"
        if column_description not in ("", " ", None):
            tmp += f", column description is {column_description.replace(chr(10), ' ')}"
        if value_description not in ("", " ", None):
            tmp += f", value description is {value_description.replace(chr(10), ' ')}"
        if vp:
            tmp += f", {vp}"
        a = f"`{otn}`" if " " in otn else otn
        b = f"`{ocn}`" if " " in ocn else ocn
        items[f"{a}.{b}"] = tmp
    p = "{\n\t"
    for k, v in items.items():
        p += f"{k}: {v}\n"
        p += "\n\t"
    p += "}"
    return p


def _strip_think(text):
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()


def _tasql_sql(text):
    """Hau xu ly cau tra loi cua sr2sql. Ban goc: 'SELECT ' + tra_loi (GPT-4 viet tiep sau `SQL = "SELECT`).
    Mo hinh chat (qwen) hay tra ca khoi ```sql``` hoac viet lai tu SELECT -> chap nhan ca hai dang."""
    t = _strip_think(text)
    m = re.findall(r"```(?:sql|sqlite)?\s*(.*?)```", t, flags=re.S | re.I)
    if m:
        t = m[-1]
    t = t.strip().strip('"').strip()
    if not re.match(r"(SELECT|WITH)\b", t, re.I):
        t = "SELECT " + t
    t = t.split('"\n')[0] if t.count('"') % 2 else t           # dau " dong chuoi SQL = "SELECT ... "
    return first_statement(t.rstrip('"').strip())


def run_tasql(item, ctx, ask, rec, args):
    if ctx.tj is None:
        raise SystemExit("TA-SQL can dev_tables.json (--tables-json)")
    q, e = item["question"], item.get("evidence") or ""
    if not args.evidence:
        e = ""
    database_schema, pk, fk = ctx.lazy("taschema", lambda: _tasql_schema_dicts(ctx))
    sys_msg = "You are an AI assistant that helps people find information."
    # ---- TASL: dummy SQL tren toan schema, roi trich thuc the schema xuat hien trong dummy SQL
    p1 = TP.dummy_sql_prompt.format(database_schema=database_schema, primary_key_dic=pk, foreign_key_dic=fk,
                                    question_prompt=q, evidence=e)
    dummy = _strip_think(ask(p1, "tasl", system=sys_msg, stop=["return SQL"]))
    rec["dummy_sql"] = dummy
    tn = ctx.tj["table_names_original"]
    cols = [[tn[int(ti)], c] for ti, c in ctx.tj["column_names_original"][1:]]
    ftabs = {t for t in tn if t in dummy}                       # so khop chuoi con, nhu ma goc
    fcols = {c for _, c in cols if c in dummy}
    sl = [tc for tc in cols if tc[1] in fcols and tc[0] in ftabs]   # giu thu tu schema (ban goc: thu tu set, khong tai lap)
    rec["schema_tables"] = sorted({t for t, _ in sl})
    rec["n_objects"] = len(rec["schema_tables"])
    # ---- TALOG: SR kieu pandas -> SQL
    processed = []
    for t, c in sl:
        processed.append(f"{f'`{t}`' if ' ' in t else t}.{f'`{c}`' if ' ' in c else c}")
    processed = f"[{', '.join(processed)}]".replace("'", "")
    coldesc = _tasql_column_description(ctx, sl)
    p2 = TP.generate_sr.format(sr_example=TP.sr_examples, question=q, schema=processed, column_description=coldesc,
                               evidence=e).strip("\n")
    sr = _strip_think(ask(p2, "talog_sr", system=sys_msg)).replace('"', "")
    rec["sr"] = sr
    p3 = TP.sr2sql.format(question=q, schema=[".".join(t) for t in sl], evidence=e, column_description=coldesc,
                          SR=sr, foreign_key_dic=fk).strip("\n")
    return _tasql_sql(ask(p3, "talog_sql", system=sys_msg))


# --------------------------------------------------------------------------- V-SQL (paper)
def vsql_query(item, args):
    """{query} cua Hinh 4/5: cau hoi; evidence cua BIRD noi vao sau (--vsql-evidence query) hoac bo (none)."""
    e = (item.get("evidence") or "").strip()
    if args.evidence and args.vsql_evidence == "query" and e:
        return f"{item['question']}\n{e}"
    return item["question"]


def run_vsql(item, ctx, ask, rec, args):
    """V-SQL dung theo paper: D' = cac view + bang khong nam trong view nao (bang da gop vao view khong hien rieng);
    schema trinh bay theo Bang 6; prompt Hinh 4 va Hinh 5 nguyen van."""
    views = ctx.oracle
    tabs = V.leftover_tables(ctx.schema, views)
    parts = [table6_view(v, ctx.desc) for v in views] + [table6_table(ctx.schema, ctx.desc, t) for t in tabs]
    rec["n_objects"] = len(views) + len(tabs)
    rec["schema_tables"] = sorted(set(tabs).union(*[v.source_tables() for v in views]))
    p1 = P_VSQL_1.format(relevant_db_schema="\n\n".join(parts), query=vsql_query(item, args))
    dummy = rec["dummy_sql"] = clean(ask(p1, "vsql_s1"))
    return restore(ctx, item, ask, rec, dummy, views, tabs, "vsql_s2", args)


def restore(ctx, item, ask, rec, dummy, views, tabs, stage, args):
    """Giai doan 2 cua paper (Hinh 5): LLM khoi phuc dummy SQL tren view ve SQL tren bang goc."""
    used = [v for v in views if references(dummy, v.name)]
    rec["views_used"] = [v.name for v in used]
    if not dummy or not used:
        return dummy                            # dummy SQL khong dung view -> da la SQL tren bang goc
    tset = set().union(*[v.source_tables() for v in used]) | {t for t in tabs if references(dummy, t)}
    p2 = P_VSQL_2.format(db_type="SQLite", view_schemas="\n\n".join(v.ddl() for v in used), query=vsql_query(item, args),
                         dummy_sql=dummy,
                         table_schemas="\n\n".join(table6_table(ctx.schema, ctx.desc, t) for t in ctx.schema.tables if t in tset))
    return clean(ask(p2, stage))


# --------------------------------------------------------------------------- V-SQL+
class PlusIndex:
    """Doi tuong schema cua V-SQL+ (view tu dong + bang khong co view) va chi muc truy hoi muc cot / muc doi tuong."""

    def __init__(self, ctx, embedder):
        s, d, n = ctx.schema, ctx.desc, ctx.args.samples
        self.views = ctx.auto
        self.tables = A.visible_tables(s, self.views)
        self.text = {v.name: A.describe(v, s, d, n) for v in self.views}
        self.text.update({t: ctx.ddl(t) for t in self.tables})
        self.names = [v.name for v in self.views] + self.tables
        self.view = {v.name: v for v in self.views}
        # nguon (bang, cot) cua tung cot trong tung doi tuong
        self.src = {v.name: {(c.table, c.col): c.name for c in v.cols} for v in self.views}
        for t in self.tables:
            self.src[t] = {(t, c.name): c.name for c in s.tables[t].columns}
        col_items, obj_items = [], []
        for v in self.views:
            ents = A.column_entries(v, s, d, n)
            col_items += [((v.name, nm), txt) for nm, _, _, txt in ents]
            obj_items.append((v.name, v.name + " " + " ".join(nm for nm, *_ in ents)))
        for t in self.tables:
            ents = [(c.name, f"{c.name} {t} {d.text(t, c.name)}") for c in s.tables[t].columns]
            col_items += [((t, nm), txt) for nm, txt in ents]
            obj_items.append((t, t + " " + " ".join(nm for nm, _ in ents)))
        self.col_index = HybridIndex(col_items, embedder)
        self.obj_index = HybridIndex(obj_items, embedder)
        self.est_tokens = sum(len(x) for x in self.text.values()) // 4

    def objects_with(self, table, col):
        return [o for o in self.names if (table, col) in self.src[o]]


def _embedder(llm, args):
    if args.no_embed or not hasattr(llm, "embed"):
        return None

    def f(texts):
        return llm.embed(args.embed_model, texts)
    try:
        f(["probe"])
        return f
    except Exception as e:  # noqa: BLE001
        print(f"[canh bao] khong goi duoc embedding '{args.embed_model}' ({e}); V-SQL+ chi dung BM25")
        args.no_embed = True
        return None


def plus_rank(px, item, links, colhits):
    """Xep hang doi tuong: RRF cua (1) truy hoi muc cot gop len doi tuong, (2) truy hoi muc doi tuong,
    (3) lien ket gia tri + ten cot duoc nhac thang."""
    q = item["question"] + " " + (item.get("evidence") or "")
    col = px.col_index.rank(q)
    agg = Counter()
    per = {}
    for (o, _), sc in col.items():
        per.setdefault(o, []).append(sc)
    for o, scs in per.items():
        agg[o] = sum(sorted(scs, reverse=True)[:3])
    r1 = [o for o, _ in agg.most_common()]
    r2 = [o for o, _ in px.obj_index.rank(q).most_common()]
    link = Counter()
    for _, t, c, w in links:
        for o in px.objects_with(t, c):
            link[o] += w
    for t, c in colhits:
        for o in px.objects_with(t, c):
            link[o] += 0.5
    r3 = [o for o, _ in link.most_common()]
    fused = rrf([r1, r2, r3], weights=[1.0, 1.0, 2.0])
    order = sorted(px.names, key=lambda o: (-fused.get(o, 0.0), px.names.index(o)))
    return order, link


def _values_text(px, objs, links, k=8):
    lines, seen = [], set()
    for val, t, c, _ in links:
        where = [f"{o}.{px.src[o][(t, c)]}" for o in objs if (t, c) in px.src[o]]
        if not where or (val, t, c) in seen:
            continue
        seen.add((val, t, c))
        lines.append(f"- {val!r} is a value of " + ", ".join(where[:3]))
        if len(lines) >= k:
            break
    return "# matched database values\n" + "\n".join(lines) + "\n" if lines else ""


def _plus_prompt(px, ctx, objs, item, links, args, extra_tables=(), note=""):
    order = [o for o in px.names if o in objs]
    parts = [px.text[o] for o in order] + [ctx.ddl(t) for t in extra_tables if t not in px.text]
    return P_PLUS.format(schema="\n\n".join(parts), values=_values_text(px, order, links) if links else "",
                         question=item["question"], evidence=_ev(item, args.evidence), note=note)


def _used(sql, names):
    return frozenset(n for n in names if references(sql, n))


_ERR = re.compile(r"no such (column|table): ([^\s]+)", re.I)


def _fallback_tables(ctx, err, shown):
    """Loi 'no such column/table' -> cac bang goc chua ten do (dung han hoac gan dung)."""
    m = _ERR.search(err or "")
    if not m:
        return [], None
    kind, name = m.group(1).lower(), m.group(2).strip("`\"[]")
    s = ctx.schema
    out = []
    if kind == "column":
        qual, _, col = name.rpartition(".")
        if qual and qual.strip("`\"") in s.tables:
            out.append(qual.strip("`\""))
        hits = [t for t in s.tables if s.tables[t].col(col)]
        if not hits:
            allc = {c.name.lower(): [] for t in s.tables.values() for c in t.columns}
            for t in s.tables.values():
                for c in t.columns:
                    allc[c.name.lower()].append(t.name)
            for c in difflib.get_close_matches(col.lower(), list(allc), n=2, cutoff=0.8):
                hits += allc[c]
        out += hits
    else:
        low = {t.lower(): t for t in s.tables}
        if name.lower() in low:
            out.append(low[name.lower()])
        else:
            out += [low[x] for x in difflib.get_close_matches(name.lower(), list(low), n=1, cutoff=0.7)]
    out = [t for t in dict.fromkeys(out) if t not in shown]
    return out[:3], name


def _where_is(px, ctx, objs, extra, name):
    """Cac cot `name` (bo tien to) co trong cac view/bang dang hien trong prompt."""
    col = name.rpartition(".")[2].lower()
    hits = []
    for o in objs:
        hits += [f"{o}.{nm}" for (t, c), nm in px.src[o].items() if nm.lower() == col or c.lower() == col]
    for t in extra:
        c = ctx.schema.tables[t].col(col)
        if c:
            hits.append(f"{t}.{c.name}")
    return list(dict.fromkeys(hits))[:4]


def run_plus(item, ctx, ask, rec, args, llm, variant=""):
    px = ctx.lazy("plus", lambda: PlusIndex(ctx, _embedder(llm, args)))
    use_vl = variant not in ("novl", "all")             # "all" = chi huong 1: khong dung thanh phan nao cua huong 2
    links = link_values(ctx.vindex, item["question"], item.get("evidence")) if use_vl else []
    colhits = link_columns(ctx.schema, item["question"], item.get("evidence")) if use_vl else set()
    rec["value_links"] = [(v, t, c) for v, t, c, _ in links[:8]]
    small = len(px.names) <= args.all_max_objects or px.est_tokens <= args.all_max_tokens
    rec["all_in_prompt"] = small or variant == "all"
    if rec["all_in_prompt"]:
        objs = list(px.names)
    else:
        order, link = plus_rank(px, item, links, colhits)
        strong = [o for o in order if link.get(o, 0) >= 1.5][:2]          # doi tuong chua gia tri khop manh
        cand = list(dict.fromkeys(order[:args.k_cand] + strong))
        rec["candidates"] = cand
        if variant == "novote" or args.n_samples <= 1:
            objs = list(dict.fromkeys(order[:args.topk] + strong))
        else:
            # bau chon: N dummy SQL tren tap ung vien (1 tham lam + N-1 mau o nhiet do > 0) -> tap view xuat hien nhieu nhat
            p = _plus_prompt(px, ctx, cand, item, links, args)
            reqs = [(p, {})] + [(p, dict(temperature=args.sample_temp, seed=i)) for i in range(1, args.n_samples)]
            sets = [_used(clean(t), cand) for t in ask.many(reqs, "plus_vote")]
            sets = [x for x in sets if x]
            if sets:
                freq = Counter(o for x in sets for o in x)
                cnt = Counter(sets)
                best = max(cnt, key=lambda x: (cnt[x], sum(freq[o] for o in x), -len(x)))
                objs = set(best) | {o for o, f in freq.items() if f * 2 > len(sets)}
                objs = [o for o in cand if o in objs or o in strong]
                rec["vote"] = dict(sets=[sorted(x) for x in sets], chosen=objs)
            else:
                objs = list(dict.fromkeys(order[:args.topk] + strong))
    rec["objects"] = objs
    shown_tables = [o for o in objs if o in ctx.schema.tables]
    extra, note = [], ""
    prompt = _plus_prompt(px, ctx, objs, item, links, args)
    dummy = clean(ask(prompt, "plus_final"))
    rec["fallback"] = []
    for k in range(args.max_fallback if variant not in ("nofb", "all") else 0):
        sql, _ = V.unfold(dummy, px.views)
        err = compile_error(ctx.path, sql)
        if err is None or err == "no_sql":
            break
        add, name = _fallback_tables(ctx, err, set(shown_tables) | set(extra))
        # schema lai: cot/bang LLM can khong co trong view duoc cung cap -> dua bang goc tuong ung vao prompt
        extra += add
        where = _where_is(px, ctx, objs, extra, name) if name else []
        if not add and not where:
            break
        note += f"\n# note\nYour previous query failed: `{name}` does not exist where you used it."
        if where:
            note += f" It exists as: {', '.join(where)}."
        if add:
            note += f" The original table(s) {', '.join(add)} are added to the schema; join them on their key columns if needed."
        note += "\n"
        rec["fallback"].append(dict(error=err, added=add, where=where))
        prompt = _plus_prompt(px, ctx, objs, item, links, args, extra_tables=extra, note=note)
        dummy = clean(ask(prompt, f"plus_fb{k}"))
    rec["dummy_sql"] = dummy
    if variant == "det":
        final, rec["views_used"] = V.unfold(dummy, px.views)       # bien the: giai ma tat dinh (khong thuoc de xuat)
    else:
        # giai doan 2 giu nguyen nhu paper (Hinh 5): V-SQL+ chi doi cach sinh view va cach chon view
        final = restore(ctx, item, ask, rec, dummy, px.views, list(ctx.schema.tables), "plus_s2", args)
    covered = set(extra) | set(shown_tables)
    for o in objs:
        if o in px.view:
            covered |= px.view[o].source_tables()
    rec["schema_tables"] = sorted(covered)
    rec["n_objects"] = len(objs) + len(extra)
    return final


# --------------------------------------------------------------------------- chay + cham
def run_item(method, item, ctx, llm, args):
    rec = dict(uid=item["uid"], qid=item["question_id"], db_id=item["db_id"], difficulty=item.get("difficulty", "unknown"),
               method=method, calls=0, prompt_tokens=0, completion_tokens=0, llm_seconds=0.0, dummy_sql=None,
               views_used=[], n_objects=0)
    ask = Asker(llm, rec, item["uid"])
    if method == "base":
        final = run_base(item, ctx, ask, rec, args)
    elif method == "tasql":
        final = run_tasql(item, ctx, ask, rec, args)
    elif method == "vsql":
        final = run_vsql(item, ctx, ask, rec, args)
    elif method.startswith("vsqlplus"):
        final = run_plus(item, ctx, ask, rec, args, llm, method[len("vsqlplus_"):] if "_" in method else "")
    else:
        raise ValueError(method)
    rec["final_sql"] = final
    rec["coverage"] = ctx.coverage(rec.get("schema_tables", []), tables_in_sql(item["SQL"], ctx.schema))
    return rec


def score(rec, gold_rows, gold_seconds, db_path, timeout):
    rows, err, sec = run_sql(db_path, rec["final_sql"], timeout)
    rec["exec_seconds"], rec["gold_seconds"], rec["error"] = sec, gold_seconds, err
    rec["correct"] = bool(err is None and gold_rows is not None and set(rows) == set(gold_rows))
    if err is not None:
        rec["outcome"] = classify_error(err)
    elif rec["correct"]:
        rec["outcome"] = "correct"
    else:
        rec["outcome"] = "wrong_empty" if not rows else "wrong_result"
    return rec


def load_meaning(path):
    p = Path(path) if path else None
    return json.loads(p.read_text(encoding="utf-8")) if p and p.exists() else None


__all__ = ["DbCtx", "run_item", "score", "NOTES", "MAIN", "ABLATIONS", "load_tables_json", "load_meaning"]
