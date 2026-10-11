"""Kiem thu CT5 schema-guard tren CSDL mau (khong can Ollama)."""
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vsql.repair import repair  # noqa: E402

d = Path(tempfile.mkdtemp()) / "t.sqlite"
con = sqlite3.connect(d)
con.executescript("""
CREATE TABLE Patient(ID INTEGER PRIMARY KEY, SEX TEXT, Birthday TEXT);
CREATE TABLE Laboratory(ID INTEGER REFERENCES Patient(ID), Date TEXT, "T-CHO" REAL, UA REAL);
INSERT INTO Patient VALUES (1,'M','1950-01-02'),(2,'F','1960-05-06');
INSERT INTO Laboratory VALUES (1,'1990-01-01',200,7),(2,'1991-01-01',180,5);
""")
con.commit()
cols = {"patient": ["ID", "SEX", "Birthday"], "laboratory": ["ID", "Date", "T-CHO", "UA"]}
columns_of = lambda n: cols.get(n.lower())
fix = lambda sql: repair(sql, str(d), columns_of, ["Patient", "Laboratory"], ["Patient", "Laboratory"])[0]
ok = lambda sql: con.execute(sql).fetchall()

cases = {
    # dung ten bang khi da co alias
    "SELECT Patient.SEX FROM Patient p WHERE p.ID = 1": [("M",)],
    # alias khong ton tai -> cot co o bang khac trong FROM
    "SELECT d.SEX FROM Patient p JOIN Laboratory l ON p.ID = l.ID WHERE l.UA > 6": [("M",)],
    # ten cot gan dung / co tien to
    "SELECT p.Patient_SEX FROM Patient p WHERE p.ID = 2": [("F",)],
    "SELECT l.PatientID FROM Laboratory l WHERE l.UA > 6": [(1,)],
    # cot co ky tu dac biet khong trich dan
    "SELECT SUM(l.T-CHO) FROM Laboratory l": [(380.0,)],
    # ham MySQL
    "SELECT COUNT(*) FROM Patient WHERE YEAR(Birthday) = 1950": [(1,)],
    # dau ; lac giua cau
    "SELECT SEX; FROM Patient WHERE ID = 1": [("M",)],
    # ten bang sai chinh ta
    "SELECT COUNT(*) FROM Patients": [(2,)],
}
bad = 0
for sql, want in cases.items():
    got = fix(sql)
    try:
        res = ok(got)
    except Exception as e:  # noqa: BLE001
        res = f"LOI {e}"
    flag = "OK " if res == want else "SAI"
    bad += res != want
    print(f"{flag} {sql!r}\n    -> {got!r} = {res}")
# CT5b: cot thuoc bang khong co trong FROM -> tu them JOIN theo khoa ngoai
from improve import fk_joiner  # noqa: E402
from vsql.db import Schema  # noqa: E402
jn = fk_joiner(Schema("t", str(d), 0))
for sql, want in {"SELECT COUNT(*) FROM Laboratory WHERE SEX = 'M'": [(1,)],
                  "SELECT l.UA FROM Laboratory l WHERE l.Birthday = '1960-05-06'": [(5.0,)]}.items():
    got = repair(sql, str(d), columns_of, ["Patient", "Laboratory"], ["Patient", "Laboratory"], joiner=jn)[0]
    res = ok(got)
    bad += res != want
    print(("OK " if res == want else "SAI"), repr(sql), "\n    ->", repr(got), "=", res)
# SQL dung thi giu nguyen
assert fix("SELECT SEX FROM Patient WHERE ID = 1") == "SELECT SEX FROM Patient WHERE ID = 1"
assert bad == 0, f"{bad} truong hop sai"
print("TAT CA KIEM THU REPAIR DAT")
