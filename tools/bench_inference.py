#!/usr/bin/env python3
"""Measure ONNX inference latency/FPS on the device it runs on. Writes results/bench_<host>_<time>.json.
Usage: python bench_inference.py --model best.onnx [--images DIR | --camera 0] [--n 300] [--imgsz 320]
Every number comes from this run; nothing is estimated."""
import argparse, json, platform, socket, statistics, time
from pathlib import Path
import cv2
import numpy as np
import onnxruntime as ort


def frames(a):
    if a.images:
        paths = sorted(p for p in Path(a.images).iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
        if not paths:
            raise SystemExit("no images found")
        for i in range(a.n):
            yield cv2.imread(str(paths[i % len(paths)]))
    else:
        cap = cv2.VideoCapture(a.camera)
        if not cap.isOpened():
            raise SystemExit("camera not available")
        for _ in range(a.n):
            ok, f = cap.read()
            if ok:
                yield f
        cap.release()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--images")
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--imgsz", type=int, default=320)
    ap.add_argument("--warmup", type=int, default=20)
    a = ap.parse_args()
    sess = ort.InferenceSession(a.model, providers=["CPUExecutionProvider"])
    inp = sess.get_inputs()[0].name
    lat = []
    for i, f in enumerate(frames(a)):
        x = cv2.resize(f, (a.imgsz, a.imgsz))[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255
        t = time.perf_counter()
        sess.run(None, {inp: np.ascontiguousarray(x)})
        if i >= a.warmup:
            lat.append((time.perf_counter() - t) * 1000)
    if not lat:
        raise SystemExit("no measured frames")
    lat.sort()
    res = {"host": socket.gethostname(), "machine": platform.machine(), "model": a.model, "imgsz": a.imgsz,
           "frames_measured": len(lat), "mean_ms": round(statistics.mean(lat), 2),
           "median_ms": round(statistics.median(lat), 2), "p95_ms": round(lat[int(0.95 * len(lat)) - 1], 2),
           "fps_from_mean": round(1000 / statistics.mean(lat), 2), "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
    Path("results").mkdir(exist_ok=True)
    out = Path("results") / f"bench_{res['host']}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2), "\nsaved", out)


main()
