"""Cac phuong phap so sanh tren cung bo du lieu, cung LLM, cung cach cham:

  vsql      : V-SQL tai hien (ban duy nhat), sat paper nhat co the:
              - view thiet ke tu cac phep JOIN cua SQL dap an (muc 6), kieu Hinh 3 (alias = ten bang, bo cot id khoa ngoai
                da thay bang gia tri); D' = cac view + bang khong nam trong view nao (muc 4.1: D' thay cho D);
              - giai doan 1: prompt Hinh 4 nguyen van, {relevant_db_schema} = toan bo D' cua CSDL (view da thiet ke theo
                JOIN dap an cua chinh CSDL do; KHONG co buoc truy hoi / chon view nao);
              - giai doan 2: luon chay (paper mo ta khung 2 giai doan, dummy SQL khong duoc thuc thi), prompt Hinh 5
                nguyen van ({db_type} = SQLite), bang lien quan theo dinh nghia view ma dummy SQL dung (muc 4.5).
              Paper khong noi cach trinh bay schema trong prompt: Bang 6 them mo ta gia tri + gia tri mau,
              ten cot dac biet co backtick.
  vsqlplus  : cai tien (V-SQL+), ket hop 2 huong, giai doan 2 giu nguyen nhu paper:
              Huong 1 - sinh view tu dong tu khoa ngoai (chi noi N-1 khi khoa duoc tham chieu la duy nhat, kiem tra so dong,
                        suy them khoa ngoai thieu khai bao, ten cot sach, ghi nguon goc cot).
              Huong 2 - chon view dung bang truy hoi lai (BM25 + embedding), bo tro boi: truy hoi muc cot roi gop len view,
                        lien ket gia tri voi DB, bau chon nhieu mau, schema lai (quay ve bang goc khi LLM dung cot khong
                        co trong view), va CSDL nho thi dua het view vao prompt.
              vsqlplus_fig4: chi 2 huong; template va cach trinh bay schema y nhu vsql.
              Bien the: vsqlplus_all (chi huong 1), vsqlplus_novote, vsqlplus_novl, vsqlplus_nofb, vsqlplus_det.
"""
import difflib
import json
import re
from collections import Counter
from pathlib import Path

from . import autoview as A
from . import baselines as B
from . import views as V
from .db import Schema, connect, qi, references, run_sql, tables_in_sql, classify_error
from .linking import HybridIndex, ValueIndex, link_columns, link_values, rrf
from .llm import extract_sql
from .meta import Descriptions, load_tables_json, table6_table, table6_view, table_ddl

NOTES = {
    "vsql": "V-SQL theo paper: view Hinh 3 theo JOIN dap an; D' = ORACLE: chi view co bang goc nam trong SQL dap an (+ bang con lai ma dap an dung), prompt Hinh 4 + Hinh 5",
    "vsqlplus": "V-SQL+ = huong 1 (sinh view tu dong) + huong 2 (chon view bang truy hoi lai); giai doan 2 nhu paper",
    "vsqlplus_all": "Chi huong 1: view tu dong, dua het view vao prompt (khong chon view)",
    "vsqlplus_novote": "V-SQL+ bo bau chon nhieu mau (huong 2)",
    "vsqlplus_novl": "V-SQL+ bo lien ket gia tri (huong 2)",
    "vsqlplus_nofb": "V-SQL+ bo schema lai (huong 2)",
    "vsqlplus_det": "V-SQL+ thay giai doan 2 bang giai ma tat dinh (ngoai de xuat, de doi chieu)",
    "vsqlplus_fig4": "V-SQL+ chi 2 huong (view tu dong + chon view); gd1/gd2 cung template + schema nhu vsql",
    "dinsql": "DIN-SQL (baseline Bang 3): schema linking -> phan loai -> sinh SQL theo loai; bo self-correction nhu paper",
    "dailsql": "DAIL-SQL (baseline Bang 3): schema CREATE TABLE + 7 vi du train BIRD chon 2 vong; 1 mau, khong bau chon nhu paper",
}
EXTRA = ["vsqlplus_fig4", "dinsql", "dailsql"]           # chay khi chon rieng (notebook: tick o tuong ung)
MAIN = ["vsql", "vsqlplus"]                               # so sanh chinh: V-SQL, V-SQL+ (DIN-SQL, DAIL-SQL: tick rieng)
ABLATIONS = ["vsqlplus_all", "vsqlplus_novote", "vsqlplus_novl", "vsqlplus_nofb", "vsqlplus_det"]
# phien ban cai dat cua tung phuong phap (ghi vao moi ban ghi). Doi cach cai dat thi tang so: ban ghi cu trong thu muc ket qua
# (vd predictions_vsql.jsonl cua ban V-SQL cu) bi tach ra old_predictions_*.jsonl va cham lai (cau tra loi LLM con trong cache).
IMPL = {"vsql": 6, "dinsql": 3, **{m: 2 for m in ["vsqlplus", "vsqlplus_fig4", "vsqlplus_all", "vsqlplus_novote", "vsqlplus_novl",
                                     "vsqlplus_nofb"]}}       # 13/11: Hinh 4/5 chinh lai dung tung chu -> prompt gd2 doi
# vsql: impl 6 = --vsql-views oracle (mac dinh tu 14/11); impl 5 = --vsql-views all (D' = moi view cua CSDL, nhu truoc)
VSQL_NOTE_ORACLE = NOTES["vsql"]
VSQL_NOTE_ALL = "V-SQL theo paper: view Hinh 3 theo JOIN dap an, D' = moi view cua CSDL, prompt Hinh 4 + Hinh 5"


def set_vsql_views(mode):
    """--vsql-views: oracle (impl 6) | all (impl 5, ket qua cu van dung lai duoc). Doi IMPL/NOTES de tach ban ghi va ghi
    dung mo ta trong summary.md."""
    IMPL["vsql"], NOTES["vsql"] = (5, VSQL_NOTE_ALL) if mode == "all" else (6, VSQL_NOTE_ORACLE)

# --------------------------------------------------------------------------- prompt
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
According to the "views schemas", "view query" and "relevant table schemas", restore the sql in view query to one used the original table query without explanation
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
    def __init__(self, db_id, db_dir, gold_sqls, args, tables_json=None):
        self.db_id, self.args = db_id, args
        self.path = str(Path(db_dir) / f"{db_id}.sqlite")
        self.schema = s = Schema(db_id, self.path, args.samples, infer_fk=not args.no_infer_fk)
        self.desc = Descriptions(db_dir, s)
        self.gold_sqls = gold_sqls
        self.tj = (tables_json or {}).get(db_id)
        self._cache = {}

    def lazy(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    # ---- view
    @property
    def oracle(self):
        """View cua V-SQL: theo JOIN dap an, kieu Hinh 3 (alias = ten bang, chi bang noi nhieu lan moi co alias, noi theo thu
        tu cot, bo cot id khoa ngoai da thay bang gia tri)."""
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
        if r.get("llm_error"):
            self.rec["llm_errors"] = self.rec.get("llm_errors", 0) + 1
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


# --------------------------------------------------------------------------- tien ich schema
def _value_prompt(ctx, t, c, fmt):
    """Cot text/date -> 'all possible values are [...]' (<=10) hoac 3 vi du.
    (Lay theo thu tu tu nhien de ket qua tai lap duoc.)"""
    if fmt not in ("text", "date", "datetime"):
        return None
    rows, err, _ = run_sql(ctx.path, f"SELECT DISTINCT {qi(c)} FROM {qi(t)} WHERE {qi(c)} IS NOT NULL LIMIT 11", 30)
    if err or not rows or not isinstance(rows[0][0], str) or len(rows[0][0]) >= 50:
        return None
    vals = [r[0] for r in rows]
    if len(vals) <= 10:
        return f"all possible values are {vals}"
    return f"example values are {vals[:3]}"


# --------------------------------------------------------------------------- V-SQL (paper)
def vsql_query(item, args):
    """{query} cua Hinh 4/5: cau hoi; evidence cua BIRD noi vao sau (--vsql-evidence query) hoac bo (none)."""
    e = (item.get("evidence") or "").strip()
    if args.evidence and args.vsql_evidence == "query" and e:
        return f"{item['question']}\n{e}"
    return item["question"]


class Render6:
    """Trinh bay schema kieu Bang 6 cua paper. extended=True (vsql, vsqlplus_fig4): them 2 cot `value_description` va
    `example_values` - paper khong quy dinh cach trinh bay schema trong prompt; them mo ta gia tri
    va "all possible values are [...]" / "example values are [...]". Ten cot can quote (co dau
    cach, ngoac, dau tru: `FRPM Count (K-12)`, `T-CHO`) ghi kem backtick, de LLM khong tu che ten (FRPM_Count_K_12)."""

    def __init__(self, ctx, extended=False):
        self.ctx, self.ext = ctx, extended

    def _examples(self, t, c):
        raw = self.ctx.desc.get(t, c).get("raw", {})
        vp = self.ctx.lazy(("valp", t, c), lambda: _value_prompt(self.ctx, t, c, raw.get("fmt", "")))
        if vp:
            return vp
        ex = self.ctx.schema.samples.get((t, c), [])[:3]
        return ("example values are " + str(list(ex))) if ex else ""

    def _rows(self, triples):
        """triples: [(ten_hien_thi, bang_nguon, cot_nguon, kieu)]"""
        out = []
        for shown, t, c, ctype in triples:
            m = self.ctx.desc.get(t, c)
            full = (m.get("full") or c) if shown.lower() == c.lower() else shown.replace("_", " ")
            row = [qi(shown) if self.ext else shown, full, m.get("desc", ""), m.get("fmt") or (ctype or "").lower()]
            if self.ext:
                row += [m.get("values", ""), self._examples(t, c)]
            out.append(row)
        return out

    def _head(self):
        return ("original_column_name | column_name | column_description | data_format"
                + (" | value_description | example_values" if self.ext else ""))

    def table(self, name):
        if not self.ext:
            return table6_table(self.ctx.schema, self.ctx.desc, name)
        t = self.ctx.schema.tables[name]
        fks = [f"{qi(name)}.{qi(c)} -> {qi(fk.ref_table)}.{qi(r)}" for fk in t.fks for c, r in zip(fk.cols, fk.ref_cols)]
        rows = self._rows([(c.name, name, c.name, c.type) for c in t.columns])
        return "\n".join([f"# table: {qi(name)}", self._head()] + [" | ".join(r) for r in rows]
                         + (["foreign keys: " + "; ".join(fks)] if fks else []))

    def view(self, v):
        if not self.ext:
            return table6_view(v, self.ctx.desc)
        rows = self._rows([(c.name, c.table, c.col, c.type) for c in v.cols])
        return "\n".join([f"# view: {v.name}", self._head()] + [" | ".join(r) for r in rows])


def vsql_schema(ctx, item, mode="oracle"):
    """D' cua V-SQL -> (views, bang goc).
    all: moi view cua CSDL + bang goc khong bi view thay the (impl 5).
    oracle: chu thich Hinh 4 ("db_schema represents the description of tables related to the query, retrieved from a
    database") va muc 6 ("retrieve the correct view description based on the user's query") -> prompt chi chua view lien
    quan toi cau hoi. Paper khong noi cach truy hoi; o day dung SQL dap an (oracle, can tren): view co bang goc (base) nam
    trong SQL dap an + bang con lai cua D' ma dap an dung + bang dap an chua view nao da chon phu (vd bang tra cuu dung rieng)."""
    views = ctx.oracle
    tabs = V.leftover_tables(ctx.schema, views)
    if mode == "all":
        return views, tabs
    gold = tables_in_sql(item["SQL"], ctx.schema)
    views = [v for v in views if v.base in gold]
    tabs = [t for t in tabs if t in gold]
    covered = set(tabs).union(*[v.source_tables() for v in views])
    tabs += [t for t in ctx.schema.tables if t in gold and t not in covered]
    return views, tabs


def run_vsql(item, ctx, ask, rec, args):
    """V-SQL: {relevant_db_schema} = D' cua CSDL = moi view (thiet ke theo JOIN dap an) + bang goc khong bi view thay the
    (chi bang goc cua view va bang tra cuu id + 1 cot gia tri nhu colour/gender moi bien mat, Hinh 1(A)); trinh bay Bang 6 mo
    rong; prompt Hinh 4; giai doan 2 luon chay voi prompt Hinh 5, "relevant table schemas" = bang ma dummy SQL dung cot (muc
    4.5). Khong co buoc truy hoi / chon view."""
    views, tabs = vsql_schema(ctx, item, getattr(args, "vsql_views", "oracle"))
    r6 = Render6(ctx, extended=True)
    parts = [r6.view(v) for v in views] + [r6.table(t) for t in tabs]
    rec["n_objects"] = len(views) + len(tabs)
    rec["schema_tables"] = sorted(set(tabs).union(*[v.source_tables() for v in views]))
    p1 = P_VSQL_1.format(relevant_db_schema="\n\n".join(parts), query=vsql_query(item, args))
    dummy = rec["dummy_sql"] = clean(ask(p1, "vsql_s1"))
    # giai doan 2: bang goc ma dummy SQL truy van truc tiep (FROM/JOIN, ke ca bang bi an khoi D') cung dua vao "relevant
    # table schemas"
    direct = tables_in_sql(dummy, ctx.schema) if dummy else set()
    return restore(ctx, item, ask, rec, dummy, views, [t for t in ctx.schema.tables if t in direct], "vsql_s2", args, r6,
                   always=True, narrow=True)


def restore(ctx, item, ask, rec, dummy, views, tabs, stage, args, r6=None, always=False, narrow=False):
    """Giai doan 2 cua paper (Hinh 5): LLM khoi phuc dummy SQL tren view ve SQL tren bang goc.
    always=False (V-SQL+): dummy SQL khong dung view thi giu nguyen. always=True (V-SQL): luon goi Hinh 5 nhu paper (dummy SQL
    khong duoc thuc thi; Hinh 5 con dua cu phap {db_type} va khoi dinh dang dau ra).
    narrow=True (V-SQL, muc 4.5): "relevant table schemas" chi gom bang ma dummy SQL thuc su dung cot qua quy tac anh xa cua
    view (vi du cua paper: v_superhero voi eye/hair/skin colour, gender, publisher_name -> chon gender, colour, publisher;
    khong co race, alignment), khong phai moi bang cua view."""
    used = [v for v in views if references(dummy, v.name)]
    rec["views_used"] = [v.name for v in used]
    if not dummy or not (used or always):
        return dummy                            # dummy SQL khong dung view -> da la SQL tren bang goc
    tset = set().union(*[v.tables_for(V.needed_columns(dummy, v) if narrow else None) for v in used])
    tset |= {t for t in tabs if references(dummy, t)}
    p2 = P_VSQL_2.format(db_type="SQLite", view_schemas="\n\n".join(v.ddl() for v in used), query=vsql_query(item, args),
                         dummy_sql=dummy,
                         table_schemas="\n\n".join((r6 or Render6(ctx)).table(t) for t in ctx.schema.tables if t in tset))
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
    for t, c in sorted(colhits):                    # sorted: thu tu cong diem co dinh -> xep hang tai lap duoc
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
    parts = [px.text[o] for o in order]
    parts += [px.text[t] if t in px.text else ctx.ddl(t) for t in extra_tables if t not in order]
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
    fig4 = variant == "fig4"
    r6 = Render6(ctx, extended=True)        # fig4: cung cach trinh bay schema voi vsql

    def make_prompt(o, extra=(), note=""):
        """fig4: template Hinh 4 + schema Bang 6 y nhu V-SQL; chi khac tap view/bang dua vao (huong 1 + huong 2).
        Gia tri khop chi dung de xep hang view, khong ghi vao prompt; schema lai chi them bang goc, khong them ghi chu."""
        if fig4:
            order = [x for x in px.names if x in o]
            parts = [r6.view(px.view[x]) if x in px.view else r6.table(x) for x in order]
            parts += [r6.table(t) for t in extra if t not in order]
            return P_VSQL_1.format(relevant_db_schema="\n\n".join(parts), query=vsql_query(item, args))
        return _plus_prompt(px, ctx, o, item, links, args, extra_tables=extra, note=note)

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
            p = make_prompt(cand)
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
    prompt = make_prompt(objs)
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
        if not add and (fig4 or not where):
            break
        note += f"\n# note\nYour previous query failed: `{name}` does not exist where you used it."
        if where:
            note += f" It exists as: {', '.join(where)}."
        if add:
            note += f" The original table(s) {', '.join(add)} are added to the schema; join them on their key columns if needed."
        note += "\n"
        rec["fallback"].append(dict(error=err, added=add, where=where))
        prompt = make_prompt(objs, extra, note)
        dummy = clean(ask(prompt, f"plus_fb{k}"))
    rec["dummy_sql"] = dummy
    if variant == "det":
        final, rec["views_used"] = V.unfold(dummy, px.views)       # bien the: giai ma tat dinh (khong thuoc de xuat)
    else:
        # giai doan 2 giu nguyen nhu paper (Hinh 5): V-SQL+ chi doi cach sinh view va cach chon view
        final = restore(ctx, item, ask, rec, dummy, px.views, list(ctx.schema.tables), "plus_s2", args, r6 if fig4 else None)
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
    if method in IMPL:
        rec["impl"] = IMPL[method]
    ask = Asker(llm, rec, item["uid"])
    if method == "vsql":
        final = run_vsql(item, ctx, ask, rec, args)
    elif method == "dinsql":
        final = B.run_din(item, ctx, ask, rec, args)
    elif method == "dailsql":
        final = B.run_dail(item, ctx, ask, rec, args)
    elif method.startswith("vsqlplus"):
        final = run_plus(item, ctx, ask, rec, args, llm, method[len("vsqlplus_"):] if "_" in method else "")
    else:
        raise ValueError(method)
    rec["final_sql"] = final
    rec["coverage"] = ctx.coverage(rec.get("schema_tables", []), tables_in_sql(item["SQL"], ctx.schema))
    add_stage_info(rec, item, ctx)
    return rec


def stage_views(method, ctx):
    """View ma SQL nhap (giai doan 1) cua phuong phap dung."""
    if method.startswith("vsqlplus"):
        return ctx.auto
    return {"vsql": ctx.oracle}[method]


def add_stage_info(rec, item, ctx):
    """Phan tich (khong goi LLM): stage1_sql = SQL nhap giai doan 1 mo rong tat dinh ve bang goc (view -> CTE), de do
    rieng giai doan 1 va giai doan 2.
    gold_tables = so bang trong SQL dap an (de xem diem manh/yeu theo do phuc tap)."""
    rec["gold_tables"] = len(tables_in_sql(item["SQL"], ctx.schema))
    if rec["method"] == "dinsql":                   # DIN-SQL: mot lan sinh SQL, khong co ban nhap de tach giai doan
        rec["stage1_sql"] = None
        return rec
    if rec["method"] == "dailsql":                  # DAIL-SQL: "giai doan 1" = SQL vong 1 (truoc khi chon lai vi du theo khung SQL)
        rec["stage1_sql"] = rec.get("dail_pre_sql") or ""
        return rec
    dummy = rec.get("dummy_sql") or ""
    vs = stage_views(rec["method"], ctx)
    if vs is None:
        rec["stage1_sql"] = clean(dummy)
    else:
        rec["stage1_sql"] = V.unfold(dummy, vs)[0] if dummy else ""
    return rec


def score(rec, gold_rows, gold_seconds, db_path, timeout):
    rows, err, sec = run_sql(db_path, rec["final_sql"], timeout)
    rec["exec_seconds"], rec["gold_seconds"], rec["error"] = sec, gold_seconds, err
    rec["correct"] = bool(err is None and gold_rows is not None and set(rows) == set(gold_rows))
    if rec.get("stage1_sql") is not None:
        score_stage1(rec, gold_rows, db_path, timeout)
    if err is not None:
        rec["outcome"] = classify_error(err)
    elif rec["correct"]:
        rec["outcome"] = "correct"
    else:
        rec["outcome"] = "wrong_empty" if not rows else "wrong_result"
    return rec


def score_stage1(rec, gold_rows, db_path, timeout):
    if rec["stage1_sql"] == rec.get("final_sql"):
        rec["stage1_correct"] = rec["correct"]
        return rec
    rows, err, _ = run_sql(db_path, rec["stage1_sql"], timeout) if rec["stage1_sql"] else (None, "no_sql", 0)
    rec["stage1_correct"] = bool(err is None and gold_rows is not None and set(rows) == set(gold_rows))
    return rec


__all__ = ["DbCtx", "run_item", "set_vsql_views", "vsql_schema", "score", "add_stage_info", "score_stage1", "NOTES", "MAIN", "ABLATIONS", "IMPL", "load_tables_json"]
