# Kịch bản demo (cập nhật 14/11/2026)

> **Trọng tâm:** tái hiện V-SQL → cải tiến V-SQL+ → đánh giá bằng cách so sánh DAIL-SQL, V-SQL, V-SQL+. Luồng gọi LLM (prompt, câu
> trả lời, số lần gọi, token) chỉ là một phần thông tin minh hoạ ở bước đánh giá. TA-SQL và DIN-SQL đã bị gỡ khỏi mã nguồn.

- Notebook: [notebooks/Demo_VSQL_VSQLplus.ipynb](notebooks/Demo_VSQL_VSQLplus.ipynb). Chỉ có 3 tuỳ chọn: số câu (1–10), phương pháp,
  model.
- Hướng dẫn chạy và lời thoại quay video: [docs/HUONG_DAN_DEMO_VIDEO.md](docs/HUONG_DAN_DEMO_VIDEO.md).
- Phân tích đầy đủ: [docs/NHAN_XET_KET_QUA_GPT4OMINI.md](docs/NHAN_XET_KET_QUA_GPT4OMINI.md).

Written for: giảng viên hướng dẫn hoặc hội đồng, trong buổi demo khoảng 7 phút.

## Các phương pháp so sánh

| Phương pháp | Vai trò | Tóm tắt |
|---|---|---|
| **DAIL-SQL** | Baseline (Bảng 3 của paper) | Schema `CREATE TABLE` + 7 ví dụ few-shot chọn từ tập train BIRD; 2 vòng; 1 mẫu, không bầu chọn |
| **V-SQL (đưa hết view)** | Tái hiện paper | View dựng theo các phép JOIN trong SQL đáp án, kiểu Hình 3; giai đoạn 1 Hình 4, giai đoạn 2 Hình 5 |
| **V-SQL (LLM chọn view)** | Tái hiện paper | Như trên, thêm 1 lần gọi LLM chọn view trước giai đoạn 1 (paper không nói cách chọn; phần tự thêm) |
| **V-SQL+ (bỏ bầu chọn)** | Cải tiến | View tự động theo khoá ngoại, chọn view bằng truy hồi, prompt mới, liên kết giá trị, sửa lỗi; giai đoạn 2 Hình 5 |

## Câu demo

10 câu cố định. Notebook lấy `SO_CAU` câu đầu: từ 3 câu trở lên có đủ dễ / trung bình / khó; 10 câu theo đúng tỷ lệ bộ dữ liệu (3 / 5 / 2).
Bộ câu gồm cả câu V-SQL thắng, câu V-SQL+ sửa được lỗi của V-SQL, và câu V-SQL / V-SQL+ thua DAIL-SQL, để đánh giá trung thực.

| # | uid | CSDL | Độ khó | DAIL | V-SQL hết view | V-SQL chọn view | V-SQL+ | Điểm minh hoạ |
|---|---|---|---|---|---|---|---|---|
| 1 | 259 | superhero | khó | ❌ | ✅ | ✅ | ✅ | View `v_superhero` (đúng Hình 3) có sẵn `alignment`, `publisher_name`, không cần JOIN; DAIL đoán cột `superhero.alignment` |
| 2 | 330 | codebase_community | TB | ✅ | ❌ | ❌ | ✅ | Hình 4 không nhắc SQLite nên V-SQL chép hàm `DIVIDE`, `YEAR` từ evidence; prompt V-SQL+ ghi rõ SQLite |
| 3 | 261 | superhero | dễ | ✅ | ❌ | ❌ | ✅ | D′ của V-SQL ẩn bảng tra cứu `publisher` nên không lấy được `publisher.id`; V-SQL+ vẫn giữ bảng này |
| 4 | 380 | card_games | TB | ❌ | ✅ | ✅ | ✅ | DAIL nối sai khoá `cards.uuid = setCode`; V-SQL nối đúng theo `setCode` |
| 5 | 427 | toxicology | dễ | ❌ | ✅ | ✅ | ✅ | DAIL lấy `atom_id` từ nhầm bảng; V-SQL dùng `v_connected` và `v_bond` |
| 6 | 266 | superhero | TB | ❌ | ❌ | ❌ | ✅ | Liên kết giá trị: CSDL ghi `'Human'`; DAIL và V-SQL viết `'human'` nên ra rỗng |
| 7 | 421 | toxicology | khó | ❌ | ✅ | ✅ | ✅ | DAIL JOIN thừa `molecule`, lấy `element` từ nhầm bảng; `v_atom` không cần JOIN |
| 8 | 265 | superhero | TB | ✅ | ❌ | ❌ | ❌ | Giai đoạn 1 của V-SQL, V-SQL+ đúng, nhưng Hình 5 viết lại `eye_colour = 'No Colour'` thành `eye_colour_id IS NULL` |
| 9 | 50 | student_club | dễ | ✅ | ❌ | ❌ | ❌ | Phải viết `'Women''s Soccer'`; DAIL học từ ví dụ, V-SQL và V-SQL+ (zero-shot) lỗi cú pháp |
| 10 | 85 | thrombosis_prediction | TB | ✅ | ✅ | ✅ | ❌ | V-SQL+ đếm trên `v_Examination` (mỗi lần khám một dòng) thay vì bảng `Patient` |

Với 10 câu: DAIL-SQL đúng 5, V-SQL đúng 5, V-SQL+ đúng 7 (gpt-4o-mini).

## Kịch bản (khoảng 7 phút)

### 0. Mở đầu (30 giây)
- Mục tiêu: tái hiện V-SQL trên BIRD mini-dev, đề xuất V-SQL+, đánh giá so với DAIL-SQL.
- Cùng model gpt-4o-mini, nhiệt độ 0, cùng 500 câu.

### 1. Tái hiện V-SQL (1 phút 30 giây) — notebook ô 4
- Ý tưởng paper: gộp bảng thành view → giai đoạn 1 viết SQL trên view (ít JOIN) → giai đoạn 2 viết lại về bảng gốc.
- Cách tái hiện: view dựng tự động theo các phép JOIN trong SQL đáp án, kiểu Hình 3. Cho xem `v_superhero` trùng đủ 12 cột Hình 3.
- CSDL superhero: 10 bảng → D′ còn 3 view. Bảng số view trên 11 CSDL.
- Prompt Hình 4, Hình 5 giữ nguyên từng chữ. Phần tự thêm: bước LLM chọn view.

### 2. Cải tiến V-SQL+ (1 phút 30 giây) — notebook ô 5
- Hai hướng: view tự động theo khoá ngoại (không nhìn đáp án), chọn view bằng truy hồi.
- Thêm: prompt mới (ghi rõ SQLite), liên kết giá trị, sửa lỗi tên cột.
- Cho xem `v_superhero` tự động (có chú thích nguồn gốc cột) và ví dụ liên kết giá trị `'Human'`.
- Bảng đóng góp: prompt mới +8,0 điểm, liên kết giá trị +4,2 điểm; bầu chọn không giúp gì nên bỏ.

### 3. Đánh giá trên câu demo (2 phút 30 giây) — notebook ô 6, 7, 8
- Bảng ✅/❌ của các câu demo.
- Câu 259: mở prompt và câu trả lời của DAIL-SQL (đoán cột sai), V-SQL (dummy SQL trên view, giai đoạn 2 khôi phục JOIN), V-SQL+ (giá trị khớp).
- Câu 330 hoặc 261: V-SQL+ sửa được lỗi của V-SQL.
- Biểu đồ số lần gọi LLM và bảng token, chi phí.

### 4. Kết quả 500 câu (1 phút) — notebook ô 9
- DAIL-SQL 50,0 · V-SQL 46,0 / 46,8 · V-SQL+ 52,6. Khác biệt với DAIL-SQL không có ý nghĩa thống kê.
- Biểu đồ giai đoạn 1: V-SQL+ gần như hết lỗi thực thi, nhưng vẫn nhiều câu "chạy được nhưng sai" hơn DAIL-SQL.

### 5. Kết luận (30 giây)
- View giúp ở câu nhiều khoá ngoại, nhưng V-SQL theo paper chưa vượt DAIL-SQL trên 500 câu.
- V-SQL+ cao nhất, chi phí chỉ hơn DAIL-SQL một chút. Hướng tiếp theo: thêm few-shot.
