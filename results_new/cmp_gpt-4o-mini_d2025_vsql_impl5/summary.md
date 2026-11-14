# Ket qua thuc nghiem V-SQL

So cau hoi chung cho moi cau hinh: **500**

## 1. Execution Accuracy (EX, %)

| Cau hinh | Mo ta | Simple | Moderate | Challenging | Tong | CI 95% |
|---|---|---|---|---|---|---|
| `vsql` | V-SQL theo paper: view Hinh 3 theo JOIN dap an, D' = moi view cua CSDL, prompt Hinh 4 + Hinh 5 | 62.8 (n=148) | 43.2 (n=250) | 28.4 (n=102) | **46.0** | [41.4, 50.4] |
| `vsqlplus` | V-SQL+ = huong 1 (sinh view tu dong) + huong 2 (chon view bang truy hoi lai); giai doan 2 nhu paper | 68.9 (n=148) | 49.6 (n=250) | 35.3 (n=102) | **52.4** | [48.0, 56.8] |
| `dailsql` | DAIL-SQL (baseline Bang 3): schema CREATE TABLE + 7 vi du train BIRD chon 2 vong; 1 mau, khong bau chon nhu paper | 66.2 (n=148) | 47.6 (n=250) | 32.4 (n=102) | **50.0** | [45.4, 54.6] |

## 2a. So sanh ghep cap voi `dailsql` (DAIL-SQL, baseline Bang 3)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsql` | -4.0 | [-8.4, +0.4] | 70 | 50 | 0.082 | 0.165 |
| `vsqlplus` | +2.4 | [-2.4, +7.0] | 56 | 68 | 0.323 | 0.323 |

## 2b. So sanh ghep cap voi `vsql` (V-SQL tai hien theo paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsqlplus` | +6.4 | [+2.2, +10.6] | 42 | 74 | 0.004 | **0.008** |
| `dailsql` | +4.0 | [-0.4, +8.4] | 50 | 70 | 0.082 | 0.082 |

p < 0.05 moi coi la khac biet co y nghia thong ke; p Holm da hieu chinh cho nhieu phep so sanh trong cung bang.

## 3. Phan loai ket qua sai (% tren tong so cau)

`schema_column` + `schema_table` + `ambiguous_column` = ao giac schema (dieu paper muon giam).

| Cau hinh | schema_column | schema_table | ambiguous_column | syntax | no_sql | timeout | other_exec | wrong_empty | wrong_result | **Ao giac schema** |
|---|---|---|---|---|---|---|---|---|---|---|
| `vsql` | 12.6 | 0.0 | 0.0 | 1.0 | 0.0 | 0.0 | 1.8 | 3.8 | 34.8 | **12.6** |
| `vsqlplus` | 7.2 | 0.4 | 0.0 | 0.6 | 0.0 | 0.0 | 1.4 | 4.8 | 33.2 | **7.6** |
| `dailsql` | 9.0 | 0.2 | 0.0 | 4.0 | 0.0 | 0.0 | 1.2 | 4.6 | 31.0 | **9.2** |

## 4. Chi phi (trung binh moi cau)

| Cau hinh | So lan goi LLM | Token vao | Token ra | Giay LLM | So doi tuong schema | Do phu bang dap an | VES xap xi |
|---|---|---|---|---|---|---|---|
| `vsql` | 2.00 | 14412 | 129 | 4.6 | 6.4 | 100.0 | 57.5 |
| `vsqlplus` | 4.04 | 19045 | 204 | 8.7 | 3.8 | 97.8 | 74.3 |
| `dailsql` | 1.75 | 2946 | 479 | 9.6 | 0.0 | 0.0 | 58.0 |

- *Do phu bang dap an*: ti le cau ma moi bang trong SQL dap an deu nam trong schema dua cho LLM (< 100% o V-SQL+ la do buoc chon view bo sot bang).
- *VES xap xi*: sqrt(t_dap_an / t_du_doan) tren cau dung, do 1 lan chay nen chi mang tinh tham khao.

## 5. Tach giai doan 1 / giai doan 2 (tren cung cac cau)

Giai doan 1 = SQL nhap mo rong tat dinh ve bang goc (view -> CTE), tuc la ket qua neu giai doan 2 khong lam sai gi. DAIL-SQL: SQL vong 1 (vi du chon theo cau hoi) so voi vong 2 (vi du chon them theo khung SQL vong 1).

| Cau hinh | Gd1 dung | Cuoi dung | Gd2 sua dung | Gd2 lam hong | Rong | Loi chinh cua cau bi lam hong |
|---|---|---|---|---|---|---|
| `vsql` | 226 (45.2%) | 230 (46.0%) | 23 | 19 | +4 | schema_column 12, wrong_result 6, wrong_empty 1 |
| `vsqlplus` | 266 (53.2%) | 262 (52.4%) | 11 | 15 | -4 | schema_column 8, wrong_result 4, wrong_empty 3 |
| `dailsql` | 248 (49.6%) | 250 (50.0%) | 23 | 21 | +2 | wrong_result 12, schema_column 7, wrong_empty 1 |

## 6. Dong gop rieng cua tung cai tien

| Yeu to | So sanh | dEX |
|---|---|---|
| V-SQL so voi DAIL-SQL | `vsql` - `dailsql` | -4.0 |
| V-SQL+ so voi DAIL-SQL | `vsqlplus` - `dailsql` | +2.4 |
| V-SQL+ so voi V-SQL | `vsqlplus` - `vsql` | +6.4 |

## 7. Diem manh / diem yeu (EX %)

### Theo CSDL

| Cau hinh | california_schools (n=30) | card_games (n=52) | codebase_community (n=49) | debit_card_specializing (n=30) | european_football_2 (n=51) | financial (n=32) | formula_1 (n=66) | student_club (n=48) | superhero (n=52) | thrombosis_prediction (n=50) | toxicology (n=40) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `vsql` | 6.7 | 46.2 | 40.8 | 46.7 | 51.0 | 37.5 | 47.0 | 60.4 | 59.6 | 42.0 | 50.0 |
| `vsqlplus` | 13.3 | 38.5 | 51.0 | 50.0 | 68.6 | 56.2 | 47.0 | 66.7 | 69.2 | 42.0 | 62.5 |
| `dailsql` | 13.3 | 51.9 | 53.1 | 50.0 | 66.7 | 18.8 | 42.4 | 62.5 | 73.1 | 42.0 | 52.5 |

### Theo so bang trong SQL dap an

| Cau hinh | 1 (n=86) | 2 (n=314) | 3 (n=84) | 4 (n=16) |
|---|---|---|---|---|
| `vsql` | 60.5 | 46.8 | 32.1 | 25.0 |
| `vsqlplus` | 68.6 | 52.5 | 38.1 | 37.5 |
| `dailsql` | 67.4 | 51.3 | 31.0 | 31.2 |
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
