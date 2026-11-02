# M3 Decision rule sheet (template: fill with YOUR measured values)
Based on `app/leds.py` and `app/server.py`. Replace every ____ with the value you actually use/measure.

| Item | Rule |
|---|---|
| Input | Per frame: detections with class and confidence |
| Threshold | Detection counts only if confidence >= `conf` = ____ (dashboard slider; justify with a precision/recall table from YOUR model) |
| Decision | nut only -> green (GPIO17); bolt only -> red (GPIO27); both -> blue (GPIO22, priority); none -> all off |
| Debounce | LED changes only after N = ____ consecutive agreeing frames (code default 2; test: `tests/test_leds_debounce.py`, then record the live demo) |
| Action | Exactly one LED on, others forced off |
| Safe state if camera fails | LEDs off, event logged (code: `server.py`). Tested by unplugging the camera on ____ (date); result: ____ |

Evidence to attach: debounce video, LED photos, latency over 20+ events (median ____ ms, max ____ ms).
