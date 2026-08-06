"""Validate the v2 run/result JSON schemas.

Each schema must be valid JSON, a closed object schema, and must accept a
well-formed example while rejecting a malformed one. Validation reuses the
repository's dependency-free ``context_audit.validate_against_schema`` (the same
subset validator used for the context-audit schema), so no new dependency is
introduced. Pure file inspection; no model is invoked.
"""
import copy
import json
from pathlib import Path

import context_audit as ca  # importable via conftest.py (harness dir on sys.path)

SCHEMAS = Path(__file__).resolve().parents[2] / "schemas"

SCHEMA_FILES = [
    "run_manifest.schema.json",
    "oracle_result.schema.json",
    "acceptance_result.schema.json",
    "guard_result.schema.json",
]

# Fields the work package requires the run schema to support.
RUN_REQUIRED = [
    "run_id", "task_id", "condition", "reset_state", "model", "repetition",
    "base_sha", "protocol_versions", "environment_fingerprint", "context_audit",
    "prompt_hashes", "phases", "exit_reason", "ci_attempts", "agent_visible_ci",
    "acceptance_result", "oracle_result", "guard_result", "tokens", "time",
    "iterations", "artifact_hashes", "rerun", "exclusion_status", "budget",
]


def _load(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def _run_manifest_example():
    return {
        "schema_version": "1.0.0",
        "run_id": "example-run-0001",
        "task_id": "TASK-TEMPLATE-A",
        "condition": "C4",
        "reset_state": "non-reset",
        "model": {
            "label": "Opus 4.8",
            "exact_model_id": "claude-opus-4-8",
            "resolved_model_id": None,
            "effort_input": "xhigh",
        },
        "repetition": 1,
        "base_sha": "0" * 40,
        "protocol_versions": {
            "condition_spec": "1.0.0",
            "oracle_spec": "1.0.0",
            "acceptance_spec": "1.0.0",
            "reset_protocol": "1.0.0",
            "model_execution_config": "1.0.0",
            "guard_spec": "1.0.0",
        },
        "environment_fingerprint": {
            "os": "linux",
            "cli_version": "2.1.209",
            "agent_sdk_version": "0.3.212",
            "node_version": "20.20.2",
            "npm_version": "10.8.2",
            "container_image_digest": None,
            "lockfile_sha256": "0" * 64,
        },
        "context_audit": {
            "verdict": "CLEAN",
            "report_path": "context_audit.json",
            "report_sha256": "0" * 64,
        },
        "prompt_hashes": {
            "system_prompt_sha256": None,
            "task_prompt_sha256": "a" * 64,
            "injected_context_sha256": "b" * 64,
            "reset_prompt_sha256": None,
        },
        "phases": [{"phase": "single", "start_index": 0, "exit_reason": "COMPLETED"}],
        "exit_reason": "COMPLETED",
        "ci_attempts": 1,
        "agent_visible_ci": {
            "command": "npm run ci:agent",
            "architecture_enforcement_excluded": True,
            "hidden_checks_excluded": True,
        },
        "acceptance_result": {
            "status": "PENDING",
            "artifact_path": "acceptance_result.json",
            "artifact_sha256": None,
        },
        "oracle_result": {
            "status": "PENDING",
            "artifact_path": "oracle_result.json",
            "artifact_sha256": None,
        },
        "guard_result": {
            "status": "PENDING",
            "artifact_path": "guard_result.json",
            "artifact_sha256": None,
        },
        "tokens": {"input": 0, "output": 0, "total": 0},
        "time": {"wall_clock_seconds": 0.0, "pre_reset_seconds": None, "post_reset_seconds": None},
        "iterations": 0,
        "artifact_hashes": {"patch.diff": "c" * 64},
        "rerun": {
            "is_replacement": False,
            "replaces_run_id": None,
            "replaced_by_run_id": None,
            "reason_code": None,
        },
        "exclusion_status": "EXCL_NONE",
        "budget": {
            "total_budget": None,
            "pre_reset_allowance": None,
            "pre_reset_consumed": None,
            "post_reset_allowance": None,
            "post_reset_consumed": None,
            "unit": "tokens",
        },
    }


def _oracle_example():
    """A well-formed oracle result.

    E1's accounting is the ``opportunity_accounting`` object, so the example
    carries it. The rule-based fields are retained only as legacy descriptive
    diagnostics; ``test_rule_only_accounting_is_not_sufficient_for_e1`` proves a
    result carrying *only* those cannot validate.
    """
    return {
        "schema_version": "1.0.0",
        "run_id": "example-run-0001",
        "task_id": "TASK-TEMPLATE-A",
        "condition": "C4",
        "evaluator": {"name": "nx+afci-guard", "version": "0.0.0-dev", "alias_aware": True},
        "evaluated_rules": [
            {
                "rule_id": "AR-DEP-003",
                "applicability": "applicable",
                "severity": "blocker",
                "evaluator_type": "automated",
                "satisfied": True,
                "violation_count": 0,
                "evidence_ref": "oracle_result.json",
            }
        ],
        "opportunity_accounting": {
            "applicable_opportunity_count": 2,
            "fixed_opportunity_count": 2,
            "violated_opportunity_count": 0,
            "absent_opportunity_count": 0,
        },
        "e1_analysis_eligibility": "scored",
        "raw_violation_count": 0,
        "violation_count": 0,
        "applicable_rule_count": 1,
        "rules_satisfied_count": 1,
        "satisfaction_proportion": 1.0,
        "verdict": "CONFORMANT",
    }


def _acceptance_example():
    return {
        "schema_version": "1.0.0",
        "run_id": "example-run-0001",
        "task_id": "TASK-TEMPLATE-A",
        "condition": "C4",
        "criteria": [
            {
                "criterion_id": "AC-TODO-01",
                "evaluator_type": "automated",
                "satisfied": None,
                "evidence_ref": "acceptance_result.json",
            }
        ],
        "criteria_total": 1,
        "criteria_satisfied": 0,
        "coverage_proportion": None,
        "hidden_tests": {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "pass_proportion": None,
            "suite_ref": "hidden/",
            "visible_to_model": False,
        },
        "verdict": "PENDING",
    }


def _guard_example():
    return {
        "schema_version": "1.0.0",
        "run_id": "example-run-0001",
        "task_id": "TASK-TEMPLATE-A",
        "condition": "C4",
        "guard_version": "0.0.0-dev",
        "alias_aware": True,
        "matched_path_patterns": ["@afci-bench/*"],
        "findings": [],
        "finding_count": 0,
        "validation": {
            "precision": None,
            "recall": None,
            "corpus_ref": None,
            "mutation_tests_passed": None,
        },
        "verdict": "PENDING",
    }


EXAMPLES = {
    "run_manifest.schema.json": _run_manifest_example,
    "oracle_result.schema.json": _oracle_example,
    "acceptance_result.schema.json": _acceptance_example,
    "guard_result.schema.json": _guard_example,
}


def test_schema_files_are_valid_closed_object_schemas():
    for name in SCHEMA_FILES:
        schema = _load(name)
        assert schema["type"] == "object", name
        assert schema.get("additionalProperties") is False, f"{name} must be closed"
        assert isinstance(schema.get("required"), list) and schema["required"], name
        assert schema["$id"].endswith(name), name


def test_run_manifest_supports_all_required_run_fields():
    schema = _load("run_manifest.schema.json")
    missing = [f for f in RUN_REQUIRED if f not in schema["required"]]
    assert not missing, f"run manifest missing required fields: {missing}"
    # exit_reason enum must carry both valid-outcome and infrastructure codes.
    exit_enum = set(schema["properties"]["exit_reason"]["enum"])
    for code in ("COMPLETED", "ARCH_VIOLATION", "NO_PATCH", "INFRA_API_TRANSPORT", "SETUP_CONTAMINATED"):
        assert code in exit_enum, code
    excl_enum = set(schema["properties"]["exclusion_status"]["enum"])
    assert {"EXCL_NONE", "EXCL_INFRA_SUPERSEDED", "EXCL_CONTAMINATED", "EXCL_PROTOCOL_MISMATCH"} <= excl_enum


def test_valid_examples_pass_validation():
    for name, builder in EXAMPLES.items():
        schema = _load(name)
        errors = ca.validate_against_schema(builder(), schema)
        assert errors == [], f"{name}: {errors}"


def test_missing_required_field_is_rejected():
    for name, builder in EXAMPLES.items():
        schema = _load(name)
        inst = builder()
        # drop the first required top-level field
        victim = schema["required"][1]  # skip schema_version for variety
        inst.pop(victim, None)
        errors = ca.validate_against_schema(inst, schema)
        assert errors, f"{name}: removing {victim} should fail validation"


def test_bad_enum_and_extra_property_are_rejected():
    for name, builder in EXAMPLES.items():
        schema = _load(name)
        inst = builder()
        inst["condition"] = "C9"  # not in the C1-C4 enum
        inst["totally_unexpected_key"] = 1  # additionalProperties: false
        errors = ca.validate_against_schema(inst, schema)
        assert errors, f"{name}: bad enum + extra property should fail validation"


# --------------------------------------------------------------------------- #
# E1 accounting is authoritative in oracle_result (suite-classification decision D)
# --------------------------------------------------------------------------- #
def test_oracle_result_requires_the_opportunity_accounting_block():
    """The pinned E1 fields must be REQUIRED, not optional."""
    schema = _load("oracle_result.schema.json")
    assert "opportunity_accounting" in schema["required"], (
        "opportunity_accounting carries E1's numerator and offset and must be required"
    )
    inner = schema["properties"]["opportunity_accounting"]
    for field in ("applicable_opportunity_count", "violated_opportunity_count"):
        assert field in inner["required"], f"{field} must be required inside opportunity_accounting"
    assert inner.get("additionalProperties") is False


def test_rule_only_accounting_is_not_sufficient_for_e1():
    """A result carrying ONLY the legacy rule-based accounting must not validate.

    This is the regression that keeps the superseded per-rule E1 accounting from
    being certified as a complete oracle result.
    """
    schema = _load("oracle_result.schema.json")
    inst = _oracle_example()
    inst.pop("opportunity_accounting")
    errors = ca.validate_against_schema(inst, schema)
    assert errors, (
        "an oracle result with applicable_rule_count/satisfaction_proportion but no "
        "opportunity_accounting must be rejected: it cannot supply E1"
    )


def test_applicable_rule_count_is_not_required_and_is_labelled_descriptive():
    """The inadmissible offset must never be structurally privileged."""
    schema = _load("oracle_result.schema.json")
    for field in ("applicable_rule_count", "satisfaction_proportion", "rules_satisfied_count"):
        assert field not in schema["required"], (
            f"{field} is a legacy descriptive diagnostic and must not be required"
        )
        desc = schema["properties"][field]["description"].lower()
        assert "descriptive" in desc, f"{field} must be documented as descriptive"
    rule_count_desc = schema["properties"]["applicable_rule_count"]["description"].lower()
    assert "not an admissible e1 denominator or offset" in rule_count_desc
    sat_desc = schema["properties"]["satisfaction_proportion"]["description"].lower()
    assert "not a direct architectural-conformance measurement" in sat_desc
    assert "never e1 or e2" in sat_desc


def test_oracle_result_carries_fail_closed_eligibility():
    schema = _load("oracle_result.schema.json")
    assert "e1_analysis_eligibility" in schema["required"]
    assert set(schema["properties"]["e1_analysis_eligibility"]["enum"]) == {
        "scored",
        "functional-only",
        "inactive-reserve",
    }
    inst = _oracle_example()
    inst["e1_analysis_eligibility"] = "eligible"  # not in the enum
    assert ca.validate_against_schema(inst, schema), "an invalid eligibility must fail closed"


def test_oracle_result_description_does_not_claim_broad_conformance():
    schema = _load("oracle_result.schema.json")
    blob = (schema["title"] + " " + schema["description"]).lower()
    assert "dependency-direction" in blob
    # The phrase is allowed only inside its own prohibition ("rule satisfaction is
    # NOT a direct architectural-conformance measurement"), never as a self-description.
    for idx in range(len(blob)):
        idx = blob.find("direct architectural-conformance measurement", idx)
        if idx == -1:
            break
        preceding = blob[max(0, idx - 120):idx]
        assert "not " in preceding or "never" in preceding, (
            f"the oracle result advertises itself as a broad architectural-conformance "
            f"measurement: ...{preceding[-110:]!r}"
        )
    assert "not an admissible e1 denominator or offset" in blob
    assert "not sufficient for e1" in blob
    assert "dependency direction only" in blob
