# M1: Baseline speed (3 pts)

**Checklist:** I measure FPS, latency, CPU/GPU load, temperature and show my own numbers

**Status:** HAVE

**Notes:** Two runs: uncooled (throttled, 85 C) and with fan (48 C, no throttle). Pi 5 has no GPU path used; CPU load is in vmstat_during.txt.

## Evidence files in this folder
- fan_cooled_run/bench_camera.txt
- fan_cooled_run/realtime_15fps.txt
- fan_cooled_run/system.txt
- fan_cooled_run/thermal_after.txt
- fan_cooled_run/thermal_before.txt
- fan_cooled_run/vmstat_during.txt
- uncooled_throttled_run/bench_camera.txt
- uncooled_throttled_run/realtime_15fps.txt
- uncooled_throttled_run/system.txt
- uncooled_throttled_run/thermal_after.txt
- uncooled_throttled_run/thermal_before.txt
- uncooled_throttled_run/vmstat_during.txt

Rules: only numbers measured by me on my own hardware; commit on branch `arjun` with the milestone in the message.
