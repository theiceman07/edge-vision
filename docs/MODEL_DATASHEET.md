# Model datasheet: bolt/nut detector (best.onnx)

| Item | Value |
|---|---|
| Task | Object detection, 2 classes: `bolt` (0), `nut` (1) |
| Architecture | YOLO11n (Ultralytics 8.4.184), 2.6 M parameters, about 6.4 GFLOPs at 320 px |
| Input | 1 x 3 x 320 x 320, float32, RGB, values 0-1 (the server resizes camera frames) |
| Output | 1 x 6 x 2100: 4 box values (cx, cy, w, h) + 2 class scores per anchor; NMS applied outside the model |
| Files | `app/best.pt` (5.5 MB, PyTorch), `app/best.onnx` (ONNX, CPU runtime) |
| Training | Colab T4, 60 epochs, batch 32, AdamW (auto), seed 0, augmentations in `training/results/args.yaml` |
| Data | Bolts and Nuts v8 by Kim, CC BY 4.0 (see `docs/DATA_CARD.md`) |
| Test accuracy (PyTorch, 80 images) | P 0.923, R 0.960, mAP50 0.972, mAP50-95 0.589 |
| Recommended threshold | confidence about 0.4 (best F1 0.35-0.45 on the test set), NMS IoU 0.45 as in the server |
| Speed | not yet measured on the Raspberry Pi 5 (PC only: about 14 ms ONNX, 26 ms PyTorch per image on an i5-1135G7) |

## Known limits (measured on a PC, see `docs/MODEL_VALIDATION.md`)
- Weak with heavy JPEG compression and when objects appear much smaller than in training (camera too high or far).
- Overlapping or very thin bolts are the main misses; some "false positives" are label errors in the dataset.
- Only knows nuts and bolts from this dataset; not validated on the printed part, your camera or your lighting.

## Licence notes
- Ultralytics YOLO is AGPL-3.0: sharing or deploying this code and model carries AGPL obligations.
- The dataset is CC BY 4.0: credit Kim and link the source.
