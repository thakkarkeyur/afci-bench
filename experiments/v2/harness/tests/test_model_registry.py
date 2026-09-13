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


def _yaml():
    return yaml.safe_load((DOCS_V2 / "MODEL_REGISTRY.yml").read_text(encoding="utf-8"))


def test_registry_yaml_parses_and_has_no_primary():
    y = _yaml()
    assert y["primary_model"] is None, "primary model must NOT be selected yet"
    assert "not selected" in y["primary_model_selection_status"].lower()
    ids = {m["exact_model_id"] for m in y["models"]}
    assert ids == VERIFIED_IDS, ids


def test_the_paid_activity_flag_is_an_honest_statement_of_what_has_run():
    """``no_paid_run`` WAS true and is now false, because live probes have run.

    Q1, Q8 and the context audit each start a real process against a real
    account. Leaving the flag true would have made the registry assert something
    the artifacts on disk contradict. What must stay true is the narrower claim:
    a runtime CONTROL is not a benchmark run.
    """
    y = _yaml()
    assert y["no_paid_run"] is False
    activity = y["paid_activity_to_date"].lower()
    assert "runtime control" in activity
    assert "no benchmark condition executed" in activity
    assert "no result" in activity


def test_the_diagnostic_pin_is_not_a_primary_selection():
    """SL-PT08-05 pins a model for one purpose and confers nothing wider."""
    y = _yaml()
    block = y["diagnostic_model_selection"]["PT08_DIFFICULTY_DIAGNOSTIC"]
    assert block["decision_id"] == "SL-PT08-05"
    assert block["exact_model_id"] in VERIFIED_IDS
    # the exact id, never the alias, is what the repetitions request
    assert block["selector_used_for_repetitions"] == block["exact_model_id"]
    assert block["selector_used_for_repetitions"] != block["requested_selector"]
    for flag in ("confers_no_primary_selection", "confers_no_confirmatory_eligibility"):
        assert block[flag] is True, flag
    assert block["td_b03_status"].startswith("open")
    assert y["primary_model"] is None, "a diagnostic pin must never select a primary"


def test_the_validated_runtime_version_is_not_reconciled_with_the_governed_one():
    """The installed runtime is 2.1.229; the governed toolchain value is 2.1.209.

    No version match is manufactured. The diagnostic records what it actually
    validated, the governed value is left alone, and the difference is carried
    explicitly as unresolved so no reader can mistake one for the other.
    """
    y = _yaml()
    block = y["diagnostic_model_selection"]["PT08_DIFFICULTY_DIAGNOSTIC"]
    assert block["validated_claude_code_cli_version"] == "2.1.229"
    assert block["governed_toolchain_cli_version"] == y["toolchain"]["claude_code_cli_version"]
    assert block["validated_claude_code_cli_version"] != block["governed_toolchain_cli_version"]
    assert "UNRESOLVED" in block["cli_version_discrepancy"]


def test_the_live_runtime_controls_are_recorded_as_passed():
    block = _yaml()["diagnostic_model_selection"]["PT08_DIFFICULTY_DIAGNOSTIC"]
    assert block["q1_readback"] == "PASS" and block["q1_unambiguous"] is True
    assert set(block["q1_readback_sources"]) == {"system.init.model", "modelUsage"}
    assert block["q8_invalid_model_id_rejection"] == "PASS"
    assert block["q8_invalid_model_id"] not in VERIFIED_IDS
    assert block["api_key_used"] is False
    assert block["repetitions"] == 3


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
        # The confirmatory dry-run validation is still pending for every model.
        # The one model whose runtime controls have been validated says so
        # explicitly, and says for which purpose, so a diagnostic-scoped
        # validation can never be read as the confirmatory one.
        status = r["dry_run_validation_status"].lower()
        assert "pending" in status, r["exact_model_id"]
        if "q1/q8 validated" in status:
            assert "pt08_difficulty_diagnostic only" in status
            assert "no benchmark condition executed" in status
