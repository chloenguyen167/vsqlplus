# Ket qua thuc nghiem V-SQL

So cau hoi chung cho moi cau hinh: **500**

## 1. Execution Accuracy (EX, %)

| Cau hinh | Mo ta | Simple | Moderate | Challenging | Tong | CI 95% |
|---|---|---|---|---|---|---|
| `vsql` | V-SQL theo paper: view Hinh 3 theo JOIN dap an; D' = ORACLE: chi view co bang goc nam trong SQL dap an (+ bang con lai ma dap an dung), prompt Hinh 4 + Hinh 5 | 9.5 (n=148) | 0.4 (n=250) | 2.9 (n=102) | **3.6** | [2.0, 5.2] |
| `vsqlplus` | V-SQL+ = huong 1 (sinh view tu dong) + huong 2 (chon view bang truy hoi lai); giai doan 2 nhu paper | 5.4 (n=148) | 1.2 (n=250) | 0.0 (n=102) | **2.2** | [1.0, 3.4] |
| `vsqlplus_all` | Chi huong 1: view tu dong, dua het view vao prompt (khong chon view) | 4.1 (n=148) | 2.4 (n=250) | 0.0 (n=102) | **2.4** | [1.2, 3.8] |
| `vsqlplus_novote` | V-SQL+ bo bau chon nhieu mau (huong 2) | 3.4 (n=148) | 1.2 (n=250) | 1.0 (n=102) | **1.8** | [0.8, 3.0] |
| `vsqlplus_novl` | V-SQL+ bo lien ket gia tri (huong 2) | 6.8 (n=148) | 2.0 (n=250) | 0.0 (n=102) | **3.0** | [1.6, 4.4] |
| `vsqlplus_nofb` | V-SQL+ bo schema lai (huong 2) | 4.1 (n=148) | 1.2 (n=250) | 0.0 (n=102) | **1.8** | [0.8, 3.0] |
| `vsqlplus_det` | V-SQL+ thay giai doan 2 bang giai ma tat dinh (ngoai de xuat, de doi chieu) | 17.6 (n=148) | 7.6 (n=250) | 2.9 (n=102) | **9.6** | [7.0, 12.2] |
| `dailsql` | DAIL-SQL (baseline Bang 3): schema CREATE TABLE + 7 vi du train BIRD chon 2 vong; 1 mau, khong bau chon nhu paper | 10.8 (n=148) | 4.0 (n=250) | 0.0 (n=102) | **5.2** | [3.4, 7.2] |

## 2a. So sanh ghep cap voi `dailsql` (DAIL-SQL, baseline Bang 3)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsql` | -1.6 | [-3.8, +0.8] | 21 | 13 | 0.229 | 0.229 |
| `vsqlplus` | -3.0 | [-5.2, -1.0] | 21 | 6 | 0.006 | **0.024** |
| `vsqlplus_all` | -2.8 | [-4.8, -0.8] | 20 | 6 | 0.009 | **0.028** |
| `vsqlplus_novote` | -3.4 | [-5.6, -1.2] | 23 | 6 | 0.002 | **0.014** |
| `vsqlplus_novl` | -2.2 | [-4.4, -0.2] | 20 | 9 | 0.061 | 0.123 |
| `vsqlplus_nofb` | -3.4 | [-5.6, -1.4] | 22 | 5 | 0.002 | **0.011** |
| `vsqlplus_det` | +4.4 | [+1.6, +7.2] | 16 | 38 | 0.004 | **0.019** |

## 2b. So sanh ghep cap voi `vsql` (V-SQL tai hien theo paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsqlplus` | -1.4 | [-3.2, +0.2] | 13 | 6 | 0.167 | 0.668 |
| `vsqlplus_all` | -1.2 | [-3.0, +0.4] | 13 | 7 | 0.263 | 0.688 |
| `vsqlplus_novote` | -1.8 | [-3.6, +0.0] | 15 | 6 | 0.078 | 0.392 |
| `vsqlplus_novl` | -0.6 | [-2.4, +1.0] | 11 | 8 | 0.648 | 0.688 |
| `vsqlplus_nofb` | -1.8 | [-3.4, -0.2] | 13 | 4 | 0.049 | 0.294 |
| `vsqlplus_det` | +6.0 | [+3.2, +8.6] | 10 | 40 | 0.000 | **0.000** |
| `dailsql` | +1.6 | [-0.8, +3.8] | 13 | 21 | 0.229 | 0.688 |

p < 0.05 moi coi la khac biet co y nghia thong ke; p Holm da hieu chinh cho nhieu phep so sanh trong cung bang.

## 3. Phan loai ket qua sai (% tren tong so cau)

`schema_column` + `schema_table` + `ambiguous_column` = ao giac schema (dieu paper muon giam).

| Cau hinh | schema_column | schema_table | ambiguous_column | syntax | no_sql | timeout | other_exec | wrong_empty | wrong_result | **Ao giac schema** |
|---|---|---|---|---|---|---|---|---|---|---|
| `vsql` | 17.4 | 49.8 | 0.8 | 6.0 | 11.4 | 0.0 | 2.0 | 0.8 | 8.2 | **68.0** |
| `vsqlplus` | 11.0 | 59.8 | 0.0 | 13.0 | 0.2 | 0.0 | 3.8 | 3.0 | 7.0 | **70.8** |
| `vsqlplus_all` | 27.6 | 48.0 | 0.4 | 9.6 | 0.0 | 0.0 | 2.2 | 2.4 | 7.4 | **76.0** |
| `vsqlplus_novote` | 12.0 | 60.8 | 0.2 | 13.0 | 0.2 | 0.0 | 3.4 | 1.6 | 7.0 | **73.0** |
| `vsqlplus_novl` | 16.0 | 51.8 | 0.2 | 11.8 | 0.0 | 0.2 | 3.8 | 4.0 | 9.2 | **68.0** |
| `vsqlplus_nofb` | 21.4 | 56.8 | 0.0 | 11.0 | 0.0 | 0.0 | 2.2 | 2.0 | 4.8 | **78.2** |
| `vsqlplus_det` | 25.8 | 1.2 | 2.4 | 13.0 | 0.0 | 0.6 | 6.2 | 12.6 | 28.6 | **29.4** |
| `dailsql` | 54.4 | 8.4 | 0.2 | 15.2 | 0.0 | 0.2 | 2.6 | 2.6 | 11.2 | **63.0** |

## 4. Chi phi (trung binh moi cau)

| Cau hinh | So lan goi LLM | Token vao | Token ra | Giay LLM | So doi tuong schema | Do phu bang dap an | VES xap xi |
|---|---|---|---|---|---|---|---|
| `vsql` | 1.89 | 5041 | 124 | 2.0 | 1.9 | 100.0 | 4.3 |
| `vsqlplus` | 4.52 | 24038 | 315 | 4.6 | 4.7 | 96.6 | 2.3 |
| `vsqlplus_all` | 1.62 | 7460 | 102 | 1.6 | 7.3 | 100.0 | 2.3 |
| `vsqlplus_novote` | 2.49 | 10464 | 175 | 2.7 | 5.4 | 99.8 | 3.1 |
| `vsqlplus_novl` | 4.44 | 22758 | 290 | 4.1 | 4.3 | 89.8 | 3.0 |
| `vsqlplus_nofb` | 3.83 | 20721 | 273 | 3.9 | 4.0 | 94.8 | 1.9 |
| `vsqlplus_det` | 3.79 | 23085 | 265 | 3.9 | 4.7 | 96.6 | 10.1 |
| `dailsql` | 1.50 | 2675 | 352 | 4.4 | 0.0 | 0.0 | 6.8 |

- *Do phu bang dap an*: ti le cau ma moi bang trong SQL dap an deu nam trong schema dua cho LLM (< 100% o V-SQL+ la do buoc chon view bo sot bang).
- *VES xap xi*: sqrt(t_dap_an / t_du_doan) tren cau dung, do 1 lan chay nen chi mang tinh tham khao.

## 5. Tach giai doan 1 / giai doan 2 (tren cung cac cau)

Giai doan 1 = SQL nhap mo rong tat dinh ve bang goc (view -> CTE), tuc la ket qua neu giai doan 2 khong lam sai gi. DAIL-SQL: SQL vong 1 (vi du chon theo cau hoi) so voi vong 2 (vi du chon them theo khung SQL vong 1). DIN-SQL khong tach.

| Cau hinh | Gd1 dung | Cuoi dung | Gd2 sua dung | Gd2 lam hong | Rong | Loi chinh cua cau bi lam hong |
|---|---|---|---|---|---|---|
| `vsql` | 54 (10.8%) | 18 (3.6%) | 3 | 39 | -36 | schema_table 35, wrong_result 2, schema_column 2 |
| `vsqlplus` | 48 (9.6%) | 11 (2.2%) | 1 | 38 | -37 | schema_table 35, schema_column 2, wrong_result 1 |
| `vsqlplus_all` | 29 (5.8%) | 12 (2.4%) | 1 | 18 | -17 | schema_table 17, syntax 1 |
| `vsqlplus_novote` | 36 (7.2%) | 9 (1.8%) | 2 | 29 | -27 | schema_table 25, schema_column 3, wrong_result 1 |
| `vsqlplus_novl` | 39 (7.8%) | 15 (3.0%) | 1 | 25 | -24 | schema_table 24, schema_column 1 |
| `vsqlplus_nofb` | 34 (6.8%) | 9 (1.8%) | 1 | 26 | -25 | schema_table 24, schema_column 2 |
| `vsqlplus_det` | 48 (9.6%) | 48 (9.6%) | 0 | 0 | +0 |  |
| `dailsql` | 23 (4.6%) | 26 (5.2%) | 13 | 10 | +3 | schema_column 8, wrong_result 2 |

## 6. Dong gop rieng cua tung cai tien

| Yeu to | So sanh | dEX |
|---|---|---|
| V-SQL so voi DAIL-SQL | `vsql` - `dailsql` | -1.6 |
| V-SQL+ so voi DAIL-SQL | `vsqlplus` - `dailsql` | -3.0 |
| V-SQL+ so voi V-SQL | `vsqlplus` - `vsql` | -1.4 |
| Huong 1 + prompt moi, dua het view (so voi V-SQL) | `vsqlplus_all` - `vsql` | -1.2 |
| Huong 2: chon view (so voi dua het view) | `vsqlplus` - `vsqlplus_all` | -0.2 |
| Huong 2 - bau chon nhieu mau | `vsqlplus` - `vsqlplus_novote` | +0.4 |
| Huong 2 - lien ket gia tri | `vsqlplus` - `vsqlplus_novl` | -0.8 |
| Huong 2 - schema lai | `vsqlplus` - `vsqlplus_nofb` | +0.4 |
| Giai doan 2 LLM (paper) so voi giai ma tat dinh | `vsqlplus` - `vsqlplus_det` | -7.4 |

## 7. Diem manh / diem yeu (EX %)

### Theo CSDL

| Cau hinh | california_schools (n=30) | card_games (n=52) | codebase_community (n=49) | debit_card_specializing (n=30) | european_football_2 (n=51) | financial (n=32) | formula_1 (n=66) | student_club (n=48) | superhero (n=52) | thrombosis_prediction (n=50) | toxicology (n=40) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `vsql` | 0.0 | 3.8 | 4.1 | 3.3 | 3.9 | 0.0 | 3.0 | 6.2 | 3.8 | 2.0 | 7.5 |
| `vsqlplus` | 0.0 | 9.6 | 0.0 | 0.0 | 2.0 | 0.0 | 0.0 | 6.2 | 0.0 | 2.0 | 2.5 |
| `vsqlplus_all` | 0.0 | 5.8 | 2.0 | 0.0 | 2.0 | 0.0 | 3.0 | 4.2 | 1.9 | 2.0 | 2.5 |
| `vsqlplus_novote` | 0.0 | 7.7 | 0.0 | 0.0 | 2.0 | 0.0 | 0.0 | 4.2 | 0.0 | 2.0 | 2.5 |
| `vsqlplus_novl` | 0.0 | 9.6 | 0.0 | 0.0 | 3.9 | 0.0 | 1.5 | 8.3 | 1.9 | 2.0 | 2.5 |
| `vsqlplus_nofb` | 0.0 | 7.7 | 0.0 | 0.0 | 2.0 | 0.0 | 0.0 | 4.2 | 0.0 | 2.0 | 2.5 |
| `vsqlplus_det` | 0.0 | 17.3 | 8.2 | 6.7 | 15.7 | 0.0 | 6.1 | 16.7 | 17.3 | 6.0 | 2.5 |
| `dailsql` | 0.0 | 3.8 | 12.2 | 6.7 | 3.9 | 6.2 | 1.5 | 14.6 | 3.8 | 0.0 | 5.0 |

### Theo so bang trong SQL dap an

| Cau hinh | 1 (n=86) | 2 (n=314) | 3 (n=84) | 4 (n=16) |
|---|---|---|---|---|
| `vsql` | 16.3 | 1.3 | 0.0 | 0.0 |
| `vsqlplus` | 9.3 | 1.0 | 0.0 | 0.0 |
| `vsqlplus_all` | 8.1 | 1.6 | 0.0 | 0.0 |
| `vsqlplus_novote` | 5.8 | 1.3 | 0.0 | 0.0 |
| `vsqlplus_novl` | 11.6 | 1.6 | 0.0 | 0.0 |
| `vsqlplus_nofb` | 7.0 | 1.0 | 0.0 | 0.0 |
| `vsqlplus_det` | 20.9 | 8.3 | 3.6 | 6.2 |
| `dailsql` | 17.4 | 3.2 | 1.2 | 0.0 |
(4 = tu 4 bang tro len)

## 8. Thong ke view

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
