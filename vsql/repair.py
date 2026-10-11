"""CT5 - Schema-guard: sua SQL tat dinh dua tren thong bao loi cua SQLite va schema that (khong goi LLM).

Mo hinh nho hay "ao giac" ten: dung ten bang khi bang da co alias, alias khong ton tai, ten cot gan dung
(PatientID thay vi ID, Patient_SEX thay vi SEX), ham MySQL (YEAR, MONTH...), nhieu cau lenh trong mot chuoi.
Moi vong: chay SQL -> doc loi -> tim ten dung trong cac bang/view dang co trong FROM/JOIN -> thay -> chay lai.
"""
import re
from difflib import SequenceMatcher

from .db import run_sql

_KW = {"where", "on", "join", "left", "right", "inner", "outer", "cross", "full", "group", "order", "limit", "having",
       "union", "natural", "using", "as", "select", "from", "and", "or", "not", "in", "is", "by", "case", "when", "then",
       "else", "end", "with", "set", "values", "except", "intersect", "offset", "desc", "asc"}
_ID = r'(?:`[^`]+`|"[^"]+"|\[[^\]]+\]|\w+)'
_FROM = re.compile(rf"\b(?:FROM|JOIN)\s+({_ID})(?:\s+(?:AS\s+)?({_ID}))?", re.I)
_CTE = re.compile(rf"(?:\bWITH|,)\s*({_ID})\s+AS\s*\(", re.I)


def _unq(s):
    return s[1:-1] if s and s[0] in '`"[' else s


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def scope(sql, columns_of):
    """[(ten bang/view, alias, [cot])] cho moi muc trong FROM/JOIN ma columns_of biet."""
    out = []
    for m in _FROM.finditer(sql):
        name, alias = _unq(m.group(1)), _unq(m.group(2)) if m.group(2) else None
        if alias and alias.lower() in _KW:
            alias = None
        cols = columns_of(name)
        if cols is not None:
            out.append((name, alias, cols))
    return out


def _best(target, cands, prefixes=()):
    """Ten gan nhat voi target trong cands; None neu khong du giong."""
    t = _norm(target)
    strips = {t} | {t[len(_norm(p)):] for p in prefixes if p and t.startswith(_norm(p)) and len(t) > len(_norm(p))}
    best, score = None, 0.0
    for c in cands:
        n = _norm(c)
        for s in strips:
            if not s:
                continue
            if s == n:
                sc = 1.0
            elif n and (s.endswith(n) or n.endswith(s)) and min(len(n), len(s)) >= 2:
                sc = 0.9
            else:
                sc = SequenceMatcher(None, s, n).ratio()
            if sc > score:
                best, score = c, sc
    return best if score >= 0.8 else None


def _q(name):
    return name if re.fullmatch(r"[A-Za-z_]\w*", name) else f"`{name}`"


def _sub_ident(sql, old, new):
    """Thay dinh danh old (co the co qualifier, co the trong backtick) bang new, ngoai chuoi ky tu."""
    parts = re.split(r"('(?:[^']|'')*')", sql)
    if "." in old:
        q, c = old.split(".", 1)
        pat = rf"(?<![\w.`]){_qpat(q)}\s*\.\s*{_qpat(c)}(?![\w`])"
    else:
        pat = rf"(?<![\w.`]){_qpat(old)}(?![\w`(])"
    return "".join(p if i % 2 else re.sub(pat, new.replace("\\", r"\\"), p, flags=re.I) for i, p in enumerate(parts))


def _qpat(name):
    e = re.escape(name)
    return rf'(?:`{e}`|"{e}"|\[{e}\]|{e})'


def _special(sql, missing, sc):
    """Cot co ky tu dac biet bi tach (T-CHO -> T, `First Date` -> First): tim ten day du trong cau va bao trich dan."""
    q, c = missing.split(".", 1) if "." in missing else (None, missing)
    head = (rf"{_qpat(q)}\s*\.\s*" if q else r"(?<![\w.`])")
    for m in re.finditer(head + rf"({re.escape(c)}[\w\- ]*[\w)]?)", sql, re.I):
        tail = m.group(1)
        for e in sc:
            for col in sorted(e[2], key=len, reverse=True):
                if re.search(r"[^\w]", col) and tail.lower().startswith(col.lower()):
                    old = m.group(0)[:m.group(0).lower().rfind(c.lower())] + tail[:len(col)]
                    pre = old[:len(old) - len(col)]
                    return sql.replace(old, pre + f"`{col}`")
    return None


def _from_end(sql):
    """Vi tri ket thuc menh de FROM cua truy van ngoai cung (truoc WHERE/GROUP/ORDER/HAVING/LIMIT o do sau 0)."""
    m = re.search(r"\bFROM\b", sql, re.I)
    if not m:
        return None
    depth, i = 0, m.end()
    while i < len(sql):
        ch = sql[i]
        if ch == "'":
            j = sql.find("'", i + 1)
            i = len(sql) if j < 0 else j + 1
            continue
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if depth < 0:
            return i
        if depth == 0 and re.match(r"(WHERE|GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT|UNION|EXCEPT|INTERSECT)\b", sql[i:], re.I) \
                and (i == 0 or not (sql[i - 1].isalnum() or sql[i - 1] == "_")):
            return i
        i += 1
    return len(sql.rstrip().rstrip(";"))


def _auto_join(sql, missing, sc, joiner, prefixes=()):
    """CT5b: cot thuoc bang khong co trong FROM -> them LEFT JOIN theo khoa ngoai toi bang chua cot do.
    Thu ca ten bo tien to cua view (Customer_Currency -> Currency)."""
    if not joiner:
        return None
    c = missing.split(".", 1)[-1]
    names = [c] + [c[len(p) + 1:] for p in prefixes if c.lower().startswith(p.lower() + "_") and len(c) > len(p) + 1]
    hit = next((h for h in (joiner(x, sc) for x in names) if h), None)
    if not hit:
        return None
    table, col, on = hit
    al = f"j_{re.sub(r'[^A-Za-z0-9_]', '_', table)}"
    if re.search(rf"\b{al}\b", sql):
        return None
    pos = _from_end(sql)
    if pos is None:
        return None
    clause = f" LEFT JOIN {_q(table)} AS {al} ON {on.format(a=al)} "
    sql = sql[:pos].rstrip() + clause + sql[pos:]
    return _sub_ident(sql, missing, f"{al}.{_q(col)}")


def _fix_column(sql, missing, sc, prefixes, joiner=None):
    r = _fix_column0(sql, missing, sc, prefixes)
    return r if r else _auto_join(sql, missing, sc, joiner, prefixes)


def _fix_column0(sql, missing, sc, prefixes):
    ref = lambda e: e[1] or e[0]
    sp = _special(sql, missing, sc)
    if sp and sp != sql:
        return sp
    if "." in missing:
        q, c = missing.split(".", 1)
        # 0) q la tien to FK trong view: q.c -> <muc>.q_c
        for e in sc:
            hit = next((x for x in e[2] if x.lower() == f"{q}_{c}".lower()), None)
            if hit:
                return _sub_ident(sql, missing, f"{_q(ref(e))}.{_q(hit)}")
        # 1) q la ten bang/view da co alias, la alias, hoac la bang goc cua view v_q
        tgt = [e for e in sc if (e[1] and e[1].lower() == q.lower()) or e[0].lower() in (q.lower(), f"v_{q}".lower())]
        for e in tgt:
            hit = next((x for x in e[2] if x.lower() == c.lower()), None) or _best(c, e[2], prefixes + [e[0]])
            if hit:
                return _sub_ident(sql, missing, f"{_q(ref(e))}.{_q(hit)}")
        # 2) cot c (dung ten) co o muc khac trong FROM
        for e in sc:
            hit = next((x for x in e[2] if x.lower() == c.lower()), None)
            if hit:
                return _sub_ident(sql, missing, f"{_q(ref(e))}.{_q(hit)}")
        # 3) gan dung o muc bat ky
        for e in sc:
            hit = _best(c, e[2], prefixes + [e[0], q])
            if hit:
                return _sub_ident(sql, missing, f"{_q(ref(e))}.{_q(hit)}")
        return None
    # khong co qualifier
    for e in sc:
        hit = next((x for x in e[2] if x.lower() == missing.lower()), None)
        if hit and hit != missing:
            return _sub_ident(sql, missing, _q(hit))
    for e in sc:
        hit = _best(missing, e[2], prefixes + [e[0]])
        if hit:
            new = _q(hit) if len(sc) == 1 else f"{_q(ref(e))}.{_q(hit)}"
            return _sub_ident(sql, missing, new)
    return None


_FUNCS = [(r"\bYEAR\s*\(", "CAST(strftime('%Y', "), (r"\bMONTH\s*\(", "CAST(strftime('%m', "),
          (r"\bDAY\s*\(", "CAST(strftime('%d', ")]


def _fix_function(sql, fn):
    fn = fn.upper()
    if fn in ("YEAR", "MONTH", "DAY"):
        # YEAR(x) -> CAST(strftime('%Y', x) AS INTEGER): tim dau ngoac dong tuong ung
        fmt = {"YEAR": "%Y", "MONTH": "%m", "DAY": "%d"}[fn]
        changed = False
        while m := re.search(rf"\b{fn}\s*\(", sql, re.I):
            i, d = m.end(), 1
            while i < len(sql) and d:
                d += {"(": 1, ")": -1}.get(sql[i], 0)
                i += 1
            sql = sql[:m.start()] + f"CAST(strftime('{fmt}', {sql[m.end():i - 1]}) AS INTEGER)" + sql[i:]
            changed = True
        return sql if changed else None
    simple = {"NOW": "datetime('now')", "CURDATE": "date('now')", "CURRENT_DATE": "date('now')"}
    if fn in simple:
        return re.sub(rf"\b{fn}\s*\(\s*\)", simple[fn], sql, flags=re.I)
    if fn == "ILIKE":
        return re.sub(r"\bILIKE\b", "LIKE", sql, flags=re.I)
    if fn in ("ISNULL", "IFNULL"):
        return re.sub(r"\bISNULL\s*\(", "IFNULL(", sql, flags=re.I)
    if fn == "CONCAT":
        m = re.search(r"\bCONCAT\s*\(([^()]*)\)", sql, re.I)
        if m:
            return sql[:m.start()] + "(" + " || ".join(a.strip() for a in m.group(1).split(",")) + ")" + sql[m.end():]
    return None


def _first_statement(sql):
    parts = [p for p in re.split(r";(?=(?:[^']*'[^']*')*[^']*$)", sql) if p.strip()]
    return parts[0] if parts else sql


def _normalize(sql):
    """Bo dau ; lac giua cau (vd '... AS x; FROM t') - mo hinh nho hay sinh."""
    return re.sub(r";(\s*)(?=(FROM|WHERE|JOIN|LEFT|INNER|GROUP|ORDER|HAVING|LIMIT|UNION)\b)", r"\1", sql, flags=re.I)


def repair(sql, db_path, columns_of, all_tables, prefixes=(), max_steps=8, timeout=30.0, render=None, joiner=None):
    """Tra ve (sql_moi, cac_buoc). columns_of(ten) -> list cot hoac None; all_tables: ten bang/view hop le.
    render(sql) -> SQL thuc thi duoc (vd mo rong view thanh CTE); sua tren sql goc, chay tren ban render."""
    steps = []
    render = render or (lambda x: x)
    if sql:
        n = _normalize(sql)
        if n != sql:
            steps.append("stray ;")
            sql = n
    for _ in range(max_steps):
        if not sql:
            break
        rows, err, _sec = run_sql(db_path, render(sql), timeout)
        if err is None:
            break
        e = str(err)
        new = None
        if "one statement at a time" in e:
            new = _first_statement(sql)
        elif m := re.search(r"no such column: (.+)$", e):
            new = _fix_column(sql, m.group(1).strip(), scope(sql, columns_of), list(prefixes), joiner)
        elif m := re.search(r"ambiguous column name: (.+)$", e):
            c, sc = m.group(1).strip(), scope(sql, columns_of)
            owner = next((x for x in sc if any(k.lower() == c.lower() for k in x[2])), None)
            if owner:
                new = _sub_ident(sql, c, f"{_q(owner[1] or owner[0])}.{_q(c)}")
        elif m := re.search(r"no such table: (.+)$", e):
            t = m.group(1).strip().split(".")[-1]
            hit = _best(t, all_tables)
            if hit:
                new = _sub_ident(sql, t, _q(hit))
        elif m := re.search(r"no such function: (\w+)", e):
            new = _fix_function(sql, m.group(1))
        elif "ILIKE" in sql.upper() and "syntax error" in e:
            new = _fix_function(sql, "ILIKE")
        if not new or new == sql:
            break
        steps.append(e.split(": ", 1)[-1][:80])
        sql = new
    return sql, steps
