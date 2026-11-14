"""DAIL-SQL: baseline trong Bang 3 cua paper V-SQL.

Paper (muc 5.1): "To ensure fairness, none of the models utilized self-consistency or re-modification mechanisms" ->
  - DAIL-SQL: cau hinh BIRD cua ma chinh thuc (run_for_bird.sh): bieu dien schema kieu code (CREATE TABLE), 7 vi du
    cap cau hoi-SQL tu tap train BIRD, chon vi du 2 vong (vong 1: do giong cau hoi da che ten schema; vong 2: them do
    giong khung SQL cua cau tra loi vong 1, nguong 0.85); chi 1 mau o nhiet do 0 (ma goc mac dinh n=5 bau chon -> bo).
Nhiet do 0, toi da `--num-predict` token (paper: 800 cho moi phuong phap).

Ma goc:
  DAIL-SQL https://github.com/BeachWang/DAIL-SQL (Apache-2.0); sql_normalization / sql2skeleton / jaccard_similarity /
           compute_schema_linking / match_shift / mask duoi day chep tu utils/ cua repo nay.
Diem khac bat buoc (ghi ro trong docs): DAIL-SQL dung spaCy thay Stanford CoreNLP (server Java) de tach tu va
lay lemma khi che ten schema trong cau hoi.
"""
import collections
import glob
import hashlib
import json
import os
import re
import string
from pathlib import Path

from .llm import extract_sql


def _strip_think(text):
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()


def _first_sql(text):
    """Chuan hoa dau ra giong cac phuong phap khac: mo hinh chat hay boc SQL trong ```sql```; neu co khoi code thi lay khoi do."""
    text = _strip_think(text)
    return extract_sql(text) if "```" in text else text


# =========================================================================== DAIL-SQL
# ---- chep tu DAIL-SQL utils/utils.py (sql_normalization, sql2skeleton, isNegativeInt, isFloat, jaccard_similarity)
def sql_normalization(sql):
    from sql_metadata import Parser
    sql = sql.strip()

    def white_space_fix(s):
        parsed_s = Parser(s)
        return " ".join([token.value for token in parsed_s.tokens])

    def lower(s):
        in_quotation = False
        out_s = ""
        for char in s:
            out_s += char if in_quotation else char.lower()
            if char == "'":
                in_quotation = not in_quotation
        return out_s

    def remove_semicolon(s):
        return s[:-1] if s.endswith(";") else s

    def double2single(s):
        return s.replace("\"", "'")

    def add_asc(s):
        pattern = re.compile(r'order by (?:\w+ \( \S+ \)|\w+\.\w+|\w+)(?: (?:\+|\-|\<|\<\=|\>|\>\=) (?:\w+ \( \S+ \)|\w+\.\w+|\w+))*')
        if "order by" in s and "asc" not in s and "desc" not in s:
            for p_str in pattern.findall(s):
                s = s.replace(p_str, p_str + " asc")
        return s

    def sql_split(s):
        while "  " in s:
            s = s.replace("  ", " ")
        s = s.strip()
        i = 0
        toks = []
        while i < len(s):
            tok = ""
            if s[i] == "'":
                tok = tok + s[i]
                i += 1
                while i < len(s) and s[i] != "'":
                    tok = tok + s[i]
                    i += 1
                if i < len(s):
                    tok = tok + s[i]
                    i += 1
            else:
                while i < len(s) and s[i] != " ":
                    tok = tok + s[i]
                    i += 1
                while i < len(s) and s[i] == " ":
                    i += 1
            toks.append(tok)
        return toks

    def remove_table_alias(s):
        tables_aliases = Parser(s).tables_aliases
        new_tables_aliases = {}
        for i in range(1, 11):
            if "t{}".format(i) in tables_aliases.keys():
                new_tables_aliases["t{}".format(i)] = tables_aliases["t{}".format(i)]
        table_names = []
        for tok in sql_split(s):
            if '.' in tok:
                table_names.append(tok.split('.')[0])
        for table_name in table_names:
            if table_name in tables_aliases.keys():
                new_tables_aliases[table_name] = tables_aliases[table_name]
        tables_aliases = new_tables_aliases

        new_s = []
        pre_tok = ""
        for tok in sql_split(s):
            if tok in tables_aliases.keys():
                if pre_tok == 'as':
                    new_s = new_s[:-1]
                elif pre_tok != tables_aliases[tok]:
                    new_s.append(tables_aliases[tok])
            elif '.' in tok:
                split_toks = tok.split('.')
                for i in range(len(split_toks)):
                    if len(split_toks[i]) > 2 and split_toks[i][0] == "'" and split_toks[i][-1] == "'":
                        split_toks[i] = split_toks[i].replace("'", "")
                        split_toks[i] = split_toks[i].lower()
                    if split_toks[i] in tables_aliases.keys():
                        split_toks[i] = tables_aliases[split_toks[i]]
                new_s.append('.'.join(split_toks))
            else:
                new_s.append(tok)
            pre_tok = tok

        s = new_s
        new_s = []
        for i in range(len(s)):
            if s[i] == "as":
                continue
            if i > 0 and s[i - 1] == "as":
                continue
            new_s.append(s[i])
        return ' '.join(new_s)

    processing_func = lambda x: remove_table_alias(add_asc(lower(white_space_fix(double2single(remove_semicolon(x))))))  # noqa: E731
    return processing_func(sql.strip())


def _is_neg_int(s):
    return s.startswith("-") and s[1:].isdigit()


def _is_float(s):
    if s.startswith("-"):
        s = s[1:]
    parts = s.split(".")
    if len(parts) > 2:
        return False
    return all(p.isdigit() for p in parts)


def sql2skeleton(sql, db_schema):
    from sql_metadata import Parser
    sql = sql_normalization(sql)
    table_names_original, table_dot_column_names_original, column_names_original = [], [], []
    column_names_original.append("*")
    for table_id, table_name_original in enumerate(db_schema["table_names_original"]):
        table_names_original.append(table_name_original.lower())
        table_dot_column_names_original.append(table_name_original + ".*")
        for column_id_and_name in db_schema["column_names_original"]:
            column_name_original = column_id_and_name[1]
            table_dot_column_names_original.append(table_name_original.lower() + "." + column_name_original.lower())
            column_names_original.append(column_name_original.lower())

    parsed_sql = Parser(sql)
    new_sql_tokens = []
    for token in parsed_sql.tokens:
        if token.value in table_names_original:
            new_sql_tokens.append("_")
        elif token.value in column_names_original or token.value in table_dot_column_names_original:
            new_sql_tokens.append("_")
        elif token.value.startswith("'") and token.value.endswith("'"):
            new_sql_tokens.append("_")
        elif token.value.isdigit():
            new_sql_tokens.append("_")
        elif _is_neg_int(token.value):
            new_sql_tokens.append("_")
        elif _is_float(token.value):
            new_sql_tokens.append("_")
        else:
            new_sql_tokens.append(token.value.strip())

    sql_skeleton = " ".join(new_sql_tokens)
    sql_skeleton = sql_skeleton.replace("on _ = _ and _ = _", "on _ = _")
    sql_skeleton = sql_skeleton.replace("on _ = _ or _ = _", "on _ = _")
    sql_skeleton = sql_skeleton.replace(" on _ = _", "")
    pattern3 = re.compile("_ (?:join _ ?)+")
    sql_skeleton = re.sub(pattern3, "_ ", sql_skeleton)
    while "_ , _" in sql_skeleton:
        sql_skeleton = sql_skeleton.replace("_ , _", "_")
    ops = ["=", "!=", ">", ">=", "<", "<="]
    for op in ops:
        if "_ {} _".format(op) in sql_skeleton:
            sql_skeleton = sql_skeleton.replace("_ {} _".format(op), "_")
    while "where _ and _" in sql_skeleton or "where _ or _" in sql_skeleton:
        if "where _ and _" in sql_skeleton:
            sql_skeleton = sql_skeleton.replace("where _ and _", "where _")
        if "where _ or _" in sql_skeleton:
            sql_skeleton = sql_skeleton.replace("where _ or _", "where _")
    while "  " in sql_skeleton:
        sql_skeleton = sql_skeleton.replace("  ", " ")
    split_skeleton = sql_skeleton.split(" ")
    for i in range(2, len(split_skeleton)):
        if split_skeleton[i - 2] == "order" and split_skeleton[i - 1] == "by" and split_skeleton[i] != "_":
            split_skeleton[i] = "_"
    return " ".join(split_skeleton)


def safe_skeleton(sql, db_schema):
    try:
        return sql2skeleton(sql, db_schema)
    except Exception:  # noqa: BLE001 - SQL hong (thuong gap o vong 1 cua model nho) -> khung rong
        return ""


def jaccard_similarity(skeleton1, skeleton2):
    tokens1 = skeleton1.strip().split(" ")
    tokens2 = skeleton2.strip().split(" ")
    d1, d2 = collections.Counter(tokens1), collections.Counter(tokens2)
    inter = sum(min(d1[t], d2[t]) for t in d1 if t in d2)
    return float(inter) / ((len(tokens1) + len(tokens2)) - inter)


# ---- che ten schema trong cau hoi (DAIL-SQL utils/linking_utils: compute_schema_linking, match_shift, mask)
# nltk.corpus.stopwords.words('english') (179 tu)
STOPWORDS = set("""i me my myself we our ours ourselves you you're you've you'll you'd your yours yourself yourselves he him
his himself she she's her hers herself it it's its itself they them their theirs themselves what which who whom this that
that'll these those am is are was were be been being have has had having do does did doing a an the and but if or because
as until while of at by for with about against between into through during before after above below to from up down in out
on off over under again further then once here there when where why how all any both each few more most other some such no
nor not only own same so than too very s t can will just don don't should should've now d ll m o re ve y ain aren aren't
couldn couldn't didn didn't doesn doesn't hadn hadn't hasn hasn't haven haven't isn isn't ma mightn mightn't mustn mustn't
needn needn't shan shan't shouldn shouldn't wasn wasn't weren weren't won won't wouldn wouldn't""".split())
PUNKS = set(string.punctuation)
CEM, CPM, TEM, TPM = "CEM", "CPM", "TEM", "TPM"


def compute_schema_linking(question, column, table):
    def partial_match(x_list, y_list):
        x_str, y_str = " ".join(x_list), " ".join(y_list)
        if x_str in STOPWORDS or x_str in PUNKS:
            return False
        return bool(re.match(rf"\b{re.escape(x_str)}\b", y_str))

    def exact_match(x_list, y_list):
        return " ".join(x_list) == " ".join(y_list)

    q_col_match, q_tab_match = {}, {}
    col_id2list = {i: c for i, c in enumerate(column) if i != 0}
    tab_id2list = dict(enumerate(table))
    n = 5
    while n > 0:
        for i in range(len(question) - n + 1):
            n_gram_list = question[i:i + n]
            if len(" ".join(n_gram_list).strip()) == 0:
                continue
            for col_id in col_id2list:
                if exact_match(n_gram_list, col_id2list[col_id]):
                    for q_id in range(i, i + n):
                        q_col_match[f"{q_id},{col_id}"] = CEM
            for tab_id in tab_id2list:
                if exact_match(n_gram_list, tab_id2list[tab_id]):
                    for q_id in range(i, i + n):
                        q_tab_match[f"{q_id},{tab_id}"] = TEM
            for col_id in col_id2list:
                if partial_match(n_gram_list, col_id2list[col_id]):
                    for q_id in range(i, i + n):
                        if f"{q_id},{col_id}" not in q_col_match:
                            q_col_match[f"{q_id},{col_id}"] = CPM
            for tab_id in tab_id2list:
                if partial_match(n_gram_list, tab_id2list[tab_id]):
                    for q_id in range(i, i + n):
                        if f"{q_id},{tab_id}" not in q_tab_match:
                            q_tab_match[f"{q_id},{tab_id}"] = TPM
        n -= 1
    return q_col_match, q_tab_match


def match_shift(q_col_match, q_tab_match):
    q_id_to_match = collections.defaultdict(list)
    for k, typ in q_col_match.items():
        q, c = map(int, k.split(","))
        q_id_to_match[q].append((typ, c))
    for k, typ in q_tab_match.items():
        q, t = map(int, k.split(","))
        q_id_to_match[q].append((typ, t))
    priority = []
    for q_id in q_id_to_match:
        q_id_to_match[q_id] = list(set(q_id_to_match[q_id]))
        priority.append((len(q_id_to_match[q_id]), q_id))
    priority.sort()
    matches = []
    new_col, new_tab = {}, {}
    for _, q_id in priority:
        if not list(set(matches) & set(q_id_to_match[q_id])):
            exact = [m for m in q_id_to_match[q_id] if m[0] in (CEM, TEM)]
            res = exact if exact else q_id_to_match[q_id]
            matches.extend(res)
        else:
            res = list(set(matches) & set(q_id_to_match[q_id]))
        for typ, ct in res:
            if typ in (CPM, CEM):
                new_col[f"{q_id},{ct}"] = typ
            if typ in (TPM, TEM):
                new_tab[f"{q_id},{ct}"] = typ
    return new_col, new_tab


class Tokenizer:
    """Thay Stanford CoreNLP (tokenize, ssplit, lemma; chu thuong) bang spaCy en_core_web_sm. Khong co spaCy -> tach tu
    bang regex, khong lemma (chi dung cho kiem thu; notebook cai spaCy)."""

    def __init__(self):
        self.nlp = None
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
        except Exception:  # noqa: BLE001
            print("[DAIL-SQL] CANH BAO: khong co spaCy en_core_web_sm -> che ten schema khong lemma (khac ban goc nhieu hon)")
        self.cache = {}

    @property
    def name(self):
        return "spacy" if self.nlp else "regex"

    def __call__(self, text):
        """-> (lemma chu thuong, tu goc chu thuong)"""
        if text not in self.cache:
            if self.nlp:
                toks = [t for t in self.nlp(text) if not t.is_space]
                self.cache[text] = ([t.lemma_.lower() for t in toks], [t.text.lower() for t in toks])
            else:
                toks = re.findall(r"\w+|[^\w\s]", text)
                self.cache[text] = ([t.lower() for t in toks], [t.lower() for t in toks])
        return self.cache[text]


def mask_question(question, table_json, tok, mask_tag="<mask>"):
    """mask_question_with_schema_linking cua DAIL-SQL (BIRD: cv_link tat -> khong che gia tri)."""
    q_lem, q_copy = tok(question)
    cols = [tok(c)[0] for _, c in table_json["column_names"]]
    tabs = [tok(t)[0] for t in table_json["table_names"]]
    qc, qt = match_shift(*compute_schema_linking(q_lem, cols, tabs))
    ids = {int(k.split(",")[0]) for k in qc} | {int(k.split(",")[0]) for k in qt}
    return " ".join(mask_tag if i in ids else t for i, t in enumerate(q_copy))


def with_evidence(item):
    """bird_pre_process(with_evidence=True): noi evidence vao sau cau hoi."""
    q, e = item["question"], item.get("evidence") or ""
    return (q + " " + e).strip() if len(e) > 0 else q


class DailIndex:
    """Tap vi du (train BIRD) + embedding cau hoi da che ten schema (all-mpnet-base-v2, tren CPU nhu ban goc)."""
    MODEL = "sentence-transformers/all-mpnet-base-v2"

    def __init__(self, train_path, tables_path, cache_dir, encoder=None, also=()):
        import numpy as np
        self.np = np
        raw = Path(train_path).read_bytes() + Path(tables_path).read_bytes()
        train = json.loads(Path(train_path).read_text(encoding="utf-8"))
        tables = {t["db_id"]: t for t in json.loads(Path(tables_path).read_text(encoding="utf-8"))}
        self.tok = Tokenizer()
        # che ten schema + khung SQL cua ~9.400 cau train mat vai phut -> luu lai trong thu muc ket qua
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

        def find(name):             # cache chung (--dail-cache) truoc, roi thu muc ket qua cu (ban truoc luu o day)
            for d in (cache_dir, *also):
                if (Path(d) / name).exists():
                    return Path(d) / name
            return Path(cache_dir) / name
        prep = find(f"dail_train_prep_{hashlib.md5(raw).hexdigest()[:10]}_{self.tok.name}.json")
        if prep.exists():
            self.train, masked = json.loads(prep.read_text(encoding="utf-8"))
        else:
            print(f"[DAIL-SQL] chuan bi {len(train)} vi du train (che ten schema, khung SQL; vai phut, chi lam mot lan)", flush=True)
            self.train = []
            for d in train:
                q, sql = with_evidence(d), d["SQL"]
                self.train.append(dict(question=q, query=sql, db_id=d["db_id"],
                                       pre_skeleton=safe_skeleton(sql, tables[d["db_id"]])))
            masked = [mask_question(x["question"], tables[x["db_id"]], self.tok) for x in self.train]
            prep.write_text(json.dumps([self.train, masked], ensure_ascii=False), encoding="utf-8")
        self.encode = encoder or self._st_encoder()
        key = hashlib.md5(("\n".join(masked) + self.tok.name + self.MODEL).encode()).hexdigest()[:12]
        cache = find(f"dail_train_emb_{key}.npy")
        if cache.exists():
            self.emb = np.load(cache)
        else:
            print(f"[DAIL-SQL] tinh embedding {len(masked)} cau hoi train (CPU, vai phut; luu {cache.name})", flush=True)
            self.emb = np.asarray(self.encode(masked), dtype="float32")
            np.save(cache, self.emb)
        self.qcache = {}

    def _st_encoder(self):
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(self.MODEL, device="cpu")
        return lambda xs: model.encode(xs)

    def ranked(self, question, table_json):
        """Chi so tap train theo khoang cach Euclid tang dan (EuclideanDistanceQuestionMaskSelector)."""
        if question not in self.qcache:
            m = mask_question(question, table_json, self.tok)
            e = self.np.asarray(self.encode([m]), dtype="float32")
            d = self.np.sqrt(((self.emb - e) ** 2).sum(1))
            self.qcache[question] = sorted(range(len(d)), key=lambda i: (float(d[i]), i))
        return self.qcache[question]

    def select(self, question, table_json, k, pre_skeleton=None, threshold=0.85):
        order = self.ranked(question, table_json)
        if pre_skeleton is None:                                    # vong 1: EUCDISQUESTIONMASK
            return [self.train[i] for i in order[:k]]
        top = [i for i in order if jaccard_similarity(self.train[i]["pre_skeleton"], pre_skeleton) >= threshold][:k]
        if len(top) < k:                                            # EUCDISMASKPRESKLSIMTHR: bu bang cac cau duoi nguong
            top += [i for i in order if jaccard_similarity(self.train[i]["pre_skeleton"], pre_skeleton) < threshold][:k - len(top)]
        return [self.train[i] for i in top]


_DAIL = {}


def dail_index(args):
    key = (args.dail_train, args.dail_train_tables)
    if key not in _DAIL:
        if not (args.dail_train and Path(args.dail_train).exists()):
            raise SystemExit("DAIL-SQL can tap train BIRD: --dail-train train.json --dail-train-tables train_tables.json")
        # cache tap train (che ten schema + embedding, vai phut) khong phu thuoc model / thu muc ket qua: dung chung cho buoc 8 (chay
        # thu), moi model o buoc 9 va cac lan chay lai; mac dinh canh train.json
        cdir = getattr(args, "dail_cache", "") or str(Path(args.dail_train).parent)
        _DAIL[key] = DailIndex(args.dail_train, args.dail_train_tables, cdir, getattr(args, "dail_encoder", None),
                               also=(args.out,))
    return _DAIL[key]


def prepare_dail(train, tables, cache_dir):
    """Chuan bi truoc tap train DAIL-SQL (che ten schema + embedding, vai phut tren CPU) de luu cache; Buoc 4 cua notebook goi."""
    import types
    dail_index(types.SimpleNamespace(dail_train=train, dail_train_tables=tables, out=cache_dir, dail_cache=cache_dir))
    print("[DAIL-SQL] tap train san sang (cache:", cache_dir + ")", flush=True)


def dail_schema(db_path):
    """SQLPrompt.format_question: cau CREATE cua moi bang (sqlite_master, type='table', gom ca sqlite_sequence nhu ban goc)."""
    import sqlite3
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        return [con.execute(f"SELECT sql FROM sqlite_master WHERE tbl_name='{n}'").fetchall()[0][0] for n in names]
    finally:
        con.close()


def dail_prompt(question, sqls, examples):
    target = ("/* Given the following database schema: */\n" + "\n\n".join(sqls) + "\n\n"
              + f"/* Answer the following: {question} */" + "\nSELECT ")
    if not examples:
        return target
    ex = [f"/* Answer the following: {e['question']} */\n{e['query']}" for e in examples]
    return "/* Some SQL examples are provided based on similar problems: */\n" + "\n\n".join(ex + [target])


def dail_post(text):
    """ask_llm.py (n=1): gop khoang trang, cat tu '/*', them 'SELECT' neu thieu."""
    sql = _first_sql(text)
    sql = " ".join(sql.replace("\n", " ").split())
    sql = sql.strip().split("/*")[0]
    if sql.startswith("SELECT"):
        return sql
    if sql.startswith(" "):
        return "SELECT" + sql
    return "SELECT " + sql


def run_dail(item, ctx, ask, rec, args):
    if ctx.tj is None:
        raise SystemExit("DAIL-SQL can dev_tables.json (--tables-json)")
    idx = dail_index(args)
    q = with_evidence(item) if args.evidence else item["question"]
    sqls = ctx.lazy("dail_schema", lambda: dail_schema(ctx.path))
    k = args.dail_k
    ex1 = idx.select(q, ctx.tj, k)
    pre = dail_post(ask(dail_prompt(q, sqls, ex1), "dail_pre"))       # vong 1: SQL so bo de lay khung SQL
    rec["dail_pre_sql"] = pre
    ex2 = idx.select(q, ctx.tj, k, pre_skeleton=safe_skeleton(pre, ctx.tj))
    rec["dail_examples"] = [e["question"][:80] for e in ex2]
    return dail_post(ask(dail_prompt(q, sqls, ex2), "dail_final"))


# ---- tai tap train BIRD cho DAIL-SQL: chi lay 2 file json trong train.zip (8,9 GB) bang HTTP Range, khong tai ca zip
BIRD_TRAIN_ZIP = "https://bird-bench.oss-cn-beijing.aliyuncs.com/train.zip"
BIRD_TRAIN_MD5 = {"train.json": "37131456941dabe670c3f1c2fd07f008", "train_tables.json": "3d4433984ba7d80627f3448e89f304d6"}


def fetch_bird_train(dest, url=BIRD_TRAIN_ZIP):
    import io
    import urllib.request
    import zipfile

    class HttpFile(io.RawIOBase):
        def __init__(self, u):
            self.u, self.pos = u, 0
            self.size = int(urllib.request.urlopen(urllib.request.Request(u, method="HEAD")).headers["Content-Length"])

        def seekable(self):
            return True

        def readable(self):
            return True

        def tell(self):
            return self.pos

        def seek(self, off, wh=0):
            self.pos = off if wh == 0 else self.pos + off if wh == 1 else self.size + off
            return self.pos

        def readinto(self, b):
            if self.pos >= self.size or not len(b):
                return 0
            end = min(self.pos + len(b), self.size) - 1
            r = urllib.request.urlopen(urllib.request.Request(self.u, headers={"Range": f"bytes={self.pos}-{end}"})).read()
            b[:len(r)] = r
            self.pos += len(r)
            return len(r)

    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    need = [n for n in BIRD_TRAIN_MD5 if not (dest / n).exists()]
    if need:
        z = zipfile.ZipFile(io.BufferedReader(HttpFile(url), 1 << 20))
        for n in need:
            (dest / n).write_bytes(z.read(f"train/{n}"))
    for n, m in BIRD_TRAIN_MD5.items():
        got = hashlib.md5((dest / n).read_bytes()).hexdigest()
        assert got == m, f"{n}: md5 {got} khac ban phat hanh ({m})"
    return str(dest / "train.json"), str(dest / "train_tables.json")
