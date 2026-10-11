# Ket qua thuc nghiem V-SQL

So cau hoi chung cho moi cau hinh: **225**

## 1. Execution Accuracy (EX, %)

| Cau hinh | Mo ta | Simple | Moderate | Challenging | Tong | CI 95% |
|---|---|---|---|---|---|---|
| `base` | Baseline 1 giai doan tren bang goc | 59.7 (n=62) | 38.0 (n=108) | 27.3 (n=55) | **41.3** | [35.1, 47.6] |
| `vsql` | TAI HIEN PAPER: view theo dap an + LLM tai tao | 41.9 (n=62) | 35.2 (n=108) | 18.2 (n=55) | **32.9** | [27.1, 39.1] |
| `vsql_det` | CT1: viet lai tat dinh | 35.5 (n=62) | 35.2 (n=108) | 16.4 (n=55) | **30.7** | [24.9, 36.4] |
| `auto_det` | CT1+CT2 | 37.1 (n=62) | 36.1 (n=108) | 21.8 (n=55) | **32.9** | [26.7, 39.1] |
| `hybrid` | CT1+CT2+CT3: schema lai | 37.1 (n=62) | 38.0 (n=108) | 14.5 (n=55) | **32.0** | [26.2, 38.2] |
| `hybrid_ret` | CT1+2+3+CT4: truy xuat view | 45.2 (n=62) | 34.3 (n=108) | 18.2 (n=55) | **33.3** | [27.6, 39.6] |

## 2. So sanh ghep cap voi `vsql` (phuong phap cua paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar |
|---|---|---|---|---|---|
| `base` | +8.4 | [+2.2, +14.7] | 17 | 36 | 0.013 |
| `vsql_det` | -2.2 | [-5.8, +1.3] | 11 | 6 | 0.332 |
| `auto_det` | +0.0 | [-4.4, +4.9] | 15 | 15 | 1.000 |
| `hybrid` | -0.9 | [-6.2, +4.9] | 22 | 20 | 0.878 |
| `hybrid_ret` | +0.4 | [-5.8, +6.7] | 23 | 24 | 1.000 |

p < 0.05 moi coi la khac biet co y nghia thong ke; CI chua 0 nghia la chua ket luan duoc.

## 3. Phan loai ket qua sai (% tren tong so cau)

`schema_column` + `schema_table` + `ambiguous_column` = ao giac schema (dieu paper muon giam).

| Cau hinh | schema_column | schema_table | ambiguous_column | syntax | no_sql | timeout | other_exec | wrong_empty | wrong_result | **Ao giac schema** |
|---|---|---|---|---|---|---|---|---|---|---|
| `base` | 12.4 | 0.0 | 1.3 | 1.3 | 0.0 | 0.9 | 0.9 | 4.9 | 36.9 | **13.8** |
| `vsql` | 11.1 | 0.9 | 0.9 | 1.8 | 0.0 | 0.0 | 0.9 | 4.9 | 46.7 | **12.9** |
| `vsql_det` | 16.4 | 1.3 | 0.9 | 1.8 | 0.0 | 0.0 | 1.3 | 4.0 | 43.6 | **18.7** |
| `auto_det` | 15.1 | 2.2 | 1.3 | 1.8 | 0.0 | 0.0 | 1.8 | 4.9 | 40.0 | **18.7** |
| `hybrid` | 20.0 | 1.3 | 0.4 | 3.6 | 0.0 | 0.0 | 1.3 | 3.1 | 38.2 | **21.8** |
| `hybrid_ret` | 16.9 | 0.9 | 0.4 | 3.1 | 0.0 | 0.4 | 0.4 | 4.0 | 40.4 | **18.2** |

## 4. Chi phi (trung binh moi cau)

| Cau hinh | So lan goi LLM | Token vao | Token ra | Giay LLM | So doi tuong schema | Do phu bang dap an | VES xap xi |
|---|---|---|---|---|---|---|---|
| `base` | 1.00 | 2439 | 70 | 5.9 | 5.7 | 100.0 | 46.5 |
| `vsql` | 1.96 | 5493 | 144 | 35.5 | 4.3 | 100.0 | 39.3 |
| `vsql_det` | 1.00 | 3948 | 62 | 23.2 | 4.3 | 100.0 | 38.3 |
| `auto_det` | 1.00 | 3454 | 62 | 11.1 | 3.8 | 100.0 | 35.9 |
| `hybrid` | 1.00 | 4966 | 64 | 17.8 | 8.9 | 100.0 | 33.3 |
| `hybrid_ret` | 1.00 | 3648 | 64 | 17.8 | 5.0 | 98.7 | 32.9 |

- *Do phu bang dap an*: ti le cau ma moi bang trong SQL dap an deu nam trong schema dua cho LLM (< 100% o `hybrid_ret` la loi cua buoc truy xuat).
- *VES xap xi*: sqrt(t_dap_an / t_du_doan) tren cau dung, do 1 lan chay nen chi mang tinh tham khao.

## 5. Dong gop rieng cua tung cai tien

| Yeu to | So sanh | dEX |
|---|---|---|
| CT1 viet lai tat dinh (cung view, cung dummy SQL) | `vsql_det` - `vsql` | -2.2 |
| CT3 schema lai (them bang goc) | `hybrid` - `auto_det` | -0.9 |
| CT4 truy xuat top-k | `hybrid_ret` - `hybrid` | +1.3 |
| Dong gop cua view so voi baseline 1 giai doan | `vsql` - `base` | -8.4 |

## 6. Thong ke view

| DB | Bang | FK | View oracle (trong do co nhan ban dong) | View auto | View auto giu nguyen so dong |
|---|---|---|---|---|---|
| california_schools | 3 | 2 | 2 (0) | 1 | 1 |
| card_games | 6 | 4 | 4 (0) | 1 | 1 |
| codebase_community | 8 | 13 | 7 (0) | 7 | 7 |
| debit_card_specializing | 5 | 1 | 1 (0) | 1 | 1 |
| european_football_2 | 7 | 31 | 3 (0) | 3 | 3 |
| financial | 8 | 8 | 10 (3) | 7 | 7 |
| formula_1 | 13 | 19 | 8 (0) | 8 | 8 |
| student_club | 8 | 8 | 6 (1) | 5 | 5 |
| superhero | 10 | 11 | 3 (0) | 3 | 3 |
| thrombosis_prediction | 3 | 2 | 3 (1) | 2 | 2 |
| toxicology | 4 | 5 | 4 (1) | 3 | 3 |
