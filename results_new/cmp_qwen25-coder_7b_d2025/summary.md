# Ket qua thuc nghiem V-SQL

So cau hoi chung cho moi cau hinh: **500**

## 1. Execution Accuracy (EX, %)

| Cau hinh | Mo ta | Simple | Moderate | Challenging | Tong | CI 95% |
|---|---|---|---|---|---|---|
| `tasql` | TA-SQL (baseline cua paper): TASL dummy SQL + TALOG SR->SQL | 68.9 (n=148) | 38.0 (n=250) | 25.5 (n=102) | **44.6** | [40.0, 49.0] |
| `vsqlplus` | V-SQL+ = huong 1 (sinh view tu dong) + huong 2 (chon view bang truy hoi lai); giai doan 2 nhu paper | 54.1 (n=148) | 43.6 (n=250) | 25.5 (n=102) | **43.0** | [38.6, 47.2] |
| `vsql_fair` | V-SQL dung phan paper quy dinh (Hinh 3/4/5); phan paper khong noi chinh cho ngang TA-SQL | 45.9 (n=148) | 35.2 (n=250) | 20.6 (n=102) | **35.4** | [31.2, 39.8] |

## 2a. So sanh ghep cap voi `tasql` (TA-SQL, baseline cua paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsqlplus` | -1.6 | [-6.4, +3.2] | 77 | 69 | 0.563 | 0.563 |
| `vsql_fair` | -9.2 | [-14.0, -4.4] | 95 | 49 | 0.000 | **0.000** |

## 2b. So sanh ghep cap voi `vsql_fair` (V-SQL chinh phan paper khong noi)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `tasql` | +9.2 | [+4.4, +14.0] | 49 | 95 | 0.000 | **0.000** |
| `vsqlplus` | +7.6 | [+3.4, +11.8] | 40 | 78 | 0.001 | **0.001** |

p < 0.05 moi coi la khac biet co y nghia thong ke; p Holm da hieu chinh cho nhieu phep so sanh trong cung bang.

## 3. Phan loai ket qua sai (% tren tong so cau)

`schema_column` + `schema_table` + `ambiguous_column` = ao giac schema (dieu paper muon giam).

| Cau hinh | schema_column | schema_table | ambiguous_column | syntax | no_sql | timeout | other_exec | wrong_empty | wrong_result | **Ao giac schema** |
|---|---|---|---|---|---|---|---|---|---|---|
| `tasql` | 14.0 | 0.0 | 0.6 | 0.8 | 0.0 | 0.0 | 5.6 | 5.0 | 29.4 | **14.6** |
| `vsqlplus` | 19.2 | 2.0 | 2.8 | 0.4 | 0.0 | 0.0 | 1.4 | 4.2 | 27.0 | **24.0** |
| `vsql_fair` | 23.4 | 2.8 | 1.6 | 0.8 | 1.4 | 0.0 | 2.8 | 4.2 | 27.6 | **27.8** |

## 4. Chi phi (trung binh moi cau)

| Cau hinh | So lan goi LLM | Token vao | Token ra | Giay LLM | So doi tuong schema | Do phu bang dap an | VES xap xi |
|---|---|---|---|---|---|---|---|
| `tasql` | 3.00 | 6406 | 346 | 12.1 | 2.1 | 82.6 | 65.0 |
| `vsqlplus` | 4.12 | 20999 | 210 | 9.1 | 3.9 | 99.0 | 48.8 |
| `vsql_fair` | 1.77 | 8580 | 148 | 9.1 | 7.3 | 100.0 | 38.6 |

- *Do phu bang dap an*: ti le cau ma moi bang trong SQL dap an deu nam trong schema dua cho LLM (< 100% o V-SQL+ la do buoc chon view bo sot bang).
- *VES xap xi*: sqrt(t_dap_an / t_du_doan) tren cau dung, do 1 lan chay nen chi mang tinh tham khao.

## 5. Dong gop rieng cua tung cai tien

| Yeu to | So sanh | dEX |
|---|---|---|
| V-SQL+ so voi TA-SQL | `vsqlplus` - `tasql` | -1.6 |
| V-SQL chinh phan paper khong noi so voi TA-SQL | `vsql_fair` - `tasql` | -9.2 |

## 6. Thong ke view

| DB | Bang | FK (trong do suy them) | View theo JOIN dap an (V-SQL) / giu so dong | View tu dong (V-SQL+) / giu so dong |
|---|---|---|---|---|
| california_schools | 3 | 2 (0) | 2 / 2 | 1 / 1 |
| card_games | 6 | 4 (0) | 4 / 4 | 1 / 1 |
| codebase_community | 8 | 13 (0) | 7 / 7 | 7 / 7 |
| debit_card_specializing | 5 | 4 (3) | 2 / 2 | 2 / 2 |
| european_football_2 | 7 | 31 (0) | 3 / 3 | 3 / 3 |
| financial | 8 | 8 (0) | 7 / 7 | 7 / 7 |
| formula_1 | 13 | 19 (0) | 8 / 8 | 8 / 8 |
| student_club | 8 | 8 (0) | 5 / 5 | 5 / 5 |
| superhero | 10 | 11 (0) | 3 / 3 | 3 / 3 |
| thrombosis_prediction | 3 | 2 (0) | 2 / 2 | 2 / 2 |
| toxicology | 4 | 5 (0) | 3 / 3 | 3 / 3 |
