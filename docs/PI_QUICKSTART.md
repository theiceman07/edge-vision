# Raspberry Pi 5 quick start (Raspberry Pi OS Bookworm 64-bit)
Written on a PC and **not yet tested on a Pi**: if a step fails, note the error and fix this file.

## 1. Install and get the code
```bash
sudo apt update && sudo apt install -y git python3-venv python3-pip libgl1 v4l-utils
git clone https://github.com/theiceman07/edge-vision.git && cd edge-vision
git switch -c <your-first-name>              # your own branch for your own evidence (docs/BRANCHING.md)
python3 -m venv .venv && source .venv/bin/activate     # a venv is required on Bookworm (PEP 668)
pip install --upgrade pip
pip install ultralytics onnx onnxruntime opencv-python-headless flask fpdf2 gpiozero lgpio paho-mqtt pytest
```
The install pulls PyTorch and takes 10-20 minutes. If `lgpio` fails to build: `sudo apt install -y swig python3-dev build-essential liblgpio-dev` and retry,
or `sudo apt install python3-lgpio` and recreate the venv with `--system-site-packages`.
Give your user camera/GPIO access, then log out and in: `sudo usermod -aG video,gpio $USER`.

## 2. Check the software (no hardware needed)
```bash
python -m pytest -q tests          # expect: 13 passed
```

## 3. Camera and first frame (M1)
```bash
v4l2-ctl --list-devices            # find the USB camera
python -c "import cv2; c=cv2.VideoCapture(0); ok,f=c.read(); cv2.imwrite('first_frame.jpg',f); print(ok, f.shape if ok else '')"
```
Commit `first_frame.jpg` on your branch ("M1: camera first frame"). Fix the camera height and light now; `python app/calibrate_focus.py` sets the focus.

## 4. Run the dashboard
```bash
cd app && python server.py --model best.onnx --map50 0.972        # http://<pi-ip>:5000
```
`best.onnx` is already in `app/`. 0.972 is the test mAP50 measured on Colab for this model (change it if you train your own). Use the confidence slider at about 40%.
Station test (M5): add `--expect bolt=2,nut=2` and follow `docs/STATION.md`.
LEDs (BCM): GPIO17 green = nut, GPIO27 red = bolt, GPIO22 blue = both, each through 330 ohm to GND. If LEDs stay dark, check `ls /dev/gpiochip*` and the terminal for "[leds] GPIO unavailable".

## 5. Collect the speed evidence (M1 baseline speed, M2 benchmark, 15 FPS run)
```bash
cd ~/edge-vision && source .venv/bin/activate
bash tools/pi_measure.sh app/best.onnx samples/test/images samples/test/labels 600
```
It writes `evidence/pi_<time>/` (system info, temperature before/after, throttling flags, CPU samples, latency benchmark, 10-minute paced 15 FPS run). Commit that folder on your branch.
Also record by hand: a screenshot of the live overlay, the LED colours, and the camera-unplug test (LEDs go off and the dashboard shows "Camera disconnected").

## 6. Docker and auto-start (M3 / M5)
- `docker compose up -d` (needs Docker on the Pi; check the `/dev/gpiochip*` name in `docker-compose.yml`). Reboot cold and confirm it comes back by itself.
- Or systemd: edit user and paths in `deploy/vision.service`, copy to `/etc/systemd/system/`, `sudo systemctl enable --now vision`, then `sudo reboot`.

## 7. Optional: MQTT
`python server.py --model best.onnx --mqtt-host <broker> --mqtt-ca <ca.crt>` with `MQTT_USER` / `MQTT_PASSWORD` set (broker setup: the `motor-fault-monitor` repo, `deploy/mosquitto`).

Evidence rules: commit only numbers you measured yourself, on your own branch, with the milestone in the commit message.
