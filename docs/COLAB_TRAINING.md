# Training steps (what was actually done)
1. Download the dataset from the link in `DATA_CARD.md` in YOLOv8 format.
2. Put it in a folder `ds3/` (`train/`, `valid/`, `test/`, `data.yaml`). In `data.yaml` use `path: /content/ds3`, `train: train/images`, `val: valid/images`, `test: test/images`.
3. Optional: resize images to 320 and zip as `nutsbolts_dataset_320.zip` with `ds3/` inside (the notebook expects that name).
4. Colab: open `training/train_nutsbolts_colab.ipynb`, Runtime -> T4 GPU, upload the zip into `/content`, Run all.
   Settings used: YOLO11n, imgsz 320, epochs 60, patience 15, batch 32, seed 0 (about 3 minutes on a T4).
5. Download `best.pt` / `best.onnx` from the zip the last cell produces, copy to `app/`.
6. Check results: `training/results/` (results.csv, confusion matrices), `training/errors_analysis.py` (wrong detections), `training/robustness.py` (lighting/blur/scale tests).
7. For your own part: add your own photos (`app/capture_data.py`, `autolabel.py`, `review.py`), retrain, and update the data card and numbers.
