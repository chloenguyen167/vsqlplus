# Ket qua thuc nghiem V-SQL

So cau hoi chung cho moi cau hinh: **500**

## 1. Execution Accuracy (EX, %)

| Cau hinh | Mo ta | Simple | Moderate | Challenging | Tong | CI 95% |
|---|---|---|---|---|---|---|
| `tasql` | TA-SQL (baseline cua paper): TASL dummy SQL + TALOG SR->SQL | 63.5 (n=148) | 31.6 (n=250) | 16.7 (n=102) | **38.0** | [33.8, 42.0] |
| `vsql` | V-SQL dung theo paper: view theo JOIN dap an, schema Bang 6, prompt Hinh 4 + Hinh 5 | 31.1 (n=148) | 15.6 (n=250) | 10.8 (n=102) | **19.2** | [15.6, 22.8] |
| `vsqlplus` | V-SQL+ = huong 1 (sinh view tu dong) + huong 2 (chon view bang truy hoi lai); giai doan 2 nhu paper | 39.9 (n=148) | 26.0 (n=250) | 22.5 (n=102) | **29.4** | [25.4, 33.6] |

## 2a. So sanh ghep cap voi `tasql` (TA-SQL, baseline cua paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsql` | -18.8 | [-23.2, -14.4] | 119 | 25 | 0.000 | **0.000** |
| `vsqlplus` | -8.6 | [-13.0, -3.8] | 93 | 50 | 0.000 | **0.000** |

## 2b. So sanh ghep cap voi `vsql` (V-SQL theo paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `tasql` | +18.8 | [+14.4, +23.2] | 25 | 119 | 0.000 | **0.000** |
| `vsqlplus` | +10.2 | [+6.2, +14.4] | 27 | 78 | 0.000 | **0.000** |

p < 0.05 moi coi la khac biet co y nghia thong ke; p Holm da hieu chinh cho nhieu phep so sanh trong cung bang.

## 3. Phan loai ket qua sai (% tren tong so cau)

`schema_column` + `schema_table` + `ambiguous_column` = ao giac schema (dieu paper muon giam).

| Cau hinh | schema_column | schema_table | ambiguous_column | syntax | no_sql | timeout | other_exec | wrong_empty | wrong_result | **Ao giac schema** |
|---|---|---|---|---|---|---|---|---|---|---|
| `tasql` | 14.8 | 0.8 | 0.0 | 10.0 | 0.0 | 0.2 | 3.6 | 3.8 | 28.8 | **15.6** |
| `vsql` | 32.0 | 0.6 | 0.0 | 6.8 | 0.0 | 0.4 | 3.2 | 7.2 | 30.6 | **32.6** |
| `vsqlplus` | 27.4 | 1.0 | 0.2 | 4.4 | 0.0 | 0.4 | 3.0 | 5.0 | 29.2 | **28.6** |

## 4. Chi phi (trung binh moi cau)

| Cau hinh | So lan goi LLM | Token vao | Token ra | Giay LLM | So doi tuong schema | Do phu bang dap an | VES xap xi |
|---|---|---|---|---|---|---|---|
| `tasql` | 3.00 | 6587 | 382 | 10.1 | 2.1 | 85.4 | 51.3 |
| `vsql` | 2.00 | 4141 | 127 | 4.5 | 4.4 | 100.0 | 20.5 |
| `vsqlplus` | 4.14 | 21297 | 218 | 7.7 | 3.9 | 98.0 | 47.5 |

- *Do phu bang dap an*: ti le cau ma moi bang trong SQL dap an deu nam trong schema dua cho LLM (< 100% o `hybrid_ret` la loi cua buoc truy xuat).
- *VES xap xi*: sqrt(t_dap_an / t_du_doan) tren cau dung, do 1 lan chay nen chi mang tinh tham khao.

## 5. Dong gop rieng cua tung cai tien

| Yeu to | So sanh | dEX |
|---|---|---|
| V-SQL (paper) so voi TA-SQL | `vsql` - `tasql` | -18.8 |
| V-SQL+ so voi V-SQL (paper) | `vsqlplus` - `vsql` | +10.2 |
| V-SQL+ so voi TA-SQL | `vsqlplus` - `tasql` | -8.6 |

## 6. Thong ke view

| DB | Bang | FK | View oracle (trong do co nhan ban dong) | View auto | View auto giu nguyen so dong |
|---|---|---|---|---|---|
| california_schools | 3 | 2 | 2 (0) | 1 | 1 |
| card_games | 6 | 4 | 4 (0) | 1 | 1 |
| codebase_community | 8 | 13 | 7 (0) | 7 | 7 |
| debit_card_specializing | 5 | 4 | 2 (0) | 2 | 2 |
| european_football_2 | 7 | 31 | 3 (0) | 3 | 3 |
| financial | 8 | 8 | 7 (0) | 7 | 7 |
| formula_1 | 13 | 19 | 8 (0) | 8 | 8 |
| student_club | 8 | 8 | 5 (0) | 5 | 5 |
| superhero | 10 | 11 | 3 (0) | 3 | 3 |
| thrombosis_prediction | 3 | 2 | 2 (0) | 2 | 2 |
| toxicology | 4 | 5 | 3 (0) | 3 | 3 |
