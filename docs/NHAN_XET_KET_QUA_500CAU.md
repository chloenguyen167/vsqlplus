# Nhận xét kết quả 500 câu: gpt-4o-mini và qwen3.5:9b

Tài liệu này giải thích kết quả chạy **V-SQL**, **V-SQL+** và **DAIL-SQL** trên toàn bộ 500 câu BIRD mini-dev (bản 2025-07-04)
với hai mô hình ngôn ngữ: `gpt-4o-mini` (OpenAI API) và `qwen3.5:9b` (Ollama trên Colab T4).

Số liệu lấy từ:
- `results_new/cmp_gpt-4o-mini_d2025/summary.md` và các file `predictions_*.jsonl` cùng thư mục;
- `results_new/cmp_qwen35_9b_d2025/summary.md` và các file `predictions_*.jsonl` cùng thư mục.

Một số con số (độ chồng lấn giữa các phương pháp, ví dụ lỗi) được tính thêm trực tiếp từ các file `predictions_*.jsonl`, ghép câu
theo `uid`.

---

## Tóm tắt nhanh

| Phương pháp | gpt-4o-mini | qwen3.5:9b | Giảm khi đổi sang model nhỏ |
|---|---|---|---|
| V-SQL (tái hiện paper) | 46,8% (234 câu) | 28,4% (142 câu) | −18,4 điểm |
| **V-SQL+** (đề xuất) | **52,4%** (262 câu) | 40,2% (201 câu) | −12,2 điểm |
| DAIL-SQL (baseline) | 50,0% (250 câu) | **46,4%** (232 câu) | −3,6 điểm |

1. **V-SQL+ luôn tốt hơn V-SQL**: +5,6 điểm với gpt-4o-mini, +11,8 điểm với qwen3.5:9b. Model càng yếu thì hai hướng cải tiến
   càng có ích.
2. **Với gpt-4o-mini, V-SQL+ đứng đầu**: hơn DAIL-SQL 2,4 điểm. Mức chênh này chưa đủ để khẳng định có ý nghĩa thống kê.
3. **Với qwen3.5:9b, DAIL-SQL đứng đầu**: hơn V-SQL+ 6,2 điểm, và lần này mức chênh **có ý nghĩa thống kê**.
4. **Nguyên nhân chính khiến V-SQL+ thua trên qwen3.5:9b là giai đoạn 2** (LLM viết lại SQL từ view về bảng gốc). Nếu chỉ chấm SQL
   nháp của giai đoạn 1, V-SQL+ đúng 228 câu (45,6%), gần bằng DAIL-SQL (232 câu). Giai đoạn 2 làm hỏng 41 câu đang đúng và chỉ sửa
   được 14 câu.
5. **DAIL-SQL ít bị ảnh hưởng nhất khi đổi model** (chỉ giảm 3,6 điểm), vì 7 ví dụ mẫu trong prompt "dắt tay" model nhỏ. V-SQL giảm
   mạnh nhất (18,4 điểm) vì nó cần model tự làm nhiều bước khó hơn: chọn view, viết SQL trên view, rồi tự dịch ngược về bảng gốc.

---

## 1. Thiết lập thí nghiệm

| Mục | gpt-4o-mini | qwen3.5:9b |
|---|---|---|
| Dữ liệu | BIRD mini-dev 2025-07-04: 500 câu, 11 CSDL. Độ khó: 148 dễ / 250 trung bình / 102 khó | như bên trái |
| Nơi chạy | OpenAI API | Ollama trên Google Colab (GPU T4) |
| Nhiệt độ, độ dài trả lời | 0; tối đa 800 token | như bên trái |
| Phương pháp đã chạy | `vsql`, `vsqlplus`, `dailsql` và 6 biến thể bỏ bớt thành phần của V-SQL+ | chỉ `vsql`, `vsqlplus`, `dailsql` |
| V-SQL+ chọn view bằng | **chỉ BM25** (backend OpenAI không có embedding) | BM25 + embedding `nomic-embed-text` (truy hồi lai đầy đủ) |
| Phiên bản V-SQL | impl 7: LLM chọn view theo câu hỏi | impl 7 |
| Số lần chạy | 1 | 1 |

Như vậy hai lần chạy gần như giống nhau, chỉ khác model và một điểm nhỏ: trên gpt-4o-mini, V-SQL+ chọn view chỉ bằng BM25, chưa có
embedding. Kết quả 52,4% của V-SQL+ trên gpt-4o-mini vì thế là con số của bản V-SQL+ chưa đầy đủ.

### Ba phương pháp, nói ngắn gọn

- **DAIL-SQL (baseline)**: đưa cho model toàn bộ schema dạng `CREATE TABLE` và **7 câu ví dụ** (câu hỏi + SQL đáp án) lấy từ tập
  train BIRD, chọn theo độ giống với câu hỏi hiện tại. Model viết SQL một lần, sau đó viết lại một lần nữa với ví dụ chọn theo khung
  SQL vừa viết.
- **V-SQL (tái hiện paper)**: chia làm 2 giai đoạn.
  - Trước khi chạy, mỗi CSDL được gộp sẵn thành các **view** (bảng ảo đã JOIN sẵn các bảng liên quan), để model không phải tự viết
    JOIN.
  - Một lượt gọi LLM chọn các view/bảng phù hợp với câu hỏi.
  - **Giai đoạn 1**: model viết **SQL nháp** (dummy SQL) trên các view (prompt Hình 4 của paper).
  - **Giai đoạn 2**: model viết lại SQL nháp thành SQL chạy trên **bảng gốc** (prompt Hình 5).
  - Không có câu ví dụ nào (zero-shot).
- **V-SQL+ (đề xuất)**: giữ khung 2 giai đoạn của V-SQL, thêm hai hướng cải tiến.
  - **Hướng 1, sinh view tự động** từ khóa ngoại (không phụ thuộc SQL đáp án).
  - **Hướng 2, chọn view bằng truy hồi lai**: kết hợp BM25, embedding, liên kết giá trị (tìm giá trị trong câu hỏi khớp với giá trị
    thật trong CSDL), bầu chọn nhiều mẫu, và đưa thêm schema bảng gốc khi cần.
  - Prompt giai đoạn 1 mới, nói rõ phải viết SQLite.

### Thuật ngữ dùng trong tài liệu

- **EX (Execution Accuracy)**: tỉ lệ câu mà kết quả chạy SQL của model **trùng** với kết quả chạy SQL đáp án. Đây là thước đo chính.
- **Điểm (%)**: chênh lệch EX. Trên 500 câu, 1 điểm = 5 câu.
- **CI 95%**: khoảng mà EX thật nằm trong đó với độ tin cậy 95%. Hai phương pháp có CI chồng lên nhau nhiều thì chưa chắc khác nhau.
- **McNemar, p Holm**: kiểm định so sánh hai phương pháp trên **cùng** các câu hỏi, chỉ dựa vào những câu một bên đúng mà bên kia
  sai. **p Holm < 0,05** nghĩa là khác biệt có ý nghĩa thống kê (đã hiệu chỉnh vì làm nhiều phép so sánh cùng lúc).
- **Ảo giác schema**: model dùng tên bảng hoặc tên cột **không tồn tại** (lỗi `no such column`, `no such table`). Đây chính là loại
  lỗi mà paper V-SQL muốn giảm bằng view.
- **Giai đoạn 1 đúng**: SQL nháp được thay view bằng định nghĩa của chính view đó (không gọi LLM), rồi chạy và chấm. Con số này cho
  biết kết quả **nếu giai đoạn 2 không làm sai gì**.

---

## 2. gpt-4o-mini

### 2.1 Kết quả chính

| Phương pháp | Dễ (148) | Trung bình (250) | Khó (102) | **Tổng** | CI 95% |
|---|---|---|---|---|---|
| V-SQL | 62,2 | 46,4 | 25,5 | **46,8** | 42,2 – 51,4 |
| **V-SQL+** | **68,9** | 49,6 | **35,3** | **52,4** | 48,0 – 56,8 |
| DAIL-SQL | 66,2 | 47,6 | 32,4 | **50,0** | 45,4 – 54,6 |
| *V-SQL+ thay giai đoạn 2 bằng mở rộng tất định* | 67,6 | 51,2 | 37,3 | *53,2* | 48,8 – 57,6 |

**Đọc bảng:**
- V-SQL+ cao nhất ở cả ba mức độ khó. Khoảng cách lớn nhất nằm ở **câu khó**: V-SQL+ 35,3%, V-SQL chỉ 25,5% (+9,8 điểm).
- V-SQL tái hiện thua DAIL-SQL 3,2 điểm. Paper báo cáo V-SQL hơn DAIL-SQL; ở đây chưa tái hiện được điều đó (xem mục 2.6).
- Dòng cuối là một biến thể để đối chiếu: bỏ LLM ở giai đoạn 2, chỉ thay view bằng định nghĩa của nó. Biến thể này còn cao hơn
  V-SQL+ 0,8 điểm, tức là **giai đoạn 2 bằng LLM không giúp gì** cho V-SQL+ trên gpt-4o-mini.

### 2.2 Khác biệt có thật hay chỉ do ngẫu nhiên?

| So sánh | Chênh EX | Chỉ bên A đúng / chỉ bên B đúng | p McNemar | p Holm | Kết luận |
|---|---|---|---|---|---|
| V-SQL+ − V-SQL | +5,6 | 69 / 41 | 0,010 | 0,061 | Có xu hướng rõ, nhưng sau hiệu chỉnh Holm vẫn chưa qua ngưỡng 0,05 |
| V-SQL+ (tất định) − V-SQL | +6,4 | 72 / 40 | 0,003 | **0,026** | **Có ý nghĩa thống kê** |
| V-SQL+ − DAIL-SQL | +2,4 | 68 / 56 | 0,323 | 1,000 | Chưa đủ bằng chứng |
| V-SQL − DAIL-SQL | −3,2 | 51 / 67 | 0,167 | 0,668 | Chưa đủ bằng chứng |

Giải thích cho dễ hiểu: V-SQL+ đúng thêm 69 câu mà V-SQL sai, nhưng cũng sai 41 câu mà V-SQL đúng. Phần lợi ròng là 28 câu. Với 500
câu và 8 phép so sánh cùng lúc, mức này **gần** đủ để khẳng định, nhưng chưa hẳn. Muốn chắc chắn hơn cần chạy thêm lần nữa hoặc
dùng thêm dữ liệu.

**Ba phương pháp bổ sung cho nhau khá nhiều:**
- 156 câu cả ba đều đúng.
- 332 câu (66,4%) có ít nhất một phương pháp đúng.
- 31 câu chỉ V-SQL+ đúng, 29 câu chỉ DAIL-SQL đúng, 14 câu chỉ V-SQL đúng.

Nếu có cách chọn đúng câu trả lời tốt nhất trong ba phương pháp, EX có thể lên tới 66%. Đây là gợi ý cho hướng kết hợp sau này.

### 2.3 Lỗi thuộc loại nào?

Tỉ lệ trên tổng 500 câu:

| Phương pháp | Ảo giác schema | Lỗi cú pháp | Lỗi chạy khác | Chạy được nhưng rỗng | Chạy được nhưng sai | **Tổng lỗi chạy** |
|---|---|---|---|---|---|---|
| V-SQL | 10,4% | 0,8% | 1,4% | 4,2% | 36,4% | 63 câu |
| V-SQL+ | 7,6% | 0,6% | 1,4% | 4,8% | 33,2% | 48 câu |
| DAIL-SQL | 9,2% | **4,0%** | 1,2% | 4,6% | **31,0%** | 72 câu |
| V-SQL+ (tất định) | **1,6%** | 0,6% | 2,0% | 5,2% | 37,4% | – |

**Nhận xét:**
- V-SQL+ có **ít lỗi chạy nhất** (48 câu, so với 72 của DAIL-SQL). Đúng như ý tưởng của paper: view giúp model ít bịa tên cột hơn.
- Nhưng DAIL-SQL có **ít câu "chạy được mà sai" nhất** (31,0%). Nghĩa là khi SQL của DAIL chạy được, nó hiểu câu hỏi đúng hơn. Đó
  là nhờ 7 ví dụ mẫu: model học được cách chọn đúng cột trả về, cách tính tỉ lệ, cách viết giá trị có dấu nháy, v.v.
- Khi bỏ LLM ở giai đoạn 2 (dòng cuối), ảo giác schema gần như biến mất (1,6%). Vậy phần lớn lỗi sai tên cột còn lại của V-SQL+
  **sinh ra ở giai đoạn 2**, lúc LLM tự dịch cột của view về cột của bảng gốc.

**Tóm lại:** V-SQL+ thắng nhờ **ít lỗi chạy hơn**, chưa phải nhờ hiểu câu hỏi tốt hơn DAIL-SQL.

### 2.4 Giai đoạn 1 và giai đoạn 2 đóng góp bao nhiêu?

| Phương pháp | Giai đoạn 1 đúng | Kết quả cuối đúng | Giai đoạn 2 sửa đúng | Giai đoạn 2 làm hỏng | Lợi ròng |
|---|---|---|---|---|---|
| V-SQL | 216 (43,2%) | 234 (46,8%) | 31 | 13 | **+18** |
| V-SQL+ | 266 (53,2%) | 262 (52,4%) | 11 | 15 | **−4** |
| DAIL-SQL (vòng 1 → vòng 2) | 248 (49,6%) | 250 (50,0%) | 23 | 21 | +2 |

- Với **V-SQL**, giai đoạn 2 có ích (+18 câu). Prompt Hình 4 không nói rõ phải viết SQLite, nên SQL nháp hay dùng hàm của hệ khác
  (`YEAR(`, `DIVIDE(`). Giai đoạn 2 sửa lại phần lớn các lỗi này.
- Với **V-SQL+**, SQL nháp đã tốt (prompt mới nói rõ SQLite), nên giai đoạn 2 chỉ còn cơ hội làm hỏng. Kết quả hơi âm (−4 câu).
- Phần thắng của V-SQL+ so với V-SQL đến **hoàn toàn từ giai đoạn 1**: 266 so với 216 câu, hơn 50 câu.

### 2.5 Từng thành phần của V-SQL+ đóng góp bao nhiêu?

Mỗi dòng so sánh V-SQL+ đầy đủ với một bản bị bỏ đi đúng một thành phần (chỉ có trên gpt-4o-mini):

| Thành phần | Cách đo | Chênh EX | Nhận xét |
|---|---|---|---|
| Prompt giai đoạn 1 mới | V-SQL+ so với bản dùng lại prompt Hình 4 của paper | **+8,0** | Đóng góp lớn nhất |
| Chọn view (hướng 2) | V-SQL+ so với bản đưa hết view vào prompt | **+4,4** | Chọn ít mà đúng tốt hơn đưa nhiều |
| Liên kết giá trị | V-SQL+ so với bản bỏ liên kết giá trị | **+4,2** | Rất có ích: giúp model biết viết `'CZE'` thay vì `'Czech Republic'` |
| Schema bảng gốc dự phòng | V-SQL+ so với bản bỏ | +0,6 | Gần như không tác dụng |
| Bầu chọn nhiều mẫu | V-SQL+ so với bản bỏ | −0,2 | Không có ích, còn tốn thêm khoảng 2 lượt gọi LLM mỗi câu |
| Giai đoạn 2 bằng LLM | V-SQL+ so với bản mở rộng tất định | −0,8 | Không có ích |
| Hướng 1 (view tự động), đưa hết view | So với V-SQL | +1,2 | View tự động ít nhất không kém view của paper |

**Gợi ý từ bảng này:** có thể bỏ bầu chọn nhiều mẫu (1,9 thay vì 4,0 lượt gọi LLM mỗi câu, EX 52,6%) và thay giai đoạn 2 bằng mở
rộng tất định (EX 53,2%). Mỗi thay đổi riêng lẻ đều không làm giảm EX. Bản gộp cả hai thay đổi chưa được chạy.

### 2.6 Điểm mạnh và điểm yếu theo loại câu hỏi

**Theo số bảng trong SQL đáp án:**

| Số bảng | V-SQL | V-SQL+ | DAIL-SQL |
|---|---|---|---|
| 1 bảng (86 câu) | 62,8 | **68,6** | 67,4 |
| 2 bảng (314 câu) | 48,1 | **52,5** | 51,3 |
| 3 bảng (84 câu) | 31,0 | **38,1** | 31,0 |
| ≥ 4 bảng (16 câu) | 18,8 | **37,5** | 31,2 |

V-SQL+ hơn DAIL-SQL rõ nhất ở câu cần **3 bảng trở lên**: đây là loại câu mà view (JOIN sẵn) phát huy tác dụng, đúng như lập luận của
paper. Lưu ý nhóm ≥ 4 bảng chỉ có 16 câu, nên chỉ mang tính tham khảo.

**Theo CSDL, một vài điểm đáng chú ý:**
- `financial`: V-SQL+ 56,2%, DAIL-SQL chỉ 18,8%. CSDL này có nhiều bảng nối qua mã (`account_id`, `district_id`...) và tên cột viết
  tắt khó hiểu (`A2`, `A11`...). View gộp sẵn cùng mô tả cột giúp model rất nhiều.
- `california_schools`: mọi phương pháp đều thấp (6,7–13,3%). Tên cột dài, nhiều cột gần giống nhau, câu hỏi cần công thức phức tạp.
- `card_games`: DAIL-SQL tốt nhất (51,9% so với 38,5% của V-SQL+). V-SQL+ chỉ sinh được 1 view cho CSDL này, nên ít được lợi từ view.

### 2.7 Chi phí

Trung bình mỗi câu:

| Phương pháp | Lượt gọi LLM | Token vào | Token ra | Thời gian LLM |
|---|---|---|---|---|
| V-SQL | 3,00 | 8.219 | 142 | 4,9 s |
| V-SQL+ | 4,04 | 19.045 | 204 | 8,7 s |
| V-SQL+ bỏ bầu chọn | 1,93 | 5.984 | 105 | 3,6 s |
| DAIL-SQL | 1,75 | **2.946** | 479 | 9,6 s |

V-SQL+ đầy đủ tốn token gấp khoảng 6 lần DAIL-SQL. Bản bỏ bầu chọn chỉ tốn gấp 2 lần, mà EX vẫn là 52,6%.

---

## 3. qwen3.5:9b

### 3.1 Kết quả chính

| Phương pháp | Dễ (148) | Trung bình (250) | Khó (102) | **Tổng** | CI 95% |
|---|---|---|---|---|---|
| V-SQL | 42,6 | 25,6 | 14,7 | **28,4** | 24,4 – 32,4 |
| V-SQL+ | 54,1 | 36,4 | 29,4 | **40,2** | 35,8 – 44,6 |
| **DAIL-SQL** | **60,1** | **43,2** | **34,3** | **46,4** | 41,8 – 50,8 |

| So sánh | Chênh EX | Chỉ bên A đúng / chỉ bên B đúng | p Holm | Kết luận |
|---|---|---|---|---|
| V-SQL+ − V-SQL | **+11,8** | 89 / 30 | < 0,001 | **V-SQL+ chắc chắn tốt hơn V-SQL** |
| V-SQL+ − DAIL-SQL | −6,2 | 58 / 89 | 0,013 | **DAIL-SQL tốt hơn V-SQL+ (có ý nghĩa thống kê)** |
| V-SQL − DAIL-SQL | −18,0 | 37 / 127 | < 0,001 | DAIL-SQL tốt hơn V-SQL rất xa |

**Đọc bảng:**
- Thứ tự trên model nhỏ là **DAIL-SQL > V-SQL+ > V-SQL**, ở cả ba mức độ khó.
- V-SQL+ kéo V-SQL lên thêm 59 câu đúng (từ 142 lên 201). Hai hướng cải tiến có tác dụng rất rõ trên model nhỏ.
- Nhưng V-SQL+ vẫn kém DAIL-SQL 31 câu.
- Độ chồng lấn: 87 câu cả ba đều đúng; 302 câu (60,4%) có ít nhất một phương pháp đúng. Chỉ DAIL-SQL đúng: 71 câu. Chỉ V-SQL+
  đúng: 33 câu.

### 3.2 Vì sao V-SQL+ thua DAIL-SQL trên qwen3.5:9b? Do giai đoạn 2

| Phương pháp | Giai đoạn 1 đúng | Kết quả cuối đúng | Giai đoạn 2 sửa đúng | Giai đoạn 2 làm hỏng | Lợi ròng |
|---|---|---|---|---|---|
| V-SQL | 155 (31,0%) | 142 (28,4%) | 18 | 31 | **−13** |
| V-SQL+ | **228 (45,6%)** | 201 (40,2%) | 14 | **41** | **−27** |
| DAIL-SQL (vòng 1 → vòng 2) | 225 (45,0%) | 232 (46,4%) | 37 | 30 | +7 |

Đây là phát hiện quan trọng nhất của lần chạy này:
- **Ở giai đoạn 1, V-SQL+ ngang DAIL-SQL**: 228 câu so với 225 (vòng 1 của DAIL) và 232 (kết quả cuối của DAIL). Nghĩa là view tự
  động cùng bước chọn view **đã làm tốt phần việc của mình**.
- **Giai đoạn 2 làm mất 27 câu ròng.** Trong 41 câu bị làm hỏng, 29 câu hỏng vì lỗi sai tên cột.
- Trên gpt-4o-mini, giai đoạn 2 của V-SQL+ chỉ làm mất 4 câu. Model càng nhỏ, bước "dịch ngược về bảng gốc" càng hay sai.
- Trong 89 câu DAIL-SQL đúng mà V-SQL+ sai, có 23 câu V-SQL+ đã đúng ở giai đoạn 1 rồi bị giai đoạn 2 làm hỏng.
- Biến thể mở rộng tất định chưa được chạy trên qwen3.5:9b. Nhưng theo định nghĩa, nó cho đúng kết quả của giai đoạn 1, tức khoảng
  **45,6%**: rút ngắn khoảng cách với DAIL-SQL từ 6,2 xuống còn 0,8 điểm.

**Giai đoạn 2 hỏng như thế nào? Ba ví dụ thật.** View `v_transactions_1k` gộp sẵn bảng `transactions_1k` với cột của các bảng
`gasstations`, `products` và `customers`.

- **uid 17.** SQL nháp đúng: `SELECT Description FROM v_transactions_1k WHERE Country = 'CZE'`.
  - Giai đoạn 2 viết `SELECT products.Description FROM transactions_1k JOIN gasstations ...`.
  - Model biết cột `Description` thuộc bảng `products`, nhưng **quên JOIN bảng `products`**, nên SQL lỗi `no such column`.
- **uid 18.** SQL nháp: `... FROM v_transactions_1k WHERE ChainID = 11`.
  - Giai đoạn 2 viết `FROM transactions_1k WHERE gasstations.ChainID = 11`, lại **không JOIN** bảng `gasstations`.
- **uid 3.** View `v_yearmonth` có cột `Currency`, lấy từ bảng `customers`.
  - Giai đoạn 2 có JOIN `customers`, nhưng lại viết `yearmonth.Currency`, tức **gán cột cho nhầm bảng**.

Tóm lại, khi viết lại, model nhỏ phải tự nhớ cột nào của view đến từ bảng nào và phải thêm JOIN tương ứng. Đây chính là phần việc
mà view sinh ra để model **khỏi phải làm**, nhưng giai đoạn 2 của paper lại bắt model làm lại. Mở rộng tất định làm việc này bằng
code nên không bao giờ sai.

### 3.3 Vì sao V-SQL tái hiện tụt mạnh đến vậy (28,4%)?

Ngoài lỗi ở giai đoạn 2 (−13 câu ròng), V-SQL trên qwen3.5:9b còn gặp vấn đề ở **bước chọn view bằng LLM**:
- qwen3.5:9b chọn trung bình chỉ **1,7** view/bảng mỗi câu; gpt-4o-mini chọn 2,4.
- Có **61 câu** mà một bảng cần cho đáp án không có trong schema đưa cho model (gpt-4o-mini: 21 câu). 57/61 câu này sai: không có
  bảng thì không thể viết đúng.
- V-SQL+ chọn view bằng truy hồi (không nhờ LLM), nên chỉ thiếu bảng ở 9 câu.

Ảo giác schema của V-SQL lên tới 18,6%, gần gấp đôi DAIL-SQL (9,8%). Đây là chiều ngược với mục tiêu của paper. Lý do: thiếu bảng
ở bước chọn, cộng với lỗi dịch ngược ở giai đoạn 2.

### 3.4 Lỗi thuộc loại nào?

| Phương pháp | Ảo giác schema | Lỗi cú pháp | Không ra SQL | Chạy được nhưng rỗng | Chạy được nhưng sai | **Tổng lỗi chạy** |
|---|---|---|---|---|---|---|
| V-SQL | 18,6% | 4,0% | 2,8% | 7,0% | 36,8% | 139 câu |
| V-SQL+ | 16,2% | 1,2% | 0,0% | 4,6% | 36,6% | 93 câu |
| DAIL-SQL | **9,8%** | 5,4% | 0,0% | 6,6% | **30,4%** | **83 câu** |

Khác với gpt-4o-mini, ở đây DAIL-SQL thắng **cả** về số lỗi chạy lẫn số câu chạy được mà sai. Phần lớn ảo giác schema của V-SQL+
(16,2%) đến từ giai đoạn 2, như phân tích ở mục 3.2.

### 3.5 Theo loại câu hỏi

| Số bảng | V-SQL | V-SQL+ | DAIL-SQL |
|---|---|---|---|
| 1 bảng (86) | 45,3 | 53,5 | **60,5** |
| 2 bảng (314) | 26,1 | 39,5 | **47,1** |
| 3 bảng (84) | 21,4 | 29,8 | **31,0** |
| ≥ 4 bảng (16) | 18,8 | **37,5** | **37,5** |

- Khoảng cách giữa V-SQL+ và DAIL-SQL **thu hẹp dần khi câu cần nhiều bảng hơn**: −7,0 điểm ở câu 1 bảng, −1,2 điểm ở câu 3 bảng,
  hòa ở câu ≥ 4 bảng. View vẫn có giá trị với câu nhiều JOIN, kể cả trên model nhỏ.
- Theo CSDL, V-SQL+ hơn DAIL-SQL ở `financial` (43,8 so với 31,2) và `superhero` (69,2 so với 65,4). V-SQL+ kém rõ ở
  `thrombosis_prediction` (12,0 so với 32,0) và `california_schools` (13,3 so với 23,3).

### 3.6 Chi phí

| Phương pháp | Lượt gọi LLM | Token vào | Token ra | Thời gian LLM (T4) |
|---|---|---|---|---|
| V-SQL | 2,97 | 6.082 | 148 | 12,8 s |
| V-SQL+ | 4,12 | 21.131 | 215 | 15,8 s |
| DAIL-SQL | 1,72 | 3.163 | 566 | **32,7 s** |

Trên GPU, thời gian chủ yếu phụ thuộc vào **số token phải sinh ra**, không phải số token đọc vào. DAIL-SQL sinh câu trả lời dài
(trung bình 566 token, gấp gần 4 lần V-SQL), nên chậm nhất dù prompt ngắn nhất.

---

## 4. So sánh giữa hai model

| | gpt-4o-mini | qwen3.5:9b |
|---|---|---|
| Thứ hạng | V-SQL+ > DAIL-SQL > V-SQL | DAIL-SQL > V-SQL+ > V-SQL |
| V-SQL+ so với V-SQL | +5,6 (gần ý nghĩa thống kê) | +11,8 (có ý nghĩa) |
| V-SQL+ so với DAIL-SQL | +2,4 (chưa đủ bằng chứng) | −6,2 (có ý nghĩa) |
| Giai đoạn 1 của V-SQL+ | 53,2% | 45,6% |
| Lợi ròng của giai đoạn 2 trong V-SQL+ | −4 câu | −27 câu |
| Ảo giác schema của V-SQL+ / DAIL-SQL | 7,6% / 9,2% | 16,2% / 9,8% |

**Vì sao đổi sang model nhỏ thì DAIL-SQL gần như giữ nguyên, còn V-SQL và V-SQL+ tụt mạnh?**

1. **DAIL-SQL dựa vào ví dụ mẫu.** Model nhỏ chỉ cần bắt chước 7 câu SQL mẫu có cấu trúc tương tự. Đây là việc model nhỏ làm khá tốt.
2. **V-SQL và V-SQL+ bắt model suy luận nhiều bước.** Phải hiểu view, viết SQL trên view, rồi tự dịch ngược về bảng gốc và thêm JOIN.
   Mỗi bước là một cơ hội sai, và model nhỏ sai nhiều hơn ở từng bước.
3. **Các bước mà V-SQL+ làm bằng code** (sinh view, chọn view bằng truy hồi, liên kết giá trị) **không phụ thuộc vào độ mạnh của
   model.** Vì vậy V-SQL+ giảm ít hơn V-SQL (−12,2 so với −18,4 điểm). Bước còn phụ thuộc model, giai đoạn 2, là chỗ mất điểm nhiều
   nhất.

Có 163 câu V-SQL+ đúng trên cả hai model. Riêng qwen3.5:9b còn đúng 38 câu mà gpt-4o-mini sai. Vậy model nhỏ không chỉ "làm được
một phần nhỏ những câu của model lớn", mà đôi khi cũng giải đúng câu khác.

---

## 5. Kết luận

1. **Hai hướng cải tiến của V-SQL+ có hiệu quả** trên cả hai model: tốt hơn V-SQL 5,6 điểm (gpt-4o-mini) và 11,8 điểm (qwen3.5:9b).
2. **So với DAIL-SQL, kết quả phụ thuộc model.** Trên gpt-4o-mini, V-SQL+ hơn 2,4 điểm (chưa đủ bằng chứng thống kê). Trên
   qwen3.5:9b, V-SQL+ kém 6,2 điểm (có ý nghĩa thống kê).
3. **Điểm yếu lớn nhất là giai đoạn 2 của paper** (LLM viết lại SQL về bảng gốc). Trên gpt-4o-mini nó không giúp gì (−4 câu), trên
   qwen3.5:9b nó gây hại rõ (−27 câu). Thay bước này bằng mở rộng tất định:
   - gpt-4o-mini: 53,2%, bản V-SQL+ tốt nhất;
   - qwen3.5:9b: khoảng 45,6%, gần bằng DAIL-SQL.
4. **Liên kết giá trị và chọn view** là hai thành phần đóng góp nhiều nhất của V-SQL+ (mỗi cái khoảng +4 điểm trên gpt-4o-mini).
   **Bầu chọn nhiều mẫu không có ích** và làm tăng gấp đôi chi phí.
5. **V-SQL+ mạnh ở câu nhiều bảng** (từ 3 bảng trở lên) và ở CSDL có tên cột khó hiểu (`financial`). **DAIL-SQL mạnh ở câu đơn
   giản** (1–2 bảng) nhờ ví dụ mẫu.

### Hạn chế cần nói rõ khi báo cáo

- Mỗi cấu hình chỉ chạy **1 lần**. Các chênh lệch dưới khoảng 4–5 điểm có thể thay đổi nếu chạy lại.
- Trên gpt-4o-mini, V-SQL+ chọn view **chỉ bằng BM25** (không có embedding). Trên qwen3.5:9b, V-SQL+ dùng truy hồi lai đầy đủ.
- qwen3.5:9b mới chạy 3 phương pháp chính. Chưa có các biến thể bỏ bớt thành phần, và chưa có biến thể mở rộng tất định (con số
  45,6% ở trên là ước lượng từ kết quả giai đoạn 1).
- DAIL-SQL có lỗi tách SQL đã biết (model trả lời thiếu chữ `SELECT`, nên câu trả lời thành rỗng). Trong hai lần chạy này lỗi chỉ xảy
  ra ở **2 câu** (gpt-4o-mini) và **1 câu** (qwen3.5:9b), không ảnh hưởng đáng kể đến kết luận.
- gpt-4o-mini không phải GPT-4 như trong paper, nên con số tuyệt đối không so trực tiếp với paper được. Chỉ nên so thứ hạng và xu
  hướng.

### Hướng làm tiếp

1. Chạy biến thể mở rộng tất định (`vsqlplus_det`) trên qwen3.5:9b, để xác nhận con số khoảng 45,6%.
2. Thêm vài ví dụ mẫu (few-shot) vào prompt giai đoạn 1 của V-SQL+, để giảm số câu "chạy được mà sai". Đây là điểm mạnh của
   DAIL-SQL mà V-SQL+ chưa có.
3. Bỏ bầu chọn nhiều mẫu để giảm chi phí.
