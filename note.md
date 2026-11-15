# Kịch bản demo (cập nhật 15/11/2026)

> **Trọng tâm:** tái hiện V-SQL → cải tiến V-SQL+ → đánh giá bằng cách so sánh DAIL-SQL, V-SQL, V-SQL+. Luồng gọi LLM (prompt, câu
> trả lời, số lần gọi, token) chỉ là một phần thông tin minh hoạ ở bước đánh giá. TA-SQL và DIN-SQL đã bị gỡ khỏi mã nguồn.

- Notebook: [notebooks/Demo_VSQL_VSQLplus.ipynb](notebooks/Demo_VSQL_VSQLplus.ipynb).
- Hướng dẫn chạy và lời thoại quay video: [docs/HUONG_DAN_DEMO_VIDEO.md](docs/HUONG_DAN_DEMO_VIDEO.md).
- Phân tích đầy đủ: [docs/NHAN_XET_KET_QUA_GPT4OMINI.md](docs/NHAN_XET_KET_QUA_GPT4OMINI.md).

Written for: giảng viên hướng dẫn hoặc hội đồng, trong buổi demo **3 phút**.

## Cấu trúc notebook

| Phần | Ô | Việc | Thời gian |
|---|---|---|---|
| **Chuẩn bị** (chạy trước, không quay) | A | Chọn model | — |
| | B | Mã nguồn, thư viện, dữ liệu. Colab tải gói dữ liệu demo 266 MB từ GitHub Release | Máy: 2 giây. Colab: khoảng 1 phút |
| | C | Dựng view, chỉ mục giá trị; nạp tập ví dụ DAIL-SQL (đã xử lý sẵn, không tính lại); chạy sẵn 10 câu × 4 phương pháp | Máy: khoảng 20 giây. Colab: khoảng 1–1,5 phút |
| | D | Hàm hiển thị | Tức thì |
| **Demo** (quay) | 1, 2 | View V-SQL so với Hình 3; view tự động và liên kết giá trị của V-SQL+ | Tức thì |
| | 3 | Chạy các phương pháp; tuỳ chọn số câu (1–10) và phương pháp nằm ở ô này | Khoảng 1 giây, chạy lại thoải mái |
| | 4 | Luồng gọi LLM của một câu (chọn uid) | Tức thì |
| | 5 | Số lần gọi LLM, token, chi phí | Tức thì |
| | 6 | Kết quả 500 câu | Tức thì |

DAIL-SQL không train. Phần lâu của nó là xử lý trước 9.428 câu train (che tên schema + embedding, khoảng 8 phút trên CPU) để chọn ví dụ
few-shot. Kết quả xử lý này nằm sẵn trong gói dữ liệu demo (`minidev/vsql_demo_pack.zip`, dựng bằng `scripts/make_demo_pack.py`, đưa lên
GitHub Release `demo-data-v1`), cùng 6 CSDL của câu demo và cache câu trả lời của 10 câu. Nhờ vậy toàn bộ notebook trên Colab chạy trong
khoảng 3–4 phút, không tính lại tập train và không gọi API.

## Các phương pháp so sánh

| Phương pháp | Vai trò | Tóm tắt |
|---|---|---|
| **DAIL-SQL** | Baseline (Bảng 3 của paper) | Schema `CREATE TABLE` + 7 ví dụ few-shot chọn từ tập train BIRD; 2 vòng; 1 mẫu, không bầu chọn |
| **V-SQL (đưa hết view)** | Tái hiện paper | View dựng theo các phép JOIN trong SQL đáp án, kiểu Hình 3; giai đoạn 1 Hình 4, giai đoạn 2 Hình 5 |
| **V-SQL (LLM chọn view)** | Tái hiện paper | Như trên, thêm 1 lần gọi LLM chọn view trước giai đoạn 1 (paper không nói cách chọn; phần tự thêm) |
| **V-SQL+ (bỏ bầu chọn)** | Cải tiến | View tự động theo khoá ngoại, chọn view bằng truy hồi, prompt mới, liên kết giá trị, sửa lỗi; giai đoạn 2 Hình 5 |

## Câu demo

10 câu cố định. Ô 3 lấy `SO_CAU` câu đầu: từ 3 câu trở lên có đủ dễ / trung bình / khó; 10 câu theo đúng tỷ lệ bộ dữ liệu (3 / 5 / 2).
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

## Kịch bản 3 phút

| Thời gian | Ô | Nội dung chính |
|---|---|---|
| 0:00–0:15 | đầu notebook | Mục tiêu: tái hiện V-SQL, cải tiến V-SQL+, so với DAIL-SQL; cùng gpt-4o-mini, 500 câu BIRD mini-dev |
| 0:15–0:50 | 1 | Ý tưởng view → 2 giai đoạn. View dựng theo JOIN đáp án, `v_superhero` trùng 12 cột Hình 3; 10 bảng → 3 view; prompt Hình 4, 5 nguyên văn |
| 0:50–1:25 | 2 | V-SQL+: view tự động theo khoá ngoại, chọn view bằng truy hồi, prompt SQLite, liên kết giá trị `'Human'`; prompt mới +8 điểm |
| 1:25–2:25 | 3, 4, 5 | Chạy 3 câu (1 giây). Câu 259: DAIL đoán sai cột, V-SQL dùng view rồi khôi phục JOIN, V-SQL+ có giá trị khớp. Biểu đồ số lần gọi LLM |
| 2:25–2:50 | 6 | 500 câu: DAIL-SQL 50,0 · V-SQL 46,0 / 46,8 · V-SQL+ 52,6. V-SQL+ gần như hết lỗi thực thi ở giai đoạn 1 |
| 2:50–3:00 | Kết luận | V-SQL theo paper chưa vượt DAIL-SQL; V-SQL+ cao nhất, chi phí gần DAIL-SQL; hướng tiếp: thêm few-shot |
