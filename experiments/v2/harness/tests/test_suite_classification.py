"""Governance tests for the suite-classification decision (decision D).

The independently approved suite-level decision narrowed the confirmatory
construct to **layered dependency-direction conformance**. That narrowing is only
worth anything if it is mechanically enforced, so this module asserts:

* all eight public task bodies and their recorded hashes are **unchanged** by the
  classification (classification is metadata, never a task edit);
* ``PT01``-``PT05`` are E1-``scored``, ``PT06`` is ``functional-only``, and
  ``PR01``/``PR02`` are ``inactive-reserve``, consistently in both public CSVs;
* ``PT06`` is excluded from E1 **without** being classified as a failed run;
* a zero-opportunity task cannot be entered as zero violations;
* inactive reserve tasks enter no endpoint, and ``PR02`` is barred from promotion;
* E1 uses ``opportunity_accounting.violated_opportunity_count`` over
  ``opportunity_accounting.applicable_opportunity_count``, and **not**
  ``applicable_rule_count``;
* stub rules do not enlarge the E1 denominator and ``raw_violation_count`` stays a
  separate descriptive series;
* broad architectural-conformance claims are rejected: the five named dimensions
  are explicitly not-directly-measured, kappa >= 0.70 gates confirmatory manual
  use, and the paper is forbidden from describing E1 as broad/general;
* the ``PR02``, ``PT03`` and source-comment-leakage blockers are **recorded** and
  none of them is fixed in this package;
* reset is governed as an experimental factor, not a task-content category;
* the protocol remains PRE-FREEZE and no benchmark result exists.

Pure file inspection; no model is invoked and no benchmark runs.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"
PUBLIC_TASKS_DIR = REPO / "experiments" / "v2" / "tasks" / "public"

INDEX_PATH = PUBLIC_TASKS_DIR / "TASK_INDEX.csv"
REPORT_PATH = PUBLIC_TASKS_DIR / "TASK_AUTHORING_REPORT.md"
MATRIX_PATH = DOCS_V2 / "PILOT_PUBLIC_TASK_MATRIX.csv"
SAP_PATH = DOCS_V2 / "STATISTICAL_ANALYSIS_PLAN.md"
RQ_PATH = DOCS_V2 / "RESEARCH_QUESTIONS.md"
CLAIMS_PATH = DOCS_V2 / "CLAIMS_CONSTRUCTS_METRICS.csv"
GATES_PATH = DOCS_V2 / "PILOT_GATE_MATRIX.csv"
CATALOG_PATH = DOCS_V2 / "ARCHITECTURE_RULE_CATALOG.yml"
RESET_PROTOCOL_PATH = DOCS_V2 / "RESET_PROTOCOL.md"
RESET_MATRIX_PATH = DOCS_V2 / "RESET_CHECKPOINT_MATRIX.csv"
DECISIONS_CSV = DOCS_V2 / "OPEN_DECISIONS.csv"
DECISIONS_MD = DOCS_V2 / "OPEN_DECISIONS.md"
DOCS_V2_README = DOCS_V2 / "README.md"
FINDING_SCHEMA = REPO / "experiments" / "v2" / "schemas" / "architecture_finding.schema.json"

SCORED = ["PT01", "PT02", "PT03", "PT04", "PT05"]
FUNCTIONAL_ONLY = ["PT06"]
INACTIVE_RESERVE = ["PR01", "PR02"]
ALL_TASKS = SCORED + FUNCTIONAL_ONLY + INACTIVE_RESERVE

#: The eight task-body SHA-256 values as pinned before this work package. The
#: classification decision explicitly changes **no** task body, so every one of
#: these must still be the hash of the file on disk *and* the value recorded in
#: both public CSVs. If a task is legitimately amended later (e.g. PT03 under
#: TD-B25), that amendment updates this map deliberately - it must never drift
#: silently.
FROZEN_HASHES = {
    "PT01": "6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39",
    "PT02": "ec4b60057708b20cb95e51f000671aab40afc8c55c0bc75850922a5f65841a77",
    "PT03": "cbfce1ca232cb9b6b53e0b4d202d6acee7415b50af8386c1f3bd2147089b4c21",
    "PT04": "f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5",
    "PT05": "f6efc772e76d6c287e0c71daaa93c7e1d9e62e72a1b37878df70113269ed27b3",
    "PT06": "3e0f84cfef1f9fbf97e3cd31b6704c3a0fb172b04b5e7bc33ea39927b1c8e0f2",
    "PR01": "0e1527bce41498836bb57b802d4566251d6fcfed4cca13fe59e6a97330f02302",
    "PR02": "e89a4aab236813c082f9152db779b8bbfb298148a51a8435a1e2bf38330caa83",
}

ELIGIBILITY_VOCABULARY = {"scored", "functional-only", "inactive-reserve"}

#: Dimensions E1 must never be claimed to measure directly.
NOT_DIRECTLY_MEASURED = (
    "contract ownership",
    "port/interface placement",
    "observability completeness",
    "duplicated logic",
    "general business-logic placement",
)


def _rows(path: Path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _by_id(rows, key="task_id"):
    return {r[key]: r for r in rows}


INDEX_BY_ID = _by_id(_rows(INDEX_PATH))
MATRIX_BY_ID = _by_id(_rows(MATRIX_PATH))


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(path: Path) -> str:
    """Lower-cased text with markdown emphasis and newlines collapsed.

    Lets an assertion match a phrase that the source hard-wraps or emphasises.
    """
    return re.sub(r"\s+", " ", _text(path).replace("*", "").replace("`", "")).lower()


# --------------------------------------------------------------------------- #
# 1. No task body and no task hash changed
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("task_id", ALL_TASKS)
def test_task_body_hash_is_unchanged_by_the_classification(task_id):
    path = PUBLIC_TASKS_DIR / f"{task_id}.md"
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == FROZEN_HASHES[task_id], (
        f"{task_id}.md changed: the suite classification must not edit a task body. "
        f"expected {FROZEN_HASHES[task_id][:16]}... got {actual[:16]}..."
    )


@pytest.mark.parametrize("task_id", ALL_TASKS)
def test_both_public_csvs_still_record_the_unchanged_hash(task_id):
    assert INDEX_BY_ID[task_id]["public_task_sha256"] == FROZEN_HASHES[task_id]
    assert MATRIX_BY_ID[task_id]["public_task_sha256"] == FROZEN_HASHES[task_id]


def test_all_eight_tasks_are_present_and_no_ninth_appeared():
    assert sorted(INDEX_BY_ID) == sorted(ALL_TASKS)
    assert sorted(MATRIX_BY_ID) == sorted(ALL_TASKS)


def test_hash_check_would_actually_catch_a_body_edit():
    """Guard the guard: hashing must be sensitive to a one-byte change."""
    original = (PUBLIC_TASKS_DIR / "PT01.md").read_bytes()
    assert hashlib.sha256(original + b"\n").hexdigest() != FROZEN_HASHES["PT01"]


# --------------------------------------------------------------------------- #
# 2. Eligibility is recorded, consistent, and uses the agreed vocabulary
# --------------------------------------------------------------------------- #
def test_eligibility_column_exists_in_both_public_csvs():
    assert "e1_analysis_eligibility" in INDEX_BY_ID["PT01"], "TASK_INDEX.csv lacks the field"
    assert "e1_analysis_eligibility" in MATRIX_BY_ID["PT01"], "public matrix lacks the field"


@pytest.mark.parametrize("task_id", ALL_TASKS)
def test_eligibility_uses_only_the_agreed_vocabulary(task_id):
    for row, label in ((INDEX_BY_ID[task_id], "TASK_INDEX.csv"), (MATRIX_BY_ID[task_id], "matrix")):
        value = row["e1_analysis_eligibility"]
        assert value in ELIGIBILITY_VOCABULARY, f"{task_id} in {label}: unknown value {value!r}"


@pytest.mark.parametrize("task_id", ALL_TASKS)
def test_both_public_csvs_agree_on_eligibility(task_id):
    assert (
        INDEX_BY_ID[task_id]["e1_analysis_eligibility"]
        == MATRIX_BY_ID[task_id]["e1_analysis_eligibility"]
    ), f"{task_id}: the two public CSVs disagree on eligibility"


def test_pt01_to_pt05_are_e1_scored():
    for task_id in SCORED:
        assert INDEX_BY_ID[task_id]["e1_analysis_eligibility"] == "scored", task_id


def test_pt06_is_functional_only():
    assert INDEX_BY_ID["PT06"]["e1_analysis_eligibility"] == "functional-only"


def test_pr01_and_pr02_are_inactive_reserves():
    for task_id in INACTIVE_RESERVE:
        assert INDEX_BY_ID[task_id]["e1_analysis_eligibility"] == "inactive-reserve", task_id


def test_exactly_five_of_the_six_primary_candidates_are_scored():
    primary = [t for t in ALL_TASKS if INDEX_BY_ID[t]["primary_or_reserve"] == "primary"]
    assert len(primary) == 6, primary
    scored = [t for t in primary if INDEX_BY_ID[t]["e1_analysis_eligibility"] == "scored"]
    assert len(scored) == 5, f"five of six primary candidates must contribute to E1, got {scored}"


def test_primary_reserve_classification_is_unchanged_by_the_decision():
    """Eligibility is a separate axis; it must not have rewritten primary/reserve."""
    for task_id in SCORED + FUNCTIONAL_ONLY:
        assert INDEX_BY_ID[task_id]["primary_or_reserve"] == "primary", task_id
    for task_id in INACTIVE_RESERVE:
        assert INDEX_BY_ID[task_id]["primary_or_reserve"] == "reserve", task_id


def test_eligibility_and_primary_reserve_are_independent_fields():
    """PT06 proves the axes are independent: primary, yet not E1-scored."""
    row = INDEX_BY_ID["PT06"]
    assert row["primary_or_reserve"] == "primary"
    assert row["e1_analysis_eligibility"] != "scored"


# --------------------------------------------------------------------------- #
# 3. PT06 is excluded from E1 without being a failed run
# --------------------------------------------------------------------------- #
def test_pt06_exclusion_is_not_a_failed_run():
    sap = _flat(SAP_PATH)
    assert "structurally ineligible" in sap, "the SAP must name structural ineligibility"
    assert "not coded as zero violations" in sap or "never entered as zero violations" in sap
    assert "not recorded as a failed run" in sap or "never counted as a failed run" in sap, (
        "the SAP must state that E1 exclusion is not a failed run"
    )
    assert "no_patch" in sap and "refusal" in sap, (
        "the SAP must distinguish structural exclusion from the degenerate-outcome codes"
    )


def test_pt06_still_contributes_to_functional_cost_and_exploratory_analyses():
    for path in (SAP_PATH, MATRIX_PATH, REPORT_PATH):
        flat = _flat(path)
        assert "hidden functional acceptance" in flat or "hidden acceptance" in flat, path.name
    matrix_reason = MATRIX_BY_ID["PT06"]["e1_eligibility_reason"].lower()
    for token in ("hidden functional acceptance", "cost", "exploratory"):
        assert token in matrix_reason, f"PT06 reason must mention {token}"


def test_pt06_is_still_a_valid_primary_functional_candidate():
    reason = MATRIX_BY_ID["PT06"]["e1_eligibility_reason"].lower()
    assert "valid primary functional candidate" in reason
    assert "structurally excluded from e1" in reason


# --------------------------------------------------------------------------- #
# 4. Zero-opportunity tasks cannot be entered as zero violations
# --------------------------------------------------------------------------- #
def test_zero_opportunity_tasks_cannot_be_entered_as_zero_violations():
    sap = _flat(SAP_PATH)
    assert "applicable_opportunity_count = 0" in sap, (
        "the SAP must pin the zero-denominator rule explicitly"
    )
    assert "structurally ineligible for e1" in sap
    assert "not coded as zero violations" in sap
    rq = _flat(RQ_PATH)
    assert "structurally ineligible" in rq and "not coded as zero violations" in rq, (
        "RESEARCH_QUESTIONS.md must carry the same rule so the construct and the "
        "analysis plan cannot drift"
    )


def test_zero_exposure_observations_are_excluded_from_the_model():
    sap = _flat(SAP_PATH)
    assert "contribute no exposure" in sap and "structurally excluded" in sap, (
        "the model section must exclude zero-exposure observations rather than "
        "entering them with a zero numerator"
    )


# --------------------------------------------------------------------------- #
# 5. Inactive reserves enter no endpoint; PR02 is barred from promotion
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("task_id", INACTIVE_RESERVE)
def test_inactive_reserves_do_not_enter_e1(task_id):
    reason = MATRIX_BY_ID[task_id]["e1_eligibility_reason"].lower()
    assert "not activated" in reason, task_id
    assert INDEX_BY_ID[task_id]["e1_analysis_eligibility"] == "inactive-reserve"


def test_no_reserve_was_activated():
    activated = [t for t in INACTIVE_RESERVE if INDEX_BY_ID[t]["e1_analysis_eligibility"] != "inactive-reserve"]
    assert not activated, f"no reserve may be activated by this package: {activated}"
    report = _flat(REPORT_PATH)
    assert "no reserve was activated" in report


def test_pr02_promotion_is_blocked_and_recorded():
    reason = MATRIX_BY_ID["PR02"]["e1_eligibility_reason"].lower()
    assert "not externally reachable" in reason, "PR02's blocker must be stated in the matrix"
    assert "td-b26" in reason, "PR02's blocker must cite its registry id"
    report = _flat(REPORT_PATH)
    assert "pr02 must not be promoted" in report
    assert "independently re-approved" in report, (
        "PR02 may only be activated after repair AND independent re-approval"
    )


# --------------------------------------------------------------------------- #
# 6. E1 accounting is pinned to the opportunity_accounting fields
# --------------------------------------------------------------------------- #
def test_e1_numerator_and_denominator_are_pinned():
    sap = _text(SAP_PATH)
    assert "opportunity_accounting.violated_opportunity_count" in sap, "E1 numerator not pinned"
    assert "opportunity_accounting.applicable_opportunity_count" in sap, "E1 offset not pinned"


def test_applicable_rule_count_is_forbidden_as_the_e1_offset():
    sap = _flat(SAP_PATH)
    assert "applicable_rule_count must not be used as the e1 offset" in sap or (
        "applicable_rule_count is not an admissible offset" in sap
    ), "the SAP must forbid applicable_rule_count as the E1 offset"


def test_stub_rules_do_not_increase_the_e1_denominator():
    sap = _flat(SAP_PATH)
    assert "stub or unimplemented rules must not increase the e1 denominator" in sap
    for stub in ("ar-contract-001", "ar-observ-001", "ar-code-001"):
        assert stub in sap, f"the SAP must name {stub} as an excluded stub"


def test_raw_violation_count_is_a_separate_descriptive_series():
    sap = _flat(SAP_PATH)
    assert "raw_violation_count is a separate descriptive diagnostic series" in sap
    assert "never substituted into it" in sap or "never substituted" in sap


def test_the_pinned_fields_actually_exist_in_the_finding_schema():
    """The accounting cannot be pinned to fields the artifact does not carry."""
    schema = json.loads(_text(FINDING_SCHEMA))
    acct = schema["properties"]["opportunity_accounting"]
    for field in ("violated_opportunity_count", "applicable_opportunity_count"):
        assert field in acct["properties"], field
        assert field in acct["required"], f"{field} must be required, not optional"
    assert "raw_violation_count" in schema["properties"], "the raw series must be recorded too"


def test_denominator_is_not_derived_from_touched_files():
    sap = _flat(SAP_PATH)
    assert "never derived from how many files or layers the change happened to touch" in sap


# --------------------------------------------------------------------------- #
# 7. Broad architectural-conformance claims are rejected
# --------------------------------------------------------------------------- #
def test_e1_is_renamed_to_the_dependency_direction_endpoint():
    expected = "dependency-direction violation rate per applicable frozen opportunity"
    for path in (SAP_PATH, RQ_PATH):
        assert expected in _flat(path), f"{path.name} must carry E1's narrowed name"


def test_the_confirmatory_construct_is_layered_dependency_direction_conformance():
    rq = _flat(RQ_PATH)
    assert "layered dependency-direction conformance" in rq


@pytest.mark.parametrize("dimension", NOT_DIRECTLY_MEASURED)
def test_each_broad_dimension_is_declared_not_directly_measured(dimension):
    rq = _flat(RQ_PATH)
    assert dimension in rq, f"{dimension!r} must be named in RESEARCH_QUESTIONS.md"
    sap = _flat(SAP_PATH)
    assert dimension in sap, f"{dimension!r} must be named in the SAP as not directly measured"


def test_e1_does_not_directly_measure_is_stated_explicitly():
    rq = _flat(RQ_PATH)
    assert "e1 does not directly measure" in rq
    sap = _flat(SAP_PATH)
    assert "e1 does not directly measure" in sap


def test_broad_dimensions_are_pre_registered_secondary_or_manual_evidence():
    rq = _flat(RQ_PATH)
    assert "pre-registered secondary / manual evidence" in rq or (
        "pre-registered secondary/manual evidence" in rq
    ), "the broader dimensions must be declared secondary/manual evidence"


def test_confirmatory_manual_evidence_requires_the_kappa_reliability_gate():
    for path in (RQ_PATH, SAP_PATH):
        flat = _flat(path)
        assert "0.70" in flat, f"{path.name} must state the kappa >= 0.70 gate"
        assert "kappa" in flat or "κ" in _text(path).lower(), path.name
    rq = _flat(RQ_PATH)
    assert "blinded" in rq, "the reliability gate requires blinded double rating"


def test_the_paper_must_not_describe_e1_as_broad_or_general_conformance():
    hits = 0
    for path in (RQ_PATH, SAP_PATH, GATES_PATH, DOCS_V2_README):
        flat = _flat(path)
        if "must not describe e1 as broad or general architectural conformance" in flat:
            hits += 1
    assert hits >= 2, (
        "the prohibition on describing E1 as broad/general architectural conformance "
        "must appear in at least two governance artifacts"
    )


def test_gate_g8_prohibits_directly_measured_claims_for_broader_dimensions():
    g8 = next(r for r in _rows(GATES_PATH) if r["gate_id"] == "G8")
    notes = re.sub(r"\s+", " ", g8["notes"]).lower()
    assert "prohibits" in notes, "G8 must carry the prohibition"
    assert "directly measured by e1" in notes
    assert "broader architectural dimensions" in notes


def test_the_construct_split_is_recorded_in_the_claims_matrix():
    rows = _rows(CLAIMS_PATH)
    constructs = {r["construct"] for r in rows}
    assert "CON-ACB" in constructs, "the claims matrix must carry the split-out broad construct"
    acb = [r for r in rows if r["construct"] == "CON-ACB"]
    assert acb, "at least one guardrail claim must sit on CON-ACB"
    for r in acb:
        assert r["confirmatory_or_exploratory"] == "exploratory", r["claim_id"]
        assert r["status"].strip().lower() == "candidate", r["claim_id"]
        assert "0.70" in r["aggregation"] or "0.70" in r["required_evidence"], r["claim_id"]


def test_the_catalog_assigns_broad_rules_to_the_broad_construct():
    catalog = yaml.safe_load(_text(CATALOG_PATH))
    assert "CON-ACB" in catalog["vocabularies"]["construct"]
    by_id = {r["rule_id"]: r for r in catalog["rules"]}
    for rule_id in ("AR-CONTRACT-001", "AR-OBSERV-001", "AR-CODE-001"):
        assert by_id[rule_id]["construct"] == "CON-ACB", (
            f"{rule_id} is not directly measured by E1 and must not sit on CON-AC"
        )
    for rule_id in [f"AR-DEP-{i:03d}" for i in range(1, 7)]:
        assert by_id[rule_id]["construct"] == "CON-AC", (
            f"{rule_id} is the scored family and must stay on CON-AC"
        )


def test_only_dependency_direction_rules_are_scored_into_e1():
    catalog = yaml.safe_load(_text(CATALOG_PATH))
    scored = [
        r["rule_id"]
        for r in catalog["rules"]
        if r["oracle_implementation_status"] == "implemented"
    ]
    assert scored, "at least one implemented rule must exist"
    assert all(r.startswith("AR-DEP-") for r in scored), (
        f"only dependency-direction rules may be scored into E1, found {scored}"
    )
    report = _flat(REPORT_PATH)
    assert "all current scored e1 opportunities use dependency-direction rules" in report


def test_broadening_e1_is_future_work_not_a_post_hoc_rescue():
    for path in (RQ_PATH, DECISIONS_MD):
        flat = _flat(path)
        assert "broaden e1" in flat, path.name
        assert "post hoc" in flat, path.name


# --------------------------------------------------------------------------- #
# 8. Coverage categories are distinguished
# --------------------------------------------------------------------------- #
def test_report_distinguishes_the_four_coverage_categories():
    report = _flat(REPORT_PATH)
    for category in (
        "task subject-matter coverage",
        "hidden functional coverage",
        "manual-rubric coverage",
        "directly scored e1 coverage",
    ):
        assert category in report, f"the report must distinguish {category!r}"
    assert "only category 4 is directly scored by e1" in report or (
        "only one of which e1 measures" in report
    ), "the report must state that only one category is directly scored by E1"


def test_report_states_five_of_six_primary_candidates_contribute_to_e1():
    report = _flat(REPORT_PATH)
    assert "five of the six primary candidates currently contribute to e1" in report


def test_report_records_repeated_boundary_decisions_and_unfrozen_counts():
    report = _flat(REPORT_PATH)
    assert "small number of repeated boundary decisions" in report
    assert "remain unfrozen" in report


def test_report_discloses_no_private_opportunity_answer():
    report = _text(REPORT_PATH)
    # No private opportunity identifier may appear in the public authoring report.
    assert not re.search(r"\bP[TR]\d\d-OPP-\d+", report), (
        "the authoring report must not name a private opportunity identifier"
    )
    assert not re.search(r"[A-Za-z]:[\\/]", report), "no absolute filesystem path"


def test_public_matrix_still_carries_no_hidden_answer_after_the_new_columns():
    text = _text(MATRIX_PATH)
    for leak in ("expected_layer", "prohibited_layer", "AR-", "OPP-", "legitimate_alternative"):
        assert leak not in text, f"PILOT_PUBLIC_TASK_MATRIX.csv leaks {leak}"


# --------------------------------------------------------------------------- #
# 9. Blockers are recorded and nothing is fixed or closed
# --------------------------------------------------------------------------- #
NEW_BLOCKERS = [f"TD-B{i}" for i in range(23, 34)]


@pytest.mark.parametrize("decision_id", NEW_BLOCKERS)
def test_each_new_blocker_is_registered_blocking_and_open(decision_id):
    rows = _by_id(_rows(DECISIONS_CSV), key="decision_id")
    assert decision_id in rows, f"{decision_id} is missing from OPEN_DECISIONS.csv"
    row = rows[decision_id]
    assert row["blocking"] == "yes", f"{decision_id} must be blocking"
    assert row["status"].strip().lower() == "open", f"{decision_id} must not be closed"
    assert row["owner"].strip(), f"{decision_id} needs an owner"
    assert row["gate"].strip(), f"{decision_id} needs a gate mapping"


def test_no_blocking_decision_is_closed_by_this_package():
    for row in _rows(DECISIONS_CSV):
        assert row["status"].strip().lower() == "open", row["decision_id"]


def test_pt03_contradiction_is_recorded_but_pt03_is_not_modified():
    rows = _by_id(_rows(DECISIONS_CSV), key="decision_id")
    text = rows["TD-B25"]["decision"].lower()
    assert "pt03" in text and "contradictory" in text
    assert "amendment" in text and "relink" in text, (
        "TD-B25 must require both a public amendment and a private relink"
    )
    # and PT03's body is untouched
    actual = hashlib.sha256((PUBLIC_TASKS_DIR / "PT03.md").read_bytes()).hexdigest()
    assert actual == FROZEN_HASHES["PT03"], "PT03 must not be repaired in this package"
    report = _flat(REPORT_PATH)
    assert "recorded, not fixed" in report or "is recorded, not fixed" in report


def test_source_comment_leakage_is_recorded_but_not_neutralised():
    rows = _by_id(_rows(DECISIONS_CSV), key="decision_id")
    b23 = rows["TD-B23"]["decision"].lower()
    assert "comment" in b23 and "c1" in b23
    assert "floor effect" in b23, "TD-B23 must record the floor-effect risk"
    b24 = rows["TD-B24"]["decision"].lower()
    assert "never reads typescript source content" in b24 or "source comment" in b24, (
        "TD-B24 must record that the leakage sweep does not scan source comments"
    )
    # the revealing comment is still present: this package records, it does not fix
    app = _text(REPO / "apps" / "api" / "src" / "app.ts")
    assert "BOUNDARY VIOLATION EXAMPLE" in app, (
        "premise of TD-B23: the revealing comment is still in the substrate. If it "
        "was deliberately neutralised, close TD-B23 and update this test."
    )


def test_the_leakage_sweep_still_does_not_read_source_content():
    """Premise of TD-B24 - asserted so the blocker cannot go stale silently."""
    from prepare_model_worktree import scan_snapshot_violations  # noqa: WPS433

    src = _text(REPO / "experiments" / "v2" / "harness" / "prepare_model_worktree.py")
    fn = src.split("def scan_snapshot_violations")[1].split("\ndef ")[0]
    assert "read_text" not in fn and "read_bytes" not in fn, (
        "scan_snapshot_violations now reads file content; TD-B24 may be resolvable"
    )
    assert callable(scan_snapshot_violations)


def test_attribution_and_manifest_coverage_blockers_are_recorded():
    rows = _by_id(_rows(DECISIONS_CSV), key="decision_id")
    b27 = rows["TD-B27"]["decision"].lower()
    assert "exact importer path" in b27 and "new file" in b27
    b28 = rows["TD-B28"]["decision"].lower()
    assert "ar-dep-001" in b28 and "silently omitted" in b28


def test_private_opportunity_blocker_is_recorded_as_an_identifier_only():
    rows = _by_id(_rows(DECISIONS_CSV), key="decision_id")
    b29 = rows["TD-B29"]["decision"]
    assert "PT04-OPP-01" in b29, "the blocker must name the identifier it concerns"
    lowered = b29.lower()
    assert "identifier only" in lowered, (
        "the row must state the id is an identifier only, with content kept private"
    )
    assert "private evaluator repository" in lowered


def test_pseudo_replication_and_reachability_blockers_are_recorded():
    rows = _by_id(_rows(DECISIONS_CSV), key="decision_id")
    b30 = rows["TD-B30"]["decision"].lower()
    assert "pseudo-replicate" in b30 or "pseudo-replication" in b30
    assert "shared boundary decisions" in b30
    b31 = rows["TD-B31"]["decision"].lower()
    assert "suite-wide" in b31 and "reachability" in b31
    assert "pt06-only" in b31 or "pt06 only" in b31


def test_hidden_evaluator_scaffold_blocker_is_recorded():
    rows = _by_id(_rows(DECISIONS_CSV), key="decision_id")
    b32 = rows["TD-B32"]["decision"].lower()
    assert "draft_unvalidated" in b32
    assert "independent review" in b32
    assert "mutation" in b32


def test_the_power_simulation_must_model_pseudo_replication():
    sap = _flat(SAP_PATH)
    assert "pseudo-replication" in sap
    assert "shared boundary decisions" in sap


# --------------------------------------------------------------------------- #
# 10. Reset governance
# --------------------------------------------------------------------------- #
def test_reset_is_governed_as_a_factor_not_a_task_category():
    flat = _flat(RESET_PROTOCOL_PATH)
    assert "reset is an experimental factor crossed with tasks" in flat
    assert "not a task-content category" in flat
    assert "does not require one special primary task" in flat


def test_multiple_retained_primaries_already_have_condition_neutral_checkpoints():
    flat = _flat(RESET_PROTOCOL_PATH)
    assert "multiple retained primary tasks already have condition-neutral checkpoints" in flat


def test_pt06_must_not_stay_in_e1_for_a_reset_bookkeeping_label():
    flat = _flat(RESET_PROTOCOL_PATH)
    assert "must not remain in e1 merely to satisfy a bookkeeping reset label" in flat


def test_no_public_artifact_claims_unique_reset_continuation_coverage():
    """Any mention of reset-continuation coverage must be a denial, never a claim.

    The corrected wording is allowed to *say* that no candidate uniquely provides
    "reset-continuation coverage" - that is the correction. What is forbidden is an
    affirmative claim, so every occurrence must sit inside a negation.
    """
    negations = ("no ", "not ", "never", "n't", "nothing", "neither", "without")
    checked = 0
    for path in sorted(DOCS_V2.glob("*.md")) + sorted(DOCS_V2.glob("*.csv")) + [
        REPORT_PATH,
        REPO / "README.md",
    ]:
        flat = _flat(path)
        for match in re.finditer(r"reset-continuation", flat):
            checked += 1
            window = flat[max(0, match.start() - 120) : match.start()]
            assert any(n in window for n in negations), (
                f"{path.name} appears to claim reset-continuation coverage "
                f"affirmatively: ...{window[-90:]!r}"
            )
    assert checked, (
        "premise of this test: the corrected wording mentions reset-continuation "
        "coverage at least once (as a denial)"
    )


def test_reset_matrix_has_a_withheld_row_for_each_of_the_eight_candidates():
    rows = _rows(RESET_MATRIX_PATH)
    by_task = {r["task_id"]: r for r in rows}
    for task_id in ALL_TASKS:
        assert task_id in by_task, f"RESET_CHECKPOINT_MATRIX.csv lacks a row for {task_id}"
        row = by_task[task_id]
        assert row["condition_neutral"] == "yes", task_id
        assert row["status"].strip().upper() == "TODO", f"{task_id} must stay unresolved (TD-B01)"
        assert "withheld" in row["checkpoint_definition"].lower(), (
            f"{task_id}: the predicate must be withheld, not published"
        )
    # the two template rows are retained
    assert "TASK-TEMPLATE-A" in by_task and "TASK-TEMPLATE-B" in by_task


def test_reset_matrix_publishes_no_private_checkpoint_content():
    text = _text(RESET_MATRIX_PATH)
    for leak in ("AR-", "OPP-", "expected_layer", "prohibited_layer"):
        assert leak not in text, f"RESET_CHECKPOINT_MATRIX.csv leaks {leak}"
    for row in _rows(RESET_MATRIX_PATH):
        if row["task_id"] in ALL_TASKS:
            # no concrete numeric budget or fraction may appear yet (TD-B01/TD-B11)
            assert not re.search(r"\d+\s*(tokens|turns|minutes)", row["total_budget"]), row["task_id"]


# --------------------------------------------------------------------------- #
# 11. Gate notes carry the classification consequences
# --------------------------------------------------------------------------- #
def _gate(gate_id: str) -> str:
    row = next(r for r in _rows(GATES_PATH) if r["gate_id"] == gate_id)
    return re.sub(r"\s+", " ", row["notes"]).lower()


def test_gate_g1_records_pt06_functional_only_and_pr02_blocked():
    notes = _gate("G1")
    assert "pt06 is functional-only" in notes
    assert "pr02 remains blocked and inactive" in notes
    assert "only dependency-direction opportunities" in notes


def test_gate_g2_records_boundary_repetition_floor_and_comment_risk():
    notes = _gate("G2")
    assert "shared boundary decisions" in notes
    assert "floor effect" in notes
    assert "comments" in notes and "td-b23" in notes


def test_gate_g6_adds_attribution_validation_and_retains_existing_requirements():
    notes = _gate("G6")
    assert "attribution" in notes
    assert "new files" in notes, "G6 must require mutation cases using new files"
    assert "retained, not replaced" in notes, (
        "G6 must keep its false-positive/false-negative requirements"
    )
    # and the original requirements are still in the pass criterion
    row = next(r for r in _rows(GATES_PATH) if r["gate_id"] == "G6")
    evidence = (row["pass_criterion"] + row["required_evidence"]).lower()
    assert "precision" in evidence and "recall" in evidence
    assert "known-good" in evidence


# --------------------------------------------------------------------------- #
# 12. Nothing was frozen; no benchmark ran
# --------------------------------------------------------------------------- #
def test_protocol_remains_pre_freeze():
    readme = _text(DOCS_V2_README)
    assert "PRE-FREEZE DRAFT" in readme
    assert "No `protocol-freeze` tag currently exists" in readme
    md = _flat(DECISIONS_MD)
    assert "pre-freeze draft" in md
    assert "protocol remains pre-freeze" in md


def test_no_gate_is_marked_passed():
    for row in _rows(GATES_PATH):
        status = row["status"].strip().lower()
        assert "not evaluated" in status and "passed" not in status, row["gate_id"]


def test_no_claim_is_marked_supported():
    for row in _rows(CLAIMS_PATH):
        assert row["status"].strip().lower() == "candidate", row["claim_id"]


def test_no_benchmark_result_exists():
    results = REPO / "experiments" / "v2" / "results"
    stray = [
        p.relative_to(REPO).as_posix()
        for p in results.rglob("*")
        if p.is_file() and p.name != "README.md"
    ]
    assert not stray, f"no benchmark result may exist in this package: {stray}"


def test_task_statuses_stay_candidate_and_nothing_is_frozen():
    for task_id in ALL_TASKS:
        assert INDEX_BY_ID[task_id]["task_status"] == "candidate", task_id
        assert MATRIX_BY_ID[task_id]["task_status"] == "candidate", task_id
        assert (
            MATRIX_BY_ID[task_id]["hidden_evaluator_manifest_hash"]
            == "stored_in_private_evaluator_repo"
        ), f"{task_id}: no manifest hash may be pinned publicly"


def test_the_authoring_report_records_that_nothing_was_frozen():
    report = _flat(REPORT_PATH)
    assert "no task body or task content hash changed" in report
    assert "manifest, endpoint or protocol was frozen" in report
    assert "the oracle was not implemented or changed" in report
