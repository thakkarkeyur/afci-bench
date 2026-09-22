"""Build the AFCI-Bench professor results delivery package.

REPORTING / EXPORT ONLY. This script executes no benchmark observation, invokes
no model, and reads nothing outside ``study-results/``. Every figure it emits is
recomputed from ``AFCI_MASTER_RUN_RESULTS.csv`` (the run/attempt rows) and then
checked against the frozen per-experiment analysis artifacts; the check results
are published in the workbook's ``20_RECOMPUTATION_AUDIT`` sheet rather than
asserted in prose.

Two rules are enforced throughout:

  * a missing metric is a blank, never a zero;
  * every aggregate is published beside its coverage count.

Run with:  python study-results/professor-delivery/_build/build_professor_delivery.py
"""
import csv
import datetime
import json
import statistics
import subprocess
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve()
SR = HERE.parents[2]                     # study-results/
OUT = HERE.parents[1]                    # study-results/professor-delivery/
REPO = SR.parent                         # repository root

COMPILED = "2026-09-23"

#: Text output is written with LF explicitly. The repository pins `eol=lf` in
#: .gitattributes, so writing CRLF here would leave the working tree differing
#: from the committed blob and make every rebuild look like a change.
LF = "\n"

# --------------------------------------------------------------------------- #
# loading helpers
# --------------------------------------------------------------------------- #


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def blank(v):
    return v is None or v == ""


def num(v):
    """float, or None. A blank NEVER becomes 0."""
    if blank(v):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def intn(v):
    f = num(v)
    return None if f is None else int(round(f))


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def r4(v):
    return None if v is None else round(v, 4)


RUNS = read_csv(SR / "AFCI_MASTER_RUN_RESULTS.csv")
REGISTRY = read_csv(SR / "AFCI_MASTER_EXPERIMENT_REGISTRY.csv")

A2 = SR / "05_efficiency_attempt_2_completed"
LM = SR / "06_lower_model_pilot_completed"
A2_PAIRS = read_csv(A2 / "attempt2_primary_pairs.csv")
A2_RATIOS = read_csv(A2 / "attempt2_endpoint_ratios.csv")
A2_COST = read_csv(A2 / "attempt2_provider_cost.csv")
A2_RESET = read_csv(A2 / "attempt2_reset_overhead.csv")
A2_CLAUSES = read_csv(A2 / "attempt2_decision_clauses.csv")
A2_RAW = read_csv(A2 / "attempt2_runs_raw_metrics.csv")
A2_REPORT = json.loads((A2 / "efficiency_pilot_frozen_analysis_report.json").read_text(encoding="utf-8"))

# Backstage attempt 2. Prefixed BS2, never A2: "A2" in this file means the
# EFFICIENCY attempt 2, and both directories happen to name their files
# attempt2_*.
BS2 = SR / "08_backstage_pilot_attempt_2_completed"
BS2_ARCH = read_csv(BS2 / "attempt2_architecture_summary.csv")
BS2_FUNC = read_csv(BS2 / "attempt2_functional_summary.csv")
BS2_RATIOS = read_csv(BS2 / "attempt2_endpoint_ratios.csv")
BS2_PAIRS = read_csv(BS2 / "attempt2_primary_pairs.csv")
BS2_CLAUSES = read_csv(BS2 / "attempt2_decision_clauses.csv")
BS2_RAW = read_csv(BS2 / "attempt2_runs_raw_metrics.csv")

LM_PAIRS = read_csv(LM / "lower_model_primary_pairs.csv")
LM_RATIOS = read_csv(LM / "lower_model_endpoint_ratios.csv")
LM_ARCH = read_csv(LM / "lower_model_architecture_summary.csv")
LM_CLAUSES = read_csv(LM / "lower_model_decision_clauses.csv")
LM_RAW = read_csv(LM / "lower_model_runs_raw_metrics.csv")
LM_REPORT = json.loads((LM / "lower_model_pilot_frozen_analysis_report.json").read_text(encoding="utf-8"))

V1_HEADLINE = read_csv(SR / "01_v1_original_study" / "v1_headline_recomputed.csv")
V1_TASKWISE = read_csv(SR / "01_v1_original_study" / "v1_taskwise_churn_recomputed.csv")
V1_COMPLETENESS = read_csv(SR / "01_v1_original_study" / "completeness_summary_v1.csv")
PT08 = read_csv(SR / "02_pt08_diagnostic" / "pt08_diagnostic_runs.csv")
QUAL_RUNS = read_csv(SR / "03_pt09_pt10_qualification" / "qualification_runs.csv")
QUAL_CLASS = read_csv(SR / "03_pt09_pt10_qualification" / "qualification_classification.csv")

AUDIT = []


def check(name, expected, observed, tol=5e-5):
    if isinstance(expected, float) and isinstance(observed, float):
        ok = abs(expected - observed) <= tol
    else:
        ok = expected == observed
    AUDIT.append({"check": name, "frozen_artifact_value": expected,
                  "recomputed_from_run_rows": observed,
                  "status": "MATCH" if ok else "MISMATCH"})
    return ok


# --------------------------------------------------------------------------- #
# 1. run inventory
# --------------------------------------------------------------------------- #

DIAGNOSTIC_PURPOSES = {"PT08_DIFFICULTY_DIAGNOSTIC", "INSTRUMENT_QUALIFICATION_DIAGNOSTIC"}
INFRA_STATUSES = {"INFRASTRUCTURE_INVALID_NON_OBSERVATION",
                  "DAMAGED_GOVERNED_RECORD_OVERWRITTEN",
                  "DAMAGED_POST_DELIVERY_COLLIDING_OBSERVATION"}


def tally(rows, key, blank_label="(blank)"):
    out = {}
    for r in rows:
        k = r.get(key) or blank_label
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


INV = {
    "total_rows": len(RUNS),
    "unique_run_ids": len({r["run_id"] for r in RUNS if not blank(r["run_id"])}),
    "completed": sum(1 for r in RUNS if r["run_status"] == "COMPLETE"),
    "functional_valid": sum(1 for r in RUNS if r["functional_valid"] == "true"),
    "functional_invalid": sum(1 for r in RUNS if r["functional_valid"] == "false"),
    "functional_not_captured": sum(1 for r in RUNS if blank(r["functional_valid"])),
    "eligible": sum(1 for r in RUNS if r["eligible_for_analysis"] == "true"),
    "excluded": sum(1 for r in RUNS if r["eligible_for_analysis"] != "true"),
    "diagnostic_qualification": sum(1 for r in RUNS if r["run_purpose"] in DIAGNOSTIC_PURPOSES),
    "infra_invalid_or_damaged": sum(1 for r in RUNS if r["run_status"] in INFRA_STATUSES),
    "refused": sum(1 for r in RUNS if r["run_status"] == "REFUSED"),
    "token_coverage": sum(1 for r in RUNS if not blank(r["total_input_tokens"])),
    "output_token_coverage": sum(1 for r in RUNS if not blank(r["total_output_tokens"])),
    "cost_coverage": sum(1 for r in RUNS if not blank(r["provider_cost_usd"])),
    "architecture_coverage": sum(1 for r in RUNS if not blank(r["architecture_applicable"])),
    "wall_coverage": sum(1 for r in RUNS if not blank(r["model_wall_seconds"])),
    "tool_coverage": sum(1 for r in RUNS if not blank(r["total_tool_calls"])),
    "loc_coverage": sum(1 for r in RUNS if not blank(r["lines_added"])),
    "by_experiment": tally(RUNS, "experiment_id"),
    "by_model": tally(RUNS, "model"),
    "by_condition": tally(RUNS, "condition"),
    "by_reset_state": tally(RUNS, "reset_state"),
    "by_run_status": tally(RUNS, "run_status"),
    "by_run_purpose": tally(RUNS, "run_purpose"),
    "by_task": tally(RUNS, "task"),
}

PER_EXPERIMENT = []
for exp in INV["by_experiment"]:
    rs = [r for r in RUNS if r["experiment_id"] == exp]
    PER_EXPERIMENT.append({
        "experiment_id": exp, "rows": len(rs),
        "completed": sum(1 for r in rs if r["run_status"] == "COMPLETE"),
        "functional_valid": sum(1 for r in rs if r["functional_valid"] == "true"),
        "functional_invalid": sum(1 for r in rs if r["functional_valid"] == "false"),
        "functional_not_captured": sum(1 for r in rs if blank(r["functional_valid"])),
        "eligible": sum(1 for r in rs if r["eligible_for_analysis"] == "true"),
        "excluded": sum(1 for r in rs if r["eligible_for_analysis"] != "true"),
        "token_coverage": sum(1 for r in rs if not blank(r["total_input_tokens"])),
        "output_token_coverage": sum(1 for r in rs if not blank(r["total_output_tokens"])),
        "cost_coverage": sum(1 for r in rs if not blank(r["provider_cost_usd"])),
        "wall_coverage": sum(1 for r in rs if not blank(r["model_wall_seconds"])),
        "tool_coverage": sum(1 for r in rs if not blank(r["total_tool_calls"])),
        "architecture_coverage": sum(1 for r in rs if not blank(r["architecture_applicable"])),
        "loc_coverage": sum(1 for r in rs if not blank(r["lines_added"])),
    })

check("master run/attempt rows", 146, INV["total_rows"])
check("rows eligible for any analysis", 56, INV["eligible"])

# --------------------------------------------------------------------------- #
# 2. paired endpoints
# --------------------------------------------------------------------------- #

METRIC_FN = {
    "TOTAL_INPUT_TOKENS": lambda r: num(r["total_input_tokens"]),
    "TOTAL_OUTPUT_TOKENS": lambda r: num(r["total_output_tokens"]),
    "PROVIDER_COST_USD": lambda r: num(r["provider_cost_usd"]),
    "MODEL_WALL_SECONDS": lambda r: num(r["model_wall_seconds"]),
    "EXPLORATION_CALLS": lambda r: num(r["exploration_calls"]),
    "TOTAL_TOOL_CALLS": lambda r: num(r["total_tool_calls"]),
    "UNIQUE_FILES_READ": lambda r: num(r["unique_files_read"]),
    "EDIT_AND_WRITE_CALLS": lambda r: (
        None if blank(r["edit_calls"]) and blank(r["write_calls"])
        else (num(r["edit_calls"]) or 0) + (num(r["write_calls"]) or 0)),
    "READ_CALLS": lambda r: num(r["read_calls"]),
    "GREP_CALLS": lambda r: num(r["grep_calls"]),
    "GLOB_CALLS": lambda r: num(r["glob_calls"]),
    "BASH_CALLS": lambda r: num(r["bash_calls"]),
    "EDIT_CALLS": lambda r: num(r["edit_calls"]),
    "WRITE_CALLS": lambda r: num(r["write_calls"]),
    "UNIQUE_FILES_MODIFIED": lambda r: num(r["unique_files_modified"]),
    "FILES_REEDITED": lambda r: num(r["files_reedited"]),
    "CI_COMMAND_RUNS": lambda r: num(r["ci_command_runs"]),
    "TEST_COMMAND_RUNS": lambda r: num(r["test_command_runs"]),
    "LINES_ADDED": lambda r: num(r["lines_added"]),
    "LINES_REMOVED": lambda r: num(r["lines_removed"]),
    "NET_LINES": lambda r: num(r["net_lines"]),
}


def build_blocks(rows, with_reset):
    """A block is one task x reset-state x repetition cell. It is paired-eligible
    only when it holds exactly one C1 and one C4 observation and BOTH are
    functionally valid -- the frozen pairing rule, applied here to the run rows."""
    groups = {}
    for r in rows:
        key = (r["task"], r["reset_state"] or "", r["repetition"]) if with_reset else (r["task"], r["repetition"])
        groups.setdefault(key, {}).setdefault(r["condition"], []).append(r)
    out = []
    for key, arms in sorted(groups.items()):
        c1, c4 = arms.get("C1", []), arms.get("C4", [])
        if len(c1) != 1 or len(c4) != 1:
            reason = "the block does not hold exactly one C1 and one C4 observation"
        elif c1[0]["functional_valid"] != "true" and c4[0]["functional_valid"] != "true":
            reason = "both arms are functionally invalid"
        elif c1[0]["functional_valid"] != "true":
            reason = "C1 is not functionally valid, so no C4/C1 pair can be formed"
        elif c4[0]["functional_valid"] != "true":
            reason = "C4 is not functionally valid, so no C4/C1 pair can be formed"
        else:
            reason = None
        out.append({"task": key[0], "reset_state": key[1] if with_reset else "NON_RESET",
                    "repetition": key[-1], "C1": c1[0] if len(c1) == 1 else None,
                    "C4": c4[0] if len(c4) == 1 else None,
                    "eligible": reason is None, "ineligible_reason": reason})
    return out


def endpoint(blocks, metric, restrict_reset=None):
    fn = METRIC_FN[metric]
    pairs, undefined = [], []
    for b in blocks:
        if not b["eligible"] or (restrict_reset and b["reset_state"] != restrict_reset):
            continue
        v1, v4 = fn(b["C1"]), fn(b["C4"])
        rec = {"task": b["task"], "reset_state": b["reset_state"], "repetition": b["repetition"], "C1": v1, "C4": v4}
        if v1 is None or v4 is None or v1 == 0:
            undefined.append(rec)
        else:
            rec["ratio"] = v4 / v1
            pairs.append(rec)
    ratios = [p["ratio"] for p in pairs]
    tasks = sorted({p["task"] for p in pairs})
    return {"endpoint": metric, "n": len(pairs), "median": med(ratios),
            "c4_lower_count": sum(1 for r in ratios if r < 1),
            "c4_lower_fraction": (sum(1 for r in ratios if r < 1) / len(ratios)) if ratios else None,
            "task_medians": {t: med([p["ratio"] for p in pairs if p["task"] == t]) for t in tasks},
            "C1_total": sum(p["C1"] for p in pairs) if pairs else None,
            "C4_total": sum(p["C4"] for p in pairs) if pairs else None,
            "C1_median": med([p["C1"] for p in pairs]),
            "C4_median": med([p["C4"] for p in pairs]),
            "undefined_pairs": len(undefined), "pairs": pairs}


A2_ROWS = [r for r in RUNS if r["experiment_id"] == "V2_EFF_ATTEMPT2"]
LM_ROWS = [r for r in RUNS if r["experiment_id"] == "V2_LOWER_MODEL_PILOT"]
A2_BLOCKS = build_blocks(A2_ROWS, with_reset=True)
LM_BLOCKS = build_blocks(LM_ROWS, with_reset=False)

check("Sonnet blocks observed", A2_REPORT["blocks"]["observed"], len(A2_BLOCKS))
check("Sonnet paired-eligible blocks", A2_REPORT["blocks"]["eligible"], sum(1 for b in A2_BLOCKS if b["eligible"]))
check("Haiku blocks observed", LM_REPORT["block_count"], len(LM_BLOCKS))
check("Haiku paired-eligible blocks", LM_REPORT["efficiency"]["eligible_pairs"], sum(1 for b in LM_BLOCKS if b["eligible"]))

SON = {m: endpoint(A2_BLOCKS, m) for m in METRIC_FN}
SON_NR = {m: endpoint(A2_BLOCKS, m, "NON_RESET") for m in METRIC_FN}
SON_RS = {m: endpoint(A2_BLOCKS, m, "RESET") for m in METRIC_FN}
HAI = {m: endpoint(LM_BLOCKS, m) for m in METRIC_FN}

for row in A2_RATIOS:
    name = row["endpoint"].replace(" (PRIMARY)", "")
    if row["median_C4_over_C1"] == "NOT CAPTURED":
        check(f"Sonnet {name} paired n", 0, SON[name]["n"])
        continue
    src = SON_NR if row["non_reset_only"] == "true" else SON
    check(f"Sonnet {name} median C4/C1", round(float(row["median_C4_over_C1"]), 4), r4(src[name]["median"]))
    check(f"Sonnet {name} paired n", int(row["paired_n"]), src[name]["n"])
    check(f"Sonnet {name} C4-lower count", int(row["c4_lower_count"]), src[name]["c4_lower_count"])

for row in LM_RATIOS:
    name = row["endpoint"]
    check(f"Haiku {name} median C4/C1", round(float(row["median_c4_over_c1"]), 4), r4(HAI[name]["median"]))
    check(f"Haiku {name} paired n", int(row["n_pairs"]), HAI[name]["n"])
    check(f"Haiku {name} C4-lower count", int(row["c4_lower_count"]), HAI[name]["c4_lower_count"])

check("Sonnet NON_RESET token median (cross-model record)",
      LM_REPORT["sonnet_comparison"]["within_sonnet"]["median_token_ratio"], r4(SON_NR["TOTAL_INPUT_TOKENS"]["median"]))
check("Sonnet NON_RESET token paired n",
      LM_REPORT["sonnet_comparison"]["within_sonnet"]["paired_n"], SON_NR["TOTAL_INPUT_TOKENS"]["n"])
check("Sonnet NON_RESET provider-cost median", round(float(A2_COST[-1]["ratio_C4_over_C1"]), 4),
      r4(SON_NR["PROVIDER_COST_USD"]["median"]))
check("Haiku provider-cost median", r4(med([float(r["cost_ratio"]) for r in LM_PAIRS])),
      r4(HAI["PROVIDER_COST_USD"]["median"]))

for label, rows, rep in (("Sonnet", A2_ROWS, A2_REPORT["functional_valid_counts"]),
                         ("Haiku", LM_ROWS, {"C1": LM_REPORT["functional"]["C1_valid"],
                                             "C4": LM_REPORT["functional"]["C4_valid"]})):
    for cond in ("C1", "C4"):
        check(f"{label} {cond} functionally-valid runs", rep[cond],
              sum(1 for r in rows if r["condition"] == cond and r["functional_valid"] == "true"))

for cond in ("C1", "C4"):
    rs = [r for r in LM_ROWS if r["condition"] == cond]
    check(f"Haiku {cond} applicable opportunities",
          LM_REPORT["architecture"]["overall"][cond]["applicable_opportunities"],
          sum(intn(r["architecture_applicable"]) or 0 for r in rs))
    check(f"Haiku {cond} violated opportunities",
          LM_REPORT["architecture"]["overall"][cond]["violated_opportunities"],
          sum(intn(r["architecture_violated"]) or 0 for r in rs))

# --------------------------------------------------------------------------- #
# 3. cost + token coverage
# --------------------------------------------------------------------------- #


def cov_block(rows, label, field):
    have = [r for r in rows if not blank(r[field])]
    return {"scope": label, "runs": len(rows), "runs_with_metric": len(have),
            "runs_without_metric": len(rows) - len(have),
            "captured_total": sum(num(r[field]) for r in have) if have else None,
            "median_per_run": med([num(r[field]) for r in have])}


COST_COVERAGE = [
    cov_block(A2_ROWS, "Sonnet Attempt 2 | all rows", "provider_cost_usd"),
    cov_block([r for r in A2_ROWS if r["reset_state"] == "NON_RESET"], "Sonnet Attempt 2 | NON_RESET", "provider_cost_usd"),
    cov_block([r for r in A2_ROWS if r["reset_state"] == "RESET"], "Sonnet Attempt 2 | RESET", "provider_cost_usd"),
    cov_block(LM_ROWS, "Haiku lower-model pilot | all rows (NON_RESET by design)", "provider_cost_usd"),
]
COST_ROWS = [r for r in RUNS if not blank(r["provider_cost_usd"])]
TOTAL_CAPTURED_COST = sum(num(r["provider_cost_usd"]) for r in COST_ROWS)

check("Haiku captured provider cost, all 18 runs", 3.8007, r4(sum(num(r["provider_cost_usd"]) for r in LM_ROWS)))
check("Haiku C1 paired-block cost total", 1.3862, r4(sum(p["C1"] for p in HAI["PROVIDER_COST_USD"]["pairs"])))
check("Haiku C4 paired-block cost total", 2.0068, r4(sum(p["C4"] for p in HAI["PROVIDER_COST_USD"]["pairs"])))

TOKEN_IDENTITY_FAIL = []
for r in RUNS:
    t = num(r["total_input_tokens"])
    if t is None:
        continue
    parts = [num(r["input_tokens"]), num(r["cache_creation_input_tokens"]), num(r["cache_read_input_tokens"])]
    if None in parts or abs(t - sum(parts)) > 0.5:
        TOKEN_IDENTITY_FAIL.append(r["run_id"])
check("TOTAL_INPUT_TOKENS == input + cache_creation + cache_read on every token-bearing row",
      0, len(TOKEN_IDENTITY_FAIL))

TOKEN_COVERAGE = []
for label, rows in (("Sonnet Attempt 2", A2_ROWS), ("Haiku lower-model pilot", LM_ROWS)):
    for cond in ("C1", "C4"):
        for scope, sel in (("all", lambda r: True),
                           ("NON_RESET", lambda r: r["reset_state"] == "NON_RESET"),
                           ("RESET", lambda r: r["reset_state"] == "RESET")):
            sub = [r for r in rows if r["condition"] == cond and sel(r)]
            if sub:
                TOKEN_COVERAGE.append(cov_block(sub, f"{label} | {cond} | {scope}", "total_input_tokens"))

# --------------------------------------------------------------------------- #
# 4. architecture
# --------------------------------------------------------------------------- #

ARCH = []
for exp, task, rows, cls in (
    ("PT08 diagnostic", "PT08", [r for r in RUNS if r["experiment_id"] == "V2_PT08_DIAGNOSTIC"],
     "FUNCTIONAL CEILING + ARCHITECTURE FLOOR"),
    ("PT09 qualification", "PT09",
     [r for r in RUNS if r["experiment_id"] == "V2_PT09_QUALIFICATION" and r["run_status"] == "COMPLETE"],
     "FAIL / ARCHITECTURE FLOOR"),
    ("PT10 qualification", "PT10", [r for r in RUNS if r["experiment_id"] == "V2_PT10_QUALIFICATION"],
     "REVISE / WEAK PRESSURE"),
):
    ARCH.append({"experiment": exp, "model": "claude-sonnet-5", "task": task, "condition": "C1",
                 "runs": len(rows),
                 "applicable": sum(intn(r["architecture_applicable"]) or 0 for r in rows),
                 "violated": sum(intn(r["architecture_violated"]) or 0 for r in rows),
                 "target_violation_runs": sum(1 for r in rows if (intn(r["architecture_violated"]) or 0) > 0),
                 "classification": cls})
for task in ("ALL", "PT01", "PT04", "PT07"):
    for cond in ("C1", "C4"):
        rows = [r for r in LM_ROWS if r["condition"] == cond and (task == "ALL" or r["task"] == task)]
        ARCH.append({"experiment": "Haiku lower-model pilot", "model": "claude-haiku-4-5-20251001",
                     "task": task, "condition": cond, "runs": len(rows),
                     "applicable": sum(intn(r["architecture_applicable"]) or 0 for r in rows),
                     "violated": sum(intn(r["architecture_violated"]) or 0 for r in rows),
                     "target_violation_runs": sum(1 for r in rows if (intn(r["architecture_violated"]) or 0) > 0),
                     "classification": "ARCHITECTURE FLOOR (both arms at zero)"})

check("PT08 target-violation runs", 0, ARCH[0]["target_violation_runs"])
check("PT09 target-violation runs", 0, ARCH[1]["target_violation_runs"])
check("PT10 target-violation runs", 1, ARCH[2]["target_violation_runs"])

# --------------------------------------------------------------------------- #
# 5. functional matrix
# --------------------------------------------------------------------------- #

FUNCTIONAL = []
for exp, rows in (("V2_EFF_ATTEMPT2", A2_ROWS), ("V2_LOWER_MODEL_PILOT", LM_ROWS)):
    for scope in ("ALL", "PT01", "PT04", "PT07"):
        for cond in ("C1", "C4"):
            sub = [r for r in rows if r["condition"] == cond and (scope == "ALL" or r["task"] == scope)]
            FUNCTIONAL.append({
                "experiment": exp, "scope": scope, "condition": cond, "runs": len(sub),
                "valid": sum(1 for r in sub if r["functional_valid"] == "true"),
                "invalid": sum(1 for r in sub if r["functional_valid"] == "false"),
                "no_verdict": sum(1 for r in sub if blank(r["functional_valid"])),
                "semantic_pass": sum(intn(r["semantic_pass"]) or 0 for r in sub),
                "semantic_fail": sum(intn(r["semantic_fail"]) or 0 for r in sub)})

PAIRED_BLOCKS = {}
for exp, blocks in (("V2_EFF_ATTEMPT2", A2_BLOCKS), ("V2_LOWER_MODEL_PILOT", LM_BLOCKS)):
    for scope in ("ALL", "PT01", "PT04", "PT07"):
        sel = [b for b in blocks if scope == "ALL" or b["task"] == scope]
        PAIRED_BLOCKS[(exp, scope)] = (sum(1 for b in sel if b["eligible"]), len(sel))

# --------------------------------------------------------------------------- #
# 6. rework
# --------------------------------------------------------------------------- #

A2_RAW_BY_ID = {r["run_id"]: r for r in A2_RAW}
LM_RAW_BY_ID = {r["run_id"]: r for r in LM_RAW}


def rework(blocks, raw_by_id, turn_key, fail_key=None, files_changed_key=None):
    """Paired-block arm totals.

    UNIQUE_FILES_MODIFIED (files targeted by an edit or write tool call) and
    FILES_CHANGED (files differing in the captured worktree diff) are DIFFERENT
    measurements and are reported separately: they disagree on Haiku PT07/C1/R2,
    where six files were written but only four ended up different."""
    out = {"C1": {}, "C4": {}}
    missing = {"C1": {}, "C4": {}}
    n = 0
    for b in blocks:
        if not b["eligible"]:
            continue
        n += 1
        for cond in ("C1", "C4"):
            r, raw = b[cond], raw_by_id.get(b[cond]["run_id"], {})
            for k, v in (("edit_calls", num(r["edit_calls"])), ("write_calls", num(r["write_calls"])),
                         ("edit_and_write", (num(r["edit_calls"]) or 0) + (num(r["write_calls"]) or 0)
                          if not (blank(r["edit_calls"]) and blank(r["write_calls"])) else None),
                         ("files_reedited", num(r["files_reedited"])),
                         ("unique_files_read", num(r["unique_files_read"])),
                         ("unique_files_modified", num(r["unique_files_modified"])),
                         ("ci_command_runs", num(r["ci_command_runs"])),
                         ("test_command_runs", num(r["test_command_runs"])),
                         ("lines_added", num(r["lines_added"])), ("lines_removed", num(r["lines_removed"])),
                         ("net_lines", num(r["net_lines"])), ("turns_used", num(raw.get(turn_key))),
                         ("failed_ci_cycles", num(raw.get(fail_key)) if fail_key else None),
                         ("files_changed", num(raw.get(files_changed_key)) if files_changed_key else None)):
                if v is None:
                    missing[cond][k] = missing[cond].get(k, 0) + 1
                else:
                    out[cond][k] = out[cond].get(k, 0) + v
    return out, n, missing


SON_REWORK, SON_REWORK_N, SON_REWORK_MISSING = rework(A2_BLOCKS, A2_RAW_BY_ID, "TURNS_USED", "FAILED_TEST_OR_CI_CYCLES")
HAI_REWORK, HAI_REWORK_N, HAI_REWORK_MISSING = rework(LM_BLOCKS, LM_RAW_BY_ID, "turns_used", None, "files_changed")

for k, c1, c4 in (("turns_used", 229, 309), ("edit_calls", 54, 66), ("files_reedited", 16, 20),
                  ("lines_added", 1755, 1932), ("lines_removed", 134, 186), ("net_lines", 1621, 1746),
                  ("files_changed", 25, 30)):
    check(f"Haiku paired-block {k} C1", c1, int(HAI_REWORK["C1"][k]))
    check(f"Haiku paired-block {k} C4", c4, int(HAI_REWORK["C4"][k]))

# arm-level totals over ALL runs of each arm (a different, also-published scope)
ARM_TOTALS = {}
for label, rows in (("Sonnet", A2_ROWS), ("Haiku", LM_ROWS)):
    for cond in ("C1", "C4"):
        sub = [r for r in rows if r["condition"] == cond]
        ARM_TOTALS[(label, cond)] = {
            k: (sum(num(r[k]) for r in sub if not blank(r[k])) if any(not blank(r[k]) for r in sub) else None)
            for k in ("ci_command_runs", "test_command_runs", "total_tool_calls", "exploration_calls")}

# --------------------------------------------------------------------------- #
# 7. reset recovery (Sonnet only)
# --------------------------------------------------------------------------- #


def reset_overhead(metric):
    """RESET / NON_RESET inside one task, condition and repetition.

    Scope matches the frozen analysis: a repetition contributes only when BOTH
    of its runs are functionally valid, which drops PT01/C4/R1 (reset arm
    refused) and PT04/C1/R1 (reset checkpoint never reached)."""
    fn = METRIC_FN[metric]
    rows = []
    for task in ("PT01", "PT04", "PT07"):
        for cond in ("C1", "C4"):
            ratios, dropped = [], []
            for rep in ("1", "2", "3"):
                nr = [r for r in A2_ROWS if r["task"] == task and r["condition"] == cond
                      and r["reset_state"] == "NON_RESET" and r["repetition"] == rep]
                rs = [r for r in A2_ROWS if r["task"] == task and r["condition"] == cond
                      and r["reset_state"] == "RESET" and r["repetition"] == rep]
                if len(nr) != 1 or len(rs) != 1:
                    dropped.append(f"R{rep} (no NON_RESET/RESET pair)")
                elif nr[0]["functional_valid"] != "true" or rs[0]["functional_valid"] != "true":
                    dropped.append(f"R{rep} (a run is not functionally valid)")
                else:
                    a, b = fn(nr[0]), fn(rs[0])
                    if a not in (None, 0) and b is not None:
                        ratios.append(b / a)
                    else:
                        dropped.append(f"R{rep} (metric not defined)")
            rows.append({"endpoint": metric, "task": task, "condition": cond, "n": len(ratios),
                         "median_reset_over_nonreset": med(ratios),
                         "repetitions_dropped": "; ".join(dropped)})
    return rows


RESET_ENDPOINTS = ("TOTAL_INPUT_TOKENS", "MODEL_WALL_SECONDS", "EXPLORATION_CALLS", "TOTAL_TOOL_CALLS")
RESET_OVERHEAD = []
for m in RESET_ENDPOINTS:
    RESET_OVERHEAD.extend(reset_overhead(m))

FROZEN_RESET = {(r["endpoint"], r["task"], r["condition"]): r for r in A2_RESET}
for r in RESET_OVERHEAD:
    f = FROZEN_RESET.get((r["endpoint"], r["task"], r["condition"]))
    if f and r["median_reset_over_nonreset"] is not None:
        check(f"Sonnet reset overhead {r['endpoint']} {r['task']} {r['condition']}",
              round(float(f["median_reset_over_nonreset"]), 4), r4(r["median_reset_over_nonreset"]))

RESET_C4_LOWER = {}
for m in RESET_ENDPOINTS:
    tasks = []
    for task in ("PT01", "PT04", "PT07"):
        c1 = next(r for r in RESET_OVERHEAD if r["endpoint"] == m and r["task"] == task and r["condition"] == "C1")
        c4 = next(r for r in RESET_OVERHEAD if r["endpoint"] == m and r["task"] == task and r["condition"] == "C4")
        if None not in (c1["median_reset_over_nonreset"], c4["median_reset_over_nonreset"]) \
                and c4["median_reset_over_nonreset"] < c1["median_reset_over_nonreset"]:
            tasks.append(task)
    RESET_C4_LOWER[m] = tasks

check("Sonnet reset TOKEN overhead lower for C4 in", A2_REPORT["reset_overhead"]["TOTAL_INPUT_TOKENS"]["tasks_where_c4_overhead_is_lower"], RESET_C4_LOWER["TOTAL_INPUT_TOKENS"])
check("Sonnet reset WALL overhead lower for C4 in", A2_REPORT["reset_overhead"]["MODEL_WALL_SECONDS"]["tasks_where_c4_overhead_is_lower"], RESET_C4_LOWER["MODEL_WALL_SECONDS"])
check("Sonnet reset EXPLORATION overhead lower for C4 in", A2_REPORT["reset_overhead"]["EXPLORATION_CALLS"]["tasks_where_c4_overhead_is_lower"], RESET_C4_LOWER["EXPLORATION_CALLS"])
check("Sonnet reset TOOL overhead lower for C4 in", A2_REPORT["reset_overhead"]["TOTAL_TOOL_CALLS"]["tasks_where_c4_overhead_is_lower"], RESET_C4_LOWER["TOTAL_TOOL_CALLS"])

# --------------------------------------------------------------------------- #
# 8. cross-model descriptive matrix (NON_RESET on both sides)
# --------------------------------------------------------------------------- #

CROSS_METRICS = [
    ("TOTAL_INPUT_TOKENS", "input tokens the model was charged for, MAD and cache included"),
    ("TOTAL_OUTPUT_TOKENS", "tokens the model produced"),
    ("MODEL_WALL_SECONDS", "wall-clock seconds inside the model invocation"),
    ("EXPLORATION_CALLS", "read + grep + glob tool calls"),
    ("TOTAL_TOOL_CALLS", "every tool call the agent made"),
    ("UNIQUE_FILES_READ", "distinct files opened"),
    ("EDIT_AND_WRITE_CALLS", "edit + write tool calls"),
    ("PROVIDER_COST_USD", "provider-reported USD for the run"),
]
CROSS = []
for m, gloss in CROSS_METRICS:
    s, h = SON_NR[m], HAI[m]
    CROSS.append({
        "metric": m, "gloss": gloss,
        "sonnet_median": s["median"], "sonnet_n": s["n"],
        "haiku_median": h["median"], "haiku_n": h["n"],
        "difference": (h["median"] - s["median"]) if None not in (s["median"], h["median"]) else None,
        "direction": ("Haiku ratio higher" if None not in (s["median"], h["median"]) and h["median"] > s["median"]
                      else "Haiku ratio lower" if None not in (s["median"], h["median"]) else "not comparable"),
    })

check("cross-model token difference (frozen record)",
      LM_REPORT["sonnet_comparison"]["difference_lower_model_minus_sonnet"],
      round(CROSS[0]["difference"], 3))

# --------------------------------------------------------------------------- #
# 9. git state
# --------------------------------------------------------------------------- #


def git(*args, cwd=REPO):
    try:
        return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return "(unavailable)"


#: The commit pinned in this package is the EVIDENCE commit - the last one to
#: touch study-results/ outside professor-delivery/ - not the repository HEAD.
#: Pinning HEAD would be self-referential: committing this package changes HEAD,
#: which changes the package, which needs another commit.
GIT = {"branch": git("rev-parse", "--abbrev-ref", "HEAD"),
       "evidence_commit": git("log", "-1", "--format=%H", "--",
                              "study-results/", ":(exclude)study-results/professor-delivery"),
       "evidence_subject": git("log", "-1", "--format=%s", "--",
                               "study-results/", ":(exclude)study-results/professor-delivery"),
       "origin": git("config", "--get", "remote.origin.url")}

# =========================================================================== #
#                              EXCEL WORKBOOK
# =========================================================================== #

NAVY = "1F3864"
SLATE = "2E4A6B"
BAND = "DCE6F1"
LIGHT = "F2F5FA"
AMBER = "FFF2CC"
ROSE = "FBE5E5"
MINT = "E2EFDA"

FMT_RATIO = "0.0000"
FMT_USD = "$#,##0.0000"
FMT_USD2 = "$#,##0.00"
FMT_INT = "#,##0"
FMT_SEC = "#,##0.000"
FMT_PCT = "0.0%"

THIN = Side(style="thin", color="B7C3D6")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def sheet_title(ws, title, subtitle, width=10):
    ws["A1"] = title
    ws["A1"].font = Font(size=15, bold=True, color=NAVY)
    ws["A2"] = subtitle
    ws["A2"].font = Font(size=9, italic=True, color="555555")
    ws["A2"].alignment = Alignment(wrap_text=False)
    ws.row_dimensions[1].height = 22
    return 4


def section(ws, row, text, note=None, span=12):
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(size=11, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=SLATE)
    c.alignment = Alignment(vertical="center", indent=1)
    for i in range(2, span + 1):
        ws.cell(row=row, column=i).fill = PatternFill("solid", fgColor=SLATE)
    ws.row_dimensions[row].height = 18
    row += 1
    if note:
        n = ws.cell(row=row, column=1, value=note)
        n.font = Font(size=8, italic=True, color="555555")
        row += 1
    return row


FIRST_TABLE = {}


def table(ws, row, headers, rows, formats=None, widths=None, band=True, autofilter=False):
    """Write a header row + data rows. `formats` maps 0-based column index to a
    number format. Returns the row after the table."""
    formats = formats or {}
    for j, h in enumerate(headers, start=1):
        c = ws.cell(row=row, column=j, value=h)
        c.font = Font(bold=True, color="FFFFFF", size=9)
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        c.border = BORDER
    ws.row_dimensions[row].height = 30
    header_row = row
    row += 1
    for i, data in enumerate(rows):
        for j, v in enumerate(data, start=1):
            c = ws.cell(row=row, column=j, value=v)
            c.font = Font(size=9)
            c.border = BORDER
            if band and i % 2 == 1:
                c.fill = PatternFill("solid", fgColor=LIGHT)
            fmt = formats.get(j - 1)
            if fmt and isinstance(v, (int, float)):
                c.number_format = fmt
            if isinstance(v, str) and len(v) > 60:
                c.alignment = Alignment(wrap_text=True, vertical="top")
            elif isinstance(v, (int, float)):
                c.alignment = Alignment(horizontal="right")
        row += 1
    if widths:
        for j, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(j)].width = w
    if rows:
        ref = f"A{header_row}:{get_column_letter(len(headers))}{row - 1}"
        FIRST_TABLE.setdefault(ws.title, ref)
        if autofilter:
            ws.auto_filter.ref = ref
    return row + 1


def note(ws, row, text, fill=None):
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(size=9, italic=True, color="333333")
    if fill:
        c.fill = PatternFill("solid", fgColor=fill)
    return row + 1


def freeze(ws, cell="A5"):
    ws.freeze_panes = cell


def ratio_chart(ws, anchor, title, cat_ref, series, y_title="C4 / C1 (1.00 = parity)"):
    ch = BarChart()
    ch.type = "col"
    ch.style = 10
    ch.title = title
    ch.y_axis.title = y_title
    ch.x_axis.title = None
    ch.height, ch.width = 8.5, 20
    for ref, from_rows in series:
        ch.add_data(ref, titles_from_data=True, from_rows=from_rows)
    ch.set_categories(cat_ref)
    ch.gapWidth = 60
    ws.add_chart(ch, anchor)
    return ch


OUT.mkdir(parents=True, exist_ok=True)
WRITTEN = []

# --------------------------------------------------------------------------- #
# 10. professor-safe full run export
#
# Written BEFORE the workbook so that its four fidelity checks are part of the
# audit total the workbook publishes, rather than four checks the workbook
# cannot see.
# --------------------------------------------------------------------------- #

RUN_COLS = ["experiment_id", "execution_attempt", "sequence", "run_id", "task", "model", "condition", "reset_state",
            "repetition", "run_purpose", "functional_valid", "semantic_pass", "semantic_fail",
            "architecture_applicable", "architecture_violated", "raw_architecture_violations",
            "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "total_input_tokens",
            "total_output_tokens", "model_wall_seconds", "total_run_seconds", "provider_cost_usd",
            "total_tool_calls", "exploration_calls", "read_calls", "grep_calls", "glob_calls", "bash_calls",
            "edit_calls", "write_calls", "unique_files_read", "unique_files_modified", "files_reedited",
            "ci_command_runs", "test_command_runs", "lines_added", "lines_removed", "net_lines",
            "checkpoint_status", "max_turn_status", "run_status", "eligible_for_analysis", "reason_if_excluded",
            "artifact_path", "evidence_hash_if_available", "notes"]
NUMERIC_COLS = {"execution_attempt", "sequence", "repetition", "semantic_pass", "semantic_fail",
                "architecture_applicable", "architecture_violated", "raw_architecture_violations",
                "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "total_input_tokens",
                "total_output_tokens", "model_wall_seconds", "total_run_seconds", "provider_cost_usd",
                "total_tool_calls", "exploration_calls", "read_calls", "grep_calls", "glob_calls", "bash_calls",
                "edit_calls", "write_calls", "unique_files_read", "unique_files_modified", "files_reedited",
                "ci_command_runs", "test_command_runs", "lines_added", "lines_removed", "net_lines"}
CSV_PATH = OUT / "AFCI_Professor_Full_Run_Results.csv"
with open(CSV_PATH, "w", newline="", encoding="utf-8") as fh:
    # LF explicitly: the repository pins eol=lf, so the working tree matches the blob.
    w = csv.DictWriter(fh, fieldnames=RUN_COLS, extrasaction="ignore", lineterminator=LF)
    w.writeheader()
    for src in RUNS:
        w.writerow({c: ("" if blank(src.get(c)) else src.get(c)) for c in RUN_COLS})
WRITTEN.append(CSV_PATH)
print(f"wrote {CSV_PATH}")

exported = read_csv(CSV_PATH)
check("exported CSV row count equals the master run rows", len(RUNS), len(exported))
check("exported CSV preserves every excluded row",
      sum(1 for r in RUNS if r["eligible_for_analysis"] != "true"),
      sum(1 for r in exported if r["eligible_for_analysis"] != "true"))
check("exported CSV carries a reason for every excluded row",
      True, all(not blank(r["reason_if_excluded"]) for r in exported if r["eligible_for_analysis"] != "true"))
check("exported CSV introduced no zero where the master had a blank", 0, sum(
    1 for a, b in zip(RUNS, exported)
    for c in RUN_COLS if blank(a.get(c)) and not blank(b.get(c))))


#: Computed here, after every check above has run, so the workbook publishes the
#: real total rather than a snapshot taken partway through.
AUDIT_MISMATCHES = [a for a in AUDIT if a["status"] != "MATCH"]


wb = Workbook()
wb.remove(wb.active)

# --------------------------------------------------------------------------- 01
ws = wb.create_sheet("01_EXECUTIVE_SUMMARY")
r = sheet_title(ws, "AFCI-Bench - executive summary of all runs to date",
                f"Compiled {COMPILED} from study-results/. Reporting only: no benchmark observation was executed "
                f"and no scientific result was changed. Every figure recomputes from the {INV['total_rows']} "
                "run/attempt rows; see 20_RECOMPUTATION_AUDIT.")
ws.column_dimensions["A"].width = 46
for col in "BCDEFGH":
    ws.column_dimensions[col].width = 17
ws.column_dimensions["I"].width = 60

r = section(ws, r, "PROGRAMME TOTALS")
r = table(ws, r, ["measure", "value", "note"], [
    ["Experiment sets executed", 9, "V1, PT08, PT09, PT10, efficiency Attempt 1 (aborted), efficiency Attempt 2, "
                                    "lower-model pilot, Backstage Attempt 1 (halted), Backstage Attempt 2 (complete)"],
    ["Experiment sets not started", 1,
     "OPEN_SOURCE_COMPLEXITY_STUDY - placeholder only, no runs exist"],
    ["Total run/attempt records", INV["total_rows"], "one row per scheduled run or attempt, including excluded ones"],
    ["Distinct run identities", INV["unique_run_ids"],
     "3 fewer than rows: the PT08 run-id collision (3 rows share 1 id) and the Attempt-1 collision pair (2 rows share 1 id)"],
    ["Observations with run_status = COMPLETE", INV["completed"],
     "Attempt 1's 7 surviving rows carry INTACT_GOVERNED_OBSERVATION instead, and 2 carry DAMAGED_*; the experiment "
     "registry counts those 7 as 'completed runs'. Both readings are shown, in sheet 02 and here."],
    ["Functionally valid observations", INV["functional_valid"],
     f"{INV['functional_invalid']} explicitly invalid; {INV['functional_not_captured']} carry no functional verdict at all"],
    ["Diagnostic / qualification observations", INV["diagnostic_qualification"],
     "PT08 (3) + PT09 (4, one infrastructure-invalid) + PT10 (3); instrument evidence, never treatment evidence"],
    ["Excluded from every analysis", INV["excluded"],
     "v1 (48), efficiency Attempt 1 (9), diagnostics/qualification (10), Backstage Attempt 1 (7), plus 4 v2 rows. "
     "The 12 Backstage Attempt-2 rows outside a functionally valid pair are counted here too, but ONLY the paired "
     "EFFICIENCY analysis excludes them: all 18 enter the primary architecture endpoint, which is scored "
     "independently of functional validity"],
    ["Eligible for any analysis", INV["eligible"],
     "all of them non-confirmatory: efficiency Attempt 2 (34) + lower-model pilot (16) + "
     "Backstage Attempt 2 (6, the 3 functionally valid paired blocks)"],
    ["Confirmatory observations", 0, "none. No p-value, confidence interval, effect size or power estimate exists"],
    ["Models tested", 3, "'Opus 7' (v1, historical), claude-sonnet-5, claude-haiku-4-5-20251001"],
    ["Tasks tested", len(INV["by_task"]),
     "12 v1 tasks (T01-T12) + 6 v2 synthetic tasks (PT01, PT04, PT07, PT08, PT09, PT10) + "
     "3 Backstage real-repository tasks (T1, T2, T5)"],
    ["Conditions", 4, "v1: baseline / AFCI. v2: C1 (task only) / C4 (task + explicit MAD)"],
    ["Reset states", 2, "NON_RESET and RESET; the lower-model pilot is NON_RESET only, by design"],
], formats={1: FMT_INT}, widths=[46, 17, 100])

r = section(ws, r, "RESULT CARD 1 - V1 ORIGINAL STUDY (historical / exploratory only)")
r = table(ws, r, ["observed result", "baseline", "AFCI", "change", "per-task direction"], [
    ["NON_RESET code churn (mean)", 576.58, 955.42, "+65.7%", "AFCI higher in 12/12 tasks"],
    ["NON_RESET test churn (mean)", 172.67, 244.00, "+41.3%", "AFCI higher in 12/12 tasks"],
    ["RESET true drift, delta CodeLOC (mean)", 307.7, 670.5, "+117.9%", "AFCI LOWER in 1/12 tasks"],
    ["CI pass rate", 1.0, 1.0, "0.0 pp", "48/48 - saturated, does not discriminate"],
], formats={1: "#,##0.00", 2: "#,##0.00"}, widths=[46, 17, 17, 17, 60])
r = note(ws, r, "LIMITATION: v1 runs are non-independent (the tree was never reset between tasks), the harness did not "
                "invoke a model, and the architecture guard never fired. v1 is historical evidence and no v1 number may "
                "be pooled with or contrasted against a v2 number.", AMBER)
r += 1

r = section(ws, r, "RESULT CARD 2 - SONNET EFFICIENCY PILOT, ATTEMPT 2 (claude-sonnet-5, 36 runs)")
r = table(ws, r, ["observed result", "value", "coverage", "note"], [
    ["Runs executed", 36, "36 of 36 scheduled", "35 COMPLETE, 1 REFUSED (sequence 12)"],
    ["Functionally valid", 34, "C1 17/18, C4 17/18", "essentially equal quality between the arms"],
    ["Paired-eligible blocks", 16, "of 18; minimum required 12", "2 valid runs are unpaired and unused"],
    ["Median C4/C1 input tokens (PRIMARY)", SON["TOTAL_INPUT_TOKENS"]["median"], "n = 16 pairs",
     f"C4 cheaper in {SON['TOTAL_INPUT_TOKENS']['c4_lower_count']} of 16 pairs"],
    ["  ... NON_RESET arm", SON_NR["TOTAL_INPUT_TOKENS"]["median"], "n = 9 pairs", "the like-for-like arm for cross-model comparison"],
    ["  ... RESET arm", SON_RS["TOTAL_INPUT_TOKENS"]["median"], "n = 7 pairs", ""],
    ["Median C4/C1 wall seconds", SON["MODEL_WALL_SECONDS"]["median"], "n = 16 pairs", ""],
    ["Median C4/C1 exploration calls", SON["EXPLORATION_CALLS"]["median"], "n = 16 pairs", ""],
    ["Median C4/C1 total tool calls", SON["TOTAL_TOOL_CALLS"]["median"], "n = 16 pairs", ""],
    ["Median C4/C1 unique files read", SON["UNIQUE_FILES_READ"]["median"], "n = 16 pairs", ""],
    ["Median C4/C1 edit + write calls", SON["EDIT_AND_WRITE_CALLS"]["median"], "n = 16 pairs", "C4 lower in 0 of 16"],
    ["Median C4/C1 provider cost", SON_NR["PROVIDER_COST_USD"]["median"], "n = 9 pairs, NON_RESET only",
     "PARTIAL COST CAPTURE - there is no RESET cost comparison at all"],
    ["Reset recovery: C4 token overhead lower", "2 of 3 tasks", "PT01, PT07", "the one signal running the other way"],
    ["Reset recovery: C4 wall overhead lower", "3 of 3 tasks", "PT01, PT04, PT07", "the one signal running the other way"],
    ["Architecture endpoint", "NOT MEASURED", "cost-only purpose", "no architecture claim may be derived from this pilot"],
], formats={1: FMT_RATIO}, widths=[46, 17, 24, 70])
r = note(ws, r, "DECISION (rule 11.4, frozen before the data existed): "
                "STOP - NO EFFICIENCY SIGNAL JUSTIFIES FULL-SUITE EXPANSION.", ROSE)
r += 1

r = section(ws, r, "RESULT CARD 3 - LOWER-MODEL PILOT (claude-haiku-4-5-20251001, 18 runs, NON_RESET)")
r = table(ws, r, ["observed result", "value", "coverage", "note"], [
    ["Runs executed", 18, "18 of 18 scheduled", "18 COMPLETE, 0 refused, 0 infrastructure-invalid"],
    ["Functionally valid", 17, "C1 8/9, C4 9/9", "the single invalid run is PT04/C1/R2"],
    ["Paired-eligible blocks", 8, "of 9", "1 valid C4 run is stranded by its invalid C1 partner"],
    ["Architecture: target-violation runs, C1", 0, "of 9 runs, 9 applicable opportunities", "architecture FLOOR"],
    ["Architecture: target-violation runs, C4", 0, "of 9 runs, 9 applicable opportunities", "architecture FLOOR"],
    ["Median C4/C1 input tokens (PRIMARY)", HAI["TOTAL_INPUT_TOKENS"]["median"], "n = 8 pairs",
     f"C4 cheaper in {HAI['TOTAL_INPUT_TOKENS']['c4_lower_count']} of 8 pairs"],
    ["Median C4/C1 output tokens", HAI["TOTAL_OUTPUT_TOKENS"]["median"], "n = 8 pairs", ""],
    ["Median C4/C1 wall seconds", HAI["MODEL_WALL_SECONDS"]["median"], "n = 8 pairs", ""],
    ["Median C4/C1 exploration calls", HAI["EXPLORATION_CALLS"]["median"], "n = 8 pairs", ""],
    ["Median C4/C1 total tool calls", HAI["TOTAL_TOOL_CALLS"]["median"], "n = 8 pairs", ""],
    ["Median C4/C1 unique files read", HAI["UNIQUE_FILES_READ"]["median"], "n = 8 pairs", ""],
    ["Median C4/C1 edit + write calls", HAI["EDIT_AND_WRITE_CALLS"]["median"], "n = 8 pairs", ""],
    ["Median C4/C1 provider cost", HAI["PROVIDER_COST_USD"]["median"], "n = 8 pairs", "COMPLETE COST COVERAGE"],
    ["Captured cost, C1 paired blocks", sum(p["C1"] for p in HAI["PROVIDER_COST_USD"]["pairs"]), "8 runs", ""],
    ["Captured cost, C4 paired blocks", sum(p["C4"] for p in HAI["PROVIDER_COST_USD"]["pairs"]), "8 runs", ""],
    ["Captured cost, all 18 runs", sum(num(x["provider_cost_usd"]) for x in LM_ROWS), "18 of 18 runs", ""],
], formats={1: FMT_RATIO}, widths=[46, 17, 32, 70])
for rr in range(r - 4, r - 1):
    ws.cell(row=rr, column=2).number_format = FMT_USD
r = note(ws, r, "DECISION (SL-V2-LOWER-MODEL-01 section 12, frozen before the data existed): "
                "NO LOWER-MODEL SIGNAL - DO NOT EXPAND THE SYNTHETIC LOWER-MODEL MATRIX.", ROSE)
r += 1

r = section(ws, r, "CURRENT RESEARCH CONCLUSION")
r = table(ws, r, ["#", "statement", "tag"], [
    [1, "On a clean synthetic substrate, a strong model (claude-sonnet-5) showed no efficiency benefit from being given an "
        "explicit Machine-readable Architecture Document. Every captured cost dimension except CI invocations moved against "
        "C4, while functional quality stayed level at 17/18 versus 17/18.", "FACT"],
    [2, "Lowering model capability to claude-haiku-4-5 did not reverse that result. C4's median token ratio rose to "
        f"{r4(HAI['TOTAL_INPUT_TOKENS']['median'])} against Sonnet's NON_RESET {r4(SON_NR['TOTAL_INPUT_TOKENS']['median'])} - "
        "the opposite direction to the moderator hypothesis.", "FACT"],
    [3, "Architecture quality remained at a floor in the tested synthetic tasks: PT08 0/3, PT09 0/3, PT10 1/3 for an unguided "
        "Sonnet baseline, and 0/9 in BOTH Haiku arms. A tie at zero discriminates nothing.", "FACT"],
    [4, "The strong-model-ceiling explanation for the repeated null has therefore been tested and is not supported.", "INTERPRETATION"],
    [5, "Repository architectural complexity / ambiguity / context-recovery burden is the next scientifically distinct "
        "moderator to investigate. It is the remaining rival explanation, standing by elimination rather than by evidence.", "INTERPRETATION"],
    [6, "None of this supports a claim that AFCI is ineffective in general. It was not effective HERE, on one synthetic "
        "49-file monorepo whose architecture is inferable from its own import graph, on two provisional models, with no "
        "confirmatory data and no statistical inference of any kind.", "LIMITATION"],
], widths=[5, 120, 18])
freeze(ws, "A5")

# --------------------------------------------------------------------------- 02
ws = wb.create_sheet("02_EXPERIMENT_INVENTORY")
r = sheet_title(ws, "Experiment inventory - one row per experiment set",
                "Planned/attempted/completed counts come from AFCI_MASTER_EXPERIMENT_REGISTRY.csv; the functional-valid and "
                "eligible counts are recounted from the run rows and reconcile with it.")
REG = {x["experiment_id"]: x for x in REGISTRY}
PE = {x["experiment_id"]: x for x in PER_EXPERIMENT}
inv_rows = []
ORDER = ["V1_ORIGINAL", "V2_PT08_DIAGNOSTIC", "V2_PT09_QUALIFICATION", "V2_PT10_QUALIFICATION",
         "V2_EFF_ATTEMPT1", "V2_EFF_ATTEMPT2", "V2_LOWER_MODEL_PILOT", "V2_BACKSTAGE_PILOT",
         "V2_BACKSTAGE_PILOT_ATTEMPT_2", "OPEN_SOURCE_COMPLEXITY_STUDY"]
CLASSIFICATION = {
    "V1_ORIGINAL": "HISTORICAL / EXPLORATORY",
    "V2_PT08_DIAGNOSTIC": "DIAGNOSTIC ONLY",
    "V2_PT09_QUALIFICATION": "QUALIFICATION ONLY",
    "V2_PT10_QUALIFICATION": "QUALIFICATION ONLY",
    "V2_EFF_ATTEMPT1": "ABORTED / EXCLUDED WHOLESALE",
    "V2_EFF_ATTEMPT2": "COMPLETED PILOT, NON-CONFIRMATORY",
    "V2_LOWER_MODEL_PILOT": "COMPLETED PILOT, NON-CONFIRMATORY",
    "V2_BACKSTAGE_PILOT": "HALTED / EXCLUDED WHOLESALE",
    "V2_BACKSTAGE_PILOT_ATTEMPT_2": "COMPLETED PILOT, NON-CONFIRMATORY",
    "OPEN_SOURCE_COMPLEXITY_STUDY": "NOT STARTED",
}
for eid in ORDER:
    g, p = REG[eid], PE.get(eid)
    fv = ("NOT CAPTURED" if eid == "V1_ORIGINAL" else
          "EXCLUDED" if eid == "V2_EFF_ATTEMPT1" else
          "n/a" if p is None else p["functional_valid"])
    tbd = (lambda v: v if v else "TBD")
    inv_rows.append([
        eid, g["experiment_name"], g["study_version"], tbd(g["model"]), tbd(g["runtime"]),
        intn(g["task_count"]), tbd(g["conditions"]), tbd(g["reset_states"]),
        intn(g["planned_runs"]), intn(g["attempted_runs"]), intn(g["completed_runs"]), fv,
        g["status"], "YES" if g["analysis_eligible"] == "true" else "NO",
        CLASSIFICATION[eid], g["primary_question"] or "(not yet defined)", g["decision"] or "(none)",
        g["notes"][:600],
    ])
r = table(ws, r, ["experiment_id", "experiment_name", "study_version", "model", "runtime", "task_count",
                  "conditions", "reset_states", "planned_runs", "attempted_runs", "completed_runs",
                  "functional_valid_runs", "analysis_status", "eligible_for_inference", "classification",
                  "primary_question", "decision", "notes"], inv_rows,
          formats={5: FMT_INT, 8: FMT_INT, 9: FMT_INT, 10: FMT_INT},
          widths=[26, 42, 12, 26, 30, 10, 14, 18, 11, 12, 13, 15, 26, 13, 32, 46, 48, 80],
          autofilter=True)
r = note(ws, r, "OPEN_SOURCE_COMPLEXITY_STUDY is a placeholder. No runs exist and no result is pre-populated.", AMBER)
r = note(ws, r, "V2_BACKSTAGE_PILOT_ATTEMPT_2 is COMPLETE: 18 planned, 18 attempted, 18 completed, 18 valid, 0 "
                "infrastructure-invalid, 0 retries. It was a WHOLLY NEW execution of the science "
                "SL-V2-BACKSTAGE-PILOT-01 froze, with new run ids and new destinations and zero overlap with attempt "
                "1. The frozen 11.1 continuation rule returned NO ARCHITECTURE SIGNAL - DO NOT AUTOMATICALLY EXPAND "
                "(criterion 1 PASS, criterion 2 FAIL, criterion 3 PASS). V2_BACKSTAGE_PILOT (attempt 1) stays HALTED "
                "and EXCLUDED WHOLESALE and is never pooled with it, replaced by it, or re-run under it.", AMBER)
r = note(ws, r, "planned / attempted / completed_runs on this sheet are the experiment registry's own counts. "
                "V2_EFF_ATTEMPT1's 'completed_runs = 7' is the registry counting its 7 surviving rows; those rows carry "
                "run_status = INTACT_GOVERNED_OBSERVATION, not COMPLETE, so a status-based recount of the same rows gives "
                "0. Both readings are correct at their own definition and neither is reconciled away. See sheet 20.")
r = note(ws, r, "Recounted from the run rows, the two analysed pilots agree with the registry exactly: Attempt 2 "
                f"{PE['V2_EFF_ATTEMPT2']['completed']} complete / {PE['V2_EFF_ATTEMPT2']['functional_valid']} "
                f"functionally valid / {sum(1 for b in A2_BLOCKS if b['eligible'])} paired blocks, and the lower-model "
                f"pilot {PE['V2_LOWER_MODEL_PILOT']['completed']} / {PE['V2_LOWER_MODEL_PILOT']['functional_valid']} / "
                f"{sum(1 for b in LM_BLOCKS if b['eligible'])}.")
freeze(ws, "B5")

# --------------------------------------------------------------------------- 03
ws = wb.create_sheet("03_ALL_RUNS")
r = sheet_title(ws, f"All {INV['total_rows']} run / attempt records",
                "Verbatim from AFCI_MASTER_RUN_RESULTS.csv. A blank cell means the metric was NOT CAPTURED for that run; "
                "it never means zero. Private evaluator identifiers are not present in any column.")
run_rows = []
for src in RUNS:
    row = []
    for c in RUN_COLS:
        v = src.get(c)
        if blank(v):
            row.append(None)                     # blank, never zero
        elif c in NUMERIC_COLS:
            f = num(v)
            row.append(int(f) if f is not None and float(f).is_integer() and c not in
                       ("model_wall_seconds", "total_run_seconds", "provider_cost_usd") else f)
        else:
            row.append(v)
    run_rows.append(row)
fmt = {}
for i, c in enumerate(RUN_COLS):
    if c in ("provider_cost_usd",):
        fmt[i] = FMT_USD
    elif c in ("model_wall_seconds", "total_run_seconds"):
        fmt[i] = FMT_SEC
    elif c in NUMERIC_COLS:
        fmt[i] = FMT_INT
widths = []
for c in RUN_COLS:
    widths.append(46 if c == "run_id" else 60 if c in ("reason_if_excluded", "notes", "artifact_path")
                  else 40 if c == "evidence_hash_if_available" else 13 if len(c) < 14 else 16)
r = table(ws, r, RUN_COLS, run_rows, formats=fmt, widths=widths, autofilter=True)
freeze(ws, "E5")

# --------------------------------------------------------------------------- 04
ws = wb.create_sheet("04_FUNCTIONAL_MATRIX")
r = sheet_title(ws, "Functional correctness by experiment, task and condition",
                "FUNCTIONAL_VALID is the hidden acceptance oracle's verdict (record.functional_evaluation.functional_valid) "
                "and is never inferred from CI success, model prose, exit status or any architecture value.")
for label, exp in (("SONNET EFFICIENCY PILOT, ATTEMPT 2 (claude-sonnet-5)", "V2_EFF_ATTEMPT2"),
                   ("LOWER-MODEL PILOT (claude-haiku-4-5-20251001)", "V2_LOWER_MODEL_PILOT")):
    r = section(ws, r, label)
    rows = []
    for f in [x for x in FUNCTIONAL if x["experiment"] == exp]:
        pe, pt = PAIRED_BLOCKS[(exp, f["scope"])]
        rows.append([f["scope"], f["condition"], f["runs"], f["valid"], f["invalid"], f["no_verdict"],
                     (f["valid"] / f["runs"]) if f["runs"] else None,
                     f["semantic_pass"], f["semantic_fail"],
                     f["semantic_pass"] + f["semantic_fail"], f"{pe} of {pt}"])
    r = table(ws, r, ["scope", "condition", "runs", "functionally valid", "functionally invalid",
                      "no functional verdict", "valid rate", "semantic cases passed", "semantic cases failed",
                      "semantic cases executed", "paired-valid blocks"], rows,
              formats={2: FMT_INT, 3: FMT_INT, 4: FMT_INT, 5: FMT_INT, 6: FMT_PCT, 7: FMT_INT, 8: FMT_INT, 9: FMT_INT},
              widths=[10, 11, 8, 17, 18, 19, 11, 20, 19, 20, 19])
r = note(ws, r, "Sonnet: the C4 run with no functional verdict is sequence 12 (PT01/C4/RESET/R1), which was REFUSED after "
                "the model process exceeded its 1800 s ceiling - no usage, no cost and no verdict exist for it. The C1 "
                "invalid run is PT04/C1/RESET/R1, which completed but never reached the governed reset checkpoint.")
r = note(ws, r + 1, "Haiku: the one invalid run is PT04/C1/R2, which failed all 4 of its semantic acceptance cases. Its "
                    "valid C4 partner is not deleted and not counted as a failure - it is a complete observation with no "
                    "comparator, so block PT04|R2 cannot be paired.")
CH = r + 3
ws.cell(row=CH, column=1, value="Functionally valid runs, C1 vs C4").font = Font(bold=True, size=10, color=NAVY)
base = CH + 1
chart_rows = [["arm", "C1 valid", "C4 valid"]]
for exp, name in (("V2_EFF_ATTEMPT2", "Sonnet (of 18 per arm)"), ("V2_LOWER_MODEL_PILOT", "Haiku (of 9 per arm)")):
    c1 = next(x for x in FUNCTIONAL if x["experiment"] == exp and x["scope"] == "ALL" and x["condition"] == "C1")
    c4 = next(x for x in FUNCTIONAL if x["experiment"] == exp and x["scope"] == "ALL" and x["condition"] == "C4")
    chart_rows.append([name, c1["valid"], c4["valid"]])
for i, row in enumerate(chart_rows):
    for j, v in enumerate(row, start=1):
        ws.cell(row=base + i, column=j, value=v).font = Font(size=8, color="888888")
ch = BarChart()
ch.type = "col"
ch.title = "Functionally valid runs, C1 vs C4"
ch.y_axis.title = "runs"
ch.height, ch.width = 8, 14
ch.add_data(Reference(ws, min_col=2, max_col=3, min_row=base, max_row=base + 2), titles_from_data=True)
ch.set_categories(Reference(ws, min_col=1, min_row=base + 1, max_row=base + 2))
ws.add_chart(ch, f"D{CH}")
freeze(ws, "A5")

# --------------------------------------------------------------------------- 05
ws = wb.create_sheet("05_ARCHITECTURE_MATRIX")
r = sheet_title(ws, "Architecture evidence - valid measurements only",
                "Only four experiments ever produced an architecture measurement. Opportunity ids, rule ids, forbidden "
                "scopes and anchor paths are hidden evaluator semantics and stay in the private evaluator repository; "
                "no numeric result is withheld.")
r = section(ws, r, "VALID ARCHITECTURE EVIDENCE")
arch_rows = [[a["experiment"], a["model"], a["task"], a["condition"], a["runs"], a["applicable"], a["violated"],
              a["target_violation_runs"],
              (a["violated"] / a["applicable"]) if a["applicable"] else None, a["classification"]] for a in ARCH]
r = table(ws, r, ["experiment", "model", "task", "condition", "runs", "applicable opportunities",
                  "violated opportunities", "target-violation runs", "violation proportion", "classification"],
          arch_rows, formats={4: FMT_INT, 5: FMT_INT, 6: FMT_INT, 7: FMT_INT, 8: FMT_RATIO},
          widths=[28, 28, 8, 11, 8, 22, 21, 21, 18, 40], autofilter=True)
r = section(ws, r, "EXPERIMENTS THAT PRODUCED NO VALID ARCHITECTURE MEASUREMENT")
r = table(ws, r, ["experiment", "architecture status", "why"], [
    ["V2_EFF_ATTEMPT2 (Sonnet efficiency pilot)", "NOT MEASURED",
     "AFCI_EFFICIENCY_PILOT is a cost-only purpose under its own frozen governance. No architecture endpoint was produced "
     "and none may be inferred. The 36 rows' architecture columns are blank, not zero. No continuation threshold depended "
     "on architecture, so none moved."],
    ["V1_ORIGINAL", "INVALID FOR INFERENCE",
     "AFCI-Guard matched literal libs/core import paths while the codebase uses @afci-bench/* aliases, so its regexes never "
     "fired. conformance_summary_v1.csv is all zeros and the guard has no tests. Those zeros are not measurements, and the "
     "v1 architecture columns in this package are blank rather than 0."],
    ["V2_EFF_ATTEMPT1", "EXCLUDED",
     "The attempt was aborted wholesale after 18 deterministic run-id collisions. No analysis of any kind was performed."],
], widths=[42, 26, 120])
r = note(ws, r, "LIMITATION: every architecture measurement above sits at or near a floor. PT10's single violation is the "
                "only target violation recorded anywhere in the programme. A tie at zero between C1 and C4 (the Haiku case) "
                "is NO INFORMATION, not evidence that the MAD fails to improve architecture.", AMBER)
CH = r + 2
ws.cell(row=CH, column=1, value="Target-violation runs by experiment and arm").font = Font(bold=True, size=10, color=NAVY)
base = CH + 1
cdata = [["scope", "target-violation runs", "runs measured"],
         ["PT08 C1", ARCH[0]["target_violation_runs"], ARCH[0]["runs"]],
         ["PT09 C1", ARCH[1]["target_violation_runs"], ARCH[1]["runs"]],
         ["PT10 C1", ARCH[2]["target_violation_runs"], ARCH[2]["runs"]],
         ["Haiku C1", ARCH[3]["target_violation_runs"], ARCH[3]["runs"]],
         ["Haiku C4", ARCH[4]["target_violation_runs"], ARCH[4]["runs"]]]
for i, row in enumerate(cdata):
    for j, v in enumerate(row, start=1):
        ws.cell(row=base + i, column=j, value=v).font = Font(size=8, color="888888")
ch = BarChart()
ch.type = "col"
ch.title = "Target architecture-violation runs (out of runs measured)"
ch.y_axis.title = "runs"
ch.height, ch.width = 8, 18
ch.add_data(Reference(ws, min_col=2, max_col=3, min_row=base, max_row=base + 5), titles_from_data=True)
ch.set_categories(Reference(ws, min_col=1, min_row=base + 1, max_row=base + 5))
ws.add_chart(ch, f"E{CH}")
freeze(ws, "A5")

# --------------------------------------------------------------------------- 06
ws = wb.create_sheet("06_TOKEN_MATRIX")
r = sheet_title(ws, "Token matrix",
                "TOTAL_INPUT_TOKENS = input_tokens + cache_creation_input_tokens + cache_read_input_tokens. The MAD and "
                "cache components are never removed. Every aggregate is shown beside its coverage count.")


def endpoint_rows(label, src, metric, arm_note=""):
    e = src[metric]
    tm = e["task_medians"]
    return [label, e["n"], e["C1_total"], e["C4_total"], e["C1_median"], e["C4_median"], e["median"],
            e["c4_lower_count"], e["c4_lower_fraction"],
            tm.get("PT01"), tm.get("PT04"), tm.get("PT07"), arm_note]


TOKHDR = ["scope", "paired blocks with token evidence", "C1 total input tokens", "C4 total input tokens",
          "C1 median input tokens/run", "C4 median input tokens/run", "median C4/C1 TOKEN_RATIO",
          "pairs where C4 used fewer", "share of pairs where C4 used fewer",
          "PT01 median ratio", "PT04 median ratio", "PT07 median ratio", "note"]
TOKFMT = {1: FMT_INT, 2: FMT_INT, 3: FMT_INT, 4: FMT_INT, 5: FMT_INT, 6: FMT_RATIO, 7: FMT_INT, 8: FMT_PCT,
          9: FMT_RATIO, 10: FMT_RATIO, 11: FMT_RATIO}
TOKW = [40, 16, 18, 18, 18, 18, 18, 16, 17, 14, 14, 14, 56]

r = section(ws, r, "PRIMARY ENDPOINT - TOTAL_INPUT_TOKENS, median of paired C4/C1 ratios")
r = table(ws, r, TOKHDR, [
    endpoint_rows("Sonnet Attempt 2 | overall (RESET + NON_RESET)", SON, "TOTAL_INPUT_TOKENS",
                  "the pilot's pre-registered primary endpoint"),
    endpoint_rows("Sonnet Attempt 2 | NON_RESET", SON_NR, "TOTAL_INPUT_TOKENS",
                  "the like-for-like arm for comparison with Haiku"),
    endpoint_rows("Sonnet Attempt 2 | RESET", SON_RS, "TOTAL_INPUT_TOKENS",
                  "input tokens are EXACT for reset runs; only output and cost are withheld"),
    endpoint_rows("Haiku lower-model pilot | NON_RESET", HAI, "TOTAL_INPUT_TOKENS",
                  "the pilot has no RESET arm: reset was explicitly not authorised"),
], formats=TOKFMT, widths=TOKW)

r = section(ws, r, "OUTPUT TOKENS - TOTAL_OUTPUT_TOKENS")
r = table(ws, r, [h.replace("input tokens", "output tokens").replace("TOKEN_RATIO", "OUTPUT RATIO") for h in TOKHDR], [
    endpoint_rows("Sonnet Attempt 2 | NON_RESET only", SON_NR, "TOTAL_OUTPUT_TOKENS",
                  "WITHHELD for RESET runs: phase A is interrupted before its terminal result event, which is the only "
                  "place the runtime reports output tokens. Withheld, not zero, not estimated."),
    endpoint_rows("Haiku lower-model pilot | NON_RESET", HAI, "TOTAL_OUTPUT_TOKENS",
                  "every non-reset run emits a terminal result event, so all 8 pairs are exact"),
], formats=TOKFMT, widths=TOKW)

r = section(ws, r, "RUN-LEVEL TOKEN COVERAGE (not restricted to paired blocks)")
r = table(ws, r, ["scope", "runs", "runs with token evidence", "runs without", "total input tokens",
                  "median input tokens per run"],
          [[t["scope"], t["runs"], t["runs_with_metric"], t["runs_without_metric"], t["captured_total"],
            t["median_per_run"]] for t in TOKEN_COVERAGE],
          formats={1: FMT_INT, 2: FMT_INT, 3: FMT_INT, 4: FMT_INT, 5: FMT_INT},
          widths=[52, 8, 20, 14, 20, 22])
r = note(ws, r, f"Programme-wide: {INV['token_coverage']} of {INV['total_rows']} run rows carry input-token evidence and "
                f"{INV['output_token_coverage']} carry output-token evidence. v1 (48 rows), Attempt 1 (9 rows) and the "
                "PT08/PT09/PT10 diagnostics (10 rows) predate or do not use the token instrumentation, and their cells are "
                "blank rather than 0.")
CH = r + 2
ws.cell(row=CH, column=1, value="Median C4/C1 input-token ratio by scope").font = Font(bold=True, size=10, color=NAVY)
base = CH + 1
cdata = [["scope", "median C4/C1 input tokens", "parity (1.00)"],
         ["Sonnet overall (n=16)", r4(SON["TOTAL_INPUT_TOKENS"]["median"]), 1.0],
         ["Sonnet NON_RESET (n=9)", r4(SON_NR["TOTAL_INPUT_TOKENS"]["median"]), 1.0],
         ["Sonnet RESET (n=7)", r4(SON_RS["TOTAL_INPUT_TOKENS"]["median"]), 1.0],
         ["Haiku NON_RESET (n=8)", r4(HAI["TOTAL_INPUT_TOKENS"]["median"]), 1.0]]
for i, row_ in enumerate(cdata):
    for j, v in enumerate(row_, start=1):
        ws.cell(row=base + i, column=j, value=v).font = Font(size=8, color="888888")
ch = BarChart()
ch.type = "col"
ch.title = "Median C4/C1 input-token ratio - 1.00 is parity, above 1.00 means C4 used more"
ch.y_axis.title = "C4 / C1"
ch.height, ch.width = 8.5, 18
ch.add_data(Reference(ws, min_col=2, max_col=2, min_row=base, max_row=base + 4), titles_from_data=True)
ch.set_categories(Reference(ws, min_col=1, min_row=base + 1, max_row=base + 4))
ch.gapWidth = 70
_parity = LineChart()
_parity.add_data(Reference(ws, min_col=3, max_col=3, min_row=base, max_row=base + 4), titles_from_data=True)
ch += _parity
ws.add_chart(ch, f"E{CH}")
freeze(ws, "A5")

# --------------------------------------------------------------------------- 07
ws = wb.create_sheet("07_COST_MATRIX")
r = sheet_title(ws, "Provider cost matrix",
                "Provider cost is reported exactly as the runtime captured it. A run with no terminal result event has no "
                "cost, and that cell is blank - never 0, never estimated.")
r = section(ws, r, "COST COVERAGE - read this before any cost figure below")
r = table(ws, r, ["scope", "runs", "runs with complete provider cost", "runs with no cost record",
                  "captured total (USD)", "coverage verdict"],
          [[c["scope"], c["runs"], c["runs_with_metric"], c["runs_without_metric"], c["captured_total"],
            "COMPLETE COST COVERAGE" if c["runs_without_metric"] == 0 else "PARTIAL COST CAPTURE"]
           for c in COST_COVERAGE],
          formats={1: FMT_INT, 2: FMT_INT, 3: FMT_INT, 4: FMT_USD}, widths=[52, 8, 26, 22, 20, 26])
r = note(ws, r, "The single Sonnet RESET run carrying a cost is PT04/C1/RESET/R1 - and it is exactly the run that never "
                "reached its reset checkpoint, which is why it ran to a terminal result event at all. It is functionally "
                "invalid, so it enters no paired cost figure. There are therefore ZERO usable Sonnet RESET cost pairs.", AMBER)
r += 1

r = section(ws, r, "PAIRED COST RATIOS")
COSTHDR = ["scope", "paired blocks with complete cost", "C1 captured total (USD)", "C4 captured total (USD)",
           "C1 median cost/run", "C4 median cost/run", "paired median C4/C1 cost ratio",
           "pairs where C4 cost less", "PT01 median ratio", "PT04 median ratio", "PT07 median ratio", "coverage verdict"]
COSTFMT = {1: FMT_INT, 2: FMT_USD, 3: FMT_USD, 4: FMT_USD, 5: FMT_USD, 6: FMT_RATIO, 7: FMT_INT,
           8: FMT_RATIO, 9: FMT_RATIO, 10: FMT_RATIO}


def cost_row(label, src, verdict):
    e = src["PROVIDER_COST_USD"]
    tm = e["task_medians"]
    return [label, e["n"], e["C1_total"], e["C4_total"], e["C1_median"], e["C4_median"], e["median"],
            e["c4_lower_count"], tm.get("PT01"), tm.get("PT04"), tm.get("PT07"), verdict]


r = table(ws, r, COSTHDR, [
    cost_row("Sonnet Attempt 2 | NON_RESET (like-for-like)", SON_NR,
             "PARTIAL COST CAPTURE for the pilot as a whole - this row covers the NON_RESET arm only"),
    cost_row("Sonnet Attempt 2 | RESET", SON_RS, "NO COST COMPARISON EXISTS - 0 usable pairs"),
    cost_row("Haiku lower-model pilot | NON_RESET", HAI, "COMPLETE COST COVERAGE - all 8 pairs"),
], formats=COSTFMT, widths=[46, 16, 18, 18, 16, 16, 18, 16, 14, 14, 14, 56])
r = note(ws, r, "The Sonnet pilot's 1.4928 cost ratio describes the NON_RESET arm only and must NOT be read as a "
                "whole-pilot cost ratio.", AMBER)
r += 1

r = section(ws, r, "TOTAL CAPTURED PROVIDER COST")
r = table(ws, r, ["scope", "runs with cost evidence", "captured total (USD)", "label"], [
    ["All modern runs carrying cost evidence", len(COST_ROWS), TOTAL_CAPTURED_COST,
     "CAPTURED COST, NOT NECESSARILY TOTAL STUDY COST"],
    ["  of which Sonnet Attempt 2", sum(1 for x in A2_ROWS if not blank(x["provider_cost_usd"])),
     sum(num(x["provider_cost_usd"]) for x in A2_ROWS if not blank(x["provider_cost_usd"])), ""],
    ["  of which Haiku lower-model pilot", 18, sum(num(x["provider_cost_usd"]) for x in LM_ROWS), ""],
], formats={1: FMT_INT, 2: FMT_USD2}, widths=[46, 22, 20, 52])
r = note(ws, r, f"CAVEAT: this is captured cost, not total study cost. {INV['total_rows'] - len(COST_ROWS)} of "
                f"{INV['total_rows']} run rows carry no provider-cost record at all - all 48 v1 rows (v1 predates cost "
                "instrumentation), all 9 Attempt-1 rows, all 10 diagnostic/qualification rows, 16 of 17 Sonnet RESET rows, "
                "and the one refused run. Money was spent on those runs; the runtime simply never reported it in a form "
                "the record could carry. Do not read the total as what the programme cost.", AMBER)
CH = r + 2
ws.cell(row=CH, column=1, value="Captured cost per arm, where coverage is complete").font = Font(bold=True, size=10, color=NAVY)
base = CH + 1
cdata = [["scope", "C1 total USD", "C4 total USD"],
         ["Sonnet NON_RESET (9 pairs)", SON_NR["PROVIDER_COST_USD"]["C1_total"], SON_NR["PROVIDER_COST_USD"]["C4_total"]],
         ["Haiku NON_RESET (8 pairs)", HAI["PROVIDER_COST_USD"]["C1_total"], HAI["PROVIDER_COST_USD"]["C4_total"]]]
for i, row in enumerate(cdata):
    for j, v in enumerate(row, start=1):
        ws.cell(row=base + i, column=j, value=v).font = Font(size=8, color="888888")
ch = BarChart()
ch.type = "col"
ch.title = "Captured provider cost over paired blocks (USD)"
ch.y_axis.title = "USD"
ch.height, ch.width = 8, 16
ch.add_data(Reference(ws, min_col=2, max_col=3, min_row=base, max_row=base + 2), titles_from_data=True)
ch.set_categories(Reference(ws, min_col=1, min_row=base + 1, max_row=base + 2))
ws.add_chart(ch, f"E{CH}")
freeze(ws, "A5")

# --------------------------------------------------------------------------- 08
ws = wb.create_sheet("08_TIME_MATRIX")
r = sheet_title(ws, "Time matrix - MODEL_WALL_SECONDS",
                "MODEL_WALL_SECONDS is wall-clock time inside the model invocation, the governed time endpoint. "
                "TOTAL_RUN_SECONDS (harness wall clock) is carried per run in 03_ALL_RUNS but is not an endpoint.")
TIMEHDR = ["scope", "paired blocks", "C1 total seconds", "C4 total seconds", "C1 median seconds/run",
           "C4 median seconds/run", "median C4/C1 ratio", "pairs where C4 was faster",
           "share where C4 was faster", "PT01 median ratio", "PT04 median ratio", "PT07 median ratio"]
TIMEFMT = {1: FMT_INT, 2: FMT_SEC, 3: FMT_SEC, 4: FMT_SEC, 5: FMT_SEC, 6: FMT_RATIO, 7: FMT_INT,
           8: FMT_PCT, 9: FMT_RATIO, 10: FMT_RATIO, 11: FMT_RATIO}
r = table(ws, r, TIMEHDR, [endpoint_rows(label, src, "MODEL_WALL_SECONDS")[:12] for label, src in (
    ("Sonnet Attempt 2 | overall", SON), ("Sonnet Attempt 2 | NON_RESET", SON_NR),
    ("Sonnet Attempt 2 | RESET", SON_RS), ("Haiku lower-model pilot | NON_RESET", HAI))],
    formats=TIMEFMT, widths=[40, 13, 17, 17, 19, 19, 17, 19, 19, 14, 14, 14])
r = note(ws, r, "Wall time for PT08, PT09 and PT10 is a process wall clock parsed from free-text invocation detail, not the "
                "governed MODEL_WALL_SECONDS endpoint - those purposes never captured it. Their model_wall_seconds cells "
                "are deliberately blank; total_run_seconds carries the process figure.")
freeze(ws, "A5")

# --------------------------------------------------------------------------- 09
ws = wb.create_sheet("09_EXPLORATION_TOOLS")
r = sheet_title(ws, "Exploration and tool-use matrix",
                "EXPLORATION_CALLS = read + grep + glob tool calls. Arm totals are over the paired blocks only, so the "
                "totals and the ratios describe the same runs.")
TOOLHDR = ["metric", "paired blocks", "C1 arm total", "C4 arm total", "C1 median/run", "C4 median/run",
           "median C4/C1 ratio", "pairs where C4 was lower", "PT01 median", "PT04 median", "PT07 median"]
TOOLFMT = {1: FMT_INT, 2: FMT_INT, 3: FMT_INT, 4: FMT_RATIO, 5: FMT_RATIO, 6: FMT_RATIO, 7: FMT_INT,
           8: FMT_RATIO, 9: FMT_RATIO, 10: FMT_RATIO}
TOOL_METRICS = ["EXPLORATION_CALLS", "TOTAL_TOOL_CALLS", "UNIQUE_FILES_READ", "READ_CALLS", "GREP_CALLS",
                "GLOB_CALLS", "BASH_CALLS", "EDIT_CALLS", "WRITE_CALLS", "EDIT_AND_WRITE_CALLS",
                "FILES_REEDITED", "CI_COMMAND_RUNS", "TEST_COMMAND_RUNS"]
for label, src in (("SONNET ATTEMPT 2 - overall (16 paired blocks)", SON),
                   ("SONNET ATTEMPT 2 - NON_RESET (9 paired blocks)", SON_NR),
                   ("HAIKU LOWER-MODEL PILOT - NON_RESET (8 paired blocks)", HAI)):
    r = section(ws, r, label)
    rows = []
    for m in TOOL_METRICS:
        e = src[m]
        tm = e["task_medians"]
        rows.append([m, e["n"], e["C1_total"], e["C4_total"], e["C1_median"], e["C4_median"], e["median"],
                     e["c4_lower_count"] if e["n"] else None, tm.get("PT01"), tm.get("PT04"), tm.get("PT07")])
    r = table(ws, r, TOOLHDR, rows, formats=TOOLFMT, widths=[26, 13, 13, 13, 14, 14, 17, 20, 13, 13, 13])
r = note(ws, r, "TEST_COMMAND_RUNS: the Sonnet pilot has 0 defined pairs - no C1 run issued an agent-initiated test command, "
                "so the ratio is undefined rather than zero. The Haiku pilot has exactly 1 defined pair (PT07/R2).")
freeze(ws, "A5")

# --------------------------------------------------------------------------- 10
ws = wb.create_sheet("10_REWORK_CHANGE_MATRIX")
r = sheet_title(ws, "Rework and change matrix",
                "Arm totals over the paired blocks only. UNIQUE_FILES_MODIFIED (files targeted by an edit or write tool "
                "call) and FILES_CHANGED (files differing in the captured worktree diff) are different measurements and "
                "are kept apart.")
REWORK_KEYS = [
    ("edit_calls", "edit tool calls", FMT_INT),
    ("write_calls", "write tool calls", FMT_INT),
    ("edit_and_write", "edit + write calls", FMT_INT),
    ("files_reedited", "files re-edited (edited more than once)", FMT_INT),
    ("unique_files_read", "unique files read", FMT_INT),
    ("unique_files_modified", "unique files modified (by tool call)", FMT_INT),
    ("files_changed", "files changed (worktree diff)", FMT_INT),
    ("turns_used", "assistant turns used", FMT_INT),
    ("ci_command_runs", "agent-initiated CI command runs", FMT_INT),
    ("test_command_runs", "agent-initiated test command runs", FMT_INT),
    ("failed_ci_cycles", "failed test-or-CI cycles", FMT_INT),
    ("lines_added", "lines added", FMT_INT),
    ("lines_removed", "lines removed", FMT_INT),
    ("net_lines", "net lines", FMT_INT),
]
for label, data, n, missing in (("SONNET ATTEMPT 2 - 16 paired blocks", SON_REWORK, SON_REWORK_N, SON_REWORK_MISSING),
                                ("HAIKU LOWER-MODEL PILOT - 8 paired blocks", HAI_REWORK, HAI_REWORK_N, HAI_REWORK_MISSING)):
    r = section(ws, r, label)
    rows = []
    for key, gloss, _f in REWORK_KEYS:
        c1, c4 = data["C1"].get(key), data["C4"].get(key)
        miss = missing["C1"].get(key, 0) + missing["C4"].get(key, 0)
        if c1 is None and c4 is None:
            rows.append([gloss, None, None, None, None, "NOT CAPTURED by this experiment"])
            continue
        rows.append([gloss, c1, c4, (c4 - c1) if None not in (c1, c4) else None,
                     (c4 / c1) if c1 else None,
                     "" if miss == 0 else f"{miss} of {n * 2} runs carry no value for this metric"])
    r = table(ws, r, ["metric", f"C1 total over {n} blocks", f"C4 total over {n} blocks", "C4 - C1",
                      "C4 / C1 (arm totals)", "coverage note"], rows,
              formats={1: FMT_INT, 2: FMT_INT, 3: FMT_INT, 4: FMT_RATIO},
              widths=[42, 22, 22, 12, 20, 52])
r = note(ws, r, "C4 / C1 here is a ratio of ARM TOTALS, which is a different statistic from the paired median ratios in "
                "sheets 06-09. Both are descriptive; neither is a test.")
r = note(ws, r + 1, "The Sonnet pilot captured no LOC churn (its purpose is cost-only) and the Haiku pilot records no "
                    "failed-test-or-CI-cycle count. Those cells read NOT CAPTURED rather than 0.")
freeze(ws, "A5")

# --------------------------------------------------------------------------- 11
ws = wb.create_sheet("11_RESET_RECOVERY")
r = sheet_title(ws, "Reset recovery - Sonnet Attempt 2 only",
                "Reset overhead = the run's metric under RESET divided by the same task/condition without reset. LOWER "
                "overhead is better. The Haiku pilot is excluded: reset was explicitly not authorised for it.")
for m in RESET_ENDPOINTS:
    r = section(ws, r, f"{m} - reset overhead by task and condition")
    rows = []
    for task in ("PT01", "PT04", "PT07"):
        c1 = next(x for x in RESET_OVERHEAD if x["endpoint"] == m and x["task"] == task and x["condition"] == "C1")
        c4 = next(x for x in RESET_OVERHEAD if x["endpoint"] == m and x["task"] == task and x["condition"] == "C4")
        lower = (None if None in (c1["median_reset_over_nonreset"], c4["median_reset_over_nonreset"])
                 else "YES" if c4["median_reset_over_nonreset"] < c1["median_reset_over_nonreset"] else "no")
        rows.append([task, c1["median_reset_over_nonreset"], c1["n"], c4["median_reset_over_nonreset"], c4["n"],
                     lower, (c1["repetitions_dropped"] + " " + c4["repetitions_dropped"]).strip()])
    rows.append(["TASKS WHERE C4'S OVERHEAD IS LOWER", None, None, None, None,
                 f"{len(RESET_C4_LOWER[m])} of 3", ", ".join(RESET_C4_LOWER[m]) or "none"])
    r = table(ws, r, ["task", "C1 reset overhead (median)", "C1 repetitions", "C4 reset overhead (median)",
                      "C4 repetitions", "C4 overhead lower?", "repetitions dropped, and why"], rows,
              formats={1: FMT_RATIO, 2: FMT_INT, 3: FMT_RATIO, 4: FMT_INT},
              widths=[34, 22, 14, 22, 14, 18, 56])
r = section(ws, r, "THE FROZEN RESET-SPECIFIC DECISION BRANCH (rule 11.3)")
r = table(ws, r, ["clause", "detail", "satisfied"],
          [[c["clause"], c["detail"], c["satisfied"].upper()] for c in A2_CLAUSES if "RESET-SPECIFIC" in c["rule_branch"]],
          widths=[58, 78, 12])
r = note(ws, r, "Both reset-overhead clauses PASSED. The branch failed only on its overall token clause (11.3.2), which "
                "required a median TOKEN_RATIO <= 1.10 against an observed 1.4014. The reset-recovery direction is "
                "therefore a descriptive counter-signal from 3 tasks, not a finding, and it failed the branch that would "
                "have made it a GO.", AMBER)
freeze(ws, "A5")

# --------------------------------------------------------------------------- 12
ws = wb.create_sheet("12_SONNET_VS_HAIKU")
r = sheet_title(ws, "Cross-model descriptive matrix - Sonnet vs Haiku",
                "DESCRIPTIVE ONLY. Two separate experiments, never pooled. Both sides are NON_RESET so the comparison is "
                "like-for-like; the Haiku pilot has no reset arm.")
r = note(ws, r, "This is a descriptive comparison between two separate experiments run under separate purposes, separate "
                "schedules and separate frozen analyses. It is NOT a randomised cross-model causal comparison. No "
                "interaction was estimated, no test was performed, and no pooled model exists.", AMBER)
r += 1
cross_rows = []
for c in CROSS:
    cross_rows.append([c["metric"], c["gloss"], c["sonnet_median"], c["sonnet_n"], c["haiku_median"], c["haiku_n"],
                       c["difference"],
                       f"{c['direction']}; both arms above 1.00, so C4 cost more on both models"
                       if None not in (c["sonnet_median"], c["haiku_median"]) and min(c["sonnet_median"], c["haiku_median"]) > 1
                       else c["direction"]])
r = table(ws, r, ["metric", "what it counts", "Sonnet C4/C1 NON_RESET", "Sonnet paired n",
                  "Haiku C4/C1 NON_RESET", "Haiku paired n", "difference (Haiku - Sonnet)", "interpretation"],
          cross_rows, formats={2: FMT_RATIO, 3: FMT_INT, 4: FMT_RATIO, 5: FMT_INT, 6: FMT_RATIO},
          widths=[26, 52, 20, 15, 20, 15, 21, 62], autofilter=True)
r = section(ws, r, "QUALITY CHANNEL - NOT COMPARABLE")
r = table(ws, r, ["channel", "Sonnet Attempt 2", "Haiku lower-model pilot", "comparable?"], [
    ["architecture target violations", "NOT MEASURED (cost-only purpose)", "0 of 9 in C1 and 0 of 9 in C4 (floor)", "NO"],
    ["functional validity", "C1 17/18, C4 17/18", "C1 8/9, C4 9/9", "descriptively only - different denominators"],
], widths=[32, 40, 44, 34])
r = note(ws, r, "The Sonnet pilot produced no architecture measurement at all, so only the efficiency channel is comparable "
                "across the two models.")
r += 1
r = section(ws, r, "THE MODERATOR HYPOTHESIS AND WHAT THE DATA DID")
r = table(ws, r, ["what was predicted", "what was observed", "reading"], [
    ["A weaker coding model has less ability to infer architecture from the repository alone, so an explicit MAD should "
     "become MORE useful: C4's cost ratio should fall toward or below 1.00 and its architecture violations should fall "
     "below C1's.",
     f"C4's median input-token ratio ROSE from {r4(SON_NR['TOTAL_INPUT_TOKENS']['median'])} on Sonnet to "
     f"{r4(HAI['TOTAL_INPUT_TOKENS']['median'])} on Haiku, a difference of "
     f"{r4(CROSS[0]['difference'])} in the direction opposite to the prediction. Architecture violations were 0 in both "
     "Haiku arms, so the quality channel could not discriminate at all.",
     "The strong-model-ceiling explanation for the repeated null is NOT SUPPORTED. It is not refuted either - one lower-"
     "capability model, one substrate, 8 paired blocks and 3 repetitions cannot refute anything - but the prediction it "
     "makes did not come true."],
], widths=[62, 62, 62])
CH = r + 2
ws.cell(row=CH, column=1, value="Median C4/C1 ratios, NON_RESET, Sonnet vs Haiku").font = Font(bold=True, size=10, color=NAVY)
base = CH + 1
hdr = ["metric", "Sonnet", "Haiku", "parity (1.00)"]
for j, v in enumerate(hdr, start=1):
    ws.cell(row=base, column=j, value=v).font = Font(size=8, color="888888")
for i, c in enumerate(CROSS):
    ws.cell(row=base + 1 + i, column=1, value=c["metric"]).font = Font(size=8, color="888888")
    ws.cell(row=base + 1 + i, column=2, value=r4(c["sonnet_median"])).font = Font(size=8, color="888888")
    ws.cell(row=base + 1 + i, column=3, value=r4(c["haiku_median"])).font = Font(size=8, color="888888")
    ws.cell(row=base + 1 + i, column=4, value=1.0).font = Font(size=8, color="888888")
last = base + len(CROSS)
ch = BarChart()
ch.type = "col"
ch.title = "Median C4/C1 ratio by metric (NON_RESET) - 1.00 is parity, above 1.00 means C4 cost more"
ch.y_axis.title = "C4 / C1"
ch.height, ch.width = 9.5, 24
ch.add_data(Reference(ws, min_col=2, max_col=3, min_row=base, max_row=last), titles_from_data=True)
ch.set_categories(Reference(ws, min_col=1, min_row=base + 1, max_row=last))
ch.gapWidth = 60
line = LineChart()
line.add_data(Reference(ws, min_col=4, max_col=4, min_row=base, max_row=last), titles_from_data=True)
ch += line
ws.add_chart(ch, f"D{CH}")
freeze(ws, "A5")

# --------------------------------------------------------------------------- 13
ws = wb.create_sheet("13_V1_HISTORICAL")
r = sheet_title(ws, "V1 original study - historical / exploratory evidence",
                "12 tasks x {baseline, AFCI} x {non-reset, reset} = 48 runs, one run per cell, model labelled 'Opus 7', "
                "base tag paper-v0. Published as the ASE 2026 artifact; Zenodo DOI 10.5281/zenodo.19757261.")
r = section(ws, r, "HEADLINE RESULTS (recomputed from results_v1.csv)")
r = table(ws, r, ["metric", "baseline", "AFCI", "relative change", "per-task direction"],
          [[x["metric"], num(x["baseline"]) if num(x["baseline"]) is not None else x["baseline"],
            num(x["afci"]) if num(x["afci"]) is not None else x["afci"], x["relative_change"], x["per_task_direction"]]
           for x in V1_HEADLINE], formats={1: "#,##0.00", 2: "#,##0.00"}, widths=[40, 14, 14, 16, 60])
r = section(ws, r, "CONDITION-LEVEL CHURN (a different construct from the drift figure above)")
r = table(ws, r, ["condition", "n", "mean code churn", "median code churn", "mean test churn", "median test churn",
                  "mean files changed", "mean total LOC churn", "CI pass %"],
          [[x["condition"], intn(x["n"]), num(x["mean_code_churn"]), num(x["median_code_churn"]),
            num(x["mean_test_churn"]), num(x["median_test_churn"]), num(x["mean_files_changed"]),
            num(x["mean_total_loc_churn"]), num(x["pct_ci_pass"]) / 100] for x in V1_COMPLETENESS],
          formats={1: FMT_INT, 2: "#,##0.00", 3: "#,##0.0", 4: "#,##0.00", 5: "#,##0.0", 6: "#,##0.00",
                   7: "#,##0.00", 8: FMT_PCT}, widths=[18, 6, 17, 18, 17, 18, 18, 20, 11])
r = section(ws, r, "12-TASK DIRECTIONALITY")
r = table(ws, r, ["task", "baseline code churn", "AFCI code churn", "AFCI / baseline", "higher churn",
                  "baseline test churn", "AFCI test churn", "baseline reset delta CodeLOC",
                  "AFCI reset delta CodeLOC", "baseline CI", "AFCI CI"],
          [[x["task"], intn(x["baseline_code_churn"]), intn(x["afci_code_churn"]),
            num(x["afci_over_baseline_ratio"]), x["higher_churn"], intn(x["baseline_test_churn"]),
            intn(x["afci_test_churn"]), intn(x["baseline_reset_delta_loc_code"]),
            intn(x["afci_reset_delta_loc_code"]), x["baseline_ci_pass"], x["afci_ci_pass"]] for x in V1_TASKWISE],
          formats={1: FMT_INT, 2: FMT_INT, 3: FMT_RATIO, 5: FMT_INT, 6: FMT_INT, 7: FMT_INT, 8: FMT_INT},
          widths=[8, 19, 17, 16, 13, 19, 17, 26, 24, 12, 10], autofilter=True)
r = section(ws, r, "V1 METHODOLOGICAL LIMITATIONS - each independently undermines inference")
r = table(ws, r, ["id", "limitation", "consequence"], [
    ["L1", "The harness captured patch.diff as git diff paper-v0 over the whole working tree and never reset the tree "
           "between tasks, so edits accumulate monotonically across T01 to T12.",
     "Runs are NON-INDEPENDENT. The churn trend across task index is confounded with accumulation. The single most "
     "serious v1 limitation."],
    ["L2", "run_one_v1.sh does not invoke a model; it snapshots the working tree.",
     "Generation and diff capture are not coupled; the generation step is not reproducible from the harness."],
    ["L3", "AFCI-Guard matches literal libs/core import paths, but the codebase uses @afci-bench/* aliases, so the guard "
           "regexes never fire. The guard has no tests.",
     "conformance_summary_v1.csv is all zeros. THOSE ZEROS ARE NOT MEASUREMENTS. In this package the v1 architecture "
     "columns are blank, never 0."],
    ["L4", "docs/ARCH_RULES.yml is 0 bytes on main.", "The documented machine-checkable architecture rules did not exist."],
    ["L5", "layer_jaccard evaluates to a constant 1.0 (self-comparison, expected_layers=None) yet was reported as a metric.",
     "Architecture self-comparison weakness: the metric cannot vary, so it measures nothing."],
    ["L6", "Primary metrics are churn/drift proxies. There is no per-task acceptance oracle beyond npm run ci, and "
           "ci_pass is saturated True across all 48 cells.",
     "The success gate DOES NOT DISCRIMINATE. v1 has no validated hidden task-acceptance oracle."],
    ["L7", "package-lock.json on the v1 base is out of sync with package.json; npm ci fails on the clean base.",
     "Deterministic install is broken at paper-v0 (fixed only at paper-v0-runner)."],
    ["+", "Baseline architecture leakage: the v1 baseline ran against a repository whose architecture was visible in the "
          "tree, so the 'no architecture context' arm was not architecture-free.",
     "v2 addresses this with an allowlisted model-visible worktree that excludes docs/, experiments/, paper/, archive/ "
     "and the architecture-enforcing .eslintrc.json."],
], widths=[6, 76, 76])
r = note(ws, r, "Read at face value, v1 CONTRADICTS the hypothesis: AFCI increased churn on every task and was more "
                "reset-inconsistent on 11 of 12. It should not be read at face value, for the reasons above. v1 is "
                "historical evidence and no v1 number may be pooled with, or contrasted against, a v2 number.", AMBER)
freeze(ws, "A5")

# --------------------------------------------------------------------------- 14
ws = wb.create_sheet("14_DIAGNOSTICS")
r = sheet_title(ws, "Diagnostic and qualification detail - PT08, PT09, PT10",
                "These experiments measure INSTRUMENTS, not treatments. A run-purpose firewall enforced by the record "
                "schema sets is_result=false and scored=false; they enter no numerator, denominator, dataset or power "
                "estimate and may never be promoted to confirmatory status.")
r = section(ws, r, "PER-TASK SUMMARY")
diag_rows = [
    ["PT08", "PT08 C1 difficulty diagnostic", "claude-sonnet-5", 3, 3,
     "15 of 15 acceptance cases per run", 3, 0, 0, 0.0,
     "FUNCTIONAL CEILING + ARCHITECTURE FLOOR",
     "Can an unguided C1 baseline be discriminated by PT08's architecture opportunity?",
     "PT08 = REVISE; benchmark investment = CONTINUE (SL-PT08-07)", "NO - diagnostic only"],
    ["PT09", "PT09 C1 instrument qualification", "claude-sonnet-5", 3, 3,
     "14 of 14 acceptance cases per run", 3, 0, 0, 0.0,
     "FAIL / ARCHITECTURE FLOOR",
     "Does PT09 discriminate architecture behaviour at baseline?",
     "STOP / REASSESS", "NO - qualification only"],
    ["PT10", "PT10 C1 instrument qualification", "claude-sonnet-5", 3, 3,
     "8 of 8 acceptance cases per run", 3, 1, 1, 1 / 3,
     "REVISE / WEAK PRESSURE",
     "Does PT10 discriminate architecture behaviour at baseline?",
     "STOP / REASSESS", "NO - qualification only"],
]
r = table(ws, r, ["task", "experiment", "model", "runs", "functionally valid", "acceptance detail",
                  "applicable opportunities", "violated opportunities", "target-violation runs",
                  "violation proportion", "classification", "scientific purpose", "decision", "analysis eligibility"],
          diag_rows, formats={3: FMT_INT, 4: FMT_INT, 6: FMT_INT, 7: FMT_INT, 8: FMT_INT, 9: FMT_RATIO},
          widths=[8, 32, 18, 8, 17, 28, 20, 20, 19, 17, 34, 52, 44, 22])
r = section(ws, r, "PT08 - PER-REPETITION DETAIL")
r = table(ws, r, ["repetition", "acceptance cases", "passed", "failed", "semantic passed", "functional completion",
                  "applicable", "violated", "violation proportion", "model identity", "context audit", "invocation detail"],
          [[x["label"], intn(x["acceptance_cases_total"]), intn(x["acceptance_passed"]), intn(x["acceptance_failed"]),
            intn(x["semantic_passed"]), x["functional_completion"], intn(x["architecture_applicable"]),
            intn(x["architecture_violated"]), num(x["violation_proportion"]), x["model_identity"], x["context_audit"],
            x["invocation_detail"]] for x in PT08],
          formats={1: FMT_INT, 2: FMT_INT, 3: FMT_INT, 4: FMT_INT, 6: FMT_INT, 7: FMT_INT, 8: FMT_RATIO},
          widths=[11, 17, 9, 8, 16, 20, 11, 10, 18, 15, 14, 60])
r = note(ws, r, "All three PT08 repetitions minted the identical run id (a pre-SL-RUNID-01 defect). They stayed separable "
                "only because each was given its own artifact root; distinguish them by label and session id. The "
                "artifacts keep the ids they were written with and are NOT rewritten.")
r += 1
r = section(ws, r, "PT09 / PT10 - PER-REPETITION DETAIL")
r = table(ws, r, ["task", "repetition", "acceptance cases", "passed", "failed", "semantic passed", "functional verdict",
                  "target status", "target violation", "applicable", "violated", "other raw violations",
                  "architecture verdict", "model identity", "context audit"],
          [[x["task"], intn(x["repetition"]), intn(x["acceptance_cases_total"]), intn(x["acceptance_passed"]),
            intn(x["acceptance_failed"]), intn(x["semantic_passed"]), x["functional_verdict"], x["target_status"],
            intn(x["target_violation"]), intn(x["architecture_applicable"]), intn(x["architecture_violated"]),
            intn(x["raw_other_violations_descriptive_only"]), x["architecture_verdict"], x["model_identity"],
            x["context_audit"]] for x in QUAL_RUNS],
          formats={1: FMT_INT, 2: FMT_INT, 3: FMT_INT, 4: FMT_INT, 5: FMT_INT, 8: FMT_INT, 9: FMT_INT, 10: FMT_INT, 11: FMT_INT},
          widths=[8, 11, 17, 9, 8, 16, 17, 14, 16, 11, 10, 20, 20, 15, 14], autofilter=True)
r = note(ws, r, "PT10's single violation (repetition 3) was a violation of its TARGET architecture opportunity: one "
                "forbidden import, on one line, in one already-existing file - severity blocker, confidence certain, "
                "automated. The opportunity id, the rule id, the forbidden source and target scopes and the anchor path "
                "are hidden evaluator semantics and stay in the private evaluator repository. No numeric result is withheld.")
r = note(ws, r + 1, "A fourth PT09 attempt exists and is NOT an observation: the harness could not encode the task body to "
                    "the child process stdin (UnicodeEncodeError, cp1252, U+2192), so the model received an empty prompt "
                    "and never served the request. It did not consume one of the three repetitions.")
r += 2
r = section(ws, r, "FROZEN CLASSIFICATION RULE (SL-V2-QUAL-01 section 7, frozen before the first observation)")
r = table(ws, r, ["task", "functionally valid runs", "runs", "target-violation runs", "classification", "consequence", "rule source"],
          [[x["task"], intn(x["functional_valid_runs"]), intn(x["runs"]), intn(x["target_violation_runs"]),
            x["classification"], x["consequence"], x["rule_source"]] for x in QUAL_CLASS],
          formats={1: FMT_INT, 2: FMT_INT, 3: FMT_INT}, widths=[8, 20, 8, 20, 30, 20, 56])
freeze(ws, "A5")

# --------------------------------------------------------------------------- 15
ws = wb.create_sheet("15_EXCLUSIONS")
r = sheet_title(ws, "Exclusions, invalid observations and unavailable metrics",
                f"Nothing unfavourable is omitted. Of the {INV['total_rows']} recorded run/attempt rows, 50 are eligible for any analysis "
                "at all, all 50 belong to two non-confirmatory pilots, and 0 are confirmatory.")
excl = [
    ["V1_ORIGINAL", "48", "HISTORICAL / EXPLORATORY ONLY",
     "Limitations L1-L7 plus baseline architecture leakage. Non-independent runs, no model invocation by the harness, a "
     "non-functional architecture guard, a degenerate layer metric, no acceptance oracle, and a broken deterministic "
     "install at the base tag.",
     "No v1 number may be pooled with, or contrasted against, a v2 number."],
    ["V2_PT08_DIAGNOSTIC", "3", "DIAGNOSTIC ONLY",
     "Run-purpose firewall enforced by run_record.schema.json: confirmatory_eligible, enters_confirmatory_dataset, "
     "enters_confirmatory_e1_analysis, enters_treatment_effect_analysis and enters_power_estimation are all false, plus "
     "is_result false and scored false.",
     "Exploratory observations about an INSTRUMENT, never an outcome value for PT08 and never evidence about any "
     "experimental condition."],
    ["V2_PT09_QUALIFICATION", "3", "QUALIFICATION ONLY", "Same five-flag firewall under SL-V2-QUAL-01.",
     "Does not authorise C2, C3 or C4, any condition contrast, any C1-versus-C4 comparison, any effect size, any "
     "confidence interval or any power calculation."],
    ["V2_PT09_QUALIFICATION", "1", "INFRASTRUCTURE-INVALID NON-OBSERVATION",
     "PT09 R1 attempt 1 failed with INFRA_RUNNER_CRASH: the harness could not encode the task body to the child process "
     "stdin (UnicodeEncodeError, cp1252, U+2192), so the model received an empty prompt.",
     "model_served_the_request false, is_a_substantive_observation false. It did NOT consume one of the three "
     "repetitions and was re-run under the failure re-run policy."],
    ["V2_PT10_QUALIFICATION", "3", "QUALIFICATION ONLY", "Same five-flag firewall under SL-V2-QUAL-01.", "As PT09 above."],
    ["V2_EFF_ATTEMPT1", "9", "ABORTED WHOLESALE",
     "derive_run_id omitted the reset state from the identity seed, so 36 scheduled rows collapsed to 18 run ids = 18 "
     "collision pairs. 7 intact governed observations, 2 damaged, 27 never started.",
     "No observation from execution attempt 1 may enter any efficiency analysis, under any circumstance, in whole or in "
     "part - including the 7 intact rows, because they survived by a selection mechanism nobody designed and pooling "
     "them would break the within-block pairing."],
    ["V2_EFF_ATTEMPT2", "1", "REFUSED / INFRASTRUCTURE-AFFECTED",
     "Sequence 12, PT01/C4/RESET/R1. MODEL_INVOCATION returned REFUSED with MODEL_PROCESS_FAILED: the model process "
     "exceeded 1800 s and was stopped. The operator log shows a wall clock of 14,308.7 s against an 1,800 s ceiling.",
     "No usage, no output tokens, no cost and no functional verdict exist. Its block is not paired-eligible, which also "
     "strands its otherwise-valid C1 partner (sequence 11). The artifacts record the timeout, not its cause, and this "
     "package asserts no cause."],
    ["V2_EFF_ATTEMPT2", "1", "CHECKPOINT NOT REACHED",
     "Sequence 15, PT04/C1/RESET/R1. The run completed but its governed reset checkpoint predicate was never satisfied, "
     "so the reset the row exists to carry never happened at the governed point.",
     "functional_valid false. Its block is not paired-eligible, stranding its otherwise-valid C4 partner (sequence 16). "
     "Net effect with the row above: 34 runs are individually valid but only 32 enter the 16 paired blocks."],
    ["V2_LOWER_MODEL_PILOT", "1", "FUNCTIONALLY INVALID",
     "PT04/C1/R2 failed all four of its semantic acceptance cases.",
     "Block PT04|R2 cannot be paired. It was NOT replaced: the frozen observation policy consumes a substantive "
     "observation once the real task is delivered and explicitly forbids replacing one because it failed functionality."],
    ["V2_LOWER_MODEL_PILOT", "1", "VALID BUT UNPAIRED",
     "The C4 partner of PT04/C1/R2 is a complete, functionally valid observation with no comparator.",
     "Excluded from every efficiency ratio. It is not deleted and not counted as a failure."],
]
r = section(ws, r, "EXCLUDED AND INVALID OBSERVATIONS")
r = table(ws, r, ["experiment", "rows", "category", "why", "consequence"], excl,
          widths=[26, 7, 38, 82, 82], autofilter=True)
r = section(ws, r, "METRICS THAT DO NOT EXIST, BY EXPERIMENT")
r = table(ws, r, ["experiment", "missing metric", "why it is missing", "how it is recorded"], [
    ["V1_ORIGINAL", "tokens, wall time, provider cost, tool calls, architecture",
     "v1 predates efficiency instrumentation entirely, and its architecture guard never fired.",
     "Blank cells. NOT estimated and NOT zero."],
    ["V2_PT08 / PT09 / PT10", "tokens, provider cost, tool calls, LOC churn, MODEL_WALL_SECONDS",
     "Those purposes never captured them. total_run_seconds is a process wall clock parsed from free-text invocation "
     "detail, not the governed time endpoint.",
     "model_wall_seconds deliberately blank; total_run_seconds carries the process figure."],
    ["V2_EFF_ATTEMPT2", "architecture, LOC churn",
     "AFCI_EFFICIENCY_PILOT is a cost-only purpose under its own frozen governance.",
     "Architecture columns blank for all 36 rows - not zero. No architecture claim may be derived from this pilot."],
    ["V2_EFF_ATTEMPT2", "output tokens and provider cost for RESET runs",
     "A reset run's phase A is deliberately interrupted at the checkpoint, BEFORE its terminal result event, which is the "
     "only place the runtime reports output tokens and cost. Input tokens are still EXACT, reconstructed from the "
     "streamed assistant messages.",
     "WITHHELD, not zero and not estimated. Output tokens n=9 and cost n=9, both NON_RESET only, against 16 for the "
     "primary endpoint. 17 of 36 rows carry no provider cost."],
    ["V2_EFF_ATTEMPT2", "TEST_COMMAND_RUNS as a paired endpoint",
     "No C1 run issued an agent-initiated test command, so every ratio is undefined.",
     "0 defined pairs. Reported as NOT CAPTURED, not as 0.0."],
    ["V2_LOWER_MODEL_PILOT", "reset recovery",
     "NON_RESET only by design, so that model capability is the single moderator varied.",
     "NOT APPLICABLE. The pilot is excluded from sheet 11 entirely."],
    ["V2_LOWER_MODEL_PILOT", "failed test-or-CI cycle count",
     "The lower-model raw metrics table records CI and test command counts but no failed-cycle count.",
     "NOT CAPTURED in sheet 10, rather than inferred from CI command runs."],
], widths=[26, 46, 90, 82])
r = section(ws, r, "PROGRAMME-WIDE LIMITATIONS THAT BOUND EVERY FIGURE IN THIS PACKAGE")
r = table(ws, r, ["#", "limitation"], [
    [1, "NO CONFIRMATORY EVIDENCE EXISTS. Confirmatory evidence collection has not begun. The suite-wide protocol is "
        "PRE-FREEZE, gate G1 is not passed, and TD-B32, TD-B34, TD-B03 and TD-B19 all remain open."],
    [2, "NO STATISTICAL INFERENCE OF ANY KIND. No p-value, confidence interval, effect size or power estimate exists "
        "anywhere in this programme, and no power calculation has ever been run. Every reported ratio is a median of "
        "paired ratios, a descriptive statistic. With 16, 8 and 3 paired blocks and 3 repetitions, nothing else would "
        "be defensible."],
    [3, "ONE SYNTHETIC SUBSTRATE. Every v2 run used one governed substrate: 49 files, a synthetic Nx monorepo whose "
        "layering is inferable from its own import graph and path aliases. A model can often deduce the intended "
        "architecture WITHOUT the MAD, which directly attacks the MAD's marginal value - the thing the study measures. "
        "This is the primary external-validity threat to every v2 finding."],
    [4, "NO STUDY MODEL HAS BEEN SELECTED. primary_model is still null (TD-B03 open), so claude-sonnet-5 and "
        "claude-haiku-4-5-20251001 are both provisional."],
    [5, "THE EVIDENCE BASE IS LOPSIDED. The study's actual construct - architectural conformance - has been measured only "
        "by instruments that all sat at or near the floor, while its secondary construct - cost - has one clean pilot. "
        "The cost result must not be allowed to stand in for an architecture result."],
    [6, "THIS PACKAGE IS A SECONDARY ARTIFACT. Where it and a primary artifact disagree, the primary artifact wins."],
], widths=[5, 150])
freeze(ws, "A5")

# --------------------------------------------------------------------------- 16
ws = wb.create_sheet("16_DECISION_MATRIX")
r = sheet_title(ws, "Frozen decision rules and their outcomes",
                "Every rule below was frozen BEFORE the data it judges existed, and none was changed afterwards.")
THRESHOLD_RE = __import__("re").compile(
    r"(<=\s*[\d.]+%?|>=\s*[\d.]+%?|<\s*[\d.]+%?|>\s*[\d.]+%?|at least \d+[^,;]*|at most \d+[^,;]*)")


def threshold_of(text):
    m = THRESHOLD_RE.search(text)
    return m.group(1).strip() if m else "(qualitative - see criterion)"


r = section(ws, r, "SONNET EFFICIENCY PILOT - AFCI_EFFICIENCY_PILOT_DECISION.md sections 10-11")
r = table(ws, r, ["branch", "criterion", "threshold / requirement", "observed value", "verdict"],
          [[c["rule_branch"], c["clause"], threshold_of(c["clause"] + " " + c["detail"]), c["detail"],
            "PASS" if c["satisfied"] == "true" else "FAIL"] for c in A2_CLAUSES],
          widths=[24, 60, 34, 60, 12], autofilter=True)
r = table(ws, r, ["outcome", "rule", "efficiency claim made"],
          [[A2_REPORT["decision"]["outcome"].replace("\u2014", "-"), A2_REPORT["decision"]["rule"],
            str(A2_REPORT["decision"]["efficiency_claim_made"]).upper()]], widths=[64, 10, 22])
r = note(ws, r, "Both functional guardrails and the minimum-pairs gate PASSED. Every token and secondary-endpoint "
                "threshold FAILED. The RESET-SPECIFIC GO branch failed only on its overall token clause - its two "
                "reset-overhead clauses passed.", ROSE)
r += 1
r = section(ws, r, "LOWER-MODEL PILOT - SL-V2-LOWER-MODEL-01 section 12")
lm_rows = [[c["signal"], c["clause"], threshold_of(c["clause"] + " " + c["observed"]), c["observed"], c["verdict"]]
           for c in LM_CLAUSES]
r = table(ws, r, ["signal", "criterion", "threshold / requirement", "observed value", "verdict"], lm_rows,
          widths=[22, 58, 34, 90, 12])
r = table(ws, r, ["quality signal", "efficiency signal", "expansion authorised", "outcome"],
          [[str(LM_REPORT["decision"]["quality_signal"]).upper(),
            str(LM_REPORT["decision"]["efficiency_signal"]).upper(),
            str(LM_REPORT["decision"]["expansion_authorised"]).upper(),
            "NO LOWER-MODEL SIGNAL - DO NOT EXPAND THE SYNTHETIC LOWER-MODEL MATRIX"]],
          widths=[18, 20, 22, 72])
r = note(ws, r, "Criterion 12.1.1 fails on a TIE AT ZERO, not on C4 being worse. Both arms recorded 0 target violations "
                "across 9 runs each. The frozen rule requires STRICTLY FEWER violations, so a tie scores FAIL - that is a "
                "rule outcome, not a finding about AFCI. The quality channel produced NO INFORMATION.", AMBER)
r += 1
r = section(ws, r, "WHAT THE LOWER-MODEL DECISION DOES NOT DO")
r = table(ws, r, ["point"], [
    [LM_REPORT["decision"]["open_source_study"]],
    ["Channels were never combined into one score: " + str(LM_REPORT["decision"]["channels_combined_into_one_score"]).upper()],
    ["p-values: " + LM_REPORT["decision"]["p_values"] + "; confidence intervals: " +
     LM_REPORT["decision"]["confidence_intervals"] + "; confirmatory effect claim: " +
     LM_REPORT["decision"]["confirmatory_effect_claim"]],
], widths=[170])
freeze(ws, "A5")

# --------------------------------------------------------------------------- 17
ws = wb.create_sheet("17_METRIC_AVAILABILITY")
r = sheet_title(ws, "Metric availability by experiment",
                "AVAILABLE = measured and usable. NOT CAPTURED = never measured. INVALID FOR INFERENCE = a number exists "
                "but does not measure what it claims to. EXCLUDED = the experiment is excluded wholesale.")
AV = [
    ("functional", "NOT CAPTURED", "AVAILABLE", "AVAILABLE", "AVAILABLE", "EXCLUDED", "AVAILABLE", "AVAILABLE"),
    ("architecture", "INVALID FOR INFERENCE", "AVAILABLE", "AVAILABLE", "AVAILABLE", "EXCLUDED", "NOT CAPTURED", "AVAILABLE"),
    ("input tokens", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "EXCLUDED", "AVAILABLE", "AVAILABLE"),
    ("output tokens", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "EXCLUDED",
     "AVAILABLE (NON_RESET only)", "AVAILABLE"),
    ("provider cost", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "EXCLUDED",
     "AVAILABLE (NON_RESET only)", "AVAILABLE"),
    ("wall time", "NOT CAPTURED", "AVAILABLE (process clock only)", "AVAILABLE (process clock only)",
     "AVAILABLE (process clock only)", "EXCLUDED", "AVAILABLE", "AVAILABLE"),
    ("exploration", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "EXCLUDED", "AVAILABLE", "AVAILABLE"),
    ("tools", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "EXCLUDED", "AVAILABLE", "AVAILABLE"),
    ("unique files", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "EXCLUDED", "AVAILABLE", "AVAILABLE"),
    ("rework", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "EXCLUDED",
     "AVAILABLE (no LOC churn)", "AVAILABLE"),
    ("code churn", "AVAILABLE", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "EXCLUDED", "NOT CAPTURED", "AVAILABLE"),
    ("test churn", "AVAILABLE", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "EXCLUDED", "NOT CAPTURED", "NOT CAPTURED"),
    ("reset recovery", "AVAILABLE (different construct)", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "EXCLUDED",
     "AVAILABLE", "NOT APPLICABLE (NON_RESET only)"),
    ("CI", "AVAILABLE (saturated 100%)", "NOT CAPTURED", "NOT CAPTURED", "NOT CAPTURED", "EXCLUDED",
     "AVAILABLE (as a tool-call count)", "AVAILABLE (as a tool-call count)"),
]
r = table(ws, r, ["metric", "V1", "PT08", "PT09", "PT10", "Sonnet Attempt 1", "Sonnet Attempt 2", "Haiku lower-model"],
          [list(x) for x in AV], widths=[18, 30, 30, 30, 30, 14, 32, 32], autofilter=True)
r = note(ws, r, "V1 architecture is INVALID FOR INFERENCE rather than NOT CAPTURED: a number exists (all zeros) but the "
                "guard's regexes never fired, so it measures nothing. Those zeros are not measurements and this package "
                "carries blanks in their place.")
r = note(ws, r + 1, "V1 CI is AVAILABLE but saturated at 100% across all 48 cells, so it does not discriminate task success.")
freeze(ws, "B5")

# --------------------------------------------------------------------------- 18
ws = wb.create_sheet("18_EVIDENCE_MAP")
r = sheet_title(ws, "Evidence map - summary number to raw artifact",
                "Professor-safe traceability. Every chain stops at the private boundary, and it stops at a FIELD, not at "
                "its value: no private evaluator identifier appears anywhere in this package.")
EV = [
    ["Median C4/C1 input tokens = 1.4014 (Sonnet)",
     "study-results/05_efficiency_attempt_2_completed/attempt2_endpoint_ratios.csv -> attempt2_primary_pairs.csv (16 rows) "
     "-> efficiency_pilot_frozen_analysis_report.json (primary_endpoint.pairs)",
     "AFCI_MASTER_RUN_RESULTS.csv, experiment_id = V2_EFF_ATTEMPT2 (36 rows)",
     "D:\\afci-runs\\attempt-2\\<run_id>\\run_record.json -> efficiency.usage.TOTAL_INPUT_TOKENS -> "
     "runtime_evidence.jsonl terminal result event",
     "run plan sha256 0038cd8b563ea804f4887d21cb37ceddb3a8f7632c4dd2315c260d3a9af95767",
     "VERIFIED - recomputed from the run rows in 20_RECOMPUTATION_AUDIT"],
    ["Median C4/C1 input tokens = 2.0372 (Haiku)",
     "study-results/06_lower_model_pilot_completed/lower_model_endpoint_ratios.csv -> lower_model_primary_pairs.csv "
     "(8 rows) -> lower_model_pilot_frozen_analysis_report.json (efficiency.endpoints.TOTAL_INPUT_TOKENS.pairs)",
     "AFCI_MASTER_RUN_RESULTS.csv, experiment_id = V2_LOWER_MODEL_PILOT (18 rows)",
     "D:\\afci-runs\\lower-model-pilot\\<run_id>\\run_record.json -> efficiency.usage.TOTAL_INPUT_TOKENS -> "
     "runtime_evidence.jsonl terminal result event",
     "run plan sha256 f045c0d93370f7e6f785274acd7df6b34bb28f52ba60cdcfd49eb6812b86b026",
     "VERIFIED - recomputed from the run rows"],
    ["Haiku architecture 0 violations in both arms",
     "study-results/06_lower_model_pilot_completed/lower_model_architecture_summary.csv -> frozen analysis report, "
     "architecture.overall",
     "AFCI_MASTER_RUN_RESULTS.csv, architecture_applicable / architecture_violated columns (18 rows)",
     "D:\\afci-runs\\lower-model-pilot\\<run_id>\\architecture_evaluation_result.json",
     "prepared worktree content hash da7a679552d50857408d14e980cc5257ed42e33d7116630433f8451450d1bad6 (49 entries)",
     "VERIFIED - recomputed from the run rows"],
    ["PT10 target violation in 1 of 3 runs",
     "study-results/03_pt09_pt10_qualification/qualification_classification.csv -> qualification_runs.csv (row PT10, 3)",
     "AFCI_MASTER_RUN_RESULTS.csv, experiment_id = V2_PT10_QUALIFICATION",
     "D:\\afci-v2-qual\\score\\pt10-r3.json -> architecture.target_findings[0]; captured worktree under "
     "...pt10-c1-real-r3-8f809ab6ee92\\worktree_post_run\\",
     "task sha256 1b1fe29881b3c9f309939df042272b03164fb3baae878c64345e75edddf36b86",
     "VERIFIED to the FIELD. The field's VALUE resolves to a private finding id and stays in the private evaluator repository."],
    ["PT08 0 violations in 3 of 3 runs",
     "study-results/02_pt08_diagnostic/pt08_diagnostic_runs.csv",
     "AFCI_MASTER_RUN_RESULTS.csv, experiment_id = V2_PT08_DIAGNOSTIC",
     "D:\\pt08-diagnostic\\scoring\\R{1,2,3}\\scoring_summary.json and architecture_finding.json",
     "task sha256 a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2; diagnostic-scoped evaluator mount "
     "9fdbb347aa936ddc98d19737937b954c0a925ab1e13ace6c385dce0b8bb098dc",
     "VERIFIED"],
    ["V1 code churn +65.7%",
     "study-results/01_v1_original_study/v1_headline_recomputed.csv -> v1_taskwise_churn_recomputed.csv",
     "AFCI_MASTER_RUN_RESULTS.csv, experiment_id = V1_ORIGINAL (48 rows)",
     "git branch rerun-v1-opus7-artifacts: experiments/paper/results_v1.csv, columns code_additions + code_deletions; "
     "per-run experiments/runs_v1/<TASK>/<COND>/metrics.json",
     "results_v1.csv git blob 0d350eb262b49385f290d0a9df6693b34ba3d919",
     "VERIFIED - but HISTORICAL ONLY (limitations L1-L7)"],
    ["Sonnet NON_RESET provider cost ratio 1.4928",
     "study-results/05_efficiency_attempt_2_completed/attempt2_provider_cost.csv (9 rows + median)",
     "AFCI_MASTER_RUN_RESULTS.csv, provider_cost_usd column, 19 of 36 rows populated",
     "D:\\afci-runs\\attempt-2\\<run_id>\\runtime_evidence.jsonl terminal result event",
     "execution plan sha256 562415031c04b0673c54ac352a4ca35a66e885023aa212cedc284da0c65a087e",
     "VERIFIED - NON_RESET only; there is no RESET cost comparison"],
    ["Attempt 1 aborted, 18 identity collisions",
     "study-results/04_efficiency_attempt_1_aborted/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_EVIDENCE_INVENTORY.json",
     "AFCI_MASTER_RUN_RESULTS.csv, experiment_id = V2_EFF_ATTEMPT1 (9 rows)",
     "D:\\afci-runs\\obs\\...; operator logs D:\\afci-runs\\logs\\seq-0{1..9}.log",
     "evidence inventory sha256 9985860fb3b7a5842e676cc1c66c876e712ea93a196999457d711332ba12683f",
     "VERIFIED - and excluded wholesale. No analysis was ever performed."],
]
r = table(ws, r, ["summary result", "analysis artifact", "run record", "raw artifact reference", "hash / SHA", "status"],
          EV, widths=[44, 70, 50, 74, 62, 60], autofilter=True)
r = section(ws, r, "REPOSITORY AND GOVERNANCE ANCHORS")
r = table(ws, r, ["what", "value"], [
    ["public repo branch", GIT["branch"]],
    ["evidence commit (last change to study-results/ outside this package)", GIT["evidence_commit"]],
    ["  that commit's subject", GIT["evidence_subject"]],
    ["public repo origin", GIT["origin"]],
    ["public repo main (v1 base, tag paper-v0)", "2adc8741acad7ea5423f0bf3d9ad821ff023a35f"],
    ["private evaluator repo HEAD (result provenance only; never pushed)",
     "9b047bed21e3c6c2169345322b9b14dfe80f56ee"],
    ["governed substrate commit", "630d3180af0d02a86330dfb599f559e78df65e94"],
    ["governed substrate content hash", "0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3 (49 entries)"],
    ["the MAD - docs/v2/ARCHITECTURE_CONTEXT.md", "bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d"],
    ["v1 release", "GitHub ase2026-artifacts-v1 @ 1ba21ad75dacbac5eb87d354a490b088078c30da"],
    ["v1 DOI", "10.5281/zenodo.19757261"],
], widths=[48, 76])
r = section(ws, r, "TASK BODY HASHES (public)")
r = table(ws, r, ["task", "sha256", "used by"], [
    ["PT01", "6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39", "efficiency pilot; lower-model pilot"],
    ["PT04", "f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5", "efficiency pilot; lower-model pilot"],
    ["PT07", "557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7", "efficiency pilot; lower-model pilot"],
    ["PT08", "a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2", "PT08 diagnostic"],
    ["PT09", "bac32dc0e7163c9ab1816ac6eea6c98738092cca5cf56715e280f1ec1c0ac44c", "qualification"],
    ["PT10", "1b1fe29881b3c9f309939df042272b03164fb3baae878c64345e75edddf36b86", "qualification"],
], widths=[8, 70, 40])
r = note(ws, r, "WHAT IS WITHHELD: private opportunity identifiers, rule identifiers, forbidden source and target scopes, "
                "anchor paths and hidden acceptance case semantics. They live in the private evaluator repository and the "
                "run record refuses to carry them at all. NO NUMERIC RESULT IS WITHHELD.")
r = note(ws, r + 1, "No digest is published in place of a withheld identifier: the public rule catalog and the public corpus "
                    "together bound the preimage space to a few thousand candidates, so any such digest would be "
                    "recoverable by enumeration. Traceability instead runs through run ids, task hashes and evaluator "
                    "manifest digests, which are already public and already high-entropy.")
freeze(ws, "A5")

# --------------------------------------------------------------------------- 19
ws = wb.create_sheet("19_METRIC_DEFINITIONS")
r = sheet_title(ws, "Metric definitions in plain English",
                "Read this before any matrix sheet. Direction is stated for every ratio.")
DEFS = [
    ["TOTAL_INPUT_TOKENS", "PRIMARY cost endpoint",
     "Every input token the model was charged for on a run: input_tokens + cache_creation_input_tokens + "
     "cache_read_input_tokens. The MAD's own tokens and all cache traffic are INSIDE this number and are never removed - "
     "removing them would be measuring a cheaper experiment than the one that was run.",
     "Lower is better. For reset runs it is still EXACT, reconstructed from the streamed assistant messages."],
    ["TOKEN_RATIO", "derived",
     "Within one block (same task, same reset state, same repetition), the C4 run's TOTAL_INPUT_TOKENS divided by the C1 "
     "run's. The headline figure is the MEDIAN of those per-block ratios, not a ratio of totals.",
     "1.00 is parity. Below 1.00 means the explicit MAD made the run cheaper; above 1.00 means it made it more expensive."],
    ["TOTAL_OUTPUT_TOKENS", "secondary",
     "Tokens the model produced. Reported only where a terminal result event exists.",
     "Lower is better. WITHHELD (not zero) for reset runs."],
    ["MODEL_WALL_SECONDS", "secondary",
     "Wall-clock seconds inside the model invocation itself - the governed time endpoint. Distinct from "
     "TOTAL_RUN_SECONDS, which is the harness's own wall clock around the invocation and is not an endpoint.",
     "Lower is better."],
    ["EXPLORATION_CALLS", "secondary",
     "Read + grep + glob tool calls: how much the agent looked around before and while acting. This is the metric that "
     "would fall first if an explicit architecture document actually saved the agent from having to discover the "
     "architecture.",
     "Lower is better."],
    ["TOTAL_TOOL_CALLS", "secondary", "Every tool call the agent made on the run, of any kind.", "Lower is better."],
    ["UNIQUE_FILES_READ", "secondary",
     "The number of DISTINCT files the agent opened. Reading one file ten times counts once.", "Lower is better."],
    ["EDIT_AND_WRITE_CALLS", "secondary", "Edit tool calls plus write tool calls: how much the agent changed things.",
     "Lower is better, but only weakly - a run that edits more may simply be implementing more."],
    ["FILES_REEDITED", "descriptive",
     "How many distinct files the agent edited MORE THAN ONCE in a single run. A proxy for rework: going back to a file "
     "usually means the first attempt was not right.",
     "Lower is better. No frozen paired endpoint is defined on it."],
    ["UNIQUE_FILES_MODIFIED vs FILES_CHANGED", "descriptive",
     "UNIQUE_FILES_MODIFIED counts files targeted by an edit or write TOOL CALL. FILES_CHANGED counts files that actually "
     "DIFFER in the captured worktree at the end. They are different measurements and can disagree - on Haiku PT07/C1/R2 "
     "six files were written but only four ended up different.",
     "Reported separately, never merged."],
    ["CI_COMMAND_RUNS / TEST_COMMAND_RUNS", "descriptive",
     "How many times the agent itself invoked the project's CI or test command. These are TOOL-CALL COUNTS, not pass/fail "
     "outcomes, and they are not the v1 'CI success' metric.",
     "No direction is claimed. A ratio is undefined when the C1 run issued none."],
    ["PROVIDER_COST_USD", "secondary",
     "The provider-reported USD cost of the run, taken exactly as the runtime reported it in the terminal result event. "
     "Never modelled, never back-computed from token counts, never estimated.",
     "Lower is better. A run with no terminal result event has NO cost, and that cell is blank - never 0."],
    ["FUNCTIONAL_VALID", "quality gate",
     "The hidden acceptance oracle's verdict on whether the run actually did the task: "
     "record.functional_evaluation.functional_valid, and nowhere else. It is NEVER inferred from CI success, from the "
     "model's own prose, from exit status alone, from any architecture score, or from the number of files changed.",
     "TRUE or FALSE. A blank means no verdict exists for that run at all."],
    ["architecture applicable / violated", "quality endpoint",
     "APPLICABLE counts the architecture opportunities that the run's own changes made relevant - the decision points "
     "where the run could have got the architecture right or wrong. VIOLATED counts how many of those it got wrong. "
     "TARGET-VIOLATION RUNS counts runs that violated the specific opportunity the task was built to expose.",
     "Lower violated is better. The identifiers behind these counts are hidden evaluator semantics and stay private; the "
     "counts themselves are fully published."],
    ["architecture FLOOR", "reading",
     "Both arms recorded ZERO violations, so there was nothing for the treatment to improve. The frozen rule scores this "
     "FAIL because it requires strictly fewer violations and a tie at zero is not an improvement.",
     "A floor is NO INFORMATION. It is not evidence that the MAD fails to improve architecture."],
    ["reset overhead", "derived",
     "A run's metric under RESET divided by the same task and condition WITHOUT reset. It asks what a mid-task context "
     "loss costs, rather than what the task costs.",
     "Lower overhead is better. C4's overhead being lower than C1's means the explicit MAD made recovery cheaper."],
    ["paired block", "unit of analysis",
     "One task x reset state x repetition cell, holding exactly one C1 run and one C4 run. A block is paired-eligible "
     "only when BOTH of its runs are functionally valid - a cost figure from a run that did not work is not a cheaper way "
     "of doing the task.",
     "One invalid run removes the whole block, which is why 34 individually valid Sonnet runs yield 16 pairs, not 17."],
    ["C1 / C4", "conditions",
     "C1 gives the model the task and nothing else. C4 gives it the same task PLUS the explicit Machine-readable "
     "Architecture Document. Everything else - substrate, tooling, turn budget, model, runtime - is held identical.",
     "The whole study is the difference between these two."],
]
r = table(ws, r, ["term", "role", "what it means", "direction and caveats"], DEFS,
          widths=[38, 20, 96, 84], autofilter=True)
freeze(ws, "A5")

# --------------------------------------------------------------------------- 20
ws = wb.create_sheet("20_RECOMPUTATION_AUDIT")
r = sheet_title(ws, "Recomputation audit",
                "Every headline figure in this package was recomputed from the run/attempt rows and then compared against "
                "the frozen per-experiment analysis artifact. This sheet is that comparison, published rather than asserted.")
r = table(ws, r, ["result", "count"], [
    ["Checks performed", len(AUDIT)],
    ["MATCH", sum(1 for a in AUDIT if a["status"] == "MATCH")],
    ["MISMATCH", len(AUDIT_MISMATCHES)],
], formats={1: FMT_INT}, widths=[40, 10])
r = section(ws, r, "EVERY CHECK")
r = table(ws, r, ["check", "value in the frozen analysis artifact", "value recomputed from the run rows", "status"],
          [[a["check"], str(a["frozen_artifact_value"]), str(a["recomputed_from_run_rows"]), a["status"]] for a in AUDIT],
          widths=[76, 36, 36, 12], autofilter=True)
r = section(ws, r, "SCOPE NOTES - where a figure elsewhere in the evidence package is stated at a different scope")
r = table(ws, r, ["figure", "this package reports", "note"], [
    ["Haiku CI command runs, C1 vs C4",
     f"over the 8 PAIRED BLOCKS: C1 {int(HAI_REWORK['C1']['ci_command_runs'])}, "
     f"C4 {int(HAI_REWORK['C4']['ci_command_runs'])}. Over ALL 9 runs per arm: "
     f"C1 {int(ARM_TOTALS[('Haiku', 'C1')]['ci_command_runs'])}, "
     f"C4 {int(ARM_TOTALS[('Haiku', 'C4')]['ci_command_runs'])}. Both scopes are stated, and neither is mixed.",
     "AFCI_RESULTS_SUMMARY.md reports 'C4 needed fewer failed CI cycles (9 vs 13)'. Two things differ here. First, the "
     "lower-model evidence carries a CI COMMAND COUNT, not a failed-cycle count, so this package reports it as a command "
     "count; the Sonnet pilot does record a genuine FAILED_TEST_OR_CI_CYCLES figure "
     f"(C1 {int(SON_REWORK['C1']['failed_ci_cycles'])}, C4 {int(SON_REWORK['C4']['failed_ci_cycles'])} over 16 blocks) "
     "and that is reported as one. Second, '9 vs 13' takes its two numbers from different scopes: 9 is C4 over all 9 "
     "runs and 13 is C1 over the 8 paired blocks. Held to one scope the pair is 8 vs 13 (paired) or 9 vs 15 (all runs). "
     "The direction is the same either way; the magnitude is not."],
    ["Haiku 'files changed', C1 25 vs C4 30",
     "reported as FILES_CHANGED (worktree diff), and UNIQUE_FILES_MODIFIED (tool-call count) is reported beside it as a "
     f"separate metric: C1 {int(HAI_REWORK['C1']['unique_files_modified'])}, C4 {int(HAI_REWORK['C4']['unique_files_modified'])}",
     "The two disagree on PT07/C1/R2 (6 files written, 4 files different). Merging them would misreport one of the two."],
    ["Sonnet reset-overhead scope", "16 of 18 repetition pairs",
     "A repetition contributes only when BOTH of its runs are functionally valid, which drops PT01/C4/R1 and PT04/C1/R1. "
     "Including them changes PT04's C1 overhead, so the scope is stated rather than assumed."],
    ["Sonnet block count", "19 observed blocks against 18 scheduled",
     "The refused record (sequence 12) carries no reset state, so it forms its own block key. The frozen analysis sees "
     "the same 19. The row is preserved exactly as recorded and is not repaired."],
], widths=[38, 76, 110])
freeze(ws, "A5")

# Excel allows one auto-filter per sheet. Sheets built from stacked sections get
# theirs on the first table; the narrative summary sheet gets none, deliberately.
for name in wb.sheetnames:
    sh = wb[name]
    if not sh.auto_filter.ref and name != "01_EXECUTIVE_SUMMARY" and name in FIRST_TABLE:
        sh.auto_filter.ref = FIRST_TABLE[name]

XLSX = OUT / "AFCI_Professor_Results.xlsx"

# Fixed document properties. openpyxl stamps the current clock into
# docProps/core.xml, which would make every rebuild of an unchanged workbook
# produce different bytes.
_stamp = datetime.datetime(int(COMPILED[:4]), int(COMPILED[5:7]), int(COMPILED[8:10]))
wb.properties.creator = "AFCI-Bench study-results"
wb.properties.lastModifiedBy = "AFCI-Bench study-results"
wb.properties.title = "AFCI-Bench - professor results delivery"
wb.properties.description = (
    f"All AFCI experiments to date. Compiled {COMPILED} from study-results/. "
    "Reporting only; no benchmark observation was executed.")
wb.properties.created = _stamp
wb.properties.modified = _stamp
wb.save(XLSX)


def normalize_xlsx(path):
    """Rewrite the .xlsx zip with fixed member timestamps.

    An .xlsx is a zip, and a zip records a modification time per member. Without
    this, rebuilding an unchanged workbook produces different bytes, so a reader
    who regenerates the package to check it sees a 100 KB binary diff that means
    nothing. Content, order and compression are untouched."""
    import io
    import re as _re
    import zipfile
    stamp = f"{COMPILED}T00:00:00Z".encode()
    src = path.read_bytes()
    buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(src)) as zin, zipfile.ZipFile(buf, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "docProps/core.xml":
                # openpyxl rewrites dcterms:modified with the wall clock at save
                # time whatever wb.properties says, so pin both timestamps here.
                # \g<1> rather than \1: the replacement is immediately followed by
                # a digit, and \1 + "2..." parses as backreference 12.
                for tag in (b"created", b"modified"):
                    data = _re.sub(rb"(<dcterms:" + tag + rb"[^>]*>)[^<]*(</dcterms:" + tag + rb">)",
                                   rb"\g<1>" + stamp + rb"\g<2>", data)
            fixed = zipfile.ZipInfo(info.filename, date_time=(1980, 1, 1, 0, 0, 0))
            fixed.compress_type = info.compress_type
            fixed.external_attr = info.external_attr
            fixed.internal_attr = info.internal_attr
            fixed.create_system = 0
            zout.writestr(fixed, data)
    path.write_bytes(buf.getvalue())


normalize_xlsx(XLSX)
WRITTEN.append(XLSX)
print(f"wrote {XLSX}")


# =========================================================================== #
#                            FULL RUN CSV EXPORT
# =========================================================================== #

# =========================================================================== #
#                              MARKDOWN WRITERS
# =========================================================================== #


def fnum(v, dp=4):
    return "n/a" if v is None else f"{v:,.{dp}f}"


def fint(v):
    return "n/a" if v is None else f"{int(round(v)):,}"


def fusd(v, dp=4):
    return "n/a" if v is None else f"${v:,.{dp}f}"


def ratio_line(label, src, metric):
    e = src[metric]
    tm = e["task_medians"]
    return (f"| {label} | {e['n']} | {fnum(e['median'])} | {e['c4_lower_count']}/{e['n']} | "
            f"{fnum(tm.get('PT01'))} | {fnum(tm.get('PT04'))} | {fnum(tm.get('PT07'))} |")


SUMMARY = f"""# AFCI-Bench - results delivery

**Compiled {COMPILED}** from `study-results/` on branch `{GIT['branch']}`, pinned to evidence
commit `{GIT['evidence_commit'][:12]}` (*{GIT['evidence_subject']}*) - the last change to the
evidence this package reports.

Reporting and export only. No benchmark observation was executed to produce this
package, no model was invoked, and no task definition, architecture document,
scorer, threshold, run plan, condition, raw run artifact or prior analysis was
changed. Every figure below was recomputed from the {INV['total_rows']} run/attempt
rows and then checked against the frozen per-experiment analysis artifacts:
**{len(AUDIT)} checks, {len(AUDIT_MISMATCHES)} mismatches**. The full check list is in
the workbook sheet `20_RECOMPUTATION_AUDIT`.

Claims are tagged **[FACT]** (a measured value, reproducible from the artifacts),
**[INTERPRETATION]** (a reading of those facts) and **[LIMITATION]** (a bound on
what the facts can support).

---

## 1. Study objective

AFCI asks a narrow question. If you hand a coding agent an explicit,
machine-readable description of a repository's architecture - the MAD - does it
build better, or more cheaply, than an agent given the task alone?

The programme operationalises that as two conditions held identical in every
other respect:

- **C1** - the task, and nothing else.
- **C4** - the same task, plus the explicit Machine-readable Architecture Document.

Two constructs are measured, and they are never combined into one score:

- **architectural conformance** - does the run violate the architecture
  opportunities its own changes made relevant? This is the study's actual
  construct.
- **efficiency** - tokens, wall time, exploration, tool effort and provider cost.
  This is the secondary construct, and it is the one with a clean pilot.

---

## 2. Experiments conducted

| # | experiment | model | runs | status | decision |
| --- | --- | --- | ---: | --- | --- |
| 1 | V1 original study | "Opus 7" | 48 | COMPLETE, PUBLISHED, superseded | published, then superseded by v1 limitations L1-L7 |
| 2 | PT08 C1 difficulty diagnostic | claude-sonnet-5 | 3 | COMPLETE | PT08 = REVISE; benchmark investment = CONTINUE |
| 3 | PT09 instrument qualification | claude-sonnet-5 | 3 (+1 infra-invalid) | COMPLETE | FAIL / ARCHITECTURE FLOOR -> STOP / REASSESS |
| 4 | PT10 instrument qualification | claude-sonnet-5 | 3 | COMPLETE | REVISE / WEAK PRESSURE -> STOP / REASSESS |
| 5 | Efficiency pilot, Attempt 1 | claude-sonnet-5 | 9 attempted of 36 | ABORTED | excluded wholesale; no analysis was ever performed |
| 6 | Efficiency pilot, Attempt 2 | claude-sonnet-5 | 36 | COMPLETE | STOP - NO EFFICIENCY SIGNAL JUSTIFIES FULL-SUITE EXPANSION |
| 7 | Lower-capability model pilot | claude-haiku-4-5-20251001 | 18 | COMPLETE | NO LOWER-MODEL SIGNAL - DO NOT EXPAND THE SYNTHETIC LOWER-MODEL MATRIX |
| 8 | Backstage real-repository pilot, Attempt 1 | claude-sonnet-5 | 7 attempted of 18 | HALTED | excluded wholesale; no analysis was ever performed |
| 9 | Backstage real-repository pilot, Attempt 2 | claude-sonnet-5 | 18 | COMPLETE | NO ARCHITECTURE SIGNAL - DO NOT AUTOMATICALLY EXPAND |
| 10 | Open-source complexity study | TBD | 0 | **NOT STARTED** | none - no runs exist and no result is pre-populated |

All three completed pilots were judged by a decision rule frozen **before** the
data they judge existed, and all three rules returned a negative verdict. None
was changed afterwards.

---

## 3. Evidence and run inventory

**[FACT]** Mechanically counted from `AFCI_MASTER_RUN_RESULTS.csv`.

| measure | count |
| --- | ---: |
| total run/attempt records | {INV['total_rows']} |
| distinct run identities | {INV['unique_run_ids']} |
| completed observations | {INV['completed']} |
| functionally valid observations | {INV['functional_valid']} |
| explicitly functionally invalid | {INV['functional_invalid']} |
| no functional verdict captured at all | {INV['functional_not_captured']} |
| diagnostic / qualification observations | {INV['diagnostic_qualification']} |
| infrastructure-invalid or damaged records | {INV['infra_invalid_or_damaged']} |
| refused | {INV['refused']} |
| excluded from every analysis | {INV['excluded']} |
| eligible for any analysis | {INV['eligible']} |
| **confirmatory observations** | **0** |

The three "missing" run identities are not a bookkeeping error: the PT08
diagnostic minted one run id for all three of its repetitions, and one Attempt-1
collision pair shares a single id. Both are recorded defects, kept as found.

| experiment | rows | status COMPLETE | functionally valid | eligible | token coverage | cost coverage | architecture coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
""" + "\n".join(
    f"| `{p['experiment_id']}` | {p['rows']} | {p['completed']} | "
    f"{p['functional_valid'] if p['functional_not_captured'] != p['rows'] else 'not captured'} | "
    f"{p['eligible']} | {p['token_coverage']}/{p['rows']} | {p['cost_coverage']}/{p['rows']} | "
    f"{p['architecture_coverage']}/{p['rows']} |"
    for p in sorted(PER_EXPERIMENT, key=lambda x: ORDER.index(x['experiment_id']))) + f"""

`V2_EFF_ATTEMPT1` shows 0 under *status COMPLETE* because its rows carry
`INTACT_GOVERNED_OBSERVATION` (7 rows) and `DAMAGED_*` (2 rows) instead - a
deliberately distinct status, because those runs were never admitted as
observations. The experiment registry counts the same 7 rows as "completed runs";
both readings are shown rather than reconciled away.

**[LIMITATION]** All {INV['eligible']} eligible rows belong to three
**non-confirmatory** pilots. No p-value, confidence interval, effect size or
power estimate exists anywhere in this programme, and none would be defensible
from 16, 8 and 3 paired blocks at 3 repetitions.

---

## 4. V1 historical results

**Design.** 12 tasks x {{baseline, AFCI}} x {{non-reset, reset}} = 48 runs, one run
per cell, model labelled "Opus 7". Published as the ASE 2026 artifact; Zenodo DOI
`10.5281/zenodo.19757261`.

**[FACT]**

| metric | baseline | AFCI | change | per-task direction |
| --- | ---: | ---: | ---: | --- |
| non-reset code churn (mean) | 576.58 | 955.42 | +65.7% | AFCI higher in 12/12 |
| non-reset test churn (mean) | 172.67 | 244.00 | +41.3% | AFCI higher in 12/12 |
| reset true drift, delta CodeLOC (mean) | 307.7 | 670.5 | +117.9% | AFCI **lower** in 1/12 |
| CI pass | 100% | 100% | 0.0 pp | 48/48 |

**[INTERPRETATION]** Read at face value, v1 contradicts the hypothesis: AFCI
increased churn on every task and was more reset-inconsistent on 11 of 12. It
should not be read at face value.

**[LIMITATION]** Seven recorded limitations, each of which independently
undermines inference:

| id | limitation | consequence |
| --- | --- | --- |
| L1 | the tree was never reset between tasks, so edits accumulate across T01-T12 | runs are **non-independent**; the churn trend is confounded with accumulation |
| L2 | `run_one_v1.sh` does not invoke a model - it snapshots the working tree | generation and diff capture are not coupled |
| L3 | AFCI-Guard matched literal `libs/core` paths while the code uses `@afci-bench/*` aliases | the guard's regexes never fired; its zeros are **not measurements** |
| L4 | `docs/ARCH_RULES.yml` is 0 bytes | the machine-checkable architecture rules did not exist |
| L5 | `layer_jaccard` is a constant 1.0 | the metric cannot vary, so it measures nothing |
| L6 | no per-task acceptance oracle beyond `npm run ci`, which is saturated `True` | the success gate does not discriminate |
| L7 | `npm ci` fails on the clean v1 base | deterministic install is broken at the base tag |

Also: the v1 baseline ran against a repository whose architecture was visible in
the tree, so the "no architecture context" arm was not architecture-free.

> v1 is historical / exploratory evidence. No v1 number may be pooled with, or
> contrasted against, a v2 number.

---

## 5. Architecture diagnostic results

These three experiments measure **instruments**, not treatments. A run-purpose
firewall enforced by the record schema keeps them out of every confirmatory
dataset, treatment-effect estimate and power calculation.

**[FACT]**

| task | runs | functional | applicable opportunities | target violations | classification | consequence |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| PT08 | 3 | 3/3 (15/15 acceptance cases each) | 3 | **0/3** | functional ceiling + architecture floor | PT08 = REVISE; benchmark = CONTINUE |
| PT09 | 3 | 3/3 (14/14 each) | 3 | **0/3** | FAIL / ARCHITECTURE FLOOR | STOP / REASSESS |
| PT10 | 3 | 3/3 (8/8 each) | 3 | **1/3** | REVISE / WEAK PRESSURE | STOP / REASSESS |

PT10's single violation is the only target architecture violation recorded
anywhere in the programme: one forbidden import, on one line, in one
already-existing file, severity blocker, confidence certain, automated. The
opportunity id, rule id, forbidden scopes and anchor path are hidden evaluator
semantics and stay in the private evaluator repository. **No numeric result is
withheld.**

**[INTERPRETATION]** Three independent instruments at or near the architecture
floor on this substrate is evidence about the **substrate**, not only about the
tasks. A baseline at the floor has no room beneath it, so no treatment however
good can be discriminated.

**[LIMITATION]** Three observations per instrument. No power calculation
justifies that count and none is implied.

---

## 6. Sonnet efficiency pilot (Attempt 2)

**Design.** 3 tasks (PT01, PT04, PT07) x {{C1, C4}} x {{non-reset, reset}} x 3
repetitions = 36 runs, `claude-sonnet-5`, CLI 2.1.229, block-paired with
randomised within-block condition order.

**[FACT]** Execution and validity:

| | value |
| --- | ---: |
| scheduled / executed | 36 / 36 |
| completed | 35 |
| refused | 1 (sequence 12) |
| functionally valid | 34 - C1 **17/18**, C4 **17/18** |
| paired-eligible blocks | **16 of 18** (minimum required 12) |
| runs entering the paired analysis | 32 |
| valid but unpaired | 2 |

**[FACT]** Endpoints. Every figure is the median of per-block C4/C1 ratios;
1.0000 is parity and above 1.0000 means C4 cost more.

| endpoint | n | median C4/C1 | C4 lower | PT01 | PT04 | PT07 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{ratio_line("**TOTAL_INPUT_TOKENS** (primary)", SON, "TOTAL_INPUT_TOKENS")}
{ratio_line("MODEL_WALL_SECONDS", SON, "MODEL_WALL_SECONDS")}
{ratio_line("EXPLORATION_CALLS", SON, "EXPLORATION_CALLS")}
{ratio_line("TOTAL_TOOL_CALLS", SON, "TOTAL_TOOL_CALLS")}
{ratio_line("UNIQUE_FILES_READ", SON, "UNIQUE_FILES_READ")}
{ratio_line("EDIT_AND_WRITE_CALLS", SON, "EDIT_AND_WRITE_CALLS")}
{ratio_line("CI_COMMAND_RUNS", SON, "CI_COMMAND_RUNS")}
{ratio_line("TOTAL_OUTPUT_TOKENS (non-reset only)", SON_NR, "TOTAL_OUTPUT_TOKENS")}
{ratio_line("provider cost USD (non-reset only)", SON_NR, "PROVIDER_COST_USD")}

By arm, on the primary endpoint: **NON_RESET {fnum(SON_NR['TOTAL_INPUT_TOKENS']['median'])}**
(n={SON_NR['TOTAL_INPUT_TOKENS']['n']}) and **RESET {fnum(SON_RS['TOTAL_INPUT_TOKENS']['median'])}**
(n={SON_RS['TOTAL_INPUT_TOKENS']['n']}). PT04 is the only task where C4 was
cheaper on median.

**[FACT]** One signal ran the other way. Reset overhead is a run's metric under
reset divided by the same task and condition without reset; lower is better.

| endpoint | tasks where C4's recovery overhead is lower |
| --- | --- |
| TOTAL_INPUT_TOKENS | **2 of 3** ({", ".join(RESET_C4_LOWER['TOTAL_INPUT_TOKENS'])}) |
| MODEL_WALL_SECONDS | **3 of 3** ({", ".join(RESET_C4_LOWER['MODEL_WALL_SECONDS'])}) |
| EXPLORATION_CALLS | 2 of 3 ({", ".join(RESET_C4_LOWER['EXPLORATION_CALLS'])}) |
| TOTAL_TOOL_CALLS | 2 of 3 ({", ".join(RESET_C4_LOWER['TOTAL_TOOL_CALLS'])}) |

**[FACT]** The frozen decision. Both functional guardrails and the minimum-pairs
gate passed; every token and secondary-endpoint threshold failed. The
RESET-SPECIFIC GO branch failed only on its overall token clause - its two
reset-overhead clauses passed.

> **Outcome (rule 11.4): `STOP - NO EFFICIENCY SIGNAL JUSTIFIES FULL-SUITE
> EXPANSION`.** `efficiency_claim_made = false`.

**[LIMITATION]** `AFCI_EFFICIENCY_PILOT` is a **cost-only** purpose under its own
frozen governance. **No architecture endpoint was produced and none may be
inferred from it.** LOC churn was likewise not captured.

---

## 7. Haiku lower-model pilot

**Design.** The same three tasks on `claude-haiku-4-5-20251001`, non-reset only,
3 repetitions, 18 runs. The point was to test the most obvious explanation for
the Sonnet null - that a strong model already knows what the MAD would tell it.
Quality and efficiency are two **independent** channels, combined into no single
score.

**[FACT]** Execution and validity: 18 of 18 executed, 18 COMPLETE, **0 refused,
0 infrastructure-invalid**. 17 of 18 functionally valid - C1 **8/9**, C4 **9/9**.
The single invalid run, `PT04/C1/R2`, failed all four semantic acceptance cases
and strands its valid C4 partner, leaving **8 of 9** paired-eligible blocks.

**[FACT]** Architecture quality:

| arm | runs | applicable opportunities | violated | target-violation runs |
| --- | ---: | ---: | ---: | ---: |
| C1 | 9 | 9 | 0 | **0** |
| C4 | 9 | 9 | 0 | **0** |

Identical by task: 3 applicable, 0 violated in both arms for PT01, PT04 and PT07.

**[FACT]** Efficiency endpoints, 8 paired blocks:

| endpoint | n | median C4/C1 | C4 lower | PT01 | PT04 | PT07 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{ratio_line("**TOTAL_INPUT_TOKENS** (primary)", HAI, "TOTAL_INPUT_TOKENS")}
{ratio_line("TOTAL_OUTPUT_TOKENS", HAI, "TOTAL_OUTPUT_TOKENS")}
{ratio_line("MODEL_WALL_SECONDS", HAI, "MODEL_WALL_SECONDS")}
{ratio_line("TOTAL_TOOL_CALLS", HAI, "TOTAL_TOOL_CALLS")}
{ratio_line("EXPLORATION_CALLS", HAI, "EXPLORATION_CALLS")}
{ratio_line("UNIQUE_FILES_READ", HAI, "UNIQUE_FILES_READ")}
{ratio_line("EDIT_AND_WRITE_CALLS", HAI, "EDIT_AND_WRITE_CALLS")}
{ratio_line("CI_COMMAND_RUNS", HAI, "CI_COMMAND_RUNS")}
{ratio_line("provider cost USD", HAI, "PROVIDER_COST_USD")}

PT07 is the one task where C4 was directionally cheaper on tokens, time, output
and cost. PT01 was the most expensive for C4 on every endpoint.

**[FACT]** Rework over the 8 paired blocks: edit calls
{fint(HAI_REWORK['C1']['edit_calls'])} vs {fint(HAI_REWORK['C4']['edit_calls'])},
files re-edited {fint(HAI_REWORK['C1']['files_reedited'])} vs
{fint(HAI_REWORK['C4']['files_reedited'])}, turns used
{fint(HAI_REWORK['C1']['turns_used'])} vs {fint(HAI_REWORK['C4']['turns_used'])},
files changed in the worktree diff {fint(HAI_REWORK['C1']['files_changed'])} vs
{fint(HAI_REWORK['C4']['files_changed'])}, net lines
+{fint(HAI_REWORK['C1']['net_lines'])} vs +{fint(HAI_REWORK['C4']['net_lines'])}.
Agent-initiated CI command runs went the other way:
{fint(HAI_REWORK['C1']['ci_command_runs'])} for C1 against
{fint(HAI_REWORK['C4']['ci_command_runs'])} for C4.

**[FACT]** The frozen decision:

| signal | criterion | observed | verdict |
| --- | --- | --- | --- |
""" + "\n".join(f"| {c['signal']} | {c['clause']} | {c['observed']} | **{c['verdict']}** |"
                for c in LM_CLAUSES if "trigger" not in c["signal"]) + f"""

> **`NO LOWER-MODEL SIGNAL - DO NOT EXPAND THE SYNTHETIC LOWER-MODEL MATRIX`**

**[LIMITATION]** Criterion 12.1.1 fails on a **tie at zero**, not on C4 being
worse. Neither arm violated anything, so there was nothing to discriminate. The
rule requires *strictly fewer* violations, so a tie scores FAIL. That is a rule
outcome, not a finding about AFCI: the quality channel produced **no
information**.

---

## 8. Backstage real-repository pilot (Attempt 2)

**Design.** The first AFCI experiment on a **real, large, ambiguous** open-source
repository rather than the synthetic substrate: Backstage at
`f285f6e4`, which predates the 2026-02-15 contamination boundary. 3 tasks
(T1, T2, T5) x {{C1, C4}} x NON_RESET x 3 repetitions = 18 runs, 9 paired
blocks, `claude-sonnet-5` at effort `high`, CLI 2.1.229, 96-turn ceiling.
Attempt 1 was halted at 7 of 18 and is **excluded wholesale**; attempt 2 is a
wholly new execution with new run ids and new destinations.

**[FACT] Execution.** 18/18 executed in the committed order, 18 valid, **0
infrastructure-invalid, 0 retries**, 18 unique sessions, 0 scientific
modifications. Model requested and resolved `claude-sonnet-5` on every row;
effort `high` read back from two independent channels over 2,479 hook firings;
runtime context `CLEAN` with loaded context empty on all four fields; export
tree `4dfadc10...` verified per run. Captured provider cost **${fnum(sum(num(r['provider_cost_usd']) or 0 for r in BS2_RAW), 2)}**.

**[FACT] Primary endpoint - architectural placement.** 1 applicable opportunity
per run, 18 across the set.

| scope | C1 target-violation runs | C4 target-violation runs |
| --- | ---: | ---: |
""" + "\n".join(
    f"| {r['scope']} | {r['c1_target_violation_runs']} / {r['c1_runs']} | "
    f"{r['c4_target_violation_runs']} / {r['c4_runs']} |" for r in BS2_ARCH) + f"""

**[FACT] Functional endpoint.**

| scope | C1 valid | C4 valid | paired-valid blocks |
| --- | ---: | ---: | ---: |
""" + "\n".join(
    f"| {r['scope']} | {r['c1_functional_valid']} / {r['c1_runs']} | "
    f"{r['c4_functional_valid']} / {r['c4_runs']} | "
    f"{r['paired_functionally_valid_blocks']} / {r['paired_blocks']} |"
    for r in BS2_FUNC) + f"""

**[FACT] The frozen decision** (`SL-V2-BACKSTAGE-PILOT-01` S11.1, all three
required):

| clause | statement | observed | verdict |
| --- | --- | --- | --- |
""" + "\n".join(
    f"| {c['clause']} | {c['statement']} | {c['observed']} | **{c['verdict']}** |"
    for c in BS2_CLAUSES) + f"""

> **`NO ARCHITECTURE SIGNAL - DO NOT AUTOMATICALLY EXPAND`**

**[LIMITATION]** Criterion 11.1.2 fails on **ties at zero**, not on C4 being
worse. T1 and T2 produced zero target violations in *both* arms, so neither can
show C4 as "fewer"; only T5 discriminated. Two of three tasks sat at an
architecture floor - the same failure mode the Haiku pilot hit, here partial
rather than total.

**[LIMITATION] T1 is a task-instrument failure, not a model result.** All six
T1 runs - both arms, all three repetitions - passed exactly 3 of 4 semantic
cases and failed the **same single case every time**, while both controlled T1
references pass that case in the frozen reference matrix. The oracle is
satisfiable; the model-facing task statement does not ask for the behaviour it
checks. T1 therefore contributes 0 functionally valid runs *and* 0 target
violations to either arm - inert on both endpoints. Nothing was changed in
response; the task bytes, oracle, scorer and rule stand exactly as frozen.

**[FACT] MAX_TURNS.** 2 of 18 reached the 96-turn ceiling, one per arm, both on
T5. The 64->96 raise worked: attempt 1 hit its ceiling on 4 of its 5 valid rows.
`MAX_TURNS` is a scientific outcome and was never a retry reason.

**[FACT] Secondary efficiency** (S11.2, cannot override S11.1), median C4/C1
over functionally valid paired blocks:

| endpoint | median C4/C1 | coverage | C4 lower |
| --- | ---: | ---: | ---: |
""" + "\n".join(
    f"| `{r['endpoint']}` | {r['median_ratio_c4_over_c1']} | {r['coverage']} | "
    f"{r['c4_lower_count']}/{r['c4_lower_of']} |" for r in BS2_RATIOS) + f"""

**[LIMITATION]** Coverage is **3 of 9** blocks, because no T1 run is
functionally valid. At n=3 a single block moves every median. These figures are
descriptive only and could not have rescued a failed S11.1 in any case.

**[FACT] The network preflight prevented a repeat of the attempt-1 loss.** 20
preflight refusals occurred, every one `VPN_ADAPTER_UP` - the adapter state that
severed two attempt-1 observations. Each refused **before the task was
delivered**: no artifact directory, no workspace, no provider call, no
observation consumed, $0. The cost was wall-clock only.

---

## 9. Cost and token findings

**[FACT] Token audit.** `TOTAL_INPUT_TOKENS = input_tokens +
cache_creation_input_tokens + cache_read_input_tokens` on every row that carries
tokens - checked on all {INV['token_coverage']} such rows, 0 failures. The MAD's
own tokens and all cache traffic stay inside the number.

| scope | paired blocks | C1 total input tokens | C4 total input tokens | C1 median/run | C4 median/run | median C4/C1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sonnet overall | {SON['TOTAL_INPUT_TOKENS']['n']} | {fint(SON['TOTAL_INPUT_TOKENS']['C1_total'])} | {fint(SON['TOTAL_INPUT_TOKENS']['C4_total'])} | {fint(SON['TOTAL_INPUT_TOKENS']['C1_median'])} | {fint(SON['TOTAL_INPUT_TOKENS']['C4_median'])} | {fnum(SON['TOTAL_INPUT_TOKENS']['median'])} |
| Sonnet NON_RESET | {SON_NR['TOTAL_INPUT_TOKENS']['n']} | {fint(SON_NR['TOTAL_INPUT_TOKENS']['C1_total'])} | {fint(SON_NR['TOTAL_INPUT_TOKENS']['C4_total'])} | {fint(SON_NR['TOTAL_INPUT_TOKENS']['C1_median'])} | {fint(SON_NR['TOTAL_INPUT_TOKENS']['C4_median'])} | {fnum(SON_NR['TOTAL_INPUT_TOKENS']['median'])} |
| Sonnet RESET | {SON_RS['TOTAL_INPUT_TOKENS']['n']} | {fint(SON_RS['TOTAL_INPUT_TOKENS']['C1_total'])} | {fint(SON_RS['TOTAL_INPUT_TOKENS']['C4_total'])} | {fint(SON_RS['TOTAL_INPUT_TOKENS']['C1_median'])} | {fint(SON_RS['TOTAL_INPUT_TOKENS']['C4_median'])} | {fnum(SON_RS['TOTAL_INPUT_TOKENS']['median'])} |
| Haiku NON_RESET | {HAI['TOTAL_INPUT_TOKENS']['n']} | {fint(HAI['TOTAL_INPUT_TOKENS']['C1_total'])} | {fint(HAI['TOTAL_INPUT_TOKENS']['C4_total'])} | {fint(HAI['TOTAL_INPUT_TOKENS']['C1_median'])} | {fint(HAI['TOTAL_INPUT_TOKENS']['C4_median'])} | {fnum(HAI['TOTAL_INPUT_TOKENS']['median'])} |

Token coverage: {INV['token_coverage']} of {INV['total_rows']} run rows carry
input-token evidence, {INV['output_token_coverage']} carry output tokens. v1, the
aborted Attempt 1 and the three diagnostics predate or do not use the token
instrumentation; their cells are blank, never 0.

**[FACT] Cost audit.**

| scope | runs | runs with complete cost | captured total | verdict |
| --- | ---: | ---: | ---: | --- |
""" + "\n".join(
    f"| {c['scope'].replace(' | ', ' - ')} | {c['runs']} | {c['runs_with_metric']} | {fusd(c['captured_total'])} | "
    f"{'COMPLETE COST COVERAGE' if c['runs_without_metric'] == 0 else 'PARTIAL COST CAPTURE'} |"
    for c in COST_COVERAGE) + f"""

The Sonnet RESET row counts 17, not 18: the refused run (sequence 12) carries no
reset state at all, so it sits outside both arms. 18 + 17 + 1 = 36.

| paired cost ratio | n | C1 total | C4 total | median C4/C1 |
| --- | ---: | ---: | ---: | ---: |
| Sonnet NON_RESET | {SON_NR['PROVIDER_COST_USD']['n']} | {fusd(SON_NR['PROVIDER_COST_USD']['C1_total'])} | {fusd(SON_NR['PROVIDER_COST_USD']['C4_total'])} | {fnum(SON_NR['PROVIDER_COST_USD']['median'])} |
| Sonnet RESET | 0 | n/a | n/a | **no cost comparison exists** |
| Haiku NON_RESET | {HAI['PROVIDER_COST_USD']['n']} | {fusd(HAI['PROVIDER_COST_USD']['C1_total'])} | {fusd(HAI['PROVIDER_COST_USD']['C4_total'])} | {fnum(HAI['PROVIDER_COST_USD']['median'])} |

**Total captured provider cost across all runs carrying cost evidence:
{fusd(TOTAL_CAPTURED_COST, 2)} over {len(COST_ROWS)} runs.**

> **CAPTURED COST, NOT NECESSARILY TOTAL STUDY COST.**
> {INV['total_rows'] - len(COST_ROWS)} of {INV['total_rows']} run rows carry no
> provider-cost record at all: all 48 v1 rows, all 9 Attempt-1 rows, all 10
> diagnostic rows, 16 of 17 Sonnet RESET rows, and the one refused run. Money was
> spent on those runs; the runtime never reported it in a form the record could
> carry.

**[LIMITATION]** A reset run's phase A is deliberately interrupted at the
checkpoint, **before** its terminal result event - the only place the runtime
reports output tokens and cost. For a reset run, input tokens remain **exact**
(reconstructed from the streamed assistant messages) while output tokens and cost
are **withheld, not zero and not estimated**. The one Sonnet reset run that does
carry a cost is `PT04/C1/RESET/R1`, and it carries one precisely because it never
reached its checkpoint - it is functionally invalid and enters no paired figure.
There are therefore **zero usable Sonnet RESET cost pairs**, and the 1.4928 figure
describes the non-reset arm only.

---

## 10. Functional and architecture quality

**[FACT]**

| experiment | C1 valid | C4 valid | paired-valid blocks | semantic cases passed (C1 / C4) |
| --- | ---: | ---: | ---: | --- |
| Sonnet Attempt 2 | 17/18 | 17/18 | 16 of 18 | 68 / 68 |
| Haiku lower-model pilot | 8/9 | 9/9 | 8 of 9 | 32 / 36 |

**[FACT]** Architecture, over every run that produced a measurement:

| experiment | arm | runs | applicable | violated | target-violation runs |
| --- | --- | ---: | ---: | ---: | ---: |
| PT08 diagnostic | C1 | 3 | 3 | 0 | 0 |
| PT09 qualification | C1 | 3 | 3 | 0 | 0 |
| PT10 qualification | C1 | 3 | 3 | 1 | 1 |
| Haiku pilot | C1 | 9 | 9 | 0 | 0 |
| Haiku pilot | C4 | 9 | 9 | 0 | 0 |
| **Sonnet Attempt 2** | both | 36 | **NOT MEASURED** | **NOT MEASURED** | **NOT MEASURED** |
| **V1 original** | both | 48 | **INVALID FOR INFERENCE** | **INVALID FOR INFERENCE** | **INVALID FOR INFERENCE** |

**[INTERPRETATION]** Functional acceptance is saturated and architecture sits at
a floor. Six instrument/model combinations now sit at or near that floor on this
substrate: PT08, PT09 and PT10 for an unguided Sonnet baseline, and PT01, PT04
and PT07 for Haiku in **both** arms.

**[LIMITATION]** The evidence base is lopsided. The study's *actual* construct -
architectural conformance - has been measured only by instruments that all sat at
or near the floor, while its *secondary* construct - cost - has one clean pilot.
The cost result must not be allowed to stand in for an architecture result.

---

## 11. Cross-model interpretation

**[FACT]** Both sides below are NON_RESET, so the comparison is like-for-like.

| metric | Sonnet C4/C1 (n={SON_NR['TOTAL_INPUT_TOKENS']['n']}) | Haiku C4/C1 (n={HAI['TOTAL_INPUT_TOKENS']['n']}) | difference | reading |
| --- | ---: | ---: | ---: | --- |
""" + "\n".join(
    f"| {c['metric']} | {fnum(c['sonnet_median'])} | {fnum(c['haiku_median'])} | "
    f"{'n/a' if c['difference'] is None else ('+' if c['difference'] >= 0 else '') + fnum(c['difference'])} | "
    f"{c['direction']} |" for c in CROSS) + f"""

| channel | Sonnet | Haiku | comparable? |
| --- | --- | --- | --- |
| architecture target violations | NOT MEASURED (cost-only purpose) | 0/9 in C1 and 0/9 in C4 | **no** |
| functional validity | 17/18 and 17/18 | 8/9 and 9/9 | descriptively only |

> **This is a descriptive comparison between two separate experiments, not a
> randomised cross-model causal comparison.** The two pilots ran under separate
> purposes, separate schedules and separate frozen analyses and are **never
> pooled**. No interaction was estimated, no test was performed, and no pooled
> model exists.

**[INTERPRETATION]** The moderator hypothesis predicted that a weaker coding
model, having less ability to infer architecture from the repository alone, would
find the explicit MAD *more* useful. The prediction did not come true on the
primary endpoint: C4's median input-token ratio **rose** from
{fnum(SON_NR['TOTAL_INPUT_TOKENS']['median'])} to
{fnum(HAI['TOTAL_INPUT_TOKENS']['median'])}, a difference of
{fnum(CROSS[0]['difference'])} in the direction opposite to the prediction, and
the quality channel produced nothing at all because both arms sat at zero.

Two of the eight metrics did move the predicted way -
{", ".join(c['metric'] for c in CROSS if c['difference'] is not None and c['difference'] < 0)} -
and both are reported above rather than dropped. Neither is the primary endpoint,
both remain **above** 1.0000 on the Haiku side (so C4 still cost more in absolute
terms on both models), and with 8 and 9 paired blocks and no test performed, a
two-of-eight split is not a result. It is recorded so that the six-of-eight
direction is not read as unanimity.

---

## 12. What the evidence supports

1. **[FACT]** On this substrate with `claude-sonnet-5`, explicit MAD injection
   costs more than it saves across every captured cost dimension except CI
   invocations.
2. **[FACT]** It does so without buying functional quality: 17/18 versus 17/18.
3. **[FACT]** Weakening the model did not reduce C4's relative cost; it raised it,
   and produced no quality gain because both arms sat at zero violations.
4. **[FACT]** The reset-recovery direction is the one consistent counter-signal,
   strongest in wall time (3 of 3 tasks).
5. **[INTERPRETATION]** The **strong-model ceiling** explanation for the repeated
   null is **not supported**. Instrument discrimination, not model capability, is
   the binding constraint on the programme.
6. **[INTERPRETATION]** Expanding either pilot, unchanged, is not justified. Both
   frozen rules returned a negative verdict and both were honoured.
7. **[INTERPRETATION]** The benchmark machinery works. Sterile execution, model
   pinning and readback, context auditing, hidden acceptance, the architecture
   oracle, the artifact firewall, run-identity derivation and the frozen analysis
   all executed end to end - and caught their own defects twice, in ways that cost
   real money and were recorded rather than smoothed over.

---

## 13. What the evidence does NOT support

1. **We cannot conclude AFCI does not work.** We can conclude it did not reduce
   cost here. Efficiency is one construct; architectural conformance is the
   study's actual construct, and the cost pilot **did not measure it at all**.
2. **We cannot attach any statistical confidence to anything.** No p-value, no
   confidence interval, no effect size, no power estimate.
3. **We cannot generalise past this substrate** - one synthetic 49-file monorepo
   whose architecture is legible from its own code.
4. **We cannot generalise past the two models used.** `primary_model` is still
   `null`; no model has been selected for the study.
5. **We cannot use the reset-recovery signal as a finding.** It is descriptive,
   from 3 tasks, and it failed the branch that would have made it a GO.
6. **We cannot read anything as a v1 hypothesis test.** L1-L7 make the v1
   comparison uninterpretable as a treatment contrast.
7. **We cannot claim any architecture result from the Sonnet pilot.** It produced
   none.
8. **We cannot claim an architecture result from the Haiku pilot either.** It
   produced an endpoint, but at the floor in both arms. A tie at zero
   discriminates nothing and must not be read as AFCI failing to improve
   architecture.
9. **We cannot claim that model capability moderates AFCI's value.** Two separate
   experiments compared descriptively, never pooled.

---

## 14. Limitations

| # | limitation |
| --- | --- |
| 1 | **No confirmatory evidence exists.** Collection has not begun. The suite-wide protocol is PRE-FREEZE, gate `G1` is not passed, and `TD-B32`, `TD-B34`, `TD-B03` and `TD-B19` remain open. |
| 2 | **No statistical inference of any kind.** Every reported figure is a median of paired ratios - a descriptive statistic. No power calculation has ever been run. |
| 3 | **One synthetic substrate**, 49 files, whose layering is inferable from its own import graph and path aliases. A model can often deduce the intended architecture *without* the MAD, which directly attacks the MAD's marginal value. This is the primary external-validity threat to every v2 finding. |
| 4 | **No study model has been selected.** Both models used so far are provisional. |
| 5 | **Architecture is measured only where it sat at a floor.** The evidence base is lopsided toward cost. |
| 6 | **Reset cost and output tokens do not exist for reset runs** - withheld by construction, not missing by accident. |
| 7 | **This package is a secondary artifact.** Where it and a primary artifact disagree, the primary artifact wins. |

---

## 15. Current research direction

The chain is short and each link is recorded:

1. **v1 measured the wrong things well enough to notice.** Churn is a proxy, the
   guard did not fire, the oracle did not discriminate, and runs were not
   independent. v2 replaced proxies with a hidden functional acceptance oracle and
   an out-of-band architecture oracle.
2. **PT08 showed the instruments, not the theory, were the bottleneck.** A
   baseline at the architecture floor cannot discriminate however good the
   treatment is.
3. **PT09 and PT10 showed it was not specific to PT08.** Two purpose-built
   replacements landed in the same place.
4. **The efficiency pilot asked a cheaper question that could be answered now** -
   does the MAD at least pay for itself? - and answered **no**, under a rule frozen
   before the data existed.
5. **The lower-model pilot weakened the model, and the null held.** A weaker model
   produced no quality signal and a *worse* cost ratio.
6. **[INTERPRETATION]** The common factor across steps 2-5 is not model strength -
   that has now been varied and did not matter. What remains is that **a legible
   synthetic repository gives an agent little to gain from being told its
   architecture**, whether the agent is strong or weak.

**[INTERPRETATION]** Repository architectural complexity / ambiguity /
context-recovery burden is therefore the next scientifically distinct moderator to
investigate. **This is the next hypothesis to test, not a proven one.** It stands
by elimination rather than by evidence, and nothing in this package tests it.

---

## 16. Next study - open-source architectural complexity

**Status: NOT STARTED.** No runs exist. No results are pre-populated.

Re-run against real / open-source repositories with genuine architectural
complexity, where the architecture is *not* inferable from a 49-file import
graph. That directly tests the substrate-legibility explanation - the only one of
the two rival explanations still standing.

Its motivation was never contingent on the lower-model outcome: repository
complexity is an independent moderator and the lower-model pilot measured nothing
about it. Removing the ceiling rival raises its priority; it does not authorise
it.

Before any run it needs its own decision record, new tasks, new hidden acceptance
packages and new architecture rule linkage. Gate `G1` is still not passed and the
suite is still not frozen.

---

*Sources: `study-results/AFCI_MASTER_RUN_RESULTS.csv`,
`AFCI_MASTER_EXPERIMENT_REGISTRY.csv`, and the frozen per-experiment analysis
artifacts under `01_v1_original_study/` through `06_lower_model_pilot_completed/`.
Traceability from any figure here to its raw artifact is in
`AFCI_Professor_Evidence_Map.md` and workbook sheet `18_EVIDENCE_MAP`.*
"""

SUMMARY_PATH = OUT / "AFCI_Professor_Results_Summary.md"
SUMMARY_PATH.write_text(SUMMARY, encoding="utf-8", newline=LF)
WRITTEN.append(SUMMARY_PATH)
print(f"wrote {SUMMARY_PATH}")

# --------------------------------------------------------------------------- #
# metric definitions
# --------------------------------------------------------------------------- #

DEFS_MD = ["# AFCI-Bench - metric definitions", "",
           f"Compiled {COMPILED}. Plain-English definitions for every metric that appears in",
           "`AFCI_Professor_Results.xlsx`, `AFCI_Professor_Results_Summary.md` and",
           "`AFCI_Professor_Full_Run_Results.csv`. Direction is stated for every ratio.", "",
           "Two conventions hold everywhere in this package:", "",
           "- **a missing metric is a blank, never a zero**; and",
           "- **every aggregate is published beside its coverage count**.", "", "---", ""]
for term, role, meaning, direction in DEFS:
    DEFS_MD += [f"## {term}", "", f"*{role}*", "", meaning, "", f"**Direction and caveats.** {direction}", "", "---", ""]
DEFS_MD += [
    "## How a run becomes a number", "",
    "1. The runner prepares a sterile worktree from the governed substrate and hands the model the task body",
    "   (C1) or the task body plus the MAD (C4). Nothing else differs.",
    "2. The runtime streams events. The terminal `result` event carries the exact token and cost totals; for a",
    "   reset run, whose phase A is interrupted before that event, input tokens are reconstructed exactly from",
    "   the streamed assistant messages and output tokens and cost are withheld.",
    "3. A hidden acceptance oracle, which the model never sees, decides `FUNCTIONAL_VALID`.",
    "4. An out-of-band architecture oracle scores the captured worktree against the opportunities the run's own",
    "   changes made applicable.",
    "5. The frozen analysis pairs C1 against C4 within each block and takes the median of the per-block ratios.",
    "",
    "Steps 3 and 4 are independent of each other and of step 2. A run that violated the architecture is still a",
    "run that violated it, so the architecture channel is reported over *all* runs; a cost figure from a run that",
    "did not work is not a cheaper way of doing the task, so the efficiency channel is restricted to",
    "functionally-valid pairs.", ""]
DEFS_PATH = OUT / "AFCI_Professor_Metric_Definitions.md"
DEFS_PATH.write_text("\n".join(DEFS_MD), encoding="utf-8", newline=LF)
WRITTEN.append(DEFS_PATH)
print(f"wrote {DEFS_PATH}")

# --------------------------------------------------------------------------- #
# evidence map
# --------------------------------------------------------------------------- #

EV_MD = ["# AFCI-Bench - evidence map", "",
         f"Compiled {COMPILED}. Professor-safe traceability: summary result -> analysis artifact ->",
         "run record -> raw artifact, with a hash at each anchor.", "",
         "Every chain stops at the private boundary, and it stops at a **field**, not at its value.",
         "No private evaluator identifier appears anywhere in this package.", "", "---", "",
         "## Traceability chains", ""]
for e in EV:
    EV_MD += [f"### {e[0]}", "",
              f"- **analysis artifact** - {e[1]}",
              f"- **run record** - {e[2]}",
              f"- **raw artifact** - `{e[3]}`",
              f"- **hash / SHA** - `{e[4]}`",
              f"- **status** - {e[5]}", ""]
EV_MD += ["---", "", "## Repository and governance anchors", "", "| what | value |", "| --- | --- |"]
EV_MD += [f"| public repo branch | `{GIT['branch']}` |",
          f"| evidence commit (last change to study-results/ outside this package) | `{GIT['evidence_commit']}` |",
          f"| that commit's subject | {GIT['evidence_subject']} |",
          f"| public repo origin | {GIT['origin']} |",
          "| public repo `main` (v1 base, tag `paper-v0`) | `2adc8741acad7ea5423f0bf3d9ad821ff023a35f` |",
          "| private evaluator repo HEAD (result provenance only; never pushed) | `9b047bed21e3c6c2169345322b9b14dfe80f56ee` |",
          "| governed substrate commit | `630d3180af0d02a86330dfb599f559e78df65e94` |",
          "| governed substrate content hash | `0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3` (49 entries) |",
          "| the MAD, `docs/v2/ARCHITECTURE_CONTEXT.md` | `bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d` |",
          "| v1 release | GitHub `ase2026-artifacts-v1` @ `1ba21ad75dacbac5eb87d354a490b088078c30da` |",
          "| v1 DOI | `10.5281/zenodo.19757261` |", "",
          "## Governance document hashes", "", "| document | sha256 |", "| --- | --- |",
          "| `docs/v2/AFCI_EFFICIENCY_PILOT_RUN_PLAN.json` | `0038cd8b563ea804f4887d21cb37ceddb3a8f7632c4dd2315c260d3a9af95767` |",
          "| `docs/v2/AFCI_EFFICIENCY_PILOT_DECISION.md` | `e3110d9a90009be180e76fb30368179529c187263ab823391635990b2cc0d8df` |",
          "| `docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_2_EXECUTION_PLAN.json` | `562415031c04b0673c54ac352a4ca35a66e885023aa212cedc284da0c65a087e` |",
          "| `docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_ABORT_DECISION.md` | `21547ed7d3f86e3c6793e830ca128ffe7bf3c6665ada07568c99d2c493a66445` |",
          "| `docs/v2/AFCI_EFFICIENCY_PILOT_ATTEMPT_1_EVIDENCE_INVENTORY.json` | `9985860fb3b7a5842e676cc1c66c876e712ea93a196999457d711332ba12683f` |",
          "| `docs/v2/AFCI_LOWER_MODEL_PILOT_DECISION.md` | `cbb73e76d4f9936319123f650751b079e33044e66afe6422b0c246fdbc716203` |",
          "| `docs/v2/AFCI_LOWER_MODEL_PILOT_RUN_PLAN.json` | `f045c0d93370f7e6f785274acd7df6b34bb28f52ba60cdcfd49eb6812b86b026` |",
          "| `docs/v2/AFCI_LOWER_MODEL_PILOT_EXECUTION_PLAN.json` | `2ff3f9b45e4ddf6f3318bb2a419d9d12b5eaab5b1a297acec425796ed4a24318` |",
          "| `docs/v2/V2_QUALIFICATION_DIAGNOSTIC_DECISION.md` | `e5bcebe5717ab301e9fe27565ddd9593677f56d5c6a78399c21ea1e260416385` |",
          "| `docs/v2/PT08_DIAGNOSTIC_OUTCOME_AND_DISPOSITION.md` | `3658dd21b2ac5b829df92bb8d4da5a8ad71262b6c36bd0c4f7ccbd1c1b94515e` |", "",
          "## Task body hashes (public)", "", "| task | sha256 | used by |", "| --- | --- | --- |",
          "| PT01 | `6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39` | efficiency pilot; lower-model pilot |",
          "| PT04 | `f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5` | efficiency pilot; lower-model pilot |",
          "| PT07 | `557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7` | efficiency pilot; lower-model pilot |",
          "| PT08 | `a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2` | PT08 diagnostic |",
          "| PT09 | `bac32dc0e7163c9ab1816ac6eea6c98738092cca5cf56715e280f1ec1c0ac44c` | qualification |",
          "| PT10 | `1b1fe29881b3c9f309939df042272b03164fb3baae878c64345e75edddf36b86` | qualification |", "",
          "---", "", "## What is withheld, and why no digest replaces it", "",
          "Withheld: private opportunity identifiers, rule identifiers, forbidden source and target scopes,",
          "anchor paths, and hidden acceptance case semantics. They live in the private evaluator repository,",
          "and the run record refuses to carry them at all - a structured scorer result naming hidden evaluator",
          "material is rejected rather than written. **No numeric result is withheld.**", "",
          "No hash is published in place of a withheld identifier. A digest would not be a redaction here: the",
          "public rule catalog and the public corpus together bound the preimage space to a few thousand",
          "candidates, so any such digest is recoverable by enumeration. Traceability instead runs through values",
          "that are already public and already high-entropy - the run id, the task sha256, and the evaluator",
          "manifest digests above. Those identify the evidence uniquely without disclosing what it says.", "",
          "---", "", "## Recomputation", "",
          f"Every headline figure in this package was recomputed from the {INV['total_rows']} run/attempt rows",
          "and compared against the frozen per-experiment analysis artifact:",
          f"**{len(AUDIT)} checks, {len(AUDIT_MISMATCHES)} mismatches.** The full list is in workbook sheet",
          "`20_RECOMPUTATION_AUDIT`. Regenerate this package with:", "",
          "```sh", "python study-results/professor-delivery/_build/build_professor_delivery.py", "```", ""]
EV_PATH = OUT / "AFCI_Professor_Evidence_Map.md"
EV_PATH.write_text("\n".join(EV_MD), encoding="utf-8", newline=LF)
WRITTEN.append(EV_PATH)
print(f"wrote {EV_PATH}")

# --------------------------------------------------------------------------- #
# README
# --------------------------------------------------------------------------- #

README = f"""# AFCI-Bench - professor results delivery package

**Compiled {COMPILED}** from `study-results/` on branch `{GIT['branch']}`, pinned to evidence
commit `{GIT['evidence_commit'][:12]}` (*{GIT['evidence_subject']}*) - the last change to the
evidence this package reports.

This package is safe to send outside the private evaluator repository. It carries
no private opportunity identifier, rule identifier, evaluator path, hidden
architecture rule, or hidden source/target label.

## Start here

| file | what it is |
| --- | --- |
| `AFCI_Professor_Results_Summary.md` | the 16-section narrative report - read this first |
| `AFCI_Professor_Results_Summary.pdf` | the same report, rendered |
| `AFCI_Professor_Results.xlsx` | 20 sheets: every matrix, every decision clause, every run |
| `AFCI_Professor_Full_Run_Results.csv` | all {INV['total_rows']} run/attempt rows, excluded ones included |
| `AFCI_Professor_Metric_Definitions.md` | what each metric means and which way is better |
| `AFCI_Professor_Evidence_Map.md` | summary number -> analysis artifact -> run record -> raw artifact |

## Workbook sheets

| sheet | contents |
| --- | --- |
| `01_EXECUTIVE_SUMMARY` | programme totals, three result cards, the current research conclusion |
| `02_EXPERIMENT_INVENTORY` | one row per experiment set, including the one not started |
| `03_ALL_RUNS` | all {INV['total_rows']} run/attempt records, every public-safe column |
| `04_FUNCTIONAL_MATRIX` | functional correctness by experiment, task and condition |
| `05_ARCHITECTURE_MATRIX` | architecture evidence, and what produced none |
| `06_TOKEN_MATRIX` | input and output tokens, by arm and reset state |
| `07_COST_MATRIX` | provider cost, with coverage stated before every figure |
| `08_TIME_MATRIX` | MODEL_WALL_SECONDS |
| `09_EXPLORATION_TOOLS` | exploration, tool calls, unique files, per tool type |
| `10_REWORK_CHANGE_MATRIX` | edits, re-edits, turns, files changed, LOC |
| `11_RESET_RECOVERY` | Sonnet only - reset overhead by task and condition |
| `12_SONNET_VS_HAIKU` | descriptive cross-model matrix, never pooled |
| `13_V1_HISTORICAL` | v1 results and the seven limitations that bound them |
| `14_DIAGNOSTICS` | PT08, PT09, PT10 in per-repetition detail |
| `15_EXCLUSIONS` | every excluded observation and every missing metric |
| `16_DECISION_MATRIX` | each frozen decision clause: criterion, threshold, observed, PASS/FAIL |
| `17_METRIC_AVAILABILITY` | metric x experiment availability grid |
| `18_EVIDENCE_MAP` | traceability, repository anchors, hashes |
| `19_METRIC_DEFINITIONS` | plain-English definitions |
| `20_RECOMPUTATION_AUDIT` | the {len(AUDIT)} checks behind every figure in this package |

Five descriptive charts are embedded, on sheets 04, 05, 06, 07 and 12. None
carries a significance marking, because no significance test exists in this
programme. The ratio charts draw a parity line at 1.00 so the direction is
readable without reading the axis.

## Two rules that hold everywhere

1. **A missing metric is a blank, never a zero.** A blank cell means the metric
   was not captured for that run. Reading it as 0 would invent an observation.
2. **Every aggregate is published beside its coverage count.** A median over 8
   pairs and a median over 16 pairs are different claims, and the package says
   which it is every time.

## What this package is not

- It is **not confirmatory**. Of {INV['total_rows']} run rows, {INV['eligible']}
  are eligible for any analysis, all {INV['eligible']} belong to two
  non-confirmatory pilots, and **0** are confirmatory.
- It contains **no p-value, confidence interval, effect size or power estimate**,
  because none exists in this programme.
- It is a **secondary artifact**. Where it and a primary artifact disagree, the
  primary artifact wins.

## Started, then halted - no results

`V2_BACKSTAGE_PILOT`, the Backstage real-repository architecture pilot, began
execution and was **halted part-way**. It contributes **no analysable result**.

| field | value |
| --- | --- |
| status | **{REG['V2_BACKSTAGE_PILOT']['status']}** |
| planned runs | {REG['V2_BACKSTAGE_PILOT']['planned_runs']} (3 tasks x 2 conditions x 3 repetitions, NON_RESET, 9 paired blocks) |
| attempted / valid observations / **usable** | {REG['V2_BACKSTAGE_PILOT']['attempted_runs']} / {REG['V2_BACKSTAGE_PILOT']['completed_runs']} / **{REG['V2_BACKSTAGE_PILOT']['usable_runs']}** |
| run rows here | {sum(1 for r in RUNS if r['experiment_id'] == 'V2_BACKSTAGE_PILOT')}, all `eligible_for_analysis = false` |
| consumed | $10.93 provider cost, ~5.3 h model wall time |
| decisions | `SL-V2-BACKSTAGE-PILOT-01` (freeze), `SL-V2-BACKSTAGE-PILOT-02` (halt) |
| attempt record | `../07_backstage_pilot_attempt_1_halted/` |

Two scheduled observations were severed mid-task by a local network failure
(`INFRA_API_TRANSPORT`), *below* the turn ceiling. That is rerun-eligible under
`FAILURE_RERUN_POLICY.md` S2, but the launcher refuses any run id absent from
the frozen plan, so a replacement needs a recorded protocol amendment - and S5
directs repeated infrastructure failure to be **escalated, not silently
re-attempted** (`TD-N06`, open). Execution stopped rather than improvising.

**No `C1`-vs-`C4` comparison, arm total, ratio, median or continuation criterion
was computed, and none may be derived.** The schedule is 11 rows short, the arms
are unbalanced, no paired block is both complete and usable, and
`SL-V2-BACKSTAGE-PILOT-01` S11.3 forbids a confirmatory claim from this pilot
even when complete. **No matrix cell, chart point or figure in this package
comes from it.**

## Backstage attempt 2 - COMPLETE

`V2_BACKSTAGE_PILOT_ATTEMPT_2` is a **wholly new** 18-run execution of the same
frozen science, pre-registered by `SL-V2-BACKSTAGE-PILOT-03` and executed in
full on 2026-09-22.

| field | value |
| --- | --- |
| status | **{REG['V2_BACKSTAGE_PILOT_ATTEMPT_2']['status']}** |
| planned runs | {REG['V2_BACKSTAGE_PILOT_ATTEMPT_2']['planned_runs']} (3 tasks x 2 conditions x 3 repetitions, NON_RESET, 9 paired blocks) |
| attempted / completed / **usable** | {REG['V2_BACKSTAGE_PILOT_ATTEMPT_2']['attempted_runs']} / {REG['V2_BACKSTAGE_PILOT_ATTEMPT_2']['completed_runs']} / **{REG['V2_BACKSTAGE_PILOT_ATTEMPT_2']['usable_runs']}** |
| run rows here | {sum(1 for r in RUNS if r['experiment_id'] == 'V2_BACKSTAGE_PILOT_ATTEMPT_2')} |
| infrastructure-invalid attempts / retries used | 0 / 0 |
| decisions | `SL-V2-BACKSTAGE-PILOT-01` (science, unchanged), `SL-V2-BACKSTAGE-PILOT-03` (attempt-2 execution controls) |

It reused the substrate, the three tasks and their bytes, the architecture
packet, the model, the effort level, the runtime, both conditions, the reset
state, the repetitions, the endpoints, the oracles, the scorer and the
continuation rule **unchanged**, and changed five execution controls: the turn
ceiling 64 -> 96, the Bash allowlist 8 -> 15 rules, a network preflight that
refuses before the task is delivered, 18 pre-authorised infrastructure-retry
identities, and real-destination path validation.

### The frozen continuation rule returned NO ARCHITECTURE SIGNAL

`SL-V2-BACKSTAGE-PILOT-01` S11.1 requires **all three** criteria:

| clause | statement | observed | verdict |
| --- | --- | --- | --- |
| 11.1.1 | C4 has fewer target-violation runs than C1 overall | C1 2/9, C4 1/9 | **PASS** |
| 11.1.2 | C4 has fewer target violations in >=2 of 3 tasks | fewer in **1** of 3 (T5 only) | **FAIL** |
| 11.1.3 | C4 FUNCTIONAL_VALID no more than 1 below C1 | C1 4, C4 4 | **PASS** |

> **NO ARCHITECTURE SIGNAL - DO NOT AUTOMATICALLY EXPAND**

Criterion 11.1.2 fails on **ties at zero, not on C4 being worse**: T1 and T2
produced zero target violations in *both* arms, so neither can show C4 as
"fewer". Only T5 discriminated. This is the same architecture-floor failure
mode the lower-model pilot hit, here partial rather than total.

**T1 is a task-instrument failure, not a model result.** All six T1 runs - both
arms, all three repetitions - passed exactly 3 of 4 semantic cases and failed
the *same single case* every time, while both controlled T1 references pass
that case in the frozen reference matrix. The oracle is satisfiable; the
model-facing task statement does not ask for the behaviour it checks. T1
therefore contributes 0 functionally valid runs and 0 target violations to
*either* arm - inert on both endpoints. Nothing was changed in response.

Efficiency is secondary (S11.2) and cannot override S11.1. Its medians rest on
only **3 of 9** paired blocks, because no T1 run is functionally valid, and are
descriptive only at that coverage.

**Attempt 1 is retained above and is never pooled with, replaced by, or re-run
under attempt 2.** No scientific outcome from attempt 1 was used to change any
task, architecture packet, oracle, scorer, threshold, endpoint, metric or
treatment definition - and none could have been, because no `C1`-vs-`C4`
comparison was ever computed from it. Attempt 1's **$10.93** and attempt 2's
**$32.19** are reported separately and never combined into a treatment
estimate.

## Provenance

Reporting and export only. Producing this package executed no benchmark
observation, invoked no model, and changed no task definition, architecture
document, scorer, threshold, run plan, condition, raw run artifact or prior
analysis. The private evaluator repository received one result-provenance
commit for the Backstage attempt-2 execution - an index, its leakage-validator
entries and its phase-aware launcher guards, no task, scorer or threshold - and
**nothing was pushed to it**.

Every figure was recomputed from the run/attempt rows and checked against the
frozen per-experiment analysis artifacts: **{len(AUDIT)} checks,
{len(AUDIT_MISMATCHES)} mismatches**. Regenerate with:

```sh
python study-results/professor-delivery/_build/build_professor_delivery.py
```

`_build/` holds that generator. It reads only `study-results/` and writes only
this directory.

The build is **byte-reproducible**: running it twice on unchanged evidence
produces identical files, down to the SHA-256 of the workbook and the PDF. So if
you regenerate the package and `git status` is clean, nothing in it was edited by
hand after generation.
"""
README_PATH = OUT / "README.md"
README_PATH.write_text(README, encoding="utf-8", newline=LF)
WRITTEN.append(README_PATH)
print(f"wrote {README_PATH}")


# =========================================================================== #
#                                   PDF
# =========================================================================== #

def build_pdf(md_text, path, doc_title):
    """Render the summary markdown deterministically with reportlab.

    reportlab's built-in fonts use WinAnsi, so characters outside it are mapped
    to ASCII equivalents rather than dropped silently."""
    import re as _re
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                    Spacer, Table, TableStyle)

    TRANSLIT = {"→": "->", "←": "<-", "≤": "<=", "≥": ">=", "×": "x",
                "−": "-", "–": "-", "—": "-", "‘": "'", "’": "'",
                "“": '"', "”": '"', "…": "...", " ": " ", "Δ": "delta",
                "•": "-", "±": "+/-"}

    def clean(t):
        for k, v in TRANSLIT.items():
            t = t.replace(k, v)
        return "".join(ch if ord(ch) < 256 else "?" for ch in t)

    def inline(t):
        t = clean(t)
        t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        t = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = _re.sub(r"`(.+?)`", r'<font face="Courier" size="7.5">\1</font>', t)
        t = _re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", t)
        return t

    ss = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=ss["BodyText"], fontName="Helvetica", fontSize=8.8,
                          leading=12.2, spaceAfter=5, alignment=TA_LEFT)
    h1 = ParagraphStyle("h1", parent=body, fontSize=17, leading=21, spaceBefore=4, spaceAfter=9,
                        textColor=colors.HexColor("#1F3864"), fontName="Helvetica-Bold")
    h2 = ParagraphStyle("h2", parent=body, fontSize=12.5, leading=16, spaceBefore=13, spaceAfter=6,
                        textColor=colors.HexColor("#1F3864"), fontName="Helvetica-Bold")
    h3 = ParagraphStyle("h3", parent=body, fontSize=10, leading=13, spaceBefore=8, spaceAfter=4,
                        textColor=colors.HexColor("#2E4A6B"), fontName="Helvetica-Bold")
    bullet = ParagraphStyle("bullet", parent=body, leftIndent=11, bulletIndent=2, spaceAfter=3)
    quote = ParagraphStyle("quote", parent=body, leftIndent=10, rightIndent=8, borderPadding=5,
                           backColor=colors.HexColor("#F2F5FA"), spaceBefore=5, spaceAfter=7,
                           fontName="Helvetica-Oblique")
    cell = ParagraphStyle("cell", parent=body, fontSize=6.9, leading=8.6, spaceAfter=0)
    cellh = ParagraphStyle("cellh", parent=cell, fontName="Helvetica-Bold", textColor=colors.white)

    flow, i = [], 0
    lines = md_text.split("\n")
    AVAIL = A4[0] - 32 * mm

    def flush_table(rows):
        if not rows:
            return
        ncols = max(len(r) for r in rows)
        rows = [r + [""] * (ncols - len(r)) for r in rows]
        weights = [max(4, max(len(r[c]) for r in rows) ** 0.62) for c in range(ncols)]
        total = sum(weights)
        widths = [AVAIL * w / total for w in weights]
        data = [[Paragraph(inline(c), cellh if ri == 0 else cell) for c in row] for ri, row in enumerate(rows)]
        t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B7C3D6")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 3.5), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F5FA")]),
        ]))
        flow.append(Spacer(1, 3))
        flow.append(t)
        flow.append(Spacer(1, 7))

    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|"):
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(_re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                    block.append(cells)
                i += 1
            flush_table(block)
            continue
        if ln.startswith("# "):
            flow.append(Paragraph(inline(ln[2:]), h1))
        elif ln.startswith("## "):
            flow.append(Paragraph(inline(ln[3:]), h2))
        elif ln.startswith("### "):
            flow.append(Paragraph(inline(ln[4:]), h3))
        elif ln.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip())
                i += 1
            flow.append(Paragraph(inline(" ".join(buf)), quote))
            continue
        elif _re.match(r"^\s*[-*] ", ln):
            flow.append(Paragraph(inline(_re.sub(r"^\s*[-*] ", "", ln)), bullet, bulletText="•"))
        elif _re.match(r"^\s*\d+\. ", ln):
            m = _re.match(r"^\s*(\d+)\. (.*)", ln)
            buf = [m.group(2)]
            i += 1
            while i < len(lines) and _re.match(r"^\s{2,}\S", lines[i]):
                buf.append(lines[i].strip())
                i += 1
            flow.append(Paragraph(inline(" ".join(buf)), bullet, bulletText=f"{m.group(1)}."))
            continue
        elif ln.strip() == "---":
            flow.append(Spacer(1, 5))
        elif ln.strip() == "":
            pass
        else:
            buf = [ln]
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("|", "#", ">", "-", "*")) \
                    and not _re.match(r"^\s*\d+\. ", lines[i]):
                buf.append(lines[i])
                i += 1
            flow.append(Paragraph(inline(" ".join(x.strip() for x in buf)), body))
            continue
        i += 1

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawString(16 * mm, 10 * mm, clean(doc_title))
        canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, f"page {canvas.getPageNumber()}")
        canvas.restoreState()

    # invariant=1 fixes the embedded creation date and document id, so rebuilding
    # an unchanged report produces a byte-identical PDF instead of a spurious diff.
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                      topMargin=15 * mm, bottomMargin=16 * mm, title=doc_title,
                      author="AFCI-Bench", invariant=1).build(flow, onFirstPage=footer,
                                                              onLaterPages=footer)


PDF_PATH = OUT / "AFCI_Professor_Results_Summary.pdf"
try:
    build_pdf(SUMMARY, PDF_PATH, f"AFCI-Bench results delivery - compiled {COMPILED}")
    WRITTEN.append(PDF_PATH)
    print(f"wrote {PDF_PATH}")
except Exception as exc:                                     # noqa: BLE001
    print(f"PDF NOT WRITTEN: {exc}")


# =========================================================================== #
#                          FINAL AUDIT REPORT (stdout)
# =========================================================================== #

print()
print(f"AUDIT: {len(AUDIT)} checks, {len(AUDIT_MISMATCHES)} mismatches")
for a in AUDIT_MISMATCHES:
    print("  MISMATCH", a)
print()
for p in WRITTEN:
    print(f"{p.stat().st_size:>10,} bytes  {p}")

