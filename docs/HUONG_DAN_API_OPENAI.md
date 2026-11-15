# Chạy V-SQL / DAIL-SQL bằng model GPT (API OpenAI): trên máy local và trên Colab

> **Lưu ý về model của paper.** Paper V-SQL dùng `gpt-3.5-turbo`, `gpt-4-32k` và `gpt-4-turbo`. OpenAI đã **tắt cả ba model này** trên API:
> - `gpt-4-32k` tắt ngày 6/6/2025.
> - `gpt-3.5-turbo` (gồm cả `-0125`) và `gpt-4-turbo` (gồm cả `-2024-04-09`) tắt ngày **23/10/2026**.
>
> Gọi các model này sẽ bị lỗi 404 ([trang deprecations của OpenAI](https://developers.openai.com/api/docs/deprecations)).
> Vì vậy chỉ chạy được với model **gần nhất còn hoạt động**. Khi báo cáo phải ghi rõ đã đổi model:
>
> | Model trong paper | Model thay thế đề xuất | Lý do |
> |---|---|---|
> | gpt-3.5-turbo | **`gpt-4o-mini`** | OpenAI giới thiệu model này là bản thay thế gpt-3.5-turbo; không phải model suy luận, nhận `temperature=0` và `max_tokens=800` như paper |
> | gpt-4-turbo | **`gpt-4.1`** (hoặc `gpt-4o`) | cùng hạng model lớn, không phải model suy luận, giữ được cấu hình của paper |
>
> Các model `gpt-5.x` (ví dụ `gpt-5.6-terra`, `gpt-5.6-sol`, là các model OpenAI ghi làm bản thay thế chính thức) là **model suy luận**. Chúng không nhận `temperature=0`, và token suy luận bị tính vào giới hạn 800 token đầu ra. Vì vậy chúng khác cấu hình paper nhiều hơn; xem mục 8.

---

## 1. Mua credit API

1. Vào **https://platform.openai.com** → **Sign up** (hoặc đăng nhập bằng tài khoản ChatGPT có sẵn).
   - **Gói ChatGPT Plus/Pro KHÔNG bao gồm API.** API tính tiền riêng, theo số token.
2. Vào **Settings** (bánh răng góc trên bên phải) → **Billing** → **Add payment details** → chọn *Individual*.
   - Dùng thẻ **Visa/Mastercard quốc tế**. Thẻ ghi nợ quốc tế của ngân hàng Việt Nam thường dùng được; thẻ nội địa Napas thì không.
3. Ở trang Billing, chọn **Add to credit balance**. Đây là hình thức nạp trước (trả trước), tối thiểu khoảng **$5**.
   - Gợi ý mức nạp: **$5** đủ cho `gpt-4o-mini` chạy cả 500 câu và nhiều lần chạy thử; **$20** đủ thêm `gpt-4.1` 500 câu (xem mục 6).
   - Có thể bị cộng thuế theo quốc gia. Credit có hạn sử dụng (thường 1 năm).
4. **Tắt "Auto recharge"** (tự nạp thêm). Khi tắt, số tiền đã nạp chính là mức chi tối đa: hết tiền thì API báo `insufficient_quota` và chương trình tự dừng, không bị trừ thêm.
5. (Nên làm) **Settings → Limits**: đặt ngưỡng email cảnh báo khi chi tiêu chạm một mức nhất định.

## 2. Tạo API key

1. Vào **https://platform.openai.com/api-keys** → **Create new secret key**.
2. Điền các ô như sau:
   - Name: ví dụ `vsql-plus`.
   - Project: `Default project`.
   - Permissions: `All`. Nếu chọn `Restricted` thì phải cho quyền **Write** ở mục *Model capabilities* (Chat completions).
3. **Copy key ngay**, vì key chỉ hiện một lần. Key có dạng `sk-proj-...`.
4. Giữ key bí mật:
   - **Không** dán key vào notebook, code hay chat.
   - **Không** commit key lên GitHub.
   - Nếu lỡ lộ key: vào lại trang api-keys → **Revoke**, rồi tạo key mới.

## 3. Gắn key vào chương trình

Chương trình tìm key theo thứ tự sau (code ở `vsql/llm.py`, hàm `find_api_key`):
1. Biến môi trường `OPENAI_API_KEY`.
2. File `.env` trong thư mục repo.
3. Colab Secrets.

### Trên máy local (macOS / Linux)
```bash
cd ~/proj/vsql-plus
cp .env.example .env
open -e .env        # sửa dòng OPENAI_API_KEY=sk-proj-...  (macOS; Linux: nano .env)
```
File `.env` đã có trong `.gitignore` nên không bị commit. Nếu muốn dùng biến môi trường thay cho file `.env`, thêm dòng sau vào `~/.zshrc` rồi mở terminal mới:
```bash
export OPENAI_API_KEY="sk-proj-..."
```

### Trên Google Colab
1. Mở notebook, bấm **biểu tượng chìa khoá** (Secrets) ở thanh bên trái.
2. **Add new secret**: Name = `OPENAI_API_KEY`, Value = key của bạn.
3. Bật công tắc **Notebook access** cho secret này.

Bước 2 của notebook sẽ đọc secret này. Key không hiện ra trong notebook.

## 4. Chạy trên máy local

API chạy trên máy chủ của OpenAI nên máy local **không cần GPU**. Máy chỉ cần Python ≥ 3.9 và mạng.

```bash
cd ~/proj/vsql-plus
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm                    # DAIL-SQL (che tên schema)

# Dữ liệu: câu hỏi 2025-07-04 (kiểm md5) + CSDL; --dail: tập train BIRD cho DAIL-SQL (lần đầu ~5–10 phút trên CPU)
python scripts/tai_du_lieu.py --dail
```

**a) Chạy thử 3 câu** (khoảng 1 phút, tốn dưới 1 cent với `gpt-4o-mini`):
```bash
python -u run_compare.py \
  --data minidev/MINIDEV/mini_dev_sqlite_2025-07-04.json \
  --db-root minidev/MINIDEV/dev_databases --tables-json minidev/MINIDEV/dev_tables.json \
  --dail-train minidev/bird_train/train.json --dail-train-tables minidev/bird_train/train_tables.json \
  --dail-cache minidev/bird_train \
  --backend openai --model gpt-4o-mini \
  --methods vsql,dailsql --limit 3 --out results_new/_thu_api
```
Xem kết quả trong `results_new/_thu_api/summary.md`. Bảng "Chi phí" trong file đó có số token trung bình mỗi câu, dùng để ước lượng tiền cho lần chạy thật.

**b) Chạy chính: 200 câu** (cùng mẫu với lần chạy qwen2.5-coder: `--sample 200 --seed 0`):
```bash
python -u run_compare.py \
  --data minidev/MINIDEV/mini_dev_sqlite_2025-07-04.json \
  --db-root minidev/MINIDEV/dev_databases --tables-json minidev/MINIDEV/dev_tables.json \
  --dail-train minidev/bird_train/train.json --dail-train-tables minidev/bird_train/train_tables.json \
  --dail-cache minidev/bird_train \
  --backend openai --model gpt-4o-mini --workers 4 \
  --methods vsql,dailsql --sample 200 --seed 0 \
  --out results_new/cmp_gpt-4o-mini_d2025_mau200
```
- Muốn chạy đủ 500 câu như paper: bỏ `--sample 200 --seed 0` và đổi thư mục `--out`.
- Muốn chạy model hạng GPT-4: đổi `--model gpt-4.1` và đổi thư mục `--out`.
- Muốn thêm V-SQL+: thêm `vsqlplus` vào `--methods`. Khi chạy qua API, V-SQL+ tự chuyển sang chọn view bằng BM25.
- **Bị ngắt giữa chừng** (mất mạng, hết tiền, Ctrl+C): chạy lại **đúng lệnh cũ**. Câu trả lời đã có nằm trong `llm_cache.sqlite` của thư mục kết quả, nên không bị tính tiền lại.

## 5. Chạy trên Google Colab

Notebook tải code từ GitHub (`chloenguyen167/vsqlplus`, nhánh `main`). Vì vậy phải **push code mới lên GitHub trước**.

1. Mở `notebooks/VSQL_VSQLplus_Colab.ipynb` trên Colab. Chạy qua API thì **không cần GPU**: Runtime → Change runtime type → CPU cũng được.
2. **Bước 1** (cấu hình):
   - `BACKEND = openai`
   - `API_MODELS = gpt-4o-mini` (nhiều model thì cách nhau bằng dấu phẩy, ví dụ `gpt-4o-mini, gpt-4.1`)
   - `SAMPLE = 200`
   - tick `vsql`, `dailsql`
   - `WORKERS = 4`
3. Chạy lần lượt:
   - **Bước 2**: nạp key từ Secrets.
   - **Bước 3 → 5**: tải code, tải dữ liệu, sinh view.
   - **Bước 6**: gửi thử 1 câu nhỏ tới mỗi model để kiểm tra key, số dư và tên model.
   - **Bước 7**: đồng bộ Drive.
   - **Bước 8**: chạy thử 3 câu.
   - **Bước 9**: chạy chính.
   - **Bước 10 → 12**: xem bảng kết quả, vẽ biểu đồ, tải về máy.
4. Colab bị ngắt: chạy lại Bước 1 → 7, rồi Bước 9. Phần đã chạy được khôi phục từ Drive và cache, nên không bị tính tiền lại.

## 6. Ước tính chi phí

Số token mỗi câu lấy từ lần chạy qwen2.5-coder 200 câu (tokenizer của GPT có thể lệch ±15%):

| Phương pháp | Token vào / ra mỗi câu |
|---|---|
| V-SQL (bản cũ đưa mọi view; bản truy hồi top-4 ngắn hơn) | ~9,1k / 150 |
| DAIL-SQL | 3k / 126 |
| **Cả hai** | **~12k / 280** |

Giá theo [bảng giá OpenAI](https://developers.openai.com/api/docs/pricing), Standard, ngày 14/11/2026:

| Model | Giá / 1M token (vào / ra) | 200 câu × 2 phương pháp | 500 câu × 2 phương pháp |
|---|---|---|---|
| `gpt-4o-mini` | $0.15 / $0.60 | **~$0.4** | **~$1** |
| `gpt-4.1-mini` | $0.40 / $1.60 | ~$1.1 | ~$2.6 |
| `gpt-4.1` | $2.00 / $8.00 | **~$5.3** | **~$13** |
| `gpt-4o` | $2.50 / $10.00 | ~$6.6 | ~$17 |
| `gpt-5.6-terra` | $2.00 / $12.00 | ~$5.5 + token suy luận | ~$14 + token suy luận |

- Phần lớn tiền là của **V-SQL**: prompt dài (Bảng 6 mở rộng), gọi 2 lần mỗi câu. Lần chạy thật gpt-4o-mini 500 câu × 3 phương pháp (V-SQL bản cũ đưa mọi view) hết khoảng $3.
- Tiền thực tế thường **thấp hơn** bảng trên, vì OpenAI tự giảm giá cho phần đầu prompt lặp lại (*cached input*, rẻ hơn 2–10 lần).
- V-SQL+ (bầu chọn 4 mẫu) tốn nhiều hơn V-SQL. Nên chạy thử 3 câu để xem số token trước.
- Xem số tiền đã tiêu ở **https://platform.openai.com/usage**. Số liệu có thể cập nhật trễ vài phút.

**Thứ tự đề xuất:**
1. Thử 3 câu (< $0.01).
2. `gpt-4o-mini` 200 câu (~$0.4).
3. `gpt-4.1` 200 câu (~$5.3).
4. Nếu cần thì chạy đủ 500 câu.

## 7. Cấu hình so với paper

| | Paper | Chương trình |
|---|---|---|
| temperature / top-p | 0 / 1 | 0 / mặc định (= 1) |
| max tokens đầu ra | 800 | 800 (`--num-predict`) |
| self-consistency / tự sửa lỗi | không dùng | không dùng (DAIL-SQL 1 mẫu, không bầu chọn) |
| D′ của V-SQL | view thiết kế theo JOIN đáp án, "retrieved" theo câu hỏi (không nói cách) | view theo JOIN đáp án + bảng còn lại; LLM chọn đối tượng theo câu hỏi (thêm 1 lần gọi, ~700 token) |
| Model | gpt-3.5-turbo, gpt-4-32k, gpt-4-turbo | đã bị tắt → `gpt-4o-mini`, `gpt-4.1`, ... (ghi rõ trong báo cáo) |

## 8. Model suy luận `gpt-5.x` / o-series (không khuyến nghị để tái hiện paper)

- Các model này không nhận `max_tokens` và `temperature=0`. Chương trình tự đổi sang `max_completion_tokens` và bỏ `temperature`, có in thông báo `[API] ...`.
- Token suy luận bị tính vào giới hạn 800 token đầu ra. Model có thể dùng hết 800 token để suy luận rồi trả về câu trả lời rỗng. Muốn dùng thì chạy ở máy local với `--reasoning-effort low --num-predict 4000`, và báo cáo rằng cấu hình đã khác paper.

## 9. Lỗi thường gặp

| Thông báo | Nguyên nhân → cách xử lý |
|---|---|
| `Khong tim thay API key` | Chưa có `.env` / biến môi trường / Secret. Trên Colab: chưa bật *Notebook access* hoặc chưa chạy Bước 2 |
| `HTTP 401` | Key sai hoặc đã bị thu hồi → tạo key mới |
| `insufficient_quota` / `het tien` | Chưa nạp hoặc đã hết credit (gói ChatGPT Plus không tính) → nạp thêm, chạy lại đúng lệnh cũ |
| `[API 429] cho ...s roi thu lai` | Chạm giới hạn tốc độ của tài khoản mới (tier thấp) → chương trình tự chờ; nếu lặp lại liên tục thì giảm `--workers` hoặc đặt `--rpm 30` |
| `model_not_found` / 404 | Sai tên model, hoặc model đã bị tắt (gpt-3.5-turbo, gpt-4-turbo) |
| `[API] ... dung max_completion_tokens` | Đang dùng model suy luận (mục 8). Đây là thông báo, không phải lỗi |
