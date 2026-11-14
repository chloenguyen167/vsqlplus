# Hướng dẫn chạy notebook demo và lời thoại quay video

Notebook: `notebooks/Demo_VSQL_VSQLplus.ipynb`. Kịch bản: `note.md`. Video dài khoảng **7 phút**, gồm: tái hiện V-SQL → cải tiến
V-SQL+ → đánh giá so sánh DAIL-SQL, V-SQL, V-SQL+.

## 1. Cài đặt (làm một lần)

### Cách A: chạy trên máy (khuyên dùng, không tốn tiền)

Máy đã có kết quả 500 câu ở `results_new/cmp_gpt-4o-mini_d2025`. Với model `gpt-4o-mini`, notebook dùng lại cache câu trả lời từ đó, nên
**không gọi API, không tốn tiền, chạy trong vài giây**.

```bash
cd ~/proj/vsql-plus
.venv/bin/pip install jupyter matplotlib pandas
.venv/bin/jupyter notebook notebooks/Demo_VSQL_VSQLplus.ipynb
```

Phải mở Jupyter bằng `.venv` của repo: môi trường này có spaCy `en_core_web_sm`, DAIL-SQL cần nó để chọn đúng ví dụ như lần chạy 500 câu.

### Cách B: chạy trên Colab

1. Đẩy code lên GitHub trước, vì notebook tự `git clone` repo.
2. Mở notebook trên Colab, thêm secret `OPENAI_API_KEY` (biểu tượng chìa khoá ở thanh bên trái, bật "Notebook access").
3. Colab không có cache 500 câu nên gọi API thật: khoảng 0,005 USD mỗi câu cho cả 4 phương pháp (gpt-4o-mini). Lần đầu mất 3–5 phút tải
   dữ liệu.

## 2. Ba tuỳ chọn ở ô 1

| Tuỳ chọn | Giá trị cho video | Ý nghĩa |
|---|---|---|
| `SO_CAU` | `3` | 1–10 câu, lấy theo danh sách cố định trong `note.md`. Từ 3 câu trở lên có đủ dễ / trung bình / khó; 10 câu = 3 / 5 / 2 như bộ dữ liệu |
| Phương pháp | bật cả 4 | DAIL-SQL, V-SQL (đưa hết view), V-SQL (LLM chọn view), V-SQL+ (bỏ bầu chọn) |
| `MODEL` | `gpt-4o-mini` | Model khác (vd `gpt-4.1-mini`) sẽ gọi API thật; tên có dấu `:` (vd `qwen2.5-coder:7b`) chạy qua Ollama, nên dùng trên Colab T4 |

Muốn video ngắn hơn: `SO_CAU = 3`. Muốn cho xem cả câu V-SQL / V-SQL+ thua DAIL-SQL: `SO_CAU = 10`.

## 3. Trước khi bấm quay

1. Chạy ô 1 → 3 (Chuẩn bị) và ô 6 (Chạy) **trước**, để khi quay không phải chờ.
2. Chạy thử ô 4, 5, 7, 8, 9 một lần để kiểm tra hiển thị, rồi thu gọn các dòng có thể bấm mở (prompt, "Lần 1, Lần 2...").
3. Phóng to chữ trình duyệt (Cmd + `+`) lên khoảng 125%; đóng các tab, thông báo không liên quan.
4. Mở file này ở cửa sổ khác để đọc lời thoại.

## 4. Lời thoại theo từng cảnh

Phần trong ngoặc vuông là thao tác trên màn hình. Lời thoại viết sẵn để đọc.

### Cảnh 1. Mở đầu (30 giây)

[Ô markdown đầu notebook.]

> Xin chào. Video này trình bày ba việc nhóm đã làm: tái hiện phương pháp V-SQL, đề xuất bản cải tiến V-SQL+, và đánh giá cả hai so với
> DAIL-SQL, một baseline trong paper.
>
> Bộ dữ liệu là BIRD mini-dev, 500 câu hỏi trên 11 cơ sở dữ liệu. Mọi phương pháp dùng cùng một model là gpt-4o-mini, nhiệt độ 0.

### Cảnh 2. Tái hiện V-SQL (1 phút 30 giây)

[Cuộn tới "Phần 1. Tái hiện V-SQL", chỉ vào phần ý tưởng.]

> Ý tưởng của V-SQL: cơ sở dữ liệu có nhiều khoá ngoại khiến LLM dễ JOIN sai và đoán sai tên cột. V-SQL gộp các bảng liên quan thành view,
> tức bảng ảo. Giai đoạn một, LLM viết SQL trên view, nên gần như không cần JOIN. Giai đoạn hai, LLM viết lại câu SQL đó về bảng gốc.

[Chạy ô 4. Chỉ vào dòng "10 bảng → 3 view", rồi định nghĩa `v_superhero`.]

> Paper tự thiết kế view bằng tay dựa trên các phép JOIN trong SQL đáp án, nhưng không công bố bộ view đó. Nhóm dựng view tự động theo
> cùng nguyên tắc. Ở cơ sở dữ liệu superhero, 10 bảng được gộp còn 3 view. View v_superhero do chương trình dựng trùng đủ 12 cột, đúng thứ
> tự với Hình 3 trong paper.

[Chỉ vào bảng số view trên 11 CSDL, rồi bấm mở hai prompt Hình 4, Hình 5.]

> Cả 11 cơ sở dữ liệu có tổng cộng 46 view, view nào cũng giữ đúng số dòng của bảng gốc. Hai prompt giai đoạn một và hai giữ nguyên từng
> chữ như Hình 4 và Hình 5. Paper không nói cách chọn view nào đưa vào prompt, nên nhóm làm hai bản: đưa hết view, và để LLM chọn view
> trước.

### Cảnh 3. Cải tiến V-SQL+ (1 phút 30 giây)

[Cuộn tới "Phần 2", chỉ vào bảng so sánh V-SQL và V-SQL+.]

> V-SQL+ giữ khung hai giai đoạn của paper và cải tiến theo hai hướng. Hướng một: view được tạo tự động từ khoá ngoại, không cần nhìn
> SQL đáp án. Hướng hai: chọn view bằng truy hồi, không tốn thêm lần gọi LLM. Ngoài ra có prompt mới ghi rõ phải viết SQLite, liên kết giá
> trị, và tự sửa khi sai tên cột.

[Chạy ô 5. Chỉ vào các chú thích `via` trong view tự động, rồi ví dụ `'Human'`.]

> Đây là view v_superhero tự động. Mỗi cột có chú thích lấy từ bảng nào, mô tả và giá trị mẫu. Còn đây là liên kết giá trị: câu hỏi nói
> "human", chương trình tìm trong cơ sở dữ liệu và thấy giá trị thật là "Human" viết hoa, rồi đưa vào prompt để LLM viết đúng.

[Chỉ vào bảng đóng góp.]

> Đo trên 500 câu, prompt mới đóng góp nhiều nhất, tám điểm, liên kết giá trị thêm hơn bốn điểm. Bầu chọn nhiều mẫu không giúp gì mà tốn
> gấp ba lần, nên bản dùng để so sánh bỏ bầu chọn.

### Cảnh 4. Đánh giá trên câu demo (2 phút 30 giây)

[Cuộn tới "Phần 3", kết quả ô 6, rồi bảng ✅/❌ ở ô 7.]

> Bây giờ chạy bốn phương pháp trên các câu demo, có đủ câu dễ, trung bình và khó. Mỗi câu SQL dự đoán được chạy trên cơ sở dữ liệu và so
> với kết quả của SQL đáp án.

[Cuộn tới chi tiết câu 259. Mở "Lần 1" của DAIL-SQL, cuộn qua 7 ví dụ tới câu trả lời.]

> Câu 259: phần trăm siêu anh hùng có alignment là 'Bad', và bao nhiêu trong số đó do Marvel xuất bản. DAIL-SQL đưa bảy ví dụ từ tập train
> và schema dạng CREATE TABLE. Mô hình viết superhero.alignment, nhưng bảng chỉ có alignment_id, nên lỗi.

[Mở "Lần 1" và "Lần 2" của V-SQL.]

> V-SQL đưa view v_superhero, đã có sẵn cột alignment và tên nhà xuất bản. SQL giai đoạn một không cần JOIN. Giai đoạn hai viết lại về
> bảng gốc, tự thêm hai phép JOIN, và ra kết quả đúng.

[Mở "Lần 1" của V-SQL+, cuộn tới `# matched database values`.]

> V-SQL+ cũng đúng. Prompt có thêm mục giá trị khớp câu hỏi: 'Bad' và 'Marvel Comics' là giá trị thật của cột nào.

[Cuộn tới câu 330, chỉ vào SQL cuối của V-SQL và V-SQL+.]

> Câu 330 cho thấy một điểm yếu của prompt trong paper: Hình 4 không nói phải viết SQLite, nên V-SQL dùng hàm DIVIDE, vốn không có trong
> SQLite. Prompt của V-SQL+ ghi rõ SQLite nên viết đúng.

[Cuộn tới ô 8, biểu đồ số lần gọi và bảng token.]

> Về chi phí: DAIL-SQL gọi một đến hai lần. V-SQL gọi hai lần, bản chọn view gọi ba lần. V-SQL+ gọi một lần, thêm giai đoạn hai khi có dùng
> view. Bảng bên trên cho biết token và chi phí mỗi câu.

Nếu `SO_CAU = 10`, thêm (30 giây):

[Cuộn tới câu 265 và 50.]

> Để công bằng, đây là những câu V-SQL thua DAIL-SQL. Câu 265: giai đoạn một đúng, nhưng prompt Hình 5 viết lại sai điều kiện màu mắt.
> Câu 50: tên sự kiện có dấu nháy đơn; DAIL-SQL học cách viết từ ví dụ, còn V-SQL không có ví dụ nên lỗi cú pháp.

### Cảnh 5. Kết quả trên 500 câu (1 phút)

[Cuộn tới "Phần 4", chạy ô 9. Chỉ vào bảng rồi biểu đồ bên trái.]

> Vài câu demo không đủ để kết luận, nên đây là kết quả trên đủ 500 câu. DAIL-SQL đạt 50 phần trăm. V-SQL tái hiện đạt 46 đến 47 phần
> trăm, thấp hơn khoảng ba điểm. V-SQL+ đạt 52,6, cao nhất. Các khác biệt so với DAIL-SQL đều không có ý nghĩa thống kê.

[Chỉ vào biểu đồ bên phải.]

> Biểu đồ này phân tích câu SQL ở giai đoạn một. V-SQL+ gần như không còn lỗi thực thi như sai tên cột hay dùng hàm sai. Nhưng số câu chạy
> được mà sai kết quả vẫn nhiều hơn DAIL-SQL, vì DAIL-SQL có bảy ví dụ mẫu.

### Cảnh 6. Kết luận (30 giây)

[Cuộn tới "Kết luận".]

> Tóm lại: view của V-SQL giúp ở những câu nhiều khoá ngoại, đúng như paper nói. Nhưng bản tái hiện theo paper chưa vượt được DAIL-SQL
> trên 500 câu; một lý do là paper thiết kế view bằng tay và không công bố. V-SQL+ đạt kết quả cao nhất với chi phí chỉ hơn DAIL-SQL một
> chút. Hướng tiếp theo là thêm ví dụ few-shot cho V-SQL+. Cảm ơn mọi người đã theo dõi.

## 5. Sự cố thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `CẢNH BÁO: thiếu spaCy en_core_web_sm` | Đang chạy bằng python hệ thống; mở Jupyter bằng `.venv/bin/jupyter` |
| `CHƯA CÓ OPENAI_API_KEY` | Không sao với `gpt-4o-mini` trên máy (dùng cache). Model khác hoặc Colab thì cần key |
| Ô 6 chạy lâu ở câu đầu | Lần đầu DAIL-SQL nạp mô hình embedding và tập train, khoảng 5–10 giây |
| Đổi tuỳ chọn mà kết quả không đổi | Chạy lại ô 1 rồi ô 3 → 9 |
| Colab báo lỗi `--vsql-select` | Code trên GitHub là bản cũ; đẩy code mới lên rồi chạy lại ô 2 |
