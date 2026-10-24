# Sample test images (for speed and FPS tests, not for training)
The 82 test-split images and labels of "Bolts and Nuts" v8 by Kim (https://universe.roboflow.com/kim-sxidz/bolts-and-nuts-vhkyw/dataset/8), licence CC BY 4.0 (credit the author).
Changes: images resized to 320x320 (JPEG quality 80) to keep this folder small; label files unchanged (YOLO format; 2 of them mix polygon and box rows, ultralytics skips those).
Use: `bash tools/pi_measure.sh app/best.onnx samples/test/images samples/test/labels`
