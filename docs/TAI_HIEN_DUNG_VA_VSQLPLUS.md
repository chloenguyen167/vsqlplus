# Tái hiện lại V-SQL cho đúng, so với TA-SQL, và cải tiến V-SQL+

Tài liệu này ghi lại: (1) kết quả kiểm tra phần tái hiện cũ và vì sao baseline luôn hơn V-SQL; (2) cách tái hiện lại cho đúng
paper, với TA-SQL là baseline; (3) thiết kế cải tiến V-SQL+; (4) cách chạy trên Colab T4.

Mã mới: `vsql/methods.py`, `vsql/autoview.py`, `vsql/linking.py`, `vsql/meta.py`, `vsql/tasql_prompts.py`, `run_compare.py`,
`tests/test_compare.py`, `notebooks/TASQL_VSQL_VSQLplus_Colab.ipynb`. Mã cũ (CT1–CT8, `run_experiment.py`, `improve.py`)
vẫn giữ nguyên để đối chiếu.

---

## 1. Kiểm tra phần tái hiện cũ

### 1.1 Bộ dữ liệu: 500 câu, không phải 498

`mini_dev_sqlite.json` có **500 dòng**. Trong đó `question_id` 137 và 138 mỗi mã xuất hiện hai lần (dòng 484 ≡ 487 và
485 ≡ 488, nội dung giống hệt nhau, cùng là câu `moderate` của `financial`). Đây là dữ liệu gốc của BIRD, không phải lỗi
tải về. Bộ chấm chính thức của BIRD chấm theo vị trí dòng (500 dòng), và Bảng 2 của paper đếm 148 + 250 + 102 = 500.

Mã cũ dùng `question_id` làm khóa (`report.load`: `{r["qid"]: r}`), nên hai cặp dòng bị gộp thành 498. **Đây là lỗi của mã,
không phải của dữ liệu.** Mã mới định danh mỗi câu bằng vị trí dòng (`uid` = 0..499), nên tính đủ 500 câu; đã sửa cả trong
`run_experiment.py` và `vsql/report.py`.

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
   Câu "tỉ lệ khách hàng trả EUR/CZK" buộc phải đếm qua `v_yearmonth`, nên đếm số dòng tháng thay vì số khách (uid 1471, 1486). Đây là đúng thiết kế D′ của paper, nên `vsql` vẫn giữ; V-SQL+ xử lý ở hướng 1.
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

### 2.1 V-SQL (`vsql`) — giữ đúng theo paper

| Thành phần | Paper | Cài đặt |
|---|---|---|
| Dữ liệu | BIRD mini-dev, 500 câu | như paper, đủ 500 câu |
| View | Thiết kế theo các phép JOIN trong SQL đáp án (mục 6), kiểu Hình 3 | `autoview.oracle_views`: mỗi mẫu JOIN trong đáp án có một bảng gốc (từ đó đi tới mọi bảng khác theo chiều N-1) → một view `v_<bảng gốc>` nối các bảng cha trong mẫu đó, `LEFT JOIN` như Hình 3 |
| Tên cột view | Hình 3: `eye_colour`, `publisher_name` | như Hình 3 |
| Schema D′ | các view thay cho các bảng (mục 4.1, Hình 1A) | các view + những bảng không nằm trong view nào; bảng đã gộp vào view không hiện riêng |
| Cách trình bày schema | Bảng 6: `original_column_name, column_name, column_description, data_format`, đánh dấu khóa ngoại | như Bảng 6 (khóa ngoại ghi thành dòng `foreign keys`) |
| Prompt giai đoạn 1 | Hình 4 | Hình 4 nguyên văn |
| Giai đoạn 2 | LLM khôi phục, prompt Hình 5 | Hình 5 nguyên văn (`{db_type}` = SQLite); view schemas = câu `CREATE VIEW` của các view mà dummy SQL dùng; table schemas = các bảng nguồn (trình bày như Bảng 6) |
| Tham số | temperature 0, top-p 1, tối đa 800 token | như paper |

Những điểm paper không công bố hoặc không nói rõ, nên phải chọn một cách làm:
- **View cụ thể**: paper không công bố view viết tay. View được dựng tự động đúng theo quy trình paper mô tả (dựa trên JOIN
  của đáp án, kiểu Hình 3). Mẫu JOIN 1-N (không có bảng gốc) không tạo view, vì paper không có loại view nhân bản dòng.
- **Evidence**: Hình 4 chỉ có `{relevant_db_schema}` và `{query}`, và paper không nói có dùng evidence hay không. Template giữ
  nguyên; evidence của BIRD được nối vào nội dung `{query}` sau câu hỏi, giống mọi phương pháp khác. Tắt bằng
  `--vsql-evidence none`.

Việc D′ ẩn các bảng đã gộp vào view (vd `customers`, xem 1.3 ý 3) là thiết kế của paper nên được giữ nguyên trong `vsql`.
V-SQL+ xử lý điểm này ở hướng 1.

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

### 2.3 Phạm vi so sánh

Chỉ so sánh **TA-SQL, V-SQL, V-SQL+**, đúng như paper (V-SQL so với TA-SQL). Cấu hình zero-shot `base` không thuộc so sánh;
mã vẫn giữ (`--methods base`) nhưng notebook không chạy.

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
- `tests/test_compare.py`: đường ống đủ 4 phương pháp và 4 biến thể với LLM giả lập, kể cả bản ghi trùng lặp.

**Chi phí:** V-SQL+ gọi LLM nhiều hơn V-SQL ở 5 CSDL lớn (4 mẫu bầu chọn + 1 lần sinh dummy SQL + 1 lần khôi phục). Báo cáo
ghi số lượt gọi và số token cho mỗi phương pháp. Bầu chọn chỉ dùng để **chọn view**, không bầu theo kết quả thực thi; schema
lai chỉ biên dịch thử, không xem kết quả chạy.

---

## 4. Chạy

Notebook `notebooks/TASQL_VSQL_VSQLplus_Colab.ipynb` (GPU T4): chọn model (`qwen3.5:0.8b`, `qwen3:8b`, `qwen3.5:9b`), chạy
lần lượt các ô. Notebook clone repo từ GitHub, nên **cần push mã mới lên `main` trước**. Kết quả lưu vào
`MyDrive/vsqlplus_ketqua/cmp_<model>/` (`summary.md`, `summary.csv`, `predictions_<phương pháp>.jsonl`); nếu Colab ngắt thì
chạy lại, phần đã xong được bỏ qua.

Dòng lệnh tương đương:

```bash
D=minidev/MINIDEV
python run_compare.py --data $D/mini_dev_sqlite.json --db-root $D/dev_databases --tables-json $D/dev_tables.json \
    --tasql-meaning column_meaning.json --model qwen3:8b --out results/cmp_qwen3_8b            # 4 phương pháp chính
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
