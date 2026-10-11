#!/bin/bash
# Xem tien do + uoc tinh thoi gian con lai. Chay: ./progress.sh [thu_muc_ket_qua]
cd "$(dirname "$0")"
OUT=${1:-results/q8}
python3 - "$OUT" <<'PY'
import sys, json, os, time, subprocess
out = sys.argv[1]
order = ["base","vsql","vsql_det","auto_llm","auto_det","hybrid","hybrid_ret"]
N = (len(json.load(open(json.load(open(f"{out}/config.json"))["qids"]))) if json.load(open(f"{out}/config.json")).get("qids") else json.load(open(f"{out}/config.json")).get("sample")) or 500 if os.path.exists(f"{out}/config.json") else 500
alive = subprocess.run(["pgrep","-f","run_experiment.py"],capture_output=True).returncode == 0
print(f"Tien trinh: {'DANG CHAY' if alive else 'DA DUNG'}\n")
# Giai doan A: goi LLM theo lo (prefetch). Vong 1 = SQL nhap/1 giai doan, vong 2 = tai tao (vsql, auto_llm)
pf = f"{out}/prefetch_progress.json"
if os.path.exists(pf):
    p = json.load(open(pf))
    rate = p["elapsed"] / max(p["done"], 1)                    # giay / prompt
    est2 = 0.75 * 2 * N * rate if p["round"] == 1 else 0       # vong 2 uoc ~0.75 x 500 x 2 cau hinh
    left = p["eta"] + est2
    bar = "#" * (p["done"] * 30 // max(p["total"], 1))
    print(f"A. Goi LLM - vong {p['round']}/2: {p['done']}/{p['total']} prompt  {bar:<30} ({rate:.1f} s/prompt)")
    if p["done"] < p["total"] or p["round"] == 1:
        print(f"   Con lai ~ {left/3600:.1f} gio  -> xong khoang {time.strftime('%H:%M %d/%m', time.localtime(time.time()+left))}")
        print(f"   (vong 2 chua biet chinh xac so prompt, uoc tinh ~{int(0.75*2*N)})" if p["round"] == 1 else "")
# Giai doan B: cham diem (khong goi LLM, vai phut)
done = {m: min(N, sum(1 for _ in open(f"{out}/predictions_{m}.jsonl"))) if os.path.exists(f"{out}/predictions_{m}.jsonl") else 0 for m in order}
print("B. Cham diem (chay SQL, nhanh, sau khi A xong):")
for m in order:
    print(f"   {m:11s} {done[m]:4d}/{N}  {'#'*(done[m]*30//N):<30}")
if os.path.exists(f"{out}/summary.md") and all(done[m] == N for m in order):
    print(f"\nXONG. Ket qua: {out}/summary.md")
elif not alive:
    print("\nChua xong ma tien trinh da dung -> chay lai lenh run_experiment.py (tu bo qua phan da xong)")
PY
