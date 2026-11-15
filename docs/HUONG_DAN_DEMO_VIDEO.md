# Hướng dẫn chạy notebook demo và lời thoại quay video

Notebook: `notebooks/Demo_VSQL_VSQLplus.ipynb`. Kịch bản: `note.md`. Video dài **3 phút**, gồm: tái hiện V-SQL → cải tiến V-SQL+ →
đánh giá so sánh DAIL-SQL, V-SQL, V-SQL+.

Notebook có hai phần:

- **Chuẩn bị (ô A–D):** chạy trước khi quay. Mọi việc lâu đều nằm ở đây: dựng view, chỉ mục giá trị, nạp tập ví dụ DAIL-SQL, chạy sẵn
  10 câu × 4 phương pháp.
- **Demo (ô 1–6):** mỗi ô chạy khoảng 1 giây, chạy lại bao nhiêu lần cũng được.

## 1. Cài đặt (làm một lần)

### Cách A: chạy trên máy (khuyên dùng)

```bash
cd ~/proj/vsql-plus
.venv/bin/pip install jupyter matplotlib
.venv/bin/jupyter notebook notebooks/Demo_VSQL_VSQLplus.ipynb
```

Phải mở Jupyter bằng `.venv` của repo: môi trường này có spaCy `en_core_web_sm`, DAIL-SQL cần nó để chọn đúng ví dụ như lần chạy 500 câu.
Với `gpt-4o-mini`, notebook dùng cache câu trả lời nên không gọi API, không cần khoá.

### Cách B: chạy trên Colab (toàn bộ notebook khoảng 3–4 phút)

Notebook trên Colab tải một **gói dữ liệu demo** (266 MB) thay vì `minidev.zip` đầy đủ (1,4 GB, máy chủ ở Bắc Kinh). Gói gồm 6 CSDL của
10 câu demo, file câu hỏi, tập train DAIL-SQL đã xử lý sẵn (khỏi tính lại khoảng 8 phút) và cache câu trả lời gpt-4o-mini, nên
**không cần API key** và không gọi API.

Làm một lần trên máy:

1. Commit và đẩy code lên GitHub (notebook tự `git clone` repo).
2. Đưa gói dữ liệu lên GitHub Release (gói đã dựng sẵn ở `minidev/vsql_demo_pack.zip`). Trên web: vào repo
   `chloenguyen167/vsqlplus` → **Releases** → **Draft a new release** → ô tag gõ `demo-data-v1` (chọn "Create new tag") → kéo thả file
   `vsql_demo_pack.zip` vào ô đính kèm → **Publish release**. Giữ đúng tên tag và tên file; repo phải công khai để Colab tải không cần
   đăng nhập. Nếu có GitHub CLI (`brew install gh`):

   ```bash
   gh release create demo-data-v1 minidev/vsql_demo_pack.zip --title "Dữ liệu demo" --notes "Gói dữ liệu cho notebooks/Demo_VSQL_VSQLplus.ipynb"
   ```

   Đổi danh sách câu demo thì dựng lại gói bằng `.venv/bin/python scripts/make_demo_pack.py`, rồi thay file trong release:
   `gh release upload demo-data-v1 minidev/vsql_demo_pack.zip --clobber`.

Thời gian trên Colab (ước tính, chưa đo trên Colab thật): ô B khoảng 1 phút (clone, cài thư viện còn thiếu, tải và giải nén gói); ô C
khoảng 1–1,5 phút (tải mô hình embedding cho DAIL-SQL, dựng view, chạy sẵn 10 câu); các ô demo mỗi ô khoảng 1 giây.

Chỉ khi đổi sang model khác `gpt-4o-mini` mới cần khoá: biểu tượng chìa khoá ở thanh bên trái, Tên `OPENAI_API_KEY`, Giá trị là khoá
`sk-...`, bật "Quyền truy cập vào sổ tay".

## 2. Tuỳ chọn

| Ô | Tuỳ chọn | Giá trị cho video | Ý nghĩa |
|---|---|---|---|
| A | `MODEL` | `gpt-4o-mini` | Đổi model thì phải chạy lại ô A → D. Model khác gọi API thật; tên có dấu `:` (vd `qwen2.5-coder:7b`) chạy qua Ollama trên Colab T4 |
| 3 | `SO_CAU` | `3` | 1–10 câu theo danh sách trong `note.md`. Từ 3 câu trở lên có đủ dễ / trung bình / khó |
| 3 | Phương pháp | bật cả 4 | DAIL-SQL, V-SQL (đưa hết view), V-SQL (LLM chọn view), V-SQL+ (bỏ bầu chọn) |
| 4 | `XEM_UID` | `259` | Câu muốn xem luồng gọi LLM chi tiết |

Đổi `SO_CAU` hoặc phương pháp: chỉ chạy lại ô 3 → 5, không phải chuẩn bị lại.

## 3. Trước khi bấm quay

1. Chạy ô A → D. Trên máy mất khoảng 20 giây; Colab khoảng 2–3 phút. Ô C in ra "Đã chuẩn bị xong" là được. Muốn quay cả phần
   chuẩn bị trên Colab thì toàn bộ video khoảng 5–6 phút; nên cắt đoạn chờ khi dựng video.
2. Chạy thử ô 1 → 6 một lần để kiểm tra hiển thị, rồi thu gọn các dòng có thể bấm mở (prompt, "Lần 1, Lần 2...").
3. Thu gọn phần Chuẩn bị (bấm mũi tên cạnh tiêu đề "Chuẩn bị") để màn hình bắt đầu từ phần Demo.
4. Phóng to chữ trình duyệt (Cmd + `+`) lên khoảng 125%; đóng các tab, thông báo không liên quan.

## 4. Lời thoại (3 phút)

Phần trong ngoặc vuông là thao tác trên màn hình. Lời thoại viết sẵn để đọc.

### Cảnh 1. Mở đầu (15 giây)

[Ô markdown đầu notebook.]

> Video này trình bày ba việc: tái hiện phương pháp V-SQL, đề xuất bản cải tiến V-SQL+, và so sánh cả hai với DAIL-SQL. Bộ dữ liệu là BIRD
> mini-dev, 500 câu; mọi phương pháp dùng cùng model gpt-4o-mini.

### Cảnh 2. Tái hiện V-SQL (35 giây)

[Chạy ô 1. Chỉ vào dòng "10 bảng → 3 view", rồi định nghĩa `v_superhero`.]

> V-SQL gộp các bảng liên quan thành view. Giai đoạn một, LLM viết SQL trên view nên gần như không cần JOIN; giai đoạn hai viết lại về bảng
> gốc. Paper thiết kế view bằng tay theo các phép JOIN trong SQL đáp án nhưng không công bố, nên nhóm dựng tự động theo cùng nguyên tắc.
> View v_superhero trùng đủ 12 cột với Hình 3 của paper. Prompt hai giai đoạn giữ nguyên như Hình 4 và Hình 5.

### Cảnh 3. Cải tiến V-SQL+ (35 giây)

[Chạy ô 2. Chỉ vào chú thích `via` trong view, rồi ví dụ `'Human'`, rồi bảng đóng góp phía trên.]

> V-SQL+ tạo view tự động từ khoá ngoại, không cần nhìn đáp án, và chọn view bằng truy hồi thay vì gọi thêm LLM. Prompt mới ghi rõ phải
> viết SQLite. Liên kết giá trị: câu hỏi nói "human", chương trình tìm thấy giá trị thật trong cơ sở dữ liệu là "Human" viết hoa và đưa vào
> prompt. Trên 500 câu, prompt mới đóng góp tám điểm, liên kết giá trị hơn bốn điểm.

### Cảnh 4. Đánh giá trên câu demo (60 giây)

[Chạy ô 3. Chỉ vào dòng thời gian chạy, rồi bảng ✅/❌.]

> Bây giờ chạy bốn phương pháp trên ba câu demo, đủ dễ, trung bình và khó. Mỗi câu SQL dự đoán được chạy trên cơ sở dữ liệu và so với kết quả
> của SQL đáp án.

[Chạy ô 4. Mở "Lần 1" của DAIL-SQL, cuộn tới câu trả lời; mở "Lần 1", "Lần 2" của V-SQL.]

> Câu 259 hỏi về siêu anh hùng có alignment là 'Bad'. DAIL-SQL dùng bảy ví dụ và schema gốc, nhưng đoán cột superhero.alignment không tồn
> tại nên sai. V-SQL viết SQL trên view đã có sẵn cột alignment, giai đoạn hai tự thêm hai phép JOIN và ra đúng. V-SQL+ cũng đúng.

[Chạy ô 5, chỉ vào biểu đồ.]

> Về chi phí: DAIL-SQL và V-SQL gọi LLM hai lần mỗi câu, bản LLM chọn view gọi ba lần, V-SQL+ dưới hai lần.

### Cảnh 5. Kết quả trên 500 câu (25 giây)

[Chạy ô 6. Chỉ vào biểu đồ bên trái rồi bên phải.]

> Trên đủ 500 câu: DAIL-SQL đạt 50 phần trăm, V-SQL tái hiện 46 đến 47, V-SQL+ đạt 52,6, cao nhất. Biểu đồ bên phải cho thấy lý do: ở giai
> đoạn một, V-SQL+ gần như hết lỗi thực thi như sai tên cột hay dùng hàm sai.

### Cảnh 6. Kết luận (10 giây)

[Cuộn tới "Kết luận".]

> Tóm lại, bản tái hiện V-SQL chưa vượt DAIL-SQL, còn V-SQL+ đạt kết quả cao nhất với chi phí gần bằng DAIL-SQL. Cảm ơn mọi người đã theo
> dõi.

## 5. Sự cố thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `CẢNH BÁO: thiếu spaCy en_core_web_sm` | Đang chạy bằng python hệ thống; mở Jupyter bằng `.venv/bin/jupyter` |
| Ô B in `Không tải được gói dữ liệu demo` | Chưa tạo release `demo-data-v1` (mục 1, cách B, bước 2). Notebook sẽ tải `minidev.zip` đầy đủ và tính lại tập train DAIL-SQL, mất thêm 10–20 phút |
| Ô C in `[DAIL-SQL] tinh embedding ...` hoặc `chuan bi 9428 vi du train` | Thiếu bản xử lý sẵn của tập train (không có gói dữ liệu); chờ khoảng 8 phút hoặc tạo release rồi chạy lại từ ô B |
| Ô C báo `Chua co API key` | Model khác `gpt-4o-mini` cần khoá; xem cuối mục 1, cách B |
| Ô 3–6 báo `NameError` | Chưa chạy phần Chuẩn bị, hoặc kernel vừa khởi động lại: chạy lại ô A → D |
| Colab báo lỗi `--vsql-select` | Code trên GitHub là bản cũ; đẩy code mới lên rồi chạy lại ô B |
