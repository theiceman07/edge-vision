# Enclosure model: FP32 vs INT8 on the same test set
Same 16 test images (18 labelled boxes), same script (`tools/eval_enclosure_onnx.py`), conf 0.25, IoU 0.5, 480 px. Run on the Pi 2026-11-03.

| Model | Precision | Recall | mAP50 | Size |
|---|---|---|---|---|
| FP32 `app/enclosure.onnx` | 0.450 | 0.500 | 0.416 | 10.6 MB |
| INT8 `app/enclosure_int8.onnx` | 0.474 | 0.500 | 0.431 | 4.4 MB |

INT8 = onnxruntime static quantisation (QDQ, per-channel INT8 weights, UINT8 activations), 100 calibration images taken from the TRAIN split (not test). The detect head (`/model.23`) is left in FP32: quantising it as well gave 0 detections on every test image (mAP50 0.000).
The INT8 model is not worse than FP32 here, but the difference (+0.015 mAP50) is noise on 16 images. The conclusion is "no measurable loss", not "INT8 is better".
The absolute accuracy is low for both (see ../../M1/06_train_and_run_detector/RESULTS.md).
