# Edge vision server. Build on the Pi (arm64):  docker build -t edge-vision .
# Run:  docker compose up -d     (see docker-compose.yml)
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && apt-get clean
WORKDIR /srv/app
RUN pip install --no-cache-dir flask fpdf2 opencv-python-headless onnxruntime ultralytics onnx gpiozero lgpio paho-mqtt
COPY app/ /srv/app/
EXPOSE 5000
CMD ["python", "server.py"]
