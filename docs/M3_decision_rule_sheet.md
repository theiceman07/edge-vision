# M3 Decision rule sheet
Based on `app/leds.py` and `app/server.py` (values below are what the code runs today, 2026-11-02).

| Item | Rule |
|---|---|
| Input | Per frame: detections (class, confidence) from `best.onnx` at 320 px, camera frame 640x480. Detection capped at 15 FPS (`--det-fps`). |
| Threshold | A detection counts only if confidence >= `conf` = **0.40** (`--conf`, dashboard slider). Reason: on the 80-image test set (`docs/MODEL_VALIDATION.md` section 2) F1 is best at 0.35-0.45 (0.920 at 0.35, 0.924 at 0.45); 0.40 sits in that range. The PASS/FAIL station counts only detections >= **0.50** (`--station-conf`) so borderline boxes cannot change a verdict. |
| Decision | nut only -> green (GPIO17); bolt only -> red (GPIO27); both -> blue (GPIO22, priority); none -> all off. PASS/FAIL: counts must equal the expected kit (`--expect bolt=2,nut=2`). |
| Debounce | LED changes only after **N = 2** consecutive agreeing frames (`Leds.update(confirm=2)`, covered by `tests/test_leds_debounce.py`). The PASS/FAIL verdict needs **5** consecutive agreeing frames (`--station-confirm 5`, about 0.33 s at 15 FPS). Live video of the debounce: NOT yet recorded. |
| Action | Exactly one LED on, the others forced off. The LED test (`python app/leds.py`) lit green, red and blue on the wired breadboard on 2026-11-02 (operator confirmed). |
| Safe state if camera fails | LEDs off, event "Camera stalled - reconnecting" logged, dashboard shows "Camera disconnected - reconnecting..." (code: `server.py`, after 3 s without a new frame). **Not yet tested by unplugging the camera**: date ____, result ____. |

Evidence still to attach: debounce video, LED photos/video (live detection driving the LEDs), latency over 20+ events (median ____ ms, max ____ ms), camera-unplug test.
