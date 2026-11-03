# Edge vision server. Build on the Pi (arm64):  docker build -t edge-vision .
# Run:  docker compose up -d     (see docker-compose.yml)
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && apt-get clean
WORKDIR /srv/app
# On an x86 PC, avoid multi-GB CUDA libraries:  docker build --build-arg PIP_EXTRA="--extra-index-url https://download.pytorch.org/whl/cpu" -t edge-vision .
# Offline install: wheels/ is pre-downloaded (flaky network kept killing the torch download).
# Refill with:  docker run --rm -v $PWD/wheels:/w python:3.11-slim pip download -d /w <packages>
COPY wheels/ /wheels/
RUN pip install --no-index --find-links /wheels flask fpdf2 opencv-python-headless onnxruntime ultralytics onnx gpiozero lgpio paho-mqtt \
    && python -c "import flask, cv2, onnxruntime, ultralytics, gpiozero, paho.mqtt.client" \
    && rm -rf /wheels
COPY app/ /srv/app/
EXPOSE 5000
CMD ["python", "server.py"]
