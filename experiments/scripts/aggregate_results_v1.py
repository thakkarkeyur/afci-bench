#!/usr/bin/env python3
"""aggregate_results_v1.py — Aggregate all v1 run metrics into a single CSV.

Output: experiments/paper/results_v1.csv
"""
import csv
import json
import sys
from pathlib import Path

RUNS_DIR = Path("experiments/runs_v1")
OUT_CSV = Path("experiments/paper/results_v1.csv")

FIELDNAMES = [
    "task_id", "condition",
    "delta_loc_code", "delta_loc_test", "delta_tests",
    "code_additions", "code_deletions",
    "test_additions", "test_deletions",
    "ci_pass", "layer_jaccard", "files_changed_count",
]


def main():
    rows = []
    for task_dir in sorted(RUNS_DIR.glob("T*/")):
        task_id = task_dir.name
        for cond_dir in sorted(task_dir.glob("*/")):
            condition = cond_dir.name
            metrics_path = cond_dir / "metrics.json"
            if not metrics_path.exists():
                print(f"WARN: missing metrics.json in {cond_dir}", file=sys.stderr)
                continue
            m = json.loads(metrics_path.read_text(encoding="utf-8"))
            rows.append({
                "task_id": task_id,
                "condition": condition,
                "delta_loc_code": m.get("delta_loc_code", 0),
                "delta_loc_test": m.get("delta_loc_test", 0),
                "delta_tests": m.get("delta_tests", 0),
                "code_additions": m.get("code_additions", 0),
                "code_deletions": m.get("code_deletions", 0),
                "test_additions": m.get("test_additions", 0),
                "test_deletions": m.get("test_deletions", 0),
                "ci_pass": m.get("ci_pass", False),
                "layer_jaccard": m.get("layer_jaccard", 0),
                "files_changed_count": len(m.get("files_changed", [])),
            })

    if not rows:
        print("ERROR: no run data found in", RUNS_DIR, file=sys.stderr)
        sys.exit(1)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {OUT_CSV} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
