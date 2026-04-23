#!/usr/bin/env python3
"""make_table2b_drift_v1.py — Generate LaTeX Table 2b (drift, code-only) for v1.

Reads: experiments/paper/drift_summary_v1_codeonly.csv
Writes: paper/tables/table2b_drift_codeonly_v1.tex
"""
import csv
import sys
from pathlib import Path

IN_CSV = Path("experiments/paper/drift_summary_v1_codeonly.csv")
OUT_TEX = Path("paper/tables/table2b_drift_codeonly_v1.tex")


def main():
    if not IN_CSV.exists():
        print(f"ERROR: {IN_CSV} not found. Run compute_drift_v1_codeonly.py first.", file=sys.stderr)
        sys.exit(1)

    with IN_CSV.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Code-only drift: baseline vs.\ AFCI (v1, Opus~7). "
        r"$\Delta$LOC = net lines changed in non-test source. "
        r"Drift advantage = baseline $-$ AFCI (positive $\Rightarrow$ AFCI is leaner). "
        r"Jaccard measures layer-overlap with expected touch set.}",
        r"\label{tab:drift-v1}",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\renewcommand{\arraystretch}{1.05}",
        r"\begin{tabular}{lrrrrrr}",
        r"\toprule",
        r"Task & BL $\Delta$LOC & AFCI $\Delta$LOC & Drift Adv. & BL Jaccard & AFCI Jaccard & $\Delta$Tests \\",
        r"\midrule",
    ]

    for r in rows:
        tid = r["task_id"].replace("_", r"\_")
        lines.append(
            f"  {tid} & {r['baseline_delta_loc_code']} & {r['afci_delta_loc_code']} "
            f"& {r['drift_advantage_loc_code']} & {r['baseline_layer_jaccard']} "
            f"& {r['afci_layer_jaccard']} & {r['afci_delta_tests']} \\\\"
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
