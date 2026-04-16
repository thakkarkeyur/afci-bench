#!/usr/bin/env python3
import csv
import json
from pathlib import Path
from collections import defaultdict

RUNS_DIR = Path("experiments/runs")
OUT_PAPER_DIR = Path("experiments/paper")
OUT_LATEX = Path("paper/tables/table_conformance_summary.tex")
CHECK_SCRIPT = Path("experiments/scripts/afci_guard_check.py")

def safe_load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))

def ensure_conformance(run_dir: Path):
    conf_path = run_dir / "conformance.json"
    if conf_path.exists():
        return safe_load_json(conf_path)
    # generate on demand
    import subprocess
    subprocess.check_call(["python", str(CHECK_SCRIPT), str(run_dir)])
    return safe_load_json(conf_path)

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
                "p0_boundary": conf["p0_boundary"],
                "p0_ports": conf["p0_ports"],
                "p0_contracts": conf["p0_contracts"],
                "p1_observability": conf["p1_observability"],
                "total": conf["total"],
            })

    OUT_PAPER_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_PAPER_DIR / "conformance_summary_v0.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Aggregate mean per condition across tasks
    agg = defaultdict(lambda: defaultdict(int))
    counts = defaultdict(int)

    for r in rows:
        c = r["condition"]
        counts[c] += 1
        for k in ["p0_boundary","p0_ports","p0_contracts","p1_observability","total"]:
            agg[c][k] += int(r[k])

    means = {}
    for c in counts:
        means[c] = {k: (agg[c][k] / counts[c]) for k in agg[c].keys()}

    # Write LaTeX table for paper
    OUT_LATEX.parent.mkdir(parents=True, exist_ok=True)
    order = ["baseline", "afci", "baseline_reset", "afci_reset"]
    lines = []
    lines.append("\\begin{table}[t]")
    lines.append("\\centering")
    lines.append("\\caption{Conformance violations (AFCI-Guard v0). Values are mean violations per run across tasks for each condition. Lower is better. P0 are machine-checkable; P1 are heuristic checks (upgradeable via tests/lints).}")
    lines.append("\\label{tab:conformance}")
    lines.append("\\footnotesize")
    lines.append("\\setlength{\\tabcolsep}{4pt}")
    lines.append("\\renewcommand{\\arraystretch}{1.05}")
    lines.append("\\begin{tabular}{lrrrrr}")
    lines.append("\\toprule")
    lines.append("Condition & P0 Boundary & P0 Ports & P0 Contracts & P1 Observability & Total \\\\")
    lines.append("\\midrule")

    for c in order:
        if c not in means:
            continue
        m = means[c]
        lines.append(
            f"{c.replace('_', '\\\\_')} & "
            f"{m['p0_boundary']:.2f} & {m['p0_ports']:.2f} & {m['p0_contracts']:.2f} & {m['p1_observability']:.2f} & {m['total']:.2f} \\\\"
        )

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    OUT_LATEX.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {csv_path}")
    print(f"Wrote {OUT_LATEX}")

if __name__ == "__main__":
    main()