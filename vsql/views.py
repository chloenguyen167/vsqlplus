"""Sinh view (kieu paper / tu dong tu do thi khoa ngoai / thu cong) va viet lai tat dinh view -> bang goc."""
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .db import connect, qi, references, run_sql, strip_strings, tables_in_sql, _show


@dataclass
class VCol:
    name: str
    alias: str      # alias cua bang nguon trong view (None voi view thu cong)
    table: str
    col: str
    type: str = ""


@dataclass
class Join:
    alias: str
    table: str
    parent: str     # alias cha
    on: list        # [(cot_cha, cot_bang_nay)]


@dataclass
class View:
    name: str
    base: str
    origin: str                      # oracle | oracle_fan | auto | manual
    cols: list = field(default_factory=list)
    joins: list = field(default_factory=list)
    row_preserving: bool = True      # so dong view == so dong bang goc
    verified: str = "unverified"
    raw_sql: str = None
    raw_sources: set = None

    def source_tables(self):
        if self.raw_sql:
            return set(self.raw_sources)
        return {self.base} | {j.table for j in self.joins}

    def select_sql(self, needed=None):
        """needed: tap ten cot (lower) cua bang noi can giu; None = giu tat ca."""
        if self.raw_sql:
            return self.raw_sql
        cols = [c for c in self.cols if needed is None or c.alias == self.base or c.name.lower() in needed]
        keep = {c.alias for c in cols}
        parent = {j.alias: j.parent for j in self.joins}
        for a in list(keep):                       # giu ca cac phep noi trung gian
            while a in parent:
                a = parent[a]
                keep.add(a)
        sel = ", ".join(f"{qi(c.alias)}.{qi(c.col)} AS {qi(c.name)}" for c in cols)
        sql = f"SELECT {sel} FROM {qi(self.base)}"
        for j in self.joins:
            if needed is not None and j.alias not in keep:
                continue
            on = " AND ".join(f"{qi(j.parent)}.{qi(p)} = {qi(j.alias)}.{qi(c)}" for p, c in j.on)
            sql += f" LEFT JOIN {qi(j.table)} AS {qi(j.alias)} ON {on}"
        return sql

    def ddl(self):
        return f"CREATE VIEW {qi(self.name)} AS {self.select_sql()};"

    def describe(self, schema, n_samples=3):
        """Mo ta view cho prompt giai doan 1: nhu mot bang rong, kem nguon goc cot."""
        note = f"one row per row of {self.base}" if self.row_preserving else \
            "WARNING: joins one-to-many relations, rows of the base table may repeat"
        lines = []
        for c in self.cols:
            s = f"  {qi(c.name)} {c.type}".rstrip() + ","
            bits = []
            if c.alias is not None and c.alias != self.base:
                bits.append(f"from {c.table}.{c.col}")
            ex = schema.samples.get((c.table, c.col), [])[:n_samples] if c.table else []
            if ex:
                bits.append("e.g. " + ", ".join(_show(v) for v in ex))
            if bits:
                s += "  -- " + "; ".join(bits)
            lines.append(s)
        return f"VIEW {qi(self.name)} (  -- {note}\n" + "\n".join(lines) + "\n);"


# --------------------------------------------------------------------------- xay view co cau truc
class _Builder:
    def __init__(self, schema, base, name, origin):
        self.s = schema
        self.v = View(name, base, origin)
        self.names = set()
        self.aliases = {base.lower()}
        for c in schema.tables[base].columns:
            self._add_col(c.name, base, base, c)

    def _add_col(self, name, alias, table, c):
        n, i = name, 2
        while n.lower() in self.names:
            n, i = f"{name}_{i}", i + 1
        self.names.add(n.lower())
        self.v.cols.append(VCol(n, alias, table, c.name, c.type))

    def join(self, parent_alias, table, on, prefix, skip=()):
        a, i = prefix, 2
        while a.lower() in self.aliases:
            a, i = f"{prefix}_{i}", i + 1
        self.aliases.add(a.lower())
        self.v.joins.append(Join(a, table, parent_alias, list(on)))
        for c in self.s.tables[table].columns:
            if c.name in skip:
                continue
            self._add_col(_colname(prefix, c.name), a, table, c)
        return a


def _fk_prefix(fk, parent_prefix):
    if len(fk.cols) == 1:
        p = re.sub(r"(_id|_ID|Id|ID|_code|_key)$", "", fk.cols[0])
        if not p or p == fk.cols[0] and fk.cols[0].lower() == fk.ref_cols[0].lower():
            p = fk.ref_table
    else:
        p = fk.ref_table
    return f"{parent_prefix}_{p}" if parent_prefix else p


def _colname(prefix, col):
    pl, cl = prefix.lower(), col.lower()
    if cl.startswith(pl):
        return col
    if pl.endswith(cl):
        return prefix
    return f"{prefix}_{col}"


def build_n1_view(schema, base, depth=2, allowed=None, max_cols=60, origin="auto"):
    """View = bang goc LEFT JOIN cac bang cha theo chieu N-1 (giu nguyen so dong)."""
    b = _Builder(schema, base, "v_" + base, origin)

    def expand(alias, table, prefix, d, path):
        for fk in schema.tables[table].fks:
            p = fk.ref_table
            if p in path or (allowed is not None and p not in allowed) or not schema.safe_fk(fk):
                continue
            if len(b.v.cols) + len(schema.tables[p].columns) > max_cols:
                continue
            pfx = _fk_prefix(fk, prefix)
            a = b.join(alias, p, zip(fk.cols, fk.ref_cols), pfx, skip=fk.ref_cols)
            if d > 1:
                expand(a, p, pfx, d - 1, path | {p})

    expand(base, base, "", depth, {base})
    return b.v if b.v.joins else None


def auto_views(schema, depth=2, max_cols=60):
    """Cai tien 2: sinh view tu dong tu do thi khoa ngoai, khong nhin dap an."""
    out = []
    for t in schema.tables:
        v = build_n1_view(schema, t, depth, None, max_cols, "auto")
        if v:
            out.append(v)
    return out


def _reach(schema, root, S):
    seen, stack = {root}, [root]
    while stack:
        t = stack.pop()
        for fk in schema.tables[t].fks:
            if fk.ref_table in S and fk.ref_table not in seen and schema.safe_fk(fk):
                seen.add(fk.ref_table)
                stack.append(fk.ref_table)
    return seen


def _fan_view(schema, S):
    """View cho mau JOIN co quan he 1-N (paper khong phan tich ngu nghia nay): co the nhan ban dong."""
    S = sorted(S)
    start = max(S, key=lambda t: sum(1 for fk in schema.tables[t].fks if fk.ref_table in S))
    b = _Builder(schema, start, "v_" + "_".join(S), "oracle_fan")
    inc = {start: start}
    progress = True
    while progress and len(inc) < len(S):
        progress = False
        for x in list(inc):
            for fk in schema.tables[x].fks:               # x la con, noi sang cha
                n = fk.ref_table
                if n in S and n not in inc:
                    inc[n] = b.join(inc[x], n, zip(fk.cols, fk.ref_cols), n, skip=fk.ref_cols)
                    if not schema.safe_fk(fk):
                        b.v.row_preserving = False
                    progress = True
            for n in S:                                    # n la con cua x: quan he 1-N
                if n in inc:
                    continue
                for fk in schema.tables[n].fks:
                    if fk.ref_table == x:
                        inc[n] = b.join(inc[x], n, zip(fk.ref_cols, fk.cols), n, skip=fk.cols)
                        b.v.row_preserving = False
                        progress = True
                        break
    return b.v if len(inc) == len(S) else None


def oracle_views(schema, gold_sqls, max_fan=3):
    """Tai hien cach lam cua paper: thiet ke view dua tren cac phep JOIN trong SQL dap an
    cua chinh tap danh gia (RO RI DAP AN - dung de tai hien, khong phai de trien khai)."""
    allowed, fan = {}, Counter()
    for sql in gold_sqls:
        S = tables_in_sql(sql, schema)
        if len(S) < 2:
            continue
        roots = [t for t in sorted(S) if _reach(schema, t, S) == S]
        if roots:
            allowed.setdefault(roots[0], set()).update(S)
        else:
            fan[frozenset(S)] += 1
    out = []
    for root, S in sorted(allowed.items()):
        v = build_n1_view(schema, root, depth=len(S), allowed=S, max_cols=10 ** 6, origin="oracle")
        if v:
            out.append(v)
    names = {v.name for v in out}
    for S, _ in fan.most_common(max_fan):
        v = _fan_view(schema, S)
        if v and v.name not in names:
            out.append(v)
            names.add(v.name)
    return out


_CV = re.compile(r"CREATE\s+VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"\[]?(\w+)[`\"\]]?\s+AS\s+(.*?)(?=;|\Z)", re.I | re.S)


def manual_views(schema, path):
    """View viet tay: file .sql gom cac lenh CREATE VIEW ten AS SELECT ...;"""
    out = []
    for name, body in _CV.findall(Path(path).read_text(encoding="utf-8")):
        body = body.strip()
        v = View(name, "", "manual", raw_sql=body, raw_sources=tables_in_sql(body, schema), row_preserving=False)
        con = connect(schema.path)
        cur = con.execute(f"SELECT * FROM ({body}) LIMIT 0")
        v.cols = [VCol(d[0], None, None, d[0]) for d in cur.description]
        con.close()
        out.append(v)
    return out


def validate(schema, views, timeout=60):
    """Kiem tra tu dong: view N-1 phai co so dong bang bang goc."""
    for v in views:
        if v.raw_sql:
            v.verified = "manual"
            continue
        a, e1, _ = run_sql(schema.path, f"SELECT COUNT(*) FROM ({v.select_sql()})", timeout)
        b, e2, _ = run_sql(schema.path, f"SELECT COUNT(*) FROM {qi(v.base)}", timeout)
        if e1 or e2:
            v.verified = "error: " + str(e1 or e2)
        elif a[0][0] == b[0][0]:
            v.verified = "rows_equal"
        else:
            v.verified = f"rows_differ({a[0][0]} vs {b[0][0]})"
            v.row_preserving = False
    return views


def leftover_tables(schema, views):
    used = set().union(*[v.source_tables() for v in views]) if views else set()
    return [t for t in schema.tables if t not in used]


# --------------------------------------------------------------------------- cai tien 1: viet lai tat dinh
_STAR = re.compile(r"(?:\bselect\b|,|\.|\bdistinct\b)\s*\*", re.I)


def needed_columns(sql, view):
    """Tap (bao thu) cac cot cua view ma SQL co the dung. None = can giu tat ca."""
    if view.raw_sql or not view.row_preserving:
        return None            # cat phep noi 1-N se doi so dong -> khong cat
    s = strip_strings(sql)
    if _STAR.search(s):
        return None
    low = s.lower()
    need = set()
    for c in view.cols:
        n = c.name.lower()
        if re.fullmatch(r"\w+", n):
            hit = re.search(r"(?<!\w)" + re.escape(n) + r"(?!\w)", low)
        else:
            hit = n in low
        if hit:
            need.add(n)
    return need


def unfold(sql, views, prune=True):
    """Chen dinh nghia view thanh CTE truoc dummy SQL. Tat dinh, khong goi LLM.
    prune=True: bo cac LEFT JOIN N-1 khong dung den (an toan vi khong doi so dong)."""
    used = [v for v in views if references(sql, v.name)]
    if not used:
        return sql, []
    ctes = ", ".join(f"{qi(v.name)} AS ({v.select_sql(needed_columns(sql, v) if prune else None)})" for v in used)
    m = re.match(r"\s*WITH\s+(RECURSIVE\s+)?", sql, re.I)
    if m:
        return f"WITH {m.group(1) or ''}{ctes}, {sql[m.end():]}", [v.name for v in used]
    return f"WITH {ctes} {sql.strip()}", [v.name for v in used]
