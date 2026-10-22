"""Merge repo dataset (ds2) + own-camera dataset (ds_my) into ds3.
Own-camera train images are duplicated x2 so the model favours the real camera/table."""
import shutil
from pathlib import Path
out = Path("ds3")
shutil.rmtree(out, ignore_errors=True)
n = {}
for src, rep in (("ds2", 1), ("ds_my", 2)):
    for split in ("train", "valid"):
        for img in (Path(src) / split / "images").glob("*.jpg"):
            lab = Path(src) / split / "labels" / (img.stem + ".txt")
            for r in range(rep if split == "train" else 1):
                stem = f"{src}_{img.stem}" + (f"_d{r}" if r else "")
                (out / split / "images").mkdir(parents=True, exist_ok=True)
                (out / split / "labels").mkdir(parents=True, exist_ok=True)
                shutil.copy(img, out / split / "images" / (stem + ".jpg"))
                shutil.copy(lab, out / split / "labels" / (stem + ".txt"))
                n[(src, split)] = n.get((src, split), 0) + 1
(out / "data.yaml").write_text("path: /content/ds3\ntrain: train/images\nval: valid/images\nnames:\n  0: bolt\n  1: nut\n")
print(n)
