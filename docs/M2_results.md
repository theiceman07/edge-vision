# M2 results: FP32 vs INT8 TFLite
Same test set (80 of 82 images scored; the 2 skipped have mixed polygon/box labels), same tool (ultralytics `val`, imgsz 320, batch 1), same Colab CPU runtime (Intel Xeon, shared cloud CPU).
Notebook: `training/m2_int8_colab.ipynb` (attempts 2 and 3 were extra cells typed into it). Raw numbers: `training/results/m2_int8_*_results.json`.
Target (committed before measuring, `docs/M2_target.md`): INT8 loses at most 2 points of mAP50; p95 latency under 66.7 ms at 15 FPS on the Pi.

## Results (all three attempts, none left out)
| Model | Calibration images | mAP50 | mAP50-95 | Precision | Recall | Size |
|---|---|---|---|---|---|---|
| FP32 PyTorch (`best.pt`) | - | 0.972 | 0.589 | 0.923 | 0.960 | 5.47 MB |
| INT8 TFLite attempt 1 (`app/best_int8_cal50.tflite`) | 36 (half of the 72 validation images) | 0.941 | 0.485 | 0.929 | 0.923 | 3.04 MB |
| INT8 TFLite attempt 2 | 72 (all validation images) | 0.939 | 0.446 | 0.922 | 0.919 | 3.04 MB |
| INT8 TFLite attempt 3 | 390 (training images) | 0.936 | 0.447 | 0.905 | 0.919 | 3.04 MB |

Attempt 1 per class mAP50: bolt 0.962 -> 0.902, nut 0.982 -> 0.981: bolts lose most (recall 0.93 -> 0.865).
Calibration images never overlap the test set. Ultralytics recommends more than 300 calibration images; the dataset's validation split only has 72.

## Verdict against the target
- Accuracy target: MISSED in every attempt (-3.1, -3.3 and -3.6 points vs the allowed -2.0). More calibration data did not help; the differences between attempts are small.
- Speed target: NOT YET MEASURED. The Pi is needed. On the shared Colab CPU ultralytics reported about 67 ms (FP32 PyTorch) vs 38 ms (INT8 TFLite) per image for attempt 1: a cloud CPU, not the Pi, not a benchmark.
- Plain-language trade-off: INT8 makes the model 44% smaller and probably faster, but it misses more bolts (recall down about 4 points) and box quality drops (mAP50-95 down 10+ points). Unless the Pi measurement shows FP32 cannot meet 15 FPS, keep FP32 (ONNX). If INT8 is needed, try quantisation-aware training or a larger calibration set.
