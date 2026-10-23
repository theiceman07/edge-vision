#!/usr/bin/env python3
"""Run the real dashboard server with a fake camera that loops images (for testing on a PC without a camera/Pi).
Usage: python tools/fake_camera_demo.py --model app/best.onnx --images <folder of jpgs> [--port 5000] [--conf 0.4] [--det-fps 15]
The server's own code runs unchanged (detector thread, 15 FPS stream, stats API, LED logic without GPIO); only the camera is replaced.
Run it from a scratch folder: the server writes history.db into the current directory."""
import argparse
import glob
import os
import sys
import threading
import time

import cv2

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
sys.path.insert(0, APP)
import server  # noqa: E402


class FakeCamera:
    """Loops images at 15 FPS as 640x480 frames (centre crop), same read()/close() interface as server.Camera."""
    def __init__(self, index, images=None):
        self.frames = []
        for f in images:
            im = cv2.imread(f)
            h, w = im.shape[:2]
            if h > 480:
                y = (h - 480) // 2
                im = im[y:y + 480]
            self.frames.append(cv2.resize(im, (640, 480)) if im.shape[1] != 640 else im)
        self.frame, self.ts, self.alive, self.i = None, 0, True, 0
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.alive:
            self.frame, self.ts = self.frames[(self.i // 15) % len(self.frames)], time.time()   # new image each second
            self.i += 1
            time.sleep(1 / 15)

    def read(self):
        return (self.frame, self.ts) if self.frame is not None else (None, 0)

    def close(self):
        self.alive = False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True)
    ap.add_argument("--images", required=True)
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--conf", type=float, default=0.4)
    ap.add_argument("--det-fps", type=float, default=15.0)
    ap.add_argument("--map50", type=float, default=0.0)
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.images, "*.jpg")))[:30]
    if not files:
        sys.exit("no jpg images found")
    server.Camera = lambda idx: FakeCamera(idx, files)
    server.cfg.update(model=a.model, camera=0, imgsz=320)
    server.state["conf"] = a.conf
    server.state["map50"] = server.MODEL_MAP50 = a.map50
    server.DET_PERIOD = 1 / a.det_fps if a.det_fps > 0 else 0
    server.db_init()
    threading.Thread(target=server.worker, daemon=True).start()
    threading.Thread(target=server.streamer, daemon=True).start()
    server.want_run.set()
    server.app.run(host="127.0.0.1", port=a.port, threaded=True)


if __name__ == "__main__":
    main()
