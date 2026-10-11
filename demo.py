#!/usr/bin/env python3
"""Demo khong can LLM, khong can du lieu BIRD: minh hoa 4 cai tien tren database mau theo schema `superhero`.

    python demo.py            # in ra man hinh
    python demo.py > docs/demo_output.txt

LUU Y: du lieu la ngau nhien do tests/make_toy.py sinh ra, va "LLM" la MockLLM tra loi theo kich ban.
Ket qua o muc 5 chi minh hoa CACH HONG khac nhau cua cac cau hinh, KHONG phai bang chung ve do chinh xac.
"""
import json
import shutil
import sqlite3
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_experiment                      # noqa: E402
from tests.make_toy import ITEMS, make     # noqa: E402
from vsql import views as V                # noqa: E402
from vsql.db import Schema, run_sql        # noqa: E402
from vsql.llm import MockLLM               # noqa: E402


def head(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


tmp = Path(tempfile.mkdtemp())
data, db_root, script = make(tmp)
db = db_root / "superhero" / "superhero.sqlite"
s = Schema("superhero", db)

head("1. Do thi khoa ngoai cua database mau")
print(f"{len(s.tables)} bang, {sum(len(t.fks) for t in s.tables.values())} khoa ngoai")
for t in s.tables.values():
    for fk in t.fks:
        print(f"  {fk.table}.{','.join(fk.cols)} -> {fk.ref_table}.{','.join(fk.ref_cols)}"
              f"   [phia cha duy nhat: {s.safe_fk(fk)}]")

head("2. CAI TIEN 2 - View tu dong theo huong N-1 (khong nhin dap an)")
auto = V.validate(s, V.auto_views(s))
for v in auto:
    j = ", ".join(f"{x.table} AS {x.alias}" for x in v.joins)
    print(f"  {v.name:<18} {len(v.cols):>2} cot | kiem tra so dong: {v.verified:<11} | noi: {j}")
print("\nMo ta v_superhero dua vao prompt (rut gon):")
print("\n".join(next(v for v in auto if v.name == "v_superhero").describe(s).splitlines()[:24]), "\n  ...")

head("3. CAI TIEN 1 - Viet lai tat dinh: dummy SQL -> SQL tren bang goc (khong goi LLM)")
dummy = ITEMS[1]["dummy"]
print("Dummy SQL tren view :", dummy)
for prune in (False, True):
    sql, used = V.unfold(dummy, auto, prune)
    print(f"\nSau khi mo rong view, prune={prune} ({sql.count('LEFT JOIN')} LEFT JOIN):\n  {sql}")

real = tmp / "real.sqlite"                 # ban sao co view that, de lam "chuan"
shutil.copy(db, real)
con = sqlite3.connect(real)
for v in auto:
    con.execute(v.ddl().rstrip(";"))
con.commit()
con.close()
queries = [it["dummy"] for it in ITEMS] + [
    "SELECT * FROM v_superhero WHERE race = 'Alien'",
    "SELECT gender, COUNT(*), AVG(weight_kg) FROM v_superhero GROUP BY gender",
    "SELECT hero_gender, MAX(attribute_value) FROM v_hero_attribute GROUP BY hero_gender",
    "SELECT a.superhero_name, b.power_name FROM v_superhero a JOIN v_hero_power b ON a.id = b.hero_id WHERE a.eye_colour = 'Blue'",
    "SELECT COUNT(*) FROM v_superhero WHERE skin_colour = hair_colour",
]
ok = 0
for q in queries:
    want, _, _ = run_sql(real, q)
    for prune in (True, False):
        got, err, _ = run_sql(db, V.unfold(q, auto, prune)[0])
        ok += err is None and Counter(got) == Counter(want)
print(f"\nDoi chung voi view that cua SQLite: {ok}/{2 * len(queries)} phep thu cho ket qua giong het "
      f"({len(queries)} truy van x {{co, khong}} cat JOIN thua)")

head("4. Rui ro cua view kieu paper: quan he 1-N lam nhan ban dong")
oracle = V.validate(s, V.oracle_views(s, [it["gold"] for it in ITEMS]))
for v in oracle:
    print(f"  {v.name:<50} {v.origin:<10} {v.verified}")
fan = next((v for v in oracle if v.origin == "oracle_fan"), None)
if fan:
    n_view = run_sql(db, f"SELECT COUNT(*), COUNT(DISTINCT hero_id), AVG(superhero_height_cm) FROM ({fan.select_sql()})")[0][0]
    n_true = run_sql(db, "SELECT COUNT(*), COUNT(DISTINCT id), AVG(height_cm) FROM superhero")[0][0]
    print(f"\n  COUNT(*) / so hero khac nhau / AVG(chieu cao) tren view 1-N: {n_view[0]} / {n_view[1]} / {n_view[2]:.2f}")
    print(f"  cung 3 so tren bang superhero                              : {n_true[0]} / {n_true[1]} / {n_true[2]:.2f}")
    print("  -> COUNT(*) va AVG sai neu LLM viet tren view nay; buoc kiem tra so dong cua CT2 phat hien duoc.")

head("5. Duong ong day du voi MockLLM theo kich ban (chi minh hoa dang loi, KHONG do do chinh xac)")
out = tmp / "out"
sys.stdout.flush()
_stdout = sys.stdout
sys.stdout = open(tmp / "log.txt", "w", encoding="utf-8")        # an log cua run_experiment
run_experiment.main(["--data", str(data), "--db-root", str(db_root), "--out", str(out), "--topk", "4",
                     "--views-dir", str(tmp / "none")], llm=MockLLM(script))
sys.stdout.close()
sys.stdout = _stdout
methods = list(run_experiment.METHODS)
preds = {m: [json.loads(x) for x in (out / f"predictions_{m}.jsonl").read_text(encoding="utf-8").splitlines()] for m in methods}
print(f"{'Cau':<4}{'Cau hoi':<52}" + "".join(f"{m:<14}" for m in methods))
for i, it in enumerate(ITEMS):
    print(f"{i:<4}{it['q'][:50]:<52}" + "".join(f"{preds[m][i]['outcome']:<14}" for m in methods))
print("\nSo lan goi LLM / cau: " + ", ".join(f"{m}={preds[m][0]['calls']}" for m in methods))
print("LUU Y: MockLLM duoc kich ban san (base/hybrid duoc cho SQL dung), nen 'correct' KHONG co nghia cau hinh do tot hon.")
print("Giai thich: cau 3 la loi ao giac cua Table 1 trong paper (hero_attribute.attribute_name) o buoc LLM tai tao;\n"
      "viet lai tat dinh khong the mac loi nay. Cau 4 (dem bang publisher) cho thay view-only mat thong tin ve bang\n"
      "tra cuu khong co hero -> schema lai (hybrid) khac phuc.")

head("6. CAI TIEN 4 - Do phu truy xuat theo k (BM25, khong goi LLM)")
sys.stdout = open(tmp / "log2.txt", "w", encoding="utf-8")
run_experiment.main(["--data", str(data), "--db-root", str(db_root), "--out", str(tmp / "sw"), "--retrieval-sweep",
                     "--views-dir", str(tmp / "none")])
sys.stdout.close()
sys.stdout = _stdout
print((tmp / "sw" / "retrieval_sweep.csv").read_text())
