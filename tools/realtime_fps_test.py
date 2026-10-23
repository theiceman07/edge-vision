#!/usr/bin/env python3
"""Paced real-time test: a producer 'camera' emits frames at a locked FPS, a detector thread always takes the latest frame
(same structure as app/server.py). Reports frames produced/processed/dropped, latency, and accuracy vs ground truth.
Usage: python realtime_fps_test.py --model best.onnx --images ds3/test/images --labels ds3/test/labels --fps 15 --seconds 60 --conf 0.4
All numbers come from this run on whatever machine it runs on; run it on the Pi for Pi results."""
import argparse, glob, json, statistics, threading, time
import cv2, numpy as np
from ultralytics import YOLO


def gt(path):
    out = []
    for l in open(path):
        p = l.split()
        if not p:
            continue
        v = list(map(float, p[1:]))
        if len(v) == 4:
            x, y, w, h = v; out.append((int(p[0]), [x - w/2, y - h/2, x + w/2, y + h/2]))
        else:
            out.append((int(p[0]), [min(v[0::2]), min(v[1::2]), max(v[0::2]), max(v[1::2])]))
    return out


def iou(a, b):
    x1, y1, x2, y2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]); i = max(0, x2-x1) * max(0, y2-y1)
    return i / ((a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i + 1e-9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--images", required=True); ap.add_argument("--labels", required=True)
    ap.add_argument("--fps", type=float, default=15); ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--conf", type=float, default=0.4); ap.add_argument("--imgsz", type=int, default=320)
    a = ap.parse_args()
    files = sorted(glob.glob(a.images + "/*.jpg")); frames = [cv2.imread(f) for f in files]
    truth = [gt(f.replace(a.images, a.labels).rsplit(".", 1)[0] + ".txt") for f in files]
    model = YOLO(a.model, task="detect"); model.predict(frames[0], imgsz=a.imgsz, verbose=False)          # warm-up
    for _ in range(20): model.predict(frames[0], imgsz=a.imgsz, verbose=False)
    latest = {"i": None, "seq": -1, "t": 0.0}; lock = threading.Lock(); stop = threading.Event(); produced = [0]

    def camera():
        period, nxt, k = 1.0 / a.fps, time.perf_counter(), 0
        while not stop.is_set():
            with lock:
                latest.update(i=k % len(frames), seq=produced[0], t=time.perf_counter())
            produced[0] += 1; k += 1; nxt += period
            time.sleep(max(0.0, nxt - time.perf_counter()))

    threading.Thread(target=camera, daemon=True).start()
    lat, e2e, done, tp, fp, fn, seen = [], [], 0, 0, 0, 0, -1
    t_end = time.perf_counter() + a.seconds
    while time.perf_counter() < t_end:
        with lock:
            i, seq, t_cap = latest["i"], latest["seq"], latest["t"]
        if i is None or seq == seen:
            time.sleep(0.002); continue
        seen = seq; t0 = time.perf_counter()
        r = model.predict(frames[i], imgsz=a.imgsz, conf=a.conf, verbose=False)[0].boxes
        t1 = time.perf_counter(); lat.append((t1 - t0) * 1000); e2e.append((t1 - t_cap) * 1000); done += 1
        used = set(); g = truth[i]
        for c, b in zip(r.cls.numpy(), r.xyxyn.numpy()):
            best, bj = 0, -1
            for j, (gc, gb) in enumerate(g):
                if j in used or gc != int(c): continue
                v = iou(b, gb)
                if v > best: best, bj = v, j
            if best >= 0.5: used.add(bj); tp += 1
            else: fp += 1
        fn += len(g) - len(used)
    stop.set(); lat.sort(); e2e.sort(); n = produced[0]; budget = 1000 / a.fps
    res = {"target_fps": a.fps, "seconds": a.seconds, "conf": a.conf, "frames_produced": n, "frames_processed": done,
           "frames_skipped": n - done, "effective_detection_fps": round(done / a.seconds, 2),
           "latency_ms": {"median": round(statistics.median(lat), 1), "p95": round(lat[int(0.95*len(lat))-1], 1), "max": round(lat[-1], 1)},
           "capture_to_result_ms": {"median": round(statistics.median(e2e), 1), "p95": round(e2e[int(0.95*len(e2e))-1], 1), "max": round(e2e[-1], 1)},
           "frame_budget_ms": round(budget, 1), "frames_over_budget": sum(v > budget for v in lat),
           "precision": round(tp / max(tp + fp, 1), 3), "recall": round(tp / max(tp + fn, 1), 3), "tp_fp_fn": [tp, fp, fn]}
    print(json.dumps(res, indent=2))


main()
