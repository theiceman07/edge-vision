"""Find the sharpest manual focus for the CURRENT camera position and save it to focus.txt.
Put some nuts/bolts in view, stop the dashboard (Stop button), then:  env/bin/python calibrate_focus.py"""
import cv2, glob, subprocess, time
D = (sorted(glob.glob("/dev/v4l/by-id/usb-*-video-index0")) or [0])[0]
c = cv2.VideoCapture(D, cv2.CAP_V4L2) if D != 0 else cv2.VideoCapture(0)
c.set(3, 640); c.set(4, 480); c.set(cv2.CAP_PROP_AUTOFOCUS, 0)
res = []
for v in range(0, 251, 10):
    c.set(cv2.CAP_PROP_FOCUS, v); time.sleep(0.8)
    for _ in range(4): c.read()
    s = []
    for _ in range(5):
        _, f = c.read(); g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY); h, w = g.shape
        s.append(cv2.Laplacian(g[h // 6:5 * h // 6, w // 6:5 * w // 6], cv2.CV_64F).var())
    res.append((v, sum(s) / 5))
best = max(res, key=lambda x: x[1])[0]
open("focus.txt", "w").write(str(best))
print("sharpness by focus:", [(v, round(s)) for v, s in res]); print("saved focus.txt =", best)
