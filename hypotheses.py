#!/usr/bin/env python3
"""Kiem dinh cac gia thuyet chinh P1-P6 (co dinh truoc khi xem ket qua), McNemar chinh xac + bootstrap CI + Holm.

  python hypotheses.py results/q08_500
"""
import json
import sys
from pathlib import Path

from vsql.report import _holm, boot_ci, mcnemar

PRIMARY = [("P1", "base_fix", "base"), ("P2", "vsql_fix", "vsql"), ("P3", "auto_plain_det", "auto_det"),
           ("P4", "base_fix_fb", "base_fix"), ("P5", "mrv", "base"), ("P6", "mrv", "vsql")]


def preds(d, m):
    p = Path(d) / f"predictions_{m}.jsonl"
    return {json.loads(l)["qid"]: json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}


def compare(d, pairs):
    """pairs: [(ma, a, b)] -> list dict (a so voi b); p duoc hieu chinh Holm tren ca nhom."""
    rows = []
    for key, a, b in pairs:
        A, B = preds(d, a), preds(d, b)
        qs = sorted(set(A) & set(B), key=str)
        diff = [int(A[q]["correct"]) - int(B[q]["correct"]) for q in qs]
        lo, hi = boot_ci(diff)
        lose, win = diff.count(-1), diff.count(1)
        rows.append(dict(key=key, a=a, b=b, n=len(qs), ex_a=100 * sum(A[q]["correct"] for q in qs) / len(qs),
                         ex_b=100 * sum(B[q]["correct"] for q in qs) / len(qs), delta=100 * sum(diff) / len(qs),
                         lo=100 * lo, hi=100 * hi, lose=lose, win=win, p=mcnemar(lose, win)))
    for r, h in zip(rows, _holm([r["p"] for r in rows])):
        r["holm"] = h
    return rows


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "results/q08_500"
    for r in compare(d, PRIMARY):
        print(f"{r['key']} {r['a']:15s} vs {r['b']:10s} n={r['n']} {r['ex_a']:5.1f} vs {r['ex_b']:5.1f} "
              f"d={r['delta']:+5.1f} [{r['lo']:+.1f},{r['hi']:+.1f}] thang {r['win']} thua {r['lose']} "
              f"p={r['p']:.5f} holm={r['holm']:.5f}")
