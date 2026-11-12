# 2026-11-12
thể hiện trực quan qua notebook:
(chạy mẫu nhỏ trc: 3-5 câu)
- input,output của mỗi lần gọi llm (Ta,din,dail,vsql,vsql+)
- số lần gọi llm của các phương pháp.

### Kịch bản demo
Written for: giảng viên hướng dẫn hoặc hội đồng, trong buổi demo ngắn về luồng gọi LLM của 5 phương pháp.

# Kịch bản demo: luồng gọi LLM của 5 phương pháp

**Câu hỏi minh họa** (CSDL `superhero`, chỉ để minh họa): "Có bao nhiêu siêu anh hùng mắt xanh?"

## 1. Mở đầu (khoảng 30 giây)
- Cùng một câu hỏi, cùng một mô hình, nhiệt độ 0.
- Điều cần so sánh: mỗi phương pháp **gọi LLM mấy lần, mỗi lần nhận gì và trả về gì**.
- Theo paper, DIN-SQL bỏ bước tự sửa lỗi và DAIL-SQL bỏ bầu chọn nhiều mẫu.

## 2. Từng phương pháp: input → output mỗi lần gọi

**TA-SQL — 3 lần gọi**

| Lần | Input | Output |
|---|---|---|
| 1. TASL | Schema kèm mô tả cột và giá trị + câu hỏi + evidence | Dummy SQL, chỉ để liên kết schema |
| 2. TALOG-SR | Schema + dummy SQL + câu hỏi (7 ví dụ mẫu) | Bản suy luận từng bước |
| 3. TALOG-SQL | Bản suy luận từ lần 2 | SQL cuối |

**DIN-SQL — 3 lần gọi**

| Lần | Input | Output |
|---|---|---|
| 1. Liên kết schema | `CREATE TABLE` + 3 dòng mẫu + mô tả cột + câu hỏi | Danh sách schema link |
| 2. Phân loại | Câu hỏi + schema link | Nhãn EASY / NON-NESTED / NESTED |
| 3. Sinh SQL | Prompt theo nhãn + schema link | SQL cuối |

**DAIL-SQL — 2 lần gọi**

| Lần | Input | Output |
|---|---|---|
| 1. Vòng 1 | `CREATE TABLE` + 7 ví dụ giống câu hỏi nhất + câu hỏi | SQL nháp |
| 2. Vòng 2 | `CREATE TABLE` + 7 ví dụ chọn lại theo khung SQL của bản nháp + câu hỏi | SQL cuối |

Nếu hai prompt giống hệt nhau thì chỉ tính 1 lần gọi (hệ thống không gọi lại prompt trùng).

**V-SQL — 1 hoặc 2 lần gọi**

| Lần | Input | Output |
|---|---|---|
| 1. Giai đoạn 1 | Schema dạng view và bảng (Bảng 6 của paper) + câu hỏi | Dummy SQL viết trên view |
| 2. Giai đoạn 2 | Định nghĩa view + dummy SQL + schema bảng gốc + câu hỏi | SQL trên bảng gốc |

Nếu dummy SQL không dùng view thì bỏ lần 2.

**V-SQL+ — 2 đến 8 lần gọi**

| Lần | Input | Output |
|---|---|---|
| 0. Bầu chọn (chỉ CSDL lớn) | Cùng một prompt gửi 4 lần: 1 lần nhiệt độ 0, 3 lần nhiệt độ 0.7 | 4 dummy SQL, chọn ra tập view dùng nhiều nhất |
| 1. Dummy SQL | Schema view và bảng đã chọn + giá trị khớp với câu hỏi + câu hỏi + evidence | Dummy SQL |
| 1b. Fallback (nếu lỗi tên cột/bảng, tối đa 2 lần) | Prompt cũ + ghi chú lỗi + bảng gốc thêm vào | Dummy SQL mới |
| 2. Giai đoạn 2 | Như V-SQL | SQL trên bảng gốc |

## 3. Số lần gọi LLM

Số đo thực tế (500 câu, qwen2.5-coder:7b):

| Phương pháp | Lần gọi / câu | Token input / câu | Token output / câu |
|---|---|---|---|
| TA-SQL | 3,00 | 6.406 | 346 |
| V-SQL | 1,77 | 8.580 | 148 |
| V-SQL+ | 4,12 | 20.999 | 210 |
| DIN-SQL | 3 (cố định) | chưa đo | chưa đo |
| DAIL-SQL | 1–2 | chưa đo | chưa đo |

DIN-SQL và DAIL-SQL chưa chạy trên model thật nên chưa có số đo, số lần gọi ở trên là theo thiết kế.

**Phân tích V-SQL+ (4,12 lần):**
- Dummy SQL cuối: 1,00 lần/câu.
- Giai đoạn 2: 0,89 lần/câu.
- Bầu chọn: 2,12 lần/câu (265 câu × 4 mẫu).
- Fallback: 0,10 lần/câu.

## 4. Chốt (khoảng 30 giây)
- **Số lần gọi** không quyết định thời gian. Thời gian phụ thuộc chủ yếu vào số token sinh ra: khoảng 25 token/s khi sinh, còn đọc prompt nhanh hơn khoảng 180 lần.
- V-SQL+ đọc nhiều (gấp 3,3 lần TA-SQL) nhưng sinh ít (210 so với 346 token), nên nhanh hơn.
- Công bằng với paper: bầu chọn và fallback của V-SQL+ là hai cơ chế mà paper đã bỏ ở các phương pháp khác, nên khi so cần ghi rõ hoặc dùng bản V-SQL+ chặt hơn.

Nếu cần, mình lưu bản này thành file trong `docs/` hoặc rút còn một trang cho slide.