# Split counts and leakage check

Dataset: `training/enclosure_ds`; split made per placement (one photo = one placement), seed 0.

| Class | train | val | test | total |
|---|---|---|---|---|
| empty | 22 | 6 | 3 | 31 |
| enclosure_defective | 47 | 13 | 7 | 67 |
| enclosure_good | 42 | 12 | 6 | 60 |
| **all** | 111 | 31 | 16 | 158 |

Shares: train 70%, val 20%, test 10% (target 70/20/10).

## Leakage check across splits

- Identical files (md5) in different splits: **0**
- Near-duplicates (dHash Hamming <= 6) between part photos in different splits: **0**
- Near-duplicates involving empty-mat photos (expected, same empty mat): 140


Note: the empty-mat photos look alike by design (same empty mat), so near-duplicate pairs among them are expected and harmless.
