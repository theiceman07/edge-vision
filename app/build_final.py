"""Final dataset ds3 = reviewed own-camera photos (x2 in train) + empty negatives + repo data (ds2)."""
import glob, random, shutil
from pathlib import Path
out = Path("ds3")
shutil.rmtree(out, ignore_errors=True)
random.seed(1)
cnt = {}


def put(img, lab_text, split, name):
    (out / split / "images").mkdir(parents=True, exist_ok=True)
    (out / split / "labels").mkdir(parents=True, exist_ok=True)
    shutil.copy(img, out / split / "images" / (name + ".jpg"))
    (out / split / "labels" / (name + ".txt")).write_text(lab_text)
    cnt[(split, name.split("_")[0])] = cnt.get((split, name.split("_")[0]), 0) + 1


mine = []
for c in ("nut", "bolt"):
    for p in sorted(glob.glob(f"mydata/{c}/*.jpg")):
        lf = Path("review") / (Path(p).stem + ".txt")
        if lf.exists():
            mine.append((p, lf.read_text()))
mine += [(p, "") for p in sorted(glob.glob("mydata/empty/*.jpg"))]       # negatives: no labels
random.shuffle(mine)
nval = int(len(mine) * 0.2)
for i, (p, t) in enumerate(mine):
    name = "my_" + Path(p).stem
    if i < nval:
        put(p, t, "valid", name)
    else:
        for r in range(2):
            put(p, t, "train", name + (f"_d{r}" if r else ""))
for split in ("train", "valid"):
    for img in (Path("ds2") / split / "images").glob("*.jpg"):
        put(img, (Path("ds2") / split / "labels" / (img.stem + ".txt")).read_text(), split, "repo_" + img.stem)
(out / "data.yaml").write_text("path: /content/ds3\ntrain: train/images\nval: valid/images\nnames:\n  0: bolt\n  1: nut\n")
print(cnt)
