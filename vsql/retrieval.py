"""Cai tien 4: truy xuat view/bang lien quan (BM25, tuy chon embedding qua Ollama, hoac ket hop RRF)."""
import math
import re
from collections import Counter


def tokens(text):
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(text))
    out = []
    for w in re.findall(r"[A-Za-z0-9]+", text.lower()):
        if len(w) > 3 and w.endswith("ies"):
            w = w[:-3] + "y"
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


def object_doc(schema, name, cols):
    """cols: [(ten_cot_hien_thi, bang_nguon, cot_nguon)]"""
    parts = [name, name]
    for cname, t, c in cols:
        parts += [cname, cname]
        parts += [str(v) for v in schema.samples.get((t, c), []) if isinstance(v, str)]
    return " ".join(parts)


class Retriever:
    def __init__(self, docs, mode="bm25", llm=None, embed_model=None):
        """docs: {ten_doi_tuong: van_ban}"""
        self.names = list(docs)
        self.texts = [docs[n] for n in self.names]
        self.mode = mode
        self.tok = [tokens(t) for t in self.texts]
        self.df = Counter(w for d in self.tok for w in set(d))
        self.avg = sum(map(len, self.tok)) / max(1, len(self.tok))
        self.llm, self.embed_model, self.vecs = llm, embed_model, None
        if mode in ("embed", "hybrid"):
            self.vecs = llm.embed(embed_model, self.texts)

    def _bm25(self, query, k1=1.5, b=0.75):
        q, n, scores = tokens(query), len(self.tok), []
        for d in self.tok:
            tf, s = Counter(d), 0.0
            for w in set(q):
                if w in tf:
                    idf = math.log(1 + (n - self.df[w] + 0.5) / (self.df[w] + 0.5))
                    s += idf * tf[w] * (k1 + 1) / (tf[w] + k1 * (1 - b + b * len(d) / self.avg))
            scores.append(s)
        return scores

    def _embed(self, query):
        qv = self.llm.embed(self.embed_model, [query])[0]
        nq = math.sqrt(sum(x * x for x in qv)) or 1
        return [sum(a * b for a, b in zip(qv, v)) / (nq * (math.sqrt(sum(x * x for x in v)) or 1)) for v in self.vecs]

    def rank(self, query):
        if self.mode == "bm25":
            sc = self._bm25(query)
        elif self.mode == "embed":
            sc = self._embed(query)
        else:                                               # reciprocal rank fusion
            sc = [0.0] * len(self.names)
            for s in (self._bm25(query), self._embed(query)):
                for r, i in enumerate(sorted(range(len(s)), key=lambda i: -s[i])):
                    sc[i] += 1 / (60 + r)
        order = sorted(range(len(self.names)), key=lambda i: (-sc[i], i))
        return [self.names[i] for i in order]
