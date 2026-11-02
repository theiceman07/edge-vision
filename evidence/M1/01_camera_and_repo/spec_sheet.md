# Spec sheet (measured on the device, 2026-11-02)

| Item | Value |
|---|---|
| Board | Raspberry Pi 5 Model B Rev 1.1 |
| CPU | Cortex-A76, 4 cores, max 2400 MHz |
| Memory | 4045 MB RAM |
| OS | Debian GNU/Linux 13 (trixie), kernel 6.18.50+rpt-rpi-2712, aarch64 |
| Python | Python 3.13.5 |
| Packages | Flask 3.1.3; onnxruntime 1.31.1; opencv-python 5.0.0.93; torch 2.15.0+cpu; ultralytics 8.4.198 |
| Cooling | Pi 5 active cooler (fan heatsink), fitted 2026-11-02; before that no cooler (throttled at 85 C) |
| Camera | Logitech Brio 100, USB, 640x480 MJPG, manual focus value 70 |
| Actuator | 3 LEDs on GPIO17 (green), GPIO27 (red), GPIO22 (blue), 330 ohm each |
| Repo / branch | arjun @ 6880c91 |
