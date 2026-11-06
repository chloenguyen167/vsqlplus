# Hướng dẫn chạy so sánh TA-SQL · V-SQL · V-SQL+ trên Google Colab (GPU T4)

Tài liệu này hướng dẫn từng bước chạy notebook
[`notebooks/TASQL_VSQL_VSQLplus_Colab.ipynb`](../notebooks/TASQL_VSQL_VSQLplus_Colab.ipynb) với ba model
`qwen3.5:0.8b`, `qwen3:8b`, `qwen3.5:9b`. Toàn bộ thực nghiệm chạy trên Colab, không cần cài gì trên máy cá nhân.

Nội dung thực nghiệm và lý do thiết kế xem ở [`TAI_HIEN_DUNG_VA_VSQLPLUS.md`](TAI_HIEN_DUNG_VA_VSQLPLUS.md).

---

## 0. Tóm tắt

| Việc | Ở đâu | Thời gian |
|---|---|---|
| Đưa mã mới lên GitHub (làm 1 lần) | máy cá nhân | 2 phút |
| Mở notebook, chọn GPU T4 | Colab | 1 phút |
| Bước 1 → 8: chuẩn bị, chạy thử | Colab | 15–25 phút |
| Bước 9: chạy chính | Colab | 0.8b: ~1–2 giờ; 8b / 9b: ~6–10 giờ mỗi model |
| Bước 10 → 12: xem kết quả, tải về | Colab | 2 phút |

**Khuyến nghị:** mỗi phiên Colab chỉ chạy **một model**, theo thứ tự `qwen3.5:0.8b` (nhanh, để kiểm tra toàn bộ quy trình)
→ `qwen3:8b` → `qwen3.5:9b`. Kết quả lưu vào Google Drive. Nếu phiên bị ngắt thì chạy lại, phần đã xong không phải chạy lại.

---

## 1. Chuẩn bị (làm một lần)

### 1.1 Đưa mã mới lên GitHub

Notebook tải mã bằng `git clone https://github.com/chloenguyen167/vsqlplus.git` (nhánh `main`), nên mã mới phải có trên
GitHub trước khi chạy. Trên máy cá nhân, trong thư mục repo:

```bash
git add run_compare.py vsql/ tests/ notebooks/TASQL_VSQL_VSQLplus_Colab.ipynb docs/ README.md run_experiment.py
git commit -m "Them TA-SQL, V-SQL dung theo paper, V-SQL+ va notebook Colab"
git push origin main
```

Kiểm tra: mở https://github.com/chloenguyen167/vsqlplus/tree/main/notebooks và thấy file `TASQL_VSQL_VSQLplus_Colab.ipynb`.

> Nếu repo để chế độ **private**, Colab không clone được bằng lệnh trên. Hãy để public, hoặc sửa Bước 3 để clone bằng token.

### 1.2 Tài khoản

- Một tài khoản Google, còn trống khoảng **3 GB** trên Google Drive (gồm dữ liệu BIRD ~800 MB, cache LLM và kết quả).
- Colab miễn phí là đủ (GPU T4 16 GB). Colab Pro (GPU L4/A100) chạy nhanh hơn 2–4 lần, các bước vẫn y hệt.

---

## 2. Mở notebook và chọn GPU

1. Mở link (thay bằng link repo của bạn nếu khác):
   `https://colab.research.google.com/github/chloenguyen167/vsqlplus/blob/main/notebooks/TASQL_VSQL_VSQLplus_Colab.ipynb`
   (hoặc bấm nút **Open in Colab** trong `README.md`).
2. Menu **Runtime → Change runtime type → Hardware accelerator: T4 GPU → Save**.
3. (Nên làm) **File → Save a copy in Drive**, để sửa tham số mà không ảnh hưởng bản gốc.

Chạy từng ô bằng nút ▶ bên trái ô, hoặc `Shift + Enter`. **Chạy lần lượt từ trên xuống, không bỏ ô.**

---

## 3. Chạy từng bước

### Bước 1. Cấu hình

Ô này là một biểu mẫu. Các tham số:

| Tham số | Ý nghĩa | Gợi ý |
|---|---|---|
| `CHAY_qwen35_08b`, `CHAY_qwen3_8b`, `CHAY_qwen35_9b` | Model chạy trong phiên này. Nếu chọn nhiều, các model chạy lần lượt | Tick **một** model mỗi phiên |
| `SAMPLE` | `0` = đủ 500 câu như paper. Số khác = lấy mẫu phân tầng theo CSDL × độ khó | `0` khi chạy thật; `50` nếu chỉ muốn thử nhanh |
| `ABLATION` | Chạy thêm 5 biến thể đối chiếu của V-SQL+ (chỉ hướng 1, bỏ bầu chọn, bỏ liên kết giá trị, bỏ schema lai, giải mã tất định) | Bật nếu cần bảng đóng góp của từng thành phần; tốn thêm khoảng 40% thời gian |
| `EMBED_MODEL` | Mô hình embedding cho truy hồi lai của V-SQL+ | Giữ `nomic-embed-text`. Để trống thì V-SQL+ chỉ dùng BM25 |
| `WORKERS` | Số luồng gọi Ollama song song | Giữ `1` (dùng lại KV cache tốt nhất trên một GPU) |
| `LUU_DRIVE` | Lưu kết quả vào Google Drive | Luôn bật |

Ba phương pháp so sánh chạy với mọi model: `tasql` (TA-SQL, baseline của paper), `vsql` (V-SQL theo paper), `vsqlplus` (V-SQL+).

**Kết quả mong đợi:** `Model: ['qwen3.5:0.8b'] | cấu hình: main | số câu: 500`.

> Lưu ý: kết quả chạy đủ 500 câu và kết quả chạy mẫu (`SAMPLE` > 0) nằm ở **hai thư mục khác nhau** (tên thư mục mẫu có thêm
> `_mau<N>`), nên chạy thử không làm bẩn kết quả thật.

### Bước 2. Kiểm tra GPU, kết nối Google Drive

- In ra `GPU: Tesla T4, 15360 MiB`. Nếu in `KHÔNG CÓ GPU` thì quay lại mục 2 để chọn GPU, rồi chạy lại từ Bước 1.
- Colab hỏi quyền truy cập Drive: chọn tài khoản và bấm **Allow**.

### Bước 3. Tải mã nguồn và chạy kiểm thử (~1 phút)

Clone repo vào `/content/vsqlplus` (nếu đã có thì `git pull`), sau đó chạy kiểm thử với LLM giả lập.

**Kết quả mong đợi** (2 dòng):
```
TAT CA KIEM THU (so sanh) DAT. {'base': 8, 'tasql': 8, 'vsql': 7, 'vsqlplus': 8, ...}
TAT CA KIEM THU DAT. {...}
```
Nếu có `AssertionError` hoặc `No such file`, thường là mã trên GitHub chưa được cập nhật (xem mục 1.1).

### Bước 4. Tải BIRD mini-dev và mô tả cột của TA-SQL (~2–5 phút lần đầu)

- Tải `minidev.zip` (~800 MB) từ máy chủ BIRD, giải nén phần SQLite vào `/content/data/minidev/MINIDEV`. Lần đầu bản zip
  được chép vào Drive (`MyDrive/vsqlplus_ketqua/minidev.zip`), các lần sau lấy từ Drive nên nhanh hơn.
- Tải `column_meaning.json` từ repo chính thức của TA-SQL (mô tả cột mà TA-SQL dùng trong prompt).

**Kết quả mong đợi:**
```
500 dòng dữ liệu (tính đủ, kể cả question_id 137/138 xuất hiện hai lần như bộ đánh giá chính thức); 11 CSDL
column_meaning.json: 699 cột
```

### Bước 5. Sinh view và đo độ phủ bước chọn view (~2 phút, không gọi LLM)

- In một dòng `[schema] <CSDL> {...}` cho mỗi CSDL. Cần thấy `oracle_ok` = `oracle` và `auto_ok` = `auto`, nghĩa là mọi view
  đều giữ nguyên số dòng của bảng gốc.
- Bảng độ phủ của bước chọn view (BM25 + liên kết giá trị, chưa có embedding):
  ```
  k,full_coverage_pct,n_questions_with_selection
  1,82.3,266
  ...
  4,99.6,266
  5,100.0,266
  ```
  266 là số câu thuộc 5 CSDL lớn, nơi V-SQL+ phải chọn view (6 CSDL còn lại đủ nhỏ để đưa hết view vào prompt).

View sinh ra được lưu ở `/content/ketqua/_views/views/<CSDL>.oracle.sql` (view của V-SQL theo paper) và
`<CSDL>.auto.sql` (view tự động của V-SQL+), có thể mở bằng thanh **Files** bên trái để xem.

### Bước 6. Cài Ollama, tải model và khởi động (~5–10 phút)

Cài Ollama, chạy máy chủ ở nền, tải model đã chọn cùng `nomic-embed-text`, rồi gọi thử một câu.

**Kết quả mong đợi** (số cụ thể khác nhau tùy lần):
```
Ollama: {"version":"..."}
qwen3.5:0.8b: 0.4s, ~150 token/s -> SELECT COUNT(*) FROM t;
Embedding nomic-embed-text chiều: 768
```
Dung lượng tải về: `qwen3.5:0.8b` ~1 GB, `qwen3:8b` ~5 GB, `qwen3.5:9b` ~6–7 GB.

### Bước 7. Đồng bộ Google Drive

- Nếu Drive đã có kết quả của model này từ phiên trước, ô này chép về `/content/ketqua/...` và in `Khôi phục ...`.
- Bật luồng nền tự sao lưu lên Drive mỗi 5 phút. File cache LLM (`llm_cache.sqlite`) được chép bằng cơ chế backup của SQLite,
  nên không bị hỏng khi đang ghi.

Thư mục kết quả trên Drive:

| Model | Thư mục |
|---|---|
| `qwen3.5:0.8b` | `MyDrive/vsqlplus_ketqua/cmp_qwen35_08b/` |
| `qwen3:8b` | `MyDrive/vsqlplus_ketqua/cmp_qwen3_8b/` |
| `qwen3.5:9b` | `MyDrive/vsqlplus_ketqua/cmp_qwen35_9b/` |

### Bước 8. Chạy thử 3 câu × 3 phương pháp (~2–5 phút)

Kiểm tra toàn bộ đường ống với model thật trước khi chạy lâu. **Kết quả mong đợi:** một bảng EX có 3 dòng `tasql`, `vsql`,
`vsqlplus`, mỗi dòng `n` = 3. EX của 3 câu không có ý nghĩa thống kê; chỉ cần **không có** `Error`/`Traceback`.

### Bước 9. Chạy chính

Mỗi model chạy 3 phương pháp trên 500 câu (thêm 5 biến thể của V-SQL+ nếu bật `ABLATION`). Chương trình gom các prompt còn thiếu theo từng
vòng rồi gọi LLM:

| Vòng | Nội dung |
|---|---|
| 1 | TA-SQL bước TASL (dummy SQL); V-SQL giai đoạn 1; V-SQL+ (CSDL nhỏ: dummy SQL; CSDL lớn: 4 mẫu bầu chọn) |
| 2 | TA-SQL bước sinh SR; V-SQL giai đoạn 2; V-SQL+ (CSDL lớn: dummy SQL trên view đã chọn; CSDL nhỏ: giai đoạn 2) |
| 3–5 | TA-SQL bước SR → SQL; V-SQL+ schema lai (nếu có) và giai đoạn 2 |

Dòng tiến độ có dạng:
```
[prefetch vong 1] 1850 prompt can goi LLM, 1 luong
[prefetch vong 1] 450/1850  con lai ~95 phut
```
"con lai" là thời gian còn lại **của vòng hiện tại**. Các vòng sau ngắn hơn vòng 1. Khi hết các vòng, chương trình chấm điểm
(nhanh, vì mọi câu trả lời đã nằm trong cache) và in bảng tổng hợp.

**Ước tính thời gian trên T4** (khoảng 4.500 lượt gọi LLM mỗi model):

| Model | 3 phương pháp | Có `ABLATION` |
|---|---|---|
| `qwen3.5:0.8b` | ~1–2 giờ | ~1,5–3 giờ |
| `qwen3:8b` | ~6–10 giờ | ~8–14 giờ |
| `qwen3.5:9b` | ~6–10 giờ | ~8–14 giờ |

Đây là ước tính, chưa đo thực tế. Thời gian thật phụ thuộc tốc độ GPU được cấp và độ dài câu trả lời của model. Hãy dựa vào
dòng `con lai ~N phut`.

**Giữ phiên Colab sống:**
- Để tab notebook mở. Colab miễn phí ngắt khi trình duyệt không hoạt động lâu (khoảng 90 phút) và giới hạn mỗi phiên
  tối đa khoảng 12 giờ.
- Không cần ngồi canh: dù bị ngắt, công sức không mất (xem mục 4).

### Bước 10. Bảng kết quả theo từng model

Với mỗi model, ô này in hai bảng:

1. **EX theo độ khó** (SIM./MOD./CHALL./TOTAL), kèm khoảng tin cậy 95%, tỉ lệ ảo giác schema (lỗi `no such column/table`),
   số lượt gọi LLM và số token vào mỗi câu.
2. **So sánh ghép cặp**: V-SQL+ − TA-SQL, V-SQL+ − V-SQL, V-SQL − TA-SQL, ... với ΔEX, khoảng tin cậy, số câu chỉ một bên đúng,
   p McNemar và p Holm.

Cuối ô là Bảng 3 của paper để đối chiếu.

**Cách đọc:**
- Kiểm tra cột `n` = **500** ở mọi dòng. Nếu nhỏ hơn thì lần chạy chưa xong (chạy lại Bước 9).
- Một chênh lệch chỉ được coi là có ý nghĩa thống kê khi **p Holm < 0,05**. Với 500 câu, chênh lệch khoảng 3 điểm % trở xuống
  thường không có ý nghĩa.
- Không so số tuyệt đối với paper (paper dùng GPT-3.5/GPT-4). Điều cần so là **thứ tự và chênh lệch** giữa TA-SQL, V-SQL và
  V-SQL+ trên cùng một model.
- Nếu bật `ABLATION`: `vsqlplus_all` − `vsql` là đóng góp của hướng 1 (sinh view tự động); `vsqlplus` − `vsqlplus_all` là
  đóng góp của hướng 2 (chọn view). Bảng chi tiết nằm ở mục 5 của `summary.md`.

### Bước 11. Tổng hợp giữa các model

Bảng EX của TA-SQL, V-SQL, V-SQL+ theo từng model đã có kết quả, kèm biểu đồ cột có thanh sai số (lưu ở
`/content/ketqua/bieu_do_ex.png`). Ô này đọc mọi model **đã chọn ở Bước 1**. Muốn gộp cả 3 model vào một bảng thì xem mục 5.

### Bước 12. Tải kết quả về máy

Nén `/content/ketqua` thành `ketqua_tasql_vsql_vsqlplus.zip` và tải về. Bản trên Drive vẫn được giữ.

---

## 4. Khi Colab bị ngắt giữa chừng

1. Mở lại notebook, chọn lại GPU T4 nếu cần.
2. Chạy lại **Bước 1 → 7**, giữ nguyên cấu hình như lần trước. Bước 7 sẽ in `Khôi phục ... từ Drive`.
3. Chạy lại **Bước 9** (có thể bỏ qua Bước 8).

Chương trình bỏ qua các câu đã chấm (`predictions_*.jsonl`) và lấy lại mọi câu trả lời LLM đã có trong `llm_cache.sqlite`. Phần
mất đi tối đa là khoảng 5 phút cuối trước khi ngắt (chu kỳ sao lưu).

> Đừng đổi các tham số ảnh hưởng đến prompt (`SAMPLE`, model, `EMBED_MODEL`) giữa các lần chạy tiếp của cùng một thư mục kết
> quả. Nếu đổi, cache cũ không dùng lại được và kết quả trộn lẫn hai cấu hình.

---

## 5. Gộp kết quả 3 model (sau khi đã chạy xong cả 3, mỗi model một phiên)

Chạy Bước 1 với **cả 3 ô model được tick**, chạy Bước 2 và Bước 3, **bỏ qua Bước 4 → 9**, chạy Bước 7 (để khôi phục kết quả
từ Drive), rồi chạy Bước 10 và 11. Không cần GPU cho phần này. Bước 10–11 đọc kết quả có sẵn và in bảng chung cho cả 3 model.

---

## 6. Các file kết quả

Trong mỗi thư mục `cmp_<model>/`:

| File | Nội dung |
|---|---|
| `summary.md` | Báo cáo đầy đủ: EX (tổng và theo độ khó, CI 95%), so sánh ghép cặp với `tasql` và `vsql`, phân loại lỗi, chi phí, đóng góp từng thành phần, thống kê view |
| `summary.csv` | Các số trên dạng bảng, mỗi dòng một cấu hình (dùng để vẽ biểu đồ, đưa vào báo cáo) |
| `predictions_<cấu hình>.jsonl` | Mỗi dòng một câu hỏi (500 dòng) |
| `views/<CSDL>.oracle.sql`, `views/<CSDL>.auto.sql` | View của V-SQL (theo paper) và của V-SQL+ |
| `views_stats.json` | Số bảng, khóa ngoại, khóa ngoại suy thêm, số view, số view giữ nguyên số dòng |
| `config.json` | Toàn bộ tham số của lần chạy |
| `llm_cache.sqlite` | Cache mọi câu trả lời của LLM (để chạy tiếp, tính lại không tốn GPU) |

Các trường chính trong `predictions_<cấu hình>.jsonl`:

| Trường | Ý nghĩa |
|---|---|
| `uid` | Vị trí câu trong `mini_dev_sqlite.json` (0–499); `qid` là `question_id` gốc |
| `final_sql`, `correct`, `outcome`, `error` | SQL cuối, đúng/sai, loại kết quả (`correct`, `schema_column`, `syntax`, `wrong_result`, ...), thông báo lỗi |
| `dummy_sql`, `views_used` | Dummy SQL của giai đoạn 1 và các view nó dùng (V-SQL, V-SQL+); TA-SQL lưu dummy SQL của TASL và `sr` |
| `calls`, `prompt_tokens`, `completion_tokens`, `llm_seconds` | Chi phí cho câu đó |
| `all_in_prompt`, `candidates`, `vote`, `objects` | (V-SQL+) có đưa hết view không; 5 ứng viên; các tập view của từng mẫu và tập được chọn; view/bảng cuối cùng trong prompt |
| `value_links`, `fallback` | (V-SQL+) giá trị khớp trong DB; các lần quay về bảng gốc (lỗi, bảng được thêm) |
| `coverage` | Tỉ lệ bảng của SQL đáp án có mặt trong schema đưa cho LLM |

---

## 7. Gặp lỗi?

| Hiện tượng | Cách xử lý |
|---|---|
| Bước 2 in `KHÔNG CÓ GPU` | Runtime → Change runtime type → T4 GPU; chạy lại từ Bước 1 |
| `You cannot currently connect to a GPU due to usage limits` | Hết hạn mức GPU miễn phí trong ngày; chờ vài giờ, đổi tài khoản Google, hoặc dùng Colab Pro |
| Bước 3 báo `fatal: could not read Username` / `repository not found` | Repo private hoặc sai tên; xem mục 1.1 |
| Bước 3 có `AssertionError` | Mã trên GitHub chưa phải bản mới; push lại rồi chạy lại Bước 3 |
| Bước 4 tải `minidev.zip` lỗi hoặc rất chậm | Chạy lại ô; hoặc tải `minidev.zip` về máy, tải lên Drive vào `MyDrive/vsqlplus_ketqua/minidev.zip`, rồi chạy lại Bước 4 |
| Bước 6: `pull model manifest: file does not exist` | Tên model sai hoặc Ollama quá cũ; chạy lại Bước 6 (cài lại Ollama bản mới nhất) |
| Bước 6 / 9: `CUDA out of memory`, Ollama rất chậm | Mỗi phiên chỉ chạy một model, giữ `WORKERS = 1`; Runtime → Restart session rồi chạy lại từ Bước 1 |
| `[canh bao] khong goi duoc embedding ...` | V-SQL+ tự chuyển sang chỉ BM25 (kết quả vẫn hợp lệ nhưng khác cấu hình chuẩn). Chạy `!ollama pull nomic-embed-text`, rồi chạy lại Bước 9 với **thư mục kết quả mới**, hoặc xóa `predictions_vsqlplus*.jsonl` trước khi chạy lại |
| `[CANH BAO] prompt cham nguong num_ctx` | Prompt bị cắt. Thêm `--num-ctx 24576` vào lệnh ở Bước 9 |
| `[Ollama 500] ... -> thu lai` rồi `[LOI LLM] Ollama 500 ... -> ghi nhan cau tra loi rong` | Một prompt làm Ollama lỗi lặp lại. Chương trình thử lại 3 lần, sau đó tính câu đó là sai cho phương pháp tương ứng và chạy tiếp. Cuối lần chạy in số câu bị ảnh hưởng của mỗi phương pháp. Xem nguyên nhân: `!grep -iE "error|panic|fault" /content/ollama.log \| tail -20`. Muốn thử lại các prompt đó: thêm `--retry-llm-errors` vào lệnh ở Bước 9 |
| `ConnectionRefusedError` / `URLError` ở Bước 9 | Máy chủ Ollama đã dừng (thường sau khi Restart session); chạy lại Bước 6 rồi Bước 9 |
| Bước 10 in `Chưa có kết quả cho ...` | Chưa chạy Bước 9 cho model đó, hoặc chưa khôi phục từ Drive (chạy Bước 7) |
| `n` < 500 trong bảng kết quả | Lần chạy chưa xong; chạy lại Bước 9 |

---

## 8. Chạy bằng dòng lệnh (tùy chọn)

Mọi bước của notebook đều gọi `run_compare.py`. Trong một ô Colab, sau Bước 1 → 7:

```bash
!python run_compare.py {CHUNG} --model qwen3:8b --embed-model nomic-embed-text --out /content/ketqua/cmp_qwen3_8b
!python run_compare.py {CHUNG} --model qwen3:8b --methods vsqlplus_all,vsqlplus_det --out /content/ketqua/cmp_qwen3_8b
!python run_compare.py --help        # toàn bộ tham số
```

Các tham số của V-SQL+ (giữ mặc định để khớp tài liệu): `--k-cand 5` (số ứng viên đưa vào bầu chọn), `--n-samples 4`
(1 tham lam + 3 mẫu), `--sample-temp 0.7`, `--topk 4`, `--all-max-objects 4`, `--all-max-tokens 3500`, `--max-fallback 2`.
Tham số của V-SQL: `--vsql-evidence query|none` (nối evidence vào `{query}` của Hình 4/5 hoặc bỏ hẳn evidence).
