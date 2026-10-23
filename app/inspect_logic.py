"""PASS/FAIL station logic: a tray passes when the detected object counts equal the expected kit.

decide()      counts + expected kit -> (PASS|FAIL, reason)
Stabilizer    a verdict changes only after N consecutive frames agree (no flicker from one bad frame)
StationLog    operator-entered ground truth (good|defective) + the station's decision -> CSV and live metrics
Positive class = defective. False pass = a defective tray that was passed (the dangerous error).
"""
import csv
import threading
import time
from pathlib import Path

COLUMNS = ["part_id", "truth", "decision", "reason", "counts", "ts"]


def parse_expect(text: str) -> dict:
    """'bolt=2,nut=2' -> {'bolt': 2, 'nut': 2}"""
    out = {}
    for item in text.split(","):
        name, sep, n = item.strip().partition("=")
        if not sep or not name.strip() or not n.strip().isdigit():
            raise ValueError(f"bad --expect item {item!r}; use e.g. bolt=2,nut=2")
        out[name.strip()] = int(n)
    return out


def decide(counts: dict, expected: dict) -> tuple[str, str]:
    problems = []
    for cls, want in expected.items():
        got = counts.get(cls, 0)
        if got < want:
            problems.append(f"missing {want - got} {cls}")
        elif got > want:
            problems.append(f"extra {got - want} {cls}")
    problems += [f"unexpected {got} {cls}" for cls, got in counts.items() if cls not in expected and got > 0]
    return ("FAIL", "; ".join(problems)) if problems else ("PASS", "kit complete")


class Stabilizer:
    def __init__(self, confirm: int = 5):
        self.confirm = confirm
        self.reset()

    def reset(self):
        self.verdict, self.reason, self._pending, self._n = "WAIT", "waiting for stable detection", None, 0

    def update(self, verdict: str, reason: str) -> tuple[str, str]:
        self._n = self._n + 1 if verdict == self._pending else 1
        self._pending = verdict
        if self._n >= self.confirm and (verdict != self.verdict or reason != self.reason):
            self.verdict, self.reason = verdict, reason
        return self.verdict, self.reason


class StationLog:
    def __init__(self, path=None):
        self.path, self._lock, self.rows = (Path(path) if path else None), threading.Lock(), []
        if self.path and self.path.exists():
            with self.path.open(newline="") as f:
                self.rows = list(csv.DictReader(f))

    def record(self, truth: str, decision: str, reason: str = "", counts: dict | None = None) -> dict:
        if truth not in ("good", "defective"):
            raise ValueError("truth must be good or defective")
        if decision not in ("PASS", "FAIL"):
            raise ValueError("no stable PASS/FAIL decision yet")
        with self._lock:
            row = {"part_id": len(self.rows) + 1, "truth": truth, "decision": decision.lower(), "reason": reason,
                   "counts": ";".join(f"{k}={v}" for k, v in sorted((counts or {}).items())), "ts": round(time.time(), 1)}
            self.rows.append(row)
            self._write()
            return row

    def undo(self):
        with self._lock:
            row = self.rows.pop() if self.rows else None
            self._write()
            return row

    def _write(self):
        if self.path:
            with self.path.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=COLUMNS)
                w.writeheader()
                w.writerows(self.rows)

    def metrics(self) -> dict:
        with self._lock:
            rows = list(self.rows)
        tp = sum(r["truth"] == "defective" and r["decision"] == "fail" for r in rows)
        fn = sum(r["truth"] == "defective" and r["decision"] == "pass" for r in rows)
        fp = sum(r["truth"] == "good" and r["decision"] == "fail" for r in rows)
        tn = sum(r["truth"] == "good" and r["decision"] == "pass" for r in rows)
        n_def, n_good, n = tp + fn, tn + fp, len(rows)
        return {"tested": n, "good": n_good, "defective": n_def, "correct": tp + tn, "false_pass": fn, "false_fail": fp,
                "accuracy": (tp + tn) / n if n else 0.0, "false_pass_rate": fn / n_def if n_def else 0.0,
                "false_fail_rate": fp / n_good if n_good else 0.0}

    def csv_text(self) -> str:
        import io
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(self.rows)
        return buf.getvalue()
