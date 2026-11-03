# M3: End-to-end latency (2 pts)

**Checklist:** I measure frame-to-actuator latency over 20+ events

**Status:** PARTIAL

**Notes:** PARTIAL measurement only. Per-frame camera-to-actuator-COMMAND latency over a 120 s live run (1469 frames): median 97.0 ms, p95 118.7 ms, max 360.2 ms (INT8 model, Pi 5, USB camera 640x480). The actuator was a software stub (no LED driven), and the camera saw no enclosure, so there were 0 real events. The required 20+ physical events (part placed -> LED lights, ideally with a timestamped photo or scope) are NOT done.

## Evidence files in this folder
(none yet)

Rules: only numbers measured by me on my own hardware; commit on branch `arjun` with the milestone in the message.
