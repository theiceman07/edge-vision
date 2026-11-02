"""Train the enclosure good/defective detector on the Pi CPU. Run from edge-vision/:  .venv/bin/python training/train_enclosure.py"""
from ultralytics import YOLO
m = YOLO("yolo11n.pt")
m.train(data="training/enclosure_ds/data.yaml", imgsz=480, epochs=60, patience=20, batch=8, device="cpu",
        workers=2, seed=0, project="training/enclosure_runs", name="v1", exist_ok=True, plots=True)
