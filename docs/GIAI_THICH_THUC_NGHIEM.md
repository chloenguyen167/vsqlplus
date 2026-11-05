# Giải thích thực nghiệm: tái hiện V-SQL và hướng cải tiến của nhóm

Tài liệu này giải thích, theo cách dễ hiểu nhất có thể:

1. **Bài báo V-SQL làm gì** và vì sao nó đáng để kiểm chứng.
2. **Nhóm tái hiện thực nghiệm của bài báo như thế nào**: dùng dữ liệu gì, chạy ra sao, chấm điểm thế nào, và tại sao từng bước
   lại làm như vậy.
3. **Hướng cải tiến nhóm chọn**: vì sao chọn, cách làm cụ thể, và kết quả đo được trên hai mô hình `qwen3.5:0.8b` (rất nhỏ)
   và `qwen3.5:9b` (cỡ vừa).

Các thuật ngữ chuyên ngành được giải thích ngay chỗ xuất hiện lần đầu (trong các khung **"Thuật ngữ"**), và được gom lại ở
[Phụ lục A](#phụ-lục-a-bảng-thuật-ngữ).

---

## Tóm tắt nhanh (đọc 1 phút)

- Bài báo V-SQL cho rằng mô hình ngôn ngữ lớn (LLM) hay viết sai tên cột, tên bảng khi phải nối nhiều bảng, nên đề xuất
  **gộp các bảng thành "view"** cho mô hình dễ hiểu, rồi **dịch ngược** câu SQL về bảng gốc.
- Nhóm **tái hiện** cách làm này trên bộ BIRD mini-dev (500 câu hỏi) với mô hình mã nguồn mở Qwen. Kết quả:
  **V-SQL không tốt hơn cách làm thông thường**, mà còn kém hơn khoảng 5 điểm phần trăm, và lỗi sai tên còn **tăng** chứ
  không giảm.
- Nhóm nhận thấy: khi SQL sai tên, **cơ sở dữ liệu tự báo chính xác tên nào sai**. Vì vậy nhóm đề xuất hai cải tiến:
  - **CT5 – Sửa lỗi theo lược đồ**: chạy thử SQL, đọc thông báo lỗi, tự thay bằng tên đúng. Không cần gọi thêm mô hình.
  - **CT7 – Bỏ phiếu theo kết quả thực thi**: sinh 4 câu SQL từ 4 cách mô tả cơ sở dữ liệu khác nhau, chạy cả 4, chọn kết quả
    xuất hiện nhiều nhất.
- Kết quả trên `qwen3.5:9b` (498 câu):

  | Cách làm | Độ chính xác (EX) |
  |---|---|
  | Cách thông thường (`base`) | 46,2% |
  | V-SQL (tái hiện bài báo) | 41,0% |
  | Cách thông thường + CT5 | **49,0%** (tăng 2,8 điểm, có ý nghĩa thống kê) |
  | CT7 bỏ phiếu (đã gồm CT5) | **49,6%** (cao nhất, nhưng chỉ hơn "base + CT5" 0,6 điểm) |

- Kết luận trung thực: **CT5 giúp chắc chắn** ở cả mô hình nhỏ và mô hình vừa, với chi phí gần như bằng 0. **CT7 giúp rõ ở
  mô hình nhỏ**, còn với mô hình 9B thì phần lớn lợi ích của nó đã nằm trong CT5, trong khi chi phí gấp 4 lần.

---

## Mục lục

1. [Bối cảnh: bài toán Text-to-SQL](#1-bối-cảnh-bài-toán-text-to-sql)
2. [Bài báo V-SQL đề xuất gì](#2-bài-báo-v-sql-đề-xuất-gì)
3. [Tái hiện thực nghiệm của bài báo](#3-tái-hiện-thực-nghiệm-của-bài-báo)
4. [Kết quả tái hiện và nhận xét](#4-kết-quả-tái-hiện-và-nhận-xét)
5. [Hướng cải tiến: vì sao nhóm chọn](#5-hướng-cải-tiến-vì-sao-nhóm-chọn)
6. [CT5 – Sửa lỗi theo lược đồ](#6-ct5--sửa-lỗi-theo-lược-đồ-schema-guard)
7. [CT7 – Bỏ phiếu theo kết quả thực thi](#7-ct7--bỏ-phiếu-theo-kết-quả-thực-thi)
8. [Kết quả các cải tiến](#8-kết-quả-các-cải-tiến)
9. [Hạn chế và hướng tiếp theo](#9-hạn-chế-và-hướng-tiếp-theo)
10. [Phụ lục](#phụ-lục-a-bảng-thuật-ngữ)

---

## 1. Bối cảnh: bài toán Text-to-SQL

### 1.1. Bài toán là gì?

Người dùng hỏi bằng tiếng tự nhiên, máy phải viết ra câu lệnh truy vấn cơ sở dữ liệu để trả lời. Ví dụ:

> **Câu hỏi:** "Có bao nhiêu siêu anh hùng mắt xanh và tóc vàng?"
>
> **Câu SQL cần viết:**
> ```sql
> SELECT COUNT(*)
> FROM superhero
> JOIN colour AS eye  ON superhero.eye_colour_id  = eye.id
> JOIN colour AS hair ON superhero.hair_colour_id = hair.id
> WHERE eye.colour = 'Blue' AND hair.colour = 'Blond';
> ```

> **Thuật ngữ**
> - **SQL**: ngôn ngữ dùng để hỏi dữ liệu từ cơ sở dữ liệu (CSDL). `SELECT ... FROM ... WHERE ...` nghĩa là "lấy ... từ bảng
>   ... với điều kiện ...".
> - **Bảng (table)**: dữ liệu được lưu thành nhiều bảng, mỗi bảng có nhiều **cột** (column), ví dụ bảng `superhero` có cột
>   `superhero_name`, `eye_colour_id`.
> - **Lược đồ (schema)**: "bản đồ" của CSDL, tức danh sách các bảng, các cột trong mỗi bảng và cách các bảng liên kết với nhau.
> - **Text-to-SQL**: tên gọi của bài toán chuyển câu hỏi tự nhiên (text) thành câu lệnh SQL.
> - **LLM (Large Language Model – mô hình ngôn ngữ lớn)**: các mô hình như ChatGPT, GPT-4, Qwen… Ta đưa cho nó lược đồ và câu
>   hỏi (gọi là **prompt**), nó viết ra SQL.

### 1.2. Vì sao khó? Khóa ngoại và phép JOIN

Để tránh lặp dữ liệu, CSDL thường tách thông tin ra nhiều bảng. Ví dụ bảng `superhero` không lưu chữ "Blue" mà chỉ lưu
`eye_colour_id = 7`; chữ "Blue" nằm ở bảng `colour` tại dòng có `id = 7`. Muốn biết màu mắt thật, phải **nối** (JOIN) hai bảng.

> **Thuật ngữ**
> - **Khóa ngoại (foreign key, FK)**: cột ở bảng này "trỏ" sang một dòng ở bảng khác. `superhero.eye_colour_id` là khóa ngoại
>   trỏ sang `colour.id`.
> - **JOIN (phép nối)**: ghép dòng của hai bảng dựa trên khóa ngoại.
> - **Quan hệ nhiều-một (N-1)**: nhiều siêu anh hùng cùng có một màu mắt; mỗi siêu anh hùng chỉ có đúng một màu mắt. Nối theo
>   chiều này **không làm tăng số dòng**.
> - **Quan hệ một-nhiều (1-N)**: một siêu anh hùng có nhiều siêu năng lực. Nối theo chiều này **làm nhân bản dòng** (một siêu
>   anh hùng xuất hiện nhiều lần), dễ làm sai các phép đếm `COUNT`, cộng `SUM`.

Khi phải viết nhiều JOIN, LLM hay nhầm: gán cột vào sai bảng, bịa ra tên cột gần giống tên thật, dùng bí danh (alias) không tồn
tại… Câu SQL khi chạy sẽ báo lỗi kiểu `no such column: hero_attribute.attribute_name` (không có cột này).

> **Thuật ngữ**
> - **Ảo giác lược đồ (schema hallucination)**: mô hình "tưởng tượng" ra tên bảng/cột không có thật, hoặc gán cột vào sai bảng.
>   Trong tài liệu này, ta đếm ảo giác lược đồ bằng số câu SQL bị CSDL báo một trong ba lỗi: `no such column` (không có cột),
>   `no such table` (không có bảng), `ambiguous column` (tên cột mơ hồ, có ở nhiều bảng mà không nói rõ bảng nào).
> - **Alias (bí danh)**: tên tắt đặt cho bảng trong câu SQL, ví dụ `FROM superhero AS s` thì sau đó viết `s.superhero_name`.

### 1.3. Bộ dữ liệu BIRD mini-dev và thước đo EX

Bài báo (và nhóm) đánh giá trên **BIRD mini-dev**: 500 câu hỏi trên 11 CSDL thật (trường học, đua xe F1, ngân hàng, bệnh án…),
chia theo độ khó: 148 câu dễ (simple), 250 câu trung bình (moderate), 102 câu khó (challenging). Mỗi câu có sẵn **SQL đáp án**
(gold SQL) và một đoạn **evidence** (gợi ý kiến thức, ví dụ "mắt xanh nghĩa là `colour = 'Blue'`").

> **Thuật ngữ**
> - **BIRD**: một bộ dữ liệu chuẩn (benchmark) nổi tiếng cho Text-to-SQL, gồm các CSDL lớn, "bẩn" như ngoài thực tế. Bản
>   **mini-dev** là bản rút gọn 500 câu để thử nghiệm nhanh.
> - **EX (Execution Accuracy – độ chính xác thực thi)**: tỉ lệ câu hỏi mà **kết quả chạy** SQL của mô hình **trùng** với kết quả
>   chạy SQL đáp án. Không cần câu SQL giống hệt, chỉ cần ra cùng một tập dòng kết quả. Đây là thước đo chính của BIRD và của
>   bài báo.

*Đính chính (11/2026):* các bảng kết quả trong tài liệu này tính trên **498 câu** do mã cũ gộp các dòng theo `question_id`. Bộ mini-dev có **500 dòng**: `question_id` 137 và 138 mỗi mã xuất hiện hai lần (dòng 484≡487, 485≡488, nội dung giống hệt), và bộ chấm chính thức của BIRD cũng như Bảng 2 của paper (148/250/102) đều tính đủ 500. Mã mới (`run_compare.py`, `run_experiment.py`) định danh câu theo vị trí nên tính đủ 500 câu. Xem `docs/TAI_HIEN_DUNG_VA_VSQLPLUS.md`.

---

## 2. Bài báo V-SQL đề xuất gì

Bài báo: *V-SQL: A View-based Two-stage Text-to-SQL Framework* (Zeshun You và cộng sự, arXiv:2502.15686).

### 2.1. Ý tưởng: gộp bảng thành "view"

Tác giả cho rằng LLM viết sai vì **không hiểu rõ khóa ngoại**. Vậy thì làm sẵn các phép nối cho nó: gộp mỗi bảng chính với các
bảng tra cứu của nó thành một **view**.

> **Thuật ngữ**
> - **View**: một "bảng ảo", được định nghĩa bằng một câu `SELECT`. Ví dụ view `v_superhero` = bảng `superhero` đã nối sẵn với
>   `colour`, `gender`, `race`, `publisher`. Nhìn vào view, mô hình thấy ngay cột `eye_colour` (giá trị "Blue") thay vì phải
>   tự nối `eye_colour_id` sang bảng `colour`.

Với view, câu hỏi ở mục 1.1 chỉ còn là:

```sql
SELECT COUNT(*) FROM v_superhero WHERE eye_colour = 'Blue' AND hair_colour = 'Blond';
```

Ngắn hơn, không còn JOIN, nên (theo tác giả) mô hình ít viết sai hơn.

### 2.2. Hai giai đoạn

Nhưng view không có thật trong CSDL, nên câu SQL trên view phải được dịch lại về bảng gốc. V-SQL làm như sau:

| Bước | Ai làm | Việc | Kết quả |
|---|---|---|---|
| 0. Ánh xạ bảng | Người/LLM, làm 1 lần cho mỗi CSDL | Thiết kế các view | Các lệnh `CREATE VIEW` |
| 1. Sinh SQL nháp | LLM | Viết SQL trên **view** (không chạy câu này) | SQL nháp ngắn, gọi là *dummy SQL* |
| 2. Tái tạo SQL | LLM (lần gọi thứ hai) | Đọc định nghĩa view + bảng gốc, **viết lại** SQL nháp thành SQL trên bảng gốc | SQL cuối, được chạy trên CSDL |

Tác giả ví quy trình này như "nén rồi giải nén": bước 1 nén câu hỏi thành SQL ngắn gọn, bước 2 giải nén ra SQL đầy đủ.

### 2.3. Kết quả bài báo công bố

Bài báo dùng GPT-3.5-turbo, GPT-4, GPT-4-turbo (nhiệt độ 0, tối đa 800 token trả lời), so với DIN-SQL, DAIL-SQL, TA-SQL:

| Mô hình | DIN-SQL | DAIL-SQL | TA-SQL | **V-SQL** |
|---|---|---|---|---|
| GPT-4 | 47,2 | 49,0 | **56,17** | 56,0 |
| GPT-4-turbo | 47,8 | 48,8 | 50,16 | **52,8** |
| GPT-3.5-turbo | 39,2 | 42,0 | 43,8 | **45,4** |

> **Thuật ngữ**
> - **Nhiệt độ (temperature) = 0**: cho mô hình luôn chọn câu trả lời "chắc chắn nhất", nên cùng một prompt luôn ra cùng một
>   kết quả. Nhờ vậy thí nghiệm có thể lặp lại.
> - **Token**: đơn vị chữ mà mô hình đọc/viết (khoảng 3–4 ký tự tiếng Anh). Số token quyết định chi phí và thời gian.

### 2.4. Những điểm nhóm thấy cần kiểm chứng

Phân tích chi tiết nằm trong báo cáo của nhóm (thư mục `docs/`). Tóm lại:

- **Bài báo không đo xem view có thật sự làm giảm lỗi sai tên không**, dù đó là giả thuyết chính.
- **Chênh lệch quá nhỏ** (1,6–2,6 điểm) so với dao động ngẫu nhiên của 500 câu (khoảng ±2,2 điểm), và không có kiểm định
  thống kê.
- **View được thiết kế dựa trên SQL đáp án của chính tập kiểm tra** (bài báo tự nói trong phần thảo luận). Đây là một dạng
  "nhìn trộm đáp án" mà các phương pháp so sánh không có.
- **Giai đoạn 2 lại giao việc viết JOIN cho LLM**, đúng loại việc mà bài báo cho là LLM làm kém.

Vì vậy nhóm quyết định **tái hiện lại** để tự đo, thay vì tin ngay vào con số công bố.

---

## 3. Tái hiện thực nghiệm của bài báo

### 3.1. Mục tiêu của việc tái hiện

Câu hỏi nhóm muốn trả lời: **"Nếu làm đúng như bài báo mô tả, trên cùng bộ dữ liệu, V-SQL có tốt hơn cách sinh SQL thông
thường không, và có thật sự giảm lỗi sai tên không?"**

Để trả lời công bằng, nhóm so sánh hai cách làm **trên cùng mô hình, cùng câu hỏi, cùng cách chấm**:

| Tên cấu hình | Cách làm | Vai trò |
|---|---|---|
| `base` | Đưa toàn bộ lược đồ gốc + câu hỏi cho LLM, LLM viết SQL **một lần** | Mốc so sánh (baseline) |
| `vsql` | Làm đúng 2 giai đoạn của bài báo (mục 2.2) | Tái hiện bài báo |

> **Thuật ngữ**
> - **Baseline (mốc so sánh)**: cách làm đơn giản nhất, dùng để xem phương pháp mới có hơn được nó không. Nếu một phương pháp
>   phức tạp mà không hơn baseline thì không đáng dùng.
> - **Zero-shot**: không cho mô hình xem ví dụ mẫu nào, chỉ đưa lược đồ và câu hỏi.

### 3.2. Những điểm giống và khác bài báo (và lý do)

Không thể sao chép 100% bài báo, vì một số thứ tác giả không công bố. Bảng dưới ghi rõ nhóm làm gì ở từng điểm, và **tại sao**.

| Hạng mục | Bài báo | Nhóm làm | Lý do |
|---|---|---|---|
| Dữ liệu | BIRD mini-dev, 500 câu, SQLite | **Giống** | Để so sánh được |
| Thước đo | EX | **Giống** (cộng thêm phân loại lỗi, chi phí, kiểm định thống kê) | EX để so với bài báo; phần thêm để kiểm chứng các nhận định mà bài báo chưa đo |
| Nhiệt độ, độ dài trả lời | 0; 800 token | **Giống** (temperature 0, `num_predict` 800) | Kết quả lặp lại được |
| Mô hình | GPT-3.5 / GPT-4 (trả phí) | **Qwen** chạy trên máy/Colab qua Ollama: `qwen3.5:0.8b`, `qwen3.5:9b` (thêm một lần chạy thử `qwen3:8b` trên 103 câu) | Miễn phí, chạy được hết 500 câu nhiều lần. Hệ quả: **số tuyệt đối không so trực tiếp với bài báo**, chỉ so các cấu hình với nhau trong cùng một lần chạy |
| View | Thiết kế thủ công dựa trên JOIN trong SQL đáp án; **không công bố** | Viết thuật toán `oracle_views` mô phỏng đúng quy trình đó (mục 3.4) | Không có view gốc nên phải tự tạo, nhưng giữ đúng tinh thần "dựa theo đáp án" |
| Prompt | Có trong phụ lục | Viết lại theo mô tả, không chép nguyên văn | Prompt gốc viết cho GPT; chỉnh cho đúng định dạng SQLite và mô hình Qwen |
| Evidence, giá trị mẫu | Không nói rõ | **Bật cho mọi cấu hình**: có evidence, 3 giá trị mẫu mỗi cột | Công bằng giữa các cấu hình |
| DIN-SQL, DAIL-SQL, TA-SQL | Có so sánh | Không cài lại, chỉ có `base` | Ngoài phạm vi; mục tiêu là kiểm tra đóng góp của view |

> **Thuật ngữ**
> - **Ollama**: phần mềm miễn phí để chạy LLM mã nguồn mở trên máy cá nhân hoặc GPU của Google Colab.
> - **Qwen (qwen3.5:0.8b, qwen3.5:9b)**: họ mô hình mã nguồn mở của Alibaba. "0.8b", "9b" là số tham số (0,8 tỷ và 9 tỷ). Mô
>   hình càng nhiều tham số thường càng "thông minh" nhưng chạy càng chậm, càng tốn bộ nhớ GPU.
> - **Giá trị mẫu (sample values)**: vài giá trị thật của mỗi cột được in kèm trong prompt (ví dụ `colour: 'Blue', 'Red',
>   'Green'`), để mô hình biết dữ liệu trông như thế nào.

### 3.3. Một câu hỏi được xử lý ra sao

**Cấu hình `base` (1 lần gọi LLM):**

```
Bạn là chuyên gia SQLite. Viết MỘT câu SQLite trả lời câu hỏi dựa trên lược đồ dưới đây.
### Database schema      <- toàn bộ bảng gốc, kèm 3 giá trị mẫu mỗi cột
### Question             <- câu hỏi
### External knowledge   <- evidence của BIRD
Chỉ trả về SQL trong khối ```sql.
```

Chương trình lấy câu SQL trong câu trả lời, chạy trên CSDL, so kết quả với đáp án.

**Cấu hình `vsql` (thường 2 lần gọi LLM):**

1. **Giai đoạn 1**: prompt chứa các **view** (và những bảng không thuộc view nào). Mô hình viết SQL nháp trên view.
2. **Giai đoạn 2**: chương trình tìm xem SQL nháp dùng những view nào, rồi đưa cho mô hình: định nghĩa của **đúng các view đó**,
   các **bảng gốc** liên quan, câu hỏi, và SQL nháp. Mô hình viết lại thành SQL trên bảng gốc.
3. Nếu SQL nháp không dùng view nào (nó đã viết thẳng trên bảng gốc) thì dùng luôn SQL nháp làm SQL cuối, không gọi lần 2.
   (Với `qwen3.5:9b` chỉ có 9/500 câu rơi vào trường hợp này, nên trung bình `vsql` tốn 1,98 lần gọi mỗi câu.)

Mã nguồn: [`vsql/pipeline.py`](../vsql/pipeline.py) (các prompt `P_BASE`, `P_VIEW`, `P_RECON` và hàm `run_item`).

### 3.4. Tạo view kiểu bài báo (`oracle_views`)

Vì bài báo không công bố view, nhóm viết thuật toán làm đúng quy trình bài báo mô tả: **nhìn vào các phép JOIN trong SQL đáp
án** của từng CSDL rồi tạo view cho chúng. Cụ thể ([`vsql/views.py`](../vsql/views.py), hàm `oracle_views`):

1. Với mỗi SQL đáp án dùng từ 2 bảng trở lên, lấy tập bảng đó.
2. Nếu từ một bảng "gốc" có thể đi theo khóa ngoại (chiều nhiều-một) tới tất cả các bảng còn lại → gộp vào view của bảng gốc
   đó, nối bằng `LEFT JOIN`.
3. Các nhóm bảng phải nối theo chiều một-nhiều (không đi được bằng chiều nhiều-một) → tạo tối đa 3 view loại này cho nhóm hay
   gặp nhất, và **đánh dấu "có thể nhân bản dòng"** trong prompt.
4. **Kiểm tra tự động**: với view nhiều-một, đếm số dòng của view phải bằng số dòng bảng gốc. Nếu khác là view sai.

> **Thuật ngữ**
> - **Oracle** (trong học máy): thông tin "biết trước đáp án". Gọi là `oracle_views` để nhắc rằng các view này được thiết kế
>   nhờ nhìn đáp án, tức là V-SQL được **ưu ái hơn** các cấu hình khác. Dù vậy, như sẽ thấy ở mục 4, V-SQL vẫn không vượt baseline.
> - **LEFT JOIN**: phép nối giữ lại mọi dòng của bảng bên trái, kể cả khi không tìm thấy dòng khớp ở bảng bên phải (khi đó cột
>   bên phải để trống). Khác với `JOIN` (INNER JOIN) chỉ giữ những dòng khớp.

Thống kê view tạo được (11 CSDL): ví dụ `formula_1` có 13 bảng, 19 khóa ngoại → 8 view; `financial` có 10 view, trong đó 3 view
có thể nhân bản dòng. Toàn bộ view nhiều-một đều qua bước kiểm tra số dòng. Chi tiết ở mục 6 của file `summary.md` trong mỗi
thư mục kết quả.

### 3.5. Chấm điểm và đo lường

Mỗi câu SQL cuối được chạy trên CSDL SQLite (chế độ chỉ đọc, giới hạn 30 giây; SQL đáp án được 120 giây) và được xếp vào
**đúng một** nhóm:

| Nhóm | Nghĩa |
|---|---|
| `correct` | Chạy được, tập kết quả trùng đáp án |
| `schema_column`, `schema_table`, `ambiguous_column` | **Ảo giác lược đồ** (sai tên cột / bảng / cột mơ hồ) |
| `syntax` | Sai cú pháp SQL |
| `timeout` | Chạy quá thời gian |
| `other_exec` | Lỗi khác khi chạy (ví dụ dùng hàm không có trong SQLite) |
| `wrong_empty` | Chạy được nhưng không ra dòng nào (đáp án thì có) |
| `wrong_result` | Chạy được nhưng ra kết quả khác đáp án |

**Vì sao phải phân loại lỗi?** Vì luận điểm chính của bài báo là "view giảm ảo giác lược đồ". EX chỉ cho biết đúng hay sai;
muốn kiểm chứng luận điểm này phải đếm riêng **loại** lỗi sai tên.

Ngoài ra chương trình ghi **chi phí** mỗi câu: số lần gọi LLM, số token vào/ra, số giây, số bảng/view trong prompt. **Vì sao?**
Bài báo nói V-SQL giúp tiết kiệm token nhưng không đo; nhóm đo để kiểm tra.

Mã nguồn: hàm `score` trong [`vsql/pipeline.py`](../vsql/pipeline.py), `classify_error` trong [`vsql/db.py`](../vsql/db.py),
tổng hợp trong [`vsql/report.py`](../vsql/report.py).

### 3.6. Kiểm định thống kê: vì sao cần và đọc thế nào

Với 500 câu, chỉ cần vài câu đúng/sai do may rủi là EX đã nhích 1–2 điểm. Nên không thể chỉ nhìn "46,2 > 41,0" mà kết luận.
Nhóm dùng ba công cụ:

**(a) Khoảng tin cậy 95% bằng bootstrap.**
Bốc ngẫu nhiên (có lặp lại) 498 câu từ chính 498 câu, tính EX; làm 2.000 lần; lấy khoảng chứa 95% các giá trị ở giữa.
*Đọc:* EX = 46,2%, khoảng tin cậy [41,8; 50,6] nghĩa là "nếu đổi sang bộ câu hỏi khác cùng kiểu, EX nhiều khả năng nằm trong
khoảng này". Với hiệu (ΔEX) giữa hai cấu hình: nếu khoảng tin cậy **không chứa 0** thì chênh lệch khá chắc chắn là thật.

**(b) Kiểm định McNemar (so sánh ghép cặp).**
Vì hai cấu hình trả lời **cùng** 498 câu, ta chỉ cần nhìn các câu mà hai bên **khác nhau**:
- *b* = số câu chỉ cấu hình A đúng, *c* = số câu chỉ cấu hình B đúng.
- Nếu hai cấu hình thật ra ngang nhau, *b* và *c* phải xấp xỉ nhau (như tung đồng xu). McNemar tính xác suất (**p**) để
  thấy chênh lệch lớn như vậy chỉ do may rủi.
- *Đọc:* **p < 0,05** → chênh lệch có ý nghĩa thống kê (khó là do may rủi).

Ví dụ thật (qwen3.5:9b): so `vsql` với `base`, có 74 câu chỉ `base` đúng, 48 câu chỉ `vsql` đúng, p = 0,023.

**(c) Hiệu chỉnh Holm.**
Khi so sánh nhiều cặp cùng lúc, kiểu gì cũng có cặp "trúng" p < 0,05 do may. Holm nâng các giá trị p lên để bù. Trong các bảng,
cột **p Holm** là con số nên tin. Bốn giả thuyết chính (P1, P2, P5, P6, xem mục 8) được **cố định trước khi xem kết quả**
(file [`hypotheses.py`](../hypotheses.py)) để tránh "chọn cặp đẹp sau khi đã biết số".

> **Thuật ngữ**
> - **Ý nghĩa thống kê**: chênh lệch đủ lớn so với độ dao động ngẫu nhiên, nên có thể tin là thật.
> - **Giá trị p**: xác suất thấy chênh lệch lớn như vậy *nếu thật ra hai bên ngang nhau*. Càng nhỏ càng đáng tin là có khác biệt.

### 3.7. Cách chạy lại thực nghiệm

Chương trình chỉ dùng thư viện chuẩn của Python ≥ 3.8 (không cần `pip install`) và một mô hình chạy bằng Ollama.

**Cách 1 – Google Colab (khuyến nghị nếu không có GPU):** mở
[`notebooks/VSQL_Colab.ipynb`](../notebooks/VSQL_Colab.ipynb) và làm theo [`docs/HUONG_DAN_COLAB.md`](HUONG_DAN_COLAB.md).
Kết quả `qwen3.5:9b` trong thư mục [`ollama_qwen3.5_9b_mau500/`](../ollama_qwen3.5_9b_mau500/) được tạo đúng bằng notebook
này (`BACKEND = ollama`, `MODEL = qwen3.5:9b`, `SAMPLE = 500`; cấu hình đầy đủ trong `config.json` của thư mục đó).

**Cách 2 – Máy cá nhân có Ollama:**

```bash
# 0) Kiểm thử phần không cần mô hình (nên chạy trước để chắc mã nguồn chạy được)
python tests/test_all.py
python tests/test_repair.py

# 1) Tải mô hình và dữ liệu
ollama pull qwen3.5:9b
#   tải https://bird-bench.oss-cn-beijing.aliyuncs.com/minidev.zip rồi giải nén vào thư mục minidev/
D=minidev/MINIDEV
CHUNG="--data $D/mini_dev_sqlite.json --db-root $D/dev_databases"

# 2) (tùy chọn) Xem trước các view sẽ được tạo, chưa gọi mô hình
python run_experiment.py $CHUNG --out results/q35_9b --views-only

# 3) Chạy chính: gọi mô hình cho 5 cấu hình
python run_experiment.py $CHUNG --model qwen3.5:9b --out results/q35_9b \
       --methods base,vsql,auto_det,hybrid,hybrid_ret

# 4) Áp dụng CT5 cho từng cấu hình (không gọi mô hình), rồi CT7 bỏ phiếu
for m in base vsql auto_det hybrid hybrid_ret; do
  python improve.py results/q35_9b $CHUNG --fix --methods $m
done
python improve.py results/q35_9b $CHUNG --vote mrv=base_fix,auto_det_fix,hybrid_ret_fix,hybrid_fix

# 5) Tổng hợp bảng kết quả và kiểm định giả thuyết
python -c "from vsql import report; report.build('results/q35_9b')"
python hypotheses.py results/q35_9b
python analyze.py results/q35_9b --data $D/mini_dev_sqlite.json   # EX theo CSDL, theo số JOIN
```

**Một số chi tiết kỹ thuật giúp chạy ổn định, và lý do:**

| Chi tiết | Tác dụng / lý do |
|---|---|
| **Cache câu trả lời** (`llm_cache.sqlite`) | Mỗi prompt chỉ gọi mô hình một lần. Bị ngắt giữa chừng (Colab hay bị) thì chạy lại lệnh cũ, các câu đã làm được bỏ qua. |
| **Prefetch** (gọi trước, sắp xếp prompt) | Chương trình gom mọi prompt còn thiếu, sắp theo thứ tự chữ cái rồi mới gọi. Các prompt cùng CSDL có phần đầu giống nhau đứng cạnh nhau, Ollama dùng lại phần đã tính (*KV cache*) nên nhanh hơn 3–5 lần. Kết quả từng câu không đổi. |
| `--num-ctx 16384` | Ollama mặc định chỉ đọc 4.096 token đầu của prompt và **âm thầm cắt** phần sau. Lược đồ BIRD dài nên phải nâng lên, nếu không mô hình không thấy câu hỏi. |
| `vsql` và các cấu hình dùng chung prompt | Nhờ temperature 0 + cache, hai cấu hình có cùng prompt giai đoạn 1 nhận **cùng** SQL nháp, nên chênh lệch giữa chúng chỉ do phần khác nhau. Đây là cách "cô lập" từng yếu tố. |
| `--sample N` | Lấy mẫu **phân tầng** N câu (giữ đúng tỉ lệ CSDL × độ khó) để chạy thử nhanh trước khi chạy đủ 500 câu. |

> **Thuật ngữ**
> - **KV cache**: phần tính toán mô hình đã làm cho đoạn đầu prompt; nếu prompt sau có cùng đoạn đầu thì dùng lại được, đỡ tính
>   lại.
> - **Lấy mẫu phân tầng**: chọn một phần câu hỏi sao cho tỉ lệ từng nhóm (CSDL, độ khó) giống bộ đầy đủ, để kết quả trên tập nhỏ
>   vẫn đại diện.

---

## 4. Kết quả tái hiện và nhận xét

### 4.1. Con số chính

| Mô hình | `base` (1 giai đoạn) | `vsql` (tái hiện bài báo) | Chênh lệch | p McNemar |
|---|---|---|---|---|
| `qwen3.5:0.8b` (498 câu) | 8,4% | 3,8% | **−4,6** | 0,001 (có ý nghĩa) |
| `qwen3.5:9b` (498 câu) | 46,2% | 41,0% | **−5,2** [−9,4; −0,8] | 0,023 (có ý nghĩa trước hiệu chỉnh) |
| `qwen3:8b` (thử trên 103 câu) | 38,8% | 37,9% | −1,0 | 1,0 (chưa kết luận được) |

**V-SQL không tốt hơn mà kém hơn cách làm thông thường, trên cả hai mô hình chạy đủ 498 câu.** Điều này xảy ra dù view của
`vsql` được thiết kế nhờ nhìn đáp án.

Để hình dung độ lớn: `qwen3.5:9b` một giai đoạn (46,2%) đã ngang GPT-3.5 + V-SQL trong bài báo (45,4%), nhưng hai con số này
khác mô hình nên chỉ mang tính tham khảo.

### 4.2. View có giảm lỗi sai tên không? Không, mà còn tăng

Tỉ lệ câu bị ảo giác lược đồ (% trên tổng số câu):

| Mô hình | `base` | `vsql` |
|---|---|---|
| `qwen3.5:0.8b` | 51,4% | 65,9% |
| `qwen3.5:9b` | 8,4% | 13,1% |

Luận điểm chính của bài báo không đứng vững trong thực nghiệm của nhóm. Nhìn vào các câu lỗi, nhóm thấy nguyên nhân:

- **View có tên cột dài, được ghép tiền tố**, ví dụ `hero_publisher_publisher_name`, `hero_eye_colour`. Mô hình hay đoán sai
  dạng tên (viết `hero_publisher`, `hero_alignment_id`), hoặc lấy tên cột của view này đem dùng cho view khác.
  Ví dụ thật (qwen3.5:9b): `SELECT ... hero_publisher_publisher_name ... FROM v_superhero` → lỗi, vì cột đó thuộc view
  `v_hero_attribute`, không thuộc `v_superhero`.
- **Giai đoạn 2 lại bắt mô hình tự viết JOIN**, và mô hình nhỏ còn hay **để sót tên view** trong SQL cuối (với 0.8B: 174 câu
  SQL cuối còn chứa tên `v_...` và báo lỗi; với 9B còn 3 câu).
- **Prompt dài gấp 3**: `vsql` tốn trung bình 7.782 token vào mỗi câu so với 2.577 của `base` (qwen3.5:9b), và gọi mô hình gần
  2 lần. Không có chuyện "tiết kiệm token".

### 4.3. Một điểm có lợi cho V-SQL

Khi chia theo số phép JOIN trong SQL đáp án (`qwen3.5:9b`):

| Số JOIN trong đáp án | Số câu | `base` | `vsql` |
|---|---|---|---|
| 0 | 93 | 50,5 | 44,1 |
| 1 | 303 | 49,2 | 40,6 |
| 2 | 86 | 33,7 | **38,4** |
| ≥ 3 | 16 | 31,2 | **43,8** |

Với câu cần **nhiều JOIN**, V-SQL nhỉnh hơn, đúng với trực giác của bài báo. Nhưng nhóm câu này ít (102/498), chênh lệch nhỏ
và chưa kiểm định riêng; còn ở nhóm câu 0–1 JOIN (chiếm 80%), V-SQL kém rõ rệt, nên tổng thể vẫn thua.

### 4.4. Kết luận phần tái hiện

1. Không tái hiện được lợi ích của V-SQL so với baseline một giai đoạn.
2. Giả thuyết "view giảm ảo giác lược đồ" không được ủng hộ: ảo giác tăng.
3. Ý tưởng view vẫn có giá trị ở câu nhiều JOIN, nên nhóm **không bỏ hẳn view** mà tìm cách dùng nó vào việc khác (mục 7).

---

## 5. Hướng cải tiến: vì sao nhóm chọn

### 5.1. Quan sát then chốt

Hãy nhìn lại lỗi mà bài báo muốn chữa: `hero_attribute.attribute_name` (cột `attribute_name` thực ra thuộc bảng `attribute`).
Khi chạy câu SQL này, SQLite báo:

```
no such column: hero_attribute.attribute_name
```

**Hệ quản trị CSDL đã chỉ đích danh tên nào sai.** Và chương trình có trong tay lược đồ thật: biết bảng nào có cột nào, bảng nào
nối với bảng nào. Vậy thì:

- V-SQL cố **ngăn** lỗi **trước** khi sinh SQL bằng cách đổi lược đồ, rồi hy vọng mô hình hiểu tốt hơn. Kết quả: không hiệu quả
  (mục 4).
- Nhóm làm **ngược lại**: để mô hình sinh SQL như bình thường, **chạy thử, đọc lỗi, và sửa bằng thông tin chắc chắn** (thông báo
  lỗi + lược đồ thật).

Đây là hướng *kiểm tra dựa trên kết quả thực thi* (execution-guided), nhiều hệ thống dẫn đầu bảng xếp hạng BIRD có dùng dưới
dạng nào đó, trong khi bài báo V-SQL hoàn toàn không dùng.

### 5.2. Các hướng nhóm đã thử (và vì sao chỉ giữ CT5, CT7)

Nhóm không chọn ngay mà thử 8 hướng, đo từng hướng trên `qwen3.5:0.8b` với đủ 498 câu, rồi giữ lại hướng có tác dụng rõ.

| Ký hiệu | Ý tưởng | Lý do thử | Kết quả (0.8B) | Quyết định |
|---|---|---|---|---|
| CT1 | Thay giai đoạn 2 (LLM viết lại) bằng **chèn định nghĩa view vào SQL nháp** một cách máy móc | Truy vấn trên view nhiều-một tương đương truy vấn trên định nghĩa view; không cần LLM viết JOIN | −1,0 điểm so với `vsql` (không ý nghĩa) | Bỏ |
| CT2 | **Tự động tạo view** từ đồ thị khóa ngoại, không nhìn đáp án | Bỏ rò rỉ đáp án, áp dụng được cho CSDL mới | Ngang `vsql` (±0,0) | Giữ làm *nguồn* cho CT7 |
| CT3 | Lược đồ **lai**: đưa cả view lẫn bảng gốc | Câu cần bảng gốc (đếm dòng bảng tra cứu, quan hệ 1-N) vẫn viết được | +1,8 so với chỉ dùng view | Giữ làm nguồn cho CT7 |
| CT4 | **Truy xuất** 5 view/bảng liên quan nhất bằng BM25 | Prompt ngắn hơn, ít nhiễu | ±0,0 | Giữ làm nguồn cho CT7 |
| **CT5** | **Sửa lỗi tên theo lược đồ** | Lỗi được CSDL báo chính xác | **+3,0** so với `base`, p < 0,001 | **Chọn** |
| CT6 | View giữ **tên cột gốc** (`SEX` thay vì `Patient_SEX`) | Giảm lỗi đoán tên cột của view | +1,0, p = 0,27 (không ý nghĩa) | Bỏ |
| **CT7** | **Bỏ phiếu** giữa nhiều cách biểu diễn lược đồ | Mỗi cách biểu diễn sai kiểu khác nhau | **+5,0** so với `base`, p < 0,001 | **Chọn** |
| CT8 | Câu vẫn lỗi sau CT5 → gọi LLM thêm một lần kèm thông báo lỗi | Sửa phần CT5 không sửa được | +0,0 | Bỏ |

> **Thuật ngữ**
> - **BM25**: thuật toán tìm kiếm văn bản cổ điển (giống công cụ tìm kiếm), chấm điểm mức liên quan giữa câu hỏi và mô tả của
>   từng bảng/view dựa trên từ trùng nhau. Không cần mô hình AI.
> - **CTE (Common Table Expression)**: cú pháp `WITH ten AS (SELECT ...) SELECT ... FROM ten`, cho phép định nghĩa "bảng tạm"
>   ngay trong câu SQL. CT1 dùng CTE để biến tên view thành bảng tạm có thật mà không cần tạo view trong CSDL.

Kết quả lần chạy `qwen3.5:9b` dùng đúng bộ đã chọn: CT5 cho 5 cấu hình (`base`, `vsql`, `auto_det`, `hybrid`, `hybrid_ret`) và
CT7 bỏ phiếu trên 4 nguồn.

**Vì sao hai cải tiến này hợp lý về mặt nguyên lý:**

- **CT5** nhắm thẳng vào loại lỗi bài báo nêu ra, nhưng sửa bằng **thông tin chắc chắn** thay vì nhờ mô hình "hiểu" hơn. Không
  gọi thêm mô hình nên **gần như miễn phí**, rất hợp với mô hình nhỏ chạy cục bộ. Không dùng SQL đáp án nên áp dụng được thật.
- **CT7** dựa trên nhận xét: mỗi cách mô tả lược đồ khiến mô hình **sai theo kiểu khác nhau**, còn các câu SQL **đúng** thì
  thường ra **cùng một kết quả**. Nó giữ lại ý tưởng view của bài báo, nhưng dùng view làm **một trong nhiều góc nhìn** thay vì
  thay thế hoàn toàn lược đồ gốc.

---

## 6. CT5 – Sửa lỗi theo lược đồ (schema-guard)

Mã nguồn: [`vsql/repair.py`](../vsql/repair.py) (hàm `repair`), gọi từ [`improve.py`](../improve.py) với tùy chọn `--fix`.

### 6.1. Mục đích

Tự động sửa các câu SQL **chạy báo lỗi** vì sai tên bảng/cột/alias hoặc dùng hàm không có trong SQLite, **không gọi lại mô hình**
và **không nhìn đáp án**.

### 6.2. Cách làm, từng bước

```
lặp tối đa 8 lần:
    chạy SQL trên CSDL
    nếu chạy được  -> dừng (KHÔNG đụng vào câu đã chạy được)
    đọc thông báo lỗi của SQLite
    tìm cách sửa tương ứng với loại lỗi (bảng 6.3)
    nếu không sửa được -> dừng, giữ nguyên câu
    thay vào, quay lại chạy thử
```

Trước vòng lặp có một bước dọn nhỏ: xóa dấu `;` bị đặt lạc giữa câu (mô hình nhỏ hay sinh `... AS x; FROM t`).

**Vì sao lặp?** Một câu có thể có nhiều tên sai; SQLite mỗi lần chỉ báo lỗi đầu tiên. Sửa xong lỗi này mới thấy lỗi kế.
**Vì sao tối đa 8 lần?** Để không lặp vô hạn khi sửa không hội tụ.

### 6.3. Các quy tắc sửa

| Lỗi SQLite báo | Ví dụ mô hình viết | Cách sửa |
|---|---|---|
| Cột gán nhầm bảng (đúng ví dụ của bài báo) | `hero_attribute.attribute_name` | Tìm bảng trong `FROM/JOIN` thật sự có cột `attribute_name` → `attribute.attribute_name` |
| Dùng tên bảng khi đã đặt alias | `member.first_name` với `FROM member m` | `m.first_name` |
| Alias không tồn tại | `e.type` (không có alias `e`) | Dùng alias của bảng có cột `type` → `ev.type` |
| Tên cột gần đúng | `p.PatientSEX`, `l.PatientID` | So độ giống chữ với các cột thật → `p.SEX`, `l.ID` |
| Cột thuộc bảng **chưa có** trong `FROM` | `Birthday` khi chỉ có `FROM Laboratory` | **Tự thêm `LEFT JOIN`** sang bảng có cột đó, theo khóa ngoại (xem 6.4) |
| Tên cột có ký tự đặc biệt | `l.T-CHO` (SQLite hiểu là `l.T` trừ `CHO`) | Bọc lại: `` l.`T-CHO` `` |
| Hàm của hệ quản trị khác | `YEAR(Birthday)` (MySQL) | `CAST(strftime('%Y', Birthday) AS INTEGER)`; tương tự `MONTH`, `DAY`, `NOW()`, `CONCAT`, `ILIKE`, `ISNULL` |
| Nhiều câu lệnh trong một chuỗi | `SELECT ...; SELECT ...` | Giữ câu đầu tiên |
| Tên bảng sai | `no such table: superheroes` | Tên bảng thật gần giống nhất → `superhero` |

**"Gần giống" được đo thế nào?** Bỏ ký tự đặc biệt, chữ hoa/thường; nếu trùng hẳn: điểm 1,0; nếu tên này là đuôi của tên kia
(ví dụ `PatientSEX` và `SEX`): 0,9; còn lại dùng tỉ lệ giống chuỗi ký tự (`difflib.SequenceMatcher`). **Chỉ thay khi điểm ≥ 0,8**,
để tránh thay bừa sang một cột sai nghĩa. Chương trình cũng thử bỏ các tiền tố của view (`Customer_Currency` → `Currency`).

### 6.4. Tự thêm JOIN theo khóa ngoại: chỗ tận dụng ý tưởng của bài báo

View của V-SQL thực chất là **các phép nối theo khóa ngoại được làm sẵn cho mọi câu hỏi**. CT5 dùng lại đúng tri thức đó, nhưng
**chỉ khi câu SQL thật sự cần**: nếu một cột không có trong các bảng đang dùng, chương trình tìm bảng nối **một bước** theo khóa
ngoại có chứa cột đó, rồi thêm `LEFT JOIN` vào cuối mệnh đề `FROM`.

Thứ tự ưu tiên: **chiều nhiều-một trước** (bảng đang có trỏ tới bảng cần thêm), vì chiều này không nhân bản dòng nên không làm
sai `COUNT`/`SUM`; chỉ khi không có mới thử chiều một-nhiều.

Ví dụ thật (qwen3.5:9b, CSDL `thrombosis_prediction`, câu 1185):

```sql
-- Mô hình viết: dùng cột Birthday nhưng chỉ FROM Laboratory  -> lỗi "no such column: Birthday"
SELECT ... CASE WHEN Birthday = '1959-02-18' ... FROM Laboratory
-- CT5: Laboratory.ID là khóa ngoại trỏ tới Patient.ID, Patient có cột Birthday -> thêm JOIN
SELECT ... CASE WHEN j_Patient.Birthday = '1959-02-18' ...
FROM Laboratory LEFT JOIN Patient AS j_Patient ON Laboratory.ID = j_Patient.ID
```

Sau khi sửa, câu này cho kết quả đúng.

### 6.5. Hai ví dụ khác từ lần chạy qwen3.5:9b

**Alias không tồn tại** (CSDL `student_club`, câu 1404): mô hình đặt alias `ev` cho bảng `event` nhưng lại viết `e.type`.

```sql
-- trước:  SELECT e.type, SUM(ex.cost) ... JOIN event ev ON ... GROUP BY e.type     -> no such column: e.type
-- sau:    SELECT ev.type, SUM(ex.cost) ... JOIN event ev ON ... GROUP BY ev.type    -> đúng
```

**Hàm MySQL trên SQLite** (CSDL `thrombosis_prediction`, câu 1201):

```sql
-- trước:  ... WHERE YEAR(Birthday) = 1980 ...                                  -> no such function: YEAR
-- sau:    ... WHERE CAST(strftime('%Y', Birthday) AS INTEGER) = 1980 ...       -> đúng
```

### 6.6. CT5 với các cấu hình dùng view

- Với cấu hình mà giai đoạn 2 là **chèn định nghĩa view** (`auto_det`, `hybrid`, `hybrid_ret`): CT5 sửa trên **SQL nháp** (viết
  bằng tên view, tên cột của view), mỗi lần chạy thử thì chèn lại định nghĩa view dạng CTE. Làm vậy để sửa đúng theo tên cột
  mà mô hình đã nhìn thấy trong prompt.
- Với `vsql` (giai đoạn 2 do LLM viết): nếu SQL cuối còn sót tên view, CT5 chèn định nghĩa view đó thành CTE rồi mới sửa tiếp.

### 6.7. Tính an toàn

- **Chỉ đụng vào câu đang báo lỗi.** Câu đã chạy được (dù đúng hay sai) giữ nguyên. Do đó CT5 **không thể làm hỏng một câu đang
  đúng**. Trong dữ liệu, có đúng một câu (câu 518) chuyển từ đúng sang sai ở mọi cấu hình `_fix`, nhưng CT5 **không sửa gì** ở
  câu này: lý do là ở lần chấm lại trên Colab, chính SQL đáp án của câu đó chạy quá 120 giây nên không có kết quả để so. Đây là
  nhiễu của môi trường chấm, không phải lỗi của CT5.
- **Không dùng SQL đáp án**, chỉ dùng lược đồ và khóa ngoại của CSDL, nên dùng được trong hệ thống thật.

---

## 7. CT7 – Bỏ phiếu theo kết quả thực thi

Mã nguồn: [`improve.py`](../improve.py), tùy chọn `--vote`. Lệnh dùng trong thực nghiệm:
`--vote mrv=base_fix,auto_det_fix,hybrid_ret_fix,hybrid_fix` (`mrv` = *multi-representation voting*, bỏ phiếu đa biểu diễn).

### 7.1. Mục đích

Thay vì đặt cược vào một cách mô tả lược đồ (bảng gốc **hoặc** view như V-SQL), cho mô hình nhìn CSDL qua **nhiều góc** rồi
để kết quả chạy SQL "bỏ phiếu".

### 7.2. Bốn nguồn (bốn cách mô tả lược đồ)

Mỗi nguồn là một lần gọi mô hình, sau đó qua CT5. **Thứ tự liệt kê cũng là thứ tự ưu tiên khi hòa phiếu.**

| # | Nguồn | Mô hình thấy gì | Vì sao đưa vào |
|---|---|---|---|
| 1 | `base_fix` | Toàn bộ bảng gốc | Mạnh nhất khi đứng riêng, nên được ưu tiên khi hòa |
| 2 | `auto_det_fix` | View tự động (+ bảng không thuộc view nào) | Câu nhiều JOIN dễ hơn trên view |
| 3 | `hybrid_ret_fix` | 5 view/bảng liên quan nhất (BM25) | Prompt ngắn, ít nhiễu |
| 4 | `hybrid_fix` | Cả view tự động lẫn bảng gốc | Kết hợp hai góc nhìn |

**Vì sao dùng view tự động (CT2) chứ không dùng view của bài báo?** View của bài báo được tạo nhờ nhìn đáp án; dùng nó trong
cải tiến là gian lận. View tự động chỉ dựa vào đồ thị khóa ngoại:

> Với mỗi bảng có khóa ngoại: `LEFT JOIN` sang các bảng cha theo chiều nhiều-một, sâu tối đa 2 mức, tối đa 60 cột; mỗi khóa ngoại
> có alias riêng (ví dụ `colour` được nối 3 lần thành `hero_eye_colour`, `hero_hair_colour`, `hero_skin_colour`). Kiểm tra số
> dòng view bằng số dòng bảng gốc (đều đạt ở cả 11 CSDL). Mã nguồn: `auto_views` trong [`vsql/views.py`](../vsql/views.py).

### 7.3. Quy tắc bỏ phiếu

```
với mỗi câu hỏi:
    chạy SQL của 4 nguồn
    bỏ qua câu báo lỗi và câu ra kết quả rỗng
    nhóm các câu theo TẬP KẾT QUẢ (không theo chữ SQL)
    chọn tập kết quả có nhiều phiếu nhất
    nếu hòa: chọn tập kết quả của nguồn đứng trước trong danh sách
    nếu cả 4 đều lỗi/rỗng: lấy nguồn đầu tiên chạy được (hoặc nguồn 1)
```

**Vì sao so theo kết quả chứ không theo chữ SQL?** Hai câu SQL viết khác nhau (alias khác, thứ tự điều kiện khác) vẫn có thể
đúng như nhau. EX cũng chấm theo kết quả, nên bỏ phiếu theo kết quả là khớp với cách chấm.

**Vì sao bỏ qua câu rỗng?** Phần lớn câu hỏi BIRD có đáp án khác rỗng; kết quả rỗng thường là dấu hiệu điều kiện `WHERE` sai
(ví dụ viết `'blue'` thay vì `'Blue'`).

Ví dụ minh họa: nguồn 1 và 3 cùng ra `{(42,)}`, nguồn 2 ra `{(40,)}`, nguồn 4 lỗi → chọn `{(42,)}` (2 phiếu).

> **Thuật ngữ**
> - **Self-consistency (tự nhất quán)**: kỹ thuật cho mô hình trả lời nhiều lần rồi lấy câu trả lời phổ biến nhất. CT7 giống ý
>   tưởng này, nhưng sự đa dạng đến từ **cách mô tả lược đồ** chứ không phải từ việc cho mô hình trả lời ngẫu nhiên nhiều lần
>   (nhiệt độ vẫn bằng 0).

### 7.4. Chi phí

4 lần gọi mô hình mỗi câu (gấp 4 `base`), khoảng 18.000 token vào mỗi câu (gấp 7 `base`). Đây là cái giá cần cân nhắc.

### 7.5. Trần lý thuyết

Với `qwen3.5:9b`, chỉ **60,0%** số câu có ít nhất một trong 4 nguồn đúng, và 148 câu (29,7%) cả 4 nguồn cùng đúng. Nghĩa là
dù bỏ phiếu hoàn hảo, CT7 cũng không vượt quá 60%; và vì các nguồn thường đúng/sai cùng nhau, khoảng trống để bỏ phiếu phát
huy tác dụng không lớn.

---

## 8. Kết quả các cải tiến

Toàn bộ số liệu: [`ollama_qwen3.5_9b_mau500/summary.md`](../ollama_qwen3.5_9b_mau500/summary.md) (9B) và
`results/q08_500/summary.md` (0.8B).

![EX của 5 cấu hình chính với qwen3.5:9b](../ollama_qwen3.5_9b_mau500/bieu_do_ex.png)

### 8.1. Bảng chính

EX (%) trên 498 câu, trong ngoặc là khoảng tin cậy 95%:

| Cấu hình | `qwen3.5:0.8b` | `qwen3.5:9b` | Gọi LLM/câu |
|---|---|---|---|
| `base` (một giai đoạn) | 8,4 [6,0; 10,8] | 46,2 [41,8; 50,6] | 1 |
| `vsql` (tái hiện bài báo) | 3,8 [2,2; 5,6] | 41,0 [36,5; 45,6] | ~2 |
| `base_fix` = base + **CT5** | 11,4 [8,6; 14,1] | **49,0** [44,6; 53,2] | 1 |
| `vsql_fix` = V-SQL + **CT5** | 7,6 [5,4; 10,0] | 43,8 [39,6; 48,4] | ~2 |
| `mrv` = **CT7** (4 nguồn, đã qua CT5) | **13,5** [10,6; 16,5] | **49,6** [45,2; 53,8] | 4 |

Theo độ khó (`qwen3.5:9b`):

| Cấu hình | Dễ (148) | Trung bình (248) | Khó (102) |
|---|---|---|---|
| `base` | 59,5 | 41,1 | 39,2 |
| `vsql` | 52,0 | 37,5 | 33,3 |
| `base_fix` | 60,1 | 44,0 | 45,1 |
| `mrv` | 61,5 | 44,4 | 45,1 |

CT5 giúp nhiều nhất ở câu **khó** (+5,9 điểm), là nhóm câu có nhiều JOIN và nhiều tên cột nhất, nên dễ sai tên nhất.

### 8.2. Kiểm định các giả thuyết đã đặt trước

Kết quả của `python hypotheses.py` (p đã hiệu chỉnh Holm; "thắng/thua" = số câu chỉ cấu hình mới đúng / chỉ cấu hình cũ đúng):

| Mã | Câu hỏi | `qwen3.5:0.8b` | `qwen3.5:9b` |
|---|---|---|---|
| P1 | CT5 có giúp cách làm thông thường? (`base_fix` vs `base`) | **+3,0**, thắng 15 / thua 0, p = 0,0002 | **+2,8**, thắng 15 / thua 1\*, p = 0,002 |
| P2 | CT5 có giúp V-SQL? (`vsql_fix` vs `vsql`) | **+3,8**, thắng 19 / thua 0, p < 0,0001 | **+2,8**, thắng 15 / thua 1\*, p = 0,002 |
| P5 | CT7 có hơn cách thông thường? (`mrv` vs `base`) | **+5,0**, thắng 35 / thua 10, p = 0,0007 | +3,4 [+0,2; +6,4], thắng 43 / thua 26, p = 0,053 |
| P6 | CT7 có hơn V-SQL? (`mrv` vs `vsql`) | **+9,6**, thắng 57 / thua 9, p < 0,0001 | **+8,6**, thắng 72 / thua 29, p < 0,0001 |

\* Câu "thua" là câu 518, do SQL đáp án chạy quá thời gian khi chấm lại (xem mục 6.7), không phải do CT5.

Chữ **in đậm** = có ý nghĩa thống kê (p < 0,05 sau hiệu chỉnh).

### 8.3. Diễn giải

**CT5 – có tác dụng rõ và ổn định.**
- Tăng EX khoảng **3 điểm** cho cả `base` và `vsql`, ở cả mô hình 0,8B lẫn 9B, đều có ý nghĩa thống kê.
- **Ảo giác lược đồ giảm mạnh**: với 9B, từ 8,4% xuống 1,4% (`base`) và từ 13,1% xuống 1,6% (`vsql`). Đây chính là điều bài
  báo muốn đạt được bằng view.
- Với 9B, trong 58 câu `base` bị lỗi khi chạy, CT5 sửa 41 câu cho chạy được, trong đó 15 câu thành đúng.
- Các cấu hình dùng view được lợi **nhiều hơn** từ CT5 (9B): `auto_det` +5,2, `hybrid` +6,6, `hybrid_ret` +8,0 điểm, vì view
  gây nhiều lỗi sai tên hơn. Sau CT5 các cấu hình này vẫn thấp hơn `base_fix`.
- Chi phí: **0 lần gọi mô hình thêm**, chỉ chạy thử SQL vài lần.
- Lưu ý: CT5 biến câu **lỗi** thành câu **chạy được**, nhưng chạy được chưa chắc đúng; phần lớn câu được sửa chuyển sang nhóm
  "kết quả sai" (với 9B, `wrong_result` của `base` tăng từ 35,9% lên 39,6%). Lý do: sau khi hết sai tên, câu SQL vẫn có thể
  hiểu sai ý câu hỏi.

**CT7 – mạnh với mô hình nhỏ, lợi ích thu hẹp với mô hình vừa.**
- Với 0,8B: CT7 là cấu hình tốt nhất (13,5%), hơn `base` 5,0 điểm, có ý nghĩa thống kê.
- Với 9B: CT7 vẫn cao nhất (49,6%), nhưng so với `base` thì p = 0,053 (sát ngưỡng, chưa đủ để khẳng định); và **so với
  `base_fix` chỉ hơn 0,6 điểm** (thắng 31 / thua 28, p = 0,79), tức là không khác biệt. Với 0,8B, mức hơn `base_fix` là 2,0 điểm
  (p = 0,14), cũng chưa có ý nghĩa.
- Lý do: khi mô hình mạnh lên, nguồn `base_fix` đã tốt và thường thắng phiếu (364/498 câu với 9B được lấy từ `base_fix`, 93 từ
  `auto_det_fix`, 40 từ `hybrid_ret_fix`, 1 từ `hybrid_fix`). Các nguồn dùng view kém hơn hẳn nên ít khi "cứu" được câu mà
  `base_fix` sai.
- Chi phí gấp 4 lần gọi mô hình. Với 9B, **CT5 một mình đã cho gần hết lợi ích của CT7 với 1/4 chi phí.**

**So với V-SQL**: cả `base_fix` (+8,0) và `mrv` (+8,6) đều hơn V-SQL rõ rệt trên 9B (p Holm < 0,01), trong khi tốn ít hơn
(`base_fix`) hoặc gấp đôi (`mrv`) số lần gọi mô hình.

### 8.4. Chi phí so sánh (qwen3.5:9b, trung bình mỗi câu)

| Cấu hình | Gọi LLM | Token vào | Giây LLM | EX |
|---|---|---|---|---|
| `base` | 1,00 | 2.577 | 3,9 | 46,2 |
| `vsql` | 1,98 | 7.782 | 8,4 | 41,0 |
| `base_fix` | 1,00 | 2.577 | 3,9 | 49,0 |
| `mrv` | 4,00 | 18.089 | 16,2 | 49,6 |

### 8.5. Kết luận

1. **Tái hiện**: trong điều kiện của nhóm (mô hình Qwen, BIRD mini-dev, zero-shot), V-SQL **không** tốt hơn cách sinh SQL một
   giai đoạn và **không** giảm ảo giác lược đồ.
2. **CT5** đạt đúng mục tiêu mà bài báo đặt ra (giảm lỗi sai tên) một cách trực tiếp, tăng EX khoảng 3 điểm ổn định trên cả hai
   cỡ mô hình, không tốn thêm lần gọi mô hình nào. Đây là cải tiến **nên dùng mặc định**.
3. **CT7** đáng dùng với mô hình nhỏ; với mô hình cỡ 9B trở lên, lợi ích thêm so với CT5 không đáng kể so với chi phí gấp 4.
4. Ý tưởng view của bài báo vẫn hữu ích theo cách khác: làm **tri thức nối bảng** cho CT5 (tự thêm JOIN theo khóa ngoại) và làm
   **một góc nhìn** trong CT7.

---

## 9. Hạn chế và hướng tiếp theo

**Hạn chế của thực nghiệm:**
- Chỉ dùng mô hình Qwen, không phải GPT như bài báo; số tuyệt đối không so trực tiếp được.
- View của bài báo không được công bố; `oracle_views` là mô phỏng của nhóm, có thể khác view thật của tác giả.
- Mỗi cấu hình chạy một lần (temperature 0); chưa đo độ dao động khi đổi prompt hoặc đổi seed.
- Thời gian chạy SQL đo trên Colab nên dao động (ví dụ câu 518), chỉ số VES trong `summary.md` chỉ để tham khảo.

**Hạn chế của CT5:**
- Dựa trên biểu thức chính quy (regex), không phải bộ phân tích cú pháp SQL đầy đủ; câu SQL quá phức tạp có thể không sửa được.
- Có thể chọn một cột "gần giống tên" nhưng sai nghĩa (đã giảm rủi ro bằng ngưỡng giống ≥ 0,8).
- Viết riêng cho thông báo lỗi của SQLite; chuyển sang MySQL/PostgreSQL phải thêm quy tắc.

**Hướng tiếp theo:**
- Dùng bộ phân tích cú pháp SQL (ví dụ `sqlglot`) thay cho regex.
- Thử với mô hình lớn hơn (`qwen3:14b`, `qwen3.5:27b`) để xem xu hướng "CT7 thu hẹp khi mô hình mạnh" còn tiếp tục không.
- Xử lý nhóm lỗi lớn nhất còn lại là **kết quả sai dù chạy được** (khoảng 40% số câu): ví dụ kiểm tra kết quả rỗng, sai đơn vị,
  sai phép gộp.

---

## Phụ lục A. Bảng thuật ngữ

| Thuật ngữ | Giải thích ngắn |
|---|---|
| Text-to-SQL | Chuyển câu hỏi tiếng tự nhiên thành câu lệnh SQL |
| LLM | Mô hình ngôn ngữ lớn (GPT, Qwen…) |
| Prompt | Đoạn văn bản đưa vào mô hình (hướng dẫn + lược đồ + câu hỏi) |
| Token | Đơn vị chữ mô hình đọc/viết, quyết định chi phí và thời gian |
| Temperature 0 | Mô hình luôn chọn câu trả lời chắc nhất → kết quả lặp lại được |
| Lược đồ (schema) | Danh sách bảng, cột và liên kết giữa các bảng |
| Khóa ngoại (FK) | Cột trỏ sang một dòng của bảng khác |
| JOIN / LEFT JOIN | Phép nối hai bảng / nối giữ lại mọi dòng bảng bên trái |
| Quan hệ nhiều-một (N-1) | Nối không làm tăng số dòng (mỗi dòng khớp tối đa một dòng bên kia) |
| Quan hệ một-nhiều (1-N) | Nối có thể nhân bản dòng |
| View | "Bảng ảo" định nghĩa bằng câu SELECT |
| CTE (`WITH ... AS`) | Bảng tạm định nghĩa ngay trong câu SQL |
| Alias | Tên tắt của bảng trong câu SQL |
| Ảo giác lược đồ | Mô hình dùng tên bảng/cột không có thật hoặc gán sai bảng |
| Dummy SQL / SQL nháp | SQL viết trên view ở giai đoạn 1 của V-SQL, không chạy trực tiếp |
| Oracle | Thông tin biết trước đáp án (view `oracle` = view thiết kế nhờ nhìn SQL đáp án) |
| BIRD mini-dev | Bộ 500 câu hỏi chuẩn trên 11 CSDL thật |
| Evidence | Gợi ý kiến thức đi kèm mỗi câu hỏi BIRD |
| EX | Tỉ lệ câu có kết quả chạy trùng đáp án |
| Baseline | Cách làm đơn giản dùng làm mốc so sánh |
| Zero-shot | Không đưa ví dụ mẫu cho mô hình |
| BM25 | Thuật toán tìm kiếm văn bản theo từ khóa |
| Bootstrap, khoảng tin cậy 95% | Ước lượng khoảng dao động của EX bằng cách lấy mẫu lại nhiều lần |
| McNemar | Kiểm định so sánh hai cấu hình trên cùng bộ câu, dựa trên các câu hai bên khác nhau |
| Giá trị p | Xác suất thấy chênh lệch như vậy nếu hai bên thật ra ngang nhau; < 0,05 là có ý nghĩa |
| Hiệu chỉnh Holm | Điều chỉnh p khi kiểm định nhiều cặp cùng lúc |
| Self-consistency | Lấy câu trả lời phổ biến nhất trong nhiều lần trả lời |
| Ollama | Phần mềm chạy LLM mã nguồn mở trên máy cá nhân/Colab |
| KV cache | Phần tính toán dùng lại được khi các prompt có cùng phần đầu |

## Phụ lục B. Tên các cấu hình trong file kết quả

| Tên | Nghĩa |
|---|---|
| `base` | Một giai đoạn trên bảng gốc |
| `vsql` | Tái hiện bài báo: view theo đáp án + LLM viết lại |
| `auto_det` | View tự động (CT2) + chèn định nghĩa view máy móc (CT1) |
| `hybrid` | Như `auto_det` nhưng prompt có cả bảng gốc (CT3) |
| `hybrid_ret` | Như `hybrid` nhưng chỉ giữ 5 view/bảng liên quan nhất (CT4) |
| `<tên>_fix` | Cấu hình `<tên>` sau khi áp dụng CT5 |
| `mrv` | CT7: bỏ phiếu giữa `base_fix`, `auto_det_fix`, `hybrid_ret_fix`, `hybrid_fix` |

## Phụ lục C. Bản đồ mã nguồn và file kết quả

| File | Vai trò |
|---|---|
| [`run_experiment.py`](../run_experiment.py) | Chạy thực nghiệm chính (gọi mô hình) |
| [`improve.py`](../improve.py) | Áp dụng sau: CT5 (`--fix`), CT7 (`--vote`), CT8 (`--feedback`) |
| [`hypotheses.py`](../hypotheses.py) | Kiểm định các giả thuyết P1–P6 |
| [`analyze.py`](../analyze.py) | EX theo CSDL, theo số JOIN |
| [`vsql/pipeline.py`](../vsql/pipeline.py) | Định nghĩa các cấu hình, prompt, chấm điểm |
| [`vsql/views.py`](../vsql/views.py) | Tạo view (oracle / tự động), kiểm tra số dòng, chèn CTE |
| [`vsql/repair.py`](../vsql/repair.py) | CT5 sửa lỗi theo lược đồ |
| [`vsql/retrieval.py`](../vsql/retrieval.py) | Truy xuất BM25 |
| [`vsql/report.py`](../vsql/report.py) | EX, bootstrap, McNemar, Holm, phân loại lỗi, chi phí |
| [`vsql/db.py`](../vsql/db.py) | Đọc lược đồ, chạy SQL có giới hạn thời gian, phân loại lỗi |
| [`ollama_qwen3.5_9b_mau500/`](../ollama_qwen3.5_9b_mau500/) | Kết quả `qwen3.5:9b` |
| `results/q08_500/` | Kết quả `qwen3.5:0.8b` |
| `predictions_<cấu hình>.jsonl` | Kết quả từng câu: SQL nháp, SQL cuối, lỗi, đúng/sai, token; `_fix` có thêm `repair_steps`; `mrv` có thêm `voted_from` |
| `summary.md`, `summary.csv` | Bảng tổng hợp |
