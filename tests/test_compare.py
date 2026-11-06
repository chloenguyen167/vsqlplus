"""Kiem thu TA-SQL / V-SQL (paper) / V-SQL+ voi LLM gia lap (khong can Ollama, khong can BIRD).
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
from vsql.methods import _fallback_tables, _tasql_sql, compile_error, first_statement  # noqa: E402
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

# 3. view cua V-SQL (paper) theo JOIN dap an: khong co view nhan ban dong; bang tra cuu van hien (dem publisher duoc)
oracle = V.validate(s, A.oracle_views(s, [it["gold"] for it in ITEMS]))
assert oracle and all(v.row_preserving and v.verified == "rows_equal" for v in oracle), [(v.name, v.verified) for v in oracle]
vis = A.visible_tables(s, oracle)
assert "publisher" in vis and "superhero" not in vis, vis

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
assert _tasql_sql('COUNT(*) FROM superhero"\n\nThis query counts') == "SELECT COUNT(*) FROM superhero"
assert _tasql_sql("```sql\nSELECT COUNT(*) FROM superhero;\n```") == "SELECT COUNT(*) FROM superhero"

# 7. toan bo duong ong voi LLM gia lap (so lieu chi de kiem tra ma, khong co y nghia khoa hoc)
items = json.loads(Path(data).read_text())
items.append(dict(items[0]))                     # ban ghi trung lap (nhu question_id 137/138 cua mini-dev)
Path(data).write_text(json.dumps(items))
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


class ScriptLLM:
    def __init__(self):
        self.stages = Counter()

    def chat(self, prompt, meta=None, **opts):
        u, st = meta["qid"], meta["stage"]
        self.stages[st.rstrip("0123456789")] += 1
        k = u % len(ITEMS)
        gold = ITEMS[k]["gold"]
        if st == "base":
            sql = gold
        elif st == "tasl":
            sql = gold[len("SELECT "):]
        elif st == "talog_sr":
            sql = "df1 = df.where(...)\nres = df1.select(...)"
        elif st == "talog_sql":
            sql = gold[len("SELECT "):] + '"'                 # viet tiep sau SQL = "SELECT, nhu GPT-4 trong ma goc
            return {"text": sql, "prompt_tokens": 1, "completion_tokens": 1, "seconds": 0.0}
        elif st == "vsql_s1":
            sql = PLUS[k].replace("FROM publisher", "FROM v_superhero")       # view-only: dem publisher qua view
        elif st == "vsql_s2":
            sql = ITEMS[k].get("s2", gold)
        elif st == "plus_s2":                                # khoi phuc hoan hao = mo rong tat dinh dummy SQL
            dummy = re.search(r"# view query\nQuestion: .*?\n```sql\n(.*?)\n```", prompt, re.S).group(1)
            sql = V.unfold(dummy, auto)[0]
        elif st.startswith("plus_fb"):
            assert "attribute.attribute_name" in prompt and "does not exist" in prompt
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
assert not (out / "predictions_base.jsonl").exists()         # mac dinh khong chay base
run_compare.main(["--data", str(data), "--db-root", str(db_root), "--out", str(out), "--methods", "base",
                  "--tables-json", str(tmp / "dev_tables.json"), "--no-embed",
                  "--all-max-objects", "0", "--all-max-tokens", "0", "--k-cand", "6", "--n-samples", "3"], llm=llm)
got = {m: [json.loads(l) for l in (out / f"predictions_{m}.jsonl").read_text().splitlines()]
       for m in ["base", "tasql", "vsql", "vsqlplus", "vsqlplus_all", "vsqlplus_novote", "vsqlplus_novl", "vsqlplus_nofb",
                 "vsqlplus_det"]}
assert all(len(r) == len(items) == 8 for r in got.values()), {m: len(r) for m, r in got.items()}   # du ca ban ghi trung
ex = {m: sum(r["correct"] for r in rs) for m, rs in got.items()}
assert ex["base"] == 8 and ex["tasql"] == 8, ex
assert ex["vsql"] == 7, ex                       # sai: ao giac kieu Table 1 cua paper o giai doan 2
assert ex["vsqlplus"] == 8 and ex["vsqlplus_det"] == 8 and ex["vsqlplus_nofb"] == 7 and ex["vsqlplus_all"] == 7, ex
r3 = got["vsqlplus"][3]
assert r3["fallback"] and r3["fallback"][0]["added"] == ["attribute"], r3["fallback"]
assert got["vsqlplus"][0]["vote"]["chosen"], got["vsqlplus"][0]
assert got["vsqlplus_novote"][0].get("vote") is None and got["vsqlplus_all"][0]["all_in_prompt"]
assert got["vsqlplus_det"][0]["calls"] == 4 and got["vsqlplus"][0]["views_used"]
assert got["tasql"][0]["calls"] == 3 and got["vsql"][0]["calls"] == 2 and got["vsqlplus"][0]["calls"] == 5, \
    (got["tasql"][0]["calls"], got["vsql"][0]["calls"], got["vsqlplus"][0]["calls"])
import io, contextlib  # noqa: E402
buf = io.StringIO()
with contextlib.redirect_stdout(buf):                  # chay lai: da cham het, chi in cac dong kiem tra
    run_compare.main(["--data", str(data), "--db-root", str(db_root), "--out", str(out), "--methods", "tasql,vsql",
                      "--tables-json", str(tmp / "dev_tables.json"), "--no-embed"], llm=llm)
o = buf.getvalue()
assert "8 dong; 7 question_id khac nhau; 7 cau hoi" in o and "[KIEM TRA] tasql: 8/8 dong da cham (DU)" in o, o[:600]
summary = (out / "summary.md").read_text()
assert "So cau hoi chung cho moi cau hinh: **8**" in summary
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
