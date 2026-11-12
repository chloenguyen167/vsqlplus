# Tái hiện V-SQL, so sánh với TA-SQL và cải tiến V-SQL+ trên BIRD mini-dev

[![Mở trong Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/chloenguyen167/vsqlplus/blob/main/notebooks/TASQL_VSQL_VSQLplus_Colab.ipynb)

Mã nguồn tái hiện paper **V-SQL: A View-based Two-stage Text-to-SQL Framework** (2024), so sánh với baseline mà paper dùng là
**TA-SQL** (Qu et al., ACL Findings 2024), và đề xuất cải tiến **V-SQL+**. Thực nghiệm chạy trên **BIRD mini-dev** (500 câu,
11 CSDL) với các model Qwen mã nguồn mở qua **Ollama trên Google Colab (GPU T4)**.

Chỉ dùng thư viện chuẩn của Python ≥ 3.8; không cần `pip install`.

---

## Chạy trên Google Colab (cách chính)

1. Mở notebook bằng nút **Open in Colab** ở trên ([`notebooks/TASQL_VSQL_VSQLplus_Colab.ipynb`](notebooks/TASQL_VSQL_VSQLplus_Colab.ipynb)).
2. **Runtime → Change runtime type → T4 GPU**.
3. Ở **Bước 1**, chọn model, phiên bản dữ liệu và phương pháp, rồi chạy lần lượt các ô từ trên xuống.

Notebook tự làm mọi việc: tải BIRD mini-dev, tải mô tả cột của TA-SQL, cài Ollama và model, chạy, chấm điểm, kiểm định thống kê,
vẽ biểu đồ. Kết quả được **tự sao lưu lên Google Drive** (`MyDrive/vsqlplus_ketqua/`). Nếu Colab ngắt thì chạy lại, phần đã xong
được bỏ qua; có thể chuyển sang tài khoản Google khác và chạy tiếp.

Hướng dẫn chi tiết từng bước, giải thích mọi lựa chọn ở Bước 1, kết quả mong đợi và cách xử lý lỗi:
**[`docs/HUONG_DAN_COLAB_SO_SANH.md`](docs/HUONG_DAN_COLAB_SO_SANH.md)**.

> Notebook lấy mã bằng `git clone` từ nhánh `main` của repo này. Sửa mã ở máy thì phải push lên GitHub, Colab mới thấy.

---

## Các phương pháp

**Notebook Colab chạy:** `tasql` (luôn chạy), `vsql_fair` (hiển thị là **V-SQL**), `vsqlplus` (**V-SQL+**), tùy chọn `dinsql`, `dailsql`.
Tick `dinsql`, `dailsql` để chạy thêm hai baseline còn lại của Bảng 3. Bật ô `ABLATION` để chạy thêm 5 biến thể của V-SQL+. `vsql`, `vsql_paper`, `vsqlplus_fig4` chỉ chạy được bằng dòng lệnh (`run_compare.py --methods ...`).
`summary.md` luôn có thêm bảng tách giai đoạn 1 / 2 và bảng EX theo CSDL, theo số bảng trong SQL đáp án (không tốn thêm lượt gọi LLM).

| Phương pháp | Mô tả | Lượt gọi LLM/câu |
|---|---|---|
| `tasql` | **TA-SQL**, baseline của paper (luôn chạy). Cài theo [mã chính thức](https://github.com/quge2023/TA-SQL): TASL (dummy SQL → trích bảng/cột) + TALOG (biểu diễn ký hiệu SR → SQL). Prompt chép nguyên văn (`vsql/tasql_prompts.py`), mô tả cột lấy từ `column_meaning.json` của TA-SQL | 3 |
| `vsql` | **V-SQL tái hiện, bản đầu tiên**: view thiết kế theo JOIN của SQL đáp án (mục 6 của paper); prompt Hình 4 (giai đoạn 1) và Hình 5 (giai đoạn 2, LLM khôi phục SQL) nguyên văn; schema dạng Bảng 6 | ~2 |
| `vsql_paper` | V-SQL với **view sát Hình 3**: bỏ cột id khóa ngoại đã thay bằng giá trị, alias là tên bảng, nối theo thứ tự cột | ~2 |
| `vsql_fair` | **V-SQL dùng trong notebook.** Giữ phần paper quy định, chỉnh phần paper không nói cho ngang TA-SQL: view theo JOIN đáp án, giữ cột khóa ngoại; đưa hết view của CSDL (không thêm bước chọn view); hiện cả các bảng không bị view nào thay thế; schema có mô tả giá trị và giá trị mẫu | ~2 |
| `vsqlplus` | **V-SQL+ đầy đủ**: 2 hướng cải tiến + prompt giai đoạn 1 mới | ~4–4,5 |
| `vsqlplus_fig4` | **V-SQL+ chỉ 2 hướng**: template và cách trình bày schema y như `vsql_fair`, chỉ khác ở cách sinh view và cách chọn view | ~4 |
| `dinsql` | **DIN-SQL** (baseline Bảng 3), mã chính thức cho BIRD, prompt nguyên văn; bỏ bước tự sửa lỗi như paper | 3 |
| `dailsql` | **DAIL-SQL** (baseline Bảng 3), cấu hình BIRD của mã chính thức (7 ví dụ từ tập train BIRD, chọn 2 vòng); 1 mẫu, không bầu chọn như paper | 2 |

**Hai hướng cải tiến của V-SQL+** (paper để ngỏ cả hai):
1. **Tự động sinh view** từ khóa ngoại: chỉ nối N-1 khi khóa được tham chiếu là duy nhất, kiểm tra lại số dòng, suy thêm khóa
   ngoại bị thiếu khai báo, đặt tên cột sạch như Hình 3.
2. **Chọn view đúng bằng truy hồi lai** (BM25 + embedding), bổ trợ bởi: truy hồi mức cột rồi gộp lên view; liên kết giá trị
   trong câu hỏi với giá trị thật trong DB; bầu chọn tập view từ nhiều dummy SQL; schema lai (quay về bảng gốc khi LLM dùng cột
   không có trong view); CSDL nhỏ thì đưa hết view vào prompt.

Giai đoạn 2 (LLM khôi phục SQL theo Hình 5) giữ nguyên như paper ở mọi bản V-SQL / V-SQL+.

**Biến thể đối chiếu** (ô `ABLATION` trong notebook): `vsqlplus_all` (chỉ hướng 1), `vsqlplus_novote`, `vsqlplus_novl`,
`vsqlplus_nofb` (bỏ từng thành phần của hướng 2), `vsqlplus_det` (thay giai đoạn 2 bằng giải mã tất định; không thuộc đề xuất,
chỉ để đo).

| Câu hỏi | So sánh |
|---|---|
| V-SQL đúng paper có ngang TA-SQL không? | `vsql_paper`, `vsql_fair` so với `tasql` |
| Hai hướng cải tiến có tác dụng riêng không? | `vsqlplus_fig4` − `vsql_fair` |
| Prompt mới có thêm tác dụng không? | `vsqlplus` − `vsqlplus_fig4` |

Chi tiết thiết kế và mọi điểm khác paper: [`docs/TAI_HIEN_DUNG_VA_VSQLPLUS.md`](docs/TAI_HIEN_DUNG_VA_VSQLPLUS.md).

---

## Dữ liệu

| Phiên bản (`DATASET`) | Nguồn | Ghi chú |
|---|---|---|
| `2025-07-04` (mặc định) | [Hugging Face `birdsql/bird_mini_dev`](https://huggingface.co/datasets/birdsql/bird_mini_dev), commit `f65faf4` | 500 câu khác nhau; độ khó 148 / 250 / 102 như Bảng 2 của paper |
| `2024-06` | [zip OSS gốc](https://bird-bench.oss-cn-beijing.aliyuncs.com/minidev.zip) | Có 2 câu lặp (`question_id` 137, 138), thiếu câu 119, 120 |

CSDL, `dev_tables.json` và mô tả cột giống nhau ở cả hai bản (lấy từ zip OSS). Mã định danh mỗi câu theo vị trí dòng (`uid`) nên
luôn chấm đủ 500 dòng. Notebook kiểm tra md5 của file câu hỏi. Mô tả cột TA-SQL được tải từ
[`outputs/column_meaning.json`](https://github.com/quge2023/TA-SQL/tree/master/outputs) của repo TA-SQL.

---

## Kết quả đã có

| Model | TA-SQL | V-SQL | V-SQL+ | Ghi chú |
|---|---|---|---|---|
| `qwen3.5:4b` | **38,0** | 19,2 | 29,4 | 500 câu, dữ liệu 2025; mọi chênh lệch có ý nghĩa thống kê |
| `qwen3.5:0.8b` | 1,6 | 0,8 | 2,2 | model quá nhỏ, không dùng để so sánh |

(EX, %. Lần chạy này có `tasql`, `vsql`, `vsqlplus`; chưa có `vsql_paper`, `vsql_fair`, `vsqlplus_fig4`.)

Phát hiện chính với 4b: câu SQL nháp viết trên view của V-SQL+ (giai đoạn 1) đúng 200/500 câu, ngang TA-SQL (190). Phần thua đến
từ giai đoạn 2, khi LLM viết lại SQL nháp về bảng gốc. Phân tích đầy đủ, dễ hiểu:
[`docs/NHAN_XET_KET_QUA_QWEN35.md`](docs/NHAN_XET_KET_QUA_QWEN35.md). File kết quả gốc nằm trong `results_new/`.

---

## Chạy bằng dòng lệnh (không qua notebook)

Cần Ollama đang chạy và model đã `ollama pull`. Theo hướng dẫn của nhóm, thực nghiệm chạy trên Colab chứ không chạy trên máy cá
nhân; các lệnh dưới đây chủ yếu để hiểu notebook gọi gì.

```bash
D=minidev/MINIDEV
COMMON="--data $D/mini_dev_sqlite_2025-07-04.json --db-root $D/dev_databases --tables-json $D/dev_tables.json \
        --tasql-meaning column_meaning.json"

python run_compare.py $COMMON --model qwen3.5:4b --out results/cmp_qwen35_4b \
    --methods tasql,vsql,vsql_paper,vsql_fair,vsqlplus,vsqlplus_fig4
python run_compare.py $COMMON --model qwen3.5:4b --out results/cmp_qwen35_4b --methods vsqlplus_all,vsqlplus_det
python run_compare.py $COMMON --out results/_views --views-only                   # chỉ sinh + kiểm tra view, không gọi LLM
python run_compare.py $COMMON --out results/_views --selection-sweep --no-embed   # độ phủ bước chọn view, không gọi LLM
python run_compare.py --help                                                      # toàn bộ tham số
```

Tham số hay dùng:

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--methods` | `main` (= `tasql,vsql,vsqlplus`) | Danh sách phương pháp, hoặc `all` (thêm biến thể ablation) |
| `--sample N` | 0 | Lấy mẫu phân tầng N câu theo CSDL × độ khó |
| `--num-predict` | 800 | Số token tối đa mỗi câu trả lời (như paper) |
| `--num-ctx` | 20480 | Ngữ cảnh của Ollama, đủ cho prompt dài nhất |
| `--embed-model` / `--no-embed` | `nomic-embed-text` | Embedding cho truy hồi lai của V-SQL+; `--no-embed` = chỉ BM25 |
| `--vsql-evidence` | `query` | V-SQL: nối evidence của BIRD vào `{query}` của Hình 4/5, hoặc `none` |
| `--k-cand`, `--n-samples`, `--sample-temp` | 5, 4, 0,7 | V-SQL+: số view ứng viên, số dummy SQL bầu chọn, nhiệt độ lấy mẫu |
| `--all-max-objects`, `--all-max-tokens` | 4, 3500 | V-SQL+: CSDL nhỏ hơn ngưỡng thì đưa hết view vào prompt |
| `--retry-llm-errors` | tắt | Thử lại các prompt từng bị Ollama báo lỗi |
| `--workers` | 1 | Số luồng gọi Ollama song song |

Chương trình **chạy tiếp được**: câu đã chấm được bỏ qua, mọi câu trả lời LLM lưu trong `llm_cache.sqlite`. Trước khi chấm, nó gom
các prompt còn thiếu theo từng vòng và sắp theo thứ tự chữ để Ollama dùng lại KV cache; dòng `[prefetch vong k]` cho biết số prompt
mỗi loại và thời gian còn lại. Cuối lần chạy in `[KIEM TRA] <phương pháp>: 500/500 dong da cham`.

### Kết quả ghi ra

Mỗi thư mục `--out` có:

| File | Nội dung |
|---|---|
| `summary.md`, `summary.csv` | EX tổng và theo độ khó (CI 95% bootstrap), so sánh ghép cặp (McNemar, hiệu chỉnh Holm) với `tasql` / `vsql` / `vsql_paper` / `vsql_fair`, phân loại lỗi, chi phí (lượt gọi, token, thời gian), đóng góp từng thành phần, thống kê view |
| `predictions_<phương pháp>.jsonl` | Một dòng mỗi câu: SQL cuối, đúng/sai, loại lỗi, dummy SQL, view đã dùng, chi phí; với V-SQL+ còn có view ứng viên, kết quả bầu chọn, giá trị khớp, các lần quay về bảng gốc |
| `views/<CSDL>.{oracle,oracle_paper,oracle_fair,auto}.sql` | View của `vsql`, `vsql_paper`, `vsql_fair`, và view tự động của V-SQL+ |
| `llm_cache.sqlite`, `config.json` | Cache câu trả lời LLM và embedding; tham số của lần chạy |

---

## Kiểm thử (không cần GPU, Ollama hay BIRD)

```bash
python tests/test_compare.py   # TA-SQL / V-SQL / V-SQL+ với LLM giả lập, view kiểu Hình 3, giải mã view, xử lý lỗi Ollama 500
```

---

## Cấu trúc mã

```
run_compare.py          chạy so sánh TA-SQL / V-SQL / V-SQL+ (notebook gọi file này)
vsql/methods.py         các phương pháp: tasql, vsql, vsql_paper, vsql_fair, vsqlplus (+ biến thể), chấm điểm
vsql/tasql_prompts.py   prompt TA-SQL, chép nguyên văn từ mã chính thức
vsql/baselines.py       DIN-SQL, DAIL-SQL (baseline Bảng 3 của paper)
vsql/din_prompts.py     prompt DIN-SQL cho BIRD, trích nguyên văn từ mã chính thức
vsql/autoview.py        dựng view: theo JOIN đáp án (V-SQL, có kiểu Hình 3) và tự động từ khóa ngoại (V-SQL+)
vsql/views.py           kiểm tra số dòng view, giải mã view -> bảng gốc (CTE)
vsql/linking.py         liên kết giá trị, BM25 + embedding, hợp nhất RRF (V-SQL+)
vsql/meta.py            mô tả cột từ database_description/*.csv, trình bày schema kiểu Bảng 6
vsql/db.py              đọc schema, khóa ngoại (kèm suy luận), chạy SQL có timeout
vsql/llm.py             client Ollama / API kiểu OpenAI, cache SQLite, thử lại khi lỗi
vsql/report.py          EX, CI bootstrap, McNemar + Holm, phân loại lỗi, chi phí
notebooks/TASQL_VSQL_VSQLplus_Colab.ipynb   notebook Colab chính
tests/                  kiểm thử với LLM giả lập và CSDL mẫu (test_compare.py, make_toy.py)
docs/                   hướng dẫn, thiết kế, nhận xét kết quả
```

## Tài liệu

| File | Nội dung |
|---|---|
| [`docs/HUONG_DAN_COLAB_SO_SANH.md`](docs/HUONG_DAN_COLAB_SO_SANH.md) | Hướng dẫn chạy notebook Colab từng bước, giải thích các lựa chọn, xử lý lỗi |
| [`docs/TAI_HIEN_DUNG_VA_VSQLPLUS.md`](docs/TAI_HIEN_DUNG_VA_VSQLPLUS.md) | Kiểm tra phần tái hiện cũ, hai phiên bản dữ liệu, thiết kế V-SQL / V-SQL+, các điểm khác paper |
| [`docs/NHAN_XET_KET_QUA_QWEN35.md`](docs/NHAN_XET_KET_QUA_QWEN35.md) | Nhận xét, đánh giá kết quả qwen3.5:0.8b và 4b |

## Những điểm khác paper (tóm tắt)

- **Model**: Qwen nhỏ qua Ollama thay cho GPT-3.5 / GPT-4, nên số tuyệt đối không so được với Bảng 3 của paper; điều so được là
  thứ tự và chênh lệch giữa các phương pháp trên cùng model.
- **View**: paper không công bố view thiết kế tay; mã dựng view theo JOIN của SQL đáp án, đúng quy trình paper mô tả (mục 6).
  View theo JOIN đáp án nhìn đáp án của chính tập đánh giá (như paper), nên V-SQL có lợi thế mà V-SQL+ (view tự động) không có.
- **Evidence**: paper không nói rõ; mọi phương pháp đều dùng evidence của BIRD.
- **Phiên bản dữ liệu**: paper không ghi; mặc định dùng bản 2025-07-04.
- **TA-SQL**: hậu xử lý được nới để đọc được câu trả lời của mô hình chat; giá trị mẫu lấy theo thứ tự cố định thay vì ngẫu
  nhiên để chạy lại ra cùng kết quả.
