# M2: Export to ONNX (3 pts)

**Checklist:** I run the ONNX export myself and show my commit

**Status:** HAVE

**Notes:** Enclosure model exported on Colab with `best.export(format='onnx', imgsz=480, opset=12, simplify=True)` (last-but-one cell of `training/train_enclosure_colab.ipynb`). File: `app/enclosure.onnx` (10,590,772 bytes). Commit: see `git log -- app/enclosure.onnx` (message "M1: enclosure detector trained ... M2: export ONNX").

Rules: only numbers measured by me on my own hardware; commit on branch `arjun` with the milestone in the message.
