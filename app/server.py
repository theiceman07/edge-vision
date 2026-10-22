"""Live nut/bolt/screw detector + dashboard server.

  python server.py                      # USB / CSI camera 0, model best.onnx
  python server.py --camera 1 --model best.pt
Open http://<pi-ip>:5000
"""
import argparse, csv, glob, io, json, os, sqlite3, threading, time
from datetime import datetime
import cv2
import numpy as np
from leds import Leds
from flask import Flask, Response, jsonify, render_template, request

COLORS = {"bolt": (255, 120, 40), "nut": (0, 180, 255), "screw": (80, 230, 90)}  # BGR
MODEL_MAP50 = 0.798        # mAP50 on held-out own-camera photos (yolo11n @320)
DB = "history.db"

app = Flask(__name__)
lock = threading.Lock()
cfg = {"model": "best.onnx", "camera": 0, "imgsz": 320}
state = {
    "running": False, "session": None, "counts": {}, "total": 0, "fps": 0.0,
    "latency_ms": 0.0, "video_fps": 0.0, "led": "off", "avg_conf": 0.0, "conf": 0.5, "peak": {}, "frames": 0,
    "started": None, "error": "", "camera_name": "", "map50": MODEL_MAP50,
    "classes": [], "recent": [],
}
leds = Leds()          # green=nut, red=bolt, blue=both (GPIO 17/27/22)
latest = {"jpeg": None, "cam": None, "boxes": [], "names": {}}
want_run = threading.Event()


# ───────────────────────── database ─────────────────────────
def q(sql, args=(), many=False):
    with sqlite3.connect(DB) as c:
        c.row_factory = sqlite3.Row
        cur = c.executemany(sql, args) if many else c.execute(sql, args)
        return [dict(r) for r in cur.fetchall()] if cur.description else []


def db_init():
    q("""CREATE TABLE IF NOT EXISTS sessions(id INTEGER PRIMARY KEY, start REAL, end REAL,
         frames INT, camera TEXT, model TEXT)""")
    q("""CREATE TABLE IF NOT EXISTS metrics(ts REAL, session INT, fps REAL, latency REAL,
         conf REAL, total INT, counts TEXT)""")
    q("CREATE INDEX IF NOT EXISTS i_m ON metrics(session, ts)")
    q("CREATE TABLE IF NOT EXISTS events(ts REAL, session INT, kind TEXT, msg TEXT)")
    # a crash can leave an open session behind
    q("UPDATE sessions SET end=COALESCE((SELECT MAX(ts) FROM metrics WHERE session=sessions.id), start) "
      "WHERE end IS NULL")


def log_event(kind, msg):
    q("INSERT INTO events VALUES(?,?,?,?)", (time.time(), state["session"], kind, msg))
    with lock:
        state["recent"] = ([{"ts": time.time(), "kind": kind, "msg": msg}] + state["recent"])[:30]


# ───────────────────────── camera ─────────────────────────
class Camera:
    """Reads continuously on a thread so inference always sees the newest frame."""
    def __init__(self, index):
        # a USB webcam can re-enumerate (video0 -> video1); the by-id path stays stable
        usb = sorted(glob.glob("/dev/v4l/by-id/usb-*-video-index0"))
        self.cap = cv2.VideoCapture(usb[0] if usb and index == 0 else index, cv2.CAP_V4L2)
        self.pic = None
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if os.path.exists("focus.txt"):  # fixed manual focus
                self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                self.cap.set(cv2.CAP_PROP_FOCUS, int(open("focus.txt").read()))
        else:
            self.cap = None
            from picamera2 import Picamera2
            self.pic = Picamera2(index)
            self.pic.configure(self.pic.create_video_configuration(
                main={"size": (640, 480), "format": "BGR888"}))
            self.pic.start()
        self.frame, self.ts, self.alive = None, 0, True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.alive:
            if self.cap:
                ok, f = self.cap.read()
                if not ok:
                    time.sleep(0.05)
                    continue
            else:
                f = self.pic.capture_array()
            self.frame, self.ts = f, time.time()

    def read(self):
        return (self.frame, self.ts) if self.frame is not None else (None, 0)

    def close(self):
        self.alive = False
        time.sleep(0.1)
        if self.cap:
            self.cap.release()
        if self.pic:
            self.pic.stop()
            self.pic.close()


def placeholder(text):
    img = np.full((480, 640, 3), 22, np.uint8)
    (w, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    cv2.putText(img, text, ((640 - w) // 2, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 2, cv2.LINE_AA)
    return cv2.imencode(".jpg", img)[1].tobytes()


def draw(frame, boxes, names):
    for x1, y1, x2, y2, c, cid in boxes:
        col = COLORS.get(names[cid], (200, 200, 200))
        cv2.rectangle(frame, (x1, y1), (x2, y2), col, 2)
        t = f"{names[cid]} {c:.0%}"
        (tw, th), _ = cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 6, y1), col, -1)
        cv2.putText(frame, t, (x1 + 3, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)


# ───────────────────────── worker ─────────────────────────
def worker():
    from ultralytics import YOLO
    model = YOLO(cfg["model"], task="detect")
    names = {k: ("bolt" if v == "screw" else v) for k, v in model.names.items()}  # nuts & bolts only: screw -> bolt
    with lock:
        state["classes"] = sorted(set(names.values()))
        state["counts"] = {n: 0 for n in sorted(set(names.values()))}
    latest["jpeg"] = placeholder("Stopped - press Start")
    while True:
        want_run.wait()
        cam = None
        while cam is None and want_run.is_set():
            try:
                cam = Camera(cfg["camera"])
            except Exception as e:
                state["error"] = "Camera not found - retrying (check USB cable/port)"
                time.sleep(2)
        if cam is None:
            state["error"] = ""
            continue
        latest.update(cam=cam, boxes=[], names=names)
        sid = q("INSERT INTO sessions(start,camera,model) VALUES(?,?,?)",
                (time.time(), f"camera {cfg['camera']}", cfg["model"]))
        sid = q("SELECT MAX(id) AS i FROM sessions")[0]["i"]
        with lock:
            state.update(running=True, session=sid, started=time.time(), frames=0, peak={}, error="",
                         camera_name=f"camera {cfg['camera']}")
        log_event("start", "Detection started")
        fps, last_ts, last_db, last_counts, last_change, last_warn = 0.0, 0, 0, None, 0, 0
        confs, lats = [], []
        while want_run.is_set():
            frame, fts = cam.read()
            if frame is None or fts == last_ts:
                if time.time() - max(last_ts, state["started"]) > 3:
                    state["error"] = "Camera disconnected - reconnecting..."
                    log_event("warn", "Camera stalled - reconnecting")
                    latest["cam"] = None
                    leds.off(); state["led"] = "off"
                    cam.close()
                    while want_run.is_set():
                        time.sleep(2)
                        try:
                            cam = Camera(cfg["camera"])
                            latest["cam"] = cam
                            break
                        except Exception:
                            continue
                    last_ts = time.time()
                    continue
                time.sleep(0.01)
                continue
            last_ts = fts
            t0 = time.time()
            r = model.predict(frame, imgsz=cfg["imgsz"], conf=state["conf"], iou=0.45,
                              agnostic_nms=True, verbose=False)[0]
            lat = (time.time() - t0) * 1000
            boxes = [(*map(int, b.xyxy[0]), float(b.conf[0]), int(b.cls[0])) for b in r.boxes]
            counts = {n: 0 for n in sorted(set(names.values()))}
            for *_, cid in boxes:
                counts[names[cid]] += 1
            latest["boxes"] = boxes
            leds.update(counts.get("nut", 0), counts.get("bolt", 0))
            state["led"] = leds.state
            now = time.time()
            inst = 1 / max(now - t0, 1e-3)
            fps = 0.8 * fps + 0.2 * inst if fps else inst
            conf = float(np.mean([b[4] for b in boxes])) if boxes else 0.0
            with lock:
                state.update(counts=counts, total=len(boxes), fps=round(fps, 1), latency_ms=round(lat, 1),
                             avg_conf=round(conf, 3), frames=state["frames"] + 1, error="")
                for k, v in counts.items():
                    state["peak"][k] = max(state["peak"].get(k, 0), v)
            if now - last_db >= 1.0:
                last_db = now
                q("INSERT INTO metrics VALUES(?,?,?,?,?,?,?)",
                  (now, sid, fps, lat, conf, len(boxes), json.dumps(counts)))
            # event log: report a changed count once it's been stable for 2 s
            if counts != last_counts:
                last_counts, last_change = counts, now
            elif last_change and now - last_change > 2 and counts != state.get("_logged"):
                state["_logged"] = counts
                log_event("count", "Count: " + ", ".join(f"{v} {k}" for k, v in counts.items() if v) or "Count: none")
                last_change = 0
            if boxes and conf < 0.45 and now - last_warn > 30:
                last_warn = now
                log_event("warn", f"Low mean confidence ({conf:.0%}) - check lighting/focus")
        latest["cam"] = None
        leds.off(); state["led"] = "off"
        cam.close()
        q("UPDATE sessions SET end=?, frames=? WHERE id=?", (time.time(), state["frames"], sid))
        with lock:
            state.update(running=False, fps=0.0, latency_ms=0.0, total=0, avg_conf=0.0,
                         counts={n: 0 for n in sorted(set(names.values()))})
        log_event("stop", "Detection stopped")
        latest["jpeg"] = placeholder("Stopped - press Start")


# ───────────────────────── routes ─────────────────────────
def snapshot():
    with lock:
        s = {k: v for k, v in state.items() if not k.startswith("_")}
    s["uptime"] = round(time.time() - s["started"]) if s["running"] and s["started"] else 0
    s["series"] = q("SELECT ts,fps,latency,conf,total,counts FROM metrics WHERE session=? "
                    "ORDER BY ts DESC LIMIT 90", (s["session"],))[::-1] if s["session"] else []
    for p in s["series"]:
        p["counts"] = json.loads(p["counts"])
    return s


@app.route("/")
def index():
    return render_template("index.html")


VIDEO_FPS = 15


def streamer():
    """One shared encoder: raw camera frame + latest boxes -> JPEG at a locked VIDEO_FPS."""
    period, n, t_win, last = 1 / VIDEO_FPS, 0, time.time(), 0
    while True:
        t0 = time.time()
        cam = latest.get("cam")
        if cam is not None:
            frame, ts = cam.read()
            if frame is not None and ts != last:
                last = ts
                out = frame.copy()
                draw(out, latest["boxes"], latest["names"])
                latest["jpeg"] = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes()
                latest["seq"] = latest.get("seq", 0) + 1
                n += 1
        if time.time() - t_win >= 1.0:
            state["video_fps"] = round(n / (time.time() - t_win), 1) if cam is not None else 0.0
            n, t_win = 0, time.time()
        time.sleep(max(0.0, period - (time.time() - t0)))


@app.route("/video")
def video():
    def gen():
        seen = -1
        while True:
            seq = latest.get("seq", 0)
            if seq == seen and latest.get("cam") is not None:
                time.sleep(0.01)
                continue
            seen = seq
            if latest["jpeg"] is None:
                time.sleep(0.1)
                continue
            yield b"--f\r\nContent-Type: image/jpeg\r\n\r\n" + latest["jpeg"] + b"\r\n"
            if latest.get("cam") is None:
                time.sleep(0.2)
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=f")


@app.route("/events")
def events():
    def gen():
        while True:
            yield f"data: {json.dumps(snapshot())}\n\n"
            time.sleep(0.5)
    return Response(gen(), mimetype="text/event-stream")


@app.route("/api/stats")
def stats():
    return jsonify(snapshot())


@app.route("/api/control", methods=["POST"])
def control():
    d = request.get_json(force=True)
    if "conf" in d:
        state["conf"] = min(max(float(d["conf"]), 0.05), 0.95)
    if d.get("action") == "start":
        want_run.set()
    if d.get("action") == "stop":
        want_run.clear()
    if d.get("reset"):
        state["peak"] = {}
    return jsonify(ok=True)


@app.route("/api/sessions")
def sessions():
    rows = q("""SELECT s.id, s.start, s.end, s.camera,
                (SELECT COUNT(*) FROM metrics m WHERE m.session=s.id) AS samples,
                (SELECT ROUND(AVG(fps),1) FROM metrics m WHERE m.session=s.id) AS fps,
                (SELECT ROUND(AVG(latency),0) FROM metrics m WHERE m.session=s.id) AS latency,
                (SELECT ROUND(AVG(conf) ,3) FROM metrics m WHERE m.session=s.id AND total>0) AS conf,
                (SELECT MAX(total) FROM metrics m WHERE m.session=s.id) AS peak_total
                FROM sessions s ORDER BY s.id DESC LIMIT 50""")
    return jsonify(rows)


@app.route("/api/events")
def get_events():
    return jsonify(q("SELECT * FROM events ORDER BY ts DESC LIMIT ?", (int(request.args.get("limit", 100)),)))


def session_data(sid):
    s = q("SELECT * FROM sessions WHERE id=?", (sid,))
    if not s:
        return None
    s = s[0]
    s["end"] = s["end"] or time.time()
    m = q("SELECT * FROM metrics WHERE session=? ORDER BY ts", (sid,))
    for r in m:
        r["counts"] = json.loads(r["counts"])
    return s, m, q("SELECT * FROM events WHERE session=? ORDER BY ts", (sid,))


@app.route("/report.csv")
def report_csv():
    d = session_data(request.args.get("session", type=int))
    if not d:
        return "no such session", 404
    s, m, _ = d
    classes = sorted({k for r in m for k in r["counts"]})
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["time", "fps", "latency_ms", "mean_conf", "total"] + classes)
    for r in m:
        w.writerow([datetime.fromtimestamp(r["ts"]).isoformat(timespec="seconds"), round(r["fps"], 1),
                    round(r["latency"]), round(r["conf"], 3), r["total"]] + [r["counts"].get(k, 0) for k in classes])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=session_{s['id']}.csv"})


@app.route("/report")
def report():
    d = session_data(request.args.get("session", type=int))
    if not d:
        return "no such session", 404
    s, m, ev = d
    classes = sorted({k for r in m for k in r["counts"]}) or ["bolt", "nut", "screw"]
    fmt = lambda t: datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
    nz = [r for r in m if r["total"] > 0]
    stats_ = {
        "duration": int(s["end"] - s["start"]), "samples": len(m),
        "fps": np.mean([r["fps"] for r in m]) if m else 0,
        "lat": np.mean([r["latency"] for r in m]) if m else 0,
        "p95": np.percentile([r["latency"] for r in m], 95) if m else 0,
        "conf": np.mean([r["conf"] for r in nz]) if nz else 0,
        "peak": {k: max((r["counts"].get(k, 0) for r in m), default=0) for k in classes},
        "avg": {k: np.mean([r["counts"].get(k, 0) for r in m]) if m else 0 for k in classes},
    }
    return render_template("report.html", s=s, m=m, ev=ev, st=stats_, classes=classes, fmt=fmt,
                           colors={"bolt": "#2878ff", "nut": "#e0a000", "screw": "#2faa2f"},
                           map50=MODEL_MAP50, now=fmt(time.time()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="best.onnx")
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--imgsz", type=int, default=320)
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--no-autostart", action="store_true")
    a = ap.parse_args()
    cfg.update(model=a.model, camera=a.camera, imgsz=a.imgsz)
    db_init()
    threading.Thread(target=worker, daemon=True).start()
    threading.Thread(target=streamer, daemon=True).start()
    if not a.no_autostart:
        want_run.set()
    import atexit
    atexit.register(leds.close)
    app.run(host="0.0.0.0", port=a.port, threaded=True)
