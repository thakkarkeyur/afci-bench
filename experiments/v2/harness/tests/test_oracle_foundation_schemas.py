"""Validate the new oracle-foundation schemas (Part E).

evaluator_manifest, architecture_finding, and architecture_rule_catalog must each
be a valid, closed object schema that accepts a well-formed example and rejects a
malformed one. Also checks that the committed evaluator-manifest TEMPLATE carries
no task-specific answers (answers_populated=false, empty opportunities and
legitimate alternatives). Reuses the dependency-free subset validator. No model is
invoked.
"""
import json
from pathlib import Path

import yaml
import context_audit as ca

REPO = Path(__file__).resolve().parents[4]
SCHEMAS = REPO / "experiments" / "v2" / "schemas"
TEMPLATE = REPO / "experiments" / "v2" / "manifests" / "evaluator_manifest.template.json"
CATALOG = REPO / "docs" / "v2" / "ARCHITECTURE_RULE_CATALOG.yml"

NEW_SCHEMAS = [
    "evaluator_manifest.schema.json",
    "architecture_finding.schema.json",
    "architecture_rule_catalog.schema.json",
]


def _load(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def _finding_example():
    return {
        "schema_version": "1.0.0",
        "evaluator": {
            "name": "afci-arch-oracle",
            "version": "0.1.0-dev",
            "engine": "typescript-compiler-api",
            "alias_aware": True,
            "deterministic": True,
        },
        "manifest_ref": {
            "manifest_id": "EM-X",
            "manifest_version": "1",
            "manifest_sha256": "a" * 64,
            "status": "frozen",
            "invalidated": False,
        },
        "base_sha": "0" * 40,
        "snapshot_ref": {"id": "snap", "sha256": None},
        "scored_at": None,
        "rules_evaluated": [
            {
                "rule_id": "AR-DEP-001",
                "evaluation_mode": "automated",
                "oracle_implementation_status": "implemented",
                "status": "evaluated",
            }
        ],
        "findings": [
            {
                "finding_id": "F1",
                "rule_id": "AR-DEP-003",
                "opportunity_id": None,
                "violation": True,
                "status": "VIOLATION",
                "severity": "blocker",
                "evaluation_mode": "automated",
                "automated": True,
                "confidence": "certain",
                "importer_layer": "core",
                "target_layer": "infra",
                "evidence_paths": ["libs/core/src/index.ts"],
                "evidence_locations": [{"path": "libs/core/src/index.ts", "line": 1, "column": 1, "snippet": None}],
                "resolution_chain": ["import '@afci-bench/infra' -> libs/infra/src/index.ts"],
                "message": "core must not depend on infra",
            }
        ],
        "raw_violation_count": 1,
        "opportunity_accounting": {
            "applicable_opportunity_count": 0,
            "fixed_opportunity_count": 0,
            "violated_opportunity_count": 0,
            "absent_opportunity_count": 0,
        },
        "production_source": {
            "policy_id": "PSP-V1",
            "production_file_count": 6,
            "excluded_file_count": 2,
            "excluded_paths": ["apps/api/jest.config.ts", "apps/api/src/app.spec.ts"],
        },
        "deterministic_order": True,
        "verdict": "VIOLATIONS",
    }


def _manifest_example():
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def _catalog_example():
    return yaml.safe_load(CATALOG.read_text(encoding="utf-8"))


EXAMPLES = {
    "evaluator_manifest.schema.json": _manifest_example,
    "architecture_finding.schema.json": _finding_example,
    "architecture_rule_catalog.schema.json": _catalog_example,
}


def test_new_schemas_are_valid_closed_object_schemas():
    for name in NEW_SCHEMAS:
        schema = _load(name)
        assert schema["type"] == "object", name
        assert schema.get("additionalProperties") is False, f"{name} must be closed"
        assert isinstance(schema.get("required"), list) and schema["required"], name
        assert schema["$id"].endswith(name), name


def test_valid_examples_pass_validation():
    for name, builder in EXAMPLES.items():
        schema = _load(name)
        errors = ca.validate_against_schema(builder(), schema)
        assert errors == [], f"{name}: {errors}"


def test_missing_required_field_is_rejected():
    for name, builder in EXAMPLES.items():
        schema = _load(name)
        inst = builder()
        victim = schema["required"][1]
        inst.pop(victim, None)
        errors = ca.validate_against_schema(inst, schema)
        assert errors, f"{name}: removing {victim} should fail validation"


def test_extra_property_is_rejected():
    for name, builder in EXAMPLES.items():
        schema = _load(name)
        inst = builder()
        inst["totally_unexpected_key"] = 1
        errors = ca.validate_against_schema(inst, schema)
        assert errors, f"{name}: extra property should fail a closed schema"


def test_committed_manifest_template_carries_no_task_answers():
    tpl = _manifest_example()
    schema = _load("evaluator_manifest.schema.json")
    assert ca.validate_against_schema(tpl, schema) == []
    assert tpl["answers_populated"] is False, "committed manifest must not populate answers"
    assert tpl["opportunities"] == [], "template must not enumerate task opportunities"
    assert tpl["legitimate_alternatives"] == [], "template must not list legitimate answers"
    assert tpl["hidden_test_refs"] == [], "template must not reference hidden tests"
    assert tpl["task_id"] is None, "template must not bind a task id"
    assert tpl["status"] == "template"
