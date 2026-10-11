# Phan tich bo sung (254 cau)

## EX (%) theo database

| DB | n | `base` | `vsql_det` | `auto_det` | `hybrid` | `hybrid_ret` |
|---|---|---|---|---|---|---|
| codebase_community | 15 | 40.0 | 20.0 | 20.0 | 6.7 | 20.0 |
| debit_card_specializing | 30 | 40.0 | 23.3 | 23.3 | 26.7 | 30.0 |
| european_football_2 | 51 | 45.1 | 56.9 | 51.0 | 51.0 | 47.1 |
| financial | 20 | 15.0 | 25.0 | 30.0 | 25.0 | 20.0 |
| formula_1 | 3 | 0.0 | 33.3 | 33.3 | 33.3 | 33.3 |
| student_club | 45 | 57.8 | 37.8 | 33.3 | 31.1 | 33.3 |
| thrombosis_prediction | 50 | 30.0 | 6.0 | 20.0 | 20.0 | 20.0 |
| toxicology | 40 | 42.5 | 32.5 | 37.5 | 30.0 | 42.5 |

## EX (%) theo so JOIN trong SQL dap an

| So JOIN | n | `base` | `vsql_det` | `auto_det` | `hybrid` | `hybrid_ret` |
|---|---|---|---|---|---|---|
| 0 | 48 | 60.4 | 35.4 | 41.7 | 39.6 | 43.8 |
| 1 | 160 | 39.4 | 33.1 | 35.0 | 31.2 | 33.8 |
| 2 | 39 | 20.5 | 17.9 | 15.4 | 17.9 | 17.9 |
| >=3 | 7 | 28.6 | 14.3 | 14.3 | 14.3 | 14.3 |

## Giai doan 2: LLM tai tao so voi viet lai tat dinh (cung dummy SQL)

## So cau ao giac schema

| Cau hinh | no such column | no such table | ambiguous | Tong |
|---|---|---|---|---|
| `base` | 30 | 0 | 3 | 33 |
| `vsql_det` | 45 | 3 | 2 | 50 |
| `auto_det` | 37 | 5 | 3 | 45 |
| `hybrid` | 53 | 3 | 1 | 57 |
| `hybrid_ret` | 44 | 2 | 1 | 47 |

## Bo sung tu cac cau hinh (oracle union)

- Ty le cau co it nhat mot cau hinh dung: 51.2%
- Ty le cau moi cau hinh deu dung: 14.2%
