# Phan tich bo sung (225 cau)

## EX (%) theo database

| DB | n | `base` | `vsql` | `vsql_det` | `auto_det` | `hybrid` | `hybrid_ret` |
|---|---|---|---|---|---|---|---|
| codebase_community | 3 | 66.7 | 33.3 | 33.3 | 33.3 | 0.0 | 66.7 |
| debit_card_specializing | 30 | 40.0 | 23.3 | 23.3 | 23.3 | 26.7 | 30.0 |
| european_football_2 | 51 | 45.1 | 52.9 | 56.9 | 51.0 | 51.0 | 47.1 |
| financial | 13 | 23.1 | 15.4 | 23.1 | 30.8 | 23.1 | 23.1 |
| student_club | 45 | 57.8 | 51.1 | 37.8 | 33.3 | 31.1 | 33.3 |
| thrombosis_prediction | 50 | 30.0 | 10.0 | 6.0 | 20.0 | 20.0 | 20.0 |
| toxicology | 33 | 36.4 | 27.3 | 27.3 | 33.3 | 33.3 | 36.4 |

## EX (%) theo so JOIN trong SQL dap an

| So JOIN | n | `base` | `vsql` | `vsql_det` | `auto_det` | `hybrid` | `hybrid_ret` |
|---|---|---|---|---|---|---|---|
| 0 | 44 | 61.4 | 38.6 | 36.4 | 40.9 | 38.6 | 45.5 |
| 1 | 144 | 39.6 | 34.7 | 32.6 | 34.7 | 33.3 | 34.0 |
| 2 | 31 | 22.6 | 19.4 | 16.1 | 16.1 | 19.4 | 16.1 |
| >=3 | 6 | 33.3 | 16.7 | 16.7 | 16.7 | 16.7 | 16.7 |

## Giai doan 2: LLM tai tao so voi viet lai tat dinh (cung dummy SQL)

### `vsql` vs `vsql_det`

- Cau co cung dummy SQL: 225/225; trong do dummy SQL khong dung view nao: 8
- Chi `vsql_det` dung: 6 (loi cua `vsql`: {'wrong_empty': 1, 'schema_column': 3, 'wrong_result': 2})
- Chi `vsql` dung: 11 (loi cua `vsql_det`: {'wrong_result': 1, 'schema_column': 8, 'other_exec': 1, 'schema_table': 1})
- Ty le cau goi LLM lan 2 o `vsql`: 96.4%

## So cau ao giac schema

| Cau hinh | no such column | no such table | ambiguous | Tong |
|---|---|---|---|---|
| `base` | 28 | 0 | 3 | 31 |
| `vsql` | 25 | 2 | 2 | 29 |
| `vsql_det` | 37 | 3 | 2 | 42 |
| `auto_det` | 34 | 5 | 3 | 42 |
| `hybrid` | 45 | 3 | 1 | 49 |
| `hybrid_ret` | 38 | 2 | 1 | 41 |

## Bo sung tu cac cau hinh (oracle union)

- Ty le cau co it nhat mot cau hinh dung: 52.0%
- Ty le cau moi cau hinh deu dung: 14.7%
