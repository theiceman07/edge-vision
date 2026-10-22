> **Origin:** this repo starts from code in https://github.com/theiceman07/cv-edge-computing (initial commit cc367b6). Model weights from that repo are NOT included. All measurements, datasets and results added here are produced by me on my own device; see the commit history.

# Nuts & Bolts detection on Raspberry Pi 5 (edge CV)

Real-time nut/bolt detection from a USB webcam with a live web dashboard, status LEDs, session history and PDF/CSV reports.

- **Model:** YOLO11n, 2 classes (`bolt`, `nut`), input 320 px, exported to ONNX. Own-camera validation mAP50 = 0.80 (bolt 0.77, nut 0.83); about 55 ms/frame on a Pi 5 CPU.
- **Video:** locked 15 FPS stream, detection runs separately.
- **LEDs (BCM):** GPIO17 green = nut only, GPIO27 red = bolt only, GPIO22 blue = both (priority). Each LED: GPIO -> 330 ohm -> LED(+), LED(-) -> GND.

## Run
```bash
# old dashboard (OpenCV capture + onnxruntime, drives the LEDs, PDF/CSV reports) - from repo root
python dashboard.py            # http://<pi-ip>:5000

# newer server (separate video/detection threads, sessions, events, HTML report) - from app/
cd app && python server.py     # http://<pi-ip>:5000  (same port: run only one at a time)
```
Install: `pip install ultralytics onnxruntime opencv-python flask fpdf2 gpiozero lgpio` (use CPU-only torch on the Pi).

## Camera focus
`app/focus.txt` holds a fixed manual focus value (autofocus hunts on a plain table). It depends on camera height - re-run `python calibrate_focus.py` (from `app/`) after moving the camera.

## Training pipeline (`app/`)
1. `capture_data.py` - collect photos from your own camera (`n` nuts, `b` bolts, `e` empty/negatives).
2. `autolabel.py` - FastSAM proposals -> YOLO labels; `review.py` - quick browser tool to fix them by hand.
3. `build_final.py` - merge own-camera photos with other data into `ds3/`.
4. `train_colab_v3.ipynb` - train YOLO11n @320 on a Colab T4, export `best.onnx`.

Datasets and photos are not included in this repo.
