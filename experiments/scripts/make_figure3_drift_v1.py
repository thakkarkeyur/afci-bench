#!/usr/bin/env python3
"""make_figure3_drift_v1.py — Generate Figure 3 (drift bar chart, code-only) for v1.

Reads: experiments/paper/drift_summary_v1_codeonly.csv
Writes: paper/figures/Figure3_drift_codeonly_v1.pdf
"""
import csv
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("ERROR: matplotlib and numpy required. Install with: pip install matplotlib numpy", file=sys.stderr)
    sys.exit(1)

IN_CSV = Path("experiments/paper/drift_summary_v1_codeonly.csv")
OUT_PDF = Path("paper/figures/Figure3_drift_codeonly_v1.pdf")


def main():
    if not IN_CSV.exists():
        print(f"ERROR: {IN_CSV} not found. Run compute_drift_v1_codeonly.py first.", file=sys.stderr)
        sys.exit(1)

    with IN_CSV.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    tasks = [r["task_id"] for r in rows]
    bl_loc = [int(r["baseline_delta_loc_code"]) for r in rows]
    af_loc = [int(r["afci_delta_loc_code"]) for r in rows]

    x = np.arange(len(tasks))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 5))
    bars_bl = ax.bar(x - width / 2, bl_loc, width, label="Baseline", color="#d62728", alpha=0.85)
    bars_af = ax.bar(x + width / 2, af_loc, width, label="AFCI", color="#1f77b4", alpha=0.85)

    ax.set_xlabel("Task")
    ax.set_ylabel("ΔLOC (code-only)")
    ax.set_title("Code-Only Drift: Baseline vs AFCI (v1, Opus 7)")
    ax.set_xticks(x)
    ax.set_xticklabels(tasks, rotation=45, ha="right", fontsize=8)
    ax.legend()
    ax.axhline(y=0, color="grey", linewidth=0.5, linestyle="--")

    fig.tight_layout()
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(OUT_PDF), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
