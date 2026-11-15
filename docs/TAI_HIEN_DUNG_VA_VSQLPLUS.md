# Thiết kế V-SQL (tái hiện), V-SQL+ (cải tiến) và DAIL-SQL (baseline)

Tài liệu mô tả đúng những gì mã hiện tại làm, và chỗ nào khác paper. Kết quả chạy nằm ở
[NHAN_XET_KET_QUA_GPT4OMINI.md](NHAN_XET_KET_QUA_GPT4OMINI.md) và [NHAN_XET_KET_QUA_500CAU.md](NHAN_XET_KET_QUA_500CAU.md); cách chạy
ở [README](../README.md).

Mã: `vsql/methods.py` (phương pháp, prompt, chấm điểm), `vsql/autoview.py` (dựng view), `vsql/views.py` (kiểm tra và giải mã view),
`vsql/linking.py` (BM25, embedding, liên kết giá trị), `vsql/meta.py` (mô tả cột, schema kiểu Bảng 6), `vsql/baselines.py`
(DAIL-SQL), `run_compare.py` (chạy và tổng hợp), `tests/test_compare.py` (kiểm thử).

---

## 1. Dữ liệu

BIRD mini-dev, bản câu hỏi **2025-07-04** trên Hugging Face (`birdsql/bird_mini_dev`, commit `f65faf4`, md5 `595b6b01…`): 500 câu
khác nhau, 11 CSDL, độ khó 148 / 250 / 102 như Bảng 2 của paper. CSDL, `dev_tables.json` và mô tả cột lấy từ zip OSS
(`minidev.zip`).

Không dùng `mini_dev_sqlite.json` trong zip OSS (bản 2024-06): file đó có 2 câu lặp (`question_id` 137, 138) nên chỉ có 498 câu khác
nhau. `run_compare.py` từ chối file có `question_id` lặp. Bản Hugging Face mới nhất (sau 2026-10) đã viết lại câu hỏi, không so được
với paper nên cũng không dùng. Mỗi câu được định danh theo vị trí dòng (`uid` = 0..499); notebook kiểm tra md5 của file câu hỏi.

---

## 2. V-SQL (`vsql`): bản tái hiện

Một bản duy nhất, phiên bản cài đặt `IMPL["vsql"] = 7` trong `vsql/methods.py`. Đổi cách cài đặt thì tăng số này; bản ghi cũ trong thư
mục kết quả được tách ra `old_predictions_vsql_*.jsonl` và chấm lại (câu trả lời LLM vẫn nằm trong cache).

| Thành phần | Paper | Cài đặt |
|---|---|---|
| View (mục 6, Hình 3) | Thiết kế tay theo các phép JOIN trong SQL đáp án. Hình 3: `v_superhero` có 12 cột `id, superhero_name, full_name, gender, eye_colour, …, height_cm, weight_kg`; `gender_id`, `eye_colour_id`… được thay bằng giá trị | `autoview.oracle_views`: mỗi mẫu JOIN của SQL đáp án có một bảng gốc → view `v_<bảng gốc>` nối các bảng cha của mẫu đó bằng `LEFT JOIN`. Cột id trỏ tới **bảng tra cứu** (`id` + một cột giá trị: `gender`, `colour`, `race`…) được thay tại chỗ bằng giá trị. Các khoá ngoại khác (`Patient.ID`, `raceId`, `molecule_id`…) là mã định danh có nghĩa nên giữ. `v_superhero` sinh ra trùng Hình 3 cả 12 cột và thứ tự. Mẫu JOIN 1-N (không có bảng gốc) không tạo view vì paper không có view nhân bản dòng. Tổng 46 view cho 11 CSDL |
| D′ (mục 4.1, Hình 1A) | D′ là schema gồm các view, thay cho D | Mọi view + các bảng chưa bị view thay thế. Chỉ bảng gốc của view và bảng tra cứu đã được view thay trọn mới biến mất; bảng thực thể (`Patient`, `users`, `customers`…) vẫn hiện, vì câu hỏi chỉ về chính bảng đó (đếm bệnh nhân, đếm khách) không trả lời đúng được qua view của bảng con |
| Chọn đối tượng của D′ (Hình 1 "Relevant Views", chú thích Hình 4) | Có bước truy hồi theo câu hỏi, **không nói cách làm** | **Phần tự thêm.** Mặc định `--vsql-select llm`: 1 lần gọi LLM (`P_VSQL_SEL`) nhận danh mục D′ (mỗi dòng: view + bảng gốc + tên cột, hoặc bảng + tên cột) và `{query}`, trả về tên đối tượng cần dùng; chương trình khớp tên nguyên từ, không khớp tên nào thì đưa hết D′ (`sel_fallback`). Còn `bm25` (top-k theo `--vsql-topk`, mặc định 4) và `all` (đưa hết) để đối chiếu. Không cách nào nhìn SQL đáp án. CSDL chỉ có 1 đối tượng thì bỏ qua bước này |
| Schema trong prompt (Bảng 6) | `original_column_name, column_name, column_description, data_format` | Như Bảng 6, thêm hai cột `value_description`, `example_values`. Tên cột đặc biệt (dấu cách, ngoặc, dấu trừ) ghi kèm backtick để LLM không tự chế tên. Paper không nói cách trình bày schema trong prompt; đây là phần tự thêm |
| Giai đoạn 1 | Prompt Hình 4 | Nguyên văn. Evidence của BIRD nối vào `{query}` (`--vsql-evidence query`; mọi phương pháp đều dùng evidence). Hình 4 không nêu phương ngữ SQL và không có khối định dạng đầu ra: giữ nguyên |
| Giai đoạn 2 | Prompt Hình 5; dummy SQL không được thực thi; bảng liên quan lấy theo định nghĩa view (mục 4.5) | Nguyên văn (kể cả lỗi chính tả `foramt`), `{db_type}` = SQLite. **Luôn chạy**, kể cả khi dummy SQL không dùng view. `{view_schemas}` = câu `create view` của các view dummy SQL dùng; `{table_schemas}` chỉ gồm bảng mà dummy SQL thực sự dùng cột của view, cộng bảng mà nó truy vấn trực tiếp |
| Tham số (mục 5.1) | Nhiệt độ 0, tối đa 800 token, không self-consistency, không sửa lỗi | Như paper |

Số lần gọi LLM: 3 mỗi câu (chọn đối tượng, giai đoạn 1, giai đoạn 2).

**Lợi thế của V-SQL so với V-SQL+:** view của V-SQL được dựng từ SQL đáp án của chính tập đánh giá (như paper làm), còn view của
V-SQL+ thì không nhìn đáp án.

---

## 3. V-SQL+ (`vsqlplus`)

V-SQL+ giữ khung hai giai đoạn của paper (giai đoạn 1 sinh dummy SQL trên view, giai đoạn 2 khôi phục về bảng gốc bằng Hình 5, giống
hệt V-SQL) và cải tiến hai việc mà paper để ngỏ:

- **Hướng 1, tự động sinh view** (paper: "the design of table mappings requires manual effort").
- **Hướng 2, chọn đúng view bằng truy hồi lai** (paper: "as the number of views increases, it becomes more challenging to retrieve the
  correct view"). Lõi là truy hồi lai BM25 + embedding; liên kết giá trị, bầu chọn, schema lai và quy tắc "CSDL nhỏ thì đưa hết" bổ trợ.

```
Hướng 1: view tự động (khoá ngoại N-1, kiểm số dòng) → schema = view + bảng không bị view thay thế
Hướng 2: chọn view
   CSDL nhỏ (≤ 4 đối tượng hoặc ≤ 3.500 token)? ── có ──► đưa hết vào prompt
   không ▼
   xếp hạng = RRF(truy hồi mức cột gộp lên view, truy hồi mức view, liên kết giá trị ×2)
   5 ứng viên → 4 dummy SQL (1 tham lam + 3 mẫu, T = 0,7) → tập view xuất hiện nhiều nhất
   ▼
giai đoạn 1: dummy SQL (T = 0) trên các view đã chọn, prompt `P_PLUS`, kèm "giá trị khớp trong DB"
   └─ schema lai: dummy SQL dùng cột/bảng không có (biên dịch thử) → thêm bảng gốc chứa cột đó, sinh lại (≤ 2 lần)
giai đoạn 2 (Hình 5, như V-SQL): khôi phục về bảng gốc; dummy SQL không dùng view thì giữ nguyên
```

**Hướng 1: tự động sinh view** (`autoview.auto_views`, `views.validate`)

| Việc | Cài đặt |
|---|---|
| Dựng view | Mỗi bảng có khoá ngoại → `v_<bảng>` = bảng đó `LEFT JOIN` các bảng cha theo chiều N-1. Mức nối thứ 2 trở đi chỉ nối bảng tra cứu nhỏ (≤ 4 cột); tối đa 60 cột mỗi view. Tổng 42 view cho 11 CSDL |
| Đúng đắn | Chỉ nối khi khoá được tham chiếu là duy nhất (kiểm bằng SQL); sau đó kiểm tra `COUNT(*)` của view bằng của bảng gốc (đạt ở cả 11 CSDL, cả view của V-SQL) |
| Khoá ngoại thiếu | Suy thêm theo tên cột và kiểm tra bao hàm giá trị (`debit_card_specializing` thiếu 3 khoá ngoại) |
| Tên cột | Sạch như Hình 3: giữ tên gốc; trùng tên hoặc nối cùng bảng nhiều lần thì dùng tên vai trò (`eye_colour_id` → `eye_colour`) |
| Mô tả | Mỗi cột ghi nguồn (ví dụ `customers.Currency via transactions_1k.CustomerID`), mô tả từ `database_description` và giá trị mẫu, để khớp được với evidence |
| Schema | View chỉ thay bảng gốc của chính nó; mọi bảng khác (bảng tra cứu, bảng thực thể) vẫn hiện |

**Hướng 2: chọn view bằng truy hồi lai** (`linking.py`, `methods.plus_rank`, `methods.run_plus`)

| Thành phần | Cài đặt |
|---|---|
| Truy hồi lai | BM25 + embedding (`nomic-embed-text` qua Ollama, có cache; `--no-embed` = chỉ BM25), hợp nhất bằng RRF |
| Truy hồi mức cột rồi gộp lên view | Điểm view = tổng điểm 3 cột tốt nhất của nó |
| Liên kết giá trị | Chỉ mục mọi giá trị văn bản (≤ 80 ký tự) trong DB; khớp n-gram 1–6 từ và chuỗi trong nháy của câu hỏi + evidence (ví dụ "Dark Horse Comics" → `publisher.publisher_name`). Trọng số gấp đôi trong RRF; view chứa giá trị khớp mạnh luôn được giữ; giá trị khớp được ghi vào prompt |
| Bầu chọn nhiều mẫu | 4 dummy SQL trên 5 ứng viên; chọn tập view xuất hiện nhiều nhất, cộng các view có mặt trong hơn nửa số mẫu |
| Schema lai | Dummy SQL dùng cột hoặc bảng không có trong view được cung cấp (biên dịch thử, không xem kết quả chạy) → thêm bảng gốc chứa cột đó, kèm ghi chú cột đó nằm ở đâu, rồi sinh lại, tối đa 2 lần |
| CSDL nhỏ thì đưa hết | 6/11 CSDL đủ nhỏ để đưa hết view; chỉ 5 CSDL lớn (`card_games`, `codebase_community`, `european_football_2`, `formula_1`, `student_club`; 266/500 câu) đi qua xếp hạng và bầu chọn |

Bầu chọn chỉ dùng để **chọn view**, không bầu theo kết quả thực thi. Số lần gọi LLM: khoảng 6 ở 5 CSDL lớn (4 mẫu bầu chọn + dummy SQL + giai đoạn 2), khoảng 2 ở CSDL nhỏ
(thêm 1 lần mỗi lần sửa lỗi bằng schema lai); trung bình 4,04 mỗi câu với gpt-4o-mini.

**Hai bản V-SQL+**

| | `vsqlplus` | `vsqlplus_fig4` |
|---|---|---|
| Hướng 1 + hướng 2 | có | có |
| Template giai đoạn 1 | prompt mới `P_PLUS` | Hình 4 nguyên văn, như `vsql` |
| Trình bày schema | `CREATE VIEW` có nguồn gốc cột, mô tả, giá trị mẫu | Bảng 6 mở rộng, như `vsql` (cả giai đoạn 2) |
| Giá trị khớp trong DB | xếp hạng và ghi vào prompt | chỉ xếp hạng |
| Schema lai | thêm bảng gốc + ghi chú cột nằm ở đâu | chỉ thêm bảng gốc |
| Evidence | mục `# evidence` riêng | nối vào `{query}` như V-SQL |

So sánh sạch nhất cho hai hướng cải tiến: `vsqlplus_fig4` − `vsql`. Tác dụng riêng của prompt mới: `vsqlplus` − `vsqlplus_fig4`.

**Biến thể đối chiếu** (ô `ABLATION` trong notebook Colab hoặc `--methods all`)

| Biến thể | Ý nghĩa |
|---|---|
| `vsqlplus_all` | Chỉ hướng 1: view tự động, đưa hết view vào prompt, không dùng thành phần nào của hướng 2 |
| `vsqlplus_novote`, `vsqlplus_novl`, `vsqlplus_nofb` | Bỏ lần lượt bầu chọn, liên kết giá trị, schema lai |
| `vsqlplus_det` | Thay giai đoạn 2 bằng giải mã tất định (view → CTE). Không thuộc đề xuất, chỉ để đo; dùng lại dummy SQL nên không tốn thêm lượt gọi |

---

## 4. DAIL-SQL (`dailsql`): baseline của Bảng 3

Paper (mục 5.1): "To ensure fairness, none of the models utilized self-consistency or re-modification mechanisms". Paper không ghi cách
cài DAIL-SQL cho BIRD nên dùng mã chính thức của tác giả
([`run_for_bird.sh`](https://github.com/BeachWang/DAIL-SQL/blob/2061f68112222083134a0c9e2877961ff315ff44/run_for_bird.sh)), chỉ bỏ cơ chế
mà paper loại.

| | DAIL-SQL |
|---|---|
| Prompt | Schema dạng `CREATE TABLE` (lấy từ `sqlite_master`) + 7 ví dụ câu hỏi–SQL từ tập train BIRD, kết thúc bằng `SELECT `. Các mẫu `SQLPrompt`, `QuestionSqlExampleStyle` chép nguyên văn |
| Chọn ví dụ | Vòng 1: khoảng cách Euclid giữa embedding (`all-mpnet-base-v2`) của câu hỏi đã che tên bảng/cột. Vòng 2: ưu tiên ví dụ có khung SQL giống khung SQL của câu trả lời vòng 1 (Jaccard ≥ 0,85) |
| Bỏ theo paper | Bầu chọn nhiều mẫu (mã gốc mặc định `n=5`); ở đây 1 mẫu, nhiệt độ 0 |
| Số lần gọi LLM | 2 mỗi câu (vòng 1 chỉ để lấy khung SQL) |

Chung với mọi phương pháp: tối đa 800 token, dùng evidence của BIRD (nối sau câu hỏi như `bird_pre_process(with_evidence=True)`).

**Điểm khác buộc phải có:** mã gốc che tên schema bằng Stanford CoreNLP (server Java) + GloVe; ở đây dùng **spaCy `en_core_web_sm`** để
tách từ và lấy lemma, còn thuật toán khớp n-gram (`compute_schema_linking`, `match_shift`) chép nguyên văn. `sql_metadata` phải là bản
2.x (bản 3.x đổi API, làm hỏng hàm tạo khung SQL). Tập train lấy đúng hai file `train.json`, `train_tables.json` trong `train.zip`
chính thức bằng HTTP Range, không tải cả 8,9 GB. Câu trả lời có khối ` ```sql ` thì lấy SQL trong khối đó, rồi hậu xử lý như mã gốc.
Xử lý trước tập train (che tên + embedding 9.428 câu) mất khoảng 8 phút trên CPU và được lưu cache.

---

## 5. Chấm điểm và so sánh

- **EX** theo định nghĩa của BIRD: so tập dòng kết quả; timeout 30 giây.
- Mỗi cặp phương pháp so ghép cặp trên cùng 500 câu bằng kiểm định McNemar chính xác, hiệu chỉnh Holm, kèm khoảng tin cậy bootstrap
  95% của ΔEX; `summary.md` so với `dailsql` và `vsql`.
- **Tách hai giai đoạn** (không tốn thêm lượt gọi): `stage1_sql` là dummy SQL mở rộng tất định về bảng gốc (view → CTE), dùng để đo riêng
  giai đoạn 1 và xem giai đoạn 2 sửa đúng hay làm hỏng bao nhiêu câu. Với DAIL-SQL, "giai đoạn 1" là SQL của vòng 1.
- Ngoài ra `summary.md` có EX theo CSDL, theo số bảng trong SQL đáp án, phân loại lỗi và chi phí (lượt gọi, token, thời gian).

---

## 6. Kiểm chứng (không cần GPU, Ollama hay BIRD)

`python tests/test_compare.py`, LLM giả lập và CSDL mẫu (`tests/make_toy.py`):

- Giải mã view: tạo view thật trong bản sao SQLite, chạy các truy vấn mẫu (lọc, nhóm, nối view–view, `SELECT *`) trên view thật và trên bản đã
  mở rộng thành CTE (có và không cắt JOIN thừa); kết quả trùng nhau, so cả số lần lặp dòng.
- Đường ống đủ các phương pháp và biến thể; từ chối file câu hỏi có `question_id` lặp; tách bản ghi của cài đặt cũ khi `IMPL` đổi;
  xử lý lỗi Ollama 500.
- `tests/test_openai_client.py`: client API kiểu OpenAI (đổi `max_tokens` thành `max_completion_tokens`, bỏ `temperature` khi model không nhận).

Kiểm tra trên dữ liệu thật: `run_compare.py --views-only` (sinh view và kiểm số dòng, không gọi LLM) và `--selection-sweep --no-embed` (độ
phủ bảng đáp án của bước chọn view, không gọi LLM sinh SQL).

---

## 7. Giới hạn

- Số tuyệt đối không so được với Bảng 3 của paper (khác model). Điều so được là thứ tự và độ chênh giữa V-SQL, V-SQL+ và DAIL-SQL trên
  cùng một model.
- Bước chọn đối tượng của V-SQL (LLM chọn) và schema Bảng 6 mở rộng là phần tự thêm, vì paper không nói cách làm.
- Giai đoạn 2 (Hình 5) là chỗ phương pháp dễ mất điểm với model nhỏ: model hay bỏ JOIN cần thiết (notice 1 của Hình 5 yêu cầu "join as
  little as possible"). Cả V-SQL và V-SQL+ giữ nguyên bước này như paper.
