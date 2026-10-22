#!/usr/bin/env python3
"""Score detector output against hand-checked ground truth.
Input CSV columns: image,truth,predicted  (class names, 'none' if nothing). Prints accuracy + per-class precision/recall.
Ground truth must be labelled by you from the real images."""
import csv, sys
from collections import Counter

rows = list(csv.DictReader(open(sys.argv[1])))
tp, fp, fn = Counter(), Counter(), Counter()
for r in rows:
    t, p = r["truth"], r["predicted"]
    if t == p:
        tp[t] += 1
    else:
        fp[p] += 1
        fn[t] += 1
print(f"images: {len(rows)}  accuracy: {sum(tp.values()) / len(rows):.3f}")
for c in sorted(set(tp) | set(fp) | set(fn)):
    pr = tp[c] / (tp[c] + fp[c]) if tp[c] + fp[c] else 0
    rc = tp[c] / (tp[c] + fn[c]) if tp[c] + fn[c] else 0
    print(f"{c:12s} precision {pr:.3f} recall {rc:.3f} (tp {tp[c]} fp {fp[c]} fn {fn[c]})")
