"""Structural and invariant validation for every v2 CSV matrix.

Covers the work-package requirement that *every* CSV created in study v2 has the
exact number of columns declared by its header (parsed with the real csv module,
so quoted fields are handled), plus protocol invariants that must hold before any
data collection: no claim is marked ``supported`` and no pilot gate is marked
``passed``. Pure file inspection; no model is invoked.
"""
import csv
import glob
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"
EXP_V2 = REPO / "experiments" / "v2"


def _all_v2_csvs():
    paths = sorted(glob.glob(str(DOCS_V2 / "*.csv"))) + sorted(
        glob.glob(str(EXP_V2 / "**" / "*.csv"), recursive=True)
    )
    return [Path(p) for p in paths]


def _rows(path: Path):
    with open(path, newline="", encoding="utf-8") as fh:
        return [r for r in csv.reader(fh) if r]  # drop trailing blank rows


# --------------------------------------------------------------------------- #
# Column-count integrity for every v2 CSV
# --------------------------------------------------------------------------- #
def test_v2_csvs_exist():
    assert _all_v2_csvs(), "no v2 CSVs found"


@pytest.mark.parametrize("path", _all_v2_csvs(), ids=lambda p: p.name)
def test_every_row_matches_header_width(path):
    rows = _rows(path)
    assert rows, f"{path} is empty"
    header = rows[0]
    assert len(header) >= 2, f"{path} header too narrow"
    assert len(set(header)) == len(header), f"{path} has duplicate header columns"
    width = len(header)
    for i, row in enumerate(rows[1:], start=2):
        assert len(row) == width, (
            f"{path.name} row {i} has {len(row)} columns, header declares {width}: {row[:2]}"
        )
    assert len(rows) >= 2, f"{path} has a header but no data rows"


# --------------------------------------------------------------------------- #
# The known matrices are present
# --------------------------------------------------------------------------- #
def test_required_matrices_present():
    for name in (
        "CONDITION_MATRIX.csv",
        "RESET_CHECKPOINT_MATRIX.csv",
        "CLAIMS_CONSTRUCTS_METRICS.csv",
        "TASK_RULE_MATRIX.csv",
        "TASK_ACCEPTANCE_MATRIX.csv",
        "TASK_LAYER_MATRIX.csv",
        "ORACLE_TRACEABILITY.csv",
        "MODEL_REGISTRY.csv",
        "MODEL_CONFIGURATION_MATRIX.csv",
        "REVIEWER_RESPONSE_MATRIX.csv",
        "PILOT_GATE_MATRIX.csv",
        "RUN_ARTIFACT_MATRIX.csv",
    ):
        assert (DOCS_V2 / name).is_file(), f"missing matrix {name}"


# --------------------------------------------------------------------------- #
# MODEL_CONFIGURATION_MATRIX regression: the cli_version row is now well-formed
# --------------------------------------------------------------------------- #
def test_model_configuration_matrix_is_13_wide():
    rows = _rows(DOCS_V2 / "MODEL_CONFIGURATION_MATRIX.csv")
    assert len(rows[0]) == 13
    cli = [r for r in rows if r[0] == "cli_version"]
    assert cli and len(cli[0]) == 13, "cli_version row must have 13 columns"


# --------------------------------------------------------------------------- #
# Claim matrix schema + 'no supported before data' invariant
# --------------------------------------------------------------------------- #
def test_claims_matrix_schema_and_status():
    path = DOCS_V2 / "CLAIMS_CONSTRUCTS_METRICS.csv"
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        expected = [
            "claim_id", "candidate_claim", "construct", "direct_metric",
            "secondary_metric", "research_question", "unit_of_analysis",
            "aggregation", "confirmatory_or_exploratory", "required_evidence",
            "unsupported_claim_risk", "status", "notes",
        ]
        assert reader.fieldnames == expected, reader.fieldnames
        # CON-AC is narrowed to layered dependency-direction conformance (E1);
        # CON-ACB is broader architectural conformance that E1 does NOT directly
        # measure (suite-classification decision D).
        constructs = {"CON-AC", "CON-ACB", "CON-TC", "CON-RR", "CON-EC", "CON-IE", "CON-AI"}
        rows = list(reader)
    assert rows, "no claims"
    for r in rows:
        assert r["status"].strip().lower() == "candidate", (
            f"{r['claim_id']} status must be candidate before data collection, got {r['status']!r}"
        )
        assert r["construct"] in constructs, f"{r['claim_id']} unknown construct {r['construct']}"
        assert r["confirmatory_or_exploratory"] in {"confirmatory", "exploratory"}


# --------------------------------------------------------------------------- #
# Gate matrix: G1-G8 present, none passed
# --------------------------------------------------------------------------- #
def test_gate_matrix_g1_to_g8_none_passed():
    path = DOCS_V2 / "PILOT_GATE_MATRIX.csv"
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    ids = [r["gate_id"] for r in rows]
    assert ids == [f"G{i}" for i in range(1, 9)], ids
    for r in rows:
        status = r["status"].strip().lower()
        assert "not evaluated" in status, f"{r['gate_id']} must be not-evaluated, got {status!r}"
        assert "passed" not in status, f"{r['gate_id']} must not be marked passed"
