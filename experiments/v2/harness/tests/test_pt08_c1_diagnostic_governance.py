"""Governance guards for `SL-PT08-01`, the pre-Stage-0 `PT08` `C1` diagnostic.

WHAT THIS MODULE GUARDS
-----------------------
The repository had a closed loop: ``SL-CA1-02`` allows ``PT08``'s discriminative
difficulty to be judged only on baseline ``C1`` evidence, the only vehicle it
named for that evidence was the Stage-1 pilot, Stage 1 follows Stage 0, and
Stage 0 is gated on ``TD-B34`` — so the instrument's own difficulty could not be
checked until after the expansion that check was meant to inform. The Study Lead
adjudicated it in ``SL-PT08-01``. This module makes that adjudication, and every
bound on it, load-bearing:

* the decision exists, is ``PT08``-only, ``C1``-only, **non-confirmatory**, and
  sits **outside** the Stage 0 -> Stage 1 -> core-grid sequence;
* ``TD-B34`` stays open and still blocks Stage 0, and the exception reaches this
  one diagnostic and nothing else;
* the diagnostic's observations are analytically quarantined — no confirmatory
  dataset, no confirmatory ``E1`` estimation, no treatment-effect analysis, no
  power estimation — and ``C4`` may still never inform ``PT08``'s difficulty;
* the narrow ``TD-B12``/``G6`` exception is scoped to this diagnostic alone, is
  evidenced by ``PT08``'s own reviewed task-specific corpus, and discharges
  neither the blocker nor the gate;
* everything that is **not** waived stays required — a real runner, governed
  isolation, model selection, hidden-acceptance validation and its independent
  review, ``PT08``'s freeze, and the public ``PT08-PUB-P2-2`` synchronization
  that must precede that freeze.

AND IN THE OTHER DIRECTION
--------------------------
Recording a decision is not performing one. Nothing here asserts that the
diagnostic can run, that a runner exists, that isolation is clean, that hidden
acceptance is validated, that ``PT08`` is frozen, that ``G1`` is passed, that
``TD-B34`` is closed, that priority B is complete, that a model or a sample size
is chosen, or that any result exists. The active accounting is untouched: this
package performs **no** public accounting synchronization, and the record must
not smuggle one in.

Pure file inspection. No model is invoked, no benchmark runs, nothing is frozen
and no power value is produced.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

import governance_text as G

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"

RECORD_PATH = DOCS_V2 / "PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md"
CAND_A1_PATH = DOCS_V2 / "CAND_A1_PREAUTHORING_DECISION.md"
POLICY_PATH = DOCS_V2 / "PILOT_AND_POWER_POLICY.md"
FEASIBILITY_PATH = DOCS_V2 / "DEPENDENCY_TASK_FEASIBILITY.md"
DECISIONS_CSV = DOCS_V2 / "OPEN_DECISIONS.csv"
GATE_MATRIX = DOCS_V2 / "PILOT_GATE_MATRIX.csv"
MODEL_REGISTRY = DOCS_V2 / "MODEL_REGISTRY.yml"

#: The decision identifier, in the repository's existing `SL-<subject>-<nn>`
#: Study-Lead convention. Pinned here so a rename is a deliberate act.
DECISION_ID = "sl-pt08-01"

#: Section headings of the record, keyed by the short name used below. Assertions
#: are scoped to a heading's own subtree — never to a character window.
S_DECISION = "2. sl-pt08-01 — the authoritative decision"
S_PLACE = "3. where the diagnostic sits"
S_CLARIFY = "4. sl-ca1-02 is clarified"
S_TDB34 = "5. td-b34 — the exception boundary"
S_G6 = "6. td-b12 / g6 — the narrow diagnostic exception"
S_NOT_WAIVED = "7. requirements that are not waived"
S_NOT_NEEDED = "8. requirements that are not prerequisites"
S_FIREWALL = "9. the diagnostic data firewall"
S_EVIDENCE = "10. permitted and prohibited diagnostic evidence"
S_PENDING = "11. sample size, model selection, and accounting"
S_PROHIBITIONS = "12. prohibitions attaching to this record"

_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")


# --------------------------------------------------------------------------- #
# Passage helpers — heading-scoped and row-scoped, never window-scoped.
# --------------------------------------------------------------------------- #
def _rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def _passages(path: Path):
    return G.markdown_passages(path, _rel(path))


def _region_lines(path: Path, heading_prefix: str) -> tuple[int, int]:
    """1-based ``[start, end)`` line range of a heading and its whole subtree."""
    lines = path.read_text(encoding="utf-8").split("\n")
    start = level = None
    for i, line in enumerate(lines, 1):
        head = _HEADING_RE.match(line)
        if not head:
            continue
        if start is None:
            if G.norm(head.group(2)).startswith(heading_prefix.lower()):
                start, level = i, len(head.group(1))
            continue
        if len(head.group(1)) <= level:
            return start, i
    assert start is not None, f"{path.name}: no heading starting with {heading_prefix!r}"
    return start, len(lines) + 2


def _section(path: Path, heading_prefix: str) -> str:
    """Normalised text of every passage inside one heading's subtree."""
    start, end = _region_lines(path, heading_prefix)
    hits = [p.flat for p in _passages(path) if start <= p.line < end]
    assert hits, f"{path.name}: section {heading_prefix!r} is empty"
    return " || ".join(hits)


def _row_by_first_cell(path: Path, heading_prefix: str, first_cell: str) -> list[str]:
    """Cells of the one table row in a subtree whose FIRST cell is ``first_cell``."""
    start, end = _region_lines(path, heading_prefix)
    rows = []
    for p in _passages(path):
        if p.kind != "table-row" or not (start <= p.line < end):
            continue
        cells = [c.strip() for c in p.flat.strip("|").split("|")]
        if cells and cells[0] == first_cell.lower():
            rows.append(cells)
    assert len(rows) == 1, (
        f"{path.name}: expected exactly one row under {heading_prefix!r} whose first "
        f"cell is {first_cell!r}, found {len(rows)}"
    )
    return rows[0]


def _flat(path: Path) -> str:
    return G.norm(path.read_text(encoding="utf-8"))


def _decision(decision_id: str) -> dict:
    with open(DECISIONS_CSV, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["decision_id"] == decision_id:
                return row
    raise AssertionError(f"{decision_id} is not in the registry")


def _gate(gate_id: str) -> dict:
    with open(GATE_MATRIX, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["gate_id"] == gate_id:
                return row
    raise AssertionError(f"{gate_id} is not in the gate matrix")


def _authoritative_decision() -> str:
    """The single blockquote passage carrying the adjudication verbatim."""
    return G.find_passage(_rel(RECORD_PATH), f"{DECISION_ID}. one pre-registered").flat


# --------------------------------------------------------------------------- 1
# M.1 — the decision exists, is governed, and is identified consistently.


def test_the_decision_record_exists_and_is_inside_the_governed_document_set():
    """A record outside the governed globs would escape every text backstop."""
    assert RECORD_PATH.is_file(), "the SL-PT08-01 decision record is missing"
    assert _rel(RECORD_PATH) in G.governed_files(), (
        "the diagnostic decision record is not picked up by the governed-document "
        "globs, so the repository-wide backstops cannot see it"
    )


def test_the_decision_id_follows_the_existing_study_lead_convention():
    """`SL-<subject>-<nn>`, the convention `SL-CA1-01`/`SL-CA1-02` already set."""
    flat = _flat(RECORD_PATH)
    assert DECISION_ID in flat
    assert "sl-<subject>-<nn>" in flat, (
        "the record must state the convention its identifier follows"
    )
    for prior in ("sl-ca1-01", "sl-ca1-02"):
        assert prior in flat, f"the record must cite the prior convention holder {prior!r}"
    # and the identifier is cross-referenced from the records it clarifies
    assert DECISION_ID in _flat(CAND_A1_PATH)
    assert DECISION_ID in _flat(POLICY_PATH)


# --------------------------------------------------------------------------- 2
# M.2 / M.3 / M.4 — PT08-only, C1-only, non-confirmatory.


def test_the_diagnostic_is_pt08_only_c1_only_and_non_confirmatory():
    """The three scope words live in the authoritative passage's own text."""
    decision = _authoritative_decision()
    assert "pt08-only, c1-only, non-confirmatory difficulty diagnostic" in decision, (
        "the adjudication no longer states its own scope"
    )
    scope = _section(RECORD_PATH, S_DECISION)
    assert (
        "the authorisation is for one instrument (pt08), one condition (c1), and "
        "one purpose (instrument difficulty)" in scope
    )
    assert "it extends to no other task, no other condition, and no other question" in scope


@pytest.mark.parametrize(
    "widening",
    ["c1 and c4", "c1/c4", "c1 or c4", "all conditions", "every scored task"],
)
def test_the_authoritative_decision_carries_no_widened_scope(widening):
    """Mutation guard: the scope may not be broadened inside its own passage."""
    assert widening not in _authoritative_decision(), (
        f"the adjudication has been widened to {widening!r}"
    )


def test_the_diagnostic_is_never_described_as_confirmatory():
    section = _section(RECORD_PATH, S_DECISION)
    assert "non-confirmatory" in section
    for claim in ("is confirmatory", "confirmatory diagnostic",
                  "confirmatory_eligible: true"):
        assert claim not in section, f"the diagnostic is described as {claim!r}"


# --------------------------------------------------------------------------- 3
# M.5 — pre-Stage-0, outside the normal staged sequence.


def test_the_diagnostic_is_pre_stage_0_and_outside_the_staged_sequence():
    place = _section(RECORD_PATH, S_PLACE)
    assert "outside that sequence" in place
    assert "deliberately not called stage 1" in place, (
        "the record must say why it is not named Stage 1"
    )
    assert "pre-stage-0 pt08 c1 difficulty diagnostic" in place, (
        "the diagnostic must carry its own governed name"
    )
    assert "completing it advances no stage" in place
    assert "it is a pre-confirmatory instrument-difficulty diagnostic only" in place


def test_the_stage_table_separates_it_from_stage_0_and_stage_1():
    """Row-scoped: each stage's own cells, so none can borrow another's answer."""
    conditions = _row_by_first_cell(RECORD_PATH, S_PLACE, "conditions")
    assert conditions[1] == "none scored"          # Stage 0
    assert conditions[2] == "c1, c3, c4"           # Stage 1 screening pilot
    assert conditions[3] == "c1 only"              # this diagnostic
    tasks = _row_by_first_cell(RECORD_PATH, S_PLACE, "tasks")
    assert tasks[3] == "pt08 only"
    gated = _row_by_first_cell(RECORD_PATH, S_PLACE, "gated on td-b34")
    assert gated[1] == "yes" and gated[2] == "yes"
    assert gated[3].startswith("no — the one bounded exception")


def test_the_pilot_policy_places_the_diagnostic_outside_the_sequence_too():
    policy = _flat(POLICY_PATH)
    assert "pre-stage-0 instrument diagnostics (outside the staged sequence)" in policy
    assert "exactly one such diagnostic is authorised" in policy
    assert "completing it advances no stage" in policy
    # the staged sequence itself is unchanged
    assert "stage 0 — non-evidentiary technical dry runs" in policy
    assert "stage 1 — screening pilot" in policy


# --------------------------------------------------------------------------- 4
# M.6 / M.7 / M.8 / M.9 — TD-B34: open, still blocking, narrowly excepted.


def test_td_b34_remains_open_and_blocking_in_the_registry():
    row = _decision("TD-B34")
    assert row["status"].strip().lower() == "open", (
        "authorising a non-confirmatory diagnostic does not resolve TD-B34"
    )
    assert row["blocking"] == "yes"


def test_td_b34_still_gates_stage_0():
    policy = _flat(POLICY_PATH)
    assert "stage 0 is additionally gated on decision b" in policy
    assert "td-b34 remains open and blocking before stage 0" in policy
    boundary = _section(RECORD_PATH, S_TDB34)
    for blocked in ("stage 0", "normal stage 1", "final pilot progression",
                    "confirmatory execution"):
        assert blocked in boundary, f"TD-B34 must still be recorded as blocking {blocked!r}"
    assert "the power simulation, where applicable" in boundary


def test_td_b34_does_not_block_this_one_diagnostic():
    boundary = _section(RECORD_PATH, S_TDB34)
    assert (
        "td-b34 does not block this one specifically authorised non-confirmatory "
        "pt08 difficulty diagnostic" in boundary
    )
    policy = _flat(POLICY_PATH)
    assert "one bounded exception, and only one" in policy


def test_the_td_b34_exception_discharges_and_changes_nothing_else():
    boundary = _section(RECORD_PATH, S_TDB34)
    for denial in (
        "does not mark priority b complete",
        "does not weaken td-b34's final closure conditions in any respect",
        "does not count the diagnostic as a replication observation",
        "does not change any decision-cluster observation depth",
        "does not create an additional active opportunity",
        "closes no td-b34 subcondition — none",
        "is not precedent for any second exception",
    ):
        assert denial in boundary, f"the exception boundary no longer denies: {denial!r}"


def test_priority_b_is_not_started_and_stays_required_on_the_normal_path():
    registry = _decision("TD-B34")["decision"].lower()
    assert "priority b (dc-api-core-ar-dep-005) has had no candidate review at all" in registry
    not_needed = _section(RECORD_PATH, S_NOT_NEEDED)
    assert "priority-b candidate authoring or review" in not_needed
    assert "unstarted where it was unstarted" in not_needed
    prohibitions = _section(RECORD_PATH, S_PROHIBITIONS)
    assert "priority b is not complete and is not started" in prohibitions


# --------------------------------------------------------------------------- 5
# M.10 / M.11 / M.12 — the analytic quarantine.


@pytest.mark.parametrize(
    "field",
    ["confirmatory_eligible", "enters_confirmatory_dataset",
     "enters_confirmatory_e1_analysis", "enters_treatment_effect_analysis",
     "enters_power_estimation"],
)
def test_every_quarantine_flag_is_required_to_be_false(field):
    """Row-scoped, so no flag can be read off a neighbouring row."""
    cells = _row_by_first_cell(RECORD_PATH, S_FIREWALL, field)
    assert cells[1] == "false", f"{field} is no longer required to be false: {cells[1]!r}"


def test_the_run_purpose_marker_is_pinned():
    cells = _row_by_first_cell(RECORD_PATH, S_FIREWALL, "run_purpose")
    assert cells[1] == "pt08_difficulty_diagnostic"


def test_the_authoritative_decision_bars_every_confirmatory_use():
    decision = _authoritative_decision()
    for barred in (
        "enter the confirmatory dataset",
        "enter confirmatory e1 effect estimation",
        "be pooled with the later stage-1 or core-grid observations",
        "be reported as a c1-versus-c4 treatment effect",
        "be used to estimate afci benefit",
        "be used for confirmatory interaction estimates",
        "discharge td-b34",
        "discharge priority b",
        "pass stage 0",
        "pass g1",
        "discharge the global power-analysis gates",
    ):
        assert barred in decision, f"the adjudication no longer bars: {barred!r}"


def test_the_firewall_invents_no_schema_and_fails_closed_in_the_future_runner():
    firewall = _section(RECORD_PATH, S_FIREWALL)
    assert "no result schema and no runner artifact is invented here" in firewall
    assert "mandatory future runner requirements" in firewall
    assert "the future runner must fail closed" in firewall
    assert "an unmarked artifact is an error, never a confirmatory observation" in firewall
    # and no speculative runtime artifact was actually created
    for directory in ("results", "analysis"):
        stray = [
            p.name
            for p in (REPO / "experiments" / "v2" / directory).rglob("*")
            if p.is_file() and p.name != "README.md"
        ]
        assert not stray, f"an artifact appeared in experiments/v2/{directory}: {stray}"


# --------------------------------------------------------------------------- 6
# M.13 — C4 may still never inform PT08's difficulty.


def test_c4_and_treatment_effects_may_never_inform_pt08_difficulty():
    evidence = _section(RECORD_PATH, S_EVIDENCE)
    assert "not permitted, in any form:" in evidence, (
        "the prohibited-use list must still be introduced as a prohibition; a "
        "relabelled list of the same items would permit exactly what it forbids"
    )
    for prohibited in ("comparison against c4", "any afci effect", "any condition contrast",
                       "any treatment-effect estimate", "any interaction estimate",
                       "selecting or shaping requirements because they maximise an "
                       "afci advantage"):
        assert prohibited in evidence, f"the prohibited-use list lost: {prohibited!r}"
    clarify = _section(RECORD_PATH, S_CLARIFY)
    assert "c4 and treatment-effect results may never tune pt08" in clarify
    # SL-CA1-02's own record keeps the rule, unedited
    cand = _flat(CAND_A1_PATH)
    assert (
        "the task must never be tuned based on c4 or on any treatment-effect result"
        in cand
    )


def test_the_permitted_evidence_list_is_exactly_the_pre_registered_one():
    evidence = _section(RECORD_PATH, S_EVIDENCE)
    assert "the study lead may inspect, and only these:" in evidence, (
        "the permitted list must stay closed; an open list is not pre-registration"
    )
    for permitted in ("functional completion rate", "pt08 hidden-acceptance pass/fail",
                      "pt08 applicable opportunity count",
                      "pt08 violated opportunity count",
                      "pt08 architecture-violation proportion under c1",
                      "floor/ceiling behaviour", "qualitative failure modes"):
        assert permitted in evidence, f"the permitted-evidence list lost: {permitted!r}"
    assert "unusably easy, unusably hard, or structurally non-discriminating" in evidence
    assert "stay exploratory and non-confirmatory" in evidence
    assert "normal author, review, hash and re-link process" in evidence


# --------------------------------------------------------------------------- 7
# M.14 / M.15 / M.16 — the narrow G6 / TD-B12 exception.


def test_td_b12_stays_open_and_g6_stays_unevaluated():
    row = _decision("TD-B12")
    assert row["status"].strip().lower() == "open"
    assert row["blocking"] == "yes"
    assert row["gate"].strip() == "G6"
    g6 = _gate("G6")
    assert "passed" not in g6["status"].strip().lower(), g6["status"]
    assert "not evaluated" in g6["status"].strip().lower()


def test_the_g6_exception_is_scoped_to_this_diagnostic_alone():
    section = _section(RECORD_PATH, S_G6)
    assert (
        "for this pt08-only non-confirmatory diagnostic only, completion of the "
        "global td-b12 / g6 precision-and-recall bar is not required before the "
        "diagnostic" in section
    )
    for denial in (
        "it does not discharge td-b12, which stays open and blocking",
        "it does not pass g6, which stays open and blocking",
        "it does not permit confirmatory scoring before g6",
        "remain mandatory at their existing final-study gate",
        "task-specific evidence about one instrument is not global guard validation",
    ):
        assert denial in section, f"the G6 exception no longer denies: {denial!r}"


def test_the_g6_exception_rests_on_pt08s_own_reviewed_corpus():
    section = _section(RECORD_PATH, S_G6)
    assert "evidence basis, recorded exactly as supplied" in section
    assert "task-specific architecture corpus" in section
    assert "full corpus: 11 of 11 cases resolve as expected" in section
    assert "no case resolves not_applicable" in section
    for label, violated in (
        ("a conforming implementation", "0"),
        ("the pre-declared boundary-only family alt-c", "0"),
        ("a direct forbidden-direction edge", "1"),
        ("a forbidden-direction edge in a newly created source file", "1"),
    ):
        cells = _row_by_first_cell(RECORD_PATH, S_G6, label)
        assert cells[1] == "1", f"{label}: applicable must be 1, got {cells[1]!r}"
        assert cells[2] == violated, f"{label}: violated must be {violated}, got {cells[2]!r}"


# --------------------------------------------------------------------------- 8
# M.17 - M.22 — nothing mechanical is waived.


@pytest.mark.parametrize(
    "requirement",
    [
        "a real runner / execution harness — none exists in this repository today",
        "runner-time worktree enforcement",
        "a fresh process/session",
        "a clean context audit, failing closed on contaminated",
        "an isolated container / vm as governed",
        "a dedicated, uncontaminated identity as governed",
        "absence of managed / account-tied policy contamination",
        "primary-model selection by the study lead",
        "exact model-id input with runtime readback validation",
        "invalid-model-id rejection",
        "pt08 hidden functional acceptance fixture authoring",
        "pt08 reference-pass / reference-fail / mutation validation",
        "the required independent review of that hidden-acceptance validation",
        "pt08's required manifest freeze under the existing lifecycle rules",
        "public pt08-pub-p2-2 synchronization before that freeze",
        "pt08 public/private hash and linkage consistency",
        "no signed non-finite hidden semantic cases while public p2-1 remains open",
        "no out-of-scope numeric hidden cases",
        "no persistence assertion",
        "the existing observation-isolation requirements, in full",
    ],
)
def test_each_unwaived_requirement_is_still_recorded(requirement):
    """Twenty separate prerequisites, each asserted on its own."""
    assert requirement in _section(RECORD_PATH, S_NOT_WAIVED), (
        f"a prerequisite of the diagnostic was dropped: {requirement!r}"
    )


def test_recording_the_decision_confers_no_readiness():
    section = _section(RECORD_PATH, S_NOT_WAIVED)
    assert "recording this decision does not make the diagnostic executable" in section
    assert "the current mechanical state is no-go" in section
    assert "nothing above is relaxed by this record, and this record confers no readiness" in section
    prohibitions = _section(RECORD_PATH, S_PROHIBITIONS)
    assert "the diagnostic cannot run now" in prohibitions
    assert "no runner exists" in prohibitions
    assert "isolation is not asserted to be clean" in prohibitions
    assert "pt08 hidden acceptance is not validated" in prohibitions
    assert "pt08 is not frozen" in prohibitions
    assert "gate g1 is not passed" in prohibitions


def test_no_runner_has_appeared_in_the_public_repository():
    """The prerequisite is a fact about the tree, not only about the prose."""
    harness = REPO / "experiments" / "v2" / "harness"
    present = sorted(p.name for p in harness.glob("*.py"))
    assert present == [
        "context_audit.py",
        "evaluator_mount.py",
        "governance_text.py",
        "prepare_model_worktree.py",
        "substrate_identity.py",
    ], f"the harness gained or lost a module; a runner may have appeared: {present}"


# --------------------------------------------------------------------------- 9
# M.23 — what is genuinely not needed, with no status changed.


@pytest.mark.parametrize(
    "not_needed",
    [
        "priority-b candidate authoring or review",
        "td-b34 closure",
        "migration of the eight legacy td-b39 packages",
        "pt03 repair",
        "pr02 activation",
        "c2 token-matching work",
        "c3 execution",
        "c4 execution",
        "treatment-effect analysis",
        "the global power simulation (td-b37)",
        "the small-cluster power work (td-b41)",
        "the final task-count decision (td-b14)",
        "the final core-grid repetition count (td-b10)",
        "the final confirmatory gates g3, g4, g5, g7 and g8",
    ],
)
def test_each_non_prerequisite_is_listed_without_changing_its_status(not_needed):
    assert not_needed in _section(RECORD_PATH, S_NOT_NEEDED), (
        f"the non-prerequisite list lost: {not_needed!r}"
    )


@pytest.mark.parametrize("decision_id", ["TD-B34", "TD-B39", "TD-B37", "TD-B41",
                                         "TD-B12", "TD-B05", "TD-B14", "TD-B22",
                                         "TD-B19", "TD-B21", "TD-B03"])
def test_no_blocker_this_record_mentions_was_quietly_resolved(decision_id):
    assert _decision(decision_id)["status"].strip().lower() == "open", (
        f"{decision_id} must stay open; this record resolves nothing"
    )


def test_no_gate_is_marked_passed():
    with open(GATE_MATRIX, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            assert "passed" not in row["status"].strip().lower(), row["gate_id"]


# --------------------------------------------------------------------------- 10
# M.24 / M.25 — no accounting moved, and none was synchronised here.


def test_the_public_active_accounting_statements_are_untouched():
    """The public counts stand exactly as they stood; this package moves none.

    Counted, not merely located: `CAND-A1` states the active accounting twice —
    in §2a and again in §7 — and changing one of the two would leave the other
    to satisfy a presence-only check while the record itself contradicted
    itself.
    """
    record = _flat(CAND_A1_PATH)
    for statement, occurrences in (
        ("active e1 opportunities remain 5", 2),
        ("decision clusters remain 3", 2),
        ("cluster observation depths remain 3 / 1 / 1", 2),
    ):
        assert record.count(statement) == occurrences, (
            f"the public accounting statement {statement!r} now appears "
            f"{record.count(statement)} times, not {occurrences}"
        )
    feasibility = _flat(FEASIBILITY_PATH)
    assert "active e1 opportunities: 5" in feasibility
    assert "decision clusters: 3" in feasibility


@pytest.mark.parametrize(
    "accounting",
    ["6 opportunities", "7 opportunities", "3 / 2 / 1", "3/2/1",
     "adds one active observation", "active e1 opportunities remain 6"],
)
def test_the_diagnostic_record_performs_no_accounting_synchronization(accounting):
    """PT08-PUB-P2-2 is a separate package; this record must not pre-empt it."""
    assert accounting not in _flat(RECORD_PATH), (
        f"the diagnostic record performs accounting synchronization ({accounting!r}), "
        "which belongs to PT08-PUB-P2-2 and is not part of this package"
    )


def test_the_record_says_the_public_synchronization_is_still_required():
    section = _section(RECORD_PATH, S_PENDING)
    assert "no accounting synchronization is performed here" in section
    assert (
        "pt08-pub-p2-2 remains required and is not performed in this package" in section
    )
    assert "it must precede pt08's freeze" in section


# --------------------------------------------------------------------------- 11
# M.26 / M.27 / M.28 — no model, no result, no sample size.


def test_no_benchmark_result_or_power_value_exists():
    prohibitions = _section(RECORD_PATH, S_PROHIBITIONS)
    assert "no experiment has been run and no result exists" in prohibitions
    assert "no power simulation was run and no power value is produced" in prohibitions
    assert "the protocol remains pre-freeze" in prohibitions
    for directory in ("results", "analysis"):
        stray = [
            p.name
            for p in (REPO / "experiments" / "v2" / directory).rglob("*")
            if p.is_file() and p.name != "README.md"
        ]
        assert not stray, f"an artifact appeared in experiments/v2/{directory}: {stray}"


def test_the_diagnostic_sample_size_remains_undecided():
    section = _section(RECORD_PATH, S_PENDING)
    assert "sample size: study-lead decision pending" in section
    assert (
        "there is no governed sample size for a pt08-only c1 diagnostic" in section
    )
    assert "this record pins none" in section
    assert "not blocked on that later choice" in section


@pytest.mark.parametrize("pin", [r"n\s*=\s*\d+", r"\b\d+\s+diagnostic runs\b",
                                 r"\bdiagnostic sample size of \d+"])
def test_no_diagnostic_sample_size_is_silently_pinned(pin):
    hits = re.findall(pin, _flat(RECORD_PATH))
    assert not hits, f"a diagnostic sample size was pinned: {hits}"


def test_the_primary_model_is_still_null_and_selection_is_a_separate_decision():
    registry = MODEL_REGISTRY.read_text(encoding="utf-8")
    assert re.search(r"(?m)^primary_model:\s*null\b", registry), (
        "a primary model has been selected; TD-B03 governs that decision"
    )
    assert _decision("TD-B03")["status"].strip().lower() == "open"
    section = _section(RECORD_PATH, S_PENDING)
    assert "model selection: a separate study-lead decision, taken before execution" in section
    assert "primary_model stays null and td-b03 stays open" in section
    assert "no model is selected here" in section
    assert "independent of any desired afci effect size" in section


# --------------------------------------------------------------------------- 12
# The clarification preserves SL-CA1-02 rather than erasing it.


def test_sl_ca1_02_is_clarified_and_its_original_wording_survives_verbatim():
    cand = _flat(CAND_A1_PATH)
    # the original Stage-1 sentence is still there, word for word
    assert (
        "discriminative difficulty must be evaluated only through the pre-registered "
        "stage-1 baseline-only c1 pilot" in cand
    )
    clarification = _section(CAND_A1_PATH, "4. sl-ca1-02")
    assert "nothing above is edited, withdrawn or rewritten" in clarification
    assert "as recorded then" in clarification, (
        "the repository's own provenance convention must mark what is history"
    )
    assert "clarified on this point only, and on no other" in clarification
    assert "additional authorised vehicle" in clarification
    assert "changes the vehicle, never the evidence class" in clarification
    # and the clarification claims nothing beyond itself
    assert (
        "sl-pt08-01 resolves no other question: td-b34 stays open and blocking on "
        "the normal path" in clarification
    )


def test_the_record_states_the_circularity_it_resolves():
    section = _section(RECORD_PATH, "1. the circularity this record resolves")
    assert "study-lead adjudication question" in section
    assert "not something derivable from the existing text" in section
    assert "sits after stage 0" in section
