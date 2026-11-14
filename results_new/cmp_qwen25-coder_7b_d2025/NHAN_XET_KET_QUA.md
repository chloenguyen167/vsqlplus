# Nhận xét kết quả: qwen2.5-coder:7b (500 câu, BIRD mini-dev bản 2025-07-04)

Kết quả trong thư mục này (`summary.md`, `predictions_*.jsonl`), chạy trên Colab T4. So với các lần chạy trước, xem
`docs/NHAN_XET_KET_QUA_QWEN35.md` (qwen3.5:0.8b và 4b).

---

## Tóm tắt nhanh

- **TA-SQL 44,6% ≈ V-SQL+ 43,0% > V-SQL (`vsql_fair`) 35,4%.**
  - V-SQL+ và TA-SQL **không khác nhau có ý nghĩa thống kê** (p = 0,56).
  - V-SQL+ hơn V-SQL rõ rệt (+7,6 điểm, p = 0,001).
- Đây là lần đầu **V-SQL+ ngang TA-SQL**. Với qwen3.5:4b, V-SQL+ còn thua TA-SQL 8,6 điểm.
- **Nếu chỉ chấm câu SQL nháp viết trên view (giai đoạn 1), V-SQL+ đúng 251/500, cao hơn TA-SQL (223/500) có ý nghĩa thống kê**
  (p = 0,02). Giai đoạn 2 của paper (LLM viết lại SQL nháp về bảng gốc) vẫn làm mất ròng 36 câu, nên kết quả cuối chỉ còn ngang.
- **V-SQL (`vsql_fair`) vẫn thua TA-SQL** (−9,2 điểm). Một phần nguyên nhân là lỗi thiết kế của chính `vsql_fair` (mục 4).
- Mức điểm tương đương bảng của paper với GPT-3.5-turbo: TA-SQL 43,8%, V-SQL 45,4%.

---

## 1. Thiết lập

| Mục | Giá trị |
|---|---|
| Model | `qwen2.5-coder:7b` (Ollama), nhiệt độ 0, tối đa 800 token mỗi câu trả lời |
| Dữ liệu | BIRD mini-dev bản 2025-07-04: 500 câu khác nhau, 11 CSDL; độ khó 148 dễ / 250 trung bình / 102 khó |
| Embedding (V-SQL+) | `nomic-embed-text` |
| Phương pháp | `tasql`, `vsql_fair`, `vsqlplus`. **Chưa chạy** `vsql`, `vsql_paper`, `vsqlplus_fig4` |
| Lỗi gọi LLM | 0 câu |

> **Thuật ngữ**
> - **EX**: tỉ lệ câu mà kết quả chạy SQL của mô hình trùng với kết quả của SQL đáp án.
> - **Giai đoạn 1 / SQL nháp**: câu SQL viết trên các view. **Giai đoạn 2**: LLM viết lại câu SQL nháp thành SQL trên bảng gốc
>   (prompt Hình 5 của paper).
> - **Chấm giai đoạn 1**: thay mỗi view trong SQL nháp bằng chính định nghĩa của nó (không gọi LLM) rồi chạy. Cách này giữ đúng
>   nghĩa câu SQL nháp, nên cho biết mô hình viết SQL trên view tốt đến đâu.
> - **p (McNemar)**: so hai phương pháp trên cùng các câu; p < 0,05 là khác biệt có ý nghĩa thống kê.

---

## 2. Kết quả chính

| Phương pháp | Dễ | Trung bình | Khó | **Tổng** | CI 95% | Lỗi sai tên bảng/cột | Lượt gọi LLM/câu | Token vào/câu | Giây LLM/câu |
|---|---|---|---|---|---|---|---|---|---|
| TA-SQL | **68,9** | 38,0 | 25,5 | **44,6** | 40,0–49,0 | 14,6% | 3,00 | 6.406 | 12,1 |
| V-SQL+ | 54,1 | **43,6** | 25,5 | **43,0** | 38,6–47,2 | 24,0% | 4,12 | 20.999 | 9,1 |
| V-SQL (`vsql_fair`) | 45,9 | 35,2 | 20,6 | **35,4** | 31,2–39,8 | 27,8% | 1,77 | 8.580 | 9,1 |

| So sánh | ΔEX | Chỉ bên trái đúng / chỉ bên phải đúng | p |
|---|---|---|---|
| V-SQL+ − TA-SQL | −1,6 | 69 / 77 | 0,56 (không khác biệt) |
| V-SQL+ − V-SQL | **+7,6** | 78 / 40 | 0,001 |
| V-SQL − TA-SQL | −9,2 | 49 / 95 | < 0,001 |

**Đọc bảng:**
- **Câu trung bình** (250 câu, nhóm lớn nhất): V-SQL+ **hơn** TA-SQL (43,6% so với 38,0%).
- **Câu khó**: V-SQL+ và TA-SQL ngang nhau (25,5%).
- **Câu dễ**: TA-SQL hơn hẳn (68,9% so với 54,1%). Đây là chỗ V-SQL+ thua điểm.
- V-SQL+ nhanh hơn TA-SQL mỗi câu (9,1 so với 12,1 giây), nhưng dùng gấp 3,3 lần token đầu vào, chủ yếu do 4 mẫu bầu chọn ở 5 CSDL lớn.

---

## 3. Tách giai đoạn 1 và giai đoạn 2

| | Số câu đúng / 500 |
|---|---|
| TA-SQL | 223 |
| V-SQL+ — giai đoạn 1 (SQL nháp trên view) | **251** |
| V-SQL+ — sau giai đoạn 2 (kết quả cuối) | 215 |
| V-SQL — giai đoạn 1 | 130 |
| V-SQL — sau giai đoạn 2 | 177 |

**V-SQL+:**
- Ở giai đoạn 1, V-SQL+ **hơn TA-SQL 28 câu** (chỉ V-SQL+ đúng 84 câu, chỉ TA-SQL đúng 56 câu; p = 0,02). Nghĩa là mô hình viết SQL trên
  view tự động, được chọn bằng truy hồi lai, **tốt hơn** TA-SQL viết trên bảng gốc. Đây là bằng chứng rõ nhất đến nay cho hai hướng
  cải tiến.
- Giai đoạn 2 làm hỏng 53 câu đang đúng và chỉ sửa được 17 câu, mất ròng 36 câu:
  - 40 câu lỗi "no such column": mô hình đổi tên view thành tên bảng nhưng không lấy cột từ bảng được nối;
  - 9 câu lỗi "ambiguous column": thêm phép nối nhưng không ghi rõ cột thuộc bảng nào;
  - 4 câu khác.

Ví dụ (CSDL `debit_card_specializing`):

```sql
-- SQL nháp (đúng): Currency đã có sẵn trong view
SELECT Currency FROM v_transactions_1k WHERE Date = '2012-08-24' AND Time = '16:25:00'
-- Sau giai đoạn 2 (sai): chỉ bỏ "v_", không nối bảng customers chứa Currency
SELECT Currency FROM transactions_1k WHERE Date = '2012-08-24' AND Time = '16:25:00'

-- SQL nháp (đúng)
SELECT SUM(Consumption) FROM v_yearmonth WHERE CustomerID = 6 AND Date BETWEEN '201308' AND '201311'
-- Sau giai đoạn 2 (sai): có nối customers nhưng để CustomerID không rõ của bảng nào -> "ambiguous column name"
SELECT SUM(Consumption) FROM yearmonth LEFT JOIN customers AS Customer ON yearmonth.CustomerID = Customer.CustomerID
WHERE CustomerID = 6 AND ...
```

**V-SQL (`vsql_fair`):** điều ngược lại xảy ra. Giai đoạn 2 **sửa được** 69 câu và chỉ làm hỏng 22, nên kết quả cuối (177) cao hơn
giai đoạn 1 (130). Lý do ở mục 4.

---

## 4. Lỗi thiết kế của `vsql_fair`

`vsql_fair` dùng view kiểu Hình 3: **bỏ các cột khóa ngoại** đã được thay bằng giá trị (ví dụ bỏ `link_to_major` vì đã có `major_name`).
Đồng thời, để ngang TA-SQL, nó **vẫn hiện các bảng tra cứu** (`major`, `products`…). Mô hình 7B thấy cả view lẫn bảng tra cứu, nên
thường nối chúng lại qua đúng cột khóa ngoại đã bị bỏ:

```sql
-- SQL nháp: v_member không còn cột link_to_major (đã bỏ theo Hình 3)
SELECT T1.major_name FROM major AS T1 JOIN v_member AS T2 ON T1.major_id = T2.link_to_major WHERE ...
```

Có **108/500** SQL nháp của `vsql_fair` hỏng vì dùng cột `…_id` / `link_to_…` không còn trong view. Giai đoạn 2 viết lại sang bảng
gốc (`member` vẫn có `link_to_major`) nên vô tình sửa được những câu này. Như vậy, kết hợp "view bỏ khóa ngoại" với "hiện bảng tra
cứu" tự mâu thuẫn; điều chỉnh "hiện bảng" của `vsql_fair` gây ra lỗi giai đoạn 1 mà paper gốc không có.

**Đã sửa trong mã (12/11):** `vsql_fair` giờ **giữ lại cột khóa ngoại** trong view (vẫn không thêm bước chọn view nào). Nếu mở rộng
tất định các SQL nháp của lần chạy này bằng view mới, số câu đúng ở giai đoạn 1 tăng từ 130 lên 171; số thật cần chạy lại `vsql_fair`. Hình 3 không
quy định trường hợp này, vì paper không hiện bảng tra cứu cạnh view. `vsql_paper` (không hiện bảng tra cứu) và `vsqlplus` (view tự động
giữ khóa ngoại) không gặp lỗi này.

---

## 5. Theo nhóm câu hỏi

**Theo số bảng trong SQL đáp án** (số câu đúng; trong ngoặc là giai đoạn 1):

| Số bảng | Số câu | TA-SQL | V-SQL | V-SQL+ |
|---|---|---|---|---|
| 1 | 86 | **49** | 42 (38) | 43 (43) |
| 2 | 314 | 144 | 110 (77) | **146** (167) |
| 3 trở lên | 100 | **30** | 25 (15) | 26 (**41**) |

- Câu **cần nối bảng** là nơi view có ích: ở giai đoạn 1, V-SQL+ hơn TA-SQL ở cả nhóm 2 bảng (167 so với 144) lẫn nhóm 3 bảng trở lên
  (41 so với 30). Sau giai đoạn 2, lợi thế ở nhóm 3 bảng mất hết (còn 26), vì câu càng nhiều bảng thì viết lại càng dễ sai.
- Câu **chỉ 1 bảng**: TA-SQL tốt hơn. View chứa nhiều cột không cần, còn TA-SQL chỉ đưa ra các cột liên quan.

**CSDL nhỏ (V-SQL+ đưa hết view) và CSDL lớn (V-SQL+ chọn view):**

| Nhóm | Số câu | TA-SQL | V-SQL | V-SQL+ (giai đoạn 1) |
|---|---|---|---|---|
| 6 CSDL nhỏ, đưa hết view | 234 | **97** | 76 | 87 (111) |
| 5 CSDL lớn, có chọn view | 266 | 126 | 101 | **128** (140) |

Ở CSDL lớn, nơi bước chọn view (hướng 2) hoạt động, V-SQL+ nhỉnh hơn TA-SQL ngay cả ở kết quả cuối. Bước chọn view phủ đủ bảng đáp án
ở 99,0% số câu. Bước chọn bảng của TA-SQL chỉ phủ 82,6%.

**Theo CSDL**, V-SQL+ hơn TA-SQL rõ ở `financial` (14 so với 9), `student_club` (32 so với 27); thua rõ ở `european_football_2`
(29 so với 36), `superhero` (34 so với 41), `debit_card_specializing` (11 so với 16).

---

## 6. Về TA-SQL với model này

- `qwen2.5-coder:7b` làm theo định dạng tốt: **không có** câu trả lời nào là văn xuôi. Với qwen3.5:4b có 31 câu như vậy. Chỉ 8 câu chạm
  giới hạn 800 token.
- Lỗi đáng kể nhất là dùng hàm của MySQL: 23 câu dùng `YEAR()` (thêm 2 câu `MONTH()`), SQLite không có, nên báo lỗi.
- Vì vậy 44,6% phản ánh khá đúng năng lực của TA-SQL với model này. Con số tương đương TA-SQL + GPT-3.5-turbo trong paper (43,8%) và
  bảng chính thức của BIRD (41,6%).

---

## 7. So với các model đã chạy (500 câu, dữ liệu 2025)

| Model | TA-SQL | V-SQL | V-SQL+ | V-SQL+ − TA-SQL |
|---|---|---|---|---|
| qwen3.5:0.8b | 1,6 | 0,8 (`vsql`) | 2,2 | không so được |
| qwen3.5:4b | 38,0 | 19,2 (`vsql`) | 29,4 | −8,6 (có ý nghĩa) |
| **qwen2.5-coder:7b** | **44,6** | 35,4 (`vsql_fair`) | **43,0** | −1,6 (không có ý nghĩa) |
| *Paper, GPT-3.5-turbo* | *43,8* | *45,4* | — | — |

Model càng mạnh thì V-SQL+ càng tiến sát TA-SQL. Mô hình chuyên về code viết lại SQL ở giai đoạn 2 tốt hơn (mất ròng 36 câu, so với
53 câu của qwen3.5:4b). Paper chạy với GPT-3.5/GPT-4, vốn viết lại SQL tốt hơn, nên không gặp nút thắt này ở mức tương tự.
Lưu ý cột V-SQL không cùng phiên bản giữa các dòng (`vsql` và `vsql_fair`), nên không so trực tiếp được.

---

## 8. Kết luận

1. **Hai hướng cải tiến có tác dụng rõ**: SQL nháp trên view của V-SQL+ đúng nhiều hơn TA-SQL (251 so với 223, p = 0,02), nhất là
   ở câu cần nối nhiều bảng và ở CSDL lớn.
2. **Kết quả cuối V-SQL+ ngang TA-SQL** (43,0% so với 44,6%, p = 0,56). Phần chênh còn lại hoàn toàn do giai đoạn 2 (LLM viết lại SQL),
   bước mà đề xuất giữ nguyên như paper.
3. **`vsql_fair` đã được sửa** (giữ cột khóa ngoại trong view); cần chạy lại trước khi dùng để kết luận V-SQL so với TA-SQL.

## 9. Lưu ý khi dùng các số này

- Mỗi phương pháp chạy một lần, nhiệt độ 0.
- Chưa có `vsqlplus_fig4`, nên chưa tách được tác dụng của 2 hướng khỏi tác dụng của prompt giai đoạn 1 mới trong `vsqlplus`.
- `config.json` không ghi phiên bản mã. Nếu lần chạy dùng mã trước khi sửa lỗi "quay về bảng gốc" và lỗi thứ tự giá trị khớp
  (cập nhật ngày 07–08/11), thì một số ít câu của V-SQL+ có thể khác một chút khi chạy lại.
- Số tuyệt đối không so trực tiếp được với paper (khác model). Điều so được là thứ tự và chênh lệch giữa các phương pháp trên cùng model.
