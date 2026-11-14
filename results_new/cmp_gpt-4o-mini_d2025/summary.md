# Ket qua thuc nghiem V-SQL

So cau hoi chung cho moi cau hinh: **500**

## 1. Execution Accuracy (EX, %)

| Cau hinh | Mo ta | Simple | Moderate | Challenging | Tong | CI 95% |
|---|---|---|---|---|---|---|
| `vsql` | V-SQL theo paper: view Hinh 3 theo JOIN dap an, D' chon theo cau hoi (mac dinh LLM chon), prompt Hinh 4 + Hinh 5 | 62.2 (n=148) | 46.4 (n=250) | 25.5 (n=102) | **46.8** | [42.2, 51.4] |
| `vsqlplus` | V-SQL+ = huong 1 (sinh view tu dong) + huong 2 (chon view bang truy hoi lai); giai doan 2 nhu paper | 68.9 (n=148) | 49.6 (n=250) | 35.3 (n=102) | **52.4** | [48.0, 56.8] |
| `vsqlplus_all` | Chi huong 1: view tu dong, dua het view vao prompt (khong chon view) | 62.8 (n=148) | 44.8 (n=250) | 34.3 (n=102) | **48.0** | [43.8, 52.6] |
| `vsqlplus_novote` | V-SQL+ bo bau chon nhieu mau (huong 2) | 68.2 (n=148) | 49.6 (n=250) | 37.3 (n=102) | **52.6** | [48.2, 57.0] |
| `vsqlplus_novl` | V-SQL+ bo lien ket gia tri (huong 2) | 65.5 (n=148) | 42.4 (n=250) | 37.3 (n=102) | **48.2** | [43.8, 52.6] |
| `vsqlplus_nofb` | V-SQL+ bo schema lai (huong 2) | 68.9 (n=148) | 48.8 (n=250) | 34.3 (n=102) | **51.8** | [47.4, 56.2] |
| `vsqlplus_det` | V-SQL+ thay giai doan 2 bang giai ma tat dinh (ngoai de xuat, de doi chieu) | 67.6 (n=148) | 51.2 (n=250) | 37.3 (n=102) | **53.2** | [48.8, 57.6] |
| `vsqlplus_fig4` | V-SQL+ chi 2 huong (view tu dong + chon view); gd1/gd2 cung template + schema nhu vsql | 56.8 (n=148) | 40.8 (n=250) | 35.3 (n=102) | **44.4** | [40.0, 48.8] |
| `dailsql` | DAIL-SQL (baseline Bang 3): schema CREATE TABLE + 7 vi du train BIRD chon 2 vong; 1 mau, khong bau chon nhu paper | 66.2 (n=148) | 47.6 (n=250) | 32.4 (n=102) | **50.0** | [45.4, 54.6] |

## 2a. So sanh ghep cap voi `dailsql` (DAIL-SQL, baseline Bang 3)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsql` | -3.2 | [-7.6, +0.8] | 67 | 51 | 0.167 | 1.000 |
| `vsqlplus` | +2.4 | [-2.4, +7.0] | 56 | 68 | 0.323 | 1.000 |
| `vsqlplus_all` | -2.0 | [-6.0, +2.0] | 56 | 46 | 0.373 | 1.000 |
| `vsqlplus_novote` | +2.6 | [-2.0, +7.0] | 54 | 67 | 0.275 | 1.000 |
| `vsqlplus_novl` | -1.8 | [-6.4, +2.8] | 66 | 57 | 0.471 | 1.000 |
| `vsqlplus_nofb` | +1.8 | [-2.8, +6.2] | 57 | 66 | 0.471 | 1.000 |
| `vsqlplus_det` | +3.2 | [-1.0, +7.4] | 50 | 66 | 0.163 | 1.000 |
| `vsqlplus_fig4` | -5.6 | [-10.2, -1.2] | 81 | 53 | 0.019 | 0.155 |

## 2b. So sanh ghep cap voi `vsql` (V-SQL tai hien theo paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsqlplus` | +5.6 | [+1.6, +9.8] | 41 | 69 | 0.010 | 0.061 |
| `vsqlplus_all` | +1.2 | [-2.8, +5.2] | 51 | 57 | 0.631 | 1.000 |
| `vsqlplus_novote` | +5.8 | [+1.8, +10.2] | 43 | 72 | 0.009 | 0.061 |
| `vsqlplus_novl` | +1.4 | [-2.8, +5.4] | 50 | 57 | 0.562 | 1.000 |
| `vsqlplus_nofb` | +5.0 | [+1.0, +9.0] | 42 | 67 | 0.021 | 0.105 |
| `vsqlplus_det` | +6.4 | [+2.4, +10.4] | 40 | 72 | 0.003 | **0.026** |
| `vsqlplus_fig4` | -2.4 | [-6.0, +1.2] | 47 | 35 | 0.224 | 0.673 |
| `dailsql` | +3.2 | [-0.8, +7.6] | 51 | 67 | 0.167 | 0.668 |

p < 0.05 moi coi la khac biet co y nghia thong ke; p Holm da hieu chinh cho nhieu phep so sanh trong cung bang.

## 3. Phan loai ket qua sai (% tren tong so cau)

`schema_column` + `schema_table` + `ambiguous_column` = ao giac schema (dieu paper muon giam).

| Cau hinh | schema_column | schema_table | ambiguous_column | syntax | no_sql | timeout | other_exec | wrong_empty | wrong_result | **Ao giac schema** |
|---|---|---|---|---|---|---|---|---|---|---|
| `vsql` | 10.4 | 0.0 | 0.0 | 0.8 | 0.0 | 0.0 | 1.4 | 4.2 | 36.4 | **10.4** |
| `vsqlplus` | 7.2 | 0.4 | 0.0 | 0.6 | 0.0 | 0.0 | 1.4 | 4.8 | 33.2 | **7.6** |
| `vsqlplus_all` | 8.6 | 0.0 | 0.0 | 1.4 | 0.0 | 0.2 | 1.2 | 6.4 | 34.2 | **8.6** |
| `vsqlplus_novote` | 6.8 | 0.2 | 0.0 | 1.0 | 0.0 | 0.0 | 1.8 | 6.2 | 31.4 | **7.0** |
| `vsqlplus_novl` | 6.2 | 1.4 | 0.0 | 1.2 | 0.0 | 0.4 | 1.8 | 5.8 | 35.0 | **7.6** |
| `vsqlplus_nofb` | 8.4 | 0.4 | 0.0 | 0.6 | 0.0 | 0.0 | 1.2 | 4.8 | 32.8 | **8.8** |
| `vsqlplus_det` | 0.8 | 0.4 | 0.4 | 0.6 | 0.0 | 0.0 | 2.0 | 5.2 | 37.4 | **1.6** |
| `vsqlplus_fig4` | 7.8 | 0.2 | 0.0 | 1.0 | 0.0 | 0.2 | 3.6 | 5.4 | 37.4 | **8.0** |
| `dailsql` | 9.0 | 0.2 | 0.0 | 4.0 | 0.0 | 0.0 | 1.2 | 4.6 | 31.0 | **9.2** |

## 4. Chi phi (trung binh moi cau)

| Cau hinh | So lan goi LLM | Token vao | Token ra | Giay LLM | So doi tuong schema | Do phu bang dap an | VES xap xi |
|---|---|---|---|---|---|---|---|
| `vsql` | 3.00 | 8219 | 142 | 4.9 | 2.4 | 95.8 | 63.8 |
| `vsqlplus` | 4.04 | 19045 | 204 | 8.7 | 3.8 | 97.8 | 74.3 |
| `vsqlplus_all` | 1.85 | 7085 | 100 | 3.3 | 7.3 | 100.0 | 62.3 |
| `vsqlplus_novote` | 1.93 | 5984 | 105 | 3.6 | 4.8 | 99.8 | 70.5 |
| `vsqlplus_novl` | 4.02 | 18434 | 199 | 6.8 | 3.3 | 93.6 | 68.1 |
| `vsqlplus_nofb` | 4.00 | 18853 | 202 | 8.6 | 3.8 | 97.8 | 70.9 |
| `vsqlplus_det` | 3.17 | 18030 | 152 | 7.0 | 3.8 | 97.8 | 63.2 |
| `vsqlplus_fig4` | 3.97 | 33778 | 259 | 7.5 | 3.9 | 98.8 | 53.9 |
| `dailsql` | 1.75 | 2946 | 479 | 9.6 | 0.0 | 0.0 | 58.0 |

- *Do phu bang dap an*: ti le cau ma moi bang trong SQL dap an deu nam trong schema dua cho LLM (< 100% o V-SQL+ la do buoc chon view bo sot bang).
- *VES xap xi*: sqrt(t_dap_an / t_du_doan) tren cau dung, do 1 lan chay nen chi mang tinh tham khao.

## 5. Tach giai doan 1 / giai doan 2 (tren cung cac cau)

Giai doan 1 = SQL nhap mo rong tat dinh ve bang goc (view -> CTE), tuc la ket qua neu giai doan 2 khong lam sai gi. DAIL-SQL: SQL vong 1 (vi du chon theo cau hoi) so voi vong 2 (vi du chon them theo khung SQL vong 1).

| Cau hinh | Gd1 dung | Cuoi dung | Gd2 sua dung | Gd2 lam hong | Rong | Loi chinh cua cau bi lam hong |
|---|---|---|---|---|---|---|
| `vsql` | 216 (43.2%) | 234 (46.8%) | 31 | 13 | +18 | schema_column 6, wrong_result 5, wrong_empty 2 |
| `vsqlplus` | 266 (53.2%) | 262 (52.4%) | 11 | 15 | -4 | schema_column 8, wrong_result 4, wrong_empty 3 |
| `vsqlplus_all` | 245 (49.0%) | 240 (48.0%) | 10 | 15 | -5 | schema_column 7, wrong_result 5, wrong_empty 2 |
| `vsqlplus_novote` | 267 (53.4%) | 263 (52.6%) | 13 | 17 | -4 | schema_column 9, wrong_empty 5, wrong_result 3 |
| `vsqlplus_novl` | 251 (50.2%) | 241 (48.2%) | 6 | 16 | -10 | schema_column 7, wrong_result 5, wrong_empty 3 |
| `vsqlplus_nofb` | 261 (52.2%) | 259 (51.8%) | 13 | 15 | -2 | schema_column 8, wrong_result 4, wrong_empty 3 |
| `vsqlplus_det` | 266 (53.2%) | 266 (53.2%) | 0 | 0 | +0 |  |
| `vsqlplus_fig4` | 217 (43.4%) | 222 (44.4%) | 23 | 18 | +5 | schema_column 10, wrong_result 5, wrong_empty 3 |
| `dailsql` | 248 (49.6%) | 250 (50.0%) | 23 | 21 | +2 | wrong_result 12, schema_column 7, wrong_empty 1 |

## 6. Dong gop rieng cua tung cai tien

| Yeu to | So sanh | dEX |
|---|---|---|
| V-SQL so voi DAIL-SQL | `vsql` - `dailsql` | -3.2 |
| V-SQL+ so voi DAIL-SQL | `vsqlplus` - `dailsql` | +2.4 |
| V-SQL+ so voi V-SQL | `vsqlplus` - `vsql` | +5.6 |
| Huong 1 + prompt moi, dua het view (so voi V-SQL) | `vsqlplus_all` - `vsql` | +1.2 |
| Huong 2: chon view (so voi dua het view) | `vsqlplus` - `vsqlplus_all` | +4.4 |
| Huong 2 - bau chon nhieu mau | `vsqlplus` - `vsqlplus_novote` | -0.2 |
| Huong 2 - lien ket gia tri | `vsqlplus` - `vsqlplus_novl` | +4.2 |
| Huong 2 - schema lai | `vsqlplus` - `vsqlplus_nofb` | +0.6 |
| Giai doan 2 LLM (paper) so voi giai ma tat dinh | `vsqlplus` - `vsqlplus_det` | -0.8 |
| 2 huong cai tien, cung template + schema (so voi V-SQL) | `vsqlplus_fig4` - `vsql` | -2.4 |
| Tac dung rieng cua prompt gd1 moi (V-SQL+ hien tai so voi ban Hinh 4) | `vsqlplus` - `vsqlplus_fig4` | +8.0 |

## 7. Diem manh / diem yeu (EX %)

### Theo CSDL

| Cau hinh | california_schools (n=30) | card_games (n=52) | codebase_community (n=49) | debit_card_specializing (n=30) | european_football_2 (n=51) | financial (n=32) | formula_1 (n=66) | student_club (n=48) | superhero (n=52) | thrombosis_prediction (n=50) | toxicology (n=40) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `vsql` | 6.7 | 40.4 | 51.0 | 36.7 | 64.7 | 31.2 | 50.0 | 60.4 | 57.7 | 40.0 | 50.0 |
| `vsqlplus` | 13.3 | 38.5 | 51.0 | 50.0 | 68.6 | 56.2 | 47.0 | 66.7 | 69.2 | 42.0 | 62.5 |
| `vsqlplus_all` | 10.0 | 38.5 | 49.0 | 46.7 | 66.7 | 46.9 | 36.4 | 64.6 | 63.5 | 34.0 | 62.5 |
| `vsqlplus_novote` | 13.3 | 50.0 | 46.9 | 50.0 | 64.7 | 56.2 | 42.4 | 70.8 | 69.2 | 42.0 | 62.5 |
| `vsqlplus_novl` | 10.0 | 38.5 | 42.9 | 46.7 | 66.7 | 46.9 | 42.4 | 60.4 | 63.5 | 38.0 | 62.5 |
| `vsqlplus_nofb` | 13.3 | 36.5 | 51.0 | 50.0 | 68.6 | 56.2 | 47.0 | 64.6 | 69.2 | 40.0 | 62.5 |
| `vsqlplus_det` | 20.0 | 42.3 | 44.9 | 50.0 | 72.5 | 59.4 | 43.9 | 64.6 | 76.9 | 40.0 | 62.5 |
| `vsqlplus_fig4` | 10.0 | 48.1 | 38.8 | 33.3 | 60.8 | 40.6 | 42.4 | 56.2 | 67.3 | 26.0 | 45.0 |
| `dailsql` | 13.3 | 51.9 | 53.1 | 50.0 | 66.7 | 18.8 | 42.4 | 62.5 | 73.1 | 42.0 | 52.5 |

### Theo so bang trong SQL dap an

| Cau hinh | 1 (n=86) | 2 (n=314) | 3 (n=84) | 4 (n=16) |
|---|---|---|---|---|
| `vsql` | 62.8 | 48.1 | 31.0 | 18.8 |
| `vsqlplus` | 68.6 | 52.5 | 38.1 | 37.5 |
| `vsqlplus_all` | 57.0 | 51.3 | 31.0 | 25.0 |
| `vsqlplus_novote` | 67.4 | 53.5 | 36.9 | 37.5 |
| `vsqlplus_novl` | 59.3 | 50.6 | 32.1 | 25.0 |
| `vsqlplus_nofb` | 68.6 | 51.9 | 36.9 | 37.5 |
| `vsqlplus_det` | 66.3 | 53.8 | 39.3 | 43.8 |
| `vsqlplus_fig4` | 52.3 | 46.5 | 32.1 | 25.0 |
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
