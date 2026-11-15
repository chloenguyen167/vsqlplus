# Ket qua thuc nghiem V-SQL

So cau hoi chung cho moi cau hinh: **500**

## 1. Execution Accuracy (EX, %)

| Cau hinh | Mo ta | Simple | Moderate | Challenging | Tong | CI 95% |
|---|---|---|---|---|---|---|
| `vsql` | V-SQL theo paper: view Hinh 3 theo JOIN dap an, D' chon theo cau hoi (mac dinh LLM chon), prompt Hinh 4 + Hinh 5 | 42.6 (n=148) | 25.6 (n=250) | 14.7 (n=102) | **28.4** | [24.4, 32.4] |
| `vsqlplus` | V-SQL+ = huong 1 (sinh view tu dong) + huong 2 (chon view bang truy hoi lai); giai doan 2 nhu paper | 54.1 (n=148) | 36.4 (n=250) | 29.4 (n=102) | **40.2** | [35.8, 44.6] |
| `dailsql` | DAIL-SQL (baseline Bang 3): schema CREATE TABLE + 7 vi du train BIRD chon 2 vong; 1 mau, khong bau chon nhu paper | 60.1 (n=148) | 43.2 (n=250) | 34.3 (n=102) | **46.4** | [41.8, 50.8] |

## 2a. So sanh ghep cap voi `dailsql` (DAIL-SQL, baseline Bang 3)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsql` | -18.0 | [-22.6, -13.2] | 127 | 37 | 0.000 | **0.000** |
| `vsqlplus` | -6.2 | [-11.0, -1.4] | 89 | 58 | 0.013 | **0.013** |

## 2b. So sanh ghep cap voi `vsql` (V-SQL tai hien theo paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsqlplus` | +11.8 | [+7.6, +16.0] | 30 | 89 | 0.000 | **0.000** |
| `dailsql` | +18.0 | [+13.2, +22.6] | 37 | 127 | 0.000 | **0.000** |

p < 0.05 moi coi la khac biet co y nghia thong ke; p Holm da hieu chinh cho nhieu phep so sanh trong cung bang.

## 3. Phan loai ket qua sai (% tren tong so cau)

`schema_column` + `schema_table` + `ambiguous_column` = ao giac schema (dieu paper muon giam).

| Cau hinh | schema_column | schema_table | ambiguous_column | syntax | no_sql | timeout | other_exec | wrong_empty | wrong_result | **Ao giac schema** |
|---|---|---|---|---|---|---|---|---|---|---|
| `vsql` | 17.8 | 0.8 | 0.0 | 4.0 | 2.8 | 0.2 | 2.2 | 7.0 | 36.8 | **18.6** |
| `vsqlplus` | 16.2 | 0.0 | 0.0 | 1.2 | 0.0 | 0.2 | 1.0 | 4.6 | 36.6 | **16.2** |
| `dailsql` | 9.8 | 0.0 | 0.0 | 5.4 | 0.0 | 0.4 | 1.0 | 6.6 | 30.4 | **9.8** |

## 4. Chi phi (trung binh moi cau)

| Cau hinh | So lan goi LLM | Token vao | Token ra | Giay LLM | So doi tuong schema | Do phu bang dap an | VES xap xi |
|---|---|---|---|---|---|---|---|
| `vsql` | 2.97 | 6082 | 148 | 12.8 | 1.7 | 87.8 | 32.3 |
| `vsqlplus` | 4.12 | 21131 | 215 | 15.8 | 3.8 | 98.2 | 52.5 |
| `dailsql` | 1.72 | 3163 | 566 | 32.7 | 0.0 | 0.0 | 61.4 |

- *Do phu bang dap an*: ti le cau ma moi bang trong SQL dap an deu nam trong schema dua cho LLM (< 100% o V-SQL+ la do buoc chon view bo sot bang).
- *VES xap xi*: sqrt(t_dap_an / t_du_doan) tren cau dung, do 1 lan chay nen chi mang tinh tham khao.

## 5. Tach giai doan 1 / giai doan 2 (tren cung cac cau)

Giai doan 1 = SQL nhap mo rong tat dinh ve bang goc (view -> CTE), tuc la ket qua neu giai doan 2 khong lam sai gi. DAIL-SQL: SQL vong 1 (vi du chon theo cau hoi) so voi vong 2 (vi du chon them theo khung SQL vong 1). DIN-SQL khong tach.

| Cau hinh | Gd1 dung | Cuoi dung | Gd2 sua dung | Gd2 lam hong | Rong | Loi chinh cua cau bi lam hong |
|---|---|---|---|---|---|---|
| `vsql` | 155 (31.0%) | 142 (28.4%) | 18 | 31 | -13 | schema_column 17, wrong_result 6, syntax 4 |
| `vsqlplus` | 228 (45.6%) | 201 (40.2%) | 14 | 41 | -27 | schema_column 29, wrong_result 10, wrong_empty 1 |
| `dailsql` | 225 (45.0%) | 232 (46.4%) | 37 | 30 | +7 | wrong_result 17, schema_column 8, wrong_empty 3 |

## 6. Dong gop rieng cua tung cai tien

| Yeu to | So sanh | dEX |
|---|---|---|
| V-SQL so voi DAIL-SQL | `vsql` - `dailsql` | -18.0 |
| V-SQL+ so voi DAIL-SQL | `vsqlplus` - `dailsql` | -6.2 |
| V-SQL+ so voi V-SQL | `vsqlplus` - `vsql` | +11.8 |

## 7. Diem manh / diem yeu (EX %)

### Theo CSDL

| Cau hinh | california_schools (n=30) | card_games (n=52) | codebase_community (n=49) | debit_card_specializing (n=30) | european_football_2 (n=51) | financial (n=32) | formula_1 (n=66) | student_club (n=48) | superhero (n=52) | thrombosis_prediction (n=50) | toxicology (n=40) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `vsql` | 0.0 | 34.6 | 22.4 | 13.3 | 35.3 | 21.9 | 31.8 | 45.8 | 50.0 | 12.0 | 22.5 |
| `vsqlplus` | 13.3 | 42.3 | 36.7 | 30.0 | 60.8 | 43.8 | 39.4 | 47.9 | 69.2 | 12.0 | 30.0 |
| `dailsql` | 23.3 | 51.9 | 49.0 | 30.0 | 60.8 | 31.2 | 42.4 | 64.6 | 65.4 | 32.0 | 37.5 |

### Theo so bang trong SQL dap an

| Cau hinh | 1 (n=86) | 2 (n=314) | 3 (n=84) | 4 (n=16) |
|---|---|---|---|---|
| `vsql` | 45.3 | 26.1 | 21.4 | 18.8 |
| `vsqlplus` | 53.5 | 39.5 | 29.8 | 37.5 |
| `dailsql` | 60.5 | 47.1 | 31.0 | 37.5 |
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
