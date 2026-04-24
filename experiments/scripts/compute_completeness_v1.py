"""Compute completeness/thoroughness summary for v1 benchmark results.

Reads experiments/paper/results_v1.csv (48 rows: 12 tasks x 4 conditions) and
produces:
  experiments/paper/completeness_summary_v1.csv
  experiments/paper/completeness_taskwise_v1.csv
  paper/tables/table_completeness_v1.tex
  paper/figures/Figure4_completeness_v1.pdf

Definitions:
  code_churn      = code_additions + code_deletions
  test_churn      = test_additions + test_deletions
  total_loc_churn = code_churn + test_churn   (results_v1.csv has no diff_loc_*
                    columns; total churn = code + test additions + deletions)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_CSV = REPO_ROOT / "experiments" / "paper" / "results_v1.csv"
OUT_DIR_CSV = REPO_ROOT / "experiments" / "paper"
OUT_DIR_TEX = REPO_ROOT / "paper" / "tables"
OUT_DIR_FIG = REPO_ROOT / "paper" / "figures"

CONDITIONS = ["baseline", "afci", "baseline_reset", "afci_reset"]
CONDITION_LABELS = {
    "baseline": "Baseline",
    "afci": "AFCI",
    "baseline_reset": "Baseline (reset)",
    "afci_reset": "AFCI (reset)",
}
REQUIRED_COLS = {
    "task_id", "condition",
    "code_additions", "code_deletions",
    "test_additions", "test_deletions",
    "ci_pass", "files_changed_count",
}


def main():
    df = pd.read_csv(RESULTS_CSV)
    assert len(df) == 48, f"expected 48 rows, got {len(df)}"
    missing = REQUIRED_COLS - set(df.columns)
    assert not missing, f"missing columns: {missing}"
    assert set(df["condition"].unique()) == set(CONDITIONS), (
        f"unexpected conditions: {sorted(df['condition'].unique())}"
    )
    assert df["task_id"].nunique() == 12, "expected 12 distinct task_ids"

    df["code_churn"] = df["code_additions"] + df["code_deletions"]
    df["test_churn"] = df["test_additions"] + df["test_deletions"]
    df["total_loc_churn"] = df["code_churn"] + df["test_churn"]
    df["ci_pass_bool"] = df["ci_pass"].astype(bool)

    # Per-condition summary
    rows = []
    for cond in CONDITIONS:
        sub = df[df["condition"] == cond]
        rows.append({
            "condition": cond,
            "n": len(sub),
            "mean_code_churn": round(sub["code_churn"].mean(), 2),
            "median_code_churn": float(sub["code_churn"].median()),
            "mean_test_churn": round(sub["test_churn"].mean(), 2),
            "median_test_churn": float(sub["test_churn"].median()),
            "mean_files_changed": round(sub["files_changed_count"].mean(), 2),
            "mean_total_loc_churn": round(sub["total_loc_churn"].mean(), 2),
            "pct_ci_pass": round(100.0 * sub["ci_pass_bool"].mean(), 1),
        })
    summary = pd.DataFrame(rows)
    OUT_DIR_CSV.mkdir(parents=True, exist_ok=True)
    summary_path = OUT_DIR_CSV / "completeness_summary_v1.csv"
    summary.to_csv(summary_path, index=False)
    print(f"[csv] {summary_path}")

    # Taskwise pivot
    pivot = df.pivot(index="task_id", columns="condition",
                     values=["code_churn", "test_churn"])
    tw = pd.DataFrame({
        "baseline_code_churn": pivot["code_churn"]["baseline"],
        "afci_code_churn": pivot["code_churn"]["afci"],
        "baseline_test_churn": pivot["test_churn"]["baseline"],
        "afci_test_churn": pivot["test_churn"]["afci"],
        "baseline_reset_code_churn": pivot["code_churn"]["baseline_reset"],
        "afci_reset_code_churn": pivot["code_churn"]["afci_reset"],
        "baseline_reset_test_churn": pivot["test_churn"]["baseline_reset"],
        "afci_reset_test_churn": pivot["test_churn"]["afci_reset"],
    }).reset_index()
    taskwise_path = OUT_DIR_CSV / "completeness_taskwise_v1.csv"
    tw.to_csv(taskwise_path, index=False)
    print(f"[csv] {taskwise_path}")

    # Head-to-head counts
    n_tasks = len(tw)
    nonreset_code_hi = int((tw["afci_code_churn"] > tw["baseline_code_churn"]).sum())
    nonreset_test_hi = int((tw["afci_test_churn"] > tw["baseline_test_churn"]).sum())
    reset_code_hi = int((tw["afci_reset_code_churn"] > tw["baseline_reset_code_churn"]).sum())
    reset_test_hi = int((tw["afci_reset_test_churn"] > tw["baseline_reset_test_churn"]).sum())

    # LaTeX table
    OUT_DIR_TEX.mkdir(parents=True, exist_ok=True)
    tex_path = OUT_DIR_TEX / "table_completeness_v1.tex"

    def fmt(x, digits=1):
        if isinstance(x, (int,)):
            return str(x)
        return f"{x:.{digits}f}"

    lines = []
    lines.append(r"\begin{table}[t]")
    lines.append(r"\centering")
    lines.append(r"\footnotesize")
    lines.append(r"\caption{Completeness/thoroughness summary (v1). Code/test churn and change footprint per condition.}")
    lines.append(r"\label{tab:completeness-v1}")
    lines.append(r"\resizebox{\linewidth}{!}{%")
    lines.append(r"\begin{tabular}{lrrrrrrr}")
    lines.append(r"\toprule")
    lines.append(r"Condition & Mean code & Med.\ code & Mean test & Med.\ test & Mean files & Mean total & CI pass \\")
    lines.append(r"          & churn     & churn      & churn     & churn      & changed    & LOC churn  & (\%)    \\")
    lines.append(r"\midrule")
    for r in rows:
        lines.append(
            f"{CONDITION_LABELS[r['condition']]} & "
            f"{fmt(r['mean_code_churn'])} & "
            f"{fmt(r['median_code_churn'])} & "
            f"{fmt(r['mean_test_churn'])} & "
            f"{fmt(r['median_test_churn'])} & "
            f"{fmt(r['mean_files_changed'])} & "
            f"{fmt(r['mean_total_loc_churn'])} & "
            f"{fmt(r['pct_ci_pass'])} \\\\"
        )
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}%")
    lines.append(r"}")
    lines.append(r"\end{table}")
    tex_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[tex] {tex_path}")

    # Figure4: grouped bar chart (mean code churn, mean test churn) per condition
    OUT_DIR_FIG.mkdir(parents=True, exist_ok=True)
    fig_path = OUT_DIR_FIG / "Figure4_completeness_v1.pdf"

    labels = [CONDITION_LABELS[c] for c in CONDITIONS]
    mean_code = [next(r for r in rows if r["condition"] == c)["mean_code_churn"] for c in CONDITIONS]
    mean_test = [next(r for r in rows if r["condition"] == c)["mean_test_churn"] for c in CONDITIONS]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.4, 3.4))
    x = list(range(len(CONDITIONS)))
    ax1.bar(x, mean_code)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=20, ha="right")
    ax1.set_ylabel("Mean Code Churn (code-only LOC)")
    ax1.grid(axis="y", linestyle=":", alpha=0.5)

    ax2.bar(x, mean_test)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=20, ha="right")
    ax2.set_ylabel("Mean Test Churn (code-only LOC)")
    ax2.grid(axis="y", linestyle=":", alpha=0.5)

    fig.suptitle("Completeness / thoroughness (v1): mean churn per condition")
    fig.tight_layout()
    fig.savefig(fig_path)
    plt.close(fig)
    print(f"[fig] {fig_path}")

    # Headline stats
    print()
    print("=== Headline stats ===")
    for r in rows:
        print(
            f"[{CONDITION_LABELS[r['condition']]:<18}] "
            f"mean code_churn={r['mean_code_churn']:.2f}, "
            f"mean test_churn={r['mean_test_churn']:.2f}, "
            f"CI pass={r['pct_ci_pass']:.1f}%"
        )
    print()
    print(
        f"AFCI non-reset higher code churn in {nonreset_code_hi}/{n_tasks} tasks; "
        f"higher test churn in {nonreset_test_hi}/{n_tasks} tasks"
    )
    print(
        f"AFCI reset higher code churn in {reset_code_hi}/{n_tasks} tasks; "
        f"higher test churn in {reset_test_hi}/{n_tasks} tasks"
    )


if __name__ == "__main__":
    main()
