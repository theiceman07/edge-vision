# M2: Fair benchmark (4 pts)

**Checklist:** I run 20 warm-up and 100+ timed runs at batch 1. I show median and p95 latency, FPS and model size

**Status:** PARTIAL

**Notes:** ONNX FP32 and INT8 on the Pi done for the enclosure model (280 timed runs each, test-set images, not the live camera).

## Evidence files in this folder
- fan_cooled_bench_camera.json
- uncooled_throttled_bench.json
- enclosure_fp32_480_bench.json
- enclosure_int8_480_bench.json

Rules: only numbers measured by me on my own hardware; commit on branch `arjun` with the milestone in the message.

## Enclosure model (app/enclosure.onnx, YOLO11n FP32, 480 px)
Measured on this Pi (aarch64, 4 cores, onnxruntime CPU, batch 1) on 2026-11-03: 20 warm-up + 280 timed runs over the test images, inference time only (resize/normalise before the timer, no NMS).
Median 114.9 ms, mean 117.6 ms, p95 131.0 ms, 8.5 FPS from the mean. Model size 10.6 MB (10,590,772 bytes).
Temperature 30.7 C before, 42.2 C after; `get_throttled` 0x0 before and after (no throttling). Not a fan-cooled-vs-uncooled comparison; this run was not separately cooled.
Against a 15 FPS target this FP32 model at 480 does NOT make it (about 8.5 FPS). Options: INT8, 320 px input, or a lower target. A 640 px retrain would be slower still.

## Enclosure INT8 (app/enclosure_int8.onnx, 480 px)
Same method (20 warm-up + 280 timed, batch 1, inference only), same Pi, 2026-11-03.
Median 66.8 ms, mean 68.3 ms, p95 78.6 ms, 14.6 FPS from the mean. Size 4.4 MB. Temperature 36.2 C -> 45.0 C, `get_throttled` 0x0 (no throttling).
FP32 -> INT8: median 114.9 -> 66.8 ms (1.72x faster), size 10.6 -> 4.4 MB. This is just under 15 FPS and does not include pre/post-processing or NMS, so the full pipeline will be slower than 14.6 FPS.
