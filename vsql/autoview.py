"""Sinh view theo kieu bai bao V-SQL (Hinh 3): moi bang co khoa ngoai -> mot view `v_<bang>` = bang do LEFT JOIN cac bang
cha theo chieu N-1, ten cot sach (`eye_colour`, `publisher_name`) thay vi ten co tien to.

Dung cho ca hai noi:
  * V-SQL (tai hien paper): `oracle_views` - chi tao view cho cac bang goc xuat hien trong phep JOIN cua SQL dap an
    (paper: "we referred to the join operations in the ground truth SQL ... and manually designed the view").
  * V-SQL+ (cai tien): `auto_views` - tu dong tu do thi khoa ngoai, khong nhin dap an.

Dam bao dung dan:
  * chi noi theo khoa ngoai co cot duoc tham chieu la DUY NHAT (N-1) -> LEFT JOIN khong nhan ban dong;
  * kiem tra lai bang SQL: COUNT(*) cua view == COUNT(*) cua bang goc (`views.validate`);
  * moi cot cua view nho nguon (bang, cot) -> mo ta cot, gia tri mau, va viet lai tat dinh view -> bang goc.
"""
import re

from . import views as V
from .db import qi, tables_in_sql, _show
from .meta import column_comment

_SUFFIX = re.compile(r"(_id|_ID|Id|ID|_code|_Code|_key)$")


def _role(fk, n_same):
    """Ten vai tro cua khoa ngoai: eye_colour_id -> eye_colour; link_to_major -> major; publisher_id -> publisher."""
    if len(fk.cols) != 1:
        return fk.ref_table
    c = fk.cols[0]
    r = _SUFFIX.sub("", c).rstrip("_")
    if not r or r.lower() == fk.ref_cols[0].lower():
        r = fk.ref_table
    if n_same == 1 and r.lower().startswith("link_to_"):
        r = r[len("link_to_"):] or fk.ref_table
    return r


class _Builder:
    def __init__(self, schema, base, name, origin):
        self.s = schema
        self.v = V.View(name, base, origin)
        self.names = set()
        self.aliases = {base.lower()}
        for c in schema.tables[base].columns:
            self._add(c.name, base, base, c)

    def _add(self, name, alias, table, c):
        n, i = name, 2
        while n.lower() in self.names:
            n, i = f"{name}_{i}", i + 1
        self.names.add(n.lower())
        self.v.cols.append(V.VCol(n, alias, table, c.name, c.type))

    def join(self, parent_alias, fk, role, force_role):
        p = fk.ref_table
        a, i = role, 2
        while a.lower() in self.aliases or a.lower() in {t.lower() for t in self.s.tables if t != p}:
            a, i = f"{role}_{i}", i + 1
        self.aliases.add(a.lower())
        self.v.joins.append(V.Join(a, p, parent_alias, list(zip(fk.cols, fk.ref_cols))))
        cols = [c for c in self.s.tables[p].columns if c.name not in fk.ref_cols]
        for c in cols:
            plain_ok = not force_role and c.name.lower() not in self.names
            if plain_ok:
                nm = c.name
            elif len(cols) == 1:
                nm = role                                   # colour.colour qua eye_colour_id -> eye_colour
            else:
                nm = V._colname(role, c.name)               # vd away_team + team_long_name -> away_team_team_long_name
            self._add(nm, a, p, c)
        return a


def build_view(schema, base, depth=2, allowed=None, max_cols=60, origin="auto", lookup_cols=4):
    """View N-1 cho bang `base`; allowed: chi noi toi cac bang trong tap nay (None = moi bang).
    Tu muc noi thu 2, view tu dong chi noi bang tra cuu co <= lookup_cols cot (vd colour, gender)."""
    b = _Builder(schema, base, "v_" + base, origin)

    def expand(alias, table, d, path):
        fks = [fk for fk in schema.tables[table].fks
               if fk.ref_table not in path and (allowed is None or fk.ref_table in allowed) and schema.safe_fk(fk)]
        per_parent = {}
        for fk in fks:
            per_parent[fk.ref_table] = per_parent.get(fk.ref_table, 0) + 1
        nexts = []
        for fk in fks:
            p = fk.ref_table
            extra = len(schema.tables[p].columns) - len(fk.ref_cols)
            if len(b.v.cols) + extra > max_cols:
                continue
            if alias != base and allowed is None and extra > lookup_cols:
                continue                                    # muc 2 tro di: chi noi bang tra cuu nho (giu view gon)
            n_same = per_parent[p]
            a = b.join(alias, fk, _role(fk, n_same), force_role=n_same > 1)
            nexts.append((a, p))
        if d > 1:
            for a, p in nexts:
                expand(a, p, d - 1, path | {p})

    expand(base, base, depth, {base})
    return b.v if b.v.joins else None


def auto_views(schema, depth=2, max_cols=60):
    """V-SQL+: mot view cho moi bang co khoa ngoai N-1, khong nhin dap an."""
    return [v for v in (build_view(schema, t, depth, None, max_cols, "auto") for t in schema.tables) if v]


def oracle_views(schema, gold_sqls, max_cols=10 ** 6):
    """Tai hien paper: chi tao view cho cac bang 'goc' cua cac mau JOIN trong SQL dap an (tu do moi bang con lai deu
    toi duoc theo chieu N-1), noi toi cac bang cha xuat hien trong cac mau do. Mau JOIN co quan he 1-N (khong co bang
    goc) khong tao view: paper khong mo ta view nhan ban dong; cac bang do van co mat trong schema."""
    allowed = {}
    for sql in gold_sqls:
        S = tables_in_sql(sql, schema)
        if len(S) < 2:
            continue
        roots = [t for t in sorted(S) if V._reach(schema, t, S) == S]
        if roots:
            allowed.setdefault(roots[0], set()).update(S)
    out = []
    for root, S in sorted(allowed.items()):
        v = build_view(schema, root, depth=len(S), allowed=S, max_cols=max_cols, origin="oracle")
        if v:
            out.append(v)
    return out


def visible_tables(schema, views):
    """Bang goc van hien trong schema: moi bang KHONG phai bang goc cua mot view (view thay the bang goc cua no;
    bang tra cuu / bang cha van giu de truy van truc tiep, vd dem so khach hang)."""
    bases = {v.base for v in views}
    return [t for t in schema.tables if t not in bases]


def describe(view, schema, desc, n_samples=3, show_source=True):
    """Mo ta view cho prompt: nhu CREATE TABLE, moi cot kem mo ta va gia tri mau; show_source: them nguon goc cot
    (bang.cot qua khoa ngoai nao). V-SQL goc an nguon goc (view thay hoan toan bang); V-SQL+ hien de khop voi evidence."""
    lines = []
    for c in view.cols:
        s = f"  {qi(c.name)} {c.type}".rstrip() + ","
        bits = []
        if show_source and c.alias != view.base:
            j = next(j for j in view.joins if j.alias == c.alias)
            bits.append(f"{c.table}.{c.col} via {view.base if j.parent == view.base else j.parent}.{j.on[0][0]}")
        # cot lay tu bang cha: mo ta ngan hon (bang cha thuong cung co mat trong schema voi mo ta day du)
        com = column_comment(schema, desc, c.table, c.col, n_samples, 200 if c.alias == view.base else 80)
        if com:
            bits.append(com)
        if bits:
            s += "  -- " + "; ".join(bits)
        lines.append(s)
    return (f"CREATE VIEW {qi(view.name)} (  -- one row per row of table {view.base}\n"
            + "\n".join(lines) + "\n);")


def column_entries(view, schema, desc, n_samples=3):
    """[(ten_cot_view, bang_nguon, cot_nguon, van_ban)] cho truy hoi muc cot."""
    out = []
    for c in view.cols:
        ex = schema.samples.get((c.table, c.col), [])[:n_samples]
        txt = " ".join([c.name, c.table, c.col, desc.text(c.table, c.col) if desc else ""]
                       + [_show(x) for x in ex if isinstance(x, str)])
        out.append((c.name, c.table, c.col, txt))
    return out
