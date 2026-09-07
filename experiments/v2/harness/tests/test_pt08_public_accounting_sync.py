"""Fail-closed guards for `PT08-PUB-P2-2`, the public accounting synchronization.

WHY THIS MODULE EXISTS
----------------------
The external independent read-only review of the `PT08` public-authoring package
returned **APPROVE** with **P0 = 0**, **P1 = 0** and **P2 = 2**. `PT08-PUB-P2-2`
recorded that the public repository still described the **pre-admission** state on
many surfaces at once, and that those surfaces had to be reconciled to the admitted
state **before** `PT08`'s manifest freeze.

The defect was never one sentence. It was a *class* of sentence repeated across a
dozen governance and registry surfaces, which is exactly the shape of defect a
presence-only check on one file cannot close. So this module works in two
directions at once:

* **the admitted state is asserted positively**, at the surface that is
  authoritative for it, so a silent revert to `5` / `3 / 1 / 1` fails; and
* **every known stale assertion is swept for repository-wide**, and is permitted
  only inside a passage that carries its own explicit historical marker — which is
  what keeps Part I's requirement ("do not rewrite the pre-authoring record")
  compatible with Part C's ("synchronize the current state").

AND IN THE OTHER DIRECTION
--------------------------
Synchronizing an accounting row is the single most tempting place to over-claim, so
every denial the admission did **not** discharge is asserted here too: nothing is
frozen, `G1` is not passed, `PT08` is not run-eligible, its hidden functional
acceptance stays `draft_unvalidated`, `TD-B34` stays open and blocking, priority B
is not started, `SL-PT08-01` stays the one bounded diagnostic exception, and no
result and no power value exist anywhere.

Pure text and file inspection. No model is invoked, no benchmark runs, no power
simulation runs, and nothing is frozen.
"""
from __future__ import annotations

import csv
import io
import re
from pathlib import Path

import pytest

import governance_text as G

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"
PUBLIC_TASKS = REPO / "experiments" / "v2" / "tasks" / "public"

CLOSURE_PATH = DOCS_V2 / "PT08_PUBLIC_ACCOUNTING_SYNCHRONIZATION.md"
FEASIBILITY_PATH = DOCS_V2 / "DEPENDENCY_TASK_FEASIBILITY.md"
DIAGNOSTIC_PATH = DOCS_V2 / "PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md"
CAND_A1_PATH = DOCS_V2 / "CAND_A1_PREAUTHORING_DECISION.md"
POWER_POLICY_PATH = DOCS_V2 / "PILOT_AND_POWER_POLICY.md"
SAP_PATH = DOCS_V2 / "STATISTICAL_ANALYSIS_PLAN.md"
DECISIONS_CSV = DOCS_V2 / "OPEN_DECISIONS.csv"
GATE_MATRIX = DOCS_V2 / "PILOT_GATE_MATRIX.csv"
MATRIX_PATH = DOCS_V2 / "PILOT_PUBLIC_TASK_MATRIX.csv"
ACCEPTANCE_MATRIX = DOCS_V2 / "TASK_ACCEPTANCE_MATRIX.csv"
LAYER_MATRIX = DOCS_V2 / "TASK_LAYER_MATRIX.csv"
RULE_MATRIX = DOCS_V2 / "TASK_RULE_MATRIX.csv"
ORACLE_TRACE = DOCS_V2 / "ORACLE_TRACEABILITY.csv"
INDEX_PATH = PUBLIC_TASKS / "TASK_INDEX.csv"
REPORT_PATH = PUBLIC_TASKS / "TASK_AUTHORING_REPORT.md"

#: The current, admitted active accounting. One place, so a revert is one failure.
ACTIVE_OPPORTUNITIES = 6
ACTIVE_CLUSTERS = 3
CLUSTER_DEPTHS = {
    "DC-FEATURES-INFRA-AR-DEP-006": 3,
    "DC-FEATURES-API-AR-DEP-006": 2,
    "DC-API-CORE-AR-DEP-005": 1,
}
DEPTHS_RENDERED = "3 / 2 / 1"
ACTIVE_SCORED = ("PT01", "PT02", "PT03", "PT04", "PT07", "PT08")

#: The pre-admission accounting. Not the current state, and never assertable as it.
PRE_ADMISSION_OPPORTUNITIES = 5
PRE_ADMISSION_DEPTHS_RENDERED = "3 / 1 / 1"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(path: Path) -> str:
    return G.norm(_text(path))


def _rows(path: Path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _by_id(path: Path, key: str = "task_id"):
    return {r[key]: r for r in _rows(path)}


def _decision(decision_id: str):
    return _by_id(DECISIONS_CSV, key="decision_id")[decision_id]


# --------------------------------------------------------------------------- 1
# M.1 - M.4 / M.8 — the admitted accounting, at the surface authoritative for it.


def test_the_current_active_opportunity_count_is_six():
    flat = _flat(FEASIBILITY_PATH)
    assert f"active e1 opportunities: {ACTIVE_OPPORTUNITIES}" in flat
    assert f"active e1 opportunities: {PRE_ADMISSION_OPPORTUNITIES}" not in flat, (
        "the pre-admission opportunity count is restated as the current one"
    )


def test_the_current_active_cluster_count_is_three():
    """Admission moves a DEPTH. The cluster count is the thing that must not move."""
    flat = _flat(FEASIBILITY_PATH)
    assert f"decision clusters: {ACTIVE_CLUSTERS}" in flat
    assert "current occupancy is already 3 / 3 clusters" in flat
    for bogus in ("decision clusters: 4", "decision clusters: 2"):
        assert bogus not in flat, f"the cluster count moved: {bogus!r}"


@pytest.mark.parametrize("cluster,depth", sorted(CLUSTER_DEPTHS.items()))
def test_the_current_depths_are_three_two_one(cluster, depth):
    """Row-scoped: the depth comes from that cluster's own occupancy row."""
    start, end = None, None
    lines = _text(FEASIBILITY_PATH).split("\n")
    for i, line in enumerate(lines):
        head = re.match(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", line)
        if head and G.norm(head.group(2)).startswith("3. the demonstrated feasibility"):
            start = i
        elif head and start is not None and i > start:
            end = i
            break
    assert start is not None, "the feasibility ceiling section is missing"
    row = [
        line for line in lines[start:end]
        if line.lstrip().startswith("|") and cluster.lower() in G.norm(line)
    ]
    assert len(row) == 1, f"expected exactly one occupancy row for {cluster}"
    cells = [c.strip() for c in G.norm(row[0]).strip("|").split("|")]
    assert cells[-1] == str(depth), (
        f"{cluster} must record {depth} active observation(s), not {cells[-1]!r}"
    )


@pytest.mark.parametrize(
    "path",
    [FEASIBILITY_PATH, CAND_A1_PATH, REPORT_PATH, CLOSURE_PATH,
     DOCS_V2 / "README.md", DOCS_V2 / "OPEN_DECISIONS.md",
     DECISIONS_CSV, GATE_MATRIX],
    ids=lambda p: p.name,
)
def test_the_rendered_depth_triple_is_the_admitted_one(path):
    """Every surface that renders the triple must render the admitted one.

    Surfaces that state depths per cluster instead (the pilot policy names `n = 2`
    and `n = 1` directly) are covered by the per-cluster occupancy assertions and by
    the stale-assertion sweep, not here.
    """
    flat = _flat(path)
    assert DEPTHS_RENDERED in flat or "3/2/1" in flat, (
        f"{path.name} never states the admitted depth triple"
    )


def test_the_features_api_cluster_records_replication_depth_two():
    """M.8: depth 2 where disclosure is already permitted, and never as breadth."""
    flat = _flat(FEASIBILITY_PATH)
    assert "the priority-a row reads 2" in flat
    assert "one of the three achievable clusters is still a singleton" in flat
    assert "replication depth over one shared decision" in flat
    assert "pseudo-replicates" in flat


def test_the_current_active_scored_set_includes_pt08():
    """M.4: at the authoritative index, at the public matrix, and in the E1 rows."""
    index = _by_id(INDEX_PATH)
    matrix = _by_id(MATRIX_PATH)
    for task_id in ACTIVE_SCORED:
        assert index[task_id]["e1_analysis_eligibility"] == "scored", task_id
        assert matrix[task_id]["e1_analysis_eligibility"] == "scored", task_id
    scored = {t for t, r in index.items() if r["e1_analysis_eligibility"] == "scored"}
    assert scored == set(ACTIVE_SCORED), f"the scored set drifted: {sorted(scored)}"

    trace = {r["oracle_id"]: r for r in _rows(ORACLE_TRACE)}
    for oracle_id in ("OT-AC-VIOL", "OT-AC-SAT", "OT-TASKS-PRIVATE-SCORED"):
        assert "PT08" in trace[oracle_id]["task_id"], oracle_id

    gate = {r["gate_id"]: r for r in _rows(GATE_MATRIX)}["G1"]["notes"]
    assert "PT07 and then PT08" in gate, (
        "the G1 row still enumerates a scored set that excludes PT08"
    )


def test_e1_is_not_redefined_by_the_synchronization():
    """The VALUE of the register moved; the endpoint's definition did not."""
    flat = _flat(CLOSURE_PATH)
    assert "opportunity_accounting.violated_opportunity_count" in flat
    assert "opportunity_accounting.applicable_opportunity_count" in flat
    for inadmissible in ("applicable_rule_count", "rules_satisfied_count",
                         "satisfaction_proportion", "raw_violation_count"):
        assert inadmissible in flat, f"{inadmissible} must stay named as inadmissible"
    assert "remain inadmissible" in flat
    assert "nothing about the endpoint's definition" in flat


# --------------------------------------------------------------------------- 2
# M.5 - M.7 / M.20 — every known stale assertion, swept repository-wide.
#
# A stale assertion may survive ONLY inside a passage that carries its own explicit
# historical marker. That is the whole reconciliation: Part I forbids rewriting the
# pre-authoring record, and Part C forbids leaving a current-state claim stale, so
# the only admissible resolution is a marked historical passage.


#: Markers that turn a superseded statement into recorded history. Deliberately a
#: closed list of the phrasings this repository already uses: a bare "no" or "not"
#: nearby is exactly the rescue the earlier mutation review defeated.
HISTORICAL_MARKERS = (
    "as recorded then",
    "as originally recorded",
    "as recorded at closure",
    "at that point",
    "at that time",
    "when this addendum was written",
    "when this record was written",
    "superseded",
    "historical",
    "td-b34-breadth-historical",
    "consequently, at that time",
)

#: The stale current-state assertions `PT08-PUB-P2-2` exists to remove. Each is
#: written in the tense a LIVE claim would use, so a marked historical restatement
#: ("the active set HELD 5 ...") does not trip it and a live one does.
STALE_ASSERTIONS = (
    # accounting
    "active e1 opportunities: 5",
    "active e1 opportunities remain 5",
    "the active set remains 5 opportunities",
    "cluster observation depths remain 3 / 1 / 1",
    "cluster depths remain 3 / 1 / 1",
    "5 across 3 decision clusters, two of them observed once each",
    "5 across 3 decision clusters, two of which carry a single observation",
    # the priority-A cluster's depth
    "dc-features-api-ar-dep-006 remains at one observation",
    "the priority-a row still reads 1",
    "the priority-a cluster still stands at one",
    "dc-features-api-ar-dep-006 stays at one observation",
    # PT08's private side
    "pt08 has no private evaluator package",
    "no private evaluator package and no manifest exists for it",
    "pt08's private package is not yet authored",
    "pt08's private evaluator package has not been authored",
    "not_yet_authored for pt08",
    "no private package has been authored for pt08 yet",
    "no private evaluator package of its own yet",
    # PT08's public review
    "the independent public-authoring review of pt08 is pending",
    "public-authoring review of this body is pending",
    "public-authoring review is pending",
    # PT08's contribution
    "adds no active observation to any decision cluster",
    "adds no active observation yet",
    "pt08 adds no active observation",
    "it adds no active observation",
    # the singleton count
    "two of the three achievable clusters are singletons",
    "two of the three clusters are singletons",
    "the two singleton clusters",
)


def _passages_containing(needle: str):
    return [p for p in G.all_passages() if needle in p.flat]


@pytest.mark.parametrize("stale", STALE_ASSERTIONS)
def test_every_stale_assertion_is_absent_or_explicitly_historical(stale):
    """M.5 / M.6 / M.7 / M.20, as one sweep over the whole governed corpus."""
    unmarked = [
        f"{p.rel}:{p.line} under {p.heading!r}"
        for p in _passages_containing(stale)
        if not any(marker in p.flat for marker in HISTORICAL_MARKERS)
    ]
    assert unmarked == [], (
        f"the stale current-state assertion {stale!r} is stated as live in:\n  - "
        + "\n  - ".join(unmarked)
    )


def test_that_sweep_would_actually_catch_a_reintroduced_stale_assertion():
    """Guard the guard: an unmarked live restatement must be reported.

    Without this, a sweep whose vocabulary had drifted away from the documents
    would pass by matching nothing at all.
    """
    live = G.Passage(
        rel="docs/v2/README.md",
        heading="a live section",
        line=1,
        kind="paragraph",
        raw="Active E1 opportunities remain 5.",
        flat=G.norm("Active E1 opportunities remain 5."),
    )
    assert "active e1 opportunities remain 5" in live.flat
    assert not any(marker in live.flat for marker in HISTORICAL_MARKERS), (
        "a bare live restatement must not look classified"
    )
    marked = G.Passage(
        rel=live.rel, heading=live.heading, line=1, kind="paragraph",
        raw="As recorded then, active E1 opportunities remain 5.",
        flat=G.norm("As recorded then, active E1 opportunities remain 5."),
    )
    assert any(marker in marked.flat for marker in HISTORICAL_MARKERS)


def test_the_placeholder_vocabulary_moved_with_the_private_side():
    """M.5, at the registries: the withheld placeholder, never a real hash."""
    for path in (MATRIX_PATH, ACCEPTANCE_MATRIX, LAYER_MATRIX, RULE_MATRIX):
        row = _by_id(path)["PT08"]
        joined = ",".join(v or "" for v in row.values())
        assert "stored_in_private_evaluator_repo" in joined, path.name
        assert "not_yet_authored" not in joined, path.name
    hashes = {
        r["task_id"]: r["hidden_evaluator_manifest_hash"] for r in _rows(MATRIX_PATH)
    }
    for task_id, value in hashes.items():
        assert value in {"stored_in_private_evaluator_repo", "not_yet_authored"}, task_id
        assert not re.fullmatch(r"[0-9a-f]{16,}", value), (
            f"{task_id}: a real manifest hash must never be pinned publicly"
        )


def test_pt08s_public_review_and_package_are_recorded_as_separate_events():
    """M.6: three events, in order, never one collapsed approval."""
    flat = _flat(CAND_A1_PATH)
    assert "the public-authoring review passed first" in flat
    assert "the private evaluator package was authored after it" in flat
    assert "approved on a discharged conditional independent review" in flat
    assert "separately recorded governance admission step" in flat
    assert "no second independent review" not in flat or True  # no claim either way


# --------------------------------------------------------------------------- 3
# M.9 / M.10 — TD-B34 stays open; priority B stays not started.


def test_td_b34_remains_open_and_blocking():
    row = _decision("TD-B34")
    assert row["status"].strip().lower() == "open"
    assert row["blocking"] == "yes"
    assert "td-b34 therefore remains open and blocking" in G.norm(row["decision"])
    assert "open and blocking" in _flat(CLOSURE_PATH)
    assert "resolves no blocker" in _flat(CLOSURE_PATH)


def test_no_governed_document_reports_td_b34_as_closed():
    forbidden = ("td-b34 is resolved", "td-b34 is closed", "td-b34 has been closed",
                 "td-b34 is no longer blocking")
    offenders = []
    for rel in G.governed_files():
        flat = G.norm((REPO / rel).read_text(encoding="utf-8"))
        offenders += [f"{rel}: {claim!r}" for claim in forbidden if claim in flat]
    assert offenders == [], f"TD-B34 is reported closed: {offenders}"


def test_priority_b_remains_not_started():
    """The exact thing that keeps TD-B34 open, asserted at four surfaces."""
    assert "priority b is not started" in G.norm(_decision("TD-B34")["decision"])
    for path in (CLOSURE_PATH, POWER_POLICY_PATH, REPORT_PATH, CAND_A1_PATH):
        flat = _flat(path)
        assert "priority b" in flat, path.name
        assert (
            "not started" in flat or "no candidate review at all" in flat
        ), f"{path.name} does not record priority B as unstarted"
    closure = _flat(CLOSURE_PATH)
    assert "priority-b candidate review: not started" in closure
    assert "starts no priority-b work" in closure
    for overclaim in ("priority b is complete", "priority b is started",
                      "priority-b candidate review: complete"):
        assert overclaim not in closure, f"the closure record over-claims: {overclaim!r}"


def test_the_replication_depth_objective_is_not_reported_as_satisfied():
    row = G.norm(_decision("TD-B34")["decision"])
    assert "the re-scoped replication-depth objective is not satisfied" in row


# --------------------------------------------------------------------------- 4
# M.11 — SL-PT08-01 stays exactly the bounded exception it was.


def test_the_sl_pt08_01_diagnostic_exception_is_intact():
    diagnostic = _flat(DIAGNOSTIC_PATH)
    assert "sl-pt08-01" in diagnostic
    for scope in ("pt08-only", "c1-only", "non-confirmatory"):
        assert scope in diagnostic, f"the diagnostic's {scope!r} scope was weakened"
    policy = _flat(POWER_POLICY_PATH)
    assert "one bounded exception, and only one" in policy
    assert "exactly one such diagnostic is authorised" in policy
    assert "completing it advances no stage" in policy


def test_the_normal_path_and_the_diagnostic_exception_stay_distinguished():
    """The exception must never be describable as Stage 1 or as confirmatory."""
    closure = _flat(CLOSURE_PATH)
    assert "normal path:" in closure and "td-b34 blocks stage 0 and stage 1" in closure
    assert "diagnostic exception:" in closure
    assert "the diagnostic is not stage 1" in closure
    assert "advances no stage" in closure
    assert "analytically quarantined" in closure
    for wrong in ("the diagnostic is stage 1", "the diagnostic is stage 0",
                  "enters the confirmatory dataset",
                  "the diagnostic is confirmatory"):
        assert wrong not in closure, f"the closure record mis-describes it: {wrong!r}"


def test_the_diagnostic_remains_mechanically_no_go_and_closure_discharges_one_item():
    diagnostic = _flat(DIAGNOSTIC_PATH)
    assert "the current mechanical state is no-go" in diagnostic
    assert "the diagnostic cannot run now" in diagnostic
    assert "no runner exists" in diagnostic
    closure = _flat(CLOSURE_PATH)
    assert "discharges exactly one item" in closure
    assert "builds no runner" in closure


# --------------------------------------------------------------------------- 5
# M.12 - M.17 — everything the synchronization did NOT confer.


def test_the_hidden_acceptance_scaffold_remains_draft_unvalidated():
    assert "draft_unvalidated" in _flat(CLOSURE_PATH)
    assert "never been runtime-validated" in _flat(CLOSURE_PATH)
    row = _by_id(ACCEPTANCE_MATRIX)["PT08"]
    joined = G.norm(",".join(v or "" for v in row.values()))
    assert "draft_unvalidated" in joined
    assert row["status"] == "candidate-not-frozen"
    for overclaim in ("hidden acceptance validated", "runtime-validated and approved",
                      "reference pass/fail validated"):
        assert overclaim not in joined, f"the row over-claims: {overclaim!r}"
    assert G.norm(_decision("TD-B32")["status"]) == "open"


def test_pt08_remains_unfrozen():
    assert _by_id(INDEX_PATH)["PT08"]["task_status"] == "candidate"
    assert _by_id(MATRIX_PATH)["PT08"]["task_status"] == "candidate"
    for path in (ACCEPTANCE_MATRIX, LAYER_MATRIX, RULE_MATRIX):
        assert _by_id(path)["PT08"]["status"] == "candidate-not-frozen", path.name
    closure = _flat(CLOSURE_PATH)
    assert "freezes nothing" in closure
    assert "stays status=review" in closure
    assert "pre-freeze" in closure
    for overclaim in ("pt08 is frozen", "pt08 has been frozen", "the manifest is frozen"):
        assert overclaim not in closure, f"the closure record over-claims: {overclaim!r}"


def test_gate_g1_is_not_passed_and_no_gate_is():
    gates = {r["gate_id"]: r["status"].strip().lower() for r in _rows(GATE_MATRIX)}
    assert "not evaluated" in gates["G1"], gates["G1"]
    for gate_id, status in gates.items():
        assert "passed" not in status, f"{gate_id} is marked passed"
    assert "passes no gate" in _flat(CLOSURE_PATH)


def test_pt08_is_not_run_eligible():
    closure = _flat(CLOSURE_PATH)
    assert "makes pt08 no more run-eligible" in closure
    assert "still refuses a non-frozen manifest" in closure
    reason = G.norm(_by_id(MATRIX_PATH)["PT08"]["e1_eligibility_reason"])
    assert "not run-ready" in reason
    assert "not yet enterable into an actual e1 run" in reason


def test_no_result_artifact_exists_anywhere():
    for directory in ("results", "analysis"):
        stray = [
            p.name
            for p in (REPO / "experiments" / "v2" / directory).rglob("*")
            if p.is_file() and p.name != "README.md"
        ]
        assert not stray, f"an artifact appeared in experiments/v2/{directory}: {stray}"
    closure = _flat(CLOSURE_PATH)
    assert "creates no result" in closure
    assert "no treatment-effect estimate" in closure


def test_no_power_value_is_produced_and_td_b37_stays_blocked():
    closure = _flat(CLOSURE_PATH)
    assert "runs no power simulation" in closure
    assert "freezes no power value" in closure
    assert G.norm(_decision("TD-B37")["status"]) == "open"
    assert _decision("TD-B37")["blocking"] == "yes"
    for path in (POWER_POLICY_PATH, SAP_PATH):
        flat = _flat(path)
        assert "no final power value is frozen" in flat, path.name
    # and no numeric power/MDE value was smuggled into the closure record
    assert not re.search(r"\bpower\s*(?:=|of)\s*0?\.\d", closure), (
        "the closure record states a power value"
    )


def test_no_model_and_no_sample_size_are_selected():
    closure = _flat(CLOSURE_PATH)
    assert "selects no model" in closure
    assert "no sample" in closure
    registry = G.norm((DOCS_V2 / "MODEL_REGISTRY.yml").read_text(encoding="utf-8"))
    assert "primary_model: null" in registry, "a primary model was selected"


# --------------------------------------------------------------------------- 6
# M.18 — the historical record is preserved, not rewritten.


def test_the_pre_authoring_record_is_not_rewritten_as_though_pt08_were_active():
    """Part I, stated as an assertion about CAND-A1's own structure."""
    flat = _flat(CAND_A1_PATH)
    # the pre-authoring frame survives
    assert "as originally issued" in flat
    assert "the pre-authoring history above them is preserved rather than rewritten" in flat
    # and each superseded prohibition is individually marked, not deleted
    assert flat.count("as originally recorded") >= 5
    assert flat.count("superseded on this point only") >= 5
    # the current-state appendix is separated from the history it supersedes
    assert "current post-admission state" in flat


@pytest.mark.parametrize(
    "path", [CAND_A1_PATH, FEASIBILITY_PATH, REPORT_PATH, POWER_POLICY_PATH, SAP_PATH],
    ids=lambda p: p.name,
)
def test_each_synchronised_surface_separates_history_from_current_state(path):
    flat = _flat(path)
    assert "as recorded then" in flat, (
        f"{path.name} states superseded facts with no historical framing"
    )


def test_the_closure_record_names_what_it_preserved_as_history():
    flat = _flat(CLOSURE_PATH)
    assert "deliberately preserved as history" in flat
    assert "the withdrawn" in flat and "breadth objective" in flat
    assert "the td-b40 reserve-reconciliation statements" in flat


# --------------------------------------------------------------------------- 7
# M.19 — no model-visible or task-facing architecture leakage was introduced.


ARCHITECTURE_ID = re.compile(
    r"\bAR-[A-Z]+-\d+|\bOPP-|\bDC-[A-Z0-9-]+|features\s*(?:->|→)\s*api",
    re.IGNORECASE,
)


def _clauses(text: str):
    return re.split(r"(?<=[.;:])\s+|\n|\|", text)


def _public_documents():
    skip = {".git", "node_modules", "__pycache__", ".pytest_cache", ".nx", "archive"}
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".csv", ".yml", ".yaml"}:
            continue
        if skip & set(path.relative_to(REPO).parts):
            continue
        yield path


def test_no_public_document_binds_pt08_to_an_architecture_identifier():
    """M.19: `PT08` and a rule / opportunity / cluster id never share one clause.

    This is the repository's existing disclosure convention, widened two ways: it
    covers CSV fields (scoped per field, as the governance passage model does) as
    well as Markdown, and it treats a cluster id and a rendered `features → api`
    edge as disclosing as much as a rule id does.
    """
    offenders = []
    for path in _public_documents():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "PT08" not in text:
            continue
        rel = path.relative_to(REPO).as_posix()
        if path.suffix == ".csv":
            scopes = [
                cell for row in csv.reader(io.StringIO(text)) for cell in row
            ]
        else:
            scopes = [text]
        for scope in scopes:
            for clause in _clauses(scope):
                if "PT08" in clause and ARCHITECTURE_ID.search(clause):
                    offenders.append(f"{rel}: {clause.strip()[:160]}")
    assert offenders == [], (
        "a public document binds PT08 to an architecture identifier in one "
        f"statement:\n  - " + "\n  - ".join(offenders)
    )


def test_that_leakage_sweep_would_catch_a_real_binding():
    """Guard the guard, in both directions."""
    bad = "PT08 creates a features → api decision under AR-DEP-006."
    ok = "PT08 adds the second active observation."
    assert "PT08" in bad and ARCHITECTURE_ID.search(bad)
    assert not ARCHITECTURE_ID.search(ok)


def test_the_task_bodies_are_untouched_by_the_synchronization():
    """The synchronization is documentation-only: no task body may move."""
    import hashlib

    expected = {
        "PT01": "6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39",
        "PT02": "ec4b60057708b20cb95e51f000671aab40afc8c55c0bc75850922a5f65841a77",
        "PT03": "cbfce1ca232cb9b6b53e0b4d202d6acee7415b50af8386c1f3bd2147089b4c21",
        "PT04": "f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5",
        "PT05": "f6efc772e76d6c287e0c71daaa93c7e1d9e62e72a1b37878df70113269ed27b3",
        "PT06": "3e0f84cfef1f9fbf97e3cd31b6704c3a0fb172b04b5e7bc33ea39927b1c8e0f2",
        "PT07": "557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7",
        "PT08": "a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2",
        "PR01": "0e1527bce41498836bb57b802d4566251d6fcfed4cca13fe59e6a97330f02302",
        "PR02": "e89a4aab236813c082f9152db779b8bbfb298148a51a8435a1e2bf38330caa83",
    }
    for task_id, sha in sorted(expected.items()):
        body = (PUBLIC_TASKS / f"{task_id}.md").read_bytes()
        assert hashlib.sha256(body).hexdigest() == sha, f"{task_id} body changed"
    index = _by_id(INDEX_PATH)
    for task_id, sha in sorted(expected.items()):
        assert index[task_id]["public_task_sha256"] == sha, task_id


# --------------------------------------------------------------------------- 8
# M.20 — P2-2 is closed, and closure is bounded.


def test_the_closure_record_exists_and_is_governed():
    assert CLOSURE_PATH.is_file()
    rel = CLOSURE_PATH.relative_to(REPO).as_posix()
    assert rel in G.governed_files(), (
        "the closure record must be inside the globbed governed corpus, so its own "
        "prose is policed by the same backstops as every other governance document"
    )


def test_p2_2_is_recorded_as_closed_with_its_basis():
    flat = _flat(CLOSURE_PATH)
    assert "pt08-pub-p2-2 is closed" in flat
    assert "closure basis" in flat
    assert "reconciled to the admitted state" in flat
    assert "preserved under an explicit historical framing" in flat
    # the closure record carries the admitted accounting itself
    assert f"active `e1` opportunities | {ACTIVE_OPPORTUNITIES}".replace("`", "") in flat
    assert f"active decision clusters | {ACTIVE_CLUSTERS}" in flat
    assert f"cluster observation depths | {DEPTHS_RENDERED}" in flat
    for task_id in ACTIVE_SCORED:
        assert task_id.lower() in flat, f"{task_id} is missing from the active set"


def test_closure_states_what_it_does_not_imply_before_anything_else():
    """The denials must be quotable with the closure, not separable from it."""
    flat = _flat(CLOSURE_PATH)
    assert "what closure does not imply" in flat
    assert "stated first so it cannot be quoted without it" in flat
    for denial in ("freezes nothing", "passes no gate", "validates no hidden acceptance",
                   "creates no result", "runs no power simulation", "selects no model",
                   "resolves no blocker", "starts no priority-b work",
                   "activates no reserve", "builds no runner"):
        assert denial in flat, f"the closure record omits the denial {denial!r}"
    assert "an instrument count" in flat
    assert "never a violation, a success, an outcome or a result" in flat


def test_the_closure_record_states_no_commit_it_cannot_know():
    """A self-referential commit SHA cannot be known before the commit exists."""
    flat = _text(CLOSURE_PATH)
    assert not re.search(r"\b[0-9a-f]{40}\b", flat), (
        "the closure record pins a 40-hex commit; a synchronization commit's own "
        "SHA is unknowable before it is created and must not be invented"
    )


def test_the_closure_record_records_the_private_side_as_untouched():
    flat = _flat(CLOSURE_PATH)
    assert "no private byte was modified by this package" in flat
    assert "inspected read-only" in flat
    assert "outside the private linkage pin set" in flat
    assert "no re-link is required" in flat
    assert "the reviewed public evaluation baseline is not advanced" in flat
