import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from inspect_logic import Stabilizer, StationLog, decide, parse_expect  # noqa: E402

KIT = {"bolt": 2, "nut": 2}


def test_parse_expect():
    assert parse_expect("bolt=2, nut=2") == KIT
    for bad in ("bolt", "bolt=x", "=2", "bolt=-1"):
        with pytest.raises(ValueError):
            parse_expect(bad)


def test_decide_pass_and_each_defect_type():
    assert decide({"bolt": 2, "nut": 2}, KIT) == ("PASS", "kit complete")
    assert decide({"bolt": 1, "nut": 2}, KIT) == ("FAIL", "missing 1 bolt")
    assert decide({"bolt": 2, "nut": 3}, KIT) == ("FAIL", "extra 1 nut")
    assert decide({"bolt": 1, "nut": 3}, KIT) == ("FAIL", "missing 1 bolt; extra 1 nut")
    assert decide({"bolt": 2, "nut": 2, "screw": 1}, KIT) == ("FAIL", "unexpected 1 screw")
    assert decide({}, KIT)[0] == "FAIL"


def test_stabilizer_ignores_single_bad_frame():
    s = Stabilizer(confirm=3)
    assert s.update("PASS", "kit complete")[0] == "WAIT"
    for _ in range(2):
        s.update("PASS", "kit complete")
    assert s.verdict == "PASS"
    assert s.update("FAIL", "missing 1 nut")[0] == "PASS"            # one bad frame: no change
    s.update("PASS", "kit complete")
    s.update("FAIL", "missing 1 nut"); s.update("FAIL", "missing 1 nut")
    assert s.update("FAIL", "missing 1 nut") == ("FAIL", "missing 1 nut")   # three in a row: changes


def test_station_log_metrics_persist_and_undo(tmp_path):
    p = tmp_path / "log.csv"
    log = StationLog(p)
    spec = [("good", "PASS")] * 9 + [("good", "FAIL")] + [("defective", "FAIL")] * 8 + [("defective", "PASS")] * 2
    for truth, dec in spec:
        log.record(truth, dec, counts={"bolt": 2, "nut": 2})
    m = log.metrics()
    assert (m["tested"], m["correct"], m["false_pass"], m["false_fail"]) == (20, 17, 2, 1)
    assert abs(m["false_pass_rate"] - 0.2) < 1e-9 and abs(m["accuracy"] - 0.85) < 1e-9
    assert StationLog(p).metrics()["tested"] == 20                   # survives restart
    row = log.undo()
    assert str(row["part_id"]) == "20" and log.metrics()["tested"] == 19


def test_station_log_rejects_bad_input(tmp_path):
    log = StationLog(tmp_path / "l.csv")
    with pytest.raises(ValueError):
        log.record("maybe", "PASS")
    with pytest.raises(ValueError):
        log.record("good", "WAIT")
