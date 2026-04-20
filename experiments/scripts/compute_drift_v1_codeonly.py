#!/usr/bin/env python3
"""compute_drift_v1_codeonly.py — Compute drift summary (code-only) for v1 runs.

Reads: experiments/paper/results_v1.csv
Writes: experiments/paper/drift_summary_v1_codeonly.csv

Compares baseline vs afci conditions per task. For reset variants,
compares baseline_reset vs afci_reset.
"""
import csv
import sys
from pathlib import Path
from collections import defaultdict

IN_CSV = Path("experiments/paper/results_v1.csv")
OUT_CSV = Path("experiments/paper/drift_summary_v1_codeonly.csv")

FIELDNAMES = [
    "task_id",
    "baseline_delta_loc_code", "afci_delta_loc_code", "drift_advantage_loc_code",
    "baseline_layer_jaccard", "afci_layer_jaccard",
    "baseline_delta_tests", "afci_delta_tests",
]


def main():
    if not IN_CSV.exists():
        print(f"ERROR: {IN_CSV} not found. Run aggregate_results_v1.py first.", file=sys.stderr)
        sys.exit(1)

    data = defaultdict(dict)
    with IN_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            task = row["task_id"]
            cond = row["condition"]
            data[task][cond] = row

    rows = []
    for task_id in sorted(data.keys()):
        task_data = data[task_id]
        # Non-reset comparison
        bl = task_data.get("baseline")
        af = task_data.get("afci")
        if bl and af:
            rows.append(_make_row(task_id, bl, af))
        # Reset comparison
        bl_r = task_data.get("baseline_reset")
        af_r = task_data.get("afci_reset")
        if bl_r and af_r:
            rows.append(_make_row(task_id + "_reset", bl_r, af_r))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT_CSV} ({len(rows)} rows)")


def _make_row(task_id: str, bl: dict, af: dict) -> dict:
    bl_loc = int(bl["delta_loc_code"])
    af_loc = int(af["delta_loc_code"])
    return {
        "task_id": task_id,
        "baseline_delta_loc_code": bl_loc,
        "afci_delta_loc_code": af_loc,
        "drift_advantage_loc_code": bl_loc - af_loc,
        "baseline_layer_jaccard": float(bl["layer_jaccard"]),
        "afci_layer_jaccard": float(af["layer_jaccard"]),
        "baseline_delta_tests": int(bl["delta_tests"]),
        "afci_delta_tests": int(af["delta_tests"]),
    }


if __name__ == "__main__":
    main()
