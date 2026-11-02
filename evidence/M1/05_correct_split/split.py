#!/usr/bin/env python3
"""Verify a YOLO dataset split: counts per split/class (target 70/20/10) and leakage across splits by image hash.
The split itself is made by tools/label_enclosure.py (per placement, seed 0). This script checks it and writes split_counts.md.
Usage: .venv/bin/python tools/split.py training/enclosure_ds [--out evidence/M1/05_correct_split/split_counts.md]
Leakage tests: (1) identical files (md5); (2) near-duplicates: 64-bit difference hash, Hamming distance <= --near (default 6)."""
import argparse, glob, hashlib, itertools, os
from collections import Counter
import cv2, numpy as np

def dhash(path):
    g = cv2.resize(cv2.imread(path, 0), (9, 8), interpolation=cv2.INTER_AREA)
    return int("".join("1" if v else "0" for v in (g[:, 1:] > g[:, :-1]).flatten()), 2)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("ds"); ap.add_argument("--out", default=None); ap.add_argument("--near", type=int, default=6)
    a = ap.parse_args()
    files = {sp: sorted(glob.glob(f"{a.ds}/{sp}/images/*.jpg")) for sp in ("train", "val", "test")}
    cls = lambda f: "empty" if os.path.basename(f).startswith("empty") else os.path.basename(f).rsplit("_b", 1)[0]
    tot = sum(map(len, files.values()))
    L = ["# Split counts and leakage check", "", f"Dataset: `{a.ds}`; split made per placement (one photo = one placement), seed 0.", "",
         "| Class | train | val | test | total |", "|---|---|---|---|---|"]
    for c in sorted({cls(f) for v in files.values() for f in v}):
        n = [sum(cls(f) == c for f in files[sp]) for sp in files]; L.append(f"| {c} | {n[0]} | {n[1]} | {n[2]} | {sum(n)} |")
    n = [len(files[sp]) for sp in files]
    L += [f"| **all** | {n[0]} | {n[1]} | {n[2]} | {tot} |", "", f"Shares: train {n[0]/tot:.0%}, val {n[1]/tot:.0%}, test {n[2]/tot:.0%} (target 70/20/10).", ""]
    md5 = {f: hashlib.md5(open(f, "rb").read()).hexdigest() for v in files.values() for f in v}
    dh = {f: dhash(f) for v in files.values() for f in v}
    exact = [(x, y) for sa, sb in itertools.combinations(files, 2) for x in files[sa] for y in files[sb] if md5[x] == md5[y]]
    near = [(x, y, bin(dh[x] ^ dh[y]).count("1")) for sa, sb in itertools.combinations(files, 2) for x in files[sa] for y in files[sb]
            if bin(dh[x] ^ dh[y]).count("1") <= a.near]
    parts = [t for t in near if cls(t[0]) != "empty" and cls(t[1]) != "empty"]
    L += ["## Leakage check across splits", "", f"- Identical files (md5) in different splits: **{len(exact)}**",
          f"- Near-duplicates (dHash Hamming <= {a.near}) between part photos in different splits: **{len(parts)}**",
          f"- Near-duplicates involving empty-mat photos (expected, same empty mat): {len(near) - len(parts)}", ""]
    if parts:
        L += ["| file A | file B | distance |", "|---|---|---|"] + [f"| {os.path.basename(x)} | {os.path.basename(y)} | {d} |" for x, y, d in parts[:30]]
    L += ["", "Note: the empty-mat photos look alike by design (same empty mat), so near-duplicate pairs among them are expected and harmless."]
    out = "\n".join(L); print(out)
    if a.out: open(a.out, "w").write(out + "\n")

if __name__ == "__main__":
    main()
