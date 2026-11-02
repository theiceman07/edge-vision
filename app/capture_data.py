"""Collect training photos from YOUR camera and table.
  env/bin/python capture_data.py
Keys:  n = saving NUTS-only scenes   b = saving BOLTS-only scenes
       e = saving EMPTY table / background (no nuts or bolts)
       p = pause     q/ESC = quit
While a label is active a photo is saved every 0.7 s - slide, rotate and re-scatter the parts between shots.
Photos go to mydata/<nut|bolt|empty>/.

Enclosure mode (python capture_data.py --set enclosure):
       g = GOOD enclosure   d = DEFECTIVE enclosure   e = EMPTY sheet   p = pause   q/ESC = quit
Photos go to mydata_enc/<enclosure_good|enclosure_defective|empty>/ and are named <class>_b<block>_<ms>.jpg.
Each key press starts a new BLOCK (one placement/lighting session); the train/test split is made per block,
so near-identical shots never end up on both sides.
"""
import argparse, glob, os, time
import cv2

ap = argparse.ArgumentParser()
ap.add_argument("--set", choices=["nutsbolts", "enclosure"], default="nutsbolts")
ap.add_argument("--every", type=float, default=0.7, help="seconds between saved photos")
ap.add_argument("--manual", action="store_true", help="class key only SELECTS the class; SPACE saves one photo (one block each)")
args = ap.parse_args()

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
if args.set == "enclosure":
    KEYS = {ord("g"): "enclosure_good", ord("d"): "enclosure_defective", ord("e"): "empty"}
    ROOT = "mydata_enc"
else:
    KEYS = {ord("n"): "nut", ord("b"): "bolt", ord("e"): "empty"}
    ROOT = "mydata"
cur, last, block, flash = None, 0, 0, 0
n = {k: len(glob.glob(f"{ROOT}/{k}/*.jpg")) for k in KEYS.values()}
for k in n:
    os.makedirs(f"{ROOT}/{k}", exist_ok=True)
block = 1 + max([int(os.path.basename(f).split("_b")[1].split("_")[0]) for k in n for f in glob.glob(f"{ROOT}/{k}/*_b*_*.jpg")] or [0])
while True:
    ok, f = cap.read()
    if not ok:
        time.sleep(0.05)
        continue
    now = time.time()
    if cur and not args.manual and now - last > args.every:
        cv2.imwrite(f"{ROOT}/{cur}/{cur}_b{block}_{int(now*1000)}.jpg", f)
        n[cur] += 1
        last = now
    v = f.copy()
    cv2.rectangle(v, (0, 0), (640, 26), (20, 20, 20), -1)
    cv2.putText(v, f"{cur or 'PAUSED'} blk{block} " + " ".join(f"{k.split('_')[-1]}={c}" for k, c in n.items()) + "  [" + "/".join(chr(c) for c in KEYS) + "/p/q]",
                (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if cur else (0, 165, 255), 1, cv2.LINE_AA)
    if now - flash < 0.25:
        cv2.rectangle(v, (0, 0), (639, 479), (255, 255, 255), 8)     # white frame = photo saved
    cv2.imshow("capture", v)
    k = cv2.waitKey(1) & 0xFF
    if k in (27, ord("q")):
        break
    if args.manual and k == 32 and cur:       # SPACE: one clean snapshot, its own block
        block += 1
        cv2.imwrite(f"{ROOT}/{cur}/{cur}_b{block}_{int(now*1000)}.jpg", f)
        n[cur] += 1
        flash = now
    if k in KEYS:
        if args.manual:
            cur = KEYS[k]
        elif cur != KEYS[k]:
            block += 1                    # new class key = new block (new placement/lighting)
        if not args.manual:
            cur = KEYS[k]
    if k == ord("p"):
        cur = None
        block += 1                        # next press starts a fresh block even for the same class
print(n)
