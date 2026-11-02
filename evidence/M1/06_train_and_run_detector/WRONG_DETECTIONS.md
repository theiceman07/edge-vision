# M1: 10 wrong detections (test split, best.onnx, conf >= 0.25, IoU >= 0.5)
Run: `errors_analysis.py` over ds3/test (82 images). Totals: 438 correct detections, 86 errors (63 false positives, 22 missed, 1 class confusion).
Green = ground-truth boxes, red = wrong prediction, magenta = missed object. Images: err_01.jpg ... err_10.jpg, montage.jpg.
The causes below are my visual reading of each image, not proven by an experiment.

| # | Type | Image | What happened | Likely cause |
|---|---|---|---|---|
| 1 | class confusion (nut vs bolt, conf 0.74) | image_61 | A nut resting on the end of a bolt is predicted as nut but matched to a bolt label | Overlapping objects: nut sits on the bolt, boxes overlap, label ambiguous |
| 2 | false positive (nut 0.87) | nut-bolt-train_176 | Model boxes one nut out of three touching nuts | Ground truth is one big box around all three nuts; model detects them individually. Label inconsistency |
| 3 | false positive (bolt 0.75) | image_66 | A small bolt in the cluster has a predicted box but no label | Object not annotated in the test labels (label omission); model arguably right |
| 4 | false positive (bolt 0.69) | image_59 | Long bolt crossed by other bolts: predicted box does not line up with the labelled one | Heavy overlap/occlusion; predicted and labelled boxes differ so IoU < 0.5, counted as FP plus a miss |
| 5 | false positive (bolt 0.69) | nut-bolt-train_115 | Right-hand bolt on the plate boxed on its own | Labels group several bolts in one large box (top-left); model separates them. Label inconsistency |
| 6 | false positive (nut 0.62) | image_20 | Close-up of one large nut fills the frame | Labelled box is smaller than the nut (loose annotation); prediction covers the whole nut so IoU < 0.5 |
| 7 | missed bolt | image_51 | Bolt lying under crossing bolts not detected | Blur plus strong overlap, low contrast against bolts underneath |
| 8 | missed bolt | nut-bolt-train_163 | Long thin threaded rod with nuts on it, vertical, on white | Unusual shape (very thin, tall, nuts attached) and few such examples; small at 320 px |
| 9 | missed bolt | image_58 | Thin tall bolt next to a nut on dark background | Thin object near other objects, overlapping boxes, 320 px resolution |
| 10 | missed bolt | 504_jpg | A normal-looking bolt on a plate not detected | Unclear; confidence probably below 0.25 (pale plate, lighting). Needs a lower threshold test |

## What this tells us
- At least 4 of the 6 false positives (2, 3, 5, 6) are annotation problems in the dataset (grouped boxes, unlabelled objects, loose boxes), not model errors, so mAP understates the model slightly on this test set.
- Real model weaknesses: overlapping/occluded bolts (4, 7, 9) and thin tall bolts (8, 9). Fixes: more such images, higher input size than 320, or tighter labels.
- Next step for your own part: take your own photos under the same camera/light and repeat this analysis.
