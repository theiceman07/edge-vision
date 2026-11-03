#!/usr/bin/env python3
"""Live camera -> ONNX detector -> decision (conf 0.40, confirm N=2) -> actuator command, on the Pi. Camera thread keeps only the latest
frame (same pattern as app/server.py). Per processed frame we log capture->actuator-command latency (frame grabbed -> decision applied).
The actuator here is a software stub (no LED hardware is driven), so 'actuator' latency = time until the command would be issued.
Usage: python live_pipeline_test.py --model app/enclosure_int8.onnx --seconds 120 --out DIR"""
import argparse, json, statistics, threading, time, os
import cv2, numpy as np, onnxruntime as ort
ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--seconds", type=int, default=120)
ap.add_argument("--imgsz", type=int, default=480); ap.add_argument("--conf", type=float, default=0.40); ap.add_argument("--confirm", type=int, default=2)
ap.add_argument("--out", required=True); a = ap.parse_args()
names = ["enclosure_good", "enclosure_defective"]
sess = ort.InferenceSession(a.model, providers=["CPUExecutionProvider"]); inp = sess.get_inputs()[0].name
cap = cv2.VideoCapture(0); S = a.imgsz
latest = {"f": None, "t": 0, "id": 0}; produced = [0]; stop = threading.Event(); lock = threading.Lock()
def grab():
    while not stop.is_set():
        ok, f = cap.read()
        if ok:
            with lock: latest.update(f=f, t=time.perf_counter(), id=latest["id"] + 1)
            produced[0] += 1
threading.Thread(target=grab, daemon=True).start()
def detect(img):
    h, w = img.shape[:2]; r = min(S / h, S / w); nh, nw = round(h * r), round(w * r)
    c = np.full((S, S, 3), 114, np.uint8); dy, dx = (S - nh) // 2, (S - nw) // 2; c[dy:dy + nh, dx:dx + nw] = cv2.resize(img, (nw, nh))
    x = np.ascontiguousarray(c[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255)
    o = sess.run(None, {inp: x})[0][0].T; sc = o[:, 4:]; cl = sc.argmax(1); p = sc.max(1); m = p >= a.conf
    o, cl, p = o[m], cl[m], p[m]
    b = np.stack([o[:, 0] - o[:, 2] / 2, o[:, 1] - o[:, 3] / 2, o[:, 2], o[:, 3]], 1)
    k = cv2.dnn.NMSBoxes(b.tolist(), p.tolist(), a.conf, 0.7); k = np.array(k).flatten().astype(int)
    return [(int(cl[i]), float(p[i])) for i in k]
state, pending, n_same = "none", "none", 0; lat, events, seen, t0 = [], [], 0, time.perf_counter()
while time.perf_counter() - t0 < a.seconds:
    with lock: f, tc, fid = latest["f"], latest["t"], latest["id"]
    if f is None or fid == seen: time.sleep(0.001); continue
    seen = fid; dets = detect(f)
    want = "none" if not dets else names[max(dets, key=lambda d: d[1])[0]]
    n_same = n_same + 1 if want == pending else 1; pending = want
    if want != state and n_same >= a.confirm: state = want; events.append((round(time.perf_counter() - t0, 2), state))
    lat.append((time.perf_counter() - tc) * 1000)   # actuator command issued here
stop.set(); el = time.perf_counter() - t0; lat.sort()
res = {"model": a.model, "seconds": round(el, 1), "camera_frames_produced": produced[0], "camera_fps": round(produced[0] / el, 2),
       "frames_processed": len(lat), "processed_fps": round(len(lat) / el, 2), "frames_dropped_by_latest_frame_policy": produced[0] - len(lat),
       "latency_ms_median": round(statistics.median(lat), 1), "latency_ms_mean": round(statistics.mean(lat), 1),
       "latency_ms_p95": round(lat[int(0.95 * len(lat)) - 1], 1), "latency_ms_max": round(lat[-1], 1), "state_changes": events}
os.makedirs(a.out, exist_ok=True); json.dump(res, open(os.path.join(a.out, "live_pipeline_%s.json" % time.strftime("%Y%m%d_%H%M%S")), "w"), indent=2)
print(json.dumps(res, indent=2))
