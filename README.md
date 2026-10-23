> **Origin:** starts from https://github.com/theiceman07/cv-edge-computing (initial commit cc367b6), plus shared infrastructure added on this `shared-base` branch (no model weights, no personal results).

# Edge Vision: bolt/nut detection on Raspberry Pi 5

USB camera -> YOLO (ONNX, 320 px) -> decision + debounce -> GPIO LEDs, live dashboard, optional MQTT, PASS/FAIL station, session history and reports.

**This branch is a neutral starting point.** It contains shared code and templates only. Train your own model, measure on your own device and commit your results on your own branch (`docs/BRANCHING.md`).

## Start
```bash
pip install ultralytics onnx onnxruntime opencv-python flask fpdf2 gpiozero lgpio paho-mqtt     # CPU-only torch on the Pi
cd app && python server.py --model best.onnx --map50 <YOUR measured mAP50>                   # http://<pi-ip>:5000
```
Options: `--camera N`, `--imgsz 320`, `--det-fps 15` (detection cap, `0` = unlimited), `--map50` (shows 0 until set),
`--expect bolt=2,nut=2` (PASS/FAIL station, see `docs/STATION.md`), `--mqtt-host --mqtt-ca ...` (env `MQTT_USER`/`MQTT_PASSWORD`).
The video stream is locked at 15 FPS. You must supply `app/best.onnx` (train with `docs/COLAB_TRAINING.md`).

## What is here
- `app/` server, LEDs (GPIO17 green nut / 27 red bolt / 22 blue both), MQTT publisher, station logic, data-collection and labelling tools.
- `tools/` `bench_inference.py`, `realtime_fps_test.py` (paced 15 FPS run), `pi_measure.sh` (one-command Pi evidence), `fake_camera_demo.py` (run the server on a PC), `passfail_eval.py`, `eval_detections.py`.
- `training/` Colab notebooks and analysis scripts (`errors_analysis.py`, `robustness.py`); results are NOT included.
- `docs/` templates and guides: `DATA_CARD.md`, `M3_decision_rule_sheet.md`, `STATION.md`, `SYSTEM_ARCHITECTURE.md`, `COLAB_TRAINING.md`, `BRANCHING.md`.
- `cad/` feeder bracket Model 1 (good) and Model 2 (defective variant): STEP/STL, renders and a verification table (`cad/README.md`); prompts in `docs/CAD_PROMPTS.md`. Stand-in for the IDRP part until your coach confirms.
- `Dockerfile`, `docker-compose.yml`, `deploy/vision.service` (untested on a Pi).
- Tests: `python -m pytest -q tests` (LED debounce logic, MQTT publisher, station logic, pass/fail maths).

Only commit numbers you measured yourself, naming the machine.
