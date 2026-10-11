"""Kiem thu phan tat dinh + duong ong (MockLLM). Chay: python tests/test_all.py"""
import shutil
import sqlite3
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.make_toy import ITEMS, make                      # noqa: E402
from vsql import views as V                                 # noqa: E402
from vsql.db import Schema, run_sql                         # noqa: E402
from vsql.llm import MockLLM, extract_sql                   # noqa: E402
from vsql.report import mcnemar                             # noqa: E402
import run_experiment                                       # noqa: E402

tmp = Path(tempfile.mkdtemp())
data, db_root, script = make(tmp)
db = db_root / "superhero" / "superhero.sqlite"
s = Schema("superhero", db)

# 1. view tu dong: dung 3 view nhu paper, giu nguyen so dong, bang colour duoc noi 3 lan
auto = V.validate(s, V.auto_views(s))
assert sorted(v.name for v in auto) == ["v_hero_attribute", "v_hero_power", "v_superhero"], [v.name for v in auto]
assert all(v.verified == "rows_equal" for v in auto), [(v.name, v.verified) for v in auto]
vsh = next(v for v in auto if v.name == "v_superhero")
names = [c.name for c in vsh.cols]
assert {"eye_colour", "hair_colour", "skin_colour", "gender", "race", "publisher_name", "alignment"} <= set(names), names
assert len(names) == len({n.lower() for n in names})
assert sum(j.table == "colour" for j in vsh.joins) == 3

# 2. view kieu paper (theo dap an): co view 1-N nhan ban dong, bi kiem tra tu dong phat hien
oracle = V.validate(s, V.oracle_views(s, [it["gold"] for it in ITEMS]))
fan = [v for v in oracle if v.origin == "oracle_fan"]
assert fan and not fan[0].row_preserving and fan[0].verified.startswith("rows_differ"), [(v.name, v.verified) for v in oracle]

# 3. viet lai tat dinh == chay tren VIEW that cua SQLite (co va khong cat JOIN)
real = tmp / "real.sqlite"
shutil.copy(db, real)
con = sqlite3.connect(real)
for v in auto:
    con.execute(v.ddl().rstrip(";"))
con.commit()
con.close()
extra = ["SELECT * FROM v_superhero WHERE race = 'Alien'",
         "SELECT gender, COUNT(*), AVG(weight_kg) FROM v_superhero GROUP BY gender ORDER BY 2 DESC",
         "SELECT a.superhero_name, b.power_name FROM v_superhero a JOIN v_hero_power b ON a.id = b.hero_id WHERE a.eye_colour = 'Blue'",
         "WITH x AS (SELECT hero_id FROM v_hero_attribute WHERE attribute_name = 'Speed' AND attribute_value = 100) "
         "SELECT COUNT(*) FROM v_superhero WHERE id IN (SELECT hero_id FROM x)",
         "SELECT hero_gender, MAX(attribute_value) FROM v_hero_attribute GROUP BY hero_gender"]
for q in [it["dummy"] for it in ITEMS] + extra:
    want, err, _ = run_sql(real, q)
    assert err is None, (q, err)
    for prune in (True, False):
        sql, used = V.unfold(q, auto, prune)
        got, err, _ = run_sql(db, sql)
        assert err is None and used, (sql, err)
        assert Counter(got) == Counter(want), (q, prune)
pruned, _ = V.unfold(ITEMS[0]["dummy"], auto, True)
assert pruned.count("LEFT JOIN") == 1 and V.unfold(ITEMS[0]["dummy"], auto, False)[0].count("LEFT JOIN") == 7, pruned

# 4. tien ich
assert extract_sql("<think>x</think>Here:\n```sql\nSELECT 1;\n```") == "SELECT 1"
assert abs(mcnemar(0, 5) - 0.0625) < 1e-9 and mcnemar(3, 3) == 1.0

# 5. toan bo duong ong voi MockLLM (so lieu chi de kiem tra ma, khong co y nghia khoa hoc)
out = tmp / "out"
run_experiment.main(["--data", str(data), "--db-root", str(db_root), "--out", str(out), "--topk", "4",
                     "--views-dir", str(tmp / "none")], llm=MockLLM(script))
import json
got = {m: [json.loads(l) for l in (out / f"predictions_{m}.jsonl").read_text().splitlines()] for m in run_experiment.CORE}
ex = {m: sum(r["correct"] for r in rs) for m, rs in got.items()}
assert ex["base"] == 7 and ex["vsql"] == 6 and ex["vsql_det"] == 6 and ex["auto_det"] == 6 and ex["hybrid"] == 7, ex
assert got["vsql"][3]["outcome"] == "schema_column"            # ao giac kieu Table 1 duoc phan loai dung
assert got["vsql"][0]["calls"] == 2 and got["vsql_det"][0]["calls"] == 1
print("\nTAT CA KIEM THU DAT.", ex)
