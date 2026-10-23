# M2 results: FP32 vs INT8 TFLite (attempt 1)
Same test set (80 of 82 images scored), same tool (ultralytics `val`, imgsz 320, batch 1), same Colab CPU runtime. Notebook: `training/m2_int8_colab.ipynb`. Raw numbers: `training/results/m2_int8_cal50_results.json`.
Target (committed before measuring, `docs/M2_target.md`): INT8 loses at most 2 points of mAP50; p95 latency under 66.7 ms at 15 FPS on the Pi.

| Model | mAP50 | mAP50-95 | Precision | Recall | Size |
|---|---|---|---|---|---|
| FP32 PyTorch (`best.pt`) | 0.972 | 0.589 | 0.923 | 0.960 | 5.47 MB |
| INT8 TFLite, calibration `fraction=0.5` (`app/best_int8_cal50.tflite`) | 0.941 | 0.485 | 0.929 | 0.923 | 3.04 MB |
| Change | -3.1 points | -10.4 points | +0.6 | -3.7 | -44% |

Per class mAP50: bolt 0.962 -> 0.902, nut 0.982 -> 0.981. Bolts lose most (recall 0.93 -> 0.865).

## Verdict against the target
- Accuracy target: MISSED (-3.1 points vs the allowed -2.0).
- Speed target: NOT YET MEASURED. The Pi is needed. On the shared Colab Xeon CPU ultralytics reported about 67 ms (FP32 PyTorch) vs 38 ms (INT8 TFLite) per image; that is a cloud CPU, not the Pi, and not a benchmark.
- Plain-language trade-off: INT8 makes the file 44% smaller and probably faster, but it misses a few more bolts (recall down 3.7 points). Per the target's "if missed" rule the next step is to tune calibration and measure again, or keep FP32.
