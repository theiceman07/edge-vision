"""Auto-label class-folder photos into a YOLO dataset using FastSAM.

Folders: bolt/ nut/ (screw/ counts as bolt) and empty/ (negatives, no labels).
Stage 1 (slow): FastSAM proposals -> cached in <out>/raw.json
Stage 2 (instant): refine (edge filter, duplicates, nut holes) -> YOLO labels
Usage: python autolabel.py <out_dir> --src <folder> [--src <folder2>] [--edge 0.04] [--preview N]
"""
import argparse, json, random, shutil
from pathlib import Path
import cv2
import numpy as np

CLASSES = ["bolt", "nut"]
NEGATIVE = {"empty"}            # no labels: teach the model what NOT to detect
ALIAS = {"screw": "bolt"}       # nuts & bolts only: screw photos count as bolts


def raw_boxes(model, path, img):
    h, w = img.shape[:2]
    r = model(str(path), imgsz=640, conf=0.35, iou=0.6, retina_masks=True, verbose=False)[0]
    if r.boxes is None:
        return []
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    bg = cv2.resize(cv2.medianBlur(cv2.resize(g, (w // 4, h // 4)), 31), (w, h))
    fg = cv2.absdiff(g, bg) > 18
    edges = cv2.Canny(g, 40, 120) > 0
    out = []
    for b in r.boxes.xyxy.cpu().numpy():
        x1, y1, x2, y2 = [int(v) for v in b]
        x1, y1, x2, y2 = max(x1, 0), max(y1, 0), min(x2, w), min(y2, h)
        bw, bh = x2 - x1, y2 - y1
        if bw < 6 or bh < 6 or bw * bh > 0.30 * w * h:
            continue
        out.append([x1, y1, bw, bh, float(fg[y1:y2, x1:x2].mean()), float(edges[y1:y2, x1:x2].mean())])
    return out


def inter(a, c):
    ix = max(0, min(a[0] + a[2], c[0] + c[2]) - max(a[0], c[0]))
    iy = max(0, min(a[1] + a[3], c[1] + c[3]) - max(a[1], c[1]))
    return ix * iy


def refine(raw, ci, w, h, edge_thr, gray=None, std_thr=11):
    boxes = []
    for x, y, bw, bh, fg, ed in raw:
        if gray is not None and gray[y:y + bh, x:x + bw].std() < std_thr:   # smooth patch = shadow
            continue
        if fg < 0.12 or ed < edge_thr:           # background patch / soft shadow
            continue
        if (x <= 1 or y <= 1 or x + bw >= w - 1 or y + bh >= h - 1) and bw * bh < 0.01 * w * h:
            continue                              # clipped scraps at the frame edge
        boxes.append([x, y, bw, bh, ed])
    # duplicates: heavy overlap -> keep the one with more edges (the real object, not its shadow)
    boxes.sort(key=lambda b: -b[4])
    keep = []
    for a in boxes:
        dup = False
        for c in keep:
            i = inter(a, c)
            aa, ca = a[2] * a[3], c[2] * c[3]
            if i / (aa + ca - i) > 0.55 or (i > 0.85 * min(aa, ca) and min(aa, ca) > 0.5 * max(aa, ca)):
                dup = True
                break
        if not dup:
            keep.append(a)
    # boxes swallowing 2+ others are merged piles
    res = []
    for a in keep:
        inner = sum(1 for c in keep if c is not a and inter(a, c) > 0.8 * c[2] * c[3] and c[2] * c[3] < 0.7 * a[2] * a[3])
        if inner < 2:
            res.append(a)
    if ci == 1:                                   # drop the hole inside each nut
        res = [a for a in res if not any(
            c is not a and inter(a, c) > 0.9 * a[2] * a[3] and a[2] * a[3] < 0.7 * c[2] * c[3] for c in res)]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--src", action="append", required=True)
    ap.add_argument("--preview", type=int, default=0)
    ap.add_argument("--val", type=float, default=0.2)
    ap.add_argument("--edge", type=float, default=0.012)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    cache_f = out / "raw.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    items = []
    for si, src in enumerate(a.src):
        for c in CLASSES + sorted(NEGATIVE) + sorted(ALIAS):
            k = ALIAS.get(c, c)
            ci = CLASSES.index(k) if k in CLASSES else -1
            items += [(p, ci, f"{si}_") for p in sorted((Path(src) / c).glob("*.jpg"))]
    random.seed(0)
    random.shuffle(items)
    model = None
    for p, ci, _ in items:                        # stage 1
        if ci >= 0 and str(p) not in cache:
            if model is None:
                from ultralytics import FastSAM
                model = FastSAM("FastSAM-s.pt")
            cache[str(p)] = raw_boxes(model, p, cv2.imread(str(p)))
            if len(cache) % 25 == 0:
                print("fastsam", len(cache), flush=True)
                cache_f.write_text(json.dumps(cache))
    cache_f.write_text(json.dumps(cache))
    for s in ("train", "valid"):
        shutil.rmtree(out / s, ignore_errors=True)
    nval, total = int(len(items) * a.val), 0
    for i, (p, ci, tag) in enumerate(items):      # stage 2
        split = "valid" if i < nval else "train"
        (out / split / "images").mkdir(parents=True, exist_ok=True)
        (out / split / "labels").mkdir(parents=True, exist_ok=True)
        img = cv2.imread(str(p))
        h, w = img.shape[:2]
        boxes = refine(cache[str(p)], ci, w, h, a.edge, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)) if ci >= 0 else []
        name = f"{tag}{p.parent.name}_{p.name}"
        shutil.copy(p, out / split / "images" / name)
        with open(out / split / "labels" / (Path(name).stem + ".txt"), "w") as f:
            for x, y, bw, bh, _ in boxes:
                f.write(f"{ci} {(x+bw/2)/w:.6f} {(y+bh/2)/h:.6f} {bw/w:.6f} {bh/h:.6f}\n")
        total += len(boxes)
        if i < a.preview:
            vis = img.copy()
            for x, y, bw, bh, _ in boxes:
                cv2.rectangle(vis, (x, y), (x + bw, y + bh), (0, 255, 0) if ci == 1 else (255, 120, 0), 2)
            cv2.imwrite(str(out / f"preview_{i}.jpg"), vis)
    (out / "data.yaml").write_text(
        f"path: {out.resolve()}\ntrain: train/images\nval: valid/images\nnames:\n" +
        "".join(f"  {i}: {c}\n" for i, c in enumerate(CLASSES)))
    print(f"{len(items)} images, {total} boxes")


if __name__ == "__main__":
    main()
