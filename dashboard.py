import cv2
import time
import json
import sqlite3
import threading
import numpy as np
from pathlib import Path
from datetime import datetime

from flask import Flask, Response, jsonify, request, send_file
from fpdf import FPDF

BASE_DIR     = Path(__file__).parent
MODEL_PATH   = str(BASE_DIR / "best_v3.onnx")   # 2-class YOLO11n @320 (bolt, nut)
DB_PATH      = str(BASE_DIR / "history.db")
REPORTS_DIR  = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

TARGET_FPS   = 15
INPUT_SIZE   = 320
CONF_THRESH  = 0.40
NMS_THRESH   = 0.45
MIN_BOX_AREA = 0.001
MAX_BOX_AREA = 0.40
CLASSES      = ["bolt", "nut"]
COLORS       = [(0, 200, 255), (0, 255, 0)]

try:
    from gpiozero import LED
    led_nut, led_bolt, led_both = LED(17), LED(27), LED(22)   # green, red, blue
except Exception as e:
    print(f"WARNING: LEDs disabled ({e})")
    led_nut = led_bolt = led_both = None

LED_HOLD     = 0.8   # seconds an LED stays on after the last detection (bridges missed frames)

_led = {"colour": "off", "last_seen": 0.0}


def update_leds(counts):
    """green = nut only, red = bolt only, blue = both (priority). Steady on; off only after LED_HOLD s of nothing."""
    if led_nut is None:
        return
    nut, bolt = counts.get("nut", 0) > 0, counts.get("bolt", 0) > 0
    want = "blue" if nut and bolt else "green" if nut else "red" if bolt else "off"
    now = time.time()
    if want != "off":
        _led["last_seen"] = now
    elif _led["colour"] != "off" and now - _led["last_seen"] < LED_HOLD:
        return                                   # brief gap: keep the current colour lit
    if want != _led["colour"]:
        _led["colour"] = want
        led_both.value = want == "blue"
        led_nut.value = want == "green"
        led_bolt.value = want == "red"


def leds_off():
    _led["colour"] = "off"
    if led_nut is not None:
        for led in (led_nut, led_bolt, led_both):
            led.off()


app = Flask(__name__)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time TEXT,
        end_time TEXT,
        runtime_s REAL,
        avg_fps REAL,
        avg_latency_ms REAL,
        avg_accuracy REAL,
        total_frames INTEGER,
        bolt_count INTEGER,
        nut_count INTEGER
    )""")
    conn.commit()
    conn.close()


init_db()


class DetectionEngine:
    def __init__(self):
        self.net = None
        self.cap = None
        self.lock = threading.Lock()
        self.running = False
        self.stop_event = threading.Event()
        self.latest_frame = None
        self.latest_dets = []
        self.display_jpeg = None

        # live stats
        self.fps = 0.0
        self.latency_ms = 0.0
        self.accuracy = 0.0
        self.object_count = 0
        self.start_time = None
        self.bolt_total_max = 0
        self.nut_total_max = 0

        # running aggregates for the current session
        self._fps_sum = 0.0
        self._fps_n = 0
        self._latency_sum = 0.0
        self._acc_sum = 0.0
        self._acc_n = 0          # frames that actually had detections
        self._frame_n = 0

        self.infer_thread = None
        self.capture_thread = None

    def _load_model(self):
        if self.net is None:
            import onnxruntime as ort                       # ~3x faster than cv2.dnn on the Pi
            so = ort.SessionOptions()
            so.intra_op_num_threads = 3                     # leave a core for camera + web
            self.net = ort.InferenceSession(MODEL_PATH, so, providers=["CPUExecutionProvider"])
            self.inp_name = self.net.get_inputs()[0].name

    def start(self):
        with self.lock:
            if self.running:
                return False
            self._load_model()
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            fp = BASE_DIR / 'app' / 'focus.txt'          # fixed manual focus (autofocus hunts)
            if fp.exists():
                self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                self.cap.set(cv2.CAP_PROP_FOCUS, int(fp.read_text()))
            if not self.cap.isOpened():
                self.cap = None
                return False

            self.stop_event.clear()
            self.latest_frame = None
            self.latest_dets = []
            self.fps = 0.0
            self.latency_ms = 0.0
            self.accuracy = 0.0
            self.object_count = 0
            self._fps_sum = self._latency_sum = self._acc_sum = 0.0
            self._fps_n = 0
            self._frame_n = 0
            self._acc_n = 0
            self.bolt_total_max = 0
            self.nut_total_max = 0
            self.start_time = time.time()
            self.running = True

            self.infer_thread = threading.Thread(target=self._infer_worker, daemon=True)
            self.capture_thread = threading.Thread(target=self._capture_worker, daemon=True)
            self.infer_thread.start()
            self.capture_thread.start()
            return True

    def stop(self):
        with self.lock:
            if not self.running:
                return None
            self.stop_event.set()
            self.running = False
            runtime_s = time.time() - self.start_time if self.start_time else 0.0

        if self.infer_thread:
            self.infer_thread.join(timeout=2)
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        if self.cap:
            self.cap.release()
            self.cap = None
        leds_off()

        n = max(1, self._frame_n)
        record = {
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "runtime_s": runtime_s,
            "avg_fps": self._fps_sum / max(1, self._fps_n),
            "avg_latency_ms": self._latency_sum / n,
            "avg_accuracy": self._acc_sum / max(1, self._acc_n),   # mean confidence over frames with detections
            "total_frames": self._frame_n,
            "bolt_count": self.bolt_total_max,
            "nut_count": self.nut_total_max,
        }
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""INSERT INTO sessions
            (start_time, end_time, runtime_s, avg_fps, avg_latency_ms, avg_accuracy,
             total_frames, bolt_count, nut_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record["start_time"], record["end_time"], record["runtime_s"],
             record["avg_fps"], record["avg_latency_ms"], record["avg_accuracy"],
             record["total_frames"], record["bolt_count"], record["nut_count"]))
        conn.commit()
        conn.close()
        self.start_time = None
        return record

    def _infer_worker(self):
        while not self.stop_event.is_set():
            with self.lock:
                frame = self.latest_frame
            if frame is None:
                time.sleep(0.005)
                continue

            t0 = time.time()
            h, w = frame.shape[:2]
            cy, cx = h // 2, w // 2
            ch, cw = h // 2, w // 2
            crop = frame[cy - ch // 2: cy + ch // 2, cx - cw // 2: cx + cw // 2]
            infer_frame = cv2.resize(crop, (w, h))
            x_scale = cw / INPUT_SIZE
            y_scale = ch / INPUT_SIZE
            x_offset = cx - cw // 2
            y_offset = cy - ch // 2

            blob = cv2.dnn.blobFromImage(infer_frame, 1 / 255.0, (INPUT_SIZE, INPUT_SIZE),
                                          swapRB=True, crop=False)
            output = self.net.run(None, {self.inp_name: blob})[0][0].T

            boxes, confidences, class_ids = [], [], []
            for det in output:
                scores = det[4:]
                cls_id = int(np.argmax(scores))
                conf = float(scores[cls_id])
                if conf < CONF_THRESH:
                    continue
                dcx, dcy, dbw, dbh = det[:4]
                x1 = int((dcx - dbw / 2) * x_scale) + x_offset
                y1 = int((dcy - dbh / 2) * y_scale) + y_offset
                x2 = int((dcx + dbw / 2) * x_scale) + x_offset
                y2 = int((dcy + dbh / 2) * y_scale) + y_offset
                boxes.append([x1, y1, x2 - x1, y2 - y1])
                confidences.append(conf)
                class_ids.append(cls_id)

            frame_area = h * w
            results = []
            if boxes:
                indices = cv2.dnn.NMSBoxes(boxes, confidences, CONF_THRESH, NMS_THRESH)
                if len(indices) > 0:
                    for i in indices.flatten():
                        x, y, bw, bh = boxes[i]
                        ratio = (bw * bh) / frame_area
                        if ratio < MIN_BOX_AREA or ratio > MAX_BOX_AREA:
                            continue
                        results.append((x, y, x + bw, y + bh, confidences[i], class_ids[i]))

            latency_ms = (time.time() - t0) * 1000.0
            avg_conf = float(np.mean([r[4] for r in results])) if results else 0.0

            bolt_n = sum(1 for r in results if r[5] == 0)
            nut_n = sum(1 for r in results if r[5] == 1)

            with self.lock:
                self.latest_dets = results
                self.latency_ms = 0.9 * self.latency_ms + 0.1 * latency_ms if self._frame_n else latency_ms
                self.accuracy = 0.9 * self.accuracy + 0.1 * avg_conf if self._frame_n and avg_conf else (avg_conf or self.accuracy)
                self.object_count = len(results)
                self.bolt_total_max = max(self.bolt_total_max, bolt_n)
                self.nut_total_max = max(self.nut_total_max, nut_n)
                self._latency_sum += latency_ms
                if results:
                    self._acc_sum += avg_conf
                    self._acc_n += 1
                self._frame_n += 1

    def _capture_worker(self):
        prev_t = time.time()
        fps_smooth = 0.0
        frame_time = 1.0 / TARGET_FPS
        next_tick = time.time()

        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                break

            with self.lock:
                self.latest_frame = frame.copy()
                detections = list(self.latest_dets)

            display = frame.copy()
            counts = {}
            for (x1, y1, x2, y2, conf, cls_id) in detections:
                label = CLASSES[cls_id] if cls_id < len(CLASSES) else str(cls_id)
                color = COLORS[cls_id] if cls_id < len(COLORS) else (255, 255, 255)
                counts[label] = counts.get(label, 0) + 1
                cv2.rectangle(display, (x1, y1), (x2, y2), color, 2)
                cv2.putText(display, f"{label} {conf:.2f}", (x1, max(y1 - 6, 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            update_leds(counts)

            cur_t = time.time()
            delta = cur_t - prev_t
            if delta > 0:
                fps_smooth = 0.9 * fps_smooth + 0.1 * (1.0 / delta)
            prev_t = cur_t

            with self.lock:
                self.fps = fps_smooth
                self._fps_sum += fps_smooth
                self._fps_n += 1

            count_str = "  ".join(f"{k}:{v}" for k, v in counts.items()) or "none"
            overlay_h = 85 + max(0, len(counts) - 1) * 25
            cv2.rectangle(display, (10, 10), (300, overlay_h), (30, 30, 30), -1)
            cv2.rectangle(display, (10, 10), (300, overlay_h), (0, 255, 255), 1)
            cv2.putText(display, f"FPS: {fps_smooth:.1f}", (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
            cv2.putText(display, f"Objects: {count_str}", (20, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 1)

            display = cv2.resize(display, (640, 480))
            ok, buf = cv2.imencode(".jpg", display, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ok:
                with self.lock:
                    self.display_jpeg = buf.tobytes()

            next_tick += frame_time
            sleep_s = next_tick - time.time()
            if sleep_s > 0:
                time.sleep(sleep_s)
            else:
                next_tick = time.time()

    def get_status(self):
        with self.lock:
            runtime_s = (time.time() - self.start_time) if (self.running and self.start_time) else 0.0
            return {
                "running": self.running,
                "fps": round(self.fps, 1),
                "latency_ms": round(self.latency_ms, 1),
                "accuracy": round(self.accuracy * 100, 1),
                "object_count": self.object_count,
                "runtime_s": round(runtime_s, 1),
            }

    def get_jpeg(self):
        with self.lock:
            return self.display_jpeg


engine = DetectionEngine()

PLACEHOLDER_JPEG = None


def _make_placeholder():
    global PLACEHOLDER_JPEG
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(img, "Camera stopped", (170, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (120, 120, 120), 2)
    ok, buf = cv2.imencode(".jpg", img)
    PLACEHOLDER_JPEG = buf.tobytes()


_make_placeholder()


def mjpeg_generator():
    while True:
        frame = engine.get_jpeg() if engine.running else None
        payload = frame if frame is not None else PLACEHOLDER_JPEG
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + payload + b"\r\n")
        time.sleep(1.0 / TARGET_FPS)


@app.route("/")
def index():
    return send_file(BASE_DIR / "templates" / "index.html")


@app.route("/video_feed")
def video_feed():
    return Response(mjpeg_generator(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/status")
def api_status():
    return jsonify(engine.get_status())


@app.route("/api/start", methods=["POST"])
def api_start():
    ok = engine.start()
    return jsonify({"ok": ok})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    record = engine.stop()
    return jsonify({"ok": record is not None, "record": record})


@app.route("/api/history")
def api_history():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/report/<int:session_id>")
def api_report(session_id):
    fmt = request.args.get("format", "pdf")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "not found"}), 404
    row = dict(row)

    if fmt == "csv":
        path = REPORTS_DIR / f"session_{session_id}.csv"
        with open(path, "w") as f:
            f.write(",".join(row.keys()) + "\n")
            f.write(",".join(str(v) for v in row.values()) + "\n")
        return send_file(path, as_attachment=True)

    # PDF
    path = REPORTS_DIR / f"session_{session_id}.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "Nuts & Bolts Detection Report", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Session ID: {row['id']}", ln=True)
    pdf.cell(0, 8, f"Start: {row['start_time']}", ln=True)
    pdf.cell(0, 8, f"End:   {row['end_time']}", ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Summary Metrics", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Runtime: {row['runtime_s']:.1f} s", ln=True)
    pdf.cell(0, 8, f"Average FPS: {row['avg_fps']:.1f}", ln=True)
    pdf.cell(0, 8, f"Average Latency: {row['avg_latency_ms']:.1f} ms", ln=True)
    pdf.cell(0, 8, f"Average Accuracy (confidence): {row['avg_accuracy']*100:.1f} %", ln=True)
    pdf.cell(0, 8, f"Total Frames Processed: {row['total_frames']}", ln=True)
    pdf.cell(0, 8, f"Max Bolts in Frame: {row['bolt_count']}", ln=True)
    pdf.cell(0, 8, f"Max Nuts in Frame: {row['nut_count']}", ln=True)
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Recent sessions (history)", ln=True)
    pdf.set_font("Helvetica", "B", 9)
    widths = [14, 50, 24, 20, 24, 28, 15, 15]
    for w, h in zip(widths, ["ID", "Start", "Runtime s", "FPS", "Latency ms", "Accuracy %", "Bolts", "Nuts"]):
        pdf.cell(w, 7, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    hist = [dict(r) for r in conn.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 15").fetchall()]
    conn.close()
    tb = tn = 0
    for r in hist:
        vals = [r["id"], str(r["start_time"])[:19].replace("T", " "), f"{r['runtime_s']:.0f}", f"{r['avg_fps']:.1f}",
                f"{r['avg_latency_ms']:.0f}", f"{r['avg_accuracy']*100:.0f}", r["bolt_count"], r["nut_count"]]
        tb, tn = tb + (r["bolt_count"] or 0), tn + (r["nut_count"] or 0)
        for w, v in zip(widths, vals):
            pdf.cell(w, 6, str(v), border=1)
        pdf.ln()
    pdf.ln(2)
    pdf.cell(0, 6, f"Totals across listed sessions (sum of per-session max): bolts {tb}, nuts {tn}", ln=True)
    pdf.output(str(path))
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
