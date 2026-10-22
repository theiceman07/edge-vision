"""Collect training photos from YOUR camera and table.
  env/bin/python capture_data.py
Keys:  n = saving NUTS-only scenes   b = saving BOLTS-only scenes
       e = saving EMPTY table / background (no nuts or bolts)
       p = pause     q/ESC = quit
While a label is active a photo is saved every 0.7 s - slide, rotate and re-scatter the parts between shots.
Photos go to mydata/<nut|bolt|empty>/.
"""
import glob, os, time
import cv2

usb = sorted(glob.glob("/dev/v4l/by-id/usb-*-video-index0"))
cap = cv2.VideoCapture(usb[0] if usb else 0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
if os.path.exists("focus.txt"):          # fixed manual focus (autofocus hunts on a plain table)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    cap.set(cv2.CAP_PROP_FOCUS, int(open("focus.txt").read()))
if not cap.isOpened():
    raise SystemExit("Camera not found - check the USB cable/port")
KEYS = {ord("n"): "nut", ord("b"): "bolt", ord("e"): "empty"}
cur, last = None, 0
n = {k: len(glob.glob(f"mydata/{k}/*.jpg")) for k in KEYS.values()}
for k in n:
    os.makedirs(f"mydata/{k}", exist_ok=True)
while True:
    ok, f = cap.read()
    if not ok:
        time.sleep(0.05)
        continue
    now = time.time()
    if cur and now - last > 0.7:
        cv2.imwrite(f"mydata/{cur}/{cur}_{int(now*1000)}.jpg", f)
        n[cur] += 1
        last = now
    v = f.copy()
    cv2.rectangle(v, (0, 0), (640, 26), (20, 20, 20), -1)
    cv2.putText(v, f"saving: {cur or 'PAUSED'}   nut {n['nut']}  bolt {n['bolt']}  empty {n['empty']}   [n/b/e/p/q]",
                (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if cur else (0, 165, 255), 1, cv2.LINE_AA)
    cv2.imshow("capture", v)
    k = cv2.waitKey(1) & 0xFF
    if k in (27, ord("q")):
        break
    if k in KEYS:
        cur = KEYS[k]
    if k == ord("p"):
        cur = None
print(n)
