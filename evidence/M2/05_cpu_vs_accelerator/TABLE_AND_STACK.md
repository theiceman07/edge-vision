# CPU vs accelerator + software stack

This Pi 5 has NO accelerator fitted (`lspci` shows only the BCM2712 PCIe bridge and the RP1 south bridge; no Hailo/Coral device nodes). So the comparison is CPU FP32 vs CPU INT8, and there is no accelerator row with numbers.

| Run | Hardware | Precision | Median ms | p95 ms | FPS (mean) | Size | mAP50 (own test, 16 imgs) |
|---|---|---|---|---|---|---|---|
| onnxruntime CPU | Pi 5, 4x Cortex-A76 | FP32 | 114.9 | 131.0 | 8.5 | 10.6 MB | 0.416 |
| onnxruntime CPU | Pi 5, 4x Cortex-A76 | INT8 (head FP32) | 66.8 | 78.6 | 14.6 | 4.4 MB | 0.431 |
| accelerator (e.g. Hailo-8L AI Kit) | not fitted | not measured | n/a | n/a | n/a | n/a | n/a |

Measured 2026-11-03 with `tools/bench_inference.py`, 480 px, batch 1, 280 timed runs, inference only. Raw files in ../04_fair_benchmark.

## Software stack (what runs on the Pi)
```
 Camera (Pi camera / USB)  -->  OpenCV capture + resize / letterbox 480
                                        |
                                        v
                      onnxruntime (CPUExecutionProvider, 4 threads)
                      model: enclosure_int8.onnx  (YOLO11n, QDQ INT8, head FP32)
                                        |
                                        v
              decode + NMS (Python/NumPy)  -->  good / defective decision rule
                                        |
                     +------------------+------------------+
                     v                  v                  v
                 Flask dashboard     LEDs (leds.py)    MQTT publish (mqtt_pub.py)
                        (app/server.py)
 -------------------------------------------------------------
 Raspberry Pi OS (Linux 6.x, aarch64)  /  Raspberry Pi 5, 4 GB
```
Built on Colab T4: Ultralytics YOLO11n training -> `best.pt` -> ONNX export (opset 12) -> INT8 on the Pi (`tools/quantize_enclosure_int8.py`).
