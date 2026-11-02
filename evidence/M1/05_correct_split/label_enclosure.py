#!/usr/bin/env python3
"""Auto-label the enclosure photos (white parts on a dark mat) and make a 70/20/10 split BY PLACEMENT.
Usage (from edge-vision/): .venv/bin/python tools/label_enclosure.py [--src app/mydata_enc] [--out training/enclosure_ds]
Method: white = high brightness + low saturation; morphology; one box per connected group of parts.
Class of every box = the class folder of the photo (enclosure_good / enclosure_defective). empty/ = no labels.
Frames with hands (skin pixels) are skipped: this method would box the hand. Touching parts become one group box.
Split: every photo is its own placement (block id in the file name); blocks are shuffled per class (seed 0) and split
70/20/10, so no two photos of the same placement end up in different splits. Everything is written to split.csv."""
import argparse, csv, glob, os, random, shutil
import cv2, numpy as np

CLASSES = ["enclosure_good", "enclosure_defective"]


def has_hand(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    skin = ((hsv[..., 0] < 22) & (hsv[..., 1] > 70) & (hsv[..., 2] > 50) & (hsv[..., 2] < 230))
    skin[:30, :] = False
    return skin.mean() > 0.012


def find_boxes(img):
    H, W = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    v = hsv[..., 2]
    thr = max(170, float(np.median(v[30:])) + 55)          # relative to this frame's mat brightness (glare/shadow safe)
    m = ((v > thr) & (hsv[..., 1] < 60)).astype(np.uint8) * 255
    m[:30, :] = 0                                   # beige table strip along the top edge
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, _, st, _ = cv2.connectedComponentsWithStats(m)
    out = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 1500 or a > 0.35 * W * H or max(w / h, h / w) > 6:
            continue
        if (x <= 2 or y <= 32 or x + w >= W - 2 or y + h >= H - 2) and min(w, h) < 60:
            continue                                  # thin sliver cut by the frame border
        if a / (w * h) < 0.30:                        # sparse blob = glare patch, not a solid part
            continue
        out.append((int(x), int(y), int(w), int(h)))
    return out


def dhash(img):
    g = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (9, 8), interpolation=cv2.INTER_AREA)
    return int("".join("1" if v else "0" for v in (g[:, 1:] > g[:, :-1]).flatten()), 2)


def groups(lst, near=6):
    """Union photos whose 64-bit dHash is within `near` bits: a group = one 'look', kept together in ONE split (no leakage)."""
    hs = [dhash(cv2.imread(f)) for f, _, _ in lst]
    par = list(range(len(lst)))
    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(len(lst)):
        for j in range(i):
            if bin(hs[i] ^ hs[j]).count("1") <= near:
                par[find(i)] = find(j)
    g = {}
    for i in range(len(lst)):
        g.setdefault(find(i), []).append(i)
    return list(g.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="app/mydata_enc")
    ap.add_argument("--out", default="training/enclosure_ds")
    a = ap.parse_args()
    random.seed(0)
    rows, items = [], {c: [] for c in CLASSES + ["empty"]}
    for c in items:
        for f in sorted(glob.glob(f"{a.src}/{c}/*.jpg")):
            img = cv2.imread(f)
            blk = int(os.path.basename(f).split("_b")[1].split("_")[0])
            if has_hand(img):
                rows.append([os.path.basename(f), c, blk, "skipped", "hand in frame"]); continue
            bx = [] if c == "empty" else find_boxes(img)
            if c != "empty" and not bx:
                rows.append([os.path.basename(f), c, blk, "skipped", "no part found"]); continue
            items[c].append((f, blk, bx))
    shutil.rmtree(a.out, ignore_errors=True)
    for c, lst in items.items():
        n = len(lst)
        if c == "empty":                                   # empty mat: all alike by design, random split
            random.shuffle(lst); grp = [[i] for i in range(n)]
        else:
            grp = groups(lst); random.shuffle(grp); grp.sort(key=lambda g: -len(g))
        sp_of, cnt, tgt = {}, {"train": 0, "val": 0, "test": 0}, {"train": 0.7, "val": 0.2, "test": 0.1}
        for g in grp:                                      # each group goes to the split furthest below its 70/20/10 share
            sp = max(tgt, key=lambda s_: tgt[s_] * n - cnt[s_])
            for i in g:
                sp_of[i] = sp
            cnt[sp] += len(g)
        for k, (f, blk, bx) in enumerate(lst):
            sp = sp_of[k]
            os.makedirs(f"{a.out}/{sp}/images", exist_ok=True); os.makedirs(f"{a.out}/{sp}/labels", exist_ok=True)
            base = os.path.splitext(os.path.basename(f))[0]
            shutil.copy(f, f"{a.out}/{sp}/images/{base}.jpg")
            H, W = cv2.imread(f).shape[:2]
            with open(f"{a.out}/{sp}/labels/{base}.txt", "w") as fh:
                for x, y, w, h in bx:
                    fh.write(f"{CLASSES.index(c)} {(x + w / 2) / W:.6f} {(y + h / 2) / H:.6f} {w / W:.6f} {h / H:.6f}\n")
            rows.append([os.path.basename(f), c, blk, sp, f"{len(bx)} boxes"])
    with open(f"{a.out}/split.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["file", "class", "block", "split", "note"]); w.writerows(rows)
    with open(f"{a.out}/data.yaml", "w") as fh:
        fh.write(f"path: {os.path.abspath(a.out)}\ntrain: train/images\nval: val/images\ntest: test/images\nnames:\n" +
                 "".join(f"  {i}: {c}\n" for i, c in enumerate(CLASSES)))
    from collections import Counter
    print(Counter((r[3], r[1]) for r in rows))


if __name__ == "__main__":
    main()
