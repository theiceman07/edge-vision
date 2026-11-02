# M1: Correct split (2 pts)

**Checklist:** I explain and show the 70/20/10 split with no leakage

**Status:** PARTIAL

**Notes:** Enclosure dataset split 70/20/10 (train 111 / val 31 / test 16) with a group-aware split: photos whose 64-bit dHash is within 6 bits are kept in one split. `tools/split.py` verifies the counts and checks leakage (0 identical files, 0 near-duplicate part photos across splits). Weakness: the test set is only 6 good / 7 defective images. Splitter: `tools/label_enclosure.py`. A first per-photo split leaked (93 near-duplicate pairs) and was replaced.

## Evidence files in this folder
- data.yaml
- label_enclosure.py
- split.py
- split_counts.md
- split_manifest.csv

Rules: only numbers measured by me on my own hardware; commit on branch `arjun` with the milestone in the message.
