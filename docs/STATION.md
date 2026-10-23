# PASS/FAIL station (M5): definition, procedure, headline metric

## What it checks
A kit-completeness check, a standard inspection use of vision: each tray must hold the expected kit, counted by the detector.
Default kit `bolt=2,nut=2`; change it with `--expect`, e.g. `python server.py --model best.onnx --expect bolt=2,nut=2`.
- **GOOD tray** = exactly the expected kit.
- **DEFECTIVE tray** = anything else: a part missing, an extra part, or the wrong type (e.g. 3 bolts + 1 nut).
- The station says **PASS** when the detected counts equal the kit, **FAIL** otherwise, with the reason ("missing 1 nut", "extra 1 bolt").
- The verdict only changes after 5 consecutive frames agree (`--station-confirm`, about 0.33 s at 15 FPS), so one bad frame never flips it. Until then it shows WAIT.
- If you swap the nuts and bolts for your own printed part and its models, use their class names in `--expect`; the logic does not change.

## 20-tray test (10 good, 10 defective)
Prepare 10 good trays and 10 defective trays, for example 2 each of: missing bolt, missing nut, extra bolt, extra nut, wrong mix (3 bolts + 1 nut). Keep the same camera height and light as the rig.
1. Start the server with `--expect`. Wait until the badge shows PASS or FAIL.
2. Place a tray. When the verdict is stable, click **Tray is GOOD** or **Tray is DEFECTIVE** according to what the tray really is (decide the truth BEFORE looking at the verdict, do not edit it afterwards; **Undo** only for a mis-click).
3. Repeat for all 20 trays (shuffle the order). Each click logs `part_id,truth,decision,reason,counts,ts` to `station_log.csv` (also downloadable at `/inspect.csv`).
4. `python tools/passfail_eval.py station_log.csv` prints the confusion matrix and rates. Commit the CSV and the output.

## Headline metric
**Correct results out of 20** (shown live as "Correct results (headline)"), reported together with the **false-pass rate** (defective trays that were passed, out of the defective ones).
False pass is the dangerous error in inspection (a defect escapes), so it is the number to explain; false fails only cost a re-check.

## Limits
- Counting depends on the detector: overlapping parts, thin bolts and objects far from the camera are its known weak spots. Expect false fails on crowded trays.
- Tested on a PC with a fake camera looping dataset images (decision logic, buttons, CSV, metrics): not yet on a real tray with the Pi camera.
- The model has not been validated on your trays; the 20-tray result is your measurement of that.
