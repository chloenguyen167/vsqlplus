# Ket qua thuc nghiem V-SQL

So cau hoi chung cho moi cau hinh: **3**

## 1. Execution Accuracy (EX, %)

| Cau hinh | Mo ta | Simple | Moderate | Challenging | Tong | CI 95% |
|---|---|---|---|---|---|---|
| `tasql` | TA-SQL (baseline cua paper): TASL dummy SQL + TALOG SR->SQL | 0.0 (n=1) | 0.0 (n=2) | - (n=0) | **0.0** | [0.0, 0.0] |
| `vsql` | V-SQL dung theo paper: view theo JOIN dap an, schema Bang 6, prompt Hinh 4 + Hinh 5 | 0.0 (n=1) | 0.0 (n=2) | - (n=0) | **0.0** | [0.0, 0.0] |
| `vsqlplus` | V-SQL+ = huong 1 (sinh view tu dong) + huong 2 (chon view bang truy hoi lai); giai doan 2 nhu paper | 0.0 (n=1) | 0.0 (n=2) | - (n=0) | **0.0** | [0.0, 0.0] |

## 2a. So sanh ghep cap voi `tasql` (TA-SQL, baseline cua paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `vsql` | +0.0 | [+0.0, +0.0] | 0 | 0 | 1.000 | 1.000 |
| `vsqlplus` | +0.0 | [+0.0, +0.0] | 0 | 0 | 1.000 | 1.000 |

## 2b. So sanh ghep cap voi `vsql` (V-SQL theo paper)

| Cau hinh | dEX (diem %) | CI 95% cua dEX | Chi ref dung | Chi cau hinh nay dung | p McNemar | p Holm |
|---|---|---|---|---|---|---|
| `tasql` | +0.0 | [+0.0, +0.0] | 0 | 0 | 1.000 | 1.000 |
| `vsqlplus` | +0.0 | [+0.0, +0.0] | 0 | 0 | 1.000 | 1.000 |

p < 0.05 moi coi la khac biet co y nghia thong ke; p Holm da hieu chinh cho nhieu phep so sanh trong cung bang.

## 3. Phan loai ket qua sai (% tren tong so cau)

`schema_column` + `schema_table` + `ambiguous_column` = ao giac schema (dieu paper muon giam).

| Cau hinh | schema_column | schema_table | ambiguous_column | syntax | no_sql | timeout | other_exec | wrong_empty | wrong_result | **Ao giac schema** |
|---|---|---|---|---|---|---|---|---|---|---|
| `tasql` | 33.3 | 0.0 | 0.0 | 33.3 | 0.0 | 0.0 | 0.0 | 0.0 | 33.3 | **33.3** |
| `vsql` | 33.3 | 66.7 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **100.0** |
| `vsqlplus` | 33.3 | 66.7 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **100.0** |

## 4. Chi phi (trung binh moi cau)

| Cau hinh | So lan goi LLM | Token vao | Token ra | Giay LLM | So doi tuong schema | Do phu bang dap an | VES xap xi |
|---|---|---|---|---|---|---|---|
| `tasql` | 3.00 | 3341 | 499 | 5.5 | 1.7 | 100.0 | 0.0 |
| `vsql` | 2.00 | 1109 | 149 | 1.7 | 2.0 | 100.0 | 0.0 |
| `vsqlplus` | 3.00 | 3846 | 182 | 2.5 | 5.7 | 100.0 | 0.0 |

- *Do phu bang dap an*: ti le cau ma moi bang trong SQL dap an deu nam trong schema dua cho LLM (< 100% o `hybrid_ret` la loi cua buoc truy xuat).
- *VES xap xi*: sqrt(t_dap_an / t_du_doan) tren cau dung, do 1 lan chay nen chi mang tinh tham khao.

## 5. Dong gop rieng cua tung cai tien

| Yeu to | So sanh | dEX |
|---|---|---|
| V-SQL (paper) so voi TA-SQL | `vsql` - `tasql` | +0.0 |
| V-SQL+ so voi V-SQL (paper) | `vsqlplus` - `vsql` | +0.0 |
| V-SQL+ so voi TA-SQL | `vsqlplus` - `tasql` | +0.0 |

## 6. Thong ke view

| DB | Bang | FK | View oracle (trong do co nhan ban dong) | View auto | View auto giu nguyen so dong |
|---|---|---|---|---|---|
| debit_card_specializing | 5 | 4 | 2 (0) | 2 | 2 |
