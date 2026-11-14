"""Tai du lieu de chay tren may local (giong Buoc 4 cua notebook Colab):
  - BIRD mini-dev (CSDL, dev_tables.json, mo ta cot) tu zip OSS (~800 MB) neu chua co
  - file cau hoi ban 2025-07-04 tu Hugging Face (ghim commit, kiem md5)
  - --dail: train.json + train_tables.json cua BIRD (HTTP Range, khong tai ca zip 8,9 GB) va chuan bi cache DAIL-SQL
Chay tu thu muc repo:  python scripts/tai_du_lieu.py [--dail]"""
import argparse
import collections
import hashlib
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
ZIP_URL = "https://bird-bench.oss-cn-beijing.aliyuncs.com/minidev.zip"
HF_URL = ("https://huggingface.co/datasets/birdsql/bird_mini_dev/resolve/f65faf4ae3b638c1fa6df1d3370c8d92c8366301/"
          "data/mini_dev_sqlite-00000-of-00001.json")
HF_MD5 = "595b6b014a528f4386d2e16f74d14b40"


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--dir", default=str(REPO / "minidev"), help="thu muc du lieu (mac dinh ./minidev)")
    a.add_argument("--dail", action="store_true", help="tai them tap train BIRD cho DAIL-SQL")
    args = a.parse_args()
    root = Path(args.dir)
    data = root / "MINIDEV"
    if not (data / "dev_databases").is_dir():
        root.mkdir(parents=True, exist_ok=True)
        z = root / "minidev.zip"
        if not z.exists():
            print("Tai", ZIP_URL, "(~800 MB)...", flush=True)
            urllib.request.urlretrieve(ZIP_URL, z)
        with zipfile.ZipFile(z) as f:
            f.extractall(root.parent, [n for n in f.namelist() if n.startswith("minidev/MINIDEV/")])
    q = data / "mini_dev_sqlite_2025-07-04.json"
    if not q.exists():
        print("Tai cau hoi ban 2025-07-04 tu Hugging Face...", flush=True)
        urllib.request.urlretrieve(HF_URL, q)
    md5 = hashlib.md5(q.read_bytes()).hexdigest()
    if md5 != HF_MD5:
        raise SystemExit(f"File cau hoi khong khop ban 2025-07-04 (md5 {md5}); xoa {q} roi chay lai")
    d = json.loads(q.read_text())
    print(f"Cau hoi 2025-07-04: {len(d)} cau, do kho {dict(collections.Counter(x['difficulty'] for x in d))}; "
          f"{len(list((data / 'dev_databases').iterdir()))} CSDL")
    chung = f"--data {q} --db-root {data / 'dev_databases'} --tables-json {data / 'dev_tables.json'}"
    if args.dail:
        from vsql.baselines import fetch_bird_train, prepare_dail
        tj, tt = fetch_bird_train(str(root / "bird_train"))
        cache = str(root / "bird_train")
        prepare_dail(tj, tt, cache)
        chung += f" --dail-train {tj} --dail-train-tables {tt} --dail-cache {cache}"
    print("\nTham so du lieu cho run_compare.py (copy vao lenh chay):\n" + chung)


if __name__ == "__main__":
    main()
