# Ket qua thuc nghiem V-SQL

So cau hoi chung cho moi cau hinh: **498**

## 1. Execution Accuracy (EX, %)

| Cau hinh | Mo ta | Simple | Moderate | Challenging | Tong | CI 95% |
|---|---|---|---|---|---|---|
| `base` | Baseline 1 giai doan tren bang goc | 18.2 (n=148) | 5.2 (n=248) | 2.0 (n=102) | **8.4** | [6.0, 10.8] |
| `vsql` | TAI HIEN PAPER: view theo dap an + LLM tai tao | 10.1 (n=148) | 0.8 (n=248) | 2.0 (n=102) | **3.8** | [2.2, 5.6] |
| `vsql_det` | CT1: viet lai tat dinh | 4.7 (n=148) | 2.8 (n=248) | 0.0 (n=102) | **2.8** | [1.4, 4.4] |
| `auto_llm` | CT2: view tu dong (giu LLM tai tao) | 9.5 (n=148) | 1.2 (n=248) | 2.0 (n=102) | **3.8** | [2.2, 5.4] |
| `auto_det` | CT1+CT2 | 4.1 (n=148) | 3.2 (n=248) | 1.0 (n=102) | **3.0** | [1.6, 4.6] |
| `hybrid` | CT1+CT2+CT3: schema lai | 8.1 (n=148) | 3.6 (n=248) | 2.9 (n=102) | **4.8** | [3.0, 6.8] |
| `hybrid_ret` | CT1+2+3+CT4: truy xuat view | 8.8 (n=148) | 3.6 (n=248) | 2.0 (n=102) | **4.8** | [3.0, 6.8] |
| `base_ret` | Doi chung: chi truy xuat bang, khong view | 15.5 (n=148) | 4.8 (n=248) | 1.0 (n=102) | **7.2** | [5.0, 9.6] |
| `auto_plain_det` | CT1+CT2+CT6: view ten cot goc | 6.8 (n=148) | 3.6 (n=248) | 1.0 (n=102) | **4.0** | [2.4, 5.8] |
| `hybrid_ret_plain` | CT1-4+CT6: truy xuat, view ten cot goc | 9.5 (n=148) | 4.4 (n=248) | 1.0 (n=102) | **5.2** | [3.2, 7.2] |
| `auto_det_fix` | CT1+CT2 + CT5 schema-guard | 11.5 (n=148) | 4.4 (n=248) | 2.9 (n=102) | **6.2** | [4.2, 8.4] |
| `auto_llm_fix` | CT2: view tu dong (giu LLM tai tao) + CT5 schema-guard | 14.2 (n=148) | 4.4 (n=248) | 2.9 (n=102) | **7.0** | [4.8, 9.2] |
| `auto_plain_det_fix` | CT1+CT2+CT6: view ten cot goc + CT5 schema-guard | 12.2 (n=148) | 5.2 (n=248) | 2.9 (n=102) | **6.8** | [4.6, 9.0] |
| `base_fix` | Baseline 1 giai doan tren bang goc + CT5 schema-guard | 21.6 (n=148) | 8.5 (n=248) | 3.9 (n=102) | **11.4** | [8.6, 14.1] |
| `base_fix_fb` | base_fix_fb | 21.6 (n=148) | 8.5 (n=248) | 3.9 (n=102) | **11.4** | [8.6, 14.1] |
| `base_ret_fix` | Doi chung: chi truy xuat bang, khong view + CT5 schema-guard | 20.3 (n=148) | 8.1 (n=248) | 2.9 (n=102) | **10.6** | [8.0, 13.3] |
| `hybrid_fix` | CT1+CT2+CT3: schema lai + CT5 schema-guard | 14.9 (n=148) | 4.8 (n=248) | 8.8 (n=102) | **8.6** | [6.2, 11.0] |
| `hybrid_ret_fix` | CT1+2+3+CT4: truy xuat view + CT5 schema-guard | 16.9 (n=148) | 5.6 (n=248) | 4.9 (n=102) | **8.8** | [6.4, 11.4] |
| `hybrid_ret_plain_fix` | CT1-4+CT6: truy xuat, view ten cot goc + CT5 schema-guard | 14.9 (n=148) | 6.9 (n=248) | 5.9 (n=102) | **9.0** | [6.6, 11.6] |
| `mrv` | CT7 bo phieu theo ket qua thuc thi | 26.4 (n=148) | 7.7 (n=248) | 8.8 (n=102) | **13.5** | [10.6, 16.5] |
| `mrv_all` | CT7 bo phieu theo ket qua thuc thi | 26.4 (n=148) | 8.9 (n=248) | 8.8 (n=102) | **14.1** | [11.2, 17.1] |
| `mrv_fb` | CT7 bo phieu theo ket qua thuc thi | 26.4 (n=148) | 7.7 (n=248) | 8.8 (n=102) | **13.5** | [10.6, 16.5] |
| `vsql_det_fix` | CT1: viet lai tat dinh + CT5 schema-guard | 10.1 (n=148) | 5.2 (n=248) | 2.9 (n=102) | **6.2** | [4.2, 8.4] |
| `vsql_fix` | TAI HIEN PAPER: view theo dap an + LLM tai tao + CT5 schema-guard | 15.5 (n=148) | 4.8 (n=248) | 2.9 (n=102) | **7.6** | [5.4, 10.0] |

## 2a. So sanh ghep cap voi `vsql` (phuong phap cua paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `base` | +4.6 | [+2.0, +7.0] | 11 | 34 | 0.001 | **0.011** |
| `vsql_det` | -1.0 | [-2.8, +0.8] | 14 | 9 | 0.405 | 1.000 |
| `auto_llm` | +0.0 | [-1.8, +1.8] | 10 | 10 | 1.000 | 1.000 |
| `auto_det` | -0.8 | [-2.8, +1.0] | 14 | 10 | 0.541 | 1.000 |
| `hybrid` | +1.0 | [-1.4, +3.2] | 14 | 19 | 0.487 | 1.000 |
| `hybrid_ret` | +1.0 | [-1.4, +3.4] | 15 | 20 | 0.500 | 1.000 |
| `base_ret` | +3.4 | [+1.2, +5.6] | 9 | 26 | 0.006 | 0.072 |
| `auto_plain_det` | +0.2 | [-2.0, +2.4] | 15 | 16 | 1.000 | 1.000 |
| `hybrid_ret_plain` | +1.4 | [-1.0, +3.8] | 15 | 22 | 0.324 | 1.000 |
| `auto_det_fix` | +2.4 | [+0.0, +4.8] | 13 | 25 | 0.073 | 0.587 |
| `auto_llm_fix` | +3.2 | [+1.0, +5.2] | 8 | 24 | 0.007 | 0.077 |
| `auto_plain_det_fix` | +3.0 | [+0.4, +5.4] | 14 | 29 | 0.032 | 0.315 |
| `base_fix` | +7.6 | [+4.6, +10.4] | 11 | 49 | 0.000 | **0.000** |
| `base_fix_fb` | +7.6 | [+4.6, +10.4] | 11 | 49 | 0.000 | **0.000** |
| `base_ret_fix` | +6.8 | [+4.0, +9.4] | 8 | 42 | 0.000 | **0.000** |
| `hybrid_fix` | +4.8 | [+2.2, +7.4] | 11 | 35 | 0.001 | **0.008** |
| `hybrid_ret_fix` | +5.0 | [+2.4, +7.8] | 13 | 38 | 0.001 | **0.009** |
| `hybrid_ret_plain_fix` | +5.2 | [+2.6, +7.8] | 12 | 38 | 0.000 | **0.005** |
| `mrv` | +9.6 | [+6.6, +12.9] | 9 | 57 | 0.000 | **0.000** |
| `mrv_all` | +10.2 | [+7.2, +13.3] | 8 | 59 | 0.000 | **0.000** |
| `mrv_fb` | +9.6 | [+6.6, +12.9] | 9 | 57 | 0.000 | **0.000** |
| `vsql_det_fix` | +2.4 | [+0.0, +4.8] | 12 | 24 | 0.065 | 0.587 |
| `vsql_fix` | +3.8 | [+2.2, +5.6] | 0 | 19 | 0.000 | **0.000** |

## 2b. So sanh ghep cap voi `base` (baseline 1 giai doan)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsql` | -4.6 | [-7.0, -2.0] | 34 | 11 | 0.001 | **0.012** |
| `vsql_det` | -5.6 | [-8.0, -3.0] | 38 | 10 | 0.000 | **0.001** |
| `auto_llm` | -4.6 | [-7.0, -2.0] | 33 | 10 | 0.001 | **0.010** |
| `auto_det` | -5.4 | [-7.8, -2.8] | 36 | 9 | 0.000 | **0.001** |
| `hybrid` | -3.6 | [-6.2, -0.8] | 34 | 16 | 0.015 | 0.184 |
| `hybrid_ret` | -3.6 | [-6.2, -0.8] | 33 | 15 | 0.013 | 0.173 |
| `base_ret` | -1.2 | [-3.0, +0.6] | 14 | 8 | 0.286 | 1.000 |
| `auto_plain_det` | -4.4 | [-7.0, -1.6] | 35 | 13 | 0.002 | **0.029** |
| `hybrid_ret_plain` | -3.2 | [-5.8, -0.6] | 31 | 15 | 0.026 | 0.285 |
| `auto_det_fix` | -2.2 | [-4.8, +0.6] | 30 | 19 | 0.152 | 1.000 |
| `auto_llm_fix` | -1.4 | [-4.0, +1.4] | 28 | 21 | 0.392 | 1.000 |
| `auto_plain_det_fix` | -1.6 | [-4.4, +1.2] | 31 | 23 | 0.341 | 1.000 |
| `base_fix` | +3.0 | [+1.6, +4.6] | 0 | 15 | 0.000 | **0.001** |
| `base_fix_fb` | +3.0 | [+1.6, +4.6] | 0 | 15 | 0.000 | **0.001** |
| `base_ret_fix` | +2.2 | [-0.2, +4.6] | 13 | 24 | 0.099 | 0.989 |
| `hybrid_fix` | +0.2 | [-2.8, +3.4] | 31 | 32 | 1.000 | 1.000 |
| `hybrid_ret_fix` | +0.4 | [-2.4, +3.4] | 28 | 30 | 0.896 | 1.000 |
| `hybrid_ret_plain_fix` | +0.6 | [-2.4, +3.6] | 28 | 31 | 0.795 | 1.000 |
| `mrv` | +5.0 | [+2.6, +7.8] | 10 | 35 | 0.000 | **0.004** |
| `mrv_all` | +5.6 | [+3.0, +8.4] | 10 | 38 | 0.000 | **0.001** |
| `mrv_fb` | +5.0 | [+2.6, +7.8] | 10 | 35 | 0.000 | **0.004** |
| `vsql_det_fix` | -2.2 | [-5.0, +0.6] | 35 | 24 | 0.193 | 1.000 |
| `vsql_fix` | -0.8 | [-3.6, +2.2] | 32 | 28 | 0.699 | 1.000 |

p < 0.05 moi coi la khac biet co y nghia thong ke; p Holm da hieu chinh cho nhieu phep so sanh trong cung bang.

## 3. Phan loai ket qua sai (% tren tong so cau)

`schema_column` + `schema_table` + `ambiguous_column` = ao giac schema (dieu paper muon giam).

| Cau hinh | schema_column | schema_table | ambiguous_column | syntax | no_sql | timeout | other_exec | wrong_empty | wrong_result | **Ao giac schema** |
|---|---|---|---|---|---|---|---|---|---|---|
| `base` | 50.0 | 0.8 | 0.6 | 11.0 | 0.0 | 0.2 | 4.2 | 7.6 | 17.1 | **51.4** |
| `vsql` | 37.6 | 27.7 | 0.6 | 12.2 | 0.0 | 0.2 | 2.8 | 5.0 | 10.0 | **65.9** |
| `vsql_det` | 54.4 | 6.0 | 1.0 | 11.8 | 0.0 | 0.4 | 3.2 | 4.8 | 15.5 | **61.4** |
| `auto_llm` | 40.6 | 24.9 | 0.4 | 12.0 | 0.0 | 0.2 | 2.4 | 6.2 | 9.4 | **65.9** |
| `auto_det` | 55.4 | 3.2 | 0.8 | 14.1 | 0.0 | 0.4 | 1.4 | 5.2 | 16.5 | **59.4** |
| `hybrid` | 51.0 | 4.2 | 0.4 | 11.6 | 0.0 | 0.4 | 3.6 | 5.4 | 18.5 | **55.6** |
| `hybrid_ret` | 51.8 | 0.8 | 0.6 | 12.7 | 0.0 | 0.2 | 3.8 | 5.8 | 19.5 | **53.2** |
| `base_ret` | 48.4 | 0.8 | 0.6 | 11.0 | 0.0 | 0.4 | 4.4 | 7.8 | 19.3 | **49.8** |
| `auto_plain_det` | 47.0 | 2.4 | 2.0 | 12.9 | 0.0 | 0.4 | 4.4 | 7.4 | 19.5 | **51.4** |
| `hybrid_ret_plain` | 52.4 | 1.0 | 1.0 | 10.4 | 0.0 | 0.2 | 4.8 | 6.8 | 18.1 | **54.4** |
| `auto_det_fix` | 11.6 | 0.4 | 0.8 | 13.7 | 0.0 | 1.2 | 4.8 | 21.5 | 39.8 | **12.9** |
| `auto_llm_fix` | 14.1 | 0.6 | 1.2 | 12.2 | 0.0 | 0.4 | 6.4 | 20.9 | 37.1 | **15.9** |
| `auto_plain_det_fix` | 11.0 | 0.2 | 0.6 | 11.8 | 0.0 | 1.2 | 7.2 | 21.3 | 39.8 | **11.8** |
| `base_fix` | 7.6 | 0.8 | 0.4 | 10.2 | 0.0 | 0.8 | 7.0 | 18.5 | 43.2 | **8.8** |
| `base_fix_fb` | 6.0 | 0.8 | 0.4 | 10.4 | 0.0 | 0.6 | 5.6 | 18.9 | 45.8 | **7.2** |
| `base_ret_fix` | 9.0 | 0.8 | 0.6 | 10.4 | 0.0 | 0.6 | 6.2 | 19.7 | 42.0 | **10.4** |
| `hybrid_fix` | 12.7 | 0.6 | 0.2 | 10.6 | 0.0 | 1.0 | 5.6 | 19.1 | 41.6 | **13.5** |
| `hybrid_ret_fix` | 13.3 | 0.2 | 0.2 | 12.9 | 0.0 | 0.8 | 4.8 | 17.3 | 41.8 | **13.7** |
| `hybrid_ret_plain_fix` | 13.9 | 0.0 | 0.2 | 9.8 | 0.0 | 0.8 | 6.6 | 19.9 | 39.8 | **14.1** |
| `mrv` | 2.6 | 0.2 | 0.0 | 5.4 | 0.0 | 0.0 | 2.6 | 13.1 | 62.7 | **2.8** |
| `mrv_all` | 2.2 | 0.2 | 0.0 | 3.8 | 0.0 | 0.0 | 1.8 | 10.6 | 67.3 | **2.4** |
| `mrv_fb` | 2.2 | 0.2 | 0.0 | 5.4 | 0.0 | 0.0 | 2.0 | 13.1 | 63.7 | **2.4** |
| `vsql_det_fix` | 13.5 | 0.2 | 0.2 | 11.4 | 0.0 | 0.8 | 6.4 | 21.1 | 40.2 | **13.9** |
| `vsql_fix` | 17.1 | 0.6 | 0.8 | 11.8 | 0.0 | 0.6 | 7.0 | 20.3 | 34.1 | **18.5** |

## 4. Chi phi (trung binh moi cau)

| Cau hinh | So lan goi LLM | Token vao | Token ra | Giay LLM | So doi tuong schema | Do phu bang dap an | VES xap xi |
|---|---|---|---|---|---|---|---|
| `base` | 1.00 | 2577 | 88 | 1.8 | 7.3 | 100.0 | 9.3 |
| `vsql` | 1.94 | 8155 | 223 | 5.0 | 5.0 | 100.0 | 3.8 |
| `vsql_det` | 1.00 | 5851 | 110 | 2.3 | 5.0 | 100.0 | 2.4 |
| `auto_llm` | 1.84 | 6925 | 193 | 4.2 | 4.7 | 100.0 | 4.1 |
| `auto_det` | 1.00 | 5145 | 105 | 2.1 | 4.7 | 100.0 | 2.7 |
| `hybrid` | 1.00 | 6866 | 89 | 2.1 | 11.2 | 100.0 | 4.5 |
| `hybrid_ret` | 1.00 | 4416 | 90 | 2.6 | 4.9 | 98.8 | 4.4 |
| `base_ret` | 1.00 | 2119 | 83 | 1.9 | 4.6 | 95.4 | 8.0 |
| `auto_plain_det` | 1.00 | 5009 | 101 | 2.0 | 4.7 | 100.0 | 5.0 |
| `hybrid_ret_plain` | 1.00 | 4319 | 85 | 2.4 | 4.9 | 98.0 | 5.5 |
| `auto_det_fix` | 1.00 | 5145 | 105 | 2.1 | 4.7 | 100.0 | 6.0 |
| `auto_llm_fix` | 1.84 | 6925 | 193 | 4.2 | 4.7 | 100.0 | 6.5 |
| `auto_plain_det_fix` | 1.00 | 5009 | 101 | 2.0 | 4.7 | 100.0 | 6.6 |
| `base_fix` | 1.00 | 2577 | 88 | 1.8 | 7.3 | 100.0 | 11.0 |
| `base_fix_fb` | 1.27 | 2980 | 124 | 2.5 | 7.3 | 100.0 | 11.2 |
| `base_ret_fix` | 1.00 | 2119 | 83 | 1.9 | 4.6 | 95.4 | 10.1 |
| `hybrid_fix` | 1.00 | 6866 | 89 | 2.1 | 11.2 | 100.0 | 9.0 |
| `hybrid_ret_fix` | 1.00 | 4416 | 90 | 2.6 | 4.9 | 98.8 | 8.3 |
| `hybrid_ret_plain_fix` | 1.00 | 4319 | 85 | 2.4 | 4.9 | 98.0 | 8.9 |
| `mrv` | 4.00 | 19005 | 372 | 8.7 | 6.5 | 100.0 | 14.1 |
| `mrv_all` | 7.00 | 30452 | 641 | 15.0 | 6.3 | 99.6 | 15.3 |
| `mrv_fb` | 4.11 | 19167 | 384 | 8.9 | 6.5 | 100.0 | 17.6 |
| `vsql_det_fix` | 1.00 | 5851 | 110 | 2.3 | 5.0 | 100.0 | 5.0 |
| `vsql_fix` | 1.94 | 8155 | 223 | 5.0 | 5.0 | 100.0 | 7.2 |

- *Do phu bang dap an*: ti le cau ma moi bang trong SQL dap an deu nam trong schema dua cho LLM (< 100% o `hybrid_ret` la loi cua buoc truy xuat).
- *VES xap xi*: sqrt(t_dap_an / t_du_doan) tren cau dung, do 1 lan chay nen chi mang tinh tham khao.

## 5. Dong gop rieng cua tung cai tien

| Yeu to | So sanh | dEX |
|---|---|---|
| CT1 viet lai tat dinh (cung view, cung dummy SQL) | `vsql_det` - `vsql` | -1.0 |
| CT2 view tu dong thay view theo dap an (cung LLM tai tao) | `auto_llm` - `vsql` | +0.0 |
| CT1 tren view tu dong | `auto_det` - `auto_llm` | -0.8 |
| CT3 schema lai (them bang goc) | `hybrid` - `auto_det` | +1.8 |
| CT4 truy xuat top-k | `hybrid_ret` - `hybrid` | +0.0 |
| Dong gop cua view so voi baseline 1 giai doan | `vsql` - `base` | -4.6 |

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
