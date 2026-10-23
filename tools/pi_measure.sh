#!/usr/bin/env bash
# Collect Raspberry Pi evidence for M1 baseline speed / M2 benchmark / M5 15 FPS run in one go.
# Usage (from the repo root, with the camera plugged in):
#   bash tools/pi_measure.sh <model.onnx> <test_images_dir> <test_labels_dir> [seconds=600]
# Writes evidence/pi_<timestamp>/ : system info, temperature before/after, throttling flags, CPU/memory samples,
# camera latency benchmark, paced 15 FPS run. Commit that folder on YOUR branch. Everything here is measured on this device.
set -u
MODEL="${1:?model .onnx}"; IMAGES="${2:?test images dir}"; LABELS="${3:?test labels dir}"; SECS="${4:-600}"
OUT="evidence/pi_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$OUT"
temp() { vcgencmd measure_temp 2>/dev/null || echo "vcgencmd not available"; }
{ date -Is; uname -a; tr -d '\0' < /proc/device-tree/model 2>/dev/null; echo; python3 --version
  pip list 2>/dev/null | grep -i -E "ultralytics|onnx|opencv|torch|numpy|flask"; echo "model: $MODEL"; ls -l "$MODEL"; } > "$OUT/system.txt" 2>&1
{ echo "before: $(temp)"; vcgencmd get_throttled 2>/dev/null; } > "$OUT/thermal_before.txt"
vmstat 5 > "$OUT/vmstat_during.txt" 2>&1 & VM=$!
echo "== 1/2 camera latency benchmark (300 frames)"
python3 tools/bench_inference.py --model "$MODEL" --camera 0 --n 300 2>&1 | tee "$OUT/bench_camera.txt"
echo "== 2/2 paced 15 FPS run for ${SECS}s"
python3 tools/realtime_fps_test.py --model "$MODEL" --images "$IMAGES" --labels "$LABELS" --fps 15 --seconds "$SECS" --conf 0.4 2>&1 | tee "$OUT/realtime_15fps.txt"
kill "$VM" 2>/dev/null
{ echo "after: $(temp)"; vcgencmd get_throttled 2>/dev/null; echo "(get_throttled 0x0 = no throttling or undervoltage since boot)"; } > "$OUT/thermal_after.txt"
cat "$OUT/thermal_before.txt" "$OUT/thermal_after.txt"
echo "Saved to $OUT. Commit it on your branch with a message like: M1: baseline speed on Pi 5."
