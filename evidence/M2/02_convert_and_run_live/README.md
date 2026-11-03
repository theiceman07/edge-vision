# M2: Convert and run live (4 pts)

**Checklist:** I convert to TFLite INT8 or TensorRT and run it live on the device

**Status:** PARTIAL

**Notes:** Enclosure model converted to INT8 ONNX (onnxruntime static quantisation, not TFLite) and run on the Pi 5 CPU: 14.6 FPS, see ../04_fair_benchmark. The benchmark fed test-set images, not the live camera, so "live" is not shown yet. The nuts-and-bolts TFLite INT8 from Colab is still in app/best_int8_cal50.tflite.

## How it was made
`tools/quantize_enclosure_int8.py` (+ opset 12 -> 13 conversion with `onnx.version_converter`, detect head kept FP32). Output `app/enclosure_int8.onnx`, 4.4 MB.

Rules: only numbers measured by me on my own hardware; commit on branch `arjun` with the milestone in the message.
