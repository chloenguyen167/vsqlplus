"""Cau truc view dung chung (View/VCol/Join), kiem tra so dong view, giai ma tat dinh view -> bang goc (CTE).
Cach dung view: xem vsql/autoview.py."""
import re
from dataclasses import dataclass, field

from .db import qi, references, run_sql, strip_strings


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
    origin: str                      # oracle (theo JOIN dap an) | auto (tu dong tu khoa ngoai)
    cols: list = field(default_factory=list)
    joins: list = field(default_factory=list)
    row_preserving: bool = True      # so dong view == so dong bang goc
    verified: str = "unverified"
    paper: bool = False              # view kieu Hinh 3 cua paper: khong viet "AS alias" khi alias trung ten bang

    def source_tables(self):
        return {self.base} | {j.table for j in self.joins}

    def select_sql(self, needed=None):
        """needed: tap ten cot (lower) cua bang noi can giu; None = giu tat ca."""
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
            if self.paper:                          # Hinh 3: `left join colour eye_colour`, `left join gender`
                alias = "" if j.alias == j.table else f" {qi(j.alias)}"
            else:
                alias = f" AS {qi(j.alias)}"
            sql += f" LEFT JOIN {qi(j.table)}{alias} ON {on}"
        return sql

    def ddl(self):
        return f"CREATE VIEW {qi(self.name)} AS {self.select_sql()};"

def _colname(prefix, col):
    pl, cl = prefix.lower(), col.lower()
    if cl.startswith(pl):
        return col
    if pl.endswith(cl):
        return prefix
    return f"{prefix}_{col}"


def _reach(schema, root, S):
    seen, stack = {root}, [root]
    while stack:
        t = stack.pop()
        for fk in schema.tables[t].fks:
            if fk.ref_table in S and fk.ref_table not in seen and schema.safe_fk(fk):
                seen.add(fk.ref_table)
                stack.append(fk.ref_table)
    return seen


def validate(schema, views, timeout=60):
    """Kiem tra tu dong: view N-1 phai co so dong bang bang goc."""
    for v in views:
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


# --------------------------------------------------------------------------- giai ma tat dinh view -> bang goc
_STAR = re.compile(r"(?:\bselect\b|,|\.|\bdistinct\b)\s*\*", re.I)


def needed_columns(sql, view):
    """Tap (bao thu) cac cot cua view ma SQL co the dung. None = can giu tat ca."""
    if not view.row_preserving:
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
