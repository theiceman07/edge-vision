# M2 target (written before any INT8 measurement)
Written: 2026-10-23, before exporting or measuring the INT8 model. Chosen by Arjun (option "Balanced").

| Item | Target |
|---|---|
| Baseline | FP32 YOLO11n @320, test mAP50 0.972 (PyTorch, Colab; see docs/MODEL_VALIDATION.md) |
| Accuracy | INT8 model loses at most 2 points of mAP50 vs FP32 on the same test set, measured with the same tool |
| Speed | 95th-percentile latency under 66.7 ms per frame (15 FPS budget) on the Raspberry Pi 5 |
| If missed | Keep FP32 or tune (more calibration images, different quantisation) and say so |

The speed target can only be checked on the Pi. Results and the trade-off explanation go in docs/M2_results.md after measuring.
