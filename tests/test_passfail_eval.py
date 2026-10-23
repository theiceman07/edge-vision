import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from passfail_eval import evaluate  # noqa: E402


def rows(spec):
    return [{"part_id": str(i), "truth": t, "decision": d} for i, (t, d) in enumerate(spec)]


def test_counts_and_rates():
    spec = [("good", "pass")] * 9 + [("good", "fail")] + [("defective", "fail")] * 8 + [("defective", "pass")] * 2
    m = evaluate(rows(spec))
    assert (m["correct_pass"], m["false_fail"], m["caught_defective"], m["false_pass"]) == (9, 1, 8, 2)
    assert m["correct_results"] == 17 and abs(m["false_pass_rate"] - 0.2) < 1e-9 and abs(m["false_fail_rate"] - 0.1) < 1e-9


def test_empty_is_safe():
    assert evaluate([])["accuracy"] == 0.0
