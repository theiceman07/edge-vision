"""Local window test: camera -> YOLO -> on-screen overlay. Press q / ESC to quit, s to save a snapshot.
  env/bin/python local_cv.py [--model best.onnx] [--conf 0.5]
"""
import argparse, glob, os, threading, time
import cv2
import numpy as np
from ultralytics import YOLO

COLORS = {"bolt": (255, 120, 40), "nut": (0, 180, 255), "screw": (80, 230, 90)}  # BGR

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="best.onnx")
ap.add_argument("--conf", type=float, default=0.5)
ap.add_argument("--imgsz", type=int, default=320)
ap.add_argument("--fps", type=int, default=15, help="display frame rate cap")
a = ap.parse_args()

usb = sorted(glob.glob("/dev/v4l/by-id/usb-*-video-index0"))
cap = cv2.VideoCapture(usb[0] if usb else 0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
if os.path.exists("focus.txt"):          # fixed manual focus (autofocus hunts on a plain table)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    cap.set(cv2.CAP_PROP_FOCUS, int(open("focus.txt").read()))
if not cap.isOpened():
    raise SystemExit("Camera not found - check the USB cable/port")
model = YOLO(a.model, task="detect")
names = {k: ("bolt" if v == "screw" else v) for k, v in model.names.items()}  # nuts & bolts only: screw -> bolt

# camera thread: always holds the newest frame
shared = {"frame": None, "id": 0, "dets": [], "counts": {n: 0 for n in sorted(set(names.values()))}, "lat": 0.0, "dfps": 0.0, "stop": False}


def grab():
    while not shared["stop"]:
        ok, f = cap.read()
        if ok:
            shared["frame"], shared["id"] = f, shared["id"] + 1
        else:
            time.sleep(0.05)


def detect():
    seen, dfps = 0, 0.0
    while not shared["stop"]:
        f, i = shared["frame"], shared["id"]
        if f is None or i == seen:
            time.sleep(0.005)
            continue
        seen = i
        t0 = time.time()
        r = model.predict(f, imgsz=a.imgsz, conf=a.conf, iou=0.45, agnostic_nms=True, verbose=False)[0]
        counts = {n: 0 for n in sorted(set(names.values()))}
        dets = []
        for b in r.boxes:
            n = names[int(b.cls[0])]
            counts[n] += 1
            dets.append((*map(int, b.xyxy[0]), n, float(b.conf[0])))
        dt = time.time() - t0
        dfps = 0.8 * dfps + 0.2 / dt if dfps else 1 / dt
        shared.update(dets=dets, counts=counts, lat=dt * 1000, dfps=dfps)


threading.Thread(target=grab, daemon=True).start()
threading.Thread(target=detect, daemon=True).start()
print(f"running - display capped at {a.fps} FPS, detection runs as fast as the CPU allows. q/ESC quits, s snapshots")
period, vfps, tprev = 1 / a.fps, 0.0, time.time()
while True:
    t0 = time.time()
    frame = shared["frame"]
    if frame is None:
        time.sleep(0.02)
        continue
    frame = frame.copy()
    for x1, y1, x2, y2, n, c in shared["dets"]:
        col = COLORS.get(n, (200, 200, 200))
        cv2.rectangle(frame, (x1, y1), (x2, y2), col, 2)
        cv2.putText(frame, f"{n} {c:.0%}", (x1, max(y1 - 5, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1, cv2.LINE_AA)
    now = time.time()
    vfps = 0.9 * vfps + 0.1 / max(now - tprev, 1e-3) if vfps else 1 / max(now - tprev, 1e-3)
    tprev = now
    cv2.rectangle(frame, (0, 0), (640, 26), (20, 20, 20), -1)
    cv2.putText(frame, "  ".join(f"{k}:{v}" for k, v in shared["counts"].items()) +
                f"   video {vfps:.0f} fps | detect {shared['dfps']:.1f} fps {shared['lat']:.0f} ms",
                (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.imshow("Nuts & Bolts - local test", frame)
    k = cv2.waitKey(max(1, int((period - (time.time() - t0)) * 1000))) & 0xFF
    if k in (27, ord("q")):
        break
    if k == ord("s"):
        cv2.imwrite(f"snap_{int(time.time())}.jpg", frame)
        print("saved snapshot")
shared["stop"] = True
time.sleep(0.3)
cap.release()
cv2.destroyAllWindows()
