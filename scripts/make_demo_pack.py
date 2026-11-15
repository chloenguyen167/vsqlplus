"""Dựng gói dữ liệu cho notebook demo trên Colab: minidev/vsql_demo_pack.zip (~266 MB).

Gồm: 6 CSDL của 10 câu demo, file câu hỏi 2025-07-04, dev_tables.json, tập train BIRD + bản đã xử lý sẵn cho DAIL-SQL
(che tên schema + embedding), cache câu trả lời gpt-4o-mini của 10 câu × 4 phương pháp (lấy từ lần chạy 500 câu, không gọi API).

Chạy trên máy (cần minidev/, minidev/bird_train/ đã có cache DAIL-SQL, results_new/cmp_gpt-4o-mini_d2025/llm_cache.sqlite):
    .venv/bin/python scripts/make_demo_pack.py
Rồi đưa lên GitHub Release (notebook tải từ đây):
    gh release create demo-data-v1 minidev/vsql_demo_pack.zip --title "Dữ liệu demo" --notes "Gói dữ liệu cho notebooks/Demo_VSQL_VSQLplus.ipynb"
"""
import json, shutil, sqlite3, sys, tempfile, types
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NB = REPO / "notebooks/Demo_VSQL_VSQLplus.ipynb"
CACHE_500 = REPO / "results_new/cmp_gpt-4o-mini_d2025/llm_cache.sqlite"
OUT_ZIP = REPO / "minidev/vsql_demo_pack.zip"

sys.path.insert(0, str(REPO))
try:
    import IPython.display  # noqa: F401
except ImportError:                     # .venv chưa cài jupyter: ô C chỉ cần các hàm hiển thị, thay bằng hàm rỗng
    ip = types.ModuleType("IPython"); ip.display = types.ModuleType("IPython.display")
    ip.display.HTML = ip.display.Markdown = str
    ip.display.display = lambda *a, **k: None
    sys.modules.update({"IPython": ip, "IPython.display": ip.display})

import vsql.llm as L                    # chặn gọi API thật: mọi câu trả lời phải có sẵn trong cache 500 câu
L.OpenAICompatLLM._post = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("thiếu câu trả lời trong cache 500 câu"))

# Chạy ô A, B, C của notebook (gpt-4o-mini, cache 500 câu), ghi lại khoá cache của mọi lần gọi LLM
g = {}
cells = ["".join(c["source"]) for c in json.loads(NB.read_text(encoding="utf-8"))["cells"] if c["cell_type"] == "code"]
for title in ("#@title A.", "#@title B.", "#@title C."):
    src = next(s for s in cells if s.startswith(title))
    if title == "#@title C.":           # bọc GhiNhatKy trước vòng chạy sẵn
        src = src.replace("t2 = time.time()", "_wrap()\nt2 = time.time()")
        keys = set()

        def _wrap():
            orig = g["GhiNhatKy"].chat

            def chat(self, prompt, meta=None, **opts):
                keys.add(self.llm._key(prompt, opts))
                return orig(self, prompt, meta, **opts)
            g["GhiNhatKy"].chat = chat
        g["_wrap"] = _wrap
    exec(compile(src, title, "exec"), g)
assert g["MODEL"] == "gpt-4o-mini" and g["BACKEND"] == "openai"

with tempfile.TemporaryDirectory() as tmp:
    pack = Path(tmp) / "vsql_demo_pack"
    data, train = REPO / "minidev/MINIDEV", REPO / "minidev/bird_train"
    for db in sorted(g["CTX"]):
        shutil.copytree(data / "dev_databases" / db, pack / "MINIDEV/dev_databases" / db,
                        ignore=shutil.ignore_patterns(".DS_Store"))
    for f in ("dev_tables.json", "mini_dev_sqlite_2025-07-04.json"):
        shutil.copy(data / f, pack / "MINIDEV" / f)
    (pack / "bird_train").mkdir()
    for f in ["train.json", "train_tables.json", *[p.name for p in train.glob("dail_train_*")]]:
        shutil.copy(train / f, pack / "bird_train" / f)
    with sqlite3.connect(CACHE_500) as src, sqlite3.connect(pack / "llm_cache_gpt-4o-mini_demo.sqlite") as dst:
        dst.execute("CREATE TABLE cache (k TEXT PRIMARY KEY, v TEXT)")
        rows = [src.execute("SELECT k, v FROM cache WHERE k=?", (k,)).fetchone() for k in sorted(keys)]
        assert all(rows), "thiếu khoá trong cache 500 câu"
        dst.executemany("INSERT INTO cache VALUES (?, ?)", rows)
    OUT_ZIP.unlink(missing_ok=True)
    shutil.make_archive(str(OUT_ZIP.with_suffix("")), "zip", tmp, "vsql_demo_pack")
print(f"Đã ghi {OUT_ZIP} ({OUT_ZIP.stat().st_size / 1e6:.0f} MB): {len(g['CTX'])} CSDL, {len(keys)} câu trả lời trong cache")
