# Ket qua thuc nghiem V-SQL

So cau hoi chung cho moi cau hinh: **254**  (CANH BAO: cac cau hinh co so cau khac nhau; chi tinh tren phan giao)

## 1. Execution Accuracy (EX, %)

| Cau hinh | Mo ta | Simple | Moderate | Challenging | Tong | CI 95% |
|---|---|---|---|---|---|---|
| `base` | Baseline 1 giai doan tren bang goc | 56.7 (n=67) | 37.3 (n=126) | 27.9 (n=61) | **40.2** | [33.9, 46.1] |
| `vsql_det` | CT1: viet lai tat dinh | 34.3 (n=67) | 34.9 (n=126) | 18.0 (n=61) | **30.7** | [25.2, 36.6] |
| `auto_det` | CT1+CT2 | 37.3 (n=67) | 34.9 (n=126) | 23.0 (n=61) | **32.7** | [26.8, 38.2] |
| `hybrid` | CT1+CT2+CT3: schema lai | 35.8 (n=67) | 35.7 (n=126) | 13.1 (n=61) | **30.3** | [24.8, 36.2] |
| `hybrid_ret` | CT1+2+3+CT4: truy xuat view | 41.8 (n=67) | 33.3 (n=126) | 21.3 (n=61) | **32.7** | [27.2, 38.2] |

## 2. So sanh ghep cap voi `vsql_det` (phuong phap cua paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar |
|---|---|---|---|---|---|
| `base` | +9.4 | [+3.1, +15.7] | 21 | 45 | 0.004 |
| `auto_det` | +2.0 | [-2.4, +6.7] | 14 | 19 | 0.487 |
| `hybrid` | -0.4 | [-5.1, +4.7] | 22 | 21 | 1.000 |
| `hybrid_ret` | +2.0 | [-2.8, +7.1] | 21 | 26 | 0.560 |

p < 0.05 moi coi la khac biet co y nghia thong ke; CI chua 0 nghia la chua ket luan duoc.

## 3. Phan loai ket qua sai (% tren tong so cau)

`schema_column` + `schema_table` + `ambiguous_column` = ao giac schema (dieu paper muon giam).

| Cau hinh | schema_column | schema_table | ambiguous_column | syntax | no_sql | timeout | other_exec | wrong_empty | wrong_result | **Ao giac schema** |
|---|---|---|---|---|---|---|---|---|---|---|
| `base` | 11.8 | 0.0 | 1.2 | 1.2 | 0.0 | 1.2 | 0.8 | 4.7 | 39.0 | **13.0** |
| `vsql_det` | 17.7 | 1.2 | 0.8 | 2.0 | 0.0 | 0.8 | 1.2 | 3.5 | 42.1 | **19.7** |
| `auto_det` | 14.6 | 2.0 | 1.2 | 1.6 | 0.0 | 0.4 | 1.6 | 5.1 | 40.9 | **17.7** |
| `hybrid` | 20.9 | 1.2 | 0.4 | 3.1 | 0.0 | 0.4 | 1.2 | 3.1 | 39.4 | **22.4** |
| `hybrid_ret` | 17.3 | 0.8 | 0.4 | 2.8 | 0.0 | 0.4 | 0.4 | 3.9 | 41.3 | **18.5** |

## 4. Chi phi (trung binh moi cau)

| Cau hinh | So lan goi LLM | Token vao | Token ra | Giay LLM | So doi tuong schema | Do phu bang dap an | VES xap xi |
|---|---|---|---|---|---|---|---|
| `base` | 1.00 | 2386 | 69 | 5.8 | 5.9 | 100.0 | 44.1 |
| `vsql_det` | 1.00 | 4475 | 62 | 22.5 | 4.7 | 100.0 | 37.3 |
| `auto_det` | 1.00 | 4020 | 61 | 13.0 | 4.1 | 100.0 | 36.5 |
| `hybrid` | 1.00 | 5538 | 64 | 27.9 | 9.4 | 100.0 | 31.2 |
| `hybrid_ret` | 1.00 | 3822 | 63 | 19.2 | 5.0 | 98.4 | 32.0 |

- *Do phu bang dap an*: ti le cau ma moi bang trong SQL dap an deu nam trong schema dua cho LLM (< 100% o `hybrid_ret` la loi cua buoc truy xuat).
- *VES xap xi*: sqrt(t_dap_an / t_du_doan) tren cau dung, do 1 lan chay nen chi mang tinh tham khao.

## 5. Dong gop rieng cua tung cai tien

| Yeu to | So sanh | dEX |
|---|---|---|
| CT3 schema lai (them bang goc) | `hybrid` - `auto_det` | -2.4 |
| CT4 truy xuat top-k | `hybrid_ret` - `hybrid` | +2.4 |

## 6. Thong ke view

| DB | Bang | FK | View oracle (trong do co nhan ban dong) | View auto | View auto giu nguyen so dong |
|---|---|---|---|---|---|
| codebase_community | 8 | 13 | 7 (0) | 7 | 7 |
| european_football_2 | 7 | 31 | 3 (0) | 3 | 3 |
| financial | 8 | 8 | 10 (3) | 7 | 7 |
| formula_1 | 13 | 19 | 8 (0) | 8 | 8 |
| thrombosis_prediction | 3 | 2 | 3 (1) | 2 | 2 |
| toxicology | 4 | 5 | 4 (1) | 3 | 3 |
