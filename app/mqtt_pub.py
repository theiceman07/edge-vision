"""Optional MQTT publisher for detections (TLS + username/password). No-op unless a host is configured.

Topic default: factory/vision/detection   Payload: {"ts","counts","total","led","latency_ms","fps"}
Credentials: env MQTT_USER / MQTT_PASSWORD (never commit them).
"""
import json
import os
import time


class DetectionPublisher:
    def __init__(self, host=None, port=8883, cafile="ca.crt", topic="factory/vision/detection",
                 user=None, password=None, min_interval=1.0):
        self.topic, self.min_interval, self.client, self._last, self._last_counts = topic, min_interval, None, 0.0, None
        if not host:
            return
        import paho.mqtt.client as mqtt
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.tls_set(ca_certs=cafile)
        user = user or os.environ.get("MQTT_USER")
        if user:
            self.client.username_pw_set(user, password or os.environ.get("MQTT_PASSWORD"))
        self.client.connect_async(host, port)
        self.client.loop_start()

    @staticmethod
    def payload(counts, total, led, latency_ms, fps):
        return {"ts": time.time(), "counts": counts, "total": total, "led": led,
                "latency_ms": latency_ms, "fps": fps}

    def publish(self, counts, total, led, latency_ms, fps):
        """Publish when counts change or every min_interval seconds. Never raises into the detection loop."""
        if self.client is None:
            return False
        now = time.time()
        if counts == self._last_counts and now - self._last < self.min_interval:
            return False
        self._last, self._last_counts = now, dict(counts)
        try:
            self.client.publish(self.topic, json.dumps(self.payload(counts, total, led, latency_ms, fps)), qos=1)
            return True
        except Exception:
            return False
