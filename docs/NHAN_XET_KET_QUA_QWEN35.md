# Nhận xét kết quả: TA-SQL · V-SQL · V-SQL+ trên qwen3.5:0.8b và qwen3.5:4b

Kết quả lấy từ `results_new/` (chạy trên Colab, GPU T4). Phần `qwen3.5:9b` sẽ bổ sung sau (mục 6).

---

## Tóm tắt nhanh

- **qwen3.5:4b** (đáng tin cậy để so sánh): **TA-SQL 38,0% > V-SQL+ 29,4% > V-SQL 19,2%**. Mọi chênh lệch đều có ý nghĩa
  thống kê.
- **V-SQL+ hơn hẳn V-SQL** (+10,2 điểm): hai hướng cải tiến có tác dụng. Nhưng **V-SQL+ vẫn thua TA-SQL** (−8,6 điểm).
- Lý do V-SQL+ thua **không nằm ở view hay bước chọn view**. Nếu chỉ chấm câu SQL nháp viết trên view (giai đoạn 1), V-SQL+
  đúng **200/500**, ngang TA-SQL (190/500). Phần thua đến từ **giai đoạn 2 của paper** (LLM viết lại câu SQL nháp về bảng gốc):
  bước này làm hỏng 74 câu đang đúng và chỉ sửa được 21 câu.
- **qwen3.5:0.8b quá nhỏ**: cả ba phương pháp chỉ đúng 0,8–2,2%. Không dùng được để so sánh, chỉ cho thấy giới hạn của mô hình
  rất nhỏ.

---

## 1. Thiết lập

| Mục | Giá trị |
|---|---|
| Dữ liệu | BIRD mini-dev bản **2025-07-04** (Hugging Face): 500 câu khác nhau, 11 CSDL; độ khó 148 dễ / 250 trung bình / 102 khó |
| Mô hình | `qwen3.5:0.8b`, `qwen3.5:4b` qua Ollama; nhiệt độ 0; tối đa 800 token mỗi câu trả lời (như paper) |
| Embedding (V-SQL+) | `nomic-embed-text` |
| Phương pháp | `tasql` (TA-SQL), `vsql` (V-SQL tái hiện, **bản hiện tại**), `vsqlplus` (V-SQL+, **bản hiện tại**: 2 hướng cải tiến + prompt giai đoạn 1 mới) |
| Số lần chạy | 1 lần cho mỗi model |

Lần chạy này **chưa có** hai phương pháp mới thêm sau đó là `vsql_paper` (view sát Hình 3) và `vsqlplus_fig4` (V-SQL+ chỉ khác
V-SQL ở 2 hướng, dùng cùng prompt Hình 4). Xem mục 5.

> **Thuật ngữ**
> - **EX (độ chính xác thực thi)**: tỉ lệ câu mà kết quả chạy SQL của mô hình trùng với kết quả của SQL đáp án.
> - **Dummy SQL / giai đoạn 1**: câu SQL nháp viết trên các *view* (bảng ảo đã gộp sẵn các bảng liên quan).
> - **Giai đoạn 2**: LLM viết lại câu SQL nháp thành SQL trên bảng gốc (prompt Hình 5 của paper). Cả V-SQL và V-SQL+ đều dùng
>   bước này.
> - **Mở rộng tất định**: thay mỗi view trong câu SQL nháp bằng chính định nghĩa của nó (không gọi LLM). Cách này giữ đúng nghĩa
>   câu SQL nháp, nên dùng để **chấm riêng giai đoạn 1**.
> - **CI 95%**: khoảng mà EX thật nằm trong đó với độ tin cậy 95%.
> - **McNemar / p Holm**: kiểm định so sánh hai phương pháp trên cùng các câu hỏi; p Holm < 0,05 là khác biệt có ý nghĩa
>   thống kê (đã hiệu chỉnh vì so sánh nhiều cặp).

---

## 2. qwen3.5:4b

### 2.1 Kết quả chính

| Phương pháp | Dễ | Trung bình | Khó | **Tổng** | CI 95% | Lỗi sai tên bảng/cột | Lượt gọi LLM/câu | Token vào/câu | Giây LLM/câu |
|---|---|---|---|---|---|---|---|---|---|
| TA-SQL | 63,5 | 31,6 | 16,7 | **38,0** | 33,8–42,0 | 15,6% | 3,00 | 6.587 | 10,1 |
| V-SQL | 31,1 | 15,6 | 10,8 | **19,2** | 15,6–22,8 | 32,6% | 2,00 | 4.141 | 4,5 |
| V-SQL+ | 39,9 | 26,0 | **22,5** | **29,4** | 25,4–33,6 | 28,6% | 4,14 | 21.297 | 7,7 |

| So sánh | ΔEX | Chỉ bên trái đúng / chỉ bên phải đúng | p Holm |
|---|---|---|---|
| V-SQL+ − V-SQL | **+10,2** | 78 / 27 | < 0,001 |
| V-SQL+ − TA-SQL | −8,6 | 50 / 93 | < 0,001 |
| V-SQL − TA-SQL | −18,8 | 25 / 119 | < 0,001 |

**Đọc bảng:**
- V-SQL tái hiện chỉ đạt một nửa TA-SQL, **ngược với paper** (paper: V-SQL ngang hoặc hơn TA-SQL 1–3 điểm với GPT).
- V-SQL+ kéo V-SQL lên thêm 51 câu đúng (từ 96 lên 147), nhưng vẫn kém TA-SQL 43 câu.
- Ở **câu khó**, V-SQL+ (22,5%) **hơn** TA-SQL (16,7%). Ở **câu dễ**, TA-SQL hơn hẳn (63,5% so với 39,9%).
- Ý tưởng của paper là view giúp giảm lỗi sai tên bảng/cột. Ở đây lại ngược lại: V-SQL 32,6% và V-SQL+ 28,6% câu bị lỗi sai tên,
  gấp đôi TA-SQL (15,6%). Mục 2.2 giải thích lý do.

### 2.2 Tách giai đoạn 1 và giai đoạn 2

Chấm riêng câu SQL nháp (giai đoạn 1) bằng mở rộng tất định, rồi so với kết quả sau giai đoạn 2:

| | Số câu đúng / 500 |
|---|---|
| TA-SQL | 190 |
| V-SQL — giai đoạn 1 (SQL nháp trên view) | 134 |
| V-SQL — sau giai đoạn 2 (kết quả cuối) | 96 |
| V-SQL+ — giai đoạn 1 (SQL nháp trên view) | **200** |
| V-SQL+ — sau giai đoạn 2 (kết quả cuối) | 147 |

1. **Hướng cải tiến có tác dụng ở giai đoạn 1.** Câu SQL nháp của V-SQL+ đúng 200 câu, so với 134 của V-SQL. Chỉ V-SQL+ đúng ở
   98 câu, chỉ V-SQL đúng ở 32 câu (p < 0,001).
2. **Ở giai đoạn 1, V-SQL+ ngang TA-SQL**: 200 so với 190 (chỉ V-SQL+ đúng 76 câu, chỉ TA-SQL đúng 66 câu; p = 0,45, không khác
   biệt có ý nghĩa). Nói cách khác, mô hình viết SQL **trên view của V-SQL+** tốt ngang TA-SQL viết trên bảng gốc.
3. **Giai đoạn 2 làm mất điểm.** Ở V-SQL+, giai đoạn 2 làm hỏng 74 câu đang đúng và chỉ sửa được 21 câu, nên mất ròng 53 câu.
   V-SQL cũng vậy: hỏng 69, sửa 31. Trong 74 câu bị hỏng của V-SQL+:
   - 44 câu lỗi **"no such column"**: mô hình chỉ đổi tên view thành tên bảng mà **không thêm phép nối**, nên cột vốn lấy từ bảng
     khác bị mất;
   - 17 câu chạy được nhưng ra kết quả sai;
   - 5 câu vẫn còn tên view trong SQL cuối;
   - 8 câu lỗi khác.

Ví dụ (CSDL `debit_card_specializing`):

```sql
-- Câu SQL nháp (đúng): Segment là cột của customers đã được gộp sẵn vào view v_yearmonth
SELECT AVG(Consumption) / 12 FROM v_yearmonth WHERE Segment = 'SME' AND Date BETWEEN '201301' AND '201312'
-- Sau giai đoạn 2 (sai): chỉ đổi v_yearmonth -> yearmonth, quên nối bảng customers
SELECT AVG(yearmonth.Consumption) / 12 FROM yearmonth WHERE yearmonth.Segment = 'SME' AND ...
-- lỗi: no such column: yearmonth.Segment
```

Đây cũng là lý do tỉ lệ lỗi sai tên bảng/cột của V-SQL và V-SQL+ cao. Lỗi xuất hiện khi **viết lại** câu SQL nháp, không phải khi
đọc view. Paper dùng GPT-3.5/GPT-4 cho bước viết lại; mô hình 4B làm bước này kém hơn nhiều.

### 2.3 Theo số bảng trong SQL đáp án

| Số bảng | Số câu | TA-SQL | V-SQL (giai đoạn 1 / cuối) | V-SQL+ (giai đoạn 1 / cuối) |
|---|---|---|---|---|
| 1 | 86 | **49** | 21 / 30 | 34 / 33 |
| 2 | 314 | 121 | 90 / 61 | **137** / 97 |
| 3 trở lên | 100 | 20 | 23 / 5 | **29** / 17 |

- Câu cần **nối từ 2 bảng trở lên** là nơi view phát huy tác dụng: giai đoạn 1 của V-SQL+ hơn TA-SQL (137 so với 121; 29 so với 20).
  Điều này khớp với ý tưởng của paper: gộp sẵn các bảng để mô hình ít phải viết JOIN.
- Câu **chỉ cần 1 bảng** thì TA-SQL tốt hơn rõ (49 so với 33–34). Với các câu này, view thêm nhiều cột không cần thiết, còn TA-SQL
  chỉ đưa ra những cột liên quan.

### 2.4 CSDL nhỏ (đưa hết view) và CSDL lớn (chọn view)

V-SQL+ chỉ chọn view ở 5 CSDL lớn (266 câu). Ở 6 CSDL nhỏ (234 câu) nó đưa hết view vào prompt.

| Nhóm | Số câu | TA-SQL | V-SQL | V-SQL+ (giai đoạn 1 / cuối) |
|---|---|---|---|---|
| CSDL nhỏ, đưa hết view | 234 | 77 | 31 | 84 / 54 |
| CSDL lớn, có chọn view | 266 | 113 | 65 | 116 / 93 |

Ở cả hai nhóm, giai đoạn 1 của V-SQL+ đều ngang hoặc hơn TA-SQL. Bước chọn view không làm mất câu: độ phủ bảng đáp án của schema
đưa cho mô hình là 98,0%.

### 2.5 Về TA-SQL

- TA-SQL vẫn cao nhất dù chịu hai bất lợi:
  - 31 câu trả lời ở bước SR → SQL là văn xuôi ("Based on the provided Schema…"), bị cắt ở 800 token trước khi kịp viết SQL;
  - bước chọn bảng của TA-SQL chỉ phủ đủ bảng đáp án ở 85,4% số câu.
- TA-SQL chậm nhất mỗi câu (10,1 giây) vì câu trả lời dài. V-SQL+ dùng nhiều token đầu vào nhất (21.297 mỗi câu, gấp 3,2 lần
  TA-SQL), chủ yếu do 4 mẫu bầu chọn ở CSDL lớn.

---

## 3. qwen3.5:0.8b

| Phương pháp | Tổng | Số câu đúng | Lỗi sai tên bảng/cột |
|---|---|---|---|
| TA-SQL | 1,6% | 8 | 63,2% |
| V-SQL | 0,8% | 4 | 81,4% |
| V-SQL+ | 2,2% | 11 | 71,8% |

- Không có cặp nào khác nhau có ý nghĩa thống kê (p Holm ≥ 0,18). Số câu đúng quá ít để so sánh.
- **Mô hình 0.8B không làm được giai đoạn 2**: câu SQL cuối vẫn còn tên view ở 342/500 câu (V-SQL) và 283/500 câu (V-SQL+). Vì
  vậy hầu hết lỗi là "no such table: v_…".
- Giai đoạn 1 thì khá hơn: SQL nháp của V-SQL+ đúng 48 câu, V-SQL 23 câu, trong khi TA-SQL chỉ đúng 8 câu. Nhưng gần như toàn bộ
  bị mất ở giai đoạn 2.
- Kết luận: với mô hình rất nhỏ, khung hai giai đoạn của V-SQL không dùng được, vì mô hình không viết lại được SQL. Nên báo cáo kết
  quả 0.8B như một giới hạn, không dùng để kết luận về các phương pháp.

---

## 4. Kết luận chung (trên 2 model)

1. **Tái hiện V-SQL không đạt được kết quả của paper**: V-SQL thua TA-SQL trên cả hai model. Nguyên nhân chính là giai đoạn 2
   (LLM viết lại SQL), bước mà mô hình nhỏ làm kém. Paper chạy với GPT nên không gặp vấn đề này ở mức tương tự.
2. **Hai hướng cải tiến có tác dụng ở chỗ chúng tác động**, tức là giai đoạn 1: với 4b, SQL nháp trên view của V-SQL+ đúng 200
   câu, so với 134 của V-SQL và ngang TA-SQL (190). Lợi thế rõ nhất ở câu cần nối nhiều bảng và câu khó.
3. **Nút thắt còn lại là giai đoạn 2.** Cả hai hướng cải tiến đều không đụng tới bước này, vì đề xuất giữ nguyên giai đoạn 2 của
   paper.

---

## 5. Lưu ý khi dùng các số này

- **Chưa tách được tác dụng của 2 hướng khỏi tác dụng của prompt.** `vsqlplus` trong lần chạy này vừa có 2 hướng cải tiến, vừa
  có prompt giai đoạn 1 mới (schema có nguồn gốc cột và giá trị mẫu, mục giá trị khớp, ghi chú khi quay về bảng gốc). Vì vậy
  +10,2 điểm so với V-SQL là tác dụng của **cả ba**. Notebook đã có thêm:
  - `vsqlplus_fig4`: chỉ 2 hướng, giai đoạn 1 dùng đúng template Hình 4 và schema Bảng 6 như V-SQL;
  - `vsql_paper`: view sát Hình 3.

  So sánh sạch cho 2 hướng là `vsqlplus_fig4` − `vsql_paper`.
- **Lỗi đã sửa sau lần chạy này.** Khi quay về bảng gốc, nếu bảng cần thêm là một bảng tra cứu không được chọn vào prompt, mã cũ
  ghi là đã thêm nhưng không hiện bảng đó trong schema. Lỗi này ảnh hưởng 7/500 câu với 4b và 53/500 câu với 0.8b, chỉ ở V-SQL+.
- **Mỗi model chỉ chạy một lần**, nhiệt độ 0. Kết quả có thể dao động nhẹ nếu Ollama hoặc phiên bản model khác đi.
- **Dữ liệu là bản 2025-07-04**; không rõ paper dùng bản 2024 hay 2025. Số tuyệt đối không so được với Bảng 3 của paper vì khác
  model (GPT so với Qwen nhỏ). Điều so được là thứ tự và chênh lệch giữa các phương pháp trên cùng model.
- Có 1 câu ở mỗi phương pháp TA-SQL / V-SQL+ của 0.8b gặp lỗi Ollama (được tính là sai).

---

## 6. qwen3.5:9b

*(Bổ sung sau khi có kết quả.)*
