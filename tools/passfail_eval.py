#!/usr/bin/env python3
"""Confusion matrix and false-pass rate for the pass/fail station test (M5: 20 parts, 10 good + 10 defective).
Input CSV columns: part_id,truth,decision   truth = good|defective   decision = pass|fail
Usage: python passfail_eval.py results.csv
Positive class = defective. False pass = a defective part that was passed (the dangerous error)."""
import csv
import sys


def evaluate(rows):
    tp = sum(r["truth"] == "defective" and r["decision"] == "fail" for r in rows)   # defective caught
    fn = sum(r["truth"] == "defective" and r["decision"] == "pass" for r in rows)   # false pass
    fp = sum(r["truth"] == "good" and r["decision"] == "fail" for r in rows)        # false fail
    tn = sum(r["truth"] == "good" and r["decision"] == "pass" for r in rows)
    n_def, n_good = tp + fn, tn + fp
    return {"parts": len(rows), "defective": n_def, "good": n_good,
            "caught_defective": tp, "false_pass": fn, "false_fail": fp, "correct_pass": tn,
            "correct_results": tp + tn, "accuracy": (tp + tn) / len(rows) if rows else 0.0,
            "false_pass_rate": fn / n_def if n_def else 0.0, "false_fail_rate": fp / n_good if n_good else 0.0}


def main():
    rows = list(csv.DictReader(open(sys.argv[1])))
    for r in rows:
        if r["truth"] not in ("good", "defective") or r["decision"] not in ("pass", "fail"):
            sys.exit(f"bad row {r}: truth must be good|defective, decision pass|fail")
    m = evaluate(rows)
    print(f"parts {m['parts']} (good {m['good']}, defective {m['defective']})")
    print("                 decided PASS   decided FAIL")
    print(f"truth good       {m['correct_pass']:12d}   {m['false_fail']:12d}")
    print(f"truth defective  {m['false_pass']:12d}   {m['caught_defective']:12d}")
    print(f"correct results: {m['correct_results']} of {m['parts']}  (accuracy {m['accuracy']:.0%})")
    print(f"false-pass rate: {m['false_pass_rate']:.0%}   false-fail rate: {m['false_fail_rate']:.0%}")


if __name__ == "__main__":
    main()
