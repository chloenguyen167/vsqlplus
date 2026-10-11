# Tái hiện V-SQL và đánh giá 4 cải tiến (qwen3 qua Ollama)

Gói mã chạy trên máy bạn, chỉ dùng thư viện chuẩn Python ≥ 3.8 (không cần `pip install`).

## 0. Chạy nhanh, không cần Ollama hay BIRD

```bash
python tests/test_all.py     # kiểm thử phần tất định + đường ống với LLM giả lập
python demo.py               # minh họa 4 cải tiến trên CSDL mẫu theo schema superhero
```

`demo.py` dùng cơ sở dữ liệu mẫu ngẫu nhiên (`tests/make_toy.py`) và một LLM giả lập theo kịch bản, nên chỉ kiểm tra
tính đúng đắn của phần tất định (view tự động, mở rộng CTE, phát hiện view 1-N, truy xuất). Kết quả mẫu nằm ở
`docs/demo_output.txt`. **Đây không phải kết quả thực nghiệm trên BIRD.**

## Cấu trúc

```
vsql/db.py          đọc schema, khóa ngoại, giá trị mẫu; chạy SQL có timeout; phân loại lỗi
vsql/views.py       sinh view (theo đáp án / tự động / viết tay), kiểm tra số dòng, unfold (CT1)
vsql/retrieval.py   BM25, embedding, RRF (CT4)
vsql/pipeline.py    7 cấu hình + prompt
vsql/llm.py         client Ollama có cache; MockLLM
vsql/report.py      EX, CI bootstrap, McNemar, phân loại lỗi, chi phí
run_experiment.py   chạy thực nghiệm trên BIRD mini-dev
demo.py, tests/     demo và kiểm thử
```

## 1. Chuẩn bị

```bash
ollama pull qwen3:8b            # hoặc qwen3:14b / qwen3:32b tùy VRAM
# Dữ liệu BIRD mini-dev (500 câu, 11 database): tải minidev.zip rồi giải nén
#   https://bird-bench.oss-cn-beijing.aliyuncs.com/minidev.zip
python tests/test_all.py        # kiểm thử phần tất định, không cần Ollama, không cần BIRD
```

## 2. Chạy

```bash
D=minidev/MINIDEV
# (a) Xem trước view được sinh, chưa gọi LLM  ->  results/q8/views/*.sql
python run_experiment.py --data $D/mini_dev_sqlite.json --db-root $D/dev_databases --out results/q8 --views-only

# (b) Chạy thử 20 câu để ước lượng thời gian
python run_experiment.py --data $D/mini_dev_sqlite.json --db-root $D/dev_databases --out results/thu --limit 20

# (c) Chạy đầy đủ 7 cấu hình trên 500 câu
python run_experiment.py --data $D/mini_dev_sqlite.json --db-root $D/dev_databases --model qwen3:8b --out results/q8

# (d) Đo riêng bước truy xuất theo k (không gọi LLM)
python run_experiment.py --data $D/mini_dev_sqlite.json --db-root $D/dev_databases --out results/q8 --retrieval-sweep
```

Chạy được ngắt giữa chừng rồi chạy lại: câu đã xong được bỏ qua, câu trả lời của LLM được cache trong
`llm_cache.sqlite`. Kết quả nằm ở `results/q8/summary.md`, `summary.csv`, `predictions_<cấu hình>.jsonl`.
Tổng cộng khoảng 7 lượt gọi LLM cho mỗi câu hỏi (3.500 lượt cho 500 câu).

Trước khi chấm điểm, chương trình gom mọi prompt còn thiếu, sắp theo thứ tự chữ rồi gọi LLM tuần tự (bước *prefetch*):
các prompt chung schema đứng liền nhau nên Ollama dùng lại KV cache của phần đầu prompt, nhanh hơn 3–5 lần. Kết quả từng câu
không đổi. Không nên dùng `--workers 2`: trên một GPU, hai luồng tranh nhau slot cache và chậm hơn.
Xem tiến độ và thời gian còn lại: `./progress.sh`. Chạy trên tập con: `--sample N` (mẫu phân tầng theo CSDL × độ khó) hoặc
`--qids file.json`. Phân tích bổ sung (EX theo CSDL, theo số JOIN): `python analyze.py results/q8 --data $D/mini_dev_sqlite.json`.

Tham số đáng chú ý: `--num-ctx` (mặc định 16384; Ollama mặc định cắt prompt ở 4096 nên phải đặt đủ lớn,
chương trình sẽ cảnh báo nếu chạm ngưỡng), `--think` (bật suy luận của qwen3, khi đó nên tăng `--num-predict`),
`--infer-fk` (suy thêm khóa ngoại cho database thiếu khai báo), `--topk`, `--retriever bm25|embed|hybrid`,
`--depth`, `--max-cols`, `--no-evidence`.

## 3. Bảy cấu hình

| Cấu hình | View lấy từ đâu | Bảng gốc trong prompt | Đưa dummy SQL về bảng gốc | Ý nghĩa |
|---|---|---|---|---|
| `base` | không dùng view | tất cả | (một giai đoạn) | baseline zero-shot |
| `vsql` | theo JOIN trong SQL đáp án | bảng không thuộc view nào | LLM tái tạo | **tái hiện paper** |
| `vsql_det` | như `vsql` | như `vsql` | chèn CTE, tất định | cải tiến 1 |
| `auto_llm` | tự động từ đồ thị khóa ngoại | bảng không thuộc view nào | LLM tái tạo | cải tiến 2 |
| `auto_det` | tự động | như trên | tất định | cải tiến 1 + 2 |
| `hybrid` | tự động | tất cả | tất định | + cải tiến 3 (schema lai) |
| `hybrid_ret` | tự động | top-k view/bảng | tất định | + cải tiến 4 (truy xuất) |

`vsql` và `vsql_det` dùng **cùng một prompt giai đoạn 1** nên nhận cùng một dummy SQL (qua cache, temperature 0).
Chênh lệch giữa hai cấu hình này vì thế chỉ do giai đoạn 2. Tương tự cho `auto_llm` và `auto_det`.

### Cách hiện thực từng cải tiến
1. **Viết lại tất định** (`views.unfold`): định nghĩa view được chèn thành CTE trước dummy SQL. Các `LEFT JOIN`
   N-1 mà truy vấn không dùng đến bị cắt bỏ (an toàn vì không đổi số dòng). Không gọi LLM.
2. **View tự động** (`views.auto_views`): với mỗi bảng có khóa ngoại, nối `LEFT JOIN` sang các bảng cha theo
   chiều N-1 (đã kiểm tra khóa được tham chiếu là duy nhất), sâu `--depth` mức, mỗi khóa ngoại một alias riêng.
   Bảng cầu nối N-N tự thành view riêng. Sau đó kiểm tra số dòng view bằng số dòng bảng gốc.
3. **Schema lai**: prompt gồm cả view lẫn bảng gốc, kèm quy tắc khi nào dùng loại nào; LLM được phép nối view với bảng.
4. **Truy xuất**: BM25 trên tên view/bảng, tên cột và giá trị mẫu; tùy chọn embedding qua Ollama hoặc kết hợp RRF.

## 4. Metric trong `summary.md`
- **EX** theo định nghĩa của BIRD (so tập dòng kết quả), tổng và theo độ khó, kèm khoảng tin cậy bootstrap 95%.
- **So sánh ghép cặp với `vsql`**: chênh lệch EX, khoảng tin cậy, kiểm định McNemar chính xác.
- **Phân loại lỗi**: `no such column` / `no such table` / `ambiguous column` (ảo giác schema), cú pháp,
  kết quả rỗng, kết quả sai.
- **Chi phí**: số lượt gọi LLM, token vào/ra, thời gian, số đối tượng schema trong prompt, độ phủ bảng đáp án, VES xấp xỉ.
- **Đóng góp riêng** của từng cải tiến và **thống kê view** từng database.

## 5. Những điểm khác với paper (cần ghi rõ khi báo cáo)
- **Mô hình**: qwen3 thay cho GPT-3.5/GPT-4, nên số EX tuyệt đối không so trực tiếp được với Bảng 3 của paper.
  So sánh giữa các cấu hình trong cùng một lần chạy thì hợp lệ.
- **View của paper không được công bố.** `vsql` mô phỏng quy trình paper mô tả (thiết kế view theo JOIN trong
  SQL đáp án) bằng thuật toán `views.oracle_views`. Muốn dùng view viết tay, đặt `views_manual/<db_id>.sql`
  gồm các lệnh `CREATE VIEW ... AS SELECT ...;` (sẽ thay cho view oracle của database đó).
- **Prompt** do tôi viết lại theo mô tả của paper, không sao nguyên văn phụ lục.
- **Baseline DIN-SQL, DAIL-SQL, TA-SQL không được cài lại**; chỉ có baseline `base`.
- Paper không nói có dùng `evidence` và giá trị mẫu hay không; ở đây cả hai được bật cho *mọi* cấu hình
  (tắt bằng `--no-evidence`, `--samples 0`).
- View `oracle` nhìn đáp án của tập đánh giá (như paper), nên `vsql`/`vsql_det` có lợi thế không công bằng
  so với các cấu hình `auto*`/`hybrid*`.
