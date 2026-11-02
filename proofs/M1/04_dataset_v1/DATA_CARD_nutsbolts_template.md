# Data card (template: fill in YOUR run)

| Item | Value |
|---|---|
| Dataset | Bolts and Nuts v8, Roboflow Universe (mentor-approved web dataset) |
| Author / licence | Kim (workspace `kim-sxidz`), CC BY 4.0: credit the author, state your changes |
| Source | https://universe.roboflow.com/kim-sxidz/bolts-and-nuts-vhkyw/dataset/8 |
| Classes | `bolt`, `nut` |
| Images as downloaded | 550 = train 396 / valid 72 / test 82 (about 72/13/15) |
| Known issues | 6 train + 2 test label files mix polygon and box rows (ultralytics skips them); some boxes group several objects; roboflow exports contain augmented copies, so near-duplicates may sit in different splits (not checked) |
| Your changes | ____ (e.g. resized to 320, rewrote data.yaml paths) |
| Your own images | ____ |
| Your training run | ____ (date, settings, results) |

The dataset itself is not stored in this repo.
