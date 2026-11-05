"""Mo ta cot cua BIRD (database_description/*.csv) va khoa chinh/khoa ngoai theo dev_tables.json."""
import csv
import io
import json
from pathlib import Path

from .db import _show


def _read_csv(path):
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "latin1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    return list(csv.DictReader(io.StringIO(text)))


def _clean(s):
    return " ".join(str(s or "").replace("commonsense evidence:", "").split())


class Descriptions:
    """(bang, cot) -> dict(full=..., desc=..., values=..., fmt=...). Khong phan biet hoa/thuong."""

    def __init__(self, db_dir, schema):
        self.cols = {}
        d = Path(db_dir) / "database_description"
        files = {p.stem.lower(): p for p in d.glob("*.csv")} if d.is_dir() else {}
        for t in schema.tables:
            p = files.get(t.lower())
            if p is None:
                continue
            for row in _read_csv(p):
                key = next((k for k in row if k and "original_column_name" in k), None)
                if key is None:
                    continue
                ocn = (row.get(key) or "").strip()
                col = schema.tables[t].col(ocn)
                if col is None:
                    continue
                cn = row.get("column_name") or ""
                self.cols[(t.lower(), col.name.lower())] = dict(
                    full=_clean(cn), desc=_clean(row.get("column_description")),
                    values=_clean(row.get("value_description")), fmt=_clean(row.get("data_format")),
                    # nguyen van nhu ma TA-SQL doc (dung cho baseline TA-SQL)
                    raw=dict(name=cn if cn.strip() else ocn, desc=(row.get("column_description") or "").strip(),
                             fmt=(row.get("data_format") or "").strip(),
                             values=(row.get("value_description") or "").strip()))

    def get(self, table, col):
        return self.cols.get((str(table).lower(), str(col).lower()), {})

    def text(self, table, col, max_len=200):
        """Mo ta ngan gon mot cot (dung cho prompt va tai lieu truy hoi)."""
        m = self.get(table, col)
        bits = []
        if m.get("full") and m["full"].lower().replace(" ", "_") != str(col).lower():
            bits.append(m["full"])
        if m.get("desc") and m["desc"].lower() != (m.get("full") or "").lower():
            bits.append(m["desc"])
        if m.get("values"):
            bits.append("values: " + m["values"])
        s = "; ".join(bits)
        return s[:max_len] + ("..." if len(s) > max_len else "")


def column_comment(schema, desc, table, col, n_samples=3, max_len=200):
    """'-- mo ta; e.g. v1, v2' cho mot cot goc."""
    bits = []
    d = desc.text(table, col, max_len) if desc else ""
    if d:
        bits.append(d)
    ex = schema.samples.get((table, col), [])[:n_samples]
    if ex:
        bits.append("e.g. " + ", ".join(_show(v) for v in ex))
    return "; ".join(bits)


def table_ddl(schema, desc, name, n_samples=3):
    """CREATE TABLE kem mo ta cot va gia tri mau (dung chung cho base / V-SQL / V-SQL+)."""
    from .db import qi
    t = schema.tables[name]
    lines = []
    for c in t.columns:
        s = f"  {qi(c.name)} {c.type}".rstrip()
        if [c.name] == t.pk:
            s += " PRIMARY KEY"
        s += ","
        com = column_comment(schema, desc, name, c.name, n_samples)
        if com:
            s += "  -- " + com
        lines.append(s)
    if len(t.pk) > 1:
        lines.append("  PRIMARY KEY (" + ", ".join(qi(c) for c in t.pk) + "),")
    for fk in t.fks:
        lines.append(f"  FOREIGN KEY ({', '.join(qi(c) for c in fk.cols)}) REFERENCES "
                     f"{qi(fk.ref_table)}({', '.join(qi(c) for c in fk.ref_cols)}),")
    return f"CREATE TABLE {qi(name)} (\n" + "\n".join(lines) + "\n);"


def load_tables_json(path):
    """dev_tables.json -> {db_id: entry}"""
    p = Path(path)
    if not p.exists():
        return {}
    return {e["db_id"]: e for e in json.loads(p.read_text(encoding="utf-8"))}


def table6(title, rows, fks=()):
    """Trinh bay schema theo Bang 6 cua paper V-SQL: original_column_name | column_name | column_description | data_format
    (paper to do khoa ngoai; o day ghi thanh dong `foreign keys`)."""
    lines = [title, "original_column_name | column_name | column_description | data_format"]
    lines += [" | ".join(x or "" for x in r) for r in rows]
    if fks:
        lines.append("foreign keys: " + "; ".join(fks))
    return "\n".join(lines)


def _row6(desc, table, col, shown, ctype):
    m = desc.get(table, col) if desc else {}
    full = m.get("full") or col if shown.lower() == col.lower() else shown.replace("_", " ")   # cot doi ten: eye_colour
    return (shown, full, m.get("desc", ""), m.get("fmt") or (ctype or "").lower())


def table6_table(schema, desc, name):
    t = schema.tables[name]
    fks = [f"{name}.{c} -> {fk.ref_table}.{r}" for fk in t.fks for c, r in zip(fk.cols, fk.ref_cols)]
    return table6(f"# table: {name}", [_row6(desc, name, c.name, c.name, c.type) for c in t.columns], fks)


def table6_view(view, desc):
    return table6(f"# view: {view.name}", [_row6(desc, c.table, c.col, c.name, c.type) for c in view.cols])
