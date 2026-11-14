# Hướng dẫn chạy notebook demo và kịch bản quay video

Notebook: `notebooks/Demo_LuongGoiLLM_3PP.ipynb`. Kịch bản gốc: `note.md`. Video dài khoảng **5–6 phút**, so sánh 4 cấu hình:
DAIL-SQL, V-SQL (đưa hết view), V-SQL (LLM chọn view), V-SQL+ (bỏ bầu chọn).

## 1. Cài đặt (làm một lần)

### Cách A: chạy trên máy (khuyên dùng, không tốn tiền)

Máy đã có kết quả 500 câu ở `results_new/cmp_gpt-4o-mini_d2025`. Notebook chép cache câu trả lời LLM từ đó, nên **không gọi API, không
tốn tiền, chạy vài giây**.

```bash
cd ~/proj/vsql-plus
.venv/bin/pip install jupyter matplotlib pandas
.venv/bin/jupyter notebook notebooks/Demo_LuongGoiLLM_3PP.ipynb
```

- Phải dùng `.venv` của repo: môi trường này có spaCy `en_core_web_sm`, mà DAIL-SQL cần nó để chọn đúng ví dụ như lần chạy 500 câu. Nếu
  thiếu, notebook in dòng `CẢNH BÁO: thiếu spaCy ...`.
- Không cần API key nếu chỉ chạy các câu đã có trong cache (cả 500 câu đều đã có với gpt-4o-mini).

### Cách B: chạy trên Colab

1. Đẩy code lên GitHub trước, vì notebook tự `git clone` repo.
2. Mở notebook trên Colab và thêm secret `OPENAI_API_KEY` (biểu tượng chìa khoá ở thanh bên trái, bật "Notebook access").
3. Colab không có cache 500 câu nên phải gọi API thật: khoảng 0,005 USD mỗi câu cho cả 4 cấu hình, tức khoảng 0,015 USD cho 3 câu demo. Lần
   đầu mất 3–5 phút để tải dữ liệu.

## 2. Các tuỳ chọn ở ô 1 (Cấu hình)

| Tuỳ chọn | Giá trị cho video | Ý nghĩa |
|---|---|---|
| `SO_CAU` | `3` | Số câu, tự do từ 1 đến 500 |
| `CACH_CHON` | `kich_ban` | `kich_ban`: câu minh hoạ (259, 421, 380, 470, 427), quá 5 câu thì phần còn lại lấy ngẫu nhiên theo tỷ lệ độ khó. `ngau_nhien_theo_do_kho`: ngẫu nhiên, giữ tỷ lệ dễ / trung bình / khó 148 / 250 / 102. `dau_tien`: các câu đầu. `theo_uid`: đúng các uid trong `UIDS` |
| `SEED` | `0` | Đổi số này để lấy bộ câu ngẫu nhiên khác |
| `LOC_DB` | để trống | Chỉ lấy câu của các CSDL này, ví dụ `superhero` |
| 4 ô tick cấu hình | bật cả 4 | Tắt bớt nếu muốn so sánh ít hơn |
| `HIEN_CHI_TIET` | `3` | Số câu đầu hiện chi tiết từng lần gọi ở Phần 2; các câu sau chỉ tính vào bảng tổng hợp |
| `CAT_PROMPT` | `3000` | Cắt prompt dài khi hiển thị, cho màn hình gọn; `0` = hiện đủ |
| `GIOI_HAN_USD` | `1.0` | Dừng nếu tiền gọi API thật vượt mức này |

Muốn có số liệu tổng hợp ngoài video: đặt `SO_CAU = 100` (hoặc `500`), `CACH_CHON = ngau_nhien_theo_do_kho`, `HIEN_CHI_TIET = 3`. Ở Phần 3
sẽ có thêm bảng độ chính xác theo độ khó. Chạy đủ 500 câu từ cache mất khoảng 6 phút, ra đúng số trong `summary.md`.

## 3. Trước khi bấm quay

1. Chạy lần lượt các ô "Chuẩn bị" (ô 1 → 5) **trước**, để khi quay không phải chờ. Ô 5 in mỗi câu một dòng `ĐÚNG/sai` cho từng cấu hình.
2. Chạy ô 6 (Phần 2) và ô 7 (Phần 3) một lần để kiểm tra hiển thị, rồi thu gọn hết các dòng `Lần 1, Lần 2...` lại.
3. Phóng to chữ trình duyệt (Cmd + `+`) lên khoảng 125%. Đóng các tab và thông báo không liên quan.
4. Mở sẵn file này ở một cửa sổ khác để đọc lời thoại.

## 4. Kịch bản quay và lời thoại

Lời thoại viết sẵn để đọc. Phần trong ngoặc vuông là thao tác trên màn hình.

### Cảnh 1. Giới thiệu (khoảng 30 giây)

[Màn hình: ô markdown đầu notebook, bảng 4 cấu hình.]

> Xin chào. Video này minh hoạ luồng gọi LLM của ba phương pháp Text-to-SQL trên bộ BIRD mini-dev: DAIL-SQL, V-SQL và V-SQL+ do nhóm cải
> tiến.
>
> Cả ba dùng cùng một mô hình là gpt-4o-mini, nhiệt độ 0. Điều cần xem là: mỗi phương pháp gọi LLM mấy lần, mỗi lần gửi gì và nhận lại gì.
>
> V-SQL có hai bản: đưa hết view vào prompt, và để LLM chọn view trước. V-SQL+ dùng bản bỏ bầu chọn, để cùng điều kiện một mẫu với
> DAIL-SQL.

### Cảnh 2. Chuẩn bị (khoảng 20 giây)

[Cuộn qua ô 1 và ô 5, đã chạy sẵn. Dừng ở kết quả ô 5.]

> Ở ô cấu hình, chọn số câu và cách chọn câu. Video này dùng ba câu minh hoạ, là những câu V-SQL làm đúng còn DAIL-SQL làm sai.
>
> Ô này chạy cả bốn cấu hình trên ba câu. Các câu trả lời đã có sẵn trong cache của lần chạy 500 câu, nên không gọi lại API.

### Cảnh 3. Câu chính: uid 259, superhero (khoảng 2 phút 30 giây)

[Chạy ô 6. Dừng ở câu uid 259, chỉ vào câu hỏi và SQL đáp án.]

> Câu hỏi: phần trăm siêu anh hùng có alignment là 'Bad', và bao nhiêu trong số đó do Marvel Comics xuất bản. SQL đáp án phải nối ba bảng:
> superhero, publisher và alignment.

[Mở "Lần 1" của DAIL-SQL, cuộn qua 7 ví dụ, rồi tới schema `CREATE TABLE`.]

> DAIL-SQL gọi LLM hai lần. Prompt gồm bảy câu ví dụ lấy từ tập train BIRD, chọn theo độ giống câu hỏi. Ở đây đều là các câu tính phần trăm.
> Sau đó là schema dạng CREATE TABLE.

[Mở phần Output của DAIL-SQL, chỉ vào `T1.alignment`.]

> Mô hình viết superhero.alignment. Nhưng bảng superhero chỉ có cột alignment_id, nên câu SQL bị lỗi "no such column". Lần gọi thứ hai chọn
> lại ví dụ theo khung của SQL nháp, nhưng vẫn mắc cùng lỗi.

[Mở "Lần 1" của V-SQL (đưa hết view), chỉ vào `# view: v_superhero` và các cột `alignment`, `publisher_name`.]

> V-SQL không đưa bảng gốc mà đưa view. View v_superhero này giống hệt Hình 3 trong paper: nó đã gộp sẵn tên alignment, tên nhà xuất bản,
> màu mắt, giới tính... vào một bảng ảo.

[Mở Output, chỉ vào dummy SQL.]

> Vì vậy câu SQL nháp ở giai đoạn 1 không cần JOIN nào: chỉ lọc v_superhero.alignment bằng 'Bad'.

[Mở "Lần 2" của V-SQL, chỉ vào `# view schemas`, `# relevant table schemas` rồi Output.]

> Giai đoạn 2 đưa cho LLM định nghĩa của view, SQL nháp, và chỉ những bảng gốc thật sự cần. LLM viết lại thành SQL trên bảng gốc, tự thêm
> hai phép JOIN với publisher và alignment. Kết quả đúng.

[Mở "Lần 1" của V-SQL (LLM chọn view).]

> Bản LLM chọn view có thêm một lần gọi ở đầu. LLM chỉ nhận danh sách tên view và tên cột, khoảng 350 token, rồi trả lời cần v_superhero.
> Nhờ vậy prompt giai đoạn 1 ngắn đi hơn một nửa. Bước chọn này nhóm tự thêm, vì paper không mô tả cách chọn view.

[Mở "Lần 1" của V-SQL+, cuộn tới `# matched database values`.]

> V-SQL+ dùng view tự sinh từ khoá ngoại, không cần nhìn SQL đáp án. Prompt nói rõ phải viết SQLite, và có thêm mục giá trị khớp câu hỏi:
> 'Bad' là giá trị của cột alignment, 'Marvel Comics' là giá trị của cột publisher_name. Mô hình viết thẳng trên v_superhero và cũng đúng.

### Cảnh 4. Hai câu còn lại (khoảng 1 phút)

[Cuộn tới uid 421, chỉ vào tiêu đề từng cấu hình (đúng/sai) và SQL cuối; chỉ mở Output của DAIL-SQL.]

> Câu 421, CSDL toxicology: liệt kê các nguyên tố của phân tử TR004. DAIL-SQL nối thừa bảng molecule với atom, rồi lấy cột element từ nhầm
> bảng, nên bị lỗi. V-SQL chỉ cần view v_atom, không JOIN.

[Cuộn tới uid 380.]

> Câu 380, CSDL card_games: đếm số lá bài trong bộ "Hauptset Zehnte Edition" do Adam Rex vẽ. DAIL-SQL nối sai khoá: cards.uuid với setCode.
> Câu SQL chạy được nhưng ra kết quả sai. V-SQL nối đúng theo setCode.
>
> Cả ba câu cho thấy đúng điều paper muốn chứng minh: khi schema có nhiều khoá ngoại, view giúp mô hình bớt phải tự JOIN và bớt đoán tên cột.

### Cảnh 5. Số lần gọi LLM (khoảng 1 phút)

[Chạy ô 7. Chỉ vào biểu đồ, rồi bảng số đo 500 câu bên dưới.]

> Biểu đồ cho thấy số lần gọi trung bình mỗi câu, chia theo giai đoạn. DAIL-SQL gọi một đến hai lần. V-SQL đưa hết view gọi hai lần. V-SQL
> có LLM chọn view gọi ba lần. V-SQL+ gọi một lần, thêm giai đoạn 2 khi câu SQL nháp có dùng view.
>
> Bảng dưới là số đo trên đủ 500 câu. Số lần gọi không quyết định chi phí. V-SQL đưa hết view chỉ gọi hai lần nhưng đắt nhất, vì prompt dài
> nhất, khoảng 14 nghìn token. DAIL-SQL đọc ít nhất nhưng viết nhiều nhất.

### Cảnh 6. Chốt (khoảng 30 giây)

[Cuộn tới "Phần 4. Chốt".]

> Tóm lại: ở các câu nhiều khoá ngoại, view của V-SQL giúp đúng như paper nói. Nhưng trên đủ 500 câu, V-SQL vẫn thấp hơn DAIL-SQL 3,2 điểm,
> 46,8 so với 50,0. Khác biệt này không có ý nghĩa thống kê. Lý do chính là prompt giai đoạn 1 của paper không có ví dụ và không nói rõ phải
> viết SQLite, trong khi DAIL-SQL có bảy ví dụ.
>
> V-SQL+ đạt 52,6, cao nhất, với chi phí chỉ hơn DAIL-SQL một chút. Nó thắng nhờ gần như không còn lỗi thực thi như sai tên cột. Cảm ơn mọi
> người đã theo dõi.

## 5. Sự cố thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `CẢNH BÁO: thiếu spaCy en_core_web_sm` | Đang chạy bằng python hệ thống; mở Jupyter bằng `.venv/bin/jupyter` |
| `CHƯA CÓ OPENAI_API_KEY` | Không sao nếu câu đã có trong cache. Câu chưa có thì cần key: biến môi trường, file `.env` hoặc Colab Secrets |
| Ô 5 dừng với `vượt GIOI_HAN_USD` | Tăng `GIOI_HAN_USD` rồi chạy lại ô 5; phần đã gọi nằm trong cache, không tốn lại |
| Ô 5 chạy lâu ở câu đầu tiên | Lần đầu DAIL-SQL nạp mô hình embedding và tập train, khoảng 5–10 giây |
| Đổi `SO_CAU` / `CACH_CHON` mà kết quả không đổi | Chạy lại ô 1, rồi ô 4 → 7 (ô 4 chọn câu) |
| Colab báo không có `--vsql-select` | Code trên GitHub là bản cũ; đẩy code mới lên rồi chạy lại ô 2 |
