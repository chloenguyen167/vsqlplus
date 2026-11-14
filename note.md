# 2026-11-12 (cập nhật 14/11)

> **Ghi chú (14/11):** demo chỉ so sánh 3 phương pháp: DAIL-SQL, V-SQL (2 cách đưa view: đưa hết view / LLM chọn view) và V-SQL+
> (bản bỏ bầu chọn nhiều mẫu). TA-SQL và DIN-SQL đã bị gỡ khỏi mã nguồn.

Thể hiện trực quan qua notebook [notebooks/Demo_LuongGoiLLM_3PP.ipynb](notebooks/Demo_LuongGoiLLM_3PP.ipynb):
- mặc định chạy các câu minh hoạ dưới đây (`CACH_CHON = "kich_ban"`, `SO_CAU = 3`). `SO_CAU` chọn tự do từ 1 đến 500; muốn câu
  ngẫu nhiên giữ tỷ lệ dễ / trung bình / khó thì dùng `ngau_nhien_theo_do_kho`, muốn câu cụ thể thì dùng `theo_uid` + `UIDS`;
- hướng dẫn chạy và lời thoại quay video: [docs/HUONG_DAN_DEMO_VIDEO.md](docs/HUONG_DAN_DEMO_VIDEO.md);
- input, output của mỗi lần gọi LLM (DAIL-SQL, V-SQL đưa hết view, V-SQL LLM chọn view, V-SQL+ bỏ bầu chọn);
- số lần gọi LLM của các phương pháp, chia theo giai đoạn.

### Kịch bản demo
Written for: giảng viên hướng dẫn hoặc hội đồng, trong buổi demo ngắn về luồng gọi LLM của 3 phương pháp.

# Kịch bản demo: luồng gọi LLM của DAIL-SQL, V-SQL, V-SQL+

**Câu hỏi minh hoạ:** chọn trong 39 câu mà **cả hai bản V-SQL đều đúng còn DAIL-SQL sai**. 28 câu trong số đó V-SQL+ cũng đúng. Các câu
dưới đây cho thấy đúng điều paper muốn chứng minh: DAIL-SQL sai vì tự JOIN hoặc đoán tên cột, còn V-SQL hỏi thẳng trên view.

| Thứ tự | uid | CSDL | Câu hỏi | DAIL-SQL sai vì | V-SQL đúng nhờ |
|---|---|---|---|---|---|
| 1 (chính) | 259 | superhero | "What is the percentage of superheroes who act in their own self-interest or make decisions based on their own moral code? Indicate how many of the said superheroes were published by Marvel Comics." | Viết `T1.alignment` trên bảng `superhero` (chỉ có `alignment_id`) → lỗi `no such column` | `v_superhero`, đúng view Hình 3 của paper, có sẵn `alignment` và `publisher_name`: dummy SQL không JOIN; giai đoạn 2 khôi phục đúng `JOIN publisher`, `JOIN alignment` |
| 2 | 421 | toxicology | "List all the elements of the toxicology of the molecule "TR004"." | JOIN thừa `molecule` với `atom` rồi lấy `element` từ nhầm bảng → lỗi `no such column` | `v_atom` có sẵn `molecule_id`: `SELECT element FROM v_atom WHERE molecule_id = 'TR004'` |
| 3 | 380 | card_games | "Among the cards in the set "Hauptset Zehnte Edition", how many of them are designed by Adam Rex?" | JOIN sai khoá `cards.uuid = set_translations.setCode` → chạy được nhưng sai kết quả | Nối đúng `cards.setCode = v_set_translations.setCode` |
| 4 (dự phòng) | 470 | financial | "How many male customers who are living in North Bohemia have average salary greater than 8000?" | Viết `'North Bohemia'`, sai hoa thường so với dữ liệu `'north Bohemia'` | `v_client` có sẵn `A3`, `A11` của `district`, giá trị mẫu cho thấy đúng cách viết |
| 5 (dự phòng) | 427 | toxicology | "What are the atoms of the triple bond with the molecule "TR041"?" | Nối `atom` hai lần và lấy `atom_id` từ nhầm bảng → lỗi `no such column` | `v_connected` + `v_bond`: chỉ 1 JOIN giữa hai view |

Ở cả 5 câu, V-SQL+ (bỏ bầu chọn) cũng đúng.

**Lưu ý trung thực:** các câu này được chọn để minh hoạ điểm mạnh của view. Trên đủ 500 câu, V-SQL vẫn thua DAIL-SQL (DAIL đúng riêng 67
câu, V-SQL đúng riêng 51 câu); cần nói rõ điều này ở phần chốt.

## 1. Mở đầu (khoảng 30 giây)
- Cùng một câu hỏi, cùng một mô hình (gpt-4o-mini), nhiệt độ 0.
- Điều cần so sánh: mỗi phương pháp **gọi LLM mấy lần, mỗi lần nhận gì và trả về gì**.
- Theo paper, DAIL-SQL chạy 1 mẫu, không bầu chọn. Để công bằng, V-SQL+ trong demo cũng dùng bản bỏ bầu chọn.

## 2. Từng phương pháp: input → output mỗi lần gọi

**DAIL-SQL — 1 đến 2 lần gọi**

| Lần | Input | Output |
|---|---|---|
| 1. Vòng 1 | `CREATE TABLE` của mọi bảng + 7 ví dụ train BIRD giống câu hỏi nhất + câu hỏi | SQL nháp |
| 2. Vòng 2 | `CREATE TABLE` + 7 ví dụ chọn lại theo khung SQL của bản nháp + câu hỏi | SQL cuối |

Nếu hai prompt giống hệt nhau (cùng 7 ví dụ) thì chỉ tính 1 lần gọi; hệ thống không gọi lại prompt trùng.

**V-SQL, đưa hết view — 2 lần gọi**

| Lần | Input | Output |
|---|---|---|
| 1. Giai đoạn 1 (Hình 4) | Mọi view của D′ (view dựng theo JOIN của SQL đáp án) và các bảng không bị view thay thế, trình bày kiểu Bảng 6 + câu hỏi + evidence | Dummy SQL viết trên view |
| 2. Giai đoạn 2 (Hình 5) | Định nghĩa view mà dummy SQL dùng + dummy SQL + schema các bảng gốc liên quan + câu hỏi | SQL trên bảng gốc |

Giai đoạn 2 luôn chạy, như paper.

**V-SQL, LLM chọn view — 3 lần gọi**

| Lần | Input | Output |
|---|---|---|
| 0. Chọn view/bảng | Danh mục D′ (mỗi view/bảng một dòng: tên + cột) + câu hỏi + evidence | Tên các view/bảng cần dùng |
| 1. Giai đoạn 1 (Hình 4) | Như trên, nhưng chỉ các view/bảng đã chọn | Dummy SQL viết trên view |
| 2. Giai đoạn 2 (Hình 5) | Như trên | SQL trên bảng gốc |

Lần 0 là phần tự thêm: paper chỉ nói schema ở Hình 4 là "related to the query, retrieved", không nói cách chọn. Nếu câu trả lời
không khớp tên nào thì đưa hết D′.

**V-SQL+, bỏ bầu chọn — 1 đến 4 lần gọi**

| Lần | Input | Output |
|---|---|---|
| 1. Giai đoạn 1 (prompt V-SQL+) | View tự động (theo khoá ngoại) và bảng, chọn bằng truy hồi BM25 không cần LLM (CSDL nhỏ: đưa hết) + giá trị trong CSDL khớp câu hỏi + câu hỏi + evidence | Dummy SQL |
| 1b. Sửa lỗi (nếu lỗi tên cột/bảng, tối đa 2 lần) | Prompt cũ + ghi chú lỗi (cột đó thật sự nằm ở đâu) + bảng gốc thêm vào | Dummy SQL mới |
| 2. Giai đoạn 2 (Hình 5) | Như V-SQL | SQL trên bảng gốc |

Nếu dummy SQL không dùng view thì bỏ giai đoạn 2.

## 3. Số lần gọi LLM

Số đo thực tế (500 câu, gpt-4o-mini, `results_new/cmp_gpt-4o-mini_d2025`):

| Phương pháp | EX (%) | Lần gọi / câu | Token vào / câu | Token ra / câu | USD / 500 câu |
|---|---|---|---|---|---|
| DAIL-SQL | 50.0 | 1.75 | 2,946 | 479 | 0.36 |
| V-SQL, đưa hết view | 46.0 | 2.00 | 14,412 | 129 | 1.12 |
| V-SQL, LLM chọn view | 46.8 | 3.00 | 8,219 | 142 | 0.66 |
| V-SQL+, bỏ bầu chọn | 52.6 | 1.93 | 5,984 | 105 | 0.48 |

**Chi tiết số lần gọi:**
- DAIL-SQL: 124/500 câu chỉ gọi 1 lần (prompt vòng 2 trùng vòng 1).
- V-SQL+, bỏ bầu chọn (1.93 lần):
  - giai đoạn 1: 1.00 lần/câu;
  - sửa lỗi: 0.05 lần/câu;
  - giai đoạn 2: 0.88 lần/câu (12% số câu có dummy SQL không dùng view nên bỏ qua giai đoạn 2).

## 4. Chốt (khoảng 30 giây)
- **View giúp đúng chỗ paper nói** (các câu demo: không cần JOIN, không đoán tên cột). Nhưng trên đủ 500 câu, V-SQL vẫn thua DAIL-SQL 3,2
  điểm (46,8 so với 50,0, p = 0,17, không có ý nghĩa thống kê). Lý do chính: prompt Hình 4 zero-shot và không nhắc SQLite; DAIL-SQL có
  7 ví dụ.
- **Số lần gọi không quyết định chi phí.**
  - V-SQL đưa hết view chỉ gọi 2 lần nhưng đắt nhất, vì prompt dài nhất (14k token).
  - Thêm 1 lần gọi để LLM chọn view làm prompt ngắn đi khoảng 43% và rẻ hơn, nhưng độ chính xác chỉ hơn 0.8 điểm.
- **DAIL-SQL đọc ít nhất nhưng viết nhiều nhất** (479 token ra mỗi câu): mô hình viết tiếp sau `SELECT ` và thường giải thích thêm.
- **V-SQL+ (bỏ bầu chọn) đúng nhất, chi phí chỉ hơn DAIL-SQL một chút** (0.48 so với 0.36 USD / 500 câu). Nó thắng DAIL nhờ gần như không có lỗi thực thi (sai tên cột, hàm ngoài SQLite), dù
  vẫn hiểu câu hỏi kém DAIL. Phân tích chi tiết: [docs/NHAN_XET_KET_QUA_GPT4OMINI.md](docs/NHAN_XET_KET_QUA_GPT4OMINI.md), mục 3.
- **Công bằng với paper:** bước LLM chọn view của V-SQL là phần tự thêm. Bầu chọn của V-SQL+ đã bị bỏ trong demo để cùng điều kiện
  1 mẫu với DAIL-SQL.
