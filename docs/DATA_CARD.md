# Data card

| Item | Value |
|---|---|
| Dataset | Bolts and Nuts, version 8 (2024-06-30), Roboflow Universe |
| Author | Kim (Roboflow workspace `kim-sxidz`) |
| Source | https://universe.roboflow.com/kim-sxidz/bolts-and-nuts-vhkyw/dataset/8 |
| Licence | CC BY 4.0 (credit the author; changes must be stated) |
| Task / classes | Object detection, 2 classes: `bolt`, `nut` |
| Images (as downloaded) | 550 = train 396 / valid 72 / test 82 (about 72/13/15) |
| Used in training | train 390 (6 dropped), valid 72, test 80 scored by ultralytics (2 dropped): their label files mix polygon and box rows |
| Changes made by me | Resized images to 320x320 (JPEG quality 80) to fit upload limits; rewrote `data.yaml` paths. Labels unchanged (polygons are converted to boxes by ultralytics) |
| Own images | None yet. Used instead of own photos with mentor approval: mentor ______ on ______ (keep a screenshot of the approval) |
| Split / leakage | Split comes from the dataset author. Roboflow exports contain augmented copies (`.rf.` in names), so near-duplicates of one source image may sit in different splits. Not checked: do not claim "no leakage" without checking |
| Known label problems | Some boxes group several objects, some objects unlabelled, some boxes loose (see `training/errors/WRONG_DETECTIONS.md`) |
| Model trained by | Arjun, Colab T4, YOLO11n @320, 60 epochs (see `training/results/RESULTS.md`) |

The dataset itself is not stored in this repo (download it from the link).
