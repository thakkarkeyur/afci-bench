"""Validate the v2 architecture context and rule catalog (Part A).

The canonical architecture context must be a byte-stable, condition/model-free
payload whose SHA-256 is recorded in the catalog; the catalog must parse, be a
closed schema-valid object, mirror the real repository dependency evidence
(root .eslintrc.json depConstraints), be fully cross-referenced with the
traceability CSV, and claim no validated rule yet (G1/G6 open). Pure file
inspection; no model is invoked.
"""
import csv
import hashlib
import json
import re
from pathlib import Path

import yaml  # PyYAML; part of the study-v2 dependency base
import context_audit as ca  # importable via conftest.py (harness dir on sys.path)

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"
SCHEMAS = REPO / "experiments" / "v2" / "schemas"

CONTEXT = DOCS_V2 / "ARCHITECTURE_CONTEXT.md"
CATALOG = DOCS_V2 / "ARCHITECTURE_RULE_CATALOG.yml"
CATALOG_SCHEMA = SCHEMAS / "architecture_rule_catalog.schema.json"
TRACE = DOCS_V2 / "ARCHITECTURE_RULE_TRACEABILITY.csv"


def _catalog():
    return yaml.safe_load(CATALOG.read_text(encoding="utf-8"))


def test_context_is_lf_only_and_hash_matches_catalog():
    raw = CONTEXT.read_bytes()
    assert b"\r\n" not in raw, "architecture context must be LF-only for a stable hash"
    digest = hashlib.sha256(raw).hexdigest()
    cat = _catalog()
    assert cat["architecture_context"]["sha256"] == digest, (
        f"recorded hash {cat['architecture_context']['sha256']} != actual {digest}"
    )
    assert cat["architecture_context"]["bytes"] == len(raw)
    assert cat["architecture_context"]["path"] == "docs/v2/ARCHITECTURE_CONTEXT.md"


def test_context_has_no_condition_model_or_benchmark_leakage():
    text = CONTEXT.read_text(encoding="utf-8")
    # No condition identifiers, model names, or benchmark/experiment framing may
    # appear in the payload delivered as pure architecture content.
    assert re.findall(r"\bC[1-4]\b", text) == [], "condition identifier leaked"
    for token in ("Sonnet", "Opus", "Haiku", "Fable", "Claude"):
        assert token not in text, f"model name '{token}' leaked into architecture content"
    for pat in (r"(?i)benchmark", r"(?i)\bcondition\b", r"(?i)oracle", r"(?i)\btask\b", r"(?i)prompt"):
        assert re.findall(pat, text) == [], f"forbidden token matching {pat!r} in architecture content"


def test_catalog_is_schema_valid_closed_object():
    schema = json.loads(CATALOG_SCHEMA.read_text(encoding="utf-8"))
    assert schema["type"] == "object" and schema.get("additionalProperties") is False
    assert schema["$id"].endswith("architecture_rule_catalog.schema.json")
    errors = ca.validate_against_schema(_catalog(), schema)
    assert errors == [], errors


def test_catalog_matrix_matches_real_eslint_depconstraints():
    cat = _catalog()
    esl = json.loads((REPO / ".eslintrc.json").read_text(encoding="utf-8"))
    dc = esl["overrides"][0]["rules"]["@nx/enforce-module-boundaries"][1]["depConstraints"]
    esl_map = {c["sourceTag"]: sorted(c["onlyDependOnLibsWithTags"]) for c in dc}
    cat_map = {k: sorted(v) for k, v in cat["allowed_dependencies"].items()}
    assert cat_map == esl_map, f"catalog matrix drifted from .eslintrc depConstraints: {cat_map} != {esl_map}"


def test_rules_are_unique_and_cross_referenced_with_traceability():
    cat = _catalog()
    rule_ids = [r["rule_id"] for r in cat["rules"]]
    assert len(rule_ids) == len(set(rule_ids)), "duplicate rule ids"
    with open(TRACE, newline="", encoding="utf-8") as fh:
        trace_ids = [row["rule_id"] for row in csv.DictReader(fh)]
    assert sorted(trace_ids) == sorted(rule_ids), (
        f"catalog and traceability rule sets differ: {set(rule_ids) ^ set(trace_ids)}"
    )


def test_no_rule_is_marked_validated_yet():
    # Oracle/guard validation (G1/G6, TD-B12) is not performed in this package.
    for r in _catalog()["rules"]:
        assert r["validation_status"] in {"not-validated", "partial"}, (
            f"{r['rule_id']} must not be marked validated before G1/G6"
        )


def test_dependency_rules_are_excluded_from_agent_ci():
    # Every architecture rule is invisible to the coding model's CI; dependency
    # rules are additionally enforced in repository CI (ESLint boundaries).
    for r in _catalog()["rules"]:
        status = r["agent_visible_enforcement_status"]
        assert status.startswith("excluded-from-agent-ci"), r["rule_id"]
        if r["category"] == "dependency-direction":
            assert status == "excluded-from-agent-ci-enforced-in-repository-ci", r["rule_id"]
            assert r["oracle_implementation_status"] == "implemented", r["rule_id"]
        else:
            assert status == "excluded-from-agent-ci-no-automated-enforcement", r["rule_id"]
            # Non-dependency rules are not implemented as oracle checkers in this package.
            assert r["oracle_implementation_status"] in {"stub", "not-implemented"}, r["rule_id"]


def test_at_least_one_implemented_automated_dependency_rule():
    cat = _catalog()
    dep_impl = [
        r for r in cat["rules"]
        if r["category"] == "dependency-direction"
        and r["evaluation"] == "automated"
        and r["oracle_implementation_status"] == "implemented"
    ]
    assert dep_impl, "at least the dependency-direction reference checker must be implemented"
