# Tái hiện lại V-SQL cho đúng, so với TA-SQL, và cải tiến V-SQL+

Tài liệu này ghi lại: (1) kết quả kiểm tra phần tái hiện cũ và vì sao baseline luôn hơn V-SQL; (2) cách tái hiện lại cho đúng
paper, với TA-SQL là baseline; (3) thiết kế cải tiến V-SQL+; (4) cách chạy trên Colab T4.

Mã mới: `vsql/methods.py`, `vsql/autoview.py`, `vsql/linking.py`, `vsql/meta.py`, `vsql/tasql_prompts.py`, `run_compare.py`,
`tests/test_compare.py`, `notebooks/TASQL_VSQL_VSQLplus_Colab.ipynb`. Mã của lần tái hiện cũ đã được gỡ khỏi repo (vẫn còn
trong lịch sử git); mục 1 dưới đây chỉ ghi lại các vấn đề tìm thấy ở lần tái hiện đó.

---

## 1. Kiểm tra phần tái hiện cũ

### 1.1 Bộ dữ liệu: hai phiên bản mini-dev

Đã kiểm tra trực tiếp trên nguồn (06/11/2026):

| | `2024-06` — zip gốc trên OSS | `2025-07-04` — bản sửa trên Hugging Face |
|---|---|---|
| Nguồn | https://bird-bench.oss-cn-beijing.aliyuncs.com/minidev.zip (Last-Modified 20/06/2024), link "Alibaba" trong README của https://github.com/bird-bench/mini_dev | https://huggingface.co/datasets/birdsql/bird_mini_dev, commit `f65faf4ae3b638c1fa6df1d3370c8d92c8366301`, file `data/mini_dev_sqlite-00000-of-00001.json` (nay lưu ở `archive/bird_mini_dev_2025-07-04/`) |
| md5 `mini_dev_sqlite.json` | `a84c72cad3a21d74d0f45ae21d63bb83`; **trùng từng byte với bản trong repo** | `595b6b014a528f4386d2e16f74d14b40` |
| Số dòng / câu khác nhau | 500 / **498**: `question_id` 137 và 138 mỗi mã lặp 2 lần | 500 / **500** |
| Khác biệt | — | có thêm câu 119, 120 (`financial`, `moderate`) thay cho 2 bản lặp; sửa SQL đáp án câu 1322 (`student_club`) và 879 (`formula_1`); khác thứ tự ở 16/500 vị trí |
| Độ khó | 148 / 250 / 102 | 148 / 250 / 102 |
| CSDL, `dev_tables.json` | giống nhau | giống nhau; 500/500 SQL đáp án chạy được trên `dev_databases` của zip (câu 701 chậm ở cả hai bản) |

Như vậy bản trong repo đúng là bản gốc 2024 trên OSS. Bản này có 2 câu lặp, còn bản 2025 trên Hugging Face (mà README
chính thức coi là bản chuẩn) thì không. Bản Hugging Face hiện hành (cập nhật 2026-10) là bộ câu hỏi đã viết lại nhiều (độ khó
8/32/460), không so được với paper. Paper không ghi link hay phiên bản dữ liệu, và Bảng 2 (148/250/102) khớp cả hai bản.

**Từ 13/11 chỉ dùng bản 2025-07-04** (notebook tải từ Hugging Face, kiểm tra md5; thư mục kết quả `cmp_<model>_d2025`).
`run_compare.py` từ chối file câu hỏi có `question_id` lặp, tức bản 2024. Mỗi câu định danh theo vị trí dòng (`uid`).

### 1.2 Baseline sai đối tượng

Paper so sánh V-SQL với **TA-SQL** (cùng DIN-SQL, DAIL-SQL) — Bảng 3. Mã cũ không có TA-SQL; "baseline" `base` là một prompt
zero-shot do nhóm tự viết. Mã mới cài lại TA-SQL theo mã nguồn chính thức (mục 2.2).

### 1.3 Vì sao `base` luôn hơn `vsql` trong lần chạy cũ

Phân tích lại 500 dự đoán của `qwen3.5:9b` (`ollama_qwen3.5_9b_mau500.zip`). Với mỗi câu, mở rộng **tất định** dummy SQL của
giai đoạn 1 về bảng gốc rồi chấm, để tách lỗi của từng giai đoạn:

| | Số câu đúng / 500 |
|---|---|
| Dummy SQL (giai đoạn 1) mở rộng tất định | 183 |
| V-SQL cũ (giai đoạn 2 do LLM khôi phục) | 205 |
| `base` | 230 |

Giai đoạn 2 không làm mất câu đúng mà còn sửa được 22 câu. **Phần thua nằm ở giai đoạn 1**: dummy SQL viết trên view sai
317/500 câu. Đọc các câu `base` đúng mà V-SQL sai thì thấy nguyên nhân nằm ở cách dựng view và schema, không phải ở bản thân ý tưởng:

1. **Tên cột của view khó hiểu, khác Hình 3 của paper.** View cũ đặt tên kiểu `hero_publisher_publisher_name`,
   `link_to_major_major_name`, `link_to_budget_link_to_event_event_date`, và giữ lẫn cả cột id. Paper (Hình 3) dùng tên sạch:
   `eye_colour`, `publisher_name`, `gender`. Mô hình đoán sai tên, nên lỗi `no such column` tăng từ 8,0% (`base`) lên 11,2%.
2. **Evidence của BIRD nói theo tên cột gốc** (`A15`, `colour.id`, `Currency`). Khi view đổi tên cột, mô hình phải tự ánh xạ
   evidence sang tên mới.
3. **Bảng bị ẩn khỏi schema.** D′ cũ chỉ giữ các bảng *không nằm trong view nào*, nên bảng thực thể như `customers` biến mất.
   Câu "tỉ lệ khách hàng trả EUR/CZK" buộc phải đếm qua `v_yearmonth`, nên đếm số dòng tháng thay vì số khách (uid 1471, 1486). `vsql` hiện tại hiện lại các bảng này (mục 2.1).
4. **View 1-N có nhân bản dòng** (`oracle_fan`, kèm dòng `WARNING`). Paper không có loại view này.
5. **Prompt không phải của paper**, và schema không có mô tả cột (paper Bảng 6 dùng `database_description`).

### 1.4 Phần giải mã dummy SQL

Hàm `views.unfold` chèn định nghĩa view thành CTE `WITH v_x AS (...)`, nên câu SQL cuối có cùng ngữ nghĩa với việc chạy trên
view thật. `tests/test_compare.py` kiểm chứng điều này: tạo view thật trong một bản sao SQLite, chạy 7 truy vấn (lọc, nhóm,
nối view–view, `SELECT *`) trên view thật và trên bản đã mở rộng, có và không cắt JOIN thừa; kết quả trùng nhau (so cả số lần
lặp dòng). View dùng `LEFT JOIN` theo khóa ngoại N-1, khóa được tham chiếu đã được kiểm tra là duy nhất, nên số dòng giữ
nguyên (`COUNT(*)` của view bằng của bảng gốc ở cả 11 CSDL).

---

## 2. Tái hiện lại cho đúng

### 2.1 V-SQL (`vsql`): bản tái hiện duy nhất, sát paper nhất có thể

Trước 13/11 mã có ba bản (`vsql` bản đầu, `vsql_paper`, `vsql_fair`). Nay chỉ còn một bản `vsql` (phiên bản cài đặt `IMPL = 4`
trong `vsql/methods.py`); bản ghi của các cài đặt cũ trong thư mục kết quả được tách ra `old_predictions_vsql_*.jsonl`.

| Thành phần | Paper nói gì | Cài đặt |
|---|---|---|
| View (mục 6, Hình 2, Hình 3, Bảng 4) | Thiết kế tay theo các phép JOIN trong SQL đáp án. Hình 3: `v_superhero` = `id, superhero_name, full_name, gender, eye_colour, hair_colour, skin_colour, race, publisher_name, alignment, height_cm, weight_kg`; `gender_id`, `eye_colour_id`… "are mapped to their specific values"; `left join `colour` eye_colour on …`. Hình 2 (prompt nhờ LLM gợi ý view): tên bắt đầu bằng `v_`, chỉ dùng bảng gốc, gộp các bảng liên quan | `autoview.oracle_views`: mỗi mẫu JOIN của đáp án có bảng gốc → view `v_<bảng gốc>` nối các bảng cha trong mẫu đó bằng `left join`, chỉ dùng bảng gốc. Cột id trỏ tới **bảng tra cứu** (khóa `id` + một cột giá trị, như mọi trường hợp của Hình 3) được thay tại chỗ bằng giá trị; `v_superhero` sinh ra trùng Hình 3 cả 12 cột, thứ tự và cách viết. Khóa ngoại khác (`Patient.ID`, `raceId`, `molecule_id`, `year`…) là mã định danh có nghĩa nên giữ: nếu bỏ hết thì khoảng 130/500 đáp án dùng cột không còn trong view. Không dùng prompt Hình 2: paper nói view cuối cùng là thiết kế tay (mục 6, mục 7) |
| Schema D′ (mục 4.1, Hình 1A) | "D′ denotes the database schema composed of views. It is used to replace D" | Mọi view của CSDL + những bảng không nằm trong view nào (ở cả 11 CSDL không còn bảng nào như vậy, nên D′ chỉ gồm view). **Không có bước truy hồi / chọn view**: view đã được thiết kế từ đáp án của chính CSDL đó, đưa hết vào `{relevant_db_schema}` |
| Trình bày schema (Bảng 6) | `original_column_name, column_name, column_description, data_format` | Như Bảng 6, thêm `value_description`, `example_values` (paper không nói cách trình bày trong prompt; đây là loại thông tin TA-SQL nhận được); tên cột đặc biệt có backtick. Đây là điểm duy nhất thêm so với paper |
| Giai đoạn 1 (Hình 4) | Prompt Hình 4 | Đúng từng chữ (đã so lại 13/11). Evidence của BIRD nối vào `{query}` (paper không nói; mọi phương pháp đều dùng). Hình 4 không nêu phương ngữ SQL, không có khối định dạng: giữ nguyên |
| Giai đoạn 2 (Hình 5, mục 4.4, 4.5) | Prompt Hình 5; "the dummy SQL is not executed"; bảng liên quan lấy theo định nghĩa view mà dummy SQL dùng | Đúng từng chữ (13/11 sửa: paper viết `restore the sql in view query`, không có ngoặc kép; giữ cả lỗi chính tả `foramt`), `{db_type}` = SQLite. **Luôn chạy**, kể cả khi dummy SQL không dùng view. `{view_schemas}` = câu `create view` kiểu Hình 3 của các view mà dummy SQL dùng; `{table_schemas}` = bảng nguồn của các view đó + bảng mà dummy SQL truy vấn trực tiếp |
| Tham số (mục 5.1) | nhiệt độ 0, top-p 1, tối đa 800 token; không self-consistency, không sửa lỗi | như paper |

Mẫu JOIN 1-N (không có bảng gốc) không tạo view, vì paper không có loại view nhân bản dòng; 36/500 câu thuộc loại này phải nối hai view.

**Cái giá của D′ đúng paper:** 46/500 câu chỉ cần một bảng "cha" (vd đếm khách hàng, đếm cầu thủ) mà bảng đó chỉ còn nằm trong
view của bảng con, nên phải truy vấn qua view (số dòng khác). Với cài đặt `vsql_fair` cũ (có hiện bảng), V-SQL đúng 6/22 câu loại
này trong mẫu 200, TA-SQL 7/22.

### 2.1b Rà soát V-SQL ngày 13/11 (lần chạy qwen3.5:4b, mẫu 200 câu, cài đặt `vsql_fair` cũ)

Kết quả `results_new/ketqua_tasql_vsql_vsqlplus/cmp_qwen35_4b_d2025_mau200/`: TA-SQL 33,0%, DIN-SQL 29,5%, V-SQL (khi đó tên
`vsql_fair`) 24,0%. Đã dựng lại từng prompt (không gọi LLM) và đọc câu trả lời thô trong `llm_cache.sqlite`.

**Đã sửa (lỗi cài đặt):**
1. **Tên cột đặc biệt không được quote trong schema Bảng 6.** Mô hình tự chế tên `v_frpm.FRPM_Count_K_12`,
   `v_frpm.Enrollment (`K-12`)`, `l.T-CHO`: khoảng 9 câu lỗi cú pháp / sai tên cột, phần lớn ở `california_schools` (V-SQL và TA-SQL
   đều 0/12 ở CSDL này). TA-SQL ghi các tên này kèm backtick; nay V-SQL cũng vậy.
2. **`extract_sql` lấy nhầm chữ "with" trong văn xuôi làm đầu câu SQL** ("To find the league with the most …"). Ở 8/200 câu mô hình
   trả lời bằng văn xuôi: 7 câu không có SQL (trước đây tính là lỗi cú pháp, nay là `no_sql`), 1 câu (uid 160) có câu SQL nằm sau
   đoạn văn mà bản cũ cắt sai. Bản mới bắt đầu từ `SELECT` / `WITH <tên> AS (`. Đã kiểm tra trên cache của các lần chạy: không SQL
   nháp nào đang đúng bị đổi. Sửa này dùng chung cho V-SQL+, DIN-SQL, DAIL-SQL.

**Không phải lỗi cài đặt, giữ nguyên (paper quy định):**
- **Giai đoạn 2 (Hình 5) làm mất ròng 11 câu** (sửa đúng 6, làm hỏng 17, trong đó 11 câu `no such column`). Mô hình bỏ JOIN cần
  thiết, đúng như notice 1 của Hình 5 ("SQL should contain join as little as possible"), ví dụ dummy
  `SELECT v_Examination.SEX …` thành `SELECT Patient.SEX FROM Examination` không nối `Patient`.
- **Hình 4 không nêu phương ngữ SQL**: mô hình dùng `YEAR()`, `EXTRACT`, `TIMESTAMPDIFF` (MySQL), khoảng 19 câu giai đoạn 1 lỗi cú pháp.
  Hình 5 có yêu cầu SQLite, nhưng cài đặt cũ bỏ qua giai đoạn 2 khi dummy SQL không dùng view (53/200 câu, 8 câu lỗi cú pháp). Nay
  giai đoạn 2 luôn chạy (mục 2.1).
- **Hình 4 không có khối định dạng đầu ra** (Hình 5 có): 8 câu trả lời bằng văn xuôi, nhiều câu "mô phỏng" kết quả từ giá trị mẫu.

**Nguồn thua lớn nhất còn lại:** vì bảng tra cứu vẫn hiện cạnh view, **40/147** SQL nháp có dùng view lại JOIN thêm chính bảng
đã gộp trong view (vd `FROM v_member JOIN major ON …` dù `v_member` đã có `major_name`). Nhóm này chỉ đúng **5/40 (12,5%)**, so với
**30/107 (28%)** ở các SQL nháp không JOIN thừa. Hiện bảng tra cứu không có trong paper, nên đã bỏ (mục 2.1).

**Chọn view đưa vào prompt:** chú thích Hình 4 ghi schema là "description of tables related to the query, retrieved from a
database" nhưng paper không mô tả bước truy hồi nào. View đã được thiết kế từ đáp án của từng CSDL, nên bản tái hiện đưa mọi view
của CSDL vào prompt, không truy hồi. Prompt giai đoạn 1 trung bình khoảng 8.500 token (ký tự/4), `vsql_fair` cũ khoảng 9.850.

Ngoài ra, prompt V-SQL dài (trung bình 8.809 token, 7,2 đối tượng schema). TA-SQL chỉ đưa các cột đã liên kết vào bước sinh SQL.
Hai lần chạy TA-SQL trên cùng 200 câu, cùng model cho 36,0% và 33,0%, nên chênh lệch dưới khoảng 3–5 điểm trên mẫu 200 câu chưa
đáng tin.

### 2.2 TA-SQL (`tasql`) — baseline của paper

Cài theo mã chính thức https://github.com/quge2023/TA-SQL (`src/modules.py`, `src/prompt_bank.py`):

1. **TASL**: prompt `dummy_sql_prompt` gồm `database_schema` (mô tả cột từ `outputs/column_meaning.json` của TA-SQL, notebook
   tự tải), `primary_keys` và `foreign_keys` (từ `dev_tables.json`), câu hỏi, evidence. Gọi với `stop="return SQL"`. Sau đó
   trích các bảng và cột **xuất hiện như chuỗi con** trong dummy SQL, giống mã gốc.
2. **TALOG**: `generate_sr` với 7 ví dụ mẫu → biểu diễn ký hiệu SR kiểu pandas; rồi `sr2sql` → SQL. Mô tả cột cho TALOG lấy từ
   CSV của BIRD kèm "all possible values / example values", giống `_get_info_from_csv`.
3. System prompt "You are an AI assistant that helps people find information.", temperature 0, tối đa 800 token.

Prompt được chép **nguyên văn** (`vsql/tasql_prompts.py`, có kiểm tra trùng khớp từng ký tự với file gốc). Ba điểm khác,
cần thiết để chạy với mô hình chat và để chạy lại ra cùng kết quả:
- Mã gốc trả về `'SELECT ' + câu_trả_lời` vì GPT-4 viết tiếp sau `SQL = "SELECT`. Mô hình chat như qwen hay viết lại từ
  `SELECT` hoặc bọc trong khối ```` ```sql ````, nên hậu xử lý chấp nhận cả hai dạng (`methods._tasql_sql`).
- Mã gốc lấy giá trị mẫu bằng `ORDER BY RANDOM()` và duyệt cột theo thứ tự `set`, nên mỗi lần chạy ra prompt khác nhau. Ở đây
  dùng thứ tự cố định.
- Mã gốc xóa mọi dấu `"` trong SQL. Ở đây chỉ bỏ dấu `"` đóng chuỗi `SQL = "...`, vì mô hình nhỏ hay dùng `"..."` làm chuỗi.

### 2.2b DIN-SQL (`dinsql`) và DAIL-SQL (`dailsql`) — hai baseline còn lại của Bảng 3

Bảng 3 của paper so V-SQL với **DIN-SQL, DAIL-SQL và TA-SQL**. Mục 5.1 ghi: "To ensure fairness, none of the models utilized
self-consistency or re-modification mechanisms". Paper không ghi cách cài hai phương pháp này cho BIRD, nên dùng mã chính thức
của chính tác giả mỗi phương pháp, chỉ bỏ hai cơ chế mà paper loại:

| | DIN-SQL | DAIL-SQL |
|---|---|---|
| Mã gốc | [`DIN-SQL_BIRD.py`](https://github.com/MohammadrezaPourreza/Few-shot-NL2SQL-with-prompting/blob/0474801616130413b024fd008b016a190684649e/DIN-SQL_BIRD.py) | [`run_for_bird.sh`](https://github.com/BeachWang/DAIL-SQL/blob/2061f68112222083134a0c9e2877961ff315ff44/run_for_bird.sh) |
| Các bước | Liên kết schema → phân loại EASY / NON-NESTED / NESTED → sinh SQL theo loại (CoT, nhiều ví dụ) | Schema dạng `CREATE TABLE` (lấy từ `sqlite_master`) + 7 ví dụ câu hỏi–SQL từ tập train BIRD, prompt kết thúc bằng `SELECT ` |
| Chọn ví dụ | Ví dụ cố định trong prompt | Vòng 1: khoảng cách Euclid giữa embedding câu hỏi đã che tên bảng/cột (`all-mpnet-base-v2`); vòng 2: ưu tiên ví dụ có khung SQL giống khung SQL của câu trả lời vòng 1 (Jaccard ≥ 0,85) |
| Bỏ theo paper | **Bước tự sửa lỗi** (self-correction) | **Bầu chọn nhiều mẫu** (mã gốc mặc định `n=5`); ở đây 1 mẫu |
| Lượt gọi LLM / câu | 3 | 2 (vòng 1 chỉ để lấy khung SQL) |
| Prompt | `vsql/din_prompts.py`, trích tự động nguyên văn từ file gốc | Chép nguyên văn các mẫu `SQLPrompt` + `QuestionSqlExampleStyle` |

Chung với mọi phương pháp: nhiệt độ 0, tối đa 800 token (paper), evidence của BIRD (DIN-SQL đưa vào dòng `Hint:`, DAIL-SQL nối
vào sau câu hỏi như `bird_pre_process(with_evidence=True)`).

**Điểm khác buộc phải có:**
- **DIN-SQL:** mã gốc dựng schema bằng LangChain `SQLDatabase.get_table_info` (CREATE TABLE + 3 dòng mẫu). Ở đây dựng lại đúng
  định dạng đó bằng SQLAlchemy (thư viện mà LangChain dùng bên dưới), không cài LangChain. File mô tả cột đọc theo thứ tự tên
  file (mã gốc dùng `glob`, thứ tự không cố định). Nếu không đọc được nhãn phân loại, mã gốc báo lỗi; ở đây đi vào nhánh NESTED
  (nhánh cuối của mã gốc).
- **DAIL-SQL:** mã gốc che tên schema trong câu hỏi bằng Stanford CoreNLP (server Java) + GloVe; ở đây dùng **spaCy
  `en_core_web_sm`** để tách từ và lấy lemma, thuật toán khớp n-gram (`compute_schema_linking`, `match_shift`) chép nguyên văn.
  Thư viện `sql_metadata` phải là bản 2.x (bản 3.x đổi API, làm hỏng hàm tạo khung SQL). Tập train lấy đúng 2 file
  `train.json`, `train_tables.json` trong `train.zip` chính thức (đọc bằng HTTP Range, kiểm tra md5), không tải cả 8,9 GB.
- **Cả hai:** mô hình chat hay bọc SQL trong ```` ```sql ````; nếu có khối code thì lấy SQL trong khối đó, rồi hậu xử lý như
  mã gốc.

### 2.3 Phạm vi so sánh

So sánh chính: **TA-SQL, V-SQL, V-SQL+**. Muốn đầy đủ như Bảng 3 thì chạy thêm **DIN-SQL, DAIL-SQL** (tùy chọn trong notebook).
Trong paper, V-SQL hơn DIN-SQL và DAIL-SQL từ 3 đến 9 điểm ở cả ba model, còn so với TA-SQL thì chỉ ngang.

### 2.4 Chấm điểm

EX theo định nghĩa của BIRD (so tập dòng kết quả), timeout 30 giây. Mỗi cặp phương pháp được so ghép cặp trên cùng 500 câu
bằng kiểm định McNemar chính xác, hiệu chỉnh Holm, kèm khoảng tin cậy bootstrap 95% của ΔEX. Báo cáo so với `tasql`
và `vsql`.

---

## 3. V-SQL+ (`vsqlplus`)

V-SQL+ giữ nguyên khung hai giai đoạn của paper (giai đoạn 1 sinh dummy SQL trên view, giai đoạn 2 LLM khôi phục về bảng gốc
bằng prompt Hình 5) và **kết hợp cải thiện hai phần mà paper để ngỏ**:

- **Hướng 1 – Tự động sinh view** (paper: "the design of table mappings requires manual effort").
- **Hướng 2 – Chọn view cho đúng bằng truy hồi lai** (paper: "as the number of views increases, it becomes more challenging
  to retrieve the correct view"). Truy hồi lai BM25 + embedding là lõi; liên kết giá trị, truy hồi mức cột, bầu chọn nhiều mẫu,
  schema lai và quy tắc "CSDL nhỏ thì đưa hết" là các thành phần bổ trợ cho việc chọn view.

```
Hướng 1: view tự động (FK N-1, kiểm số dòng) ─► schema D⁺ = view + bảng không có view
Hướng 2: chọn view
   CSDL nhỏ (≤ 4 đối tượng hoặc ≤ 3.500 token)? ── có ──► đưa hết view vào prompt
   không ▼
   xếp hạng = RRF( truy hồi lai mức cột gộp lên view, truy hồi lai mức view, liên kết giá trị ×2 )
   5 ứng viên ─► 4 dummy SQL (1 tham lam + 3 mẫu, T = 0,7) ─► tập view xuất hiện nhiều nhất
   ▼
giai đoạn 1: dummy SQL (T = 0) trên các view đã chọn, kèm "giá trị khớp trong DB"
   └─ schema lai: dummy SQL dùng cột/bảng không tồn tại (biên dịch thử EXPLAIN) ─► thêm bảng gốc chứa cột đó, sinh lại (≤ 2 lần)
giai đoạn 2 (như paper, Hình 5): LLM khôi phục dummy SQL về bảng gốc
```

**Hướng 1 – Tự động sinh view** (`autoview.py`)

| Việc | Cài đặt |
|---|---|
| Dựng view | Mỗi bảng có khóa ngoại → `v_<bảng>` = bảng đó `LEFT JOIN` các bảng cha theo chiều N-1; mức nối thứ 2 chỉ nối bảng tra cứu nhỏ (≤ 4 cột, vd `colour`); tối đa 60 cột/view |
| Đúng đắn | Chỉ nối khi khóa được tham chiếu là duy nhất (kiểm tra bằng SQL), sau đó kiểm tra `COUNT(*)` view = bảng gốc |
| Khóa ngoại thiếu | Suy thêm theo tên cột + kiểm tra bao hàm giá trị (`debit_card_specializing` thiếu 3 FK) |
| Tên cột | Sạch như Hình 3: giữ tên gốc; trùng tên hoặc nối cùng bảng nhiều lần thì dùng tên vai trò (`eye_colour_id` → `eye_colour`) |
| Mô tả | Mỗi cột ghi nguồn (`customers.Currency via transactions_1k.CustomerID`), mô tả từ `database_description` và giá trị mẫu, để khớp được với evidence |
| Schema D⁺ | View chỉ thay bảng gốc của chính nó; bảng không có view (bảng tra cứu, bảng thực thể như `customers`) vẫn hiện — khác D′ của paper |

**Hướng 2 – Chọn view bằng truy hồi lai** (`linking.py`, `methods.plus_rank`, `methods.run_plus`)

| Thành phần | Cài đặt |
|---|---|
| Tài liệu cho mỗi view | Tên view, danh sách cột, mô tả cột (`database_description`), vài giá trị mẫu |
| Truy hồi lai | BM25 + embedding (`nomic-embed-text` qua Ollama, có cache), hợp nhất bằng RRF |
| Truy hồi mức cột rồi gộp lên view | Điểm view = tổng điểm 3 cột tốt nhất của nó; hợp với xếp hạng mức view |
| Liên kết giá trị | Chỉ mục mọi giá trị văn bản (≤ 80 ký tự) trong DB; khớp n-gram 1–6 từ và chuỗi trong nháy của câu hỏi + evidence (vd "Dark Horse Comics" → `publisher.publisher_name`). Tín hiệu có trọng số gấp đôi trong RRF; view chứa giá trị khớp mạnh luôn được giữ; giá trị khớp được ghi vào prompt |
| Bầu chọn nhiều mẫu | 4 dummy SQL trên 5 ứng viên; chọn tập view xuất hiện nhiều nhất, cộng các view có mặt trong hơn nửa số mẫu |
| Schema lai | Dummy SQL dùng cột hoặc bảng không có trong view được cung cấp → thêm bảng gốc chứa cột đó vào prompt, kèm ghi chú cột đó nằm ở đâu, rồi sinh lại |
| Ít view thì đưa hết | 6/11 CSDL đủ nhỏ để đưa hết; chỉ 5 CSDL lớn (card_games, codebase_community, european_football_2, formula_1, student_club; 266/500 câu) qua bước xếp hạng + bầu chọn |

**Hai bản V-SQL+:**

| | `vsqlplus` | `vsqlplus_fig4` |
|---|---|---|
| Hướng 1 (view tự động) + hướng 2 (chọn view) | có | có |
| Template giai đoạn 1 | prompt mới (`P_PLUS`) | **Hình 4 nguyên văn**, như `vsql` |
| Trình bày schema | `CREATE VIEW` có nguồn gốc cột, mô tả, giá trị mẫu | **Bảng 6 mở rộng, như `vsql`** (cả giai đoạn 2) |
| Giá trị khớp trong DB | dùng để xếp hạng và ghi vào prompt | chỉ dùng để xếp hạng |
| Schema lai | thêm bảng gốc + ghi chú cột nằm ở đâu | chỉ thêm bảng gốc |
| Evidence | mục `# evidence` riêng | nối vào `{query}` như V-SQL |

So sánh sạch nhất cho 2 hướng: `vsqlplus_fig4` − `vsql`. Tác dụng riêng của prompt mới: `vsqlplus` − `vsqlplus_fig4`.

**Các biến thể đối chiếu** (bật `ABLATION` trong notebook):

| Biến thể | Ý nghĩa |
|---|---|
| `vsqlplus_all` | **Chỉ hướng 1**: view tự động, đưa hết view vào prompt, không dùng thành phần nào của hướng 2. So với `vsql` → đóng góp của hướng 1; `vsqlplus` so với nó → đóng góp của hướng 2 |
| `vsqlplus_novote`, `vsqlplus_novl`, `vsqlplus_nofb` | Bỏ lần lượt bầu chọn, liên kết giá trị, schema lai |
| `vsqlplus_det` | Thay giai đoạn 2 của paper bằng giải mã tất định (CTE). Không thuộc đề xuất, chỉ để đối chiếu; dùng lại dummy SQL đã có nên không tốn thêm lượt gọi |

**Kiểm chứng đã làm (không cần GPU):**
- 11/11 CSDL: mọi view (cả của V-SQL lẫn V-SQL+) có `COUNT(*)` bằng bảng gốc.
- Độ phủ bảng đáp án của bước chọn view (BM25 + liên kết giá trị, **chưa** có embedding và bầu chọn) trên 266 câu thuộc
  5 CSDL lớn: top-1 82,3%, top-2 90,2%, top-3 97,7%, top-4 99,6%, top-5 100%.
- `tests/test_compare.py`: đường ống đủ các phương pháp và biến thể với LLM giả lập; từ chối file câu hỏi có `question_id` lặp (bản 2024); tách bản ghi của cài đặt V-SQL cũ.

**Chi phí:** V-SQL+ gọi LLM nhiều hơn V-SQL ở 5 CSDL lớn (4 mẫu bầu chọn + 1 lần sinh dummy SQL + 1 lần khôi phục). Báo cáo
ghi số lượt gọi và số token cho mỗi phương pháp. Bầu chọn chỉ dùng để **chọn view**, không bầu theo kết quả thực thi; schema
lai chỉ biên dịch thử, không xem kết quả chạy.

---

## 4. Chạy

Notebook `notebooks/TASQL_VSQL_VSQLplus_Colab.ipynb` (GPU T4): chọn model (`qwen3.5:0.8b`, `qwen3:8b`, `qwen3.5:9b`), chạy
lần lượt các ô. Notebook clone repo từ GitHub, nên **cần push mã mới lên `main` trước**. Kết quả lưu vào
`MyDrive/vsqlplus_ketqua/cmp_<model>_d2025/` (`summary.md`, `summary.csv`, `predictions_<phương pháp>.jsonl`); nếu Colab ngắt thì
chạy lại, phần đã xong được bỏ qua.

Dòng lệnh tương đương:

```bash
D=minidev/MINIDEV
python run_compare.py --data $D/mini_dev_sqlite_2025-07-04.json --db-root $D/dev_databases --tables-json $D/dev_tables.json \
    --tasql-meaning column_meaning.json --model qwen3:8b --out results/cmp_qwen3_8b_d2025      # tasql, vsql, vsqlplus
python run_compare.py ... --methods all                                                        # + 4 biến thể ablation
python run_compare.py ... --views-only                                                         # chỉ sinh view
python run_compare.py ... --selection-sweep --no-embed                                         # độ phủ bước chọn view
python tests/test_compare.py                                                                   # kiểm thử
```

Ước tính trên T4: khoảng 5.000 lượt gọi LLM cho mỗi model (4 phương pháp × 500 câu). `qwen3.5:0.8b` mất khoảng 1–2 giờ;
`qwen3:8b` và `qwen3.5:9b` mỗi model khoảng 6–10 giờ, nên chạy mỗi model một phiên.

## 5. Còn bỏ ngỏ

- **Chưa có số EX nào cho cấu hình mới**: cần chạy trên Colab. Không có số nào trong tài liệu này là kết quả của mã mới trên BIRD.
- View của `vsql` nhìn SQL đáp án của chính tập đánh giá, như paper làm, nên `vsql` có lợi thế mà V-SQL+ (view tự động) không có.
- Số tuyệt đối không so được với Bảng 3 của paper (khác model). Điều so được là thứ tự và độ chênh giữa TA-SQL, V-SQL và
  V-SQL+ trên cùng một model.
