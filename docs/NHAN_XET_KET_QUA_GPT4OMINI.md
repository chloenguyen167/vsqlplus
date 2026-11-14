# Nhận xét kết quả gpt-4o-mini, 500 câu BIRD mini-dev 2025-07-04 (14/11/2026)

Thư mục kết quả: `results_new/cmp_gpt-4o-mini_d2025/`. Mọi so sánh ghép theo `uid` (vị trí câu trong file), nhiệt độ 0.
V-SQL lần này là cài đặt **impl 7**: một lần gọi LLM chọn view/bảng của D′ theo câu hỏi, rồi chạy Hình 4 và Hình 5 như paper.
Kết quả cũ của V-SQL vẫn được giữ để đối chiếu:
- impl 6 (BM25 chọn 4 đối tượng): `old_predictions_vsql_2.jsonl`;
- impl 5 (đưa hết view): `old_predictions_vsql_1.jsonl`.

## 1. Kết quả chính

| Cấu hình | EX (%) | Riêng giai đoạn 1 (%) | Giai đoạn 2 sửa đúng / làm hỏng | Gọi LLM / câu | Token vào / câu |
|---|---|---|---|---|---|
| V-SQL impl 5 (đưa hết view) | 46.0 | 45.2 | 23 / 19 | 2.00 | 14,412 |
| V-SQL impl 6 (BM25 chọn 4) | 44.6 | 42.0 | 30 / 17 | 2.00 | 12,471 |
| **V-SQL impl 7 (LLM chọn)** | **46.8** | 43.2 | 31 / 13 | 3.00 | **8,219** |
| DAIL-SQL | 50.0 | 49.6 | 23 / 21 | 1.75 | 2,946 |
| V-SQL+ | 52.4 | 53.2 | 11 / 15 | 4.04 | 19,045 |
| V-SQL+ bỏ bầu chọn | 52.6 | 53.4 | 13 / 17 | 1.93 | 5,984 |

Với DAIL-SQL, "giai đoạn 1" là SQL của vòng 1. Với V-SQL và V-SQL+, đó là dummy SQL được mở rộng tất định về bảng gốc (view
được thay bằng CTE), tức kết quả nếu giai đoạn 2 không làm sai gì.

**So với BM25 (impl 6):** để LLM chọn tốt hơn rõ rệt, +2.2 điểm. Số câu mà bảng chính trong đáp án không được chọn (cả bảng lẫn
view `v_<bảng>` của nó đều vắng) giảm từ 210 xuống 120.

**So với đưa hết view (impl 5):** chỉ hơn 0.8 điểm. 32 câu chỉ impl 7 đúng, 28 câu chỉ impl 5 đúng, không có ý nghĩa thống kê. Lợi
ích thật là prompt ngắn hơn khoảng 43%. Riêng giai đoạn 1, impl 7 còn kém impl 5 2 điểm; giai đoạn 2 bù lại.

**So với DAIL-SQL:** thua 3.2 điểm. DAIL đúng riêng 67 câu, V-SQL đúng riêng 51 câu, p McNemar = 0.167. Khác biệt không có ý nghĩa
thống kê, nên chưa thể kết luận DAIL chắc chắn tốt hơn; nhưng V-SQL cũng chưa vượt được DAIL.

**Bước chọn chạy ổn định:**
- Không câu nào phải dùng phương án dự phòng (LLM trả lời đều khớp ít nhất một tên).
- Trung bình chọn 2.4 view/bảng mỗi câu.
- Chỉ 21/500 câu có bảng đáp án nằm ngoài schema đưa vào.

**Câu chỉ dùng 1 bảng (86 câu):** V-SQL đúng 54, DAIL 58, impl 6 là 49. Khoảng cách với DAIL ở nhóm này thu hẹp từ 9 câu xuống 4.

**Chi phí:** lần chạy V-SQL impl 7 dùng khoảng 4.1 triệu token vào và 71 nghìn token ra, tức khoảng 0.66 USD. Các phương pháp khác
lấy từ cache, không tốn thêm.

## 2. Vì sao V-SQL vẫn thua DAIL-SQL

Phần thua nằm chủ yếu ở **giai đoạn 1**: 43.2% so với 49.6% của DAIL. Giai đoạn 2 đang giúp V-SQL (+18 câu ròng), không phải nguyên
nhân. Trong 67 câu chỉ DAIL đúng, 59 câu đã sai ngay từ giai đoạn 1. Xem mẫu các câu thua, có 5 kiểu lỗi:

1. **Thiếu JOIN.** Trong các câu sai, SQL cuối của V-SQL thiếu ít nhất một bảng đáp án ở 123 câu; DAIL chỉ 76. Khoảng 46 câu do bước
   chọn bỏ sót. Phần còn lại do mô hình dùng nhầm view hoặc do Hình 5 viết lại sai JOIN.
   - uid 247, 253 (superhero): mô hình lấy `v_hero_attribute` thay vì `v_superhero`, rồi `eye_colour_id` bị đổi thành `attribute_id`.
   - uid 108: SQL cuối bỏ mất JOIN với `Patient`.
2. **D′ ẩn các bảng tra cứu.** Đây là các bảng chỉ có `id` và một cột giá trị (như `publisher`, `colour`). Khi câu hỏi cần chính cột
   `id` thì mô hình không có cách nào lấy được. Ví dụ uid 261 "publisher ID of Star Trek": mô hình chỉ thấy `publisher_name` trong view
   nên trả về tên thay vì id.
3. **Prompt Hình 4 không nói rõ phải viết SQLite.** 40 dummy SQL dùng hàm của hệ khác như `YEAR(`, `DIVIDE(`; một phần chép từ evidence
   của BIRD (`DIVIDE(COUNT(...), 12)`). Giai đoạn 2 sửa được phần lớn, nhưng 11 câu vẫn còn lỗi đến SQL cuối.
4. **Zero-shot so với 7 ví dụ.** DAIL có ví dụ mẫu nên học được cách trả đúng cột và escape dấu nháy (`'Women''s Soccer'`). Ví dụ uid 140:
   V-SQL trả 7 cột trong khi đáp án chỉ cần `player_name`. Công thức (3) của paper có thành phần ví dụ S, nhưng prompt Hình 4 không có
   chỗ để đặt ví dụ.
5. **Giai đoạn 2 vẫn làm hỏng 13 câu đã đúng.** Ví dụ uid 265: `eye_colour = 'No Colour'` bị đổi thành `eye_colour_id IS NULL`.

**Theo từng CSDL:**
- V-SQL thua nhiều nhất ở superhero và card_games (mỗi nơi 11 câu).
- V-SQL thắng ở formula_1 (12 câu chỉ V-SQL đúng) và financial (31.2% so với 18.8%).
- california_schools thì cả hai đều rất thấp (6.7% và 13.3%), do tên cột có dấu cách và ngoặc như `Enrollment (K-12)`.

### 2.1. Các lý do trên có phải do làm khác paper không?

Phần lớn **không**. Các lý do nằm ở những phần chúng tôi giữ đúng paper, hoặc ở những phần paper không mô tả nên phải tự chọn.

| Lý do | So với paper |
|---|---|
| 1. Thiếu JOIN do bước chọn view bỏ sót | **Phần tự chọn.** Paper chỉ nói schema ở Hình 4 là "related to the query, retrieved from a database" và mục 6 nói "retrieve the correct view description based on the user's query", nhưng không nói chọn bằng cách nào. Bản đưa hết view (không chọn) cũng chỉ đạt 46.0%, nên đây không phải nguyên nhân chính |
| 1'. Thiếu JOIN do Hình 5 viết lại sai | **Giống paper.** Hình 5 giữ nguyên từng chữ |
| 2. D′ ẩn bảng tra cứu | **Diễn giải từ paper.** Hình 1(A) và Hình 3 gộp `colour`, `gender`, `publisher`... vào `v_superhero`. Paper không nói bảng tra cứu còn nằm trong D′ hay không |
| 3. Hình 4 không nhắc SQLite | **Giống paper.** Hình 4 giữ nguyên từng chữ |
| 4. Zero-shot | **Paper không rõ.** Công thức (3) `y = f(x, I, S, D′ \| θ)` có tập ví dụ S, nhưng prompt Hình 4 không có chỗ đặt ví dụ. Chúng tôi theo Hình 4 |
| 5. Giai đoạn 2 làm hỏng câu đúng | **Giống paper.** Mục 4.5: giai đoạn 2 nhận dummy SQL và các bảng mà view dùng |

**Những chỗ khác paper mà không tránh được:**
- **Mô hình.** Paper dùng GPT-4 (`gpt-4-32k`), GPT-4 Turbo và gpt-3.5-turbo. Các model này OpenAI đã tắt ngày 23/10/2026; chúng tôi dùng
  gpt-4o-mini.
  - Bảng 3 của paper với gpt-3.5-turbo: V-SQL 45.4, DAIL-SQL 42.0, tức V-SQL hơn 3.4 điểm.
  - Với GPT-4: V-SQL 56.0, DAIL-SQL 49.0.
  - DAIL-SQL của chúng tôi trên gpt-4o-mini đạt 50.0, ngang mức GPT-4 trong paper, trong khi V-SQL chỉ đạt 46.8.
- **View do tác giả tự thiết kế bằng tay.** Mục 6 của paper: "we referred to the join operations in the ground truth SQL ... and
  manually designed the view creation syntax", và nói thêm rằng tạo view cho mọi phép JOIN trong SQL đáp án "does not necessarily yield
  the best results". Phần kết luận cũng nói "the design of table mappings requires manual effort". Tức là tác giả đã thử nhiều cách thiết kế
  view và chọn cách tốt nhất. Bộ view đó không được công bố, nên chúng tôi dựng view **tự động** từ các phép JOIN trong SQL đáp án theo
  đúng kiểu Hình 3 (mục 5.1). Đây có thể là phần chênh lệch lớn nhất mà không tái hiện được.
- **Cách trình bày schema.** Paper chỉ cho Bảng 6 (4 cột). Chúng tôi thêm mô tả giá trị và giá trị mẫu. Phần này giúp V-SQL, không làm
  V-SQL kém đi.

**DAIL-SQL trong paper có huấn luyện (train) không?** Không.
- Paper V-SQL xếp DAIL-SQL vào nhóm "ICL-based methods" (học trong ngữ cảnh) và ghi "none of the models utilized self-consistency or
  remodification". Công thức (1) ghi rõ tham số mô hình θ được giữ nguyên.
- Bài gốc của DAIL-SQL (Gao và cộng sự, 2023, trích dẫn [6]) là phương pháp thuần prompt + few-shot:
  - schema viết dạng `CREATE TABLE`;
  - chọn ví dụ theo độ giống câu hỏi (đã che tên schema) và độ giống khung SQL;
  - ví dụ chỉ gồm cặp câu hỏi – SQL.
- Bài đó có thí nghiệm fine-tune riêng các LLM mã nguồn mở, nhưng đó không phải DAIL-SQL.
- **Tập train BIRD chỉ dùng làm kho ví dụ để chọn**, không huấn luyện gì. Bản của chúng tôi giữ đúng như vậy: 7 ví dụ, 1 mẫu, không bầu
  chọn. Bộ mã hoá câu hỏi `all-mpnet-base-v2` là mô hình có sẵn, không huấn luyện thêm.

## 3. Vì sao giai đoạn 1 của V-SQL thua DAIL, còn giai đoạn 1 của V-SQL+ lại hơn

### 3.1. Tách từng thay đổi bằng các bản ablation

Các bản ablation cho phép đi từ V-SQL đến V-SQL+ từng bước, mỗi bước chỉ đổi một nhóm thành phần. Số liệu là số câu (trên 500) có SQL
giai đoạn 1 đúng:

| Bước | Cấu hình | Thay đổi so với dòng trên | Gđ1 đúng |
|---|---|---|---|
| 0 | `vsql` | V-SQL: view theo JOIN đáp án, LLM chọn, prompt Hình 4, schema Bảng 6 | 216 |
| 1 | `vsqlplus_fig4` | View tự động + chọn view, bầu chọn, sửa lỗi của V-SQL+; **vẫn prompt Hình 4 và schema Bảng 6** | 217 (+1) |
| 2 | `vsqlplus_all` | **Prompt V-SQL+** và cách trình bày schema của V-SQL+ (đưa hết view; bỏ chọn view, bầu chọn, sửa lỗi; chưa có liên kết giá trị) | 245 (+28) |
| 3 | `vsqlplus_novl` | Thêm chọn view bằng truy hồi và sửa lỗi tên cột/bảng | 251 (+6) |
| 4 | `vsqlplus` | Thêm liên kết giá trị (giá trị trong CSDL khớp câu hỏi) | 266 (+15) |
| | `dailsql` | Vòng 1 của DAIL-SQL | 248 |

Ba kết luận từ bảng này:

- **View không phải nguyên nhân.** Đổi view theo JOIN đáp án sang view tự động, đổi cả cách chọn view, mà giữ prompt Hình 4 thì giai
  đoạn 1 gần như không đổi (216 → 217).
- **Prompt là bước nhảy lớn nhất:** +28 câu, đưa giai đoạn 1 lên ngang DAIL (245 so với 248).
- **Liên kết giá trị và sửa lỗi** (+21 câu) mới giúp V-SQL+ vượt DAIL.

### 3.2. Phân loại lỗi giai đoạn 1

SQL giai đoạn 1 được chạy lại trên CSDL và phân loại lỗi (số câu trên 500):

| Cấu hình | Đúng | Sai tên cột | Hàm không có trong SQLite | Lỗi cú pháp | Lỗi thực thi khác | **Tổng lỗi thực thi** | Chạy được nhưng sai | Có hàm ngoài SQLite trong SQL nháp |
|---|---|---|---|---|---|---|---|---|
| `vsql` | 216 | 33 | 28 | 11 | 3 | **75** | 209 | 40 |
| `vsqlplus_fig4` | 217 | 17 | 35 | 9 | 6 | **67** | 216 | 40 |
| `vsqlplus_all` | 245 | 31 | 5 | 5 | 6 | **47** | 208 | 6 |
| `vsqlplus_novl` | 251 | 5 | 8 | 3 | 12 | **28** | 221 | 8 |
| `vsqlplus` | 266 | 4 | 6 | 3 | 8 | **21** | 213 | 6 |
| `dailsql` | 248 | 44 | 7 | 19 | 0 | **70** | 182 | 14 |

"Lỗi thực thi khác" gộp lỗi sai tên bảng và các lỗi thực thi còn lại. "Chạy được nhưng sai" gộp kết quả rỗng, thừa cột và sai giá trị.

### 3.3. Giải thích

**DAIL-SQL mạnh về hiểu câu hỏi, yếu về lỗi thực thi.**
- 7 ví dụ lấy từ tập train BIRD dạy mô hình cách dùng evidence, cách chọn cột trả về và quy ước của BIRD. Vì vậy DAIL có ít câu
  "chạy được nhưng sai" nhất (182).
- Ngược lại, DAIL chỉ đưa câu lệnh `CREATE TABLE`, không có mô tả cột hay giá trị mẫu. Do đó nó gặp nhiều lỗi sai tên cột (44) và
  lỗi cú pháp (19).

**V-SQL (giai đoạn 1) thua DAIL ở cả hai mặt.**
- *Lỗi thực thi:* tổng xấp xỉ DAIL (75 so với 70) nhưng khác loại. V-SQL có 28 câu dùng hàm không tồn tại trong SQLite. Prompt Hình 4
  không hề nhắc SQLite (chỉ Hình 5 có `{db_type}`), nên mô hình chép nguyên các hàm giả trong evidence của BIRD như `DIVIDE(...)`,
  `SUBTRACT(...)`, `YEAR(...)`.
- *Hiểu câu hỏi:* Hình 4 là zero-shot, nên V-SQL có 209 câu "chạy được nhưng sai", nhiều hơn DAIL 27 câu. Đây là phần thua chính.
  Schema dạng view giúp mô hình bớt phải tự JOIN, nhưng không bù được việc thiếu ví dụ.

**V-SQL+ (giai đoạn 1) hơn DAIL nhờ gần như xoá hết lỗi thực thi, dù vẫn hiểu câu hỏi kém hơn.**
- *Lỗi thực thi:* chỉ 21, so với 70 của DAIL (ít hơn 49 câu). Có ba nguyên nhân:
  - **Prompt V-SQL+** nói rõ "ONE SQLite query", yêu cầu trả về trong khối ```` ```sql ````, và giải thích view (`v_<t>` có đúng một
    dòng cho mỗi dòng của `<t>`, đã chứa cột của bảng tra cứu, nên đa số câu không cần JOIN). Hàm ngoài SQLite giảm từ 35 xuống 5,
    lỗi cú pháp từ 9 xuống 5.
  - **Sửa lỗi tên cột/bảng:** sau khi sinh, SQL được biên dịch thử. Nếu lỗi "no such column", chương trình báo cho mô hình cột đó thật
    sự nằm ở đâu và thêm bảng gốc vào schema. Lỗi sai tên cột giảm từ 31 xuống 5.
  - **Liên kết giá trị:** đưa vào prompt các giá trị trong CSDL khớp với câu hỏi (dạng `- 'Blue' is a value of
    v_superhero.eye_colour`), nên mô hình viết đúng chính tả và đúng hoa thường của giá trị: +15 câu.
- *Hiểu câu hỏi:* V-SQL+ vẫn có 213 câu "chạy được nhưng sai", nhiều hơn DAIL 31 câu. Tức là V-SQL+ **không** hiểu câu hỏi tốt hơn DAIL,
  nó chỉ thắng nhờ ít lỗi thực thi hơn. Lợi thế ròng là +18 câu ở giai đoạn 1 (266 so với 248).

**Hệ quả:**
- Hướng tiếp theo có triển vọng nhất cho V-SQL+ là thêm ví dụ few-shot, vì đó đúng là điểm mạnh còn lại của DAIL. Công thức (3) của
  paper cũng có thành phần S.
- Với `vsql` theo paper thì không sửa: Hình 4 không có chỗ cho ví dụ và không nhắc SQLite. Đó là giới hạn của chính thiết kế được mô tả
  trong paper.

## 4. Nhận xét chung

- Bản V-SQL bám sát paper nhất đạt khoảng 46–47%, thấp hơn DAIL khoảng 3 điểm.
- Paper báo V-SQL 56.0% với GPT-4. Trong khi đó DAIL của chúng tôi (50.0%) khớp với số DAIL trong paper (49.0%). Vậy khoảng cách nằm ở
  phần tái hiện V-SQL, cụ thể là chất lượng giai đoạn 1 với prompt Hình 4 zero-shot. Đổi cách chọn view không giải quyết được phần này.
- V-SQL+ vẫn là phương pháp tốt nhất: 52.4% (bản giải mã tất định `vsqlplus_det` đạt 53.2%) và hơn V-SQL có ý nghĩa thống kê
  (`vsqlplus_det`: p Holm = 0.026).
  - Phần lớn mức tăng đến từ prompt giai đoạn 1 mới: +8.0 điểm so với bản dùng Hình 4.
  - Liên kết giá trị góp thêm +4.2 điểm.
  - Bỏ bầu chọn nhiều mẫu thì kết quả gần như không đổi (52.6%), mà chi phí thấp hơn khoảng 3 lần.

**Lưu ý khi viết báo cáo:**
- Bước LLM chọn view (`P_VSQL_SEL`) là lần gọi thứ 3 do chúng tôi tự thêm; paper không mô tả cách chọn.
- Kiểu lỗi 2 và 3 ở mục 2 là giới hạn của chính thiết kế D′ và prompt Hình 4. Chúng không được sửa trong `vsql` để giữ đúng paper;
  các cải tiến thuộc về V-SQL+.

## 5. Cách tạo view

Cả hai cách đều tạo view kiểu **N-1**: mỗi view `v_<t>` lấy bảng `<t>` làm gốc, rồi `LEFT JOIN` sang các bảng cha theo khoá ngoại. Chỉ nối
khi cột được tham chiếu là duy nhất, nên view có **đúng một dòng cho mỗi dòng của `<t>`**. Sau khi tạo, chương trình kiểm tra lại bằng
SQL rằng `COUNT(*)` của view bằng `COUNT(*)` của bảng gốc; mọi view ở cả 11 CSDL đều đạt. Mã nguồn ở `vsql/autoview.py` và
`vsql/views.py`.

### 5.1. View của V-SQL (tái hiện paper): dựng theo các phép JOIN trong SQL đáp án

Paper (mục 6) tự thiết kế view bằng tay dựa trên các phép JOIN trong SQL đáp án. Bộ view đó không được công bố, nên chúng tôi dựng tự động
theo cùng nguyên tắc (`oracle_views`):

1. Với mỗi SQL đáp án có từ 2 bảng trở lên, lấy tập bảng S của nó và tìm **bảng gốc**: bảng từ đó đi theo khoá ngoại chiều N-1 tới được mọi
   bảng trong S. Ví dụ `superhero` tới được `colour`, `publisher`, `alignment`. Phép JOIN quan hệ 1-N (không có bảng gốc) thì không tạo
   view, vì paper không mô tả view nhân bản dòng.
2. Gộp các tập S có cùng bảng gốc. Mỗi bảng gốc cho một view `v_<gốc>`, chỉ nối tới các bảng từng xuất hiện cùng nó trong SQL đáp án.
3. Viết view đúng kiểu Hình 3:
   - alias là chính tên bảng; bảng nối nhiều lần như `colour` thì dùng tên vai trò `eye_colour`, `hair_colour`;
   - nối theo thứ tự cột khoá ngoại trong bảng;
   - cột id trỏ tới **bảng tra cứu** (bảng chỉ có `id` và một cột giá trị như `colour`, `gender`) được **thay tại chỗ** bằng giá trị:
     `gender_id` → `gender`, `eye_colour_id` → `eye_colour`;
   - khoá ngoại có ý nghĩa (như `Patient.ID`, `raceId`, `molecule_id`) được giữ.

   Kết quả là `v_superhero` trùng đúng 12 cột theo thứ tự của Hình 3.
4. **D′** = mọi view + các bảng không phải bảng gốc của view và không phải bảng tra cứu đã được gộp vào view. Như vậy chỉ `colour`, `gender`,
   `race`... biến mất (Hình 1(A)); các bảng thực thể như `Patient`, `cards`, `users` vẫn còn để hỏi trực tiếp.
5. Trình bày trong prompt kiểu Bảng 6 của paper (`original_column_name | column_name | column_description | data_format`), thêm 2 cột
   `value_description | example_values` lấy từ file mô tả cột của BIRD và từ dữ liệu.

Số view: 2–8 view mỗi CSDL, tổng cộng 46 view (bảng thống kê view trong `summary.md`).

**Lưu ý:** cách này nhìn SQL đáp án của **cả 500 câu** để chọn bảng nào được nối, đúng như paper làm. Đây là lợi thế mà DAIL-SQL và V-SQL+
không có.

### 5.2. View tự động của V-SQL+: dựng theo khoá ngoại, không nhìn SQL đáp án

`auto_views` tạo một view cho **mọi bảng có khoá ngoại**, chỉ dựa vào schema:

1. Đi theo khoá ngoại N-1 tối đa 2 mức (`--depth 2`). Từ mức 2 trở đi chỉ nối các bảng tra cứu nhỏ (≤ 4 cột) để view gọn. Mỗi view tối đa
   60 cột (`--max-cols 60`).
2. Tên cột rõ nghĩa:
   - `colour.colour` qua `eye_colour_id` thành `eye_colour`;
   - `link_to_major` thành `major`;
   - cột trùng tên thì thêm tiền tố vai trò (`away_team_team_long_name`).
3. **Giữ cả cột id lẫn cột giá trị** (khác V-SQL): `eye_colour_id` vẫn còn, `eye_colour` được thêm vào. Nhờ vậy câu hỏi hỏi đúng id (như uid
   261 "publisher ID") vẫn trả lời được.
4. **Mọi bảng không phải bảng gốc của view vẫn hiện**, kể cả bảng tra cứu, để hỏi trực tiếp (ví dụ đếm số nhà xuất bản).
5. Trình bày dạng `CREATE VIEW`. Mỗi cột có chú thích: lấy từ đâu (`colour.colour via superhero.eye_colour_id`), mô tả cột và giá trị mẫu.
6. CSDL thiếu khai báo khoá ngoại (`debit_card_specializing`): suy thêm 3 khoá ngoại theo tên cột và dữ liệu.

Số view: 1–8 view mỗi CSDL, tổng cộng 42 view. Với 9/11 CSDL, số view bằng với V-SQL (cùng bảng gốc) nhưng nội dung view khác.

## 6. Prompt đưa vào LLM ở từng giai đoạn

Câu ví dụ trong mục này là uid 259 (superhero): "What is the percentage of superheroes who act in their own self-interest or make decisions
based on their own moral code? Indicate how many of the said superheroes were published by Marvel Comics." DAIL-SQL sai, cả hai bản V-SQL
và V-SQL+ đúng. Xem đầy đủ từng prompt bằng notebook `notebooks/Demo_VSQL_VSQLplus.ipynb` (câu đầu tiên trong danh sách demo).

### 6.1. DAIL-SQL: 2 vòng, cùng một khuôn prompt

```
/* Some SQL examples are provided based on similar problems: */
/* Answer the following: <câu hỏi ví dụ 1 + evidence> */
<SQL ví dụ 1>
... (7 ví dụ lấy từ tập train BIRD)
/* Given the following database schema: */
<câu CREATE TABLE của mọi bảng, lấy nguyên từ sqlite_master>
/* Answer the following: <câu hỏi + evidence> */
SELECT 
```

- **Vòng 1:** 7 ví dụ có câu hỏi (đã che tên bảng/cột) gần câu hỏi hiện tại nhất theo embedding `all-mpnet-base-v2`, khoảng cách Euclid.
- **Vòng 2:** ưu tiên các ví dụ có khung SQL giống khung của SQL vòng 1 (Jaccard ≥ 0.85), vẫn theo thứ tự trên. Trùng 7 ví dụ thì prompt
  trùng, không gọi lại.
- Câu trả lời được ghép sau `SELECT `. Với gpt-4o-mini, mô hình thường viết thêm giải thích; chương trình tự lấy khối SQL.

Ví dụ uid 259: các ví dụ chọn được đều là câu tính phần trăm (`CAST(SUM(CASE WHEN ...) AS REAL) * 100 / COUNT(*)`). Nhưng schema chỉ có
`superhero.alignment_id`, nên mô hình viết `T1.alignment` (cột không tồn tại) và bị lỗi `no such column`.

### 6.2. V-SQL: chọn view (tự thêm), giai đoạn 1 (Hình 4), giai đoạn 2 (Hình 5)

**Lần 0, chọn view/bảng: `P_VSQL_SEL`, tự thêm, chỉ có ở `--vsql-select llm`.**

```
# target
You are an experienced database administrator. Select the views and tables in "db objects" that are needed to answer "question" by sql.
notice:
1. A view `v_<t>` has exactly one row per row of table <t> and adds columns taken from related tables.
2. Select every object the sql needs, and no others.
3. Answer with the object names only, one per line, without explanation.

# db objects
view v_hero_attribute (rows of table hero_attribute): hero_id, superhero_name, full_name, gender, eye_colour_id, ...
view v_hero_power (rows of table hero_power): hero_id, superhero_name, full_name, gender, eye_colour, ...
view v_superhero (rows of table superhero): id, superhero_name, full_name, gender, eye_colour, hair_colour, skin_colour, race, publisher_name, alignment, height_cm, weight_kg

# question
<câu hỏi>
<evidence>
```

Ví dụ uid 259: LLM trả về `v_superhero` (351 token vào).

**Lần 1, giai đoạn 1: Hình 4, nguyên văn.**

```
# target
You are an experienced database administrator, please answer "question" by sql with no explanation.
notice:
1. Do not alias the output fields
2. must avoid ambiguous column name by using table name and column name in the SQL statement. For example, use `table_name.column_name` instead of just `column_name`.
3. refer to "relevant db schema"

# relevant db schema
# view: v_superhero
original_column_name | column_name | column_description | data_format | value_description | example_values
id | id | the unique identifier of the superhero | integer |  | example values are [1, 2, 3]
gender | gender | the gender of the superhero | text |  | all possible values are ['Male', 'Female', 'N/A']
alignment | alignment | the alignment of the superhero | text | Alignment refers to ... | ...
...

# question
<câu hỏi>
<evidence>
```

- `{relevant_db_schema}` là các view/bảng đã chọn (bản `all`: mọi đối tượng của D′), trình bày theo Bảng 6 mở rộng.
- `{query}` là câu hỏi, nối thêm evidence của BIRD ở dòng sau.

Ví dụ uid 259 (897 token vào): mô hình viết `... FROM v_superhero WHERE v_superhero.alignment = 'Bad'`, không cần JOIN.

**Lần 2, giai đoạn 2: Hình 5, nguyên văn (kể cả lỗi chính tả "foramt"); `{db_type}` = SQLite.**

````
# target
According to the "views schemas", "view query" and "relevant table schemas", restore the sql in view query to one used the original table query without explanation
notice:
1. SQL should contain "join" as little as possible.
2. table in "views schemas" should not be contained in output.
3. comply with the syntax of SQLite.
4. must avoid ambiguous column name by using table name and column name in the SQL statement. ...

# view schemas
create view v_superhero as select `superhero`.`id`, ..., `alignment`.`alignment`, ... from `superhero`
left join `publisher` on ... left join `alignment` on `superhero`.`alignment_id` = `alignment`.`id` ...

# view query
Question: <câu hỏi + evidence>
```sql
<dummy SQL của giai đoạn 1>
```

# relevant table schemas
# table: alignment ...   # table: publisher ...   # table: superhero ...

# foramt
```sql
{sql}
```
````

- `{view_schemas}` là câu `CREATE VIEW` (kiểu Hình 3) của các view mà dummy SQL dùng.
- `{table_schemas}` chỉ gồm các bảng có cột thật sự được dummy SQL dùng, theo quy tắc ánh xạ của view (mục 4.5 của paper). Ở uid 259 là
  `alignment`, `publisher`, `superhero`; không có `colour`, `race`, `gender`.
- Ví dụ uid 259: mô hình khôi phục đúng `JOIN publisher ... JOIN alignment ... WHERE alignment.alignment = 'Bad'`.

### 6.3. V-SQL+ (bản bỏ bầu chọn): giai đoạn 1 (prompt V-SQL+), sửa lỗi, giai đoạn 2 (Hình 5)

**Chọn view, không gọi LLM:**
- CSDL nhỏ (≤ 4 đối tượng hoặc schema ≤ 3.500 token) thì đưa hết.
- Ngược lại, xếp hạng các view/bảng bằng hợp nhất RRF của 3 danh sách:
  - BM25 trên từng cột, gộp lên view;
  - BM25 trên từng view;
  - liên kết giá trị và tên cột được nhắc thẳng, trọng số 2.
- Giữ top 4, cộng tối đa 2 đối tượng chứa giá trị khớp mạnh.

(Bản `vsqlplus` đầy đủ thêm bước bầu chọn: 4 dummy SQL trên 5 ứng viên, chọn tập view dùng nhiều nhất.)

**Lần 1, giai đoạn 1: `P_PLUS`.**

```
# target
You are an experienced database administrator, please answer "question" by ONE SQLite query with no explanation.
The schema contains VIEWS and TABLES. A view `v_<t>` has exactly one row per row of table <t> and already contains the
columns of the lookup tables of <t> (the comment of each column tells where it comes from), so most questions need no JOIN.
notice:
1. Query views exactly like tables. Use only the views, tables and columns listed in "relevant db schema".
2. To count or list the rows of a table that has no view, query that table directly.
3. must avoid ambiguous column name by using `name.column`; quote names with spaces or special characters by backticks.
4. Use the matched database values exactly as written (same spelling and case).
# relevant db schema
CREATE VIEW v_superhero (  -- one row per row of table superhero
  id INTEGER,  -- the unique identifier of the superhero; e.g. 1, 2, 3
  alignment_id INTEGER,  -- the id of the superhero's alignment; e.g. 1, 2, 3
  ...
  publisher_name TEXT,  -- publisher.publisher_name via superhero.publisher_id; the name of the publisher; e.g. '', 'ABC Studios', 'Dark Horse Comics'
  alignment TEXT,  -- alignment.alignment via superhero.alignment_id; the alignment of the superhero; ...; e.g. 'Good', 'Bad', 'Neutral'
);
CREATE TABLE alignment ( ... );  ...
# matched database values
- 'Bad' is a value of v_hero_attribute.alignment, v_hero_power.alignment, v_superhero.alignment
- 'Marvel Comics' is a value of v_hero_attribute.publisher_name, v_hero_power.publisher_name, v_superhero.publisher_name
# question
<câu hỏi>
# evidence
<evidence>

Return only the SQL inside a ```sql code block.
```

Khác với Hình 4:
- nói rõ SQLite;
- giải thích view;
- schema dạng `CREATE VIEW` có chú thích nguồn gốc cột;
- có mục `# matched database values` (liên kết giá trị: so n-gram của câu hỏi và evidence với giá trị văn bản thật trong CSDL);
- evidence là một mục riêng;
- yêu cầu khối ```` ```sql ````.

Ví dụ uid 259: superhero chỉ có 10 đối tượng nhưng schema ngắn nên đưa hết (3.422 token vào). Mô hình viết thẳng trên `v_superhero`,
không JOIN.

**Lần 1b, sửa lỗi (nếu có).** Sau khi sinh, dummy SQL được mở rộng tất định thành CTE và biên dịch thử (`EXPLAIN`). Nếu lỗi `no such
column/table` thì gửi lại cùng prompt, thêm bảng gốc chứa cột đó và ghi chú:

```
# note
Your previous query failed: `<tên>` does not exist where you used it. It exists as: <view.cột, ...>. The original table(s) <bảng> are added to the schema; join them on their key columns if needed.
```

Tối đa 2 lần; trên 500 câu trung bình 0,05 lần mỗi câu.

**Lần 2, giai đoạn 2:** cùng prompt Hình 5 như V-SQL. Nhưng chỉ chạy khi dummy SQL dùng view (88% số câu), và `{table_schemas}` gồm mọi bảng
mà các view được dùng nối tới.
