"""Guards for `SL-PT08-02` and `SL-PT08-03`.

WHAT THIS MODULE GUARDS
-----------------------
Two Study-Lead adjudications that `SL-PT08-01` expressly deferred:

* **`SL-PT08-02`** — for ``PT08_DIFFICULTY_DIAGNOSTIC`` **only**, the harness
  ``run_record.schema.json`` is the authoritative execution-record schema,
  because it already mechanically requires every quarantine field. The pinned
  canonical ``experiments/v2/schemas/run_manifest.schema.json`` stays
  **UNCHANGED**, and its missing-firewall gap stays **UNRESOLVED** and
  **REQUIRED IN FULL** for every confirmatory / result-bearing run.
* **`SL-PT08-03`** — the diagnostic runs **three** repetitions, `C1` only,
  `PT08` only, each on a fresh process and a fresh session.

AND IN THE OTHER DIRECTION
--------------------------
The load-bearing half of this module is what it **refuses to let the repository
claim**. Nothing here asserts that the canonical schema gap is fixed, that a
model is selected, that isolation is clean, that `Q1`/`Q8` are live-validated,
that `PT08` is frozen, that `G1` is passed, that anything is run eligible, that
the diagnostic ran, or that a result exists. Several tests exist precisely to
fail if the repository ever starts claiming one of those.

The repetition count carries **no** power, precision or treatment-effect claim,
and no power calculation was performed to justify it. The `E1` accounting is
untouched.

Pure file and API inspection. No model is invoked, no benchmark runs, nothing is
frozen and no power value is produced.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

import run_governance as gov

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"

RECORD = DOCS_V2 / "PT08_DIAGNOSTIC_EXECUTION_DECISIONS.md"
SL01_RECORD = DOCS_V2 / "PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md"
SYNC_CLOSURE = DOCS_V2 / "PT08_PUBLIC_ACCOUNTING_SYNCHRONIZATION.md"

CANONICAL_SCHEMA = REPO / "experiments" / "v2" / "schemas" / "run_manifest.schema.json"
HARNESS_SCHEMA = REPO / "experiments" / "v2" / "harness" / "run_record.schema.json"

PURPOSE_NAME = "PT08_DIFFICULTY_DIAGNOSTIC"

#: The canonical result-manifest schema's content hash as this package found it.
#: `SL-PT08-02` leaves the schema UNCHANGED, so this is an equality the package
#: must keep. A deliberate, authorised future edit moves it; an accidental or
#: opportunistic one is caught here.
CANONICAL_SCHEMA_SHA256 = (
    "aded7bc599853f4034ed24fe6f2515e8b98b4f41fdb0f3177ab7da849f4e3525"
)


def _flat(path: Path) -> str:
    raw = path.read_text(encoding="utf-8").replace("*", "").replace("`", "")
    raw = re.sub(r"(?m)^\s*>\s?", "", raw)
    return re.sub(r"\s+", " ", raw).strip().lower()


@pytest.fixture(scope="module")
def purpose() -> gov.RunPurpose:
    return gov.RUN_PURPOSES[PURPOSE_NAME]


@pytest.fixture(scope="module")
def governed() -> dict:
    return gov.governed_execution_decisions()


@pytest.fixture(scope="module")
def readiness() -> gov.ReadinessReport:
    return gov.check_readiness("PT08", "C1", PURPOSE_NAME, context_verdict=None)


def _item(report: gov.ReadinessReport, name: str) -> gov.Prerequisite:
    hits = [p for p in report.prerequisites if p.item == name]
    assert len(hits) == 1, f"expected exactly one {name!r} prerequisite, got {len(hits)}"
    return hits[0]


# --------------------------------------------------------------------------- 1
# The record exists and carries both decisions in the repository's convention.


def test_the_record_exists_and_names_both_decisions():
    flat = _flat(RECORD)
    assert "sl-pt08-02" in flat
    assert "sl-pt08-03" in flat
    # the SL-<subject>-<nn> convention, and why NEW identifiers were used
    assert "sl-<subject>-<nn>" in flat
    assert "expressly deferred" in flat


def test_sl_pt08_01_is_not_edited_and_its_deferrals_still_read_true(governed):
    """The new record must not rewrite the record that deferred these questions."""
    sl01 = _flat(SL01_RECORD)
    assert "sample size: study-lead decision pending" in sl01
    assert "this record pins none" in sl01
    assert "no result schema and no runner artifact is invented here" in sl01
    assert "mandatory future runner requirements" in sl01


# --------------------------------------------------------------------------- 2
# SL-PT08-02: the diagnostic uses the harness run-record schema. (I.1)


def test_the_diagnostic_is_bound_to_the_harness_run_record_schema(purpose, governed):
    assert purpose.artifact_schema == "experiments/v2/harness/run_record.schema.json"
    assert purpose.artifact_schema_path(REPO) == HARNESS_SCHEMA
    assert HARNESS_SCHEMA.is_file()
    # and the runner re-derives that binding from the record rather than
    # asserting it
    assert (
        governed["authoritative_execution_record_schema"] == purpose.artifact_schema
    )
    assert governed["run_purpose"] == PURPOSE_NAME


def test_the_diagnostic_is_not_bound_to_the_canonical_result_manifest_schema(purpose):
    assert purpose.artifact_schema_path(REPO) != CANONICAL_SCHEMA
    assert purpose.result_bearing is False
    assert purpose.confirmatory is False


# --------------------------------------------------------------------------- 3
# The harness schema mechanically REQUIRES the firewall. (I.2, I.3, I.4, I.5)


def test_the_harness_schema_requires_a_run_purpose_block():
    schema = json.loads(HARNESS_SCHEMA.read_text(encoding="utf-8"))
    assert "run_purpose" in schema["required"], (
        "an unmarked artifact must not be able to validate"
    )


@pytest.mark.parametrize("field", gov.QUARANTINE_FIELDS)
def test_every_quarantine_field_is_required_and_pinned_false(field):
    """Required AND enum-pinned. Merely *permitting* the field is not a firewall."""
    schema = json.loads(HARNESS_SCHEMA.read_text(encoding="utf-8"))
    declarations = [
        obj for obj in gov._object_schemas(schema) if field in obj["properties"]
    ]
    assert declarations, f"{field} is absent from the authoritative schema"
    for obj in declarations:
        assert field in obj.get("required", []), f"{field} is declared but optional"
        spec = obj["properties"][field]
        assert spec.get("type") == "boolean"
        assert spec.get("enum") == [False], f"{field} is not pinned to false"


def test_the_five_eligibility_booleans_are_all_false(purpose, governed):
    flags = purpose.firewall_flags()
    assert set(flags) == set(gov.FIREWALL_FIELDS)
    assert all(v is False for v in flags.values()), flags
    for field in gov.FIREWALL_FIELDS:
        assert governed[field] is False, f"{field} is not false in the record"


@pytest.mark.parametrize("field", gov.NON_RESULT_FIELDS)
def test_is_result_and_scored_are_false_in_the_record(field, governed):
    assert governed[field] is False


def test_the_record_states_the_diagnostic_is_not_a_result(governed):
    assert governed["diagnostic_result_status"] == "non-result"


def test_the_authoritative_schema_passes_the_firewall_check(purpose):
    assert gov.artifact_schema_problems(purpose, REPO) == []


def test_a_schema_without_the_firewall_is_reported_as_failing():
    """Non-vacuity: the checker must actually reject a schema that lacks it."""
    problems = gov.schema_firewall_problems(
        json.loads(CANONICAL_SCHEMA.read_text(encoding="utf-8"))
    )
    assert problems, "the firewall checker accepts a schema with no firewall"
    assert any("run_purpose" in p for p in problems)


@pytest.mark.parametrize(
    "mutant",
    [
        {"required": ["run_purpose"], "properties": {}},
        {
            "required": ["run_purpose"],
            "properties": {f: {"type": "boolean"} for f in gov.QUARANTINE_FIELDS}
            | {"run_purpose": {"type": "object"}},
        },
        {
            "required": ["run_purpose"] + list(gov.QUARANTINE_FIELDS),
            "properties": {
                f: {"type": "boolean", "enum": [True]} for f in gov.QUARANTINE_FIELDS
            }
            | {"run_purpose": {"type": "object"}},
        },
    ],
    ids=["fields-absent", "declared-but-optional", "pinned-true"],
)
def test_the_firewall_checker_rejects_each_way_of_dropping_it(mutant):
    assert gov.schema_firewall_problems(mutant), (
        "a schema that does not enforce the quarantine was accepted"
    )


# --------------------------------------------------------------------------- 4
# The artifact-path firewall. (I.6)


@pytest.mark.parametrize(
    "relative",
    [
        "experiments/v2/results",
        "experiments/v2/results/some-run",
        "experiments/v2/analysis",
        "experiments/v2/analysis/nested/deeper",
    ],
)
def test_the_diagnostic_cannot_emit_into_results_or_analysis(purpose, relative):
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        gov.assert_artifact_area_permitted(REPO / relative, purpose)
    assert excinfo.value.code == gov.DIAGNOSTIC_ARTIFACT_IN_CONFIRMATORY_AREA


@pytest.mark.parametrize(
    "relative", ["", "experiments", "experiments/v2", "docs/v2", "experiments/v2/harness"]
)
def test_the_diagnostic_cannot_emit_anywhere_inside_the_repository(purpose, relative):
    target = REPO / relative if relative else REPO
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        gov.assert_artifact_area_permitted(target, purpose)
    assert excinfo.value.code in {
        gov.ARTIFACT_ROOT_INSIDE_CANONICAL_REPOSITORY,
        gov.DIAGNOSTIC_ARTIFACT_IN_CONFIRMATORY_AREA,
    }


def test_a_scratch_root_outside_the_repository_is_permitted(purpose, tmp_path):
    assert gov.assert_artifact_area_permitted(tmp_path / "runs", purpose)


def test_the_default_artifact_root_is_outside_the_repository():
    root = gov.default_artifact_root().resolve()
    assert REPO.resolve() not in root.parents and root != REPO.resolve()


def test_no_artifact_has_appeared_in_a_confirmatory_area():
    for directory in ("results", "analysis"):
        stray = [
            p.name
            for p in (REPO / "experiments" / "v2" / directory).rglob("*")
            if p.is_file() and p.name != "README.md"
        ]
        assert not stray, f"an artifact appeared in experiments/v2/{directory}: {stray}"


# --------------------------------------------------------------------------- 5
# The canonical schema is UNCHANGED. (I.7)


def test_the_canonical_run_manifest_schema_is_byte_identical():
    digest = hashlib.sha256(CANONICAL_SCHEMA.read_bytes()).hexdigest()
    assert digest == CANONICAL_SCHEMA_SHA256, (
        "experiments/v2/schemas/run_manifest.schema.json changed. SL-PT08-02 "
        "leaves it UNCHANGED, and that directory is byte-pinned by the private "
        "evaluator's public linkage, so editing it needs a linkage re-approval "
        "this package does not have"
    )


def test_the_canonical_schema_still_forbids_extra_properties_and_lacks_the_firewall():
    schema = json.loads(CANONICAL_SCHEMA.read_text(encoding="utf-8"))
    assert schema.get("additionalProperties") is False
    for field in gov.QUARANTINE_FIELDS + ("run_purpose",):
        assert field not in schema["properties"], (
            f"{field} appeared in the canonical schema; this package adds none"
        )
        assert field not in schema.get("required", [])


def test_the_record_declares_the_canonical_schema_unchanged(governed):
    assert governed["canonical_run_manifest_schema"] == "UNCHANGED"


# --------------------------------------------------------------------------- 6
# The global gap is NOT claimed fixed. (I.8, I.9)


def test_the_record_does_not_claim_the_canonical_gap_is_globally_resolved(governed):
    assert governed["canonical_schema_gap_globally_resolved"] is False
    assert (
        governed["canonical_result_schema_requirement"]
        == "NOT WAIVED FOR CONFIRMATORY/RESULT-BEARING RUNS"
    )


def test_the_record_says_in_prose_that_the_gap_is_unresolved_and_not_waived():
    flat = _flat(RECORD)
    assert "that gap is unresolved" in flat
    assert "does not remediate" in flat
    assert "does not waive" in flat
    assert "the canonical confirmatory run-manifest schema is not fixed" in flat


@pytest.mark.parametrize(
    "forbidden",
    [
        "canonical schema gap is fixed",
        "canonical schema is remediated",
        "run_manifest schema now carries the firewall",
        "the canonical gap is closed",
        "globally resolved",
    ],
)
def test_the_record_never_claims_global_remediation(forbidden):
    assert forbidden not in _flat(RECORD)


def test_the_canonical_gap_is_reported_as_unresolved_not_as_passed(readiness):
    item = _item(readiness, "canonical_confirmatory_run_manifest_firewall")
    assert item.status == gov.NOT_APPLICABLE, (
        "the canonical gap must never be reported PASS for this diagnostic: PASS "
        "would read as remediated, and it is not"
    )
    assert item.status != gov.PASS
    assert item.code == gov.RUN_MANIFEST_SCHEMA_LACKS_DIAGNOSTIC_FIREWALL
    detail = item.detail.lower()
    assert "unresolved" in detail
    assert "not applicable to this diagnostic" in detail
    assert "not fixed" in detail and "not waived" in detail
    assert "every future confirmatory / result-bearing run" in detail


def test_a_result_bearing_purpose_still_requires_the_canonical_schema():
    """The applicability decision narrows to non-result purposes and no further."""
    result_bearing = gov.RunPurpose(
        name="PROBE_CONFIRMATORY",
        decision_id="PROBE",
        description="a hypothetical result-bearing purpose",
        confirmatory=False,
        permitted_tasks=("PT08",),
        permitted_conditions=("C1",),
        firewall=tuple((f, False) for f in gov.FIREWALL_FIELDS),
        artifact_schema="experiments/v2/schemas/run_manifest.schema.json",
        result_bearing=True,
    )
    assert gov.artifact_schema_problems(result_bearing, REPO), (
        "a result-bearing purpose bound to the canonical schema must still be "
        "reported as lacking the firewall"
    )


def test_no_confirmatory_or_result_bearing_purpose_is_registered():
    for name, p in gov.RUN_PURPOSES.items():
        assert p.confirmatory is False, name
        assert p.result_bearing is False, name


def test_the_canonical_schema_is_verified_not_remembered():
    """The report's claim is recomputed from the file, in both directions."""
    assert gov.canonical_run_manifest_carries_firewall(REPO) is False


# --------------------------------------------------------------------------- 7
# The diagnostic no longer blocks on the canonical gap. (I.10)


def test_the_diagnostic_artifact_firewall_passes(readiness):
    item = _item(readiness, "diagnostic_artifact_firewall")
    assert item.status == gov.PASS, item.detail
    assert item.code is None
    assert "run_record.schema.json" in item.detail


def test_the_old_canonical_blocker_no_longer_blocks_this_diagnostic(readiness):
    blocked_codes = {p.code for p in readiness.blocked}
    assert gov.RUN_MANIFEST_SCHEMA_LACKS_DIAGNOSTIC_FIREWALL not in blocked_codes
    blocked_items = {p.item for p in readiness.blocked}
    assert "run_manifest_schema_firewall_fields" not in blocked_items
    assert "diagnostic_artifact_firewall" not in blocked_items


# --------------------------------------------------------------------------- 8
# SL-PT08-03: the repetition count. (I.15, I.16, I.17, I.18)


def test_the_repetition_count_is_exactly_three(purpose, governed):
    assert purpose.repetitions == 3
    assert governed["diagnostic_repetitions"] == 3


def test_the_repetition_count_is_reported_and_agrees_with_the_record(readiness):
    item = _item(readiness, "diagnostic_repetition_decision")
    assert item.status == gov.PASS, item.detail
    assert "3 independent repetitions" in item.detail


def test_the_diagnostic_is_c1_only_and_pt08_only(purpose, governed):
    assert purpose.permitted_conditions == ("C1",)
    assert purpose.permitted_tasks == ("PT08",)
    assert governed["condition"] == "C1"
    assert governed["task"] == "PT08"


@pytest.mark.parametrize("condition", ["C2", "C3", "C4"])
def test_no_other_condition_is_permitted(purpose, condition):
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        gov.assert_task_and_condition_permitted(purpose, "PT08", condition)
    assert excinfo.value.code == gov.CONDITION_NOT_PERMITTED_FOR_PURPOSE


@pytest.mark.parametrize("key,expected", gov.REPETITION_PINS)
def test_each_fresh_execution_requirement_is_pinned(governed, key, expected):
    assert governed[key] == expected


def test_the_fresh_session_requirement_is_stated_in_prose():
    flat = _flat(RECORD)
    assert "fresh process" in flat
    assert "fresh session" in flat
    assert "no --resume" in flat
    assert "no --continue" in flat
    assert "no session reuse" in flat


def test_the_count_carries_no_power_precision_or_treatment_effect_claim(governed):
    assert governed["power_claim"] == "none"
    assert governed["precision_claim"] == "none"
    assert governed["treatment_effect_claim"] == "none"
    flat = _flat(RECORD)
    assert "no power calculation was performed to justify this count" in flat
    assert "licenses no power claim" in flat
    assert "licenses no precision claim" in flat
    assert "licenses no treatment-effect claim" in flat


def test_the_three_observations_are_not_independent_architecture_constructs():
    flat = _flat(RECORD)
    assert "repeated difficulty probes" in flat
    assert "not three independent architecture constructs" in flat
    assert "repetition depth only" in flat


def test_the_diagnostic_still_enters_no_power_estimation(purpose, governed):
    assert purpose.firewall_flags()["enters_power_estimation"] is False
    assert governed["enters_power_estimation"] is False
    flat = _flat(RECORD)
    assert "power estimation" in flat


def test_the_record_states_no_accounting_and_alters_no_clustering():
    flat = _flat(RECORD)
    assert "the e1 accounting is untouched" in flat
    assert "states no active opportunity count" in flat
    assert "no decision-cluster count and no observation depth" in flat


# --------------------------------------------------------------------------- 9
# The private pre-freeze sync item is mechanically evaluated, never assumed.


def test_the_private_sync_item_is_read_from_the_private_record_not_hardcoded():
    """An OPEN or absent record must block; only a SATISFIED one may pass."""
    ok, detail = gov.private_sync_prefreeze_state("PT08", REPO / "no-such-private-root")
    assert ok is False
    assert "not available" in detail


def test_a_satisfied_sync_record_must_cite_a_reachable_public_commit(tmp_path):
    record_dir = tmp_path / "tasks" / "PT08"
    record_dir.mkdir(parents=True)
    (record_dir / "pt08_package_record.json").write_text(
        json.dumps(
            {
                "public_synchronisation_required_before_freeze": {
                    "record_id": "PROBE",
                    "state": "SATISFIED",
                    "verified_public_sha": "0" * 40,
                }
            }
        ),
        encoding="utf-8",
    )
    ok, detail = gov.private_sync_prefreeze_state("PT08", tmp_path, REPO)
    assert ok is False
    assert "not an ancestor" in detail


# --------------------------------------------------------------------------- 10
# What is STILL blocked, and what is still not claimed. (I.19–I.23)


def test_the_manifest_is_still_review_and_not_frozen_suite_wide(readiness):
    """`SL-PT08-02`/`SL-PT08-03` froze nothing, and that is still true.

    `SL-PT08-06` has since granted a DIAGNOSTIC-SCOPED freeze for one triple, so
    the readiness item now passes on that narrow route. The suite-wide lifecycle
    is what these two records were about, and it is unchanged: the manifest is
    not frozen, the suite is not frozen and gate `G1` is not passed.
    """
    assert gov.manifest_is_frozen("PT08") is False
    state = gov.manifest_freeze_state(
        "PT08", condition="C1", run_purpose=PURPOSE_NAME
    )
    assert state["global_frozen"] is False
    assert state["suite_frozen"] is False
    assert state["global_gate_g1_passed"] is False
    assert state["diagnostic_frozen"] is True
    assert state["diagnostic_freeze_authority"] == "SL-PT08-06"

    item = _item(readiness, "manifest_freeze")
    assert item.status == gov.PASS
    assert item.code is None
    assert "SL-PT08-06" in item.detail
    assert "gate G1 is NOT passed" in item.detail
    g1 = _item(readiness, "suite_wide_gate_g1")
    assert g1.status == gov.NOT_APPLICABLE


def test_gate_g1_is_not_passed_and_nothing_here_freezes_anything():
    flat = _flat(RECORD)
    assert "gate g1 is not passed" in flat
    assert "pt08 is not frozen" in flat
    assert "the protocol remains pre-freeze" in flat


def test_the_diagnostic_is_not_run_eligible(readiness):
    assert readiness.run_eligible is False
    assert readiness.blocked, "a non-eligible run must name what blocks it"


def test_no_result_exists_and_none_is_claimed():
    flat = _flat(RECORD)
    assert "no result exists" in flat
    assert "the diagnostic has not been executed" in flat
    assert "no power simulation was run" in flat


def test_the_record_still_states_what_it_stated_about_model_and_isolation():
    """These remain accurate statements about what THIS record did.

    `SL-PT08-02`/`SL-PT08-03` selected no model, established no isolated
    environment and live-validated nothing, and that stays true of them. Later
    records did those things; this one is not rewritten to claim them, exactly
    as the repository keeps every superseded reading as marked history.
    """
    flat = _flat(RECORD)
    assert "no model is selected" in flat
    assert "no isolated execution environment has been established" in flat
    assert "q1 and q8 are not live-validated" in flat


def test_no_confirmatory_primary_model_is_selected(readiness):
    """The global selection `TD-B03` governs is still open.

    `SL-PT08-05` pins a model for ONE non-confirmatory purpose. That is not the
    primary-model selection, and the guard that matters is the one below:
    `primary_model` is still null.
    """
    assert gov.primary_model() is None
    item = _item(readiness, "model_selection")
    assert item.status == gov.PASS
    assert "PT08_DIFFICULTY_DIAGNOSTIC only" in item.detail
    assert "TD-B03 stays open" in item.detail
    assert "no confirmatory selection" in item.detail


def test_q1_q8_are_now_live_validated_for_this_purpose(readiness):
    """`TD-B21`'s two controls have been exercised against a live runtime."""
    item = _item(readiness, "q1_q8_live_runtime_validation")
    assert item.status == gov.PASS
    assert item.code is None
    q1, q8, cli = gov.live_runtime_validation("PT08_DIFFICULTY_DIAGNOSTIC")
    assert q1 == "PASS" and q8 == "PASS"
    assert cli == "2.1.229", "the version recorded must be the one validated"


def test_isolation_is_still_never_asserted_in_advance(readiness):
    """A verdict is demonstrated per run; absent one, the item fails closed."""
    assert _item(readiness, "clean_isolated_context").status == gov.BLOCKED
    assert _item(readiness, "clean_isolated_context").code == gov.CONTEXT_AUDIT_UNKNOWN


def test_the_diagnostic_is_not_run_eligible_without_a_live_clean_context(readiness):
    """Neither of these two records made it eligible, and neither claims to.

    `SL-PT08-06` has since discharged the manifest-freeze prerequisite on a
    narrow scoped route. What remains is isolation, which is demonstrated per
    repetition and never asserted in advance — so a readiness call that supplies
    no verdict still reports the diagnostic as not eligible.
    """
    assert readiness.run_eligible is False
    assert [p.item for p in readiness.blocked] == ["clean_isolated_context"]


def test_the_record_closes_no_other_blocker():
    flat = _flat(RECORD)
    assert "td-b34 is not closed" in flat
    # SL-QUAL-01 later started priority B; what this record must still say is
    # that THIS diagnostic neither started nor completed it.
    assert "priority b was not started" in flat
    assert "this diagnostic neither started nor completed it" in flat
    assert "the global td-b32 row stays open" in flat
    assert "td-b12/g6 are unchanged" in flat


def test_no_private_linkage_advance_is_claimed(governed):
    assert governed["private_linkage_baseline_advance_required"] is False
    flat = _flat(RECORD)
    assert "no private-linkage baseline is advanced" in flat
    assert "no re-link is performed" in flat


# --------------------------------------------------------------------------- 11
# The public accounting is 6 / 3 / 3-2-1 and this package does not move it. (I.24)


def test_the_public_accounting_is_six_over_three_at_depths_three_two_one():
    """The authoritative closure record's own table, asserted cell by cell."""
    flat = _flat(SYNC_CLOSURE)
    for phrase in (
        "| active e1 opportunities | 6 |",
        "| active decision clusters | 3 |",
        "| cluster observation depths | 3 / 2 / 1 |",
        "| priority-a cluster observations | 2 |",
        "| remaining singleton clusters | 1 |",
    ):
        assert phrase in flat, phrase


def test_the_scored_active_set_includes_pt08():
    flat = _flat(SYNC_CLOSURE)
    assert "pt01, pt02, pt03, pt04, pt07, pt08" in flat


def test_this_package_states_no_count_of_its_own():
    """The new record must not restate an accounting number in any form."""
    flat = _flat(RECORD)
    assert not re.search(r"\b\d+\s+(?:active\s+)?e1 opportunit", flat)
    assert not re.search(r"\d\s*/\s*\d\s*/\s*\d", flat)
    assert "decision cluster" not in flat or "no decision-cluster count" in flat
