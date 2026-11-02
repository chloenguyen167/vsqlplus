# Hướng dẫn chạy thực nghiệm V-SQL trên Google Colab

Tài liệu này hướng dẫn chạy notebook [`notebooks/VSQL_Colab.ipynb`](../notebooks/VSQL_Colab.ipynb) để:

1. **Tái hiện thực nghiệm của bài báo V-SQL** trên BIRD mini-dev (500 câu, 11 CSDL): so sánh V-SQL với cách sinh SQL một
   giai đoạn thông thường (`base`).
2. **Đánh giá hai cải tiến** mà nhóm đề xuất:
   - **CT5 – Sửa lỗi theo lược đồ**: chạy SQL do mô hình sinh, đọc thông báo lỗi của SQLite, sửa tên bảng/cột/alias theo
     lược đồ thật, tự thêm JOIN theo khóa ngoại khi thiếu bảng. Không gọi thêm LLM.
   - **CT7 – Bỏ phiếu theo kết quả thực thi**: sinh SQL từ 4 cách biểu diễn lược đồ (bảng gốc, view tự động, view kèm bảng
     gốc, 5 bảng/view chọn bằng BM25), sửa lỗi bằng CT5, chạy từng câu và chọn kết quả xuất hiện nhiều nhất.

với một mô hình mạnh hơn mô hình 0,8 tỷ tham số đã dùng trong báo cáo (ví dụ `qwen3.5:9b`, `qwen3:14b`, hoặc mô hình qua API).

Mở nhanh: <https://colab.research.google.com/github/chloenguyen167/vsqlplus/blob/main/notebooks/VSQL_Colab.ipynb>

---

## 1. Chuẩn bị

| Cần có | Ghi chú |
|---|---|
| Tài khoản Google | Để dùng Colab và lưu kết quả vào Google Drive (khoảng 1 GB trống: 800 MB dữ liệu + kết quả) |
| GPU trên Colab | Bản miễn phí có **T4 (16 GB)**; Colab Pro có **L4 (24 GB)**, **A100 (40/80 GB)** |
| API key (không bắt buộc) | Chỉ khi muốn gọi model qua API thay vì chạy trên GPU của Colab (xem mục 5) |

Không cần cài gì trên máy cá nhân. Notebook tự tải mã nguồn từ GitHub và tải BIRD mini-dev.

## 2. Chọn mô hình

Notebook mặc định **chạy mô hình mã nguồn mở trên GPU của Colab bằng Ollama**. Cách này không giới hạn số lượt gọi, chỉ giới
hạn bởi thời gian của phiên Colab. Thực nghiệm đầy đủ cần khoảng **3.000 lượt gọi** (khoảng 6 lượt cho mỗi câu), nên đây là cách
duy nhất chạy hết 500 câu miễn phí.

| Model (Ollama) | Dung lượng | GPU tối thiểu | Ghi chú |
|---|---|---|---|
| `qwen3:8b` | 5,2 GB | T4 | Mô hình dùng trong lần tái hiện đầu tiên |
| **`qwen3.5:9b`** (mặc định) | 6,6 GB | T4 | Thế hệ mới nhất cỡ vừa của Qwen, khuyến nghị cho T4 |
| `qwen3:14b` | 9,3 GB | T4 | Mạnh hơn, chậm hơn khoảng 1,5–2 lần |
| `gpt-oss:20b` | 14 GB | L4 / A100 | Mô hình suy luận của OpenAI; đặt `NUM_PREDICT` 2000–4000 |
| `qwen3.5:27b` | 17 GB | L4 / A100 | Gần mức GPT-4o trên nhiều bài đánh giá; cần Colab Pro |

Dung lượng lấy từ <https://ollama.com/library> (tháng 11/2026). Có thể gõ tên model khác vào ô `MODEL`, miễn là vừa với VRAM
của GPU (dung lượng model + khoảng 1–3 GB cho bộ nhớ đệm ngữ cảnh).

**Thời gian ước tính** (chưa đo trực tiếp trên Colab; ô chạy chính in ra thời gian còn lại thực tế):

| Cấu hình | 100 câu | 500 câu |
|---|---|---|
| T4 + model 8–9B | khoảng 30–50 phút | khoảng 2–4 giờ |
| T4 + `qwen3:14b` | khoảng 1–1,5 giờ | khoảng 4–6 giờ |
| L4/A100 + model 20–27B | khoảng 30–60 phút | khoảng 2–4 giờ |

Colab miễn phí thường ngắt sau vài giờ hoặc khi bạn không tương tác. Nếu muốn chạy đủ 500 câu, nên để `LUU_DRIVE = True`
(mặc định) để có thể chạy tiếp (mục 4).

## 3. Các bước chạy

Mở notebook, chọn **Runtime → Change runtime type → T4 GPU → Save**, rồi chạy lần lượt từng ô (nút ▶ bên trái mỗi ô, hoặc
`Ctrl+Enter`).

| Bước | Việc | Thời gian |
|---|---|---|
| 1. Cấu hình | Chọn `BACKEND`, `MODEL`, `SAMPLE`, `NUM_PREDICT`, `LUU_DRIVE` trong form | – |
| 2. GPU + Drive | Kiểm tra GPU, cảnh báo nếu model không vừa VRAM; cho phép truy cập Drive | < 1 phút |
| 3. Mã nguồn | Clone repo, chạy kiểm thử (`TAT CA KIEM THU DAT`) | ~1 phút |
| 4. Dữ liệu | Tải `minidev.zip` (~800 MB), chỉ giải nén phần SQLite; lưu zip vào Drive cho lần sau | 2–5 phút |
| 5a. Ollama | Cài Ollama, tải model, chạy thử 2 câu để đo tốc độ | 3–8 phút |
| 5b. API | (chỉ khi dùng API) nạp key, liệt kê model, gọi thử | < 1 phút |
| 6. Drive | Khôi phục kết quả lần trước (nếu có) và tự sao lưu mỗi 5 phút | – |
| 7. View | Sinh view theo đáp án (mô phỏng bài báo) và view tự động, kiểm tra số dòng | 1–2 phút |
| 8. Chạy thử | 5 câu × 5 cấu hình để chắc mọi thứ hoạt động | 2–5 phút |
| **9. Chạy chính** | Gọi LLM cho `base`, `vsql`, `auto_det`, `hybrid`, `hybrid_ret` | **lâu nhất** |
| 10. Cải tiến | CT5 cho cả 5 cấu hình (song song), rồi CT7 bỏ phiếu | 10–30 phút |
| 11. Kết quả | Bảng chính, kiểm định McNemar + Holm, biểu đồ | < 1 phút |
| 12. Tải về | Nén thư mục kết quả thành zip và tải về máy | < 1 phút |

**Mẹo:** chạy thử với `SAMPLE = 100` trước (lấy mẫu phân tầng theo CSDL × độ khó, giữ đúng tỉ lệ dễ/trung bình/khó). Khi đã
ổn, đặt `SAMPLE = 0` để chạy đủ 500 câu. Lần chạy đủ 500 câu dùng lại được các câu đã có trong cache.

## 4. Khi Colab bị ngắt giữa chừng

Kết quả được ghi ở `/content/ketqua/<tên lần chạy>` và tự sao lưu sang
`MyDrive/vsqlplus_ketqua/<tên lần chạy>` mỗi 5 phút. Khi bị ngắt:

1. Mở lại notebook, chọn lại GPU.
2. Chạy lại **Bước 1 → Bước 7** với **đúng cấu hình cũ** (cùng `BACKEND`, `MODEL`, `SAMPLE`, vì tên lần chạy được ghép từ các giá
   trị này). Bước 6 sẽ báo "Đã khôi phục từ Drive".
3. Chạy lại **Bước 9**. Chương trình tự bỏ qua các câu đã có kết quả; các lượt gọi LLM đã làm nằm trong `llm_cache.sqlite`
   nên không phải gọi lại.

Tối đa mất khoảng 5 phút công việc gần nhất.

## 5. Dùng API miễn phí thay cho GPU của Colab

Chọn `BACKEND = openai` ở Bước 1, rồi cất API key vào **Colab Secrets** (biểu tượng chìa khóa ở thanh bên trái → *Add new
secret*, đặt tên trùng với ô `API_KEY_SECRET`, bật *Notebook access*).

| `API_PRESET` | Địa chỉ | Lấy key | Ví dụ `API_MODEL` |
|---|---|---|---|
| `groq` | `https://api.groq.com/openai/v1` | <https://console.groq.com/keys> | `openai/gpt-oss-120b` |
| `gemini` | `https://generativelanguage.googleapis.com/v1beta/openai` | <https://aistudio.google.com/apikey> | một model Flash/Flash-Lite trong danh sách |
| `openrouter` | `https://openrouter.ai/api/v1` | <https://openrouter.ai/keys> | model có đuôi `:free` |

Bước 5b in ra danh sách model mà key của bạn được dùng; hãy chọn tên trong danh sách đó vì các nhà cung cấp thay đổi model
thường xuyên.

**Lưu ý quan trọng về hạn mức miễn phí.** Hạn mức thay đổi liên tục, hãy xem trang của nhà cung cấp trước khi chạy:

- Groq (tháng 10–11/2026): khoảng 30 lượt/phút, 1.000 lượt và 200.000 token mỗi ngày cho mỗi model
  (<https://console.groq.com/docs/rate-limits>).
- Gemini: các nguồn ghi từ 20 đến 1.500 lượt/ngày tùy model; con số chính xác nằm ở <https://aistudio.google.com/rate-limit>.

Một câu hỏi tốn khoảng 6 lượt gọi và 20.000–40.000 token đầu vào, nên với hạn mức miễn phí chỉ chạy được **khoảng vài chục câu
mỗi ngày**. Khi dùng API, nên đặt `SAMPLE` nhỏ (30–100) và `API_RPM` thấp hơn hạn mức một chút. Nếu hết hạn mức ngày, chương
trình dừng với lỗi 429; hôm sau chạy lại Bước 9 là tiếp tục được.

Mô hình suy luận (gpt-oss, các model "thinking") dùng thêm token để suy nghĩ, nên đặt `NUM_PREDICT` 2000–4000 để câu trả lời
không bị cắt.

## 6. Đọc kết quả

Thư mục kết quả gồm:

| File | Nội dung |
|---|---|
| `predictions_<cấu hình>.jsonl` | Kết quả từng câu: SQL sinh ra, SQL cuối, lỗi, đúng/sai, số token |
| `predictions_<cấu hình>_fix.jsonl` | Sau khi áp CT5 (thêm trường `repair_steps` ghi các bước sửa) |
| `predictions_mrv.jsonl` | Kết quả CT7 (trường `voted_from` cho biết câu được chọn từ nguồn nào) |
| `summary.md`, `summary.csv` | EX theo độ khó, khoảng tin cậy, so sánh ghép cặp với `vsql` và `base`, phân loại lỗi, chi phí |
| `views/` | Định nghĩa các view đã sinh cho từng CSDL |
| `llm_cache.sqlite` | Cache câu trả lời của LLM (để chạy tiếp, không cần nộp) |
| `bieu_do_ex.png` | Biểu đồ EX của 5 cấu hình chính |

Các chỉ số:

- **EX (execution accuracy)**: tỉ lệ câu có kết quả chạy SQL trùng với SQL đáp án (định nghĩa của BIRD).
- **Khoảng tin cậy 95%**: tính bằng bootstrap 2.000 lần trên các câu hỏi.
- **Kiểm định McNemar**: so sánh hai cấu hình trên cùng bộ câu, chỉ dựa trên các câu hai bên cho kết quả khác nhau
  ("thắng/thua"). p < 0,05 là khác biệt có ý nghĩa thống kê.
- **Hiệu chỉnh Holm**: điều chỉnh p khi kiểm định nhiều giả thuyết cùng lúc.

`hypotheses.py` kiểm định 4 giả thuyết chính:

| Mã | So sánh | Câu hỏi |
|---|---|---|
| P1 | `base_fix` vs `base` | CT5 có giúp cách làm thông thường không? |
| P2 | `vsql_fix` vs `vsql` | CT5 có giúp V-SQL không? |
| P5 | `mrv` vs `base` | CT7 có tốt hơn cách làm thông thường không? |
| P6 | `mrv` vs `vsql` | CT7 có tốt hơn V-SQL không? |

(P3, P4 thuộc các cải tiến không chọn nên được bỏ qua tự động.)

Kết quả tham khảo với `qwen3.5:0.8b` trên đủ 498 câu (bộ mini-dev có 2 câu bị lặp): base 8,4%, V-SQL 3,8%, base + CT5 11,4%,
CT7 13,5%. Với mô hình mạnh hơn, EX sẽ cao hơn nhiều; điều đáng quan tâm là các chênh lệch giữa cấu hình còn giữ được hay không.

## 7. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Bước 2 báo không có GPU | Runtime → Change runtime type → T4 GPU, rồi chạy lại từ Bước 1 |
| `CUDA out of memory`, hoặc Ollama chạy rất chậm (model bị đẩy sang CPU) | Chọn model nhỏ hơn; trên T4 dùng `qwen3.5:9b` hoặc `qwen3:8b` |
| `ollama pull` lỗi mạng | Chạy lại Bước 5a |
| Bước 9 dừng với lỗi kết nối `127.0.0.1:11434` | Ollama bị tắt (thường do Colab khởi động lại); chạy lại Bước 5a rồi Bước 9 |
| API báo `429` liên tục | Đã chạm hạn mức; giảm `API_RPM`/`SAMPLE`, đợi hôm sau rồi chạy lại Bước 9 |
| API báo `400`/`404` | Sai tên model; xem danh sách ở Bước 5b và sửa `API_MODEL` |
| Model trả lời rỗng / SQL bị cắt | Tăng `NUM_PREDICT` (2000–4000 cho mô hình suy luận) |
| Muốn chạy lại từ đầu | Đổi tên lần chạy (đổi `SAMPLE`/`MODEL`) hoặc xóa thư mục trên Drive |

## 8. Chạy trên máy cá nhân

Có thể chạy cùng các lệnh như notebook trên máy có Ollama (xem `README.md`):

```bash
D=minidev/MINIDEV
CHUNG="--data $D/mini_dev_sqlite.json --db-root $D/dev_databases"
python run_experiment.py $CHUNG --model qwen3.5:9b --out results/q35_9b --methods base,vsql,auto_det,hybrid,hybrid_ret
for m in base vsql auto_det hybrid hybrid_ret; do python improve.py results/q35_9b $CHUNG --fix --methods $m & done; wait
python improve.py results/q35_9b $CHUNG --vote mrv=base_fix,auto_det_fix,hybrid_ret_fix,hybrid_fix
python -c "from vsql import report; report.build('results/q35_9b')"
python hypotheses.py results/q35_9b
```

Gọi qua API thì thêm `--backend openai --base-url <địa chỉ> --api-key-env <TÊN_BIẾN> --rpm 25` và đặt API key vào biến môi
trường đó.
