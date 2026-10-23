> **Origin:** this repo starts from code in https://github.com/theiceman07/cv-edge-computing (initial commit cc367b6). The weights in `app/` were trained here (see below); all numbers marked *PC* were measured on a laptop, not the Pi.

# Edge Vision: bolt/nut detection on Raspberry Pi 5

USB camera -> YOLO11n (ONNX, 320 px) -> decision + debounce -> GPIO LEDs, live web dashboard, optional MQTT, session history, PDF/CSV reports.

## Status
| Done and measured (PC) | Still to do on the Pi / with your own part |
|---|---|
| Model trained on Colab T4, test mAP50 0.972 | FPS, latency, CPU %, temperature on the Pi |
| PyTorch and ONNX predictions identical | Your own photos / printed part, your own data check |
| 15 FPS locked stream + 15 FPS detection cap tested with a fake camera | Camera, LEDs, Docker from cold boot, auto-start after power cycle |
| Robustness and error analysis (see `docs/`) | INT8 / TFLite conversion, before/after accuracy |

## Model
- YOLO11n, 2 classes (`bolt`, `nut`), input 320, trained on *Bolts and Nuts v8* by Kim (CC BY 4.0). See `docs/DATA_CARD.md`.
- Test set (PyTorch, Colab): precision 0.923, recall 0.960, mAP50 0.972, mAP50-95 0.589. Validation: mAP50 0.959.
- Weights: `app/best.pt` (5.5 MB), `app/best.onnx` (10.5 MB). Full numbers: `training/results/RESULTS.md`, `docs/MODEL_VALIDATION.md`.
- Recommended confidence ~0.4 (best F1 on the test set: 0.35-0.45). Weak spots: heavy JPEG compression, objects far smaller than in training (keep camera height fixed), overlapping or very thin bolts.
- Not validated: Pi speed, your camera/lighting, your own part.

## Install and run
```bash
pip install ultralytics onnxruntime opencv-python flask fpdf2 gpiozero lgpio paho-mqtt   # CPU-only torch on the Pi
cd app && python server.py --model best.onnx --map50 0.972     # http://<pi-ip>:5000
```
Options: `--camera N`, `--imgsz 320`, `--det-fps 15` (detection cap, default 15, `0` = unlimited), `--map50 <your measured value>`
(shows 0 until set), `--no-autostart`, `--mqtt-host --mqtt-port 8883 --mqtt-ca ca.crt --mqtt-topic factory/vision/detection`
(set `MQTT_USER` / `MQTT_PASSWORD` in the environment). The video stream is locked at 15 FPS (`VIDEO_FPS`).
`dashboard.py` in the repo root is the older single-file dashboard; use `app/server.py`.

## LEDs (BCM)
GPIO17 green = nut only, GPIO27 red = bolt only, GPIO22 blue = both (priority); each LED via 330 ohm to GND. An LED changes only after
2 consecutive agreeing frames (`app/leds.py`). If GPIO is unavailable the app keeps running with LEDs disabled. Rule sheet: `docs/M3_decision_rule_sheet.md`.

## Docker and auto-start
- `docker compose up -d` (uses `Dockerfile`, maps `/dev/video0` and the Pi 5 GPIO chip; check `ls /dev/gpiochip*`). Needs `app/best.onnx`. Untested on hardware.
- `deploy/vision.service`: systemd unit; edit user/paths, `sudo systemctl enable --now vision`, then reboot to prove auto-start.

## Tools (`tools/`)
- `bench_inference.py`: latency/FPS of an ONNX model on the machine it runs on (writes JSON).
- `realtime_fps_test.py`: paced run at a locked FPS (default 15): skipped frames, latency, precision/recall. Run it on the Pi for 10 minutes and note the temperature before/after.
- `eval_detections.py`: accuracy from a CSV of truth vs predicted.
- `fake_camera_demo.py`: runs the real server on a PC with a fake camera that loops images (tested 2026-10-23: video 14.7 FPS, detection 14.8 FPS with `--det-fps 15`, LED logic and stats API working). Run it from a scratch folder.
- `passfail_eval.py`: confusion matrix and false-pass rate for the 20-part station test from `part_id,truth,decision` rows.
- Tests: `python -m pytest -q tests` (LED debounce logic, MQTT publisher, pass/fail maths; no hardware needed).

## Training (`training/`, `docs/COLAB_TRAINING.md`)
Colab notebook, results, confusion matrices, `errors_analysis.py` (wrong detections, 10 written up in `training/errors/WRONG_DETECTIONS.md`),
`robustness.py`. Original data tools in `app/`: `capture_data.py`, `autolabel.py`, `review.py`, `merge_ds.py`, `build_final.py`, `calibrate_focus.py`
(`app/focus.txt` is a fixed manual focus; recalibrate after moving the camera).

## Docs
`docs/DATA_CARD.md`, `docs/MODEL_VALIDATION.md`, `docs/M3_decision_rule_sheet.md`, `docs/ARCHITECTURE.md`, `docs/COLAB_TRAINING.md`.

## Rules for results in this repo
Only commit numbers you measured yourself, with the machine named. Datasets and photos are not stored here.

## Team workflow
Shared repo with collaborators. Shared work on `main`; individually assessed milestones go on your own branch `ind/<your-name>`. See `docs/BRANCHING.md`.
