# M3 Decision rule sheet
Based on `app/leds.py` and `app/server.py` (YOLO11n @320 via ONNX). Replace every ____ with the value you actually use/measure.

| Item | Rule |
|---|---|
| Input | Per frame: detections with class (object A / object B) and confidence |
| Threshold | Detection counts only if confidence >= `conf` = ____ (dashboard value) |
| Decision | A only -> green (GPIO17); B only -> red (GPIO27); both -> blue (GPIO22, priority); none -> all off |
| Debounce | LED changes only after N = ____ consecutive agreeing frames (code default 2). One bad frame never switches it |
| Action | Exactly one LED on, others forced off |
| Safe state if camera fails | All LEDs off, placeholder frame, event logged. Tested by unplugging camera on ____ (date); result: ____ |

Evidence to attach: debounce video (1 bad frame vs N frames), LED photos, latency over 20+ events (median ____ ms, max ____ ms).
