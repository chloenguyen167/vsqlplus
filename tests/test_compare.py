"""Kiem thu V-SQL / V-SQL+ / DIN-SQL / DAIL-SQL voi LLM gia lap (khong can Ollama, khong can BIRD).
Chay: python tests/test_compare.py"""
import json
import re
import shutil
import sqlite3
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_toy import ITEMS, make                                    # noqa: E402
from vsql import autoview as A                                      # noqa: E402
from vsql import views as V                                         # noqa: E402
from vsql.db import Schema, run_sql                                 # noqa: E402
from vsql.linking import ValueIndex, link_values                    # noqa: E402
from vsql.llm import extract_sql                                    # noqa: E402
from vsql.methods import Render6, _fallback_tables, compile_error, first_statement  # noqa: E402
import run_compare                                                  # noqa: E402

tmp = Path(tempfile.mkdtemp())
data, db_root, _ = make(tmp)
db = db_root / "superhero" / "superhero.sqlite"
s = Schema("superhero", db)

# 1. view tu dong kieu paper (Hinh 3): ten cot sach, giu nguyen so dong, 3 lan noi bang colour
auto = V.validate(s, A.auto_views(s))
assert sorted(v.name for v in auto) == ["v_hero_attribute", "v_hero_power", "v_superhero"], [v.name for v in auto]
assert all(v.verified == "rows_equal" for v in auto), [(v.name, v.verified) for v in auto]
vsh = next(v for v in auto if v.name == "v_superhero")
names = [c.name for c in vsh.cols]
assert {"eye_colour", "hair_colour", "skin_colour", "gender", "race", "publisher_name", "alignment"} <= set(names), names
assert "colour" not in names                                       # khong co cot 'colour' mo ho
vhp = next(v for v in auto if v.name == "v_hero_power")
assert {"power_name", "superhero_name", "eye_colour", "publisher_name"} <= {c.name for c in vhp.cols}, [c.name for c in vhp.cols]
for v in auto:
    assert len({c.name.lower() for c in v.cols}) == len(v.cols)

# 2. giai ma tat dinh (CTE) == chay tren VIEW that cua SQLite
real = tmp / "real.sqlite"
shutil.copy(db, real)
con = sqlite3.connect(real)
for v in auto:
    con.execute(v.ddl().rstrip(";"))
con.commit()
con.close()
qs = ["SELECT COUNT(*) FROM v_superhero WHERE eye_colour = 'Blue'",
      "SELECT superhero_name FROM v_superhero WHERE publisher_name = 'Marvel Comics' AND hair_colour = 'Blond'",
      "SELECT power_name FROM v_hero_power WHERE superhero_name = '3-D Man'",
      "SELECT COUNT(*) FROM v_hero_attribute WHERE attribute_name = 'Strength' AND attribute_value = 100 AND gender = 'Female'",
      "SELECT gender, COUNT(*), AVG(weight_kg) FROM v_superhero GROUP BY gender",
      "SELECT a.superhero_name, b.power_name FROM v_superhero a JOIN v_hero_power b ON a.id = b.hero_id WHERE a.eye_colour = 'Blue'",
      "SELECT * FROM v_hero_power WHERE race = 'Alien'"]
for q in qs:
    want, err, _ = run_sql(real, q)
    assert err is None, (q, err)
    for prune in (True, False):
        sql, used = V.unfold(q, auto, prune)
        got, err, _ = run_sql(db, sql)
        assert err is None and used, (sql, err)
        assert Counter(got) == Counter(want), (q, prune)

# 3. view cua V-SQL theo JOIN dap an: khong co view nhan ban dong; kieu Hinh 3 (khong "AS alias" khi alias = ten bang,
#    colour noi 3 lan theo ten vai tro, bo cot id khoa ngoai cua bang cha DA noi vao view); D' = view + bang ngoai moi view
oracle = V.validate(s, A.oracle_views(s, [it["gold"] for it in ITEMS]))
assert oracle and all(v.row_preserving and v.verified == "rows_equal" for v in oracle), [(v.name, v.verified) for v in oracle]
assert "publisher" not in V.leftover_tables(s, oracle) and "superhero" not in V.leftover_tables(s, oracle)
sh = {v.name: v for v in oracle}["v_superhero"]
# giai doan 2 (muc 4.5): chi bang ma dummy SQL dung cot; bang thuc the (khong phai id + 1 cot gia tri) khong bi an khoi D'
assert sh.tables_for({"publisher_name", "eye_colour"}) == {"superhero", "publisher", "colour"}, sh.tables_for({"publisher_name"})
assert sh.tables_for(None) == sh.source_tables()
_j = V.Join("x", "superhero", "hero_power", [("hero_id", "id")])
assert not V.is_lookup(s, _j) and all(V.is_lookup(s, j) for j in sh.joins)
nm = {c.name for c in sh.cols}
assert not nm & {"eye_colour_id", "hair_colour_id", "skin_colour_id", "publisher_id"} and {"id", "eye_colour", "publisher_name"} <= nm, nm
d3 = sh.ddl()                                # cach viet va thu tu cot nhu Hinh 3: gia tri thay ngay tai vi tri cot khoa ngoai
assert d3.startswith("create view v_superhero as\nselect\n   `superhero`.`id`,\n   `superhero`.`superhero_name`,"), d3
assert "left join `publisher` on `superhero`.`publisher_id` = `publisher`.`id`" in d3
assert "left join `colour` eye_colour on `superhero`.`eye_colour_id` = `eye_colour`.`id`" in d3 and "`eye_colour`.`colour` as `eye_colour`" in d3
names3 = [c.name for c in sh.cols]
assert names3.index("full_name") < names3.index("eye_colour") < names3.index("publisher_name") < names3.index("height_cm"), names3
shutil.copy(db, tmp / "fig3.sqlite")
c3 = sqlite3.connect(tmp / "fig3.sqlite")
c3.execute(d3)
assert c3.execute("select count(*) from v_superhero").fetchone() == c3.execute("select count(*) from superhero").fetchone()
c3.close()

# 4. lien ket gia tri
vi = ValueIndex(s)
links = link_values(vi, "List the heroes published by Dark Horse Comics with blue eyes.")
assert ("Dark Horse Comics", "publisher", "publisher_name") in [(v, t, c) for v, t, c, _ in links], links
assert any(t == "colour" for _, t, _, _ in links), links

# 5. schema lai: phat hien cot khong co trong view -> bang goc chua cot do
err = compile_error(str(db), V.unfold("SELECT COUNT(*) FROM v_superhero WHERE attribute_name = 'Strength'", auto)[0])
assert err and "no such column" in err, err
add, name = _fallback_tables(type("C", (), {"schema": s})(), err, set())
assert add == ["attribute"] and name == "attribute_name", (add, name)
assert compile_error(str(db), "SELECT COUNT(*) FROM superhero") is None

# 6. tien ich hau xu ly
assert first_statement("SELECT 1; SELECT 2") == "SELECT 1"
assert first_statement("SELECT ';' AS x;") == "SELECT ';' AS x"
assert extract_sql("To answer with SQL we use:\nSELECT a FROM t") == "SELECT a FROM t"       # khong lay chu "with" van xuoi
assert extract_sql("To find the league with the most draws, Select all matches ...") == ""   # van xuoi, khong co SQL
assert extract_sql("```sql\nwith x as (select 1) select * from x;\n```") == "with x as (select 1) select * from x"
assert extract_sql("Answer:\n  select a\nfrom t") == "select a\nfrom t"
# Bang 6 mo rong (V-SQL): ten cot can quote ghi kem backtick
_C = type("C", (), {"desc": type("D", (), {"get": lambda self, t, c: {}})(), "schema": type("S", (), {"samples": {}})(),
                    "lazy": lambda self, k, fn: None})
rows6 = Render6(_C(), extended=True)._rows([("FRPM Count (K-12)", "frpm", "FRPM Count (K-12)", "REAL"), ("id", "t", "id", "")])
assert rows6[0][0] == "`FRPM Count (K-12)`" and rows6[1][0] == "id", rows6

# 7. toan bo duong ong voi LLM gia lap (so lieu chi de kiem tra ma, khong co y nghia khoa hoc)
items = json.loads(Path(data).read_text())
Path(data).write_text(json.dumps(items + [dict(items[0])]))     # question_id lap (dau hieu ban mini-dev 2024-06) -> tu choi
try:
    run_compare.load_data(run_compare.parse_args(["--data", str(data), "--db-root", "x"]))
    raise AssertionError("phai tu choi file cau hoi co question_id lap")
except SystemExit as e:
    assert "2024-06" in str(e), e
Path(data).write_text(json.dumps(items))
N = len(items)
cn = [[-1, "*"]]
tn = list(s.tables)
for i, t in enumerate(tn):
    cn += [[i, c.name] for c in s.tables[t].columns]
idx = {(tn[t], c): k for k, (t, c) in enumerate(cn) if t >= 0}
tj = [dict(db_id="superhero", table_names_original=tn, column_names_original=cn,
           primary_keys=[idx[(t, s.tables[t].pk[0])] for t in tn if len(s.tables[t].pk) == 1],
           foreign_keys=[[idx[(f.table, f.cols[0])], idx[(f.ref_table, f.ref_cols[0])]] for t in tn for f in s.tables[t].fks])]
(tmp / "dev_tables.json").write_text(json.dumps(tj))

PLUS = ["SELECT COUNT(*) FROM v_superhero WHERE eye_colour = 'Blue'",
        "SELECT superhero_name FROM v_superhero WHERE publisher_name = 'Marvel Comics' AND hair_colour = 'Blond'",
        "SELECT power_name FROM v_hero_power WHERE superhero_name = '3-D Man'",
        "SELECT COUNT(*) FROM v_superhero WHERE attribute_name = 'Strength'",        # sai -> quay ve bang goc
        "SELECT COUNT(*) FROM publisher",
        "SELECT COUNT(DISTINCT power_id) FROM v_hero_power WHERE hero_id IN (SELECT hero_id FROM v_hero_attribute "
        "WHERE attribute_name = 'Intelligence' AND attribute_value >= 80)",
        "SELECT AVG(height_cm) FROM v_superhero WHERE publisher_id IS NULL"]


from vsql.methods import P_VSQL_1  # noqa: E402
FIG4 = '# target\nYou are an experienced database administrator, please answer "question" by sql'


class ScriptLLM:
    def __init__(self):
        self.stages = Counter()
        self.fig4 = 0

    def chat(self, prompt, meta=None, **opts):
        u, st = meta["qid"], meta["stage"]
        if st.startswith("plus_") and prompt.startswith(FIG4):     # vsqlplus_fig4: template/schema y nhu V-SQL
            self.fig4 += 1
            assert "matched database values" not in prompt and "CREATE " not in prompt and ("# view: " in prompt or "# table: " in prompt)
            assert prompt.startswith(P_VSQL_1.split("{relevant_db_schema}")[0])
        self.stages[st.rstrip("0123456789")] += 1
        k = u % len(ITEMS)
        gold = ITEMS[k]["gold"]
        if st == "vsql_s1":
            sql = PLUS[k]
        elif st == "vsql_s2":
            sql = ITEMS[k].get("s2", gold)
        elif st == "plus_s2":                                # khoi phuc hoan hao = mo rong tat dinh dummy SQL
            dummy = re.search(r"# view query\nQuestion: .*?\n```sql\n(.*?)\n```", prompt, re.S).group(1)
            sql = V.unfold(dummy, auto)[0]
        elif st.startswith("plus_fb") and prompt.startswith(FIG4):
            assert "# table: attribute" in prompt and "# note" not in prompt          # chi them bang goc, khong ghi chu
            sql = ("SELECT COUNT(*) FROM v_hero_attribute WHERE attribute_name = 'Strength' AND attribute_value = 100 "
                   "AND gender = 'Female'")
        elif st.startswith("plus_fb"):
            assert "attribute.attribute_name" in prompt and "does not exist" in prompt and "CREATE TABLE attribute" in prompt
            sql = ("SELECT COUNT(*) FROM v_hero_attribute WHERE attribute_name = 'Strength' AND attribute_value = 100 "
                   "AND gender = 'Female'")
        else:
            sql = PLUS[k]
        return {"text": f"```sql\n{sql}\n```", "prompt_tokens": len(prompt) // 4, "completion_tokens": 5, "seconds": 0.0}


out = tmp / "out"
llm = ScriptLLM()
run_compare.main(["--data", str(data), "--db-root", str(db_root), "--out", str(out), "--methods", "all",
                  "--tables-json", str(tmp / "dev_tables.json"), "--no-embed",
                  "--all-max-objects", "0", "--all-max-tokens", "0", "--k-cand", "6", "--n-samples", "3"], llm=llm)
got = {m: [json.loads(l) for l in (out / f"predictions_{m}.jsonl").read_text().splitlines()]
       for m in ["vsql", "vsqlplus", "vsqlplus_all", "vsqlplus_novote", "vsqlplus_novl", "vsqlplus_nofb",
                 "vsqlplus_det"]}
assert all(len(r) == N for r in got.values()), {m: len(r) for m, r in got.items()}
assert all(r["impl"] == 6 for r in got["vsql"]) and got["vsqlplus"][0]["impl"] == 2   # vsql mac dinh --vsql-views oracle
ex = {m: sum(r["correct"] for r in rs) for m, rs in got.items()}
assert ex["vsql"] == N - 1, ex                   # sai: ao giac kieu Table 1 cua paper o giai doan 2
assert ex["vsqlplus"] == N and ex["vsqlplus_det"] == N and ex["vsqlplus_nofb"] == N - 1 and ex["vsqlplus_all"] == N - 1, ex
r3 = got["vsqlplus"][3]
assert r3["fallback"] and r3["fallback"][0]["added"] == ["attribute"], r3["fallback"]
assert got["vsqlplus"][0]["vote"]["chosen"], got["vsqlplus"][0]
assert got["vsqlplus_novote"][0].get("vote") is None and got["vsqlplus_all"][0]["all_in_prompt"]
assert got["vsqlplus_det"][0]["calls"] == 4 and got["vsqlplus"][0]["views_used"]
assert got["vsql"][0]["calls"] == 2 and got["vsqlplus"][0]["calls"] == 5, (got["vsql"][0]["calls"], got["vsqlplus"][0]["calls"])
import io, contextlib  # noqa: E402
buf = io.StringIO()
with contextlib.redirect_stdout(buf):                  # chay lai: da cham het, chi in cac dong kiem tra
    run_compare.main(["--data", str(data), "--db-root", str(db_root), "--out", str(out), "--methods", "vsql,vsqlplus",
                      "--tables-json", str(tmp / "dev_tables.json"), "--no-embed"], llm=llm)
o = buf.getvalue()
assert f"{N} dong; {N} question_id khac nhau; {N} cau hoi" in o and f"[KIEM TRA] vsql: {N}/{N} dong da cham (DU)" in o, o[:600]
try:                                                   # doi cai dat embedding trong thu muc da co ket qua V-SQL+ -> dung
    run_compare.main(["--data", str(data), "--db-root", str(db_root), "--out", str(out), "--methods", "vsqlplus",
                      "--tables-json", str(tmp / "dev_tables.json"), "--embed-model", "nomic-embed-text"], llm=llm)
    raise AssertionError("phai dung khi doi embedding")
except SystemExit as e:
    assert "embedding" in str(e), e
# 9. vsqlplus_fig4 (2 huong, cung template Hinh 4 + Bang 6 voi vsql)
run_compare.main(["--data", str(data), "--db-root", str(db_root), "--out", str(out), "--methods", "vsqlplus_fig4",
                  "--tables-json", str(tmp / "dev_tables.json"), "--no-embed",
                  "--all-max-objects", "0", "--all-max-tokens", "0", "--k-cand", "6", "--n-samples", "3"], llm=llm)
g2 = [json.loads(l) for l in (out / "predictions_vsqlplus_fig4.jsonl").read_text().splitlines()]
assert len(g2) == N and llm.fig4 > 0
assert g2[3]["fallback"] and g2[3]["fallback"][0]["added"] == ["attribute"]
assert sum(r["correct"] for r in g2) == N, [r["outcome"] for r in g2]
# 10. prompt cua V-SQL; ban ghi cua cai dat V-SQL cu (khong co "impl") bi tach ra va cham lai
out2 = tmp / "out2"
out2.mkdir()
(out2 / "predictions_vsql.jsonl").write_text("".join(json.dumps(dict(r, correct=False, impl=None)) + "\n" for r in got["vsql"]))
seen = []
_orig = llm.chat
def _spy(prompt, meta=None, **o):  # noqa: E302
    seen.append((meta["stage"], prompt))
    return _orig(prompt, meta, **o)
llm.chat = _spy  # noqa: E305
run_compare.main(["--data", str(data), "--db-root", str(db_root), "--out", str(out2), "--methods", "vsql",
                  "--tables-json", str(tmp / "dev_tables.json"), "--no-embed", "--vsql-views", "all"], llm=llm)
s1 = [p for st, p in seen if st == "vsql_s1"]
s2 = [p for st, p in seen if st == "vsql_s2"]
assert len(s1) == N and all(p.startswith(P_VSQL_1.split("{relevant_db_schema}")[0]) for p in s1)  # template Hinh 4; cham lai du N cau
left = V.leftover_tables(s, oracle)            # D' = view + bang ngoai moi view; bang da gop vao view (publisher) an
assert "| value_description | example_values" in s1[0] and "# table: publisher" not in s1[0]
assert all(p.count("# table: ") == len(left) for p in s1) and all(f"# table: {t}" in s1[0] for t in left)
assert all(p.count("# view: ") == len(oracle) for p in s1)                                        # moi view cua CSDL, khong truy hoi
from vsql.methods import P_VSQL_2  # noqa: E402
assert "\n\n# relevant db schema\n" in P_VSQL_1 and "\n\n# question\n{query}" in P_VSQL_1          # Hinh 4 tung chu
assert "restore the sql in view query to one used the original table query without explanation\nnotice:" in P_VSQL_2
assert P_VSQL_2.endswith("\n\n# foramt\n```sql\n{{sql}}\n```")
vs = next(p for p in s1 if "# view: v_superhero" in p).split("# view: v_superhero")[1].split("# view: ")[0]
assert "eye_colour_id |" not in vs and "eye_colour |" in vs              # Hinh 3: bo cot id khoa ngoai da thay bang gia tri
assert len(s2) == N                         # giai doan 2 luon chay, ke ca dummy SQL khong dung view ("FROM publisher")
p4 = next(p for p in s2 if "FROM publisher" in p)
assert "# table: publisher" in p4 and "comply with the syntax of SQLite" in p4
assert (out2 / "views" / "superhero.oracle.sql").exists() and (out2 / "old_predictions_vsql_1.jsonl").exists()
new = [json.loads(l) for l in (out2 / "predictions_vsql.jsonl").read_text().splitlines()]
assert len(new) == N and all(r["impl"] == 5 and r["calls"] == 2 for r in new)
assert sum(r["correct"] for r in new) == N - 1                                  # cau ao giac Table 1 o gd2
# 10b. --vsql-views oracle (mac dinh): prompt Hinh 4 chi co view co bang goc trong SQL dap an + bang D' ma dap an dung;
# ban ghi impl 5 (all) trong out2 bi tach ra khi chay lai voi oracle
from vsql.db import tables_in_sql as _tis  # noqa: E402
seen3 = []
def _spy3(prompt, meta=None, **o):  # noqa: E302
    seen3.append((meta["qid"], meta["stage"], prompt))
    return _orig(prompt, meta, **o)
llm.chat = _spy3  # noqa: E305
run_compare.main(["--data", str(data), "--db-root", str(db_root), "--out", str(out2), "--methods", "vsql",
                  "--tables-json", str(tmp / "dev_tables.json"), "--no-embed"], llm=llm)
s1o = [(u, p) for u, st, p in seen3 if st == "vsql_s1"]
assert len(s1o) == N and (out2 / "old_predictions_vsql_2.jsonl").exists()
for u, p in s1o:
    gt = _tis(ITEMS[u % len(ITEMS)]["gold"], s)
    shown_v = set(re.findall(r"^# view: (\S+)", p, re.M))
    shown_t = set(re.findall(r"^# table: `?([^`\n]+)`?", p, re.M))
    assert shown_v == {v.name for v in oracle if v.base in gt}, (u, shown_v, gt)
    assert shown_t <= gt and gt <= shown_t.union(*[v.source_tables() for v in oracle if v.name in shown_v]), (u, shown_t, gt)
new3 = [json.loads(l) for l in (out2 / "predictions_vsql.jsonl").read_text().splitlines()]
assert all(r["impl"] == 6 and r["coverage"] == 1.0 for r in new3)
assert "D' = ORACLE" in (out2 / "summary.md").read_text()
summary = (out2 / "summary.md").read_text()
assert f"So cau hoi chung cho moi cau hinh: **{N}**" in summary
assert "## 5. Tach giai doan" in summary and "### Theo so bang trong SQL dap an" in summary

# DIN-SQL (bo self-correction) va DAIL-SQL (1 mau, khong bau chon), voi LLM gia lap
from vsql import baselines as B  # noqa: E402
from vsql import din_prompts as DP  # noqa: E402
assert DP.HUMAN_EASY_CLASS_TEMPLATE.rstrip().endswith("SQL:") and not hasattr(DP, "SYSTEM_SELF_CORRECTION_PROMPT")
assert B._din_links('...\nSchema_links: [superhero.id, publisher.publisher_name]') == ["superhero.id", "publisher.publisher_name"]
assert B._din_label('So ... "NON-NESTED".\nLabel: "NON-NESTED"') == ("NON-NESTED", [])
# DIN-SQL nhu ban goc: chi doc phan sau "SQL:"; khong co "SQL:" -> placeholder (ke ca khi tra loi co SELECT)
class _Ask:
    def __init__(self, outs):
        self.outs = list(outs)

    def __call__(self, p, stage, **o):
        return self.outs.pop(0)
_ctx = type("C", (), {"lazy": lambda self, k, fn: "", "path": "x"})()
_args = type("A", (), {"evidence": True})()
_it = dict(question="q", evidence="")
for _out, want in [("```sql\nSELECT 1 FROM t;\n```", "SELECT * FROM table"), ("SELECT MAX(a) FROM t", "SELECT * FROM table"),
                  ("Let's think.\nSQL: SELECT 2", "SELECT 2"), ("I cannot answer", "SELECT * FROM table")]:
    got_din = B.run_din(_it, _ctx, _Ask(['Schema_links: [t.a]', 'Label: "EASY"', _out]), {}, _args)
    assert got_din.rstrip(";") == want.rstrip(";"), (_out, got_din)
assert B.dail_post("```sql\nSELECT a FROM t;\n```") == "SELECT a FROM t" and B.dail_post("COUNT(*) FROM t /* x */") == "SELECT COUNT(*) FROM t "
assert B.jaccard_similarity("select _ from _", "select _ from _") == 1.0
din_seen = Counter()
_base = ScriptLLM.chat


def _din_dail(self, prompt, meta=None, **o):
    st, k = meta["stage"], meta["qid"] % len(ITEMS)
    gold = ITEMS[k]["gold"]
    if st.startswith("din_") or st.startswith("dail_"):
        din_seen[st] += 1
        if st == "din_link":
            assert o.get("system") == DP.SYSTEM_SCHEMA_LINKING_TEMPLATE and "3 rows from superhero table:" in prompt
            t = "A: ...\nSchema_links: [superhero.superhero_name, superhero.id]"
        elif st == "din_class":
            assert "Schema links: ['superhero.superhero_name', 'superhero.id']" in prompt
            t = 'Label: "EASY"' if k % 2 == 0 else 'Label: "NON-NESTED"'
        elif st in ("din_easy", "din_nonnested"):
            t = f"Let's think.\nSQL: {gold}"
        elif st.startswith("dail_"):
            assert prompt.startswith("/* Some SQL examples are provided based on similar problems: */\n/* Answer the following: ")
            assert prompt.endswith(" */\nSELECT ") and "CREATE TABLE" in prompt
            t = gold[len("SELECT "):]                        # viet tiep sau "SELECT " nhu ma goc
        else:
            raise AssertionError(st)
        return {"text": t, "prompt_tokens": len(prompt) // 4, "completion_tokens": 5, "seconds": 0.0}
    return _base(self, prompt, meta, **o)


ScriptLLM.chat = _din_dail
llm = ScriptLLM()
try:
    import sql_metadata  # noqa: F401
    have_sm = True
except ImportError:
    have_sm = False
meths = "dinsql" + (",dailsql" if have_sm else "")
train = [dict(db_id="hero_train", question=f"How many heroes have {c} eyes?", evidence=f"{c} refers to colour = '{c}'",
              SQL=f"SELECT COUNT(T1.id) FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id WHERE T2.colour = '{c}'")
         for c in ["Blue", "Green", "Red", "Black", "Brown", "Amber", "Gold", "Grey"]]
(tmp / "train.json").write_text(json.dumps(train))
(tmp / "train_tables.json").write_text(json.dumps([dict(tj[0], db_id="hero_train", table_names=tn,
                                                        column_names=[[t, c.replace("_", " ")] for t, c in cn])]))
(tmp / "dev_tables.json").write_text(json.dumps([dict(tj[0], table_names=tn, column_names=[[t, c.replace("_", " ")] for t, c in cn])]))
B.DailIndex._st_encoder = lambda self: (lambda xs: [[float(len(x)), float(x.count("<mask>"))] for x in xs])
run_compare.main(["--data", str(data), "--db-root", str(db_root), "--out", str(out), "--methods", meths,
                  "--tables-json", str(tmp / "dev_tables.json"), "--no-embed",
                  "--dail-train", str(tmp / "train.json"), "--dail-train-tables", str(tmp / "train_tables.json")], llm=llm)
gd = [json.loads(l) for l in (out / "predictions_dinsql.jsonl").read_text().splitlines()]
assert len(gd) == N and all(r["calls"] == 3 for r in gd) and sum(r["correct"] for r in gd) == N, [r["outcome"] for r in gd]
assert "din_nested" not in din_seen and din_seen["din_easy"] and din_seen["din_nonnested"], din_seen
if have_sm:
    ga = [json.loads(l) for l in (out / "predictions_dailsql.jsonl").read_text().splitlines()]
    assert len(ga) == N and all(r["calls"] in (1, 2) and r["stage1_correct"] for r in ga) and sum(r["correct"] for r in ga) == N
    assert len(ga[0]["dail_examples"]) == 7
else:
    print("[bo qua] DAIL-SQL: chua cai sql_metadata<3")
assert "dinsql" in (out / "summary.md").read_text()
print("\nTAT CA KIEM THU (so sanh) DAT.", ex)

# 8. Ollama tra loi 500 lap lai o mot prompt: ghi nhan cau tra loi rong, khong dung ca lan chay; loi khac van chay tiep
import http.server  # noqa: E402
import threading  # noqa: E402
import vsql.llm as L  # noqa: E402


class _H(http.server.BaseHTTPRequestHandler):
    calls = Counter()

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        p = body["messages"][-1]["content"]
        _H.calls[p] += 1
        if "BOOM" in p or ("FLAKY" in p and _H.calls[p] == 1):
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error":"model runner has unexpectedly stopped"}')
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({"message": {"content": "```sql\nSELECT 1\n```"}, "prompt_eval_count": 5,
                                     "eval_count": 3}).encode())

    def log_message(self, *a):
        pass


srv = http.server.HTTPServer(("127.0.0.1", 0), _H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
L.time.sleep = lambda s: None                                     # khong cho that khi thu lai
llm = L.OllamaLLM("m", f"http://127.0.0.1:{srv.server_port}", str(tmp / "c.sqlite"))
r = llm.chat("BOOM prompt")
assert r["text"] == "" and r["llm_error"].startswith("500") and _H.calls["BOOM prompt"] == 3, (r, _H.calls)
assert llm.chat("BOOM prompt")["llm_error"] and _H.calls["BOOM prompt"] == 3     # da ghi nhan, khong goi lai
r = llm.chat("FLAKY prompt")
assert r["text"].startswith("```sql") and _H.calls["FLAKY prompt"] == 2          # loi 1 lan -> thu lai thanh cong
assert llm.forget_errors() == 1 and llm.cached("BOOM prompt") is None
srv.shutdown()
print("KIEM THU LOI OLLAMA DAT.")
