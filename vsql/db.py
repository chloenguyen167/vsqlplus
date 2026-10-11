"""Doc schema SQLite, khoa ngoai, gia tri mau; thuc thi SQL co gioi han thoi gian."""
import re
import sqlite3
import time
import urllib.parse
from dataclasses import dataclass, field

_SIMPLE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_KEYWORDS = set("""add all alter and as asc between by case cast check column commit create cross default
delete desc distinct drop else end except exists from full group having in index inner insert intersect
into is join key left like limit match natural not null offset on or order outer primary references
right select set table then to transaction union unique update using values when where with""".split())


def qi(name):
    """Quote dinh danh bang backtick (khong dung nhay kep: SQLite se ngam hieu thanh chuoi neu cot khong ton tai)."""
    if _SIMPLE.match(name) and name.lower() not in _KEYWORDS:
        return name
    return "`" + name.replace("`", "") + "`"


def connect(path):
    con = sqlite3.connect("file:" + urllib.parse.quote(str(path)) + "?mode=ro", uri=True)
    con.text_factory = lambda b: b.decode("utf-8", errors="ignore")
    return con


def run_sql(path, sql, timeout=30.0):
    """Tra ve (rows | None, error | None, seconds)."""
    if not sql or not sql.strip():
        return None, "no_sql", 0.0
    con = connect(path)
    t0 = time.perf_counter()
    deadline = t0 + timeout
    con.set_progress_handler(lambda: 1 if time.perf_counter() > deadline else 0, 20000)
    try:
        rows = con.execute(sql).fetchall()
        return rows, None, time.perf_counter() - t0
    except Exception as e:  # noqa: BLE001 - moi loi thuc thi deu la ket qua can ghi nhan
        msg = str(e)
        if "interrupted" in msg:
            msg = "timeout"
        return None, f"{type(e).__name__}: {msg}", time.perf_counter() - t0
    finally:
        con.close()


def classify_error(err):
    if err is None:
        return None
    m = err.lower()
    if m == "no_sql":
        return "no_sql"
    if "no such column" in m:
        return "schema_column"
    if "no such table" in m:
        return "schema_table"
    if "ambiguous column" in m:
        return "ambiguous_column"
    if "timeout" in m:
        return "timeout"
    if "syntax error" in m or "incomplete input" in m or "one statement" in m:
        return "syntax"
    return "other_exec"


@dataclass
class Column:
    name: str
    type: str
    pk: bool


@dataclass
class FK:
    table: str
    cols: tuple
    ref_table: str
    ref_cols: tuple
    source: str = "declared"


@dataclass
class Table:
    name: str
    columns: list
    pk: list
    fks: list = field(default_factory=list)

    def col(self, name):
        for c in self.columns:
            if c.name.lower() == name.lower():
                return c
        return None


class Schema:
    def __init__(self, db_id, path, n_samples=3, infer_fk=False):
        self.db_id, self.path = db_id, str(path)
        self.tables = {}
        self.samples = {}
        self._unique = {}
        con = connect(path)
        names = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for t in names:
            info = con.execute(f"PRAGMA table_info({qi(t)})").fetchall()
            cols = [Column(r[1], (r[2] or "").upper(), bool(r[5])) for r in info]
            pk = [r[1] for r in sorted((r for r in info if r[5]), key=lambda r: r[5])]
            self.tables[t] = Table(t, cols, pk)
        lower = {t.lower(): t for t in self.tables}
        for t in names:
            groups = {}
            for r in con.execute(f"PRAGMA foreign_key_list({qi(t)})"):
                groups.setdefault(r[0], []).append(r)
            for rows in groups.values():
                rows.sort(key=lambda r: r[1])
                ref = lower.get((rows[0][2] or "").lower())
                if ref is None:
                    continue
                cols = tuple(r[3] for r in rows)
                rcols = tuple(r[4] for r in rows)
                if any(c is None for c in rcols):
                    rcols = tuple(self.tables[ref].pk)
                if len(rcols) != len(cols) or not rcols:
                    continue
                # chuan hoa hoa/thuong theo ten cot that
                fix = lambda tb, c: (self.tables[tb].col(c).name if self.tables[tb].col(c) else None)
                cols = tuple(fix(t, c) for c in cols)
                rcols = tuple(fix(ref, c) for c in rcols)
                if None in cols or None in rcols:
                    continue
                # BIRD co FK khai bao trung (vd yearmonth -> customers 2 lan): bo ban trung
                if any((f.cols, f.ref_table, f.ref_cols) == (cols, ref, rcols) for f in self.tables[t].fks):
                    continue
                self.tables[t].fks.append(FK(t, cols, ref, rcols))
        if n_samples:
            for t in names:
                for c in self.tables[t].columns:
                    try:
                        rows = con.execute(
                            f"SELECT DISTINCT {qi(c.name)} FROM {qi(t)} WHERE {qi(c.name)} IS NOT NULL LIMIT {n_samples}"
                        ).fetchall()
                    except Exception:  # noqa: BLE001
                        rows = []
                    self.samples[(t, c.name)] = [r[0] for r in rows]
        con.close()
        if infer_fk:
            self._infer_fks()

    # ---- tinh duy nhat cua khoa tham chieu: dieu kien de LEFT JOIN khong nhan ban dong
    def is_unique(self, table, cols):
        key = (table, tuple(cols))
        if key not in self._unique:
            cl = ", ".join(qi(c) for c in cols)
            rows, err, _ = run_sql(
                self.path, f"SELECT 1 FROM {qi(table)} GROUP BY {cl} HAVING COUNT(*) > 1 LIMIT 1", 60)
            self._unique[key] = (err is None and not rows)
        return self._unique[key]

    def safe_fk(self, fk):
        """FK chieu N-1: phia duoc tham chieu la duy nhat."""
        return self.is_unique(fk.ref_table, fk.ref_cols)

    def _infer_fks(self):
        """Suy FK theo ten cot + kiem tra bao ham gia tri (cho DB thieu khai bao FK)."""
        for t in self.tables.values():
            have = {c for fk in t.fks for c in fk.cols}
            for c in t.columns:
                if c.name in have or [c.name] == t.pk:
                    continue
                cl = c.name.lower()
                for p in self.tables.values():
                    if p.name == t.name or len(p.pk) != 1:
                        continue
                    pk, pl = p.pk[0], p.name.lower()
                    stems = {pl, pl.rstrip("s"), pl[:-3] + "y" if pl.endswith("ies") else pl}
                    match = (cl == pk.lower() and cl != "id") or any(cl in (s + "_id", s + "id") for s in stems)
                    if not match:
                        continue
                    rows, err, _ = run_sql(
                        self.path,
                        f"SELECT 1 FROM {qi(t.name)} WHERE {qi(c.name)} IS NOT NULL AND {qi(c.name)} NOT IN "
                        f"(SELECT {qi(pk)} FROM {qi(p.name)}) LIMIT 1", 60)
                    if err is None and not rows:
                        t.fks.append(FK(t.name, (c.name,), p.name, (pk,), "inferred"))
                        break

    def table_ddl(self, name, n_samples=3):
        t = self.tables[name]
        lines = []
        for c in t.columns:
            s = f"  {qi(c.name)} {c.type}".rstrip()
            if [c.name] == t.pk:
                s += " PRIMARY KEY"
            s += ","
            ex = self.samples.get((name, c.name), [])[:n_samples]
            if ex:
                s += "  -- e.g. " + ", ".join(_show(v) for v in ex)
            lines.append(s)
        if len(t.pk) > 1:
            lines.append("  PRIMARY KEY (" + ", ".join(qi(c) for c in t.pk) + "),")
        for fk in t.fks:
            lines.append(f"  FOREIGN KEY ({', '.join(qi(c) for c in fk.cols)}) REFERENCES "
                         f"{qi(fk.ref_table)}({', '.join(qi(c) for c in fk.ref_cols)}),")
        return f"CREATE TABLE {qi(name)} (\n" + "\n".join(lines) + "\n);"


def _show(v):
    if isinstance(v, str):
        v = v.replace("\n", " ")
        return "'" + (v[:40] + "..." if len(v) > 40 else v) + "'"
    return str(v)


_STR = re.compile(r"'(?:[^']|'')*'")


def strip_strings(sql):
    return _STR.sub("''", sql)


def references(sql, name):
    """Ten (bang/view) co xuat hien nhu mot dinh danh trong SQL khong."""
    return re.search(r"(?<![\w])" + re.escape(name) + r"(?![\w])", strip_strings(sql), re.I) is not None


_FROM = re.compile(r"\b(?:from|join)\s+(`[^`]+`|\"[^\"]+\"|\[[^\]]+\]|\w+)", re.I)


def tables_in_sql(sql, schema):
    lower = {t.lower(): t for t in schema.tables}
    out = set()
    for m in _FROM.finditer(strip_strings(sql)):
        n = m.group(1).strip('`"[]').lower()
        if n in lower:
            out.add(lower[n])
    return out
