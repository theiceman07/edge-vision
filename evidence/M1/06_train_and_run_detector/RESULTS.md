# Colab run nb_short (YOLO11n @320, T4, 60 epochs, patience 15, seed 0)
Dataset: Bolts and Nuts v8 by Kim, CC BY 4.0 (https://universe.roboflow.com/kim-sxidz/bolts-and-nuts-vhkyw/dataset/8), resized to 320 px.
Used: train 390 of 396 images (6 dropped: mixed polygon/box labels), val 72, test 80 of 82 (2 dropped, same reason).

| Split | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|---|
| val (best.pt, selected on this) | 0.935 | 0.915 | 0.959 | 0.600 |
| test | 0.923 | 0.960 | 0.972 | 0.589 |

Per class (test): bolt P 0.874 R 0.930 mAP50 0.962; nut P 0.972 R 0.991 mAP50 0.982.
Per class (val): bolt P 0.916 R 0.848 mAP50 0.931; nut P 0.955 R 0.981 mAP50 0.987.
Colab T4 inference 6.7-22 ms/image (NOT a Pi number). Training took 0.051 h.
Curves: train and val losses both fall and stay close (box 1.13 vs 1.26, cls 0.70 vs 0.69 at epoch 60) -> no overfitting.
Best val mAP50 at epoch 59/60 and still creeping up -> slightly undertrained; early stopping never triggered.
Confusion matrix (normalised, val): bolt 0.96, nut 1.00 correct; most false positives are predicted bolts.
Not yet done: your own photos/part, Pi benchmark, INT8, 10 wrong-detection write-up.

---

# Enclosure detector: Colab run enc_480 (YOLO11n @480, T4, 100 epochs, patience 30, batch 16, seed 0)
Dataset: my own enclosure photos, group-aware 70/20/10 split (see ../05_correct_split). Classes: enclosure_good, enclosure_defective.
Files: `enclosure/enc_480` (training, curves, results.csv), `enclosure/eval_val_480`, `enclosure/eval_test_480` (confusion matrices), `enclosure/test_pred_480` (predictions on test). Model: `app/enclosure.onnx` (opset 12, 10.6 MB).

| Split | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|---|
| val (best.pt epoch 77, from results.csv) | 0.561 | 0.710 | 0.640 | 0.598 |
| test (my own re-evaluation of the exported ONNX, see below) | 0.450 | 0.500 | 0.416 | n/a |

Test re-evaluation: 16 images, 18 labelled boxes (7 good, 11 defective), conf 0.25, IoU 0.5, own script (onnxruntime, letterbox 480, NMS 0.7), AP50 by all-point interpolation at conf 0.001.
Per class (test): good TP 4/9 predicted, 7 labelled, P 0.444 R 0.571 AP50 0.452; defective TP 5/11 predicted, 11 labelled, P 0.455 R 0.455 AP50 0.380.
These test numbers come from my own script, not from Ultralytics `val`, so they can differ slightly from the Colab output for the test split. Use the Colab test numbers (printed by the evaluation cell, and plotted in `enclosure/eval_test_480/`) if they are available.
Reading: the test set is tiny (16 images), so the numbers are noisy. The model does NOT meet a useful target yet: val and test are both weak, and the main error is confusing good with defective (see WRONG_DETECTIONS.md), not failing to find the enclosure.
Training ran all 100 epochs without early stopping; best val mAP50-95 at epoch 77.
Not yet done: 640 run, more defective/good examples, Pi benchmark of enclosure.onnx.
