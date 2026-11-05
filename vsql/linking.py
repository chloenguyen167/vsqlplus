"""V-SQL+: lien ket gia tri va truy hoi lai muc cot -> gop len view.

ValueIndex   : chi muc gia tri van ban that trong DB (gia tri da chuan hoa -> cac cot chua no).
link_values  : khop n-gram / chuoi trong ngoac cua cau hoi + evidence voi gia tri that
               (vd "Dark Horse Comics" -> publisher.publisher_name).
link_columns : ten cot duoc nhac thang trong cau hoi / evidence (vd "A15", "Currency").
ColumnRetriever : BM25 + embedding tren tai lieu tung cot (ten, mo ta, gia tri mau), hop nhat RRF.
"""
import math
import re
from collections import Counter, defaultdict

from .db import connect, qi
from .retrieval import tokens

STOP = set("""a an the of in on at to for from by with and or not no is are was were be been being this that these those
which who whom whose what when where why how many much more most less least than then there their they them it its
as all any each every some such only own same so too very can will just do does did done have has had having
i me my we our you your he him his she her list name names give show find tell please among between number count
total average per both other others also into over under up down out about after before during while""".split())
_NUM = re.compile(r"^[\d.,%\-/: ]+$")


def norm(v):
    s = str(v).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s.strip(" \t.,;:!?\"'()[]{}")


class ValueIndex:
    """Chi muc gia tri van ban (<= max_len ky tu) cua moi cot; xay mot lan cho moi DB."""

    def __init__(self, schema, max_len=80, max_per_col=300000):
        self.idx = defaultdict(set)
        self.max_words = 1
        # tu thuoc ten bang/cot: "status", "power", "user"... khop 1 tu voi gia tri thuong la nhieu
        self.vocab = {w for t in schema.tables.values() for n in [t.name] + [c.name for c in t.columns] for w in tokens(n)}
        con = connect(schema.path)
        for t in schema.tables.values():
            for c in t.columns:
                if c.type and not any(k in c.type for k in ("CHAR", "TEXT", "CLOB", "VARCHAR")) and c.type != "":
                    continue
                try:
                    rows = con.execute(
                        f"SELECT DISTINCT {qi(c.name)} FROM {qi(t.name)} WHERE typeof({qi(c.name)}) = 'text' "
                        f"AND length({qi(c.name)}) BETWEEN 2 AND {max_len} LIMIT {max_per_col}").fetchall()
                except Exception:  # noqa: BLE001
                    continue
                for (v,) in rows:
                    n = norm(v)
                    if len(n) < 2 or _NUM.match(n):
                        continue
                    self.idx[n].add((t.name, c.name, v))
                    self.max_words = max(self.max_words, min(8, n.count(" ") + 1))
        con.close()

    def lookup(self, s):
        return self.idx.get(norm(s), set())


def _candidates(text, max_n, vocab=()):
    """n-gram (1..max_n tu) va chuoi trong dau nhay cua van ban."""
    out = []
    for q in re.findall(r"'([^']{2,80})'|\"([^\"]{2,80})\"", text):
        out.append(((q[0] or q[1]), 3.0))                       # gia tri trong ngoac: tin hieu rat manh
    words = re.findall(r"[\w][\w'\-&./]*", text)
    words = [w.rstrip(".'") for w in words]
    for n in range(min(max_n, 6), 0, -1):
        for i in range(len(words) - n + 1):
            g = words[i:i + n]
            if n == 1 and (g[0].lower() in STOP or len(g[0]) < 3 or (tokens(g[0]) or [""])[0] in vocab):
                continue
            if g[0].lower() in STOP and g[-1].lower() in STOP:
                continue
            out.append((" ".join(g), 1.0 + 0.5 * (n - 1)))
    return out


def link_values(vindex, question, evidence="", max_cols_per_value=6):
    """-> [(gia_tri_that, bang, cot, trong_so)] sap theo trong so giam dan, moi (bang, cot, gia tri) mot lan."""
    best = {}
    for text in (question, evidence or ""):
        for cand, w in _candidates(text, vindex.max_words, vindex.vocab):
            hits = vindex.lookup(cand)
            if not hits or len({(t, c) for t, c, _ in hits}) > max_cols_per_value:
                continue
            spread = len({(t, c) for t, c, _ in hits})
            for t, c, v in hits:
                k = (t, c, v)
                best[k] = max(best.get(k, 0.0), w / math.sqrt(spread))
    return sorted(((v, t, c, w) for (t, c, v), w in best.items()), key=lambda x: (-x[3], x[1], x[2]))


def link_columns(schema, question, evidence=""):
    """Cot duoc goi dich danh trong cau hoi/evidence (so khop nguyen tu, khong phan biet hoa thuong)."""
    text = f"{question} {evidence or ''}"
    low = text.lower()
    out = set()
    for t in schema.tables.values():
        for c in t.columns:
            n = c.name.lower()
            if len(n) < 2 or n in STOP or n in ("id", "name", "date", "type"):
                continue
            if re.search(r"(?<![\w])" + re.escape(n) + r"(?![\w])", low):
                out.add((t.name, c.name))
            elif " " not in n and "_" in n and n.replace("_", " ") in low:
                out.add((t.name, c.name))
    return out


def rrf(rankings, k=60, weights=None):
    """Hop nhat thu hang: rankings = [ [ten theo thu tu] ], tra ve {ten: diem}."""
    sc = Counter()
    for j, r in enumerate(rankings):
        w = weights[j] if weights else 1.0
        for i, name in enumerate(r):
            sc[name] += w / (k + i + 1)
    return sc


class Bm25:
    def __init__(self, texts):
        self.tok = [tokens(t) for t in texts]
        self.df = Counter(w for d in self.tok for w in set(d))
        self.avg = sum(map(len, self.tok)) / max(1, len(self.tok))

    def scores(self, query, k1=1.2, b=0.75):
        q, n, out = set(tokens(query)), len(self.tok), []
        for d in self.tok:
            tf, s = Counter(d), 0.0
            for w in q:
                if w in tf:
                    idf = math.log(1 + (n - self.df[w] + 0.5) / (self.df[w] + 0.5))
                    s += idf * tf[w] * (k1 + 1) / (tf[w] + k1 * (1 - b + b * len(d) / self.avg))
            out.append(s)
        return out


def _cos(a, b):
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


class HybridIndex:
    """BM25 + embedding (neu co) tren danh sach (khoa, van ban); rank() tra ve khoa theo diem RRF giam dan."""

    def __init__(self, items, embedder=None):
        self.keys = [k for k, _ in items]
        self.texts = [t for _, t in items]
        self.bm25 = Bm25(self.texts)
        self.embedder = embedder
        self.vecs = embedder(self.texts) if embedder else None

    def rank(self, query):
        bm = self.bm25.scores(query)
        rankings = [[self.keys[i] for i in sorted(range(len(bm)), key=lambda i: (-bm[i], i)) if bm[i] > 0]]
        if self.vecs is not None:
            qv = self.embedder([query])[0]
            em = [_cos(qv, v) for v in self.vecs]
            rankings.append([self.keys[i] for i in sorted(range(len(em)), key=lambda i: (-em[i], i))])
        return rrf(rankings)
