# Ket qua thuc nghiem V-SQL

So cau hoi chung cho moi cau hinh: **500**

## 1. Execution Accuracy (EX, %)

| Cau hinh | Mo ta | Simple | Moderate | Challenging | Tong | CI 95% |
|---|---|---|---|---|---|---|
| `tasql` | TA-SQL (baseline cua paper): TASL dummy SQL + TALOG SR->SQL | 4.1 (n=148) | 0.8 (n=250) | 0.0 (n=102) | **1.6** | [0.6, 2.8] |
| `vsql` | V-SQL dung theo paper: view theo JOIN dap an, schema Bang 6, prompt Hinh 4 + Hinh 5 | 0.7 (n=148) | 0.8 (n=250) | 1.0 (n=102) | **0.8** | [0.2, 1.6] |
| `vsqlplus` | V-SQL+ = huong 1 (sinh view tu dong) + huong 2 (chon view bang truy hoi lai); giai doan 2 nhu paper | 5.4 (n=148) | 1.2 (n=250) | 0.0 (n=102) | **2.2** | [1.0, 3.4] |

## 2a. So sanh ghep cap voi `tasql` (TA-SQL, baseline cua paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsql` | -0.8 | [-2.2, +0.6] | 8 | 4 | 0.388 | 0.775 |
| `vsqlplus` | +0.6 | [-0.8, +2.0] | 5 | 8 | 0.581 | 0.775 |

## 2b. So sanh ghep cap voi `vsql` (V-SQL theo paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `tasql` | +0.8 | [-0.6, +2.2] | 4 | 8 | 0.388 | 0.388 |
| `vsqlplus` | +1.4 | [+0.2, +2.8] | 3 | 10 | 0.092 | 0.185 |

p < 0.05 moi coi la khac biet co y nghia thong ke; p Holm da hieu chinh cho nhieu phep so sanh trong cung bang.

## 3. Phan loai ket qua sai (% tren tong so cau)

`schema_column` + `schema_table` + `ambiguous_column` = ao giac schema (dieu paper muon giam).

| Cau hinh | schema_column | schema_table | ambiguous_column | syntax | no_sql | timeout | other_exec | wrong_empty | wrong_result | **Ao giac schema** |
|---|---|---|---|---|---|---|---|---|---|---|
| `tasql` | 36.6 | 26.4 | 0.2 | 16.8 | 0.0 | 0.0 | 6.2 | 3.0 | 9.2 | **63.2** |
| `vsql` | 12.2 | 68.4 | 0.8 | 7.0 | 7.6 | 0.0 | 1.2 | 0.2 | 1.8 | **81.4** |
| `vsqlplus` | 14.0 | 57.2 | 0.6 | 12.6 | 0.2 | 0.0 | 4.0 | 2.0 | 7.2 | **71.8** |

## 4. Chi phi (trung binh moi cau)

| Cau hinh | So lan goi LLM | Token vao | Token ra | Giay LLM | So doi tuong schema | Do phu bang dap an | VES xap xi |
|---|---|---|---|---|---|---|---|
| `tasql` | 3.00 | 7027 | 498 | 5.9 | 2.5 | 51.0 | 2.3 |
| `vsql` | 1.89 | 3975 | 116 | 1.7 | 4.4 | 100.0 | 0.4 |
| `vsqlplus` | 4.53 | 23976 | 314 | 5.1 | 4.6 | 97.2 | 2.4 |

- *Do phu bang dap an*: ti le cau ma moi bang trong SQL dap an deu nam trong schema dua cho LLM (< 100% o `hybrid_ret` la loi cua buoc truy xuat).
- *VES xap xi*: sqrt(t_dap_an / t_du_doan) tren cau dung, do 1 lan chay nen chi mang tinh tham khao.

## 5. Dong gop rieng cua tung cai tien

| Yeu to | So sanh | dEX |
|---|---|---|
| V-SQL (paper) so voi TA-SQL | `vsql` - `tasql` | -0.8 |
| V-SQL+ so voi V-SQL (paper) | `vsqlplus` - `vsql` | +1.4 |
| V-SQL+ so voi TA-SQL | `vsqlplus` - `tasql` | +0.6 |

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
