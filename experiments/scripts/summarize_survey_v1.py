"""Sanitize and summarize the AFCI/MAD employee survey for the paper artifact.

Inputs (local-only, NEVER committed): newest *.xlsx in repo root matching the
AFCI survey export.

Outputs (sanitized, public-safe):
  experiments/paper/survey_summary_overall_v1.csv
  experiments/paper/survey_summary_by_role_v1.csv
  paper/tables/table_survey_summary_overall_v1.tex
  paper/tables/table_survey_by_role_v1.tex
  paper/figures/Figure4_reset_time_by_role_v1.pdf

Notes:
  n is small; figures are descriptive only, no statistical claims.
  Drops Email/Name/timestamps/IDs and all open-ended free-text columns.
"""
from __future__ import annotations

import glob
import os
import sys
from pathlib import Path
from statistics import median

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_CSV_DIR = REPO_ROOT / "experiments" / "paper"
OUT_TEX_DIR = REPO_ROOT / "paper" / "tables"
OUT_FIG_DIR = REPO_ROOT / "paper" / "figures"

# Bucket orderings (low rank = faster / less frequent / shorter).
RESET_ORDER = [
    "< 5 minutes",
    "5-15 minutes",
    "15-30 minutes",
    "30-60 minutes",
    "60 minutes",
    "> 60 minutes",
]
SYMPTOM_ORDER = [
    "Never",
    "Rarely (monthly)",
    "Sometimes (weekly)",
    "Often (daily)",
]
MAD_READ_ORDER = [
    "< 2 minutes",
    "2-5 minutes",
    "5-10 minutes",
    "10-20 minutes",
    "20 minutes",
    "20+ minutes",
    "> 20 minutes",
]

NA_TOKENS = {"not sure / n/a", "not sure/n/a", "n/a", "na", "nan", ""}


def normalize(s):
    """Map en-dash/em-dash to ASCII '-' and trim whitespace."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    s = str(s)
    for ch in ("–", "—", "−"):  # en-dash, em-dash, minus
        s = s.replace(ch, "-")
    s = s.replace("‘", "'").replace("’", "'")
    return s.strip()


def is_na_token(v):
    if v is None:
        return True
    return normalize(v).lower() in NA_TOKENS


def find_col(df, *needles, exclude=()):
    """Find a column whose normalized name contains all `needles` and none of
    `exclude` (case-insensitive). Returns the original column name."""
    needles_l = [n.lower() for n in needles]
    excl_l = [e.lower() for e in exclude]
    for c in df.columns:
        cl = normalize(c).lower()
        if all(n in cl for n in needles_l) and not any(e in cl for e in excl_l):
            return c
    raise KeyError(f"Could not find column with needles={needles}, exclude={exclude}")


def role_group(role):
    role_n = normalize(role) or ""
    return "Developer" if role_n.lower().startswith("software engineer") else "NonDev"


def median_bucket(values, order):
    """Return the median bucket label (using ordinal ranks). N/A values dropped."""
    ranks = []
    labels = []
    for v in values:
        v_n = normalize(v)
        if v_n is None or is_na_token(v_n):
            continue
        # find best matching bucket index
        idx = bucket_index(v_n, order)
        if idx is None:
            continue
        ranks.append(idx)
        labels.append(order[idx])
    if not ranks:
        return None
    ranks.sort()
    mid = ranks[len(ranks) // 2]  # lower-median for even n is fine for small samples
    return order[mid]


def bucket_index(value, order):
    v_n = normalize(value)
    if v_n is None:
        return None
    v_low = v_n.lower()
    for i, b in enumerate(order):
        if v_low == b.lower():
            return i
    # fuzzy: strip non-digits/letters and compare
    def squish(x):
        return "".join(ch for ch in x.lower() if ch.isalnum())
    sq = squish(v_low)
    for i, b in enumerate(order):
        if squish(b) == sq:
            return i
    return None


def pct_improved(before_vals, after_vals, order):
    n = 0
    improved = 0
    for b, a in zip(before_vals, after_vals):
        bi = bucket_index(b, order) if not is_na_token(b) else None
        ai = bucket_index(a, order) if not is_na_token(a) else None
        if bi is None or ai is None:
            continue
        n += 1
        if ai < bi:
            improved += 1
    if n == 0:
        return None, 0
    return improved / n, n


def pct_in_set(values, target_labels):
    targets_l = {t.lower() for t in target_labels}
    n = 0
    hit = 0
    for v in values:
        if is_na_token(v):
            continue
        n += 1
        if normalize(v).lower() in targets_l:
            hit += 1
    if n == 0:
        return None, 0
    return hit / n, n


def fmt_pct(p):
    if p is None:
        return "n/a"
    return f"{round(p * 100):d}%"


def fmt_med(v):
    return v if v is not None else "n/a"


def main():
    xlsx_files = sorted(glob.glob(str(REPO_ROOT / "*.xlsx")), key=os.path.getmtime, reverse=True)
    if not xlsx_files:
        print("ERROR: no XLSX file found in repo root", file=sys.stderr)
        sys.exit(1)
    src = xlsx_files[0]
    print(f"[load] {os.path.basename(src)}")

    df = pd.read_excel(src)

    # Resolve columns of interest by content keywords.
    col_role = find_col(df, "role")
    col_usage = find_col(df, "how often", "afci")
    col_reset_before = find_col(df, "back on architectural", "before afci")
    col_reset_after = find_col(df, "back on architectural", "after afci")

    # Symptom columns: BEFORE = first occurrence; AFTER = column ending in "2"
    col_sym_layer_b = find_col(df, "wrong layer", exclude=("2",))
    col_sym_layer_a = find_col(df, "wrong layer", "2")
    col_sym_dto_b = find_col(df, "duplicated dtos", exclude=("2",))
    col_sym_dto_a = find_col(df, "duplicated dtos", "2")
    col_sym_log_b = find_col(df, "missing correlationid", exclude=("2",))
    col_sym_log_a = find_col(df, "missing correlationid", "2")
    col_sym_port_b = find_col(df, "interfaces/ports", exclude=("2",))
    col_sym_port_a = find_col(df, "interfaces/ports", "2")

    col_iter_before = find_col(df, "review iterations", "before afci")
    col_iter_after = find_col(df, "review iterations", "after afci")
    col_mad_read = find_col(df, "reading mad")

    # Build a sanitized working frame (dropping PII / open-ended).
    work = pd.DataFrame({
        "role": df[col_role].map(normalize),
        "role_group": df[col_role].map(role_group),
        "usage": df[col_usage].map(normalize),
        "reset_before": df[col_reset_before].map(normalize),
        "reset_after": df[col_reset_after].map(normalize),
        "sym_layer_b": df[col_sym_layer_b].map(normalize),
        "sym_layer_a": df[col_sym_layer_a].map(normalize),
        "sym_dto_b": df[col_sym_dto_b].map(normalize),
        "sym_dto_a": df[col_sym_dto_a].map(normalize),
        "sym_log_b": df[col_sym_log_b].map(normalize),
        "sym_log_a": df[col_sym_log_a].map(normalize),
        "sym_port_b": df[col_sym_port_b].map(normalize),
        "sym_port_a": df[col_sym_port_a].map(normalize),
        "iter_before": pd.to_numeric(df[col_iter_before], errors="coerce"),
        "iter_after": pd.to_numeric(df[col_iter_after], errors="coerce"),
        "mad_read": df[col_mad_read].map(normalize),
    })

    symptoms = [
        ("wrong_layer", "sym_layer_b", "sym_layer_a"),
        ("duplicate_dtos", "sym_dto_b", "sym_dto_a"),
        ("missing_logging", "sym_log_b", "sym_log_a"),
        ("ports_inconsistent", "sym_port_b", "sym_port_a"),
    ]

    # MAD-reading buckets to count (canonicalize to the first matching label).
    mad_canonical = ["< 2 minutes", "2-5 minutes", "5-10 minutes", "10-20 minutes", "20+ minutes"]

    def canonical_mad(v):
        if is_na_token(v):
            return "Not sure / N/A"
        idx = bucket_index(v, MAD_READ_ORDER)
        if idx is None:
            return "Other"
        # collapse "20 minutes" / "20+ minutes" / "> 20 minutes" -> "20+ minutes"
        label = MAD_READ_ORDER[idx]
        if label in {"20 minutes", "20+ minutes", "> 20 minutes"}:
            return "20+ minutes"
        return label

    work["mad_read_canon"] = work["mad_read"].map(canonical_mad)

    def summarize(group_df, group_label):
        n = len(group_df)
        usage_l = group_df["usage"].dropna().map(lambda s: normalize(s).lower()).tolist()
        pct_daily_weekly = sum(1 for u in usage_l if u in {"daily", "weekly"}) / n if n else None

        med_before = median_bucket(group_df["reset_before"].tolist(), RESET_ORDER)
        med_after = median_bucket(group_df["reset_after"].tolist(), RESET_ORDER)
        p_imp_reset, _ = pct_improved(
            group_df["reset_before"].tolist(),
            group_df["reset_after"].tolist(),
            RESET_ORDER,
        )

        # symptoms: % Sometimes/Often before and after
        sym_targets = {"Sometimes (weekly)", "Often (daily)"}
        sym_summary = {}
        for key, b_col, a_col in symptoms:
            pb, _ = pct_in_set(group_df[b_col].tolist(), sym_targets)
            pa, _ = pct_in_set(group_df[a_col].tolist(), sym_targets)
            sym_summary[key] = (pb, pa)

        iter_before_vals = group_df["iter_before"].dropna().tolist()
        iter_after_vals = group_df["iter_after"].dropna().tolist()
        med_iter_b = median(iter_before_vals) if iter_before_vals else None
        med_iter_a = median(iter_after_vals) if iter_after_vals else None

        mad_counts = {b: int((group_df["mad_read_canon"] == b).sum()) for b in mad_canonical}
        mad_counts["Not sure / N/A"] = int((group_df["mad_read_canon"] == "Not sure / N/A").sum())

        row = {
            "group": group_label,
            "n": n,
            "pct_daily_weekly": fmt_pct(pct_daily_weekly),
            "median_reset_before": fmt_med(med_before),
            "median_reset_after": fmt_med(med_after),
            "pct_improved_reset": fmt_pct(p_imp_reset),
            "median_review_iter_before": "" if med_iter_b is None else f"{med_iter_b:g}",
            "median_review_iter_after": "" if med_iter_a is None else f"{med_iter_a:g}",
        }
        for key, _, _ in symptoms:
            pb, pa = sym_summary[key]
            row[f"pct_freq_{key}_before"] = fmt_pct(pb)
            row[f"pct_freq_{key}_after"] = fmt_pct(pa)
        for b in mad_canonical + ["Not sure / N/A"]:
            safe = b.replace(" ", "_").replace("<", "lt").replace(">", "gt").replace("/", "_")
            row[f"mad_read_n_{safe}"] = mad_counts[b]
        return row

    # Overall
    overall = summarize(work, "Overall")
    by_role_rows = [summarize(work[work["role_group"] == g], g) for g in ["Developer", "NonDev"]]

    # Write CSVs
    OUT_CSV_DIR.mkdir(parents=True, exist_ok=True)
    overall_df = pd.DataFrame([overall])
    by_role_df = pd.DataFrame(by_role_rows)
    overall_path = OUT_CSV_DIR / "survey_summary_overall_v1.csv"
    by_role_path = OUT_CSV_DIR / "survey_summary_by_role_v1.csv"
    overall_df.to_csv(overall_path, index=False)
    by_role_df.to_csv(by_role_path, index=False)
    print(f"[csv] {overall_path}")
    print(f"[csv] {by_role_path}")

    # LaTeX tables
    OUT_TEX_DIR.mkdir(parents=True, exist_ok=True)

    def tex_escape(s):
        s = str(s)
        return s.replace("%", r"\%").replace("&", r"\&").replace("_", r"\_")

    def write_overall_tex(row, path):
        lines = []
        lines.append(r"\begin{table}[t]")
        lines.append(r"\centering")
        lines.append(r"\small")
        lines.append(r"\caption{Survey summary (overall, n=" + str(row["n"]) +
                     r"). Descriptive only; no statistical claims due to small n.}")
        lines.append(r"\label{tab:survey-overall-v1}")
        lines.append(r"\begin{tabular}{lr}")
        lines.append(r"\toprule")
        lines.append(r"Metric & Value \\")
        lines.append(r"\midrule")
        rows = [
            ("Respondents (n)", str(row["n"])),
            ("Daily/Weekly usage", row["pct_daily_weekly"]),
            ("Median reset time, BEFORE", row["median_reset_before"]),
            ("Median reset time, AFTER", row["median_reset_after"]),
            ("Improved reset time (AFTER faster)", row["pct_improved_reset"]),
            ("Median review iters, BEFORE", row["median_review_iter_before"]),
            ("Median review iters, AFTER", row["median_review_iter_after"]),
            ("Sometimes/Often: wrong layer, BEFORE", row["pct_freq_wrong_layer_before"]),
            ("Sometimes/Often: wrong layer, AFTER", row["pct_freq_wrong_layer_after"]),
            ("Sometimes/Often: duplicate DTOs, BEFORE", row["pct_freq_duplicate_dtos_before"]),
            ("Sometimes/Often: duplicate DTOs, AFTER", row["pct_freq_duplicate_dtos_after"]),
            ("Sometimes/Often: missing logging, BEFORE", row["pct_freq_missing_logging_before"]),
            ("Sometimes/Often: missing logging, AFTER", row["pct_freq_missing_logging_after"]),
            ("Sometimes/Often: ports inconsistent, BEFORE", row["pct_freq_ports_inconsistent_before"]),
            ("Sometimes/Often: ports inconsistent, AFTER", row["pct_freq_ports_inconsistent_after"]),
        ]
        for k, v in rows:
            lines.append(f"{tex_escape(k)} & {tex_escape(v)} \\\\")
        lines.append(r"\bottomrule")
        lines.append(r"\end{tabular}")
        lines.append(r"\end{table}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def write_by_role_tex(rows, path):
        dev = next(r for r in rows if r["group"] == "Developer")
        nond = next(r for r in rows if r["group"] == "NonDev")
        lines = []
        lines.append(r"\begin{table}[t]")
        lines.append(r"\centering")
        lines.append(r"\small")
        lines.append(r"\caption{Survey summary by role group (Developer vs.\ NonDev). " +
                     r"Descriptive only; small-n samples (n$_\text{Dev}$=" + str(dev["n"]) +
                     r", n$_\text{NonDev}$=" + str(nond["n"]) + r").}")
        lines.append(r"\label{tab:survey-by-role-v1}")
        lines.append(r"\begin{tabular}{lrr}")
        lines.append(r"\toprule")
        lines.append(r"Metric & Developer & NonDev \\")
        lines.append(r"\midrule")
        items = [
            ("Respondents (n)", "n", "n"),
            ("Daily/Weekly usage", "pct_daily_weekly", "pct_daily_weekly"),
            ("Median reset, BEFORE", "median_reset_before", "median_reset_before"),
            ("Median reset, AFTER", "median_reset_after", "median_reset_after"),
            ("\\% improved reset", "pct_improved_reset", "pct_improved_reset"),
            ("Median review iters, BEFORE", "median_review_iter_before", "median_review_iter_before"),
            ("Median review iters, AFTER", "median_review_iter_after", "median_review_iter_after"),
            ("S/O: wrong layer, BEFORE", "pct_freq_wrong_layer_before", "pct_freq_wrong_layer_before"),
            ("S/O: wrong layer, AFTER", "pct_freq_wrong_layer_after", "pct_freq_wrong_layer_after"),
            ("S/O: duplicate DTOs, BEFORE", "pct_freq_duplicate_dtos_before", "pct_freq_duplicate_dtos_before"),
            ("S/O: duplicate DTOs, AFTER", "pct_freq_duplicate_dtos_after", "pct_freq_duplicate_dtos_after"),
            ("S/O: missing logging, BEFORE", "pct_freq_missing_logging_before", "pct_freq_missing_logging_before"),
            ("S/O: missing logging, AFTER", "pct_freq_missing_logging_after", "pct_freq_missing_logging_after"),
            ("S/O: ports inconsistent, BEFORE", "pct_freq_ports_inconsistent_before", "pct_freq_ports_inconsistent_before"),
            ("S/O: ports inconsistent, AFTER", "pct_freq_ports_inconsistent_after", "pct_freq_ports_inconsistent_after"),
        ]
        for label, k_dev, k_non in items:
            lines.append(f"{label} & {tex_escape(dev[k_dev])} & {tex_escape(nond[k_non])} \\\\")
        lines.append(r"\bottomrule")
        lines.append(r"\end{tabular}")
        lines.append(r"\end{table}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    overall_tex = OUT_TEX_DIR / "table_survey_summary_overall_v1.tex"
    by_role_tex = OUT_TEX_DIR / "table_survey_by_role_v1.tex"
    write_overall_tex(overall, overall_tex)
    write_by_role_tex(by_role_rows, by_role_tex)
    print(f"[tex] {overall_tex}")
    print(f"[tex] {by_role_tex}")

    # Figure 4: BEFORE vs AFTER reset time per role-group as grouped bar chart.
    OUT_FIG_DIR.mkdir(parents=True, exist_ok=True)

    # For a simple visual we map each bucket to its midpoint minutes and plot the
    # mean-of-midpoints per group as bars. Caption notes this is descriptive.
    midpoint_minutes = {
        "< 5 minutes": 2.5,
        "5-15 minutes": 10.0,
        "15-30 minutes": 22.5,
        "30-60 minutes": 45.0,
        "60 minutes": 75.0,
        "> 60 minutes": 75.0,
    }

    def mean_minutes(values):
        xs = []
        for v in values:
            if is_na_token(v):
                continue
            v_n = normalize(v)
            for k, m in midpoint_minutes.items():
                if k.lower() == v_n.lower():
                    xs.append(m)
                    break
        return sum(xs) / len(xs) if xs else 0.0

    groups = ["Developer", "NonDev"]
    before_means = []
    after_means = []
    for g in groups:
        gdf = work[work["role_group"] == g]
        before_means.append(mean_minutes(gdf["reset_before"].tolist()))
        after_means.append(mean_minutes(gdf["reset_after"].tolist()))

    fig, ax = plt.subplots(figsize=(5.0, 3.2))
    x = list(range(len(groups)))
    width = 0.35
    ax.bar([i - width / 2 for i in x], before_means, width, label="BEFORE AFCI")
    ax.bar([i + width / 2 for i in x], after_means, width, label="AFTER AFCI")
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylabel("Mean reset time (min, bucket midpoints)")
    ax.set_title("Time-to-reorient after reset/handoff (descriptive, small n)")
    ax.legend()
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig_path = OUT_FIG_DIR / "Figure4_reset_time_by_role_v1.pdf"
    fig.savefig(fig_path)
    plt.close(fig)
    print(f"[fig] {fig_path}")

    # Console summary
    print()
    n_total = len(work)
    n_dev = int((work["role_group"] == "Developer").sum())
    n_non = int((work["role_group"] == "NonDev").sum())
    print(f"N total = {n_total}")
    print(f"N Developer = {n_dev}")
    print(f"N NonDev = {n_non}")
    for r in by_role_rows:
        print(
            f"[{r['group']}] median reset BEFORE = {r['median_reset_before']}, "
            f"AFTER = {r['median_reset_after']}, "
            f"% improved = {r['pct_improved_reset']}"
        )
    print()
    print("Outputs:")
    print(f"  {overall_path}")
    print(f"  {by_role_path}")
    print(f"  {overall_tex}")
    print(f"  {by_role_tex}")
    print(f"  {fig_path}")


if __name__ == "__main__":
    main()
