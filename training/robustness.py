"""Precision/recall of results/weights/best.pt on ds3/test under perturbations (conf 0.25, IoU 0.5, class-aware)."""
import glob, sys
import cv2, numpy as np
from ultralytics import YOLO
m = YOLO("results/weights/best.pt", task="detect")

def gt(path):
    out = []
    for l in open(path):
        p = l.split()
        if not p: continue
        v = list(map(float, p[1:]))
        if len(v) == 4: x, y, w, h = v; out.append((int(p[0]), [x-w/2, y-h/2, x+w/2, y+h/2]))
        else: out.append((int(p[0]), [min(v[0::2]), min(v[1::2]), max(v[0::2]), max(v[1::2])]))
    return out
def iou(a, b):
    x1, y1, x2, y2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]); i = max(0, x2-x1)*max(0, y2-y1)
    return i / ((a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i + 1e-9)

def bright(f): return lambda im, g: (np.clip(im.astype(np.float32) * f, 0, 255).astype(np.uint8), g)
def contrast(f): return lambda im, g: (np.clip((im.astype(np.float32) - 128) * f + 128, 0, 255).astype(np.uint8), g)
def blur(k): return lambda im, g: (cv2.GaussianBlur(im, (k, k), 0), g)
def noise(s): return lambda im, g: (np.clip(im.astype(np.float32) + np.random.RandomState(0).normal(0, s, im.shape), 0, 255).astype(np.uint8), g)
def jpeg(q): return lambda im, g: (cv2.imdecode(cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, q])[1], 1), g)
def gray(im, g): return cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR), g
def rot90(im, g):
    out = []
    for c, (x1, y1, x2, y2) in g: out.append((c, [y1, 1-x2, y2, 1-x1]))     # 90 deg counter-clockwise
    return cv2.rotate(im, cv2.ROTATE_90_COUNTERCLOCKWISE), out
def small(s):
    def f(im, g):
        H = im.shape[0]; n = int(H*s); canvas = np.full_like(im, 114); o = (H-n)//2
        canvas[o:o+n, o:o+n] = cv2.resize(im, (n, n))
        return canvas, [(c, [(o+b[0]*n)/H, (o+b[1]*n)/H, (o+b[2]*n)/H, (o+b[3]*n)/H]) for c, b in g]
    return f
tests = {"baseline": lambda im, g: (im, g), "dim x0.5": bright(0.5), "very dim x0.3": bright(0.3), "bright x1.5": bright(1.5),
         "low contrast x0.5": contrast(0.5), "blur k=7": blur(7), "blur k=15": blur(15), "noise sd=15": noise(15), "JPEG q=15": jpeg(15),
         "grayscale": gray, "rotate 90": rot90, "objects at 60% size": small(0.6), "objects at 40% size": small(0.4)}
files = sorted(glob.glob("ds3/test/images/*.jpg"))
print(f"{'test':22s} {'prec':>6s} {'recall':>7s}  (TP/FP/FN)")
for name, t in tests.items():
    tp = fp = fn = 0
    for f in files:
        im = cv2.imread(f); g = gt(f.replace("images", "labels").rsplit(".", 1)[0] + ".txt")
        im2, g2 = t(im, g)
        r = m.predict(im2, imgsz=320, conf=0.25, verbose=False, device="cpu")[0].boxes
        P = [(int(c), b) for c, b in zip(r.cls.numpy(), r.xyxyn.numpy())]
        used = set()
        for c, b in P:
            best, bj = 0, -1
            for j, (gc, gb) in enumerate(g2):
                if j in used or gc != c: continue
                v = iou(b, gb)
                if v > best: best, bj = v, j
            if best >= 0.5: used.add(bj); tp += 1
            else: fp += 1
        fn += len(g2) - len(used)
    print(f"{name:22s} {tp/max(tp+fp,1):6.3f} {tp/max(tp+fn,1):7.3f}  ({tp}/{fp}/{fn})")
