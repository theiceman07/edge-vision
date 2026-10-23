# System architecture (camera + motor monitor + dashboard)

```mermaid
flowchart LR
  subgraph Vision["Vision (edge-vision, Raspberry Pi 5)"]
    CAM[USB camera 640x480] --> CAP[Capture thread]
    CAP --> DET["YOLO11n ONNX @320<br/>detection capped at 15 FPS"]
    DET --> DEC["Decision + debounce (2 frames)"]
    DEC --> LED["GPIO LEDs<br/>17 green nut / 27 red bolt / 22 blue both"]
    CAP --> VID["MJPEG stream locked at 15 FPS"]
    DET --> VID
    DEC --> DB[(SQLite sessions + events)]
  end
  subgraph Motor["Motor monitor (motor-fault-monitor)"]
    IMU[MPU6050 over I2C, 50 Hz] --> WIN[1 s windows + 13 features]
    WIN --> IFO[IsolationForest]
    IFO --> ALERT["Alert policy (3 windows)"]
    IFO --> CSV[(windows CSV)]
  end
  DET -- "detections (TLS + password)" --> MQ[("Mosquitto broker<br/>TLS 8883, no anonymous")]
  CSV -- "mqtt_bridge.py: motor score" --> MQ
  MQ --> SUB[Subscriber / PLC tag]
  VID --> WEB["Flask dashboard :5000<br/>live view, counts, FPS, latency, history, reports"]
  DB --> WEB
  ALERT --> STR["Streamlit dashboard :8501<br/>vibration charts, alerts, CSV export"]
  SYS["systemd / Docker restart policy<br/>auto-start after power cycle"] -.-> Vision
  SYS -.-> Motor
```

Status: each box exists in code. Tested on a PC only: the vision pipeline with a fake camera, the secure broker, both publishers. Not yet tested on the Pi: camera, GPIO LEDs, MPU6050, Docker/systemd auto-start, the combined dashboard.
