"""Validate the v2 model registry: YAML parses, YAML and CSV agree, only
verified models are listed, and NO primary model is selected (Sonnet/Opus must
not be chosen in this work package). Pure file inspection; no model is invoked.
"""
import csv
from pathlib import Path

import yaml  # PyYAML; part of the study-v2 dependency base

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"

VERIFIED_IDS = {
    "claude-opus-4-8",
    "claude-sonnet-5",
    "claude-haiku-4-5-20251001",
    "claude-fable-5",
}

REQUIRED_CSV_COLUMNS = [
    "model_label", "exact_model_id", "alias_status", "provider",
    "claude_code_version", "agent_sdk_version", "intended_role",
    "model_selection_status", "effort_input", "thinking_control_status",
    "workflow_control_status", "evidence_classification", "dry_run_validation_status",
]


def test_registry_yaml_parses_and_has_no_primary():
    y = yaml.safe_load((DOCS_V2 / "MODEL_REGISTRY.yml").read_text(encoding="utf-8"))
    assert y["primary_model"] is None, "primary model must NOT be selected yet"
    assert "not selected" in y["primary_model_selection_status"].lower()
    assert y["no_paid_run"] is True
    ids = {m["exact_model_id"] for m in y["models"]}
    assert ids == VERIFIED_IDS, ids


def test_registry_csv_matches_yaml_and_columns():
    y = yaml.safe_load((DOCS_V2 / "MODEL_REGISTRY.yml").read_text(encoding="utf-8"))
    with open(DOCS_V2 / "MODEL_REGISTRY.csv", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == REQUIRED_CSV_COLUMNS, reader.fieldnames
        rows = list(reader)
    csv_ids = {r["exact_model_id"] for r in rows}
    yaml_ids = {m["exact_model_id"] for m in y["models"]}
    assert csv_ids == yaml_ids == VERIFIED_IDS


def test_no_model_selected_as_primary_in_csv():
    with open(DOCS_V2 / "MODEL_REGISTRY.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        assert "not selected" in r["model_selection_status"].lower(), (
            f"{r['exact_model_id']} must not be selected as primary yet"
        )
        # dry-run validation must still be pending (no paid run performed)
        assert "pending" in r["dry_run_validation_status"].lower()
