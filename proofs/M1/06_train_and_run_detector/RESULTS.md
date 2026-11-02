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
