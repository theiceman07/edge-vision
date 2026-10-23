# Model validation (results/weights/best.pt and best.onnx), all measured on this PC (Intel i5-1135G7, CPU)
Test set: Bolts and Nuts v8 (Kim, CC BY 4.0), 82 images (80 scored by ultralytics; 2 have mixed polygon/box labels), YOLO11n @ 320.

## 1. PyTorch vs ONNX (what the server runs)
- Predictions identical: 40 test images, 232 detections each, same classes, matched-box IoU 1.000 on all 232.
- ultralytics `val` gives test mAP50 0.973 (pt) vs 0.958 (onnx), mAP50-95 0.608 vs 0.490. Predictions are the same, so this
  difference comes from how validation runs on the ONNX model, not from worse detections. Cause not investigated further.
- CPU speed on this PC: ~26 ms (pt), ~14 ms (onnx) per image. NOT Pi numbers.

## 2. Confidence threshold (test set, IoU 0.5, class-aware)
| conf | precision | recall | F1 |
|---|---|---|---|
| 0.25 | 0.873 | 0.950 | 0.910 |
| 0.35 | 0.905 | 0.935 | 0.920 |
| 0.45 | 0.943 | 0.905 | 0.924 |
| 0.50 | 0.953 | 0.872 | 0.911 |
| 0.60 | 0.968 | 0.783 | 0.866 |
| 0.70 | 0.980 | 0.631 | 0.768 |
Best F1 at conf 0.35-0.45. The server default is 0.5 (slider). Choose a value, write it in the decision sheet, justify with this table.

## 3. Robustness (conf 0.25)
| change | precision | recall |
|---|---|---|
| baseline | 0.873 | 0.950 |
| dim x0.5 / x0.3 | 0.866 / 0.834 | 0.939 / 0.926 |
| bright x1.5 | 0.858 | 0.946 |
| low contrast | 0.859 | 0.961 |
| blur k=7 / k=15 | 0.876 / 0.816 | 0.954 / 0.935 |
| noise sd 15 | 0.849 | 0.915 |
| JPEG quality 15 | 0.778 | 0.837 |
| grayscale | 0.853 | 0.935 |
| rotate 90 | 0.870 | 0.946 |
| objects 60% size | 0.862 | 0.989 |
| objects 40% size | 0.787 | 0.874 |
Fine under lighting, blur, rotation. Weak with heavy JPEG compression and when objects appear much smaller (camera too high).

## 4. NOT verified
- Raspberry Pi 5 speed/FPS/temperature, your USB camera, real lighting, 640x480 camera frames through the server, LEDs.
- Your own printed part (model only knows bolt/nut from this dataset). Test labels contain errors (grouped boxes, unlabelled objects).
