# Ket qua thuc nghiem V-SQL

So cau hoi chung cho moi cau hinh: **200**

## 1. Execution Accuracy (EX, %)

| Cau hinh | Mo ta | Simple | Moderate | Challenging | Tong | CI 95% |
|---|---|---|---|---|---|---|
| `tasql` | TA-SQL (baseline cua paper): TASL dummy SQL + TALOG SR->SQL | 52.5 (n=59) | 27.0 (n=100) | 19.5 (n=41) | **33.0** | [27.0, 39.5] |
| `vsql` | V-SQL theo paper: view Hinh 3 theo JOIN dap an, D' = moi view cua CSDL, prompt Hinh 4 + Hinh 5 | 33.9 (n=59) | 17.0 (n=100) | 17.1 (n=41) | **22.0** | [16.5, 28.5] |
| `dinsql` | DIN-SQL (baseline Bang 3): schema linking -> phan loai -> sinh SQL theo loai; bo self-correction nhu paper | 39.0 (n=59) | 27.0 (n=100) | 22.0 (n=41) | **29.5** | [23.5, 36.0] |
| `dailsql` | DAIL-SQL (baseline Bang 3): schema CREATE TABLE + 7 vi du train BIRD chon 2 vong; 1 mau, khong bau chon nhu paper | 49.2 (n=59) | 30.0 (n=100) | 29.3 (n=41) | **35.5** | [29.0, 42.5] |

## 2a. So sanh ghep cap voi `tasql` (TA-SQL, baseline cua paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsql` | -11.0 | [-18.0, -4.0] | 37 | 15 | 0.003 | **0.010** |
| `dinsql` | -3.5 | [-11.0, +4.0] | 35 | 28 | 0.450 | 0.900 |
| `dailsql` | +2.5 | [-5.5, +10.5] | 32 | 37 | 0.630 | 0.900 |

## 2b. So sanh ghep cap voi `vsql` (V-SQL tai hien theo paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `tasql` | +11.0 | [+4.0, +18.0] | 15 | 37 | 0.003 | **0.006** |
| `dinsql` | +7.5 | [-0.5, +15.5] | 25 | 40 | 0.082 | 0.082 |
| `dailsql` | +13.5 | [+6.5, +20.5] | 15 | 42 | 0.000 | **0.001** |

## 2c. So sanh ghep cap voi `dinsql` (DIN-SQL, baseline Bang 3)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `tasql` | +3.5 | [-4.0, +11.0] | 28 | 35 | 0.450 | 0.450 |
| `vsql` | -7.5 | [-15.5, +0.5] | 40 | 25 | 0.082 | 0.245 |
| `dailsql` | +6.0 | [-1.0, +13.5] | 24 | 36 | 0.155 | 0.310 |

## 2d. So sanh ghep cap voi `dailsql` (DAIL-SQL, baseline Bang 3)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `tasql` | -2.5 | [-10.5, +5.5] | 37 | 32 | 0.630 | 0.630 |
| `vsql` | -13.5 | [-20.5, -6.5] | 42 | 15 | 0.000 | **0.001** |
| `dinsql` | -6.0 | [-13.5, +1.0] | 36 | 24 | 0.155 | 0.310 |

p < 0.05 moi coi la khac biet co y nghia thong ke; p Holm da hieu chinh cho nhieu phep so sanh trong cung bang.

## 3. Phan loai ket qua sai (% tren tong so cau)

`schema_column` + `schema_table` + `ambiguous_column` = ao giac schema (dieu paper muon giam).

| Cau hinh | schema_column | schema_table | ambiguous_column | syntax | no_sql | timeout | other_exec | wrong_empty | wrong_result | **Ao giac schema** |
|---|---|---|---|---|---|---|---|---|---|---|
| `tasql` | 17.5 | 1.0 | 0.0 | 7.5 | 0.0 | 0.5 | 5.5 | 5.5 | 29.5 | **18.5** |
| `vsql` | 30.0 | 1.5 | 0.0 | 4.5 | 3.5 | 0.0 | 4.0 | 7.0 | 27.5 | **31.5** |
| `dinsql` | 9.0 | 0.0 | 0.0 | 39.5 | 0.0 | 0.0 | 0.0 | 3.5 | 18.5 | **9.0** |
| `dailsql` | 24.5 | 0.5 | 0.0 | 7.0 | 0.0 | 0.0 | 3.0 | 8.0 | 21.5 | **25.0** |

## 4. Chi phi (trung binh moi cau)

| Cau hinh | So lan goi LLM | Token vao | Token ra | Giay LLM | So doi tuong schema | Do phu bang dap an | VES xap xi |
|---|---|---|---|---|---|---|---|
| `tasql` | 3.00 | 6535 | 359 | 9.8 | 2.1 | 85.0 | 51.0 |
| `vsql` | 1.97 | 10012 | 220 | 9.3 | 4.4 | 100.0 | 31.3 |
| `dinsql` | 3.00 | 23456 | 872 | 24.3 | 0.0 | 0.0 | 51.0 |
| `dailsql` | 1.64 | 3020 | 453 | 12.3 | 0.0 | 0.0 | 56.1 |

- *Do phu bang dap an*: ti le cau ma moi bang trong SQL dap an deu nam trong schema dua cho LLM (< 100% o V-SQL+ la do buoc chon view bo sot bang).
- *VES xap xi*: sqrt(t_dap_an / t_du_doan) tren cau dung, do 1 lan chay nen chi mang tinh tham khao.

## 5. Tach giai doan 1 / giai doan 2 (tren cung cac cau)

Giai doan 1 = SQL nhap mo rong tat dinh ve bang goc (view -> CTE), tuc la ket qua neu giai doan 2 khong lam sai gi. TA-SQL: SQL nhap cua buoc TASL (chi dung de trich schema; buoc 2 viet lai tu dau). DAIL-SQL: SQL vong 1 (vi du chon theo cau hoi) so voi vong 2 (vi du chon them theo khung SQL vong 1). DIN-SQL khong tach.

| Cau hinh | Gd1 dung | Cuoi dung | Gd2 sua dung | Gd2 lam hong | Rong | Loi chinh cua cau bi lam hong |
|---|---|---|---|---|---|---|
| `tasql` | 69 (34.5%) | 66 (33.0%) | 19 | 22 | -3 | wrong_result 11, schema_column 5, syntax 4 |
| `vsql` | 57 (28.5%) | 44 (22.0%) | 12 | 25 | -13 | schema_column 17, wrong_result 5, syntax 3 |
| `dailsql` | 74 (37.0%) | 71 (35.5%) | 15 | 18 | -3 | schema_column 12, wrong_result 4, wrong_empty 2 |

## 6. Dong gop rieng cua tung cai tien

| Yeu to | So sanh | dEX |
|---|---|---|
| V-SQL so voi TA-SQL | `vsql` - `tasql` | -11.0 |
| V-SQL so voi DIN-SQL | `vsql` - `dinsql` | -7.5 |
| V-SQL so voi DAIL-SQL | `vsql` - `dailsql` | -13.5 |

## 7. Diem manh / diem yeu (EX %)

### Theo CSDL

| Cau hinh | california_schools (n=12) | card_games (n=20) | codebase_community (n=19) | debit_card_specializing (n=13) | european_football_2 (n=21) | financial (n=13) | formula_1 (n=26) | student_club (n=19) | superhero (n=21) | thrombosis_prediction (n=20) | toxicology (n=16) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `tasql` | 0.0 | 35.0 | 26.3 | 30.8 | 38.1 | 23.1 | 30.8 | 68.4 | 52.4 | 10.0 | 31.2 |
| `vsql` | 0.0 | 25.0 | 21.1 | 15.4 | 33.3 | 7.7 | 11.5 | 63.2 | 23.8 | 20.0 | 6.2 |
| `dinsql` | 8.3 | 25.0 | 26.3 | 38.5 | 38.1 | 30.8 | 15.4 | 31.6 | 57.1 | 25.0 | 25.0 |
| `dailsql` | 16.7 | 30.0 | 15.8 | 46.2 | 52.4 | 38.5 | 42.3 | 57.9 | 57.1 | 15.0 | 6.2 |

### Theo so bang trong SQL dap an

| Cau hinh | 1 (n=37) | 2 (n=120) | 3 (n=37) | 4 (n=6) |
|---|---|---|---|---|
| `tasql` | 37.8 | 35.8 | 24.3 | 0.0 |
| `vsql` | 32.4 | 23.3 | 10.8 | 0.0 |
| `dinsql` | 8.1 | 40.8 | 18.9 | 0.0 |
| `dailsql` | 45.9 | 36.7 | 21.6 | 33.3 |
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
