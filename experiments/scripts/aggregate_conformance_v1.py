#!/usr/bin/env python3
"""aggregate_conformance_v1.py — Aggregate v1 conformance results.

Reads: experiments/runs_v1/*/*/conformance.json
Writes:
  - experiments/paper/conformance_summary_v1.csv
  - paper/tables/table_conformance_summary_v1.tex
"""
import csv
import json
import subprocess
import sys
from pathlib import Path
from collections import defaultdict

RUNS_DIR = Path("experiments/runs_v1")
OUT_CSV = Path("experiments/paper/conformance_summary_v1.csv")
OUT_TEX = Path("paper/tables/table_conformance_summary_v1.tex")
CHECK_SCRIPT = Path("experiments/scripts/afci_guard_check.py")

FIELDS = ["p0_boundary", "p0_ports", "p0_contracts", "p1_observability", "total"]
CONDITIONS_ORDER = ["baseline", "afci", "baseline_reset", "afci_reset"]


def safe_load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def ensure_conformance(run_dir: Path):
    conf = run_dir / "conformance.json"
    if conf.exists():
        return safe_load(conf)
    subprocess.check_call([sys.executable, str(CHECK_SCRIPT), str(run_dir)])
    if conf.exists():
        return safe_load(conf)
    return {k: 0 for k in FIELDS}


def main():
    rows = []
    for task_dir in sorted(RUNS_DIR.glob("T*/")):
        task_id = task_dir.name
        for cond_dir in sorted(task_dir.glob("*/")):
            condition = cond_dir.name
            conf = ensure_conformance(cond_dir)
            rows.append({
                "task_id": task_id,
                "condition": condition,
                **{k: conf.get(k, 0) for k in FIELDS},
            })

    if not rows:
        print("ERROR: no conformance data found.", file=sys.stderr)
        sys.exit(1)

    # Write CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["task_id", "condition"] + FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {OUT_CSV} ({len(rows)} rows)")

    # Compute means per condition
    agg = defaultdict(lambda: defaultdict(float))
    counts = defaultdict(int)
    for r in rows:
        c = r["condition"]
        counts[c] += 1
        for k in FIELDS:
            agg[c][k] += int(r[k])

    means = {}
    for c in counts:
        means[c] = {k: agg[c][k] / counts[c] for k in FIELDS}

    # Write LaTeX
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Conformance violations (AFCI-Guard, v1 Opus~7). "
        r"Mean violations per run across tasks. Lower is better. "
        r"P0 = machine-checkable; P1 = heuristic (upgradeable).}",
        r"\label{tab:conformance-v1}",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\renewcommand{\arraystretch}{1.05}",
        r"\begin{tabular}{lrrrrr}",
        r"\toprule",
        r"Condition & P0 Boundary & P0 Ports & P0 Contracts & P1 Observability & Total \\",
        r"\midrule",
    ]

    for c in CONDITIONS_ORDER:
        if c not in means:
            continue
        m = means[c]
        label = c.replace("_", r"\_")
        lines.append(
            f"  {label} & {m['p0_boundary']:.2f} & {m['p0_ports']:.2f} "
            f"& {m['p0_contracts']:.2f} & {m['p1_observability']:.2f} & {m['total']:.2f} \\\\"
        )

    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ]

    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    OUT_TEX.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_TEX}")


if __name__ == "__main__":
    main()
