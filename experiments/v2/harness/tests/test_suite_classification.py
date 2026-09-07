"""Governance tests for the suite-classification decision (decision D).

The independently approved suite-level decision narrowed the confirmatory
construct to **layered dependency-direction conformance**. That narrowing is only
worth anything if it is mechanically enforced, so this module asserts:

* all eight public task bodies and their recorded hashes are **unchanged** by the
  classification (classification is metadata, never a task edit);
* ``PT01``-``PT04`` are E1-``scored``, ``PT05``/``PT06`` are ``functional-only``,
  and ``PR01``/``PR02`` are ``inactive-reserve``, consistently in both public CSVs;
* ``PT05`` and ``PT06`` are excluded from E1 **without** being classified as a
  failed run;
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
SCHEMAS_DIR = REPO / "experiments" / "v2" / "schemas"
FINDING_SCHEMA = SCHEMAS_DIR / "architecture_finding.schema.json"
ORACLE_RESULT_SCHEMA = SCHEMAS_DIR / "oracle_result.schema.json"
MANIFEST_SCHEMA = SCHEMAS_DIR / "evaluator_manifest.schema.json"
MANIFEST_TEMPLATE = REPO / "experiments" / "v2" / "manifests" / "evaluator_manifest.template.json"
ORACLE_TRACE_PATH = DOCS_V2 / "ORACLE_TRACEABILITY.csv"
ORACLE_REQS_PATH = DOCS_V2 / "ORACLE_VALIDATION_REQUIREMENTS.md"
ORACLE_SRC = REPO / "experiments" / "v2" / "oracle" / "src"

#: ``PT07`` and then ``PT08`` were authored later, under DECISION B (``TD-B34``),
#: and are ``scored`` like ``PT01``-``PT04``. They are listed apart in
#: :data:`AUTHORED_UNDER_DECISION_B` wherever a check is specifically about the
#: classification package, which predates both. ``PT08``'s ``scored`` value still
#: records intent, never a demonstrated denominator: its public-authoring review has
#: passed and its private evaluator package is authored and approved, but its
#: manifest is ``status=review``, ``G1`` is not passed and it is not run-eligible.
CLASSIFICATION_SCORED = ["PT01", "PT02", "PT03", "PT04"]
AUTHORED_UNDER_DECISION_B = ["PT07", "PT08"]
SCORED = CLASSIFICATION_SCORED + AUTHORED_UNDER_DECISION_B
FUNCTIONAL_ONLY = ["PT05", "PT06"]
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
    # authored later, under DECISION B; each pinned the moment it was authored
    "PT07": "557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7",
    "PT08": "a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2",
}

ELIGIBILITY_VOCABULARY = {"scored", "functional-only", "inactive-reserve"}

#: Candidates that have been authored in public but have **no private evaluator
#: package yet**, so their public rows must carry the `not_yet_authored`
#: placeholder rather than `stored_in_private_evaluator_repo`. Being on this list is
#: a statement about the private side only: it is never a licence to treat the task
#: as frozen, reviewed or E1-active.
#:
#: EMPTY as of PT08-PUB-P2-2: every authored candidate now has a private evaluator
#: package (PT07's was authored earlier, PT08's after its public-authoring review
#: passed). The set is kept rather than deleted because the placeholder distinction
#: it encodes is permanent policy and applies to every future task.
NO_PRIVATE_PACKAGE_YET: set = set()

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

    Lets an assertion match a phrase that the source hard-wraps, emphasises, or
    carries inside a markdown blockquote.
    """
    raw = _text(path).replace("*", "").replace("`", "")
    raw = re.sub(r"(?m)^\s*>\s?", "", raw)  # markdown blockquote markers
    return re.sub(r"\s+", " ", raw).lower()


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


def test_exactly_the_recorded_tasks_are_present_and_no_extra_appeared():
    assert sorted(INDEX_BY_ID) == sorted(ALL_TASKS)
    assert sorted(MATRIX_BY_ID) == sorted(ALL_TASKS)
    assert len(ALL_TASKS) == 10, (
        "the eight classified candidates plus PT07 and PT08; a change here must be a "
        "deliberate authoring decision, never drift"
    )


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


def test_the_scored_candidates_are_e1_scored():
    for task_id in SCORED:
        assert INDEX_BY_ID[task_id]["e1_analysis_eligibility"] == "scored", task_id


@pytest.mark.parametrize("task_id", FUNCTIONAL_ONLY)
def test_pt05_and_pt06_are_functional_only(task_id):
    for row, label in ((INDEX_BY_ID[task_id], "TASK_INDEX.csv"), (MATRIX_BY_ID[task_id], "matrix")):
        assert row["e1_analysis_eligibility"] == "functional-only", f"{task_id} in {label}"


def test_pr01_and_pr02_are_inactive_reserves():
    for task_id in INACTIVE_RESERVE:
        assert INDEX_BY_ID[task_id]["e1_analysis_eligibility"] == "inactive-reserve", task_id


def test_exactly_six_of_the_eight_primary_candidates_are_scored():
    """Four from the classification decision, plus PT07 and PT08 under DECISION B.

    ``PT05``/``PT06`` stay structurally excluded; nothing about authoring a new
    candidate may readmit them.
    """
    primary = [t for t in ALL_TASKS if INDEX_BY_ID[t]["primary_or_reserve"] == "primary"]
    assert len(primary) == 8, primary
    scored = [t for t in primary if INDEX_BY_ID[t]["e1_analysis_eligibility"] == "scored"]
    assert sorted(scored) == sorted(SCORED), (
        f"six of eight primary candidates may contribute to E1, got {scored}"
    )
    assert set(FUNCTIONAL_ONLY).isdisjoint(scored)


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
# 3. A functional-only task is excluded from E1 without being a failed run
# --------------------------------------------------------------------------- #
def test_e1_exclusion_is_not_a_failed_run():
    sap = _flat(SAP_PATH)
    assert "structurally ineligible" in sap, "the SAP must name structural ineligibility"
    assert "not coded as zero violations" in sap or "never entered as zero violations" in sap
    assert "not recorded as a failed run" in sap or "never counted as a failed run" in sap, (
        "the SAP must state that E1 exclusion is not a failed run"
    )
    assert "no_patch" in sap and "refusal" in sap, (
        "the SAP must distinguish structural exclusion from the degenerate-outcome codes"
    )


@pytest.mark.parametrize("task_id", FUNCTIONAL_ONLY)
def test_functional_only_tasks_still_contribute_to_functional_cost_and_exploratory(task_id):
    for path in (SAP_PATH, MATRIX_PATH, REPORT_PATH):
        flat = _flat(path)
        assert "hidden functional acceptance" in flat or "hidden acceptance" in flat, path.name
    matrix_reason = MATRIX_BY_ID[task_id]["e1_eligibility_reason"].lower()
    for token in ("hidden functional acceptance", "cost", "exploratory"):
        assert token in matrix_reason, f"{task_id} reason must mention {token}"


@pytest.mark.parametrize("task_id", FUNCTIONAL_ONLY)
def test_functional_only_tasks_are_still_valid_primary_functional_candidates(task_id):
    reason = MATRIX_BY_ID[task_id]["e1_eligibility_reason"].lower()
    assert "valid primary functional candidate" in reason
    assert "structurally excluded from e1" in reason


def test_pt05_reclassification_reason_is_structural_and_pre_run():
    """PT05 is functionally valid; only its E1 exposure is missing (Part B)."""
    reason = MATRIX_BY_ID["PT05"]["e1_eligibility_reason"].lower()
    assert "creates no currently scored dependency-direction opportunity" in reason, (
        "PT05's reason must name the structural cause: no task-created scored "
        "dependency-direction opportunity"
    )
    assert "before any benchmark or model execution" in reason, (
        "PT05's reason must state that the reclassification predates any run"
    )
    for forbidden_framing in (
        "zero violations",
        "failed",
        "missing",
        "invalid",
        "refusal",
    ):
        # each may appear ONLY inside its explicit denial
        for match in re.finditer(re.escape(forbidden_framing), reason):
            window = reason[max(0, match.start() - 60) : match.start()]
            assert "not " in window, (
                f"PT05's reason presents {forbidden_framing!r} without a denial: {window!r}"
            )


def test_pt05_reclassification_is_not_attributed_to_a_model_outcome():
    report = _flat(REPORT_PATH)
    assert "pt05 is functionally valid but structurally ineligible for e1" in report, (
        "the authoring report must state PT05's reclassification in the approved wording"
    )
    assert "not based on a model outcome" in report
    assert "no benchmark or model execution" in report


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


def test_report_states_which_primary_candidates_contribute_to_e1():
    """The scored subset must be stated for the CURRENT suite, not a stale one.

    It read "four of the six primary candidates" while the suite held six; after
    ``PT07`` and then ``PT08`` were authored under DECISION B the current statement
    is six of eight, and the assertion moves with it rather than pinning a
    superseded count.
    """
    report = _flat(REPORT_PATH)
    assert "six of the eight primary candidates currently remain e1-scored candidates" in report
    assert "pt01-pt04, pt07 and pt08 are scored" in report


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
# 9. Blockers are recorded; only the substrate-leakage pair has been fixed
# --------------------------------------------------------------------------- #
NEW_BLOCKERS = [f"TD-B{i}" for i in range(23, 34)]

#: The two blockers the model-visible architecture-comment remediation closed by
#: actually doing the work: removing the disclosure (TD-B23) and extending the
#: leakage audit that proves it stays removed (TD-B24). Every other blocker in
#: this family must still be open.
RESOLVED_BLOCKERS = {"TD-B23", "TD-B24"}

#: Closed by later, separate work packages, and listed apart from
#: RESOLVED_BLOCKERS because they belong to different threat classes and different
#: families. TD-B23/TD-B24 are about the substrate stating the scored RULE; TD-B38
#: is about it revealing the EXPERIMENT; TD-B40 is about the private opportunity
#: MIGRATION and its independent re-approval, and closed only once both of its
#: residuals completed. Keeping them separate preserves this guard's real job:
#: proving that no remediation let an unrelated blocker ride along.
#:
#: TD-B40's closure is deliberately narrow and is asserted as such in
#: test_private_state_reconciliation.py: it freezes no manifest, passes no gate
#: (G1 included), activates no reserve, and resolves neither TD-B34 nor TD-B39 —
#: all four of which this module's own per-blocker status assertions still require
#: to be open.
RESOLVED_ELSEWHERE = {"TD-B38", "TD-B40"}


@pytest.mark.parametrize("decision_id", NEW_BLOCKERS)
def test_each_new_blocker_is_registered_blocking_and_correctly_statused(decision_id):
    rows = _by_id(_rows(DECISIONS_CSV), key="decision_id")
    assert decision_id in rows, f"{decision_id} is missing from OPEN_DECISIONS.csv"
    row = rows[decision_id]
    assert row["blocking"] == "yes", f"{decision_id} must be blocking"
    expected = "resolved" if decision_id in RESOLVED_BLOCKERS else "open"
    assert row["status"].strip().lower() == expected, (
        f"{decision_id} must be {expected}"
    )
    assert row["owner"].strip(), f"{decision_id} needs an owner"
    assert row["gate"].strip(), f"{decision_id} needs a gate mapping"


def test_only_the_substrate_leakage_decisions_are_closed():
    """Nothing else may ride along on the substrate remediations."""
    closed = {
        row["decision_id"]
        for row in _rows(DECISIONS_CSV)
        if row["status"].strip().lower() != "open"
    }
    assert closed == RESOLVED_BLOCKERS | RESOLVED_ELSEWHERE, (
        f"unexpected closed decisions: {sorted(closed - RESOLVED_BLOCKERS - RESOLVED_ELSEWHERE)}"
    )


def test_no_blocker_in_this_family_was_closed_by_the_awareness_remediation():
    """The awareness package closed TD-B38 only; TD-B25..TD-B33 stay open."""
    rows = _by_id(_rows(DECISIONS_CSV), key="decision_id")
    for decision_id in NEW_BLOCKERS:
        if decision_id in RESOLVED_BLOCKERS:
            continue
        assert rows[decision_id]["status"].strip().lower() == "open", (
            f"{decision_id} must remain open"
        )


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


def test_source_comment_leakage_is_neutralised_and_recorded():
    """TD-B23 is resolved by removal, not by restatement.

    The earlier form of this test asserted the *unfixed* premise and said to close
    TD-B23 and update it if the comments were ever deliberately neutralised. They
    have been, so it now asserts the opposite: the disclosure is gone from all
    three files that carried it, and the registry records which disposition was
    taken.
    """
    rows = _by_id(_rows(DECISIONS_CSV), key="decision_id")
    b23 = rows["TD-B23"]
    assert b23["status"].strip().lower() == "resolved"
    assert "NEUTRALISE" in b23["decision"].upper(), (
        "TD-B23 offered neutralise-or-pre-register; the registry must say which"
    )
    assert rows["TD-B24"]["status"].strip().lower() == "resolved"

    app = _text(REPO / "apps" / "api" / "src" / "app.ts")
    assert "BOUNDARY VIOLATION EXAMPLE" not in app.upper(), (
        "the worked boundary-violation example is back in the substrate"
    )
    for phrase in ("cannot import core", "should not depend on core"):
        assert phrase not in app.lower(), f"app.ts states the rule again: {phrase!r}"

    infra = _text(REPO / "libs" / "infra" / "src" / "index.ts").lower()
    assert "avoid importing from core" not in infra
    assert "deliberate architectural choice" not in infra

    features = _text(REPO / "libs" / "features" / "src" / "index.ts").lower()
    assert "without directly importing core" not in features

    # ...but the files are still real source, not stripped to nothing
    for rel in ("apps/api/src/app.ts", "libs/infra/src/index.ts", "libs/features/src/index.ts"):
        text = _text(REPO / rel)
        assert "@afci-bench/" in text and "export" in text, f"{rel} lost its content"


def test_the_leakage_sweep_now_reads_source_content():
    """TD-B24 is resolved: the sweep opens files instead of only matching names."""
    from prepare_model_worktree import (  # noqa: WPS433
        find_comment_disclosures,
        scan_snapshot_violations,
        scan_source_comment_disclosures,
    )

    assert callable(scan_snapshot_violations)
    assert callable(scan_source_comment_disclosures)

    src = _text(REPO / "experiments" / "v2" / "harness" / "prepare_model_worktree.py")
    fn = src.split("def scan_snapshot_violations")[1].split("\ndef ")[0]
    assert "scan_source_comment_disclosures" in fn, (
        "scan_snapshot_violations must delegate to the source-comment sweep"
    )
    body = src.split("def scan_source_comment_disclosures")[1].split("\ndef ")[0]
    assert "read_text" in body, "the source-comment sweep must actually read file content"

    # it detects the historical disclosure and leaves ordinary prose alone
    assert find_comment_disclosures(Path("x.ts"), "// api cannot import core directly\n")
    assert not find_comment_disclosures(
        Path("x.ts"), "// Adapter to convert infra's OrderEntity to core's Order\n"
    )


def test_attribution_and_manifest_coverage_blockers_are_recorded():
    rows = _by_id(_rows(DECISIONS_CSV), key="decision_id")
    b27 = rows["TD-B27"]["decision"].lower()
    # The attribution rule is decided (frozen architectural scope, not an exact
    # importer path) and mutation-validated for NEW files; what remains blocking is
    # re-authoring the private opportunity sets and the labelled-corpus validation.
    assert "frozen architectural scope" in b27 and "new file" in b27
    assert "locator.importer_path is provenance only" in b27
    assert "remains blocking" in b27
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


def test_reset_matrix_has_a_withheld_row_for_each_candidate():
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
        # Two placeholders are legal, and only these two. Every candidate that has
        # a private package carries `stored_in_private_evaluator_repo`; a candidate
        # authored in public with no private package yet carries `not_yet_authored`
        # (PT08's value, and PT07's until its package was authored). A real hash
        # here would pin private content publicly and would also imply a frozen
        # package, so neither is admissible pre-freeze.
        manifest_hash = MATRIX_BY_ID[task_id]["hidden_evaluator_manifest_hash"]
        expected = (
            "not_yet_authored" if task_id in NO_PRIVATE_PACKAGE_YET
            else "stored_in_private_evaluator_repo"
        )
        assert manifest_hash == expected, (
            f"{task_id}: expected the {expected!r} placeholder, got {manifest_hash!r}; "
            "no manifest hash may be pinned publicly"
        )
        assert not re.fullmatch(r"[0-9a-f]{16,}", manifest_hash), task_id


def test_the_authoring_report_records_that_nothing_was_frozen():
    report = _flat(REPORT_PATH)
    assert "no task body or task content hash changed" in report
    assert "manifest, endpoint or protocol was frozen" in report
    # The oracle IS changed by the production-source policy, so the report must
    # scope that change rather than deny it: no new rule family, no new answer.
    assert "no new architecture-rule family was implemented" in report
    assert "production-source scoring policy" in report
    assert "adds no rule, no opportunity and no answer" in report


# --------------------------------------------------------------------------- #
# 13. Repository-wide contradiction sweep
#
# The presence tests above prove the approved wording EXISTS. These prove no
# equivalent CONTRADICTORY wording exists anywhere else, which is the failure mode
# that let the superseded per-rule endpoint survive in the oracle specs. Each
# sweep is deliberately *contextual*, not a blanket ban: a hit is tolerated only
# when its surrounding window explicitly marks it as prohibited, superseded,
# legacy, historical (v1), or as CON-ACB secondary/manual evidence. Legitimate
# discussion of broader architecture stays legal; asserting it as E1 does not.
# --------------------------------------------------------------------------- #

#: Markers that make a superseded phrase legitimate in context - it is being
#: forbidden, labelled legacy/descriptive, or narrated as the pre-decision state.
EXCULPATING = (
    "not ",
    "never",
    "no longer",
    "cannot",
    "n't",
    "superseded",
    "pre-narrowing",
    "pre-decision",
    "legacy",
    "prohibit",
    "inadmissible",
    "forbid",
    "instead of",
    "rather than",
    "descriptive",
    "v1 ",
    "had all retained",
)

#: Markers that make a broad-architecture statement legitimate: it is explicitly
#: filed as the non-directly-measured construct or as secondary/manual evidence.
ACB_LABELLED = (
    "con-acb",
    "con-ai",
    "secondary",
    "manual",
    "exploratory",
    "not directly measured",
    "does not directly measure",
    "kappa",
    "broader",
)


def _swept_files():
    """Public protocol, traceability and schema artifacts.

    Deliberately broad: every docs/v2 protocol document and matrix, every public
    schema, the public task artifacts, the manifest template and the root README.
    Nothing is allowlisted out - a contradictory sentence in ANY of these fails.
    """
    return (
        sorted(DOCS_V2.glob("*.md"))
        + sorted(DOCS_V2.glob("*.csv"))
        + sorted(SCHEMAS_DIR.glob("*.json"))
        + [
            REPORT_PATH,
            INDEX_PATH,
            MANIFEST_TEMPLATE,
            REPO / "experiments" / "v2" / "manifests" / "README.md",
            REPO / "README.md",
        ]
    )


_SENTENCE_END = re.compile(r"(?<=[.!?])\s")


def _clause(flat: str, start: int, end: int, cap: int = 200) -> str:
    """The sentence containing [start:end), clipped to +/- ``cap`` characters.

    Scoping to the sentence matters: an early version used a wide symmetric
    window, and an unrelated "not" elsewhere in the paragraph silently exculpated
    a genuine violation (a mutation test caught it). A prohibition or legacy label
    has to sit in the SAME statement as the phrase it disowns. The character cap
    stops a long, period-free CSV cell from becoming one permissive "sentence".
    """
    left = 0
    for m in _SENTENCE_END.finditer(flat, 0, start):
        left = m.end()
    m = _SENTENCE_END.search(flat, end)
    right = m.start() if m else len(flat)
    return flat[max(left, start - cap) : min(right, end + cap)]


def _offences(pattern: str, allow=EXCULPATING):
    """Every occurrence of ``pattern`` whose own sentence carries no exculpating marker."""
    bad = []
    for path in _swept_files():
        flat = _flat(path)
        for match in re.finditer(re.escape(pattern), flat):
            clause = _clause(flat, match.start(), match.end())
            if not any(marker in clause for marker in allow):
                bad.append(f"{path.name}: {clause[:200]!r}")
    return bad


def test_no_artifact_defines_e1_with_a_per_rule_denominator():
    for phrase in (
        "architecture-violation rate per applicable rule",
        "violation rate per applicable rule",
        "per applicable rule/opportunity",
        "rate per applicable rule",
    ):
        offences = _offences(phrase)
        assert not offences, (
            f"superseded per-rule E1 denominator {phrase!r} stated without a "
            f"prohibition/legacy marker: {offences}"
        )


def test_no_artifact_names_e1_the_architecture_rule_violation_rate():
    for phrase in (
        "architecture-violation rate",
        "architecture-rule violation rate",
        "architecture-rule violation count/rate",
    ):
        offences = _offences(phrase)
        assert not offences, (
            f"superseded endpoint name {phrase!r} used as a current definition: {offences}"
        )


def test_applicable_rule_count_is_never_presented_as_the_e1_offset():
    """`applicable_rule_count` may only appear alongside its prohibition."""
    offences = _offences("applicable_rule_count")
    assert not offences, f"applicable_rule_count presented without its prohibition: {offences}"


def test_applicable_rule_satisfaction_is_not_offered_as_an_endpoint():
    offences = _offences("applicable-rule satisfaction")
    assert not offences, f"superseded E2 name used as a current definition: {offences}"


def test_manual_adjudication_is_never_pooled_into_e1():
    """No CON-AC traceability row may be produced by manual adjudication."""
    for row in _rows(ORACLE_TRACE_PATH):
        if row["construct"] != "CON-AC":
            continue
        assert "manual" not in row["evaluator_type"].lower(), (
            f"{row['oracle_id']}: a CON-AC (E1/E2) quantity must be automated only, "
            f"got evaluator_type={row['evaluator_type']!r}"
        )
        assert "manual adjudication" not in row["evaluator_ref"].lower(), (
            f"{row['oracle_id']}: manual adjudication must not feed a CON-AC quantity"
        )
    # and the prose must say so somewhere authoritative
    assert "manual assessments never enter e1" in _flat(ORACLE_REQS_PATH)


def test_no_ineligible_task_is_mapped_into_e1():
    """PT06 and the inactive reserves must not be traced to CON-AC or to CL01."""
    ineligible = set(FUNCTIONAL_ONLY) | set(INACTIVE_RESERVE)
    for row in _rows(ORACLE_TRACE_PATH):
        listed = {t.strip() for t in re.split(r"[;,]", row["task_id"])}
        overlap = listed & ineligible
        if not overlap:
            continue
        assert row["construct"] != "CON-AC", (
            f"{row['oracle_id']} traces E1-ineligible task(s) {sorted(overlap)} to CON-AC"
        )
        claims = {c.strip() for c in row["claim_ids"].split(";")}
        assert "CL01" not in claims, (
            f"{row['oracle_id']} maps E1-ineligible task(s) {sorted(overlap)} to the "
            f"confirmatory E1 claim CL01"
        )


def test_no_traceability_row_maps_all_eight_tasks_to_the_e1_claim():
    for row in _rows(ORACLE_TRACE_PATH):
        listed = {t.strip() for t in re.split(r"[;,]", row["task_id"])}
        if set(ALL_TASKS) <= listed:
            claims = {c.strip() for c in row["claim_ids"].split(";")}
            assert "CL01" not in claims, (
                f"{row['oracle_id']} maps all eight candidates to CL01; E1 admits the "
                f"scored subset only"
            )


def test_a_stub_or_manual_construct_is_never_traced_to_e1():
    """CON-ACB rows exist and are kept out of the confirmatory E1 claim family."""
    e1_claims = {"CL01", "CL02", "CL03", "CL04"}
    acb_rows = [r for r in _rows(ORACLE_TRACE_PATH) if r["construct"] == "CON-ACB"]
    assert acb_rows, "the broader dimensions must have their own CON-ACB traceability row"
    for row in acb_rows:
        claims = {c.strip() for c in row["claim_ids"].split(";")}
        assert not (claims & e1_claims), (
            f"{row['oracle_id']} (CON-ACB) is mapped into the E1 claim family {sorted(claims & e1_claims)}"
        )
        notes = row["notes"].lower()
        assert "never pooled into the e1" in notes or "not directly measured by e1" in notes


def test_oracle_result_is_not_sufficient_for_e1_without_opportunity_accounting():
    schema = json.loads(_text(ORACLE_RESULT_SCHEMA))
    assert "opportunity_accounting" in schema["required"], (
        "oracle_result must REQUIRE the opportunity accounting E1 is computed from"
    )
    for field in ("applicable_rule_count", "satisfaction_proportion", "rules_satisfied_count"):
        assert field not in schema["required"], (
            f"{field} is a legacy descriptive diagnostic and must not be structurally privileged"
        )
    blob = (schema["title"] + " " + schema["description"]).lower()
    assert "dependency-direction" in blob
    # The phrase may appear only inside its own prohibition, never as a self-description.
    for match in re.finditer(r"direct architectural-conformance measurement", blob):
        window = blob[max(0, match.start() - 120) : match.end()]
        assert any(m in window for m in EXCULPATING), (
            f"oracle_result advertises itself as a broad architectural-conformance "
            f"measurement: ...{window[-110:]!r}"
        )


def test_confirmatory_research_questions_name_dependency_direction():
    """Neither RQ1 nor RQ2 may state its confirmatory scope as broad conformance."""
    rq = _text(RQ_PATH)
    for heading in ("### RQ1", "### RQ2"):
        start = rq.index(heading)
        end = rq.index("### RQ", start + len(heading))
        body = re.sub(r"\s+", " ", rq[start:end].replace("*", "").replace("`", "")).lower()
        assert "dependency-direction" in body or "dependency direction" in body, (
            f"{heading} must state its confirmatory scope as dependency-direction conformance"
        )
        for match in re.finditer(r"architectural conformance", body):
            window = body[max(0, match.start() - 260) : match.end() + 260]
            assert any(m in window for m in ACB_LABELLED), (
                f"{heading} uses broad 'architectural conformance' without a "
                f"CON-ACB/secondary/exploratory label: ...{window[170:350]!r}"
            )


def test_the_endpoint_defining_artifacts_all_carry_the_narrowed_name():
    """Every artifact that DEFINES the endpoint states the same narrowed name."""
    expected = "dependency-direction violation rate per applicable frozen opportunity"
    for path in (SAP_PATH, RQ_PATH, ORACLE_REQS_PATH, DOCS_V2_README, REPO / "README.md"):
        assert expected in _flat(path), f"{path.name} must carry E1's narrowed name"
    g3 = _gate("G3")
    assert expected in g3, "gate G3 must state the narrowed primary endpoint"
    assert "dependency-direction conformance only" in g3
    assert "violated_opportunity_count" in g3 and "applicable_opportunity_count" in g3
    assert "scored tasks only" in g3 or "scored tasks ONLY".lower() in g3
    assert "pt06" in g3 and "must not enter" in g3
    trace = {r["oracle_id"]: r for r in _rows(ORACLE_TRACE_PATH)}
    assert expected in trace["OT-AC-VIOL"]["measured_quantity"].lower()


def test_broad_architecture_discussion_stays_legal_when_properly_labelled():
    """Positive control: the sweep must not be an indiscriminate keyword ban.

    CON-ACB is *about* broader architectural conformance, so the protocol has to be
    able to discuss it. This asserts that discussion is present and survives the
    same contextual rule the sweeps above apply.
    """
    rq = _flat(RQ_PATH)
    assert re.search(
        r"con-acb\s*[-–—]\s*broader architectural conformance \(not directly measured by e1\)",
        rq,
    ), "the CON-ACB construct heading must survive as legitimate broad-architecture discussion"
    for match in re.finditer(r"broader architectural conformance", rq):
        window = rq[max(0, match.start() - 260) : match.end() + 260]
        assert any(m in window for m in ACB_LABELLED), (
            "the CON-ACB discussion must itself stay labelled"
        )


# --------------------------------------------------------------------------- #
# 14. Manifest eligibility is schema-bound and fail-closed
# --------------------------------------------------------------------------- #
def test_evaluator_manifest_requires_analysis_eligibility():
    schema = json.loads(_text(MANIFEST_SCHEMA))
    assert "e1_analysis_eligibility" in schema["required"], (
        "the manifest must be bound to the public classification, not merely annotated"
    )
    prop = schema["properties"]["e1_analysis_eligibility"]
    assert set(prop["enum"]) == ELIGIBILITY_VOCABULARY, prop["enum"]


def test_manifest_eligibility_vocabulary_matches_the_public_index():
    """One vocabulary across the public index, the public matrix and the manifest."""
    schema = json.loads(_text(MANIFEST_SCHEMA))
    manifest_values = set(schema["properties"]["e1_analysis_eligibility"]["enum"])
    oracle_values = set(
        json.loads(_text(ORACLE_RESULT_SCHEMA))["properties"]["e1_analysis_eligibility"]["enum"]
    )
    index_values = {INDEX_BY_ID[t]["e1_analysis_eligibility"] for t in ALL_TASKS}
    assert manifest_values == oracle_values == ELIGIBILITY_VOCABULARY
    assert index_values <= manifest_values


def test_the_five_eligibility_gates_are_documented_and_implemented():
    """Each gate must exist in the spec AND as a fail-closed reason in the engine."""
    reasons = _text(ORACLE_SRC / "errors.ts")
    integrity = _text(ORACLE_SRC / "manifestIntegrity.ts")
    spec = _flat(ORACLE_REQS_PATH)
    for code in (
        "ELIGIBILITY_MISSING",
        "ELIGIBILITY_TASK_INDEX_MISMATCH",
        "ELIGIBILITY_DENOMINATOR_CONFLICT",
        "ELIGIBILITY_RESERVE_INACTIVE",
        "ELIGIBILITY_SCORED_WITHOUT_OPPORTUNITIES",
    ):
        assert code in reasons, f"{code} must be a declared oracle fail reason"
        assert code.lower() in spec, f"{code} must be documented in the oracle spec"
    for code in (
        "ELIGIBILITY_TASK_INDEX_MISMATCH",
        "ELIGIBILITY_DENOMINATOR_CONFLICT",
        "ELIGIBILITY_RESERVE_INACTIVE",
        "ELIGIBILITY_SCORED_WITHOUT_OPPORTUNITIES",
    ):
        assert code in integrity, f"{code} must be thrown by the integrity gates"
    # the loader is the gate for a pre-migration manifest
    assert "ELIGIBILITY_MISSING" in _text(ORACLE_SRC / "manifest.ts")


def test_the_committed_manifest_template_carries_a_consistent_eligibility():
    tpl = json.loads(_text(MANIFEST_TEMPLATE))
    assert tpl["e1_analysis_eligibility"] in ELIGIBILITY_VOCABULARY
    # gate 4: a 'scored' manifest may not have an empty opportunity set
    if tpl["e1_analysis_eligibility"] == "scored":
        assert tpl["opportunities"], "a scored manifest needs a non-zero denominator"
    else:
        assert tpl["opportunities"] == [], "the template publishes no opportunities"


def test_private_manifest_migration_is_recorded_and_no_private_repo_was_touched():
    for flat in (_flat(ORACLE_REQS_PATH), _flat(DECISIONS_MD)):
        assert "migrat" in flat, "the private-manifest migration must be recorded publicly"
    reqs = _flat(ORACLE_REQS_PATH)
    assert "private manifests require migration" in reqs
    assert "were not touched here" in reqs or "were not accessed" in reqs
    decisions = _flat(DECISIONS_MD)
    assert "not accessed or modified" in decisions, (
        "the decision log must record that the private evaluator repository was untouched"
    )
    assert "fail closed" in decisions


# --------------------------------------------------------------------------- #
# 15. Production-source scoring (E1 measures production dependencies only)
# --------------------------------------------------------------------------- #
PRODUCTION_SOURCE_SRC = ORACLE_SRC / "productionSource.ts"
SCOPE_ATTRIBUTION_TEST = (
    REPO / "experiments" / "v2" / "oracle" / "tests" / "scopeAttribution.test.ts"
)

#: The test/config classes the approved policy must hold out of the E1 graph.
EXCLUDED_SOURCE_CLASSES = ("*.spec.ts", "*.test.ts", "__tests__", "jest.config.ts")


def test_the_production_source_policy_is_implemented_and_wired_into_scoring():
    """The policy must exist as code AND actually gate the import graph."""
    assert PRODUCTION_SOURCE_SRC.exists(), "the production-source policy module is missing"
    policy = _text(PRODUCTION_SOURCE_SRC)
    for token in EXCLUDED_SOURCE_CLASSES:
        assert token in policy, f"the production-source policy must exclude {token}"
    for directory in ("__mocks__", "__fixtures__", "test-fixtures", "test-helpers"):
        assert directory in policy, f"the policy must exclude the {directory} subtree"
    # It is a policy, not a substring check: production source keeping an
    # incidental word must survive, so `*.config.ts` must NOT be a wildcard.
    assert "'*.config.ts'" not in policy, (
        "`*.config.ts` must not be a wildcard exclusion (app.config.ts is production)"
    )
    # ...and the engine must partition BEFORE building edges.
    engine = _text(ORACLE_SRC / "engine.ts")
    assert "partitionProductionSources" in engine, (
        "the engine must partition the scanned source before resolving imports"
    )
    assert "INVALID_PRODUCTION_SOURCE_POLICY" in _text(ORACLE_SRC / "errors.ts"), (
        "a malformed production-source policy must be a declared fail-closed reason"
    )


def test_the_production_source_policy_is_specified_in_the_oracle_requirements():
    reqs = _flat(ORACLE_REQS_PATH)
    assert "production dependency graph" in reqs
    assert "excluded test/config/support graph" in reqs
    assert "excluded files may still be examined descriptively" in reqs, (
        "the spec must say whether excluded files remain descriptively visible"
    )
    # why excluded edges can never enter either side of E1
    assert "why an excluded edge can never enter the e1 numerator" in reqs
    assert "why an excluded file can never move the e1 denominator" in reqs
    assert "the frozen architectural layer scopes are unchanged" in reqs


def test_the_e1_denominator_stays_frozen_opportunity_based_not_file_based():
    for path in (ORACLE_REQS_PATH, SAP_PATH):
        flat = _flat(path)
        assert "frozen" in flat and "opportunity count" in flat, path.name
    reqs = _flat(ORACLE_REQS_PATH)
    assert "it is not a file count" in reqs, (
        "the spec must state explicitly that the denominator is not a file count"
    )


def test_the_finding_schema_records_the_production_partition():
    schema = json.loads(_text(FINDING_SCHEMA))
    assert "production_source" in schema["required"], (
        "the partition must be recorded on every finding, not optionally"
    )
    block = schema["properties"]["production_source"]
    for field in ("policy_id", "production_file_count", "excluded_file_count", "excluded_paths"):
        assert field in block["properties"], field
        assert field in block["required"], f"{field} must be required"
    # and it must not be presented as an E1 quantity
    assert "descriptive only" in block["description"].lower()


def test_the_manifest_schema_allows_only_an_additive_policy_extension():
    schema = json.loads(_text(MANIFEST_SCHEMA))
    policy = schema["properties"]["dependency_policy"]["properties"]["production_source_policy"]
    assert set(policy["properties"]) <= {
        "policy_id",
        "additional_excluded_config_basenames",
        "additional_excluded_spec_basename_globs",
        "additional_excluded_directory_names",
    }, "a manifest may only ADD exclusions, never remove or replace them"
    assert "production_source_policy" not in schema["properties"]["dependency_policy"]["required"], (
        "omitting the field must be legal - the baseline always applies"
    )
    assert "additive-only" in policy["description"].lower()


def test_the_m8_regression_cases_exist_and_m0_to_m7_are_retained():
    corpus = _text(SCOPE_ATTRIBUTION_TEST)
    for case in ("M8-A", "M8-B", "M8-C", "M8-D", "M8-E", "M8-F"):
        assert case in corpus, f"{case} must exist in the scope-attribution corpus"
    for case in ("M0", "M1", "M2", "M3", "M4", "M4A", "M5", "M6", "M7"):
        assert f"id: '{case}'" in corpus, f"{case} must be retained unchanged"


# --------------------------------------------------------------------------- #
# 16. DECISION B stays open and blocking; nothing is declared confirmatory-ready
# --------------------------------------------------------------------------- #
def test_decision_b_is_registered_open_and_blocking():
    rows = _by_id(_rows(DECISIONS_CSV), key="decision_id")
    assert "TD-B34" in rows, "DECISION B must be registered"
    row = rows["TD-B34"]
    assert row["blocking"] == "yes"
    assert row["status"].strip().lower() == "open"
    text = row["decision"].lower()
    assert "decision b" in text
    assert "before stage 0" in text
    # construct validity, not an oracle failure, and not a reserve activation
    assert "construct validity" in text
    assert "not an oracle failure" in text
    assert "no reserve is being activated" in text
    assert "predates any benchmark or model outcome" in text
    assert "no experimental result exists" in text
    assert "new rule families are not required" in text
    assert "remains the approved attribution mechanism" in text


def test_decision_b_keeps_its_gates_blocking_and_the_suite_not_ready():
    for gate_id in ("G1", "G2", "G6"):
        notes = _gate(gate_id)
        assert "td-b34" in notes or "td-b36" in notes or "td-b37" in notes, (
            f"gate {gate_id} must cite the reassessment blockers it now carries"
        )
        assert "blocking" in notes, f"gate {gate_id} must stay explicitly blocking"
    assert "the suite is not ready" in _gate("G1")
    # no gate anywhere may be marked passed (guarded again here on purpose)
    for row in _rows(GATES_PATH):
        assert "passed" not in row["status"].strip().lower(), row["gate_id"]


def test_stage_0_is_gated_on_decision_b():
    policy = _flat(DOCS_V2 / "PILOT_AND_POWER_POLICY.md")
    assert "stage 0 is additionally gated on decision b" in policy
    assert "td-b34" in policy


def test_the_authoring_requirements_for_the_next_tasks_are_recorded():
    policy = _flat(DOCS_V2 / "TASK_AUTHORING_POLICY.md")
    assert "requirements for the next architecture tasks" in policy
    for requirement in (
        "creates a genuine dependency decision caused by the required functional",
        "does not merely preserve an already-satisfied boundary",
        "feasible through the public interface",
        "avoids implementation-dependent hidden setup",
        "fixed before model output",
        "compatible with legitimate implementation alternatives",
        "does not depend on which file the model creates",
        "duplicate an existing architectural instrument",
        "no architecture hint",
    ):
        assert requirement in policy, f"the authoring bar must state: {requirement!r}"
    assert "do not create artificial tasks merely to hit rule ids" in policy
    assert "task-created decision" in policy


def test_decision_b_itself_authored_nothing_and_the_later_package_authored_one():
    """Two separate facts, both of which must stay on the record.

    The package that *recorded* DECISION B deliberately authored no task — it set
    the acceptance bar instead. A later package authored exactly one candidate,
    ``PT07``. Neither statement may quietly replace the other: losing the first
    would let the requirements look retrofitted to a task that already existed,
    and losing the second would understate what the public suite now contains.
    """
    bodies = sorted(p.stem for p in PUBLIC_TASKS_DIR.glob("*.md") if p.stem in set(ALL_TASKS))
    assert bodies == sorted(ALL_TASKS), "the public task set drifted from the recorded one"
    report = _flat(REPORT_PATH)
    assert "no replacement or additional task was authored" in report, (
        "the DECISION B package's own no-authoring record must stay"
    )
    assert "one new primary task has now been authored under decision b" in report, (
        "the later authoring of PT07 must be recorded"
    )
    assert "this package authored exactly one task body" in report


# --------------------------------------------------------------------------- #
# 17. Statistical governance: clustered exposures, deferred power
# --------------------------------------------------------------------------- #
def test_the_task_set_is_recorded_as_not_confirmatory_ready():
    sap = _flat(SAP_PATH)
    assert "is not confirmatory-ready" in sap
    assert "repeated task exposures to the same boundary are clustered" in sap
    assert "task count is not the independent architecture-decision count" in sap
    assert "cluster identifier will be required" in sap
    assert "no final power value is frozen" in sap
    assert "no power simulation was run" in sap
    report = _flat(REPORT_PATH)
    assert "repeated tasks over one boundary do not count as independent architecture" in report
    assert "further public task authoring is required before stage 0" in report


def test_the_power_simulation_is_deferred_until_more_distinct_decisions_exist():
    for path in (SAP_PATH, DOCS_V2 / "PILOT_AND_POWER_POLICY.md"):
        flat = _flat(path)
        assert "only after" in flat, path.name
        assert "distinct dependency" in flat or "distinct decisions" in flat, path.name
    rows = _by_id(_rows(DECISIONS_CSV), key="decision_id")
    b37 = rows["TD-B37"]["decision"].lower()
    assert "clustered" in b37
    assert "not equal to the independent architecture-decision count" in b37
    assert "cluster identifier" in b37
    assert "no power simulation was run" in b37


#: Phrases that would claim the suite is ready. Each may appear ONLY inside a
#: denial - this is the guard against a later edit quietly declaring readiness.
READINESS_CLAIMS = (
    "confirmatory-ready",
    "ready for stage 0",
    "the suite is ready",
    "enough distinct dependency",
)


@pytest.mark.parametrize("phrase", READINESS_CLAIMS)
def test_no_documentation_claims_the_current_task_set_is_confirmatory_ready(phrase):
    negations = ("no ", "not ", "never", "n't", "cannot", "must ", "insufficient", "too few")
    for path in _swept_files() + [DOCS_V2 / "PILOT_AND_POWER_POLICY.md"]:
        flat = _flat(path)
        for match in re.finditer(re.escape(phrase), flat):
            clause = _clause(flat, match.start(), match.end())
            assert any(n in clause for n in negations), (
                f"{path.name} appears to claim readiness ({phrase!r}) without a "
                f"denial: ...{clause[:200]!r}"
            )


def test_the_readiness_sweep_would_actually_catch_an_affirmative_claim():
    """Guard the guard: the sweep must not be vacuously satisfied.

    Every real occurrence of a readiness phrase currently sits inside a denial, so
    the parametrized sweep above passes. This asserts the same rule REJECTS an
    affirmative claim, using the identical clause-scoping helper on synthetic text.
    """
    negations = ("no ", "not ", "never", "n't", "cannot", "must ", "insufficient", "too few")

    def offends(sentence: str, phrase: str) -> bool:
        flat = re.sub(r"\s+", " ", sentence).lower()
        match = re.search(re.escape(phrase), flat)
        assert match, "premise: the phrase must occur in the synthetic sentence"
        clause = _clause(flat, match.start(), match.end())
        return not any(n in clause for n in negations)

    # An affirmative claim is caught ...
    assert offends("The current task set is confirmatory-ready.", "confirmatory-ready")
    assert offends("The suite is ready for the core grid.", "the suite is ready")
    # ... while the approved denial is not.
    assert not offends(
        "The current four-task architecture set is not confirmatory-ready.",
        "confirmatory-ready",
    )
    # and a denial in a DIFFERENT sentence does not launder the claim
    assert offends(
        "Nothing was frozen. The current task set is confirmatory-ready.",
        "confirmatory-ready",
    )


def test_an_inactive_reserve_keeps_draft_opportunities_but_stays_inactive():
    """Reserves are made analytically inactive, not stripped of draft content."""
    integrity = _text(ORACLE_SRC / "manifestIntegrity.ts")
    assert "analytically inactive" in integrity
    assert "NOT required to be deleted" in integrity or "not required to be deleted" in integrity
    reqs = _flat(ORACLE_REQS_PATH)
    assert "may retain draft opportunities" in reqs
    assert "analytically inactive" in reqs
