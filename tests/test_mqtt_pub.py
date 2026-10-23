import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from mqtt_pub import DetectionPublisher  # noqa: E402


def test_noop_without_host():
    p = DetectionPublisher()
    assert p.publish({"nut": 1}, 1, "green", 50.0, 15.0) is False


def test_payload_fields():
    d = DetectionPublisher.payload({"nut": 2, "bolt": 0}, 2, "green", 48.2, 14.9)
    assert d["counts"]["nut"] == 2 and d["led"] == "green" and "ts" in d
