"""Public governance guards for the `CAND-A1` pre-authoring decision record.

WHAT THIS MODULE GUARDS
-----------------------
The independent Priority-A pre-authoring review of `CAND-A1` returned **DECISION
B — REPAIR CANDIDATE BEFORE AUTHORING**, with **P0 = 0** and four P1 findings.
This module makes the repaired state load-bearing in the *public* record:

* the carrier is a **publicly specified query parameter** named ``maxTotal`` and
  is **not** a new request header (``SL-CA1-01``, closes ``P1-1``);
* the forcing class is **natural-path / opportunity-creating**, accepted as a
  construct-validity limitation, with difficulty evaluated only on the
  pre-registered **Stage-1 baseline-only C1** pilot and **no** `C4`/effect-based
  tuning (``SL-CA1-02``, closes ``P1-2``);
* ``features -> infra`` and ``features -> api`` carry **different forcing
  strength** even though both are task-creatable (closes ``P1-3``);
* the ``P-3`` .. ``P-6`` contract decisions are pinned *before* any prose exists;
* ``ALT-C`` and ``ALT-K`` are **pre-declared legal** alternatives;
* the ``TD-B40(B)`` independent re-approval is recorded, and ``TD-B40``'s closure
  is bounded (closes ``P1-4``).

AND IN THE OTHER DIRECTION
--------------------------
`CAND-A1` must stay a candidate: **no** ``PT08`` identifier anywhere, **no**
authored body, **no** eligibility row, **no** denominator row, **no** change to
the active counts (**5** opportunities over **3** clusters at depths **3 / 1 /
1**), and ``DC-FEATURES-API-AR-DEP-006`` still at **one** observation. Nothing is
frozen and no gate is passed.

HOW IT ASSERTS
--------------
Section-scoped, row-scoped and table-cell-scoped through
:mod:`governance_text`'s passage model. There is **no** fixed-width character
window anywhere in this module: a claim is located by the heading it lives under
and, for tables, by its own row's cells. That is the same repair the independent
mutation review forced on the replication-depth guards.

Pure file inspection. No model is invoked, nothing is frozen, and no benchmark or
power value is produced.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

import governance_text as G

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"
PUBLIC_TASKS = REPO / "experiments" / "v2" / "tasks" / "public"

RECORD_PATH = DOCS_V2 / "CAND_A1_PREAUTHORING_DECISION.md"
FEASIBILITY_PATH = DOCS_V2 / "DEPENDENCY_TASK_FEASIBILITY.md"
POLICY_PATH = DOCS_V2 / "TASK_AUTHORING_POLICY.md"
DECISIONS_CSV = DOCS_V2 / "OPEN_DECISIONS.csv"
DECISIONS_MD = DOCS_V2 / "OPEN_DECISIONS.md"
TASK_INDEX = PUBLIC_TASKS / "TASK_INDEX.csv"

FEATURES_INFRA = "DC-FEATURES-INFRA-AR-DEP-006"
FEATURES_API = "DC-FEATURES-API-AR-DEP-006"
API_CORE = "DC-API-CORE-AR-DEP-005"

#: The active cluster occupancy this package must not move.
CLUSTER_DEPTHS = {FEATURES_INFRA: 3, FEATURES_API: 1, API_CORE: 1}
ACTIVE_OPPORTUNITIES = 5
ACTIVE_CLUSTERS = 3

#: The `P-4` subsection heading, used to scope every wire-determinacy assertion to
#: that pin's own tables rather than to the whole pins section.
WIRE_SECTION = "p-4 — query parameter and wire determinacy"


# --------------------------------------------------------------------------- #
# Passage helpers — heading-scoped, never window-scoped.
# --------------------------------------------------------------------------- #
def _rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def _passages(path: Path):
    return G.markdown_passages(path, _rel(path))


_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")


def _region_lines(path: Path, heading_prefix: str) -> tuple[int, int]:
    """1-based ``[start, end)`` line range of a heading and everything beneath it.

    "Beneath it" means up to the next heading of the SAME OR HIGHER level, so a
    section's own subsections are included and its siblings are not. This is a
    structural region, not a character window: nothing outside the heading's own
    subtree can satisfy an assertion scoped to it.
    """
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
    """Normalised text of every passage inside one heading's subtree.

    The join is an explicit delimiter, not whitespace, so a phrase can never be
    assembled by accident across two unrelated passages.
    """
    start, end = _region_lines(path, heading_prefix)
    hits = [p.flat for p in _passages(path) if start <= p.line < end]
    assert hits, f"{path.name}: section {heading_prefix!r} is empty"
    return " || ".join(hits)


def _row_cells(path: Path, heading_prefix: str, key: str) -> list[str]:
    """Cells of the single table row inside ``heading_prefix``'s subtree naming ``key``."""
    start, end = _region_lines(path, heading_prefix)
    rows = [
        p for p in _passages(path)
        if p.kind == "table-row" and start <= p.line < end and key.lower() in p.flat
    ]
    assert len(rows) == 1, (
        f"{path.name}: expected exactly one row under {heading_prefix!r} naming "
        f"{key!r}, found {len(rows)}"
    )
    return [c.strip() for c in rows[0].flat.strip("|").split("|")]


def _row_by_first_cell(path: Path, heading_prefix: str, first_cell: str) -> list[str]:
    """Cells of the one table row inside a subtree whose FIRST cell is ``first_cell``.

    Keying on the row's own label rather than on "contains this word" is what
    stops a case borrowing a neighbour's outcome: ``EMPTY``'s note mentions the
    word "absent", and ``ABSENT``'s outcome must not be readable from it.
    """
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


def _decision(decision_id: str) -> dict:
    with open(DECISIONS_CSV, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["decision_id"] == decision_id:
                return row
    raise AssertionError(f"{decision_id} is not in the registry")


def _flat(path: Path) -> str:
    return G.norm(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# The record exists and is governed.
# --------------------------------------------------------------------------- #
def test_the_record_exists_and_is_inside_the_governed_document_set():
    """A record outside the governed globs would escape every backstop."""
    assert RECORD_PATH.is_file(), "the CAND-A1 pre-authoring record is missing"
    assert _rel(RECORD_PATH) in G.governed_files(), (
        "the CAND-A1 record is not picked up by the governed-document globs, so the "
        "breadth and fourth-cluster backstops cannot see it"
    )


def test_the_record_declares_that_it_authorises_nothing():
    preamble = _section(RECORD_PATH, "docs/v2 — cand-a1 pre-authoring")
    for claim in ("authors no public task body",
                  "creates no private evaluator package",
                  "creates no manifest",
                  "assigns no pt08 identifier",
                  "creates no architecture opportunity",
                  "enters no e1 denominator",
                  "activates no reserve",
                  "authorizes no paid model run",
                  "produces no power value"):
        assert claim in preamble, f"the record does not disclaim: {claim!r}"
    assert "pre-freeze" in preamble


# --------------------------------------------------------------------------- #
# PART L.1 / L.2 — the carrier is a query parameter named maxTotal.
# --------------------------------------------------------------------------- #
def test_the_carrier_is_a_query_parameter_not_a_header():
    """PART L.1 / P1-1: pinned in the identity table AND in the SL-CA1-01 section."""
    cells = _row_cells(RECORD_PATH, "2. candidate identity", "approved carrier")
    assert cells[0] == "approved carrier"
    assert "query parameter" in cells[1]
    assert "header" not in cells[1], (
        "the approved-carrier cell must not name a header in any form"
    )

    body = _section(RECORD_PATH, "3. sl-ca1-01")
    assert "do not use a new request header" in body
    assert "publicly specified query parameter" in body
    assert "ordinary public api input" in body
    assert (
        "no special-header adjudication under requirement 5 is required, because no "
        "special header is used" in body
    )
    assert "p1-1 is closed" in body


def test_the_query_parameter_name_is_maxTotal():
    """PART L.2: one name, in the identity table and in every pin that uses it."""
    cells = _row_cells(RECORD_PATH, "2. candidate identity", "approved carrier")
    assert "maxtotal" in cells[1]
    for heading in ("3. sl-ca1-01", "5. pinned contract decisions"):
        assert "maxtotal" in _section(RECORD_PATH, heading), heading
    # the authoring bar's requirement-5 adjudication names it too
    assert "maxtotal" in _section(POLICY_PATH, "12.1 requirements every candidate")


def test_requirement_five_is_adjudicated_rather_than_left_ambiguous():
    """P1-1: the ambiguity is resolved in the authoring bar itself."""
    body = _section(POLICY_PATH, "12.1 requirements every candidate")
    assert "adjudication (pre-authoring finding p1-1)" in body
    assert "does not forbid ordinary public api input" in body
    assert "is therefore admissible under requirement 5" in body
    assert "is not adjudicated admissible here" in body, (
        "a new request header must NOT be blessed by this adjudication"
    )


# --------------------------------------------------------------------------- #
# PART L.3 / L.4 / L.17 — no PT08, not active, no denominator row.
# --------------------------------------------------------------------------- #
def test_no_pt08_identifier_exists_in_any_public_artifact():
    """PART L.3: not in the index, not on disk, not claimed by the record."""
    with open(TASK_INDEX, newline="", encoding="utf-8") as fh:
        ids = [r["task_id"] for r in csv.DictReader(fh)]
    assert "PT08" not in ids
    assert len(ids) == 9, f"the approved index must still hold nine tasks, not {len(ids)}"
    assert not (PUBLIC_TASKS / "PT08.md").exists()
    cells = _row_cells(RECORD_PATH, "2. candidate identity", "task identifier assigned")
    assert cells[1] == "none"
    body = _section(RECORD_PATH, "2. candidate identity")
    assert "no pt08 identifier is assigned by this record, and none exists" in body


def test_the_candidate_is_not_counted_as_active_anywhere():
    """PART L.4 / L.17: no eligibility, no denominator row, not in the index."""
    body = _section(RECORD_PATH, "2. candidate identity")
    assert "has no eligibility status" in body
    assert "no denominator row" in body
    assert "no active opportunity" in body
    assert "it is not in" in body and "task_index.csv" in body

    # the record's own prohibition list says it again, independently
    prohibitions = _section(RECORD_PATH, "9. prohibitions attaching to this record")
    assert "cand-a1 enters no e1 denominator row" in prohibitions
    assert "cand-a1 is not an active opportunity and is not counted as active" in prohibitions

    # and no public per-task matrix has acquired a CAND-A1 row
    for name in ("PILOT_PUBLIC_TASK_MATRIX.csv", "TASK_RULE_MATRIX.csv",
                 "TASK_ACCEPTANCE_MATRIX.csv", "TASK_LAYER_MATRIX.csv",
                 "ORACLE_TRACEABILITY.csv"):
        text = (DOCS_V2 / name).read_text(encoding="utf-8")
        assert "CAND-A1" not in text and "PT08" not in text, (
            f"{name} carries a row for an unauthored candidate"
        )


def test_the_authoring_state_and_review_state_are_recorded_honestly():
    assert _row_cells(RECORD_PATH, "2. candidate identity", "authoring state")[1] == (
        "not yet authored"
    )
    review = _row_cells(RECORD_PATH, "2. candidate identity", "review state")[1]
    assert "decision b" in review and "awaiting focused remediation review" in review


# --------------------------------------------------------------------------- #
# PART L.18 / L.20 — the counts and the cluster depth must not move.
# --------------------------------------------------------------------------- #
def test_the_active_set_is_still_five_over_three():
    """PART L.18: asserted against the feasibility record, not the candidate record."""
    flat = _flat(FEASIBILITY_PATH)
    assert f"active e1 opportunities: {ACTIVE_OPPORTUNITIES}" in flat
    assert f"decision clusters: {ACTIVE_CLUSTERS}" in flat


@pytest.mark.parametrize("cluster,depth", sorted(CLUSTER_DEPTHS.items()))
def test_the_occupancy_table_still_records_the_pre_authoring_depths(cluster, depth):
    """PART L.20: the depth comes from the occupancy row's own final cell."""
    cells = _row_cells(FEASIBILITY_PATH, "3. the demonstrated feasibility ceiling",
                       cluster)
    assert cells[0] == cluster.lower()
    assert cells[-1] == str(depth), (
        f"{cluster} must still record {depth} active observation(s), not {cells[-1]!r}"
    )


def test_the_record_forbids_pre_counting_the_replication():
    """PART I: depth 2 needs four named preconditions, none of which has happened."""
    body = _section(RECORD_PATH, "7. what must not move before authoring")
    assert f"active `e1` opportunities remain {ACTIVE_OPPORTUNITIES}".replace("`", "") in body
    assert "decision clusters remain 3" in body
    assert "cluster observation depths remain 3 / 1 / 1" in body
    assert "remains at one observation" in body
    assert "none may be pre-counted" in body
    for precondition in ("the public task is authored",
                         "an independent public-authoring review passes",
                         "a private evaluator package is subsequently authored and "
                         "validated",
                         "eligibility governance permits inclusion"):
        assert precondition in body, f"missing depth-2 precondition: {precondition!r}"


# --------------------------------------------------------------------------- #
# PART L.5 / L.6 / L.7 / L.8 — forcing class, acceptance, tuning rules.
# --------------------------------------------------------------------------- #
def test_the_forcing_class_is_natural_path_and_not_strict():
    """PART L.5: pinned in the identity table cell, and its inverse excluded."""
    cells = _row_cells(RECORD_PATH, "2. candidate identity", "forcing class")
    assert cells[0] == "forcing class"
    assert cells[1] == "natural-path / opportunity-creating"
    assert "strict" not in cells[1]

    body = _section(RECORD_PATH, "4. sl-ca1-02")
    assert "its forcing class is natural-path / opportunity-creating, not strict" in body
    assert "therefore the task does not strictly force `features`-scope work".replace("`", "") in body


def test_study_lead_acceptance_is_recorded_fact_by_fact():
    """PART L.6: SL-CA1-02, each required finding as its own statement."""
    acceptance = _row_cells(RECORD_PATH, "2. candidate identity",
                            "study lead acceptance")[1]
    assert acceptance.startswith("recorded")
    assert "sl-ca1-01" in acceptance and "sl-ca1-02" in acceptance
    body = _section(RECORD_PATH, "4. sl-ca1-02")
    for statement in (
        "accepted as a scientifically valid independent replication instrument",
        "is not preservation-only",
        "doing nothing fails the functional contract",
        "creates a real new functional requirement",
        "violating implementation is compiling, ci-agent-clean and "
        "evaluator-detectable",
        "conforming implementations exist",
        "a legitimate boundary-only implementation also exists",
        "cheaper than both",
        "accepted as a construct-validity limitation",
        "must not be represented as having forcing strength equal to",
        "remain pseudo-replicates",
    ):
        assert statement in body, f"SL-CA1-02 no longer records: {statement!r}"
    assert "p1-2 is closed" in body


def test_difficulty_is_evaluated_only_on_the_stage_1_c1_baseline_pilot():
    """PART L.7: the only admissible difficulty evidence, named."""
    body = _section(RECORD_PATH, "4. sl-ca1-02")
    assert (
        "discriminative difficulty must be evaluated only through the "
        "pre-registered stage-1 baseline-only c1 pilot" in body
    )
    # the pilot policy itself must still carry the baseline-only rule it cites
    pilot = _flat(DOCS_V2 / "PILOT_AND_POWER_POLICY.md")
    assert "baseline-only task-hardening decisions" in pilot
    assert "difficulty is tuned on c1" in pilot


def test_no_c4_or_treatment_effect_tuning_is_permitted():
    """PART L.8: the inadmissible inputs are enumerated, not implied."""
    body = _section(RECORD_PATH, "4. sl-ca1-02")
    assert (
        "the task must never be tuned based on c4 or on any treatment-effect result"
        in body
    )
    assert "inadmissible inputs to task tuning" in body
    for inadmissible in ("an observed afci advantage", "a condition contrast",
                         "an interaction estimate"):
        assert inadmissible in body, f"not listed as inadmissible: {inadmissible!r}"


# --------------------------------------------------------------------------- #
# PART L.9 — the forcing-strength asymmetry (P1-3).
# --------------------------------------------------------------------------- #
def test_the_forcing_asymmetry_is_recorded_in_the_authoritative_feasibility_record():
    """PART L.9: §2a exists, is normative, and states both classes."""
    body = _section(FEASIBILITY_PATH, "2a. task-createdness is not forcing strength")
    assert (
        "ar-dep-006 is task-creatable for both represented forbidden targets. the two "
        "existing decision families have different forcing strength on the canonical "
        "substrate." in body
    )
    assert "strong / strict task-created forcing" in body
    assert "natural-path / opportunity-creating forcing" in body
    assert "task-creatable does not mean every valid implementation must encounter " \
           "the forbidden decision" in body
    assert "this closes pre-authoring finding" in body and "p1-3" in body


@pytest.mark.parametrize(
    "cluster,expected_class,escape",
    [(FEATURES_INFRA, "strong / strict task-created forcing", "no"),
     (FEATURES_API, "natural-path / opportunity-creating forcing", "yes")],
    ids=["features-infra-strict", "features-api-natural-path"],
)
def test_each_family_carries_its_own_forcing_class_row(cluster, expected_class, escape):
    """Row-scoped: the class comes from that family's own table row."""
    cells = _row_cells(FEASIBILITY_PATH,
                       "2a. task-createdness is not forcing strength", cluster)
    assert cells[1] == "yes", f"{cluster} must stay task-creatable"
    assert cells[2] == expected_class, (
        f"{cluster} must record {expected_class!r}, not {cells[2]!r}"
    )
    assert cells[3] == escape, (
        f"{cluster} must record boundary-only-conforming = {escape!r}"
    )


def test_the_two_families_do_not_share_a_forcing_class():
    """The asymmetry must be a real difference, not two labels for one class."""
    infra = _row_cells(FEASIBILITY_PATH,
                       "2a. task-createdness is not forcing strength", FEATURES_INFRA)
    api = _row_cells(FEASIBILITY_PATH,
                     "2a. task-createdness is not forcing strength", FEATURES_API)
    assert infra[2] != api[2]
    assert infra[3] != api[3]


def test_no_public_artifact_says_features_api_is_strictly_forced():
    """The inversion of P1-3's claim, excluded document-wide."""
    offenders = []
    for rel in G.governed_files():
        flat = G.norm((REPO / rel).read_text(encoding="utf-8"))
        for inversion in ("features → api is strictly forced",
                          "features → api is strictly-forced",
                          "features → api carries strict forcing",
                          "features → api is strict task-created forcing"):
            if inversion in flat:
                offenders.append(f"{rel}: {inversion}")
    assert offenders == [], (
        f"a governed document asserts strict forcing for features → api: {offenders}"
    )


def test_the_asymmetry_changes_no_count_and_adds_no_cluster():
    """PART D: §2a must state what it does NOT do."""
    body = _section(FEASIBILITY_PATH, "2a. task-createdness is not forcing strength")
    assert "does not redefine `e1`".replace("`", "") in body
    assert "does not change the" in body and "feasibility ceiling" in body
    assert "adds no decision cluster" in body
    assert "reopens none" in body
    assert "deliberately not adjudicated" in body, (
        "api → core must be recorded as unadjudicated, never guessed"
    )
    assert "this does not invalidate" in body and "pt04" in body


# --------------------------------------------------------------------------- #
# PART L.15 — the P-3 .. P-6 contract pins.
# --------------------------------------------------------------------------- #
def test_all_four_contract_pins_have_their_own_subsection():
    body = _flat(RECORD_PATH)
    for pin in ("`p-3` — rejection outcome",
                "`p-4` — query parameter and wire determinacy",
                "`p-4` precedence — body validation versus malformed `maxtotal`",
                "`p-5` — no new money semantics",
                "`p-6` — observation boundary"):
        assert pin.replace("`", "") in body, f"missing pin subsection: {pin!r}"


def test_p3_pins_409_the_error_value_and_the_exact_key_set():
    """PART L.15: status, error, and a CLOSED response-key set."""
    section = "p-3 — rejection outcome"
    assert _row_by_first_cell(RECORD_PATH, section, "http status")[1] == "409"
    assert _row_by_first_cell(RECORD_PATH, section, "error")[1] == (
        "ordervaluelimitexceeded"
    )
    keys = _row_by_first_cell(RECORD_PATH, section, "response keys")
    assert keys[1] == "exactly error, message, correlationid"
    extra = _row_by_first_cell(RECORD_PATH, section, "additional response keys")
    assert extra[1] == "not permitted"
    body = _section(RECORD_PATH, "5. pinned contract decisions")
    assert "exact message text not pinned" in body
    assert "409 is not interchangeable with 400" in body
    assert "policy outcome, not a request-validation outcome" in body
    assert "distinct from an ordinary" in body and "validationerror" in body
    assert "pt06's validation-envelope work" in body


@pytest.mark.parametrize(
    "case,expected",
    [("absent", "existing behaviour unchanged"),
     ("zero", "valid"),
     ("negative", "400"),
     ("empty", "400"),
     ("non-numeric", "400"),
     ("repeated maxtotal values", "400")],
)
def test_p4_pins_each_wire_case_in_its_own_row(case, expected):
    """PART L.15: row-scoped, so one case cannot borrow another's outcome."""
    cells = _row_by_first_cell(RECORD_PATH, WIRE_SECTION, case)
    assert expected in cells[1], (
        f"the {case!r} row must record {expected!r}, not {cells[1]!r}"
    )


def test_every_pinned_wire_case_has_exactly_one_row():
    """No case may be dropped, and none may be duplicated with two outcomes."""
    start, end = _region_lines(RECORD_PATH, WIRE_SECTION)
    labels = []
    for p in _passages(RECORD_PATH):
        if p.kind == "table-row" and start <= p.line < end:
            cells = [c.strip() for c in p.flat.strip("|").split("|")]
            labels.append(cells[0])
    for case in ("absent", "present once", "zero", "negative", "empty",
                 "non-numeric", "`nan` / `infinity` spellings".replace("`", ""),
                 "repeated maxtotal values"):
        assert labels.count(case) == 1, (
            f"the wire table must carry exactly one {case!r} row, found "
            f"{labels.count(case)}"
        )


def test_p4_pins_negative_and_malformed_values_as_invalid():
    """PART M.13: 'negative is valid' must be impossible to state here."""
    for case in ("negative", "empty", "non-numeric",
                 "repeated maxtotal values"):
        cells = _row_by_first_cell(RECORD_PATH, WIRE_SECTION, case)
        assert cells[1].startswith("invalid"), (
            f"the {case!r} row must record an INVALID outcome, not {cells[1]!r}"
        )
        # "valid" as a standalone word would be the inverted claim; "invalid" and
        # "validationerror" both keep it bound to other characters.
        assert not re.search(r"\bvalid\b", cells[1]), (
            f"the {case!r} row records a VALID outcome: {cells[1]!r}"
        )
    # and the one case that IS valid stays valid
    zero = _row_by_first_cell(RECORD_PATH, WIRE_SECTION, "zero")
    assert re.search(r"\bvalid\b", zero[1]), (
        f"a ceiling of zero must stay valid, not {zero[1]!r}"
    )


def test_p4_accepts_equality_and_rejects_only_above_the_ceiling():
    """PART L.15 / PART M.14: the equality boundary, row by row."""
    eq = _row_by_first_cell(RECORD_PATH, WIRE_SECTION,
                            "reported order total == maxtotal")
    assert "accepted" in eq[1]
    assert "normal creation result" in eq[1]
    assert "409" not in eq[1], "equality must never be recorded as a rejection"
    below = _row_by_first_cell(RECORD_PATH, WIRE_SECTION,
                               "reported order total < maxtotal")
    assert below[1] == "normal creation result"
    above = _row_by_first_cell(RECORD_PATH, WIRE_SECTION,
                               "reported order total > maxtotal")
    assert "409" in above[1] and "ordervaluelimitexceeded" in above[1]
    body = _section(RECORD_PATH, "5. pinned contract decisions")
    assert "equality is accepted" in body
    assert "never a rejection" in body


def test_p4_precedence_is_pinned_deterministically():
    """PART L.15: one selected precedence, with its reason and the rejected one."""
    body = _section(RECORD_PATH, "5. pinned contract decisions")
    assert "selected pin: existing body validation wins" in body
    assert "the existing body-validation outcome, unchanged" in body
    assert "it preserves an existing outcome" in body
    assert "it follows the substrate's own order" in body
    assert "it is deterministic and single-valued" in body
    assert "malformed ceiling wins* was rejected".replace("*", "") in body
    assert (
        "existing request-body validation remains governed by the existing "
        "task/service contract and is not re-specified by" in body
    )


def test_p5_forbids_every_new_money_rule():
    """PART L.15 / PART M.17: no rounding rule may be inserted."""
    body = _section(RECORD_PATH, "5. pinned contract decisions")
    for prohibition in ("no new rounding rule", "no new precision rule",
                        "no discount rule", "no currency conversion",
                        "no change to the existing subtotal/total computation",
                        "no new monetary rounding rule is introduced",
                        "is not rounded before comparison",
                        "no currency-conversion rule is introduced"):
        assert prohibition in body, f"P-5/P-4 no longer forbids: {prohibition!r}"
    assert (
        "the comparison is against the same total the service itself would report "
        "for that request under existing behaviour" in body
    )
    assert "compared against the existing service-computed/reported total" in body
    assert "pt05 owns order-level discount computation" in body
    assert "pr01 owns cent-exact" in body


def test_p6_pins_http_only_observation_with_no_seam_and_no_repository_reset():
    """PART L.15 / PART M.18: resetOrderRepository must stay excluded."""
    body = _section(RECORD_PATH, "5. pinned contract decisions")
    for pin in ("http only", "no `logoutput` seam".replace("`", ""),
                "no new seam of any kind",
                "no hidden header and no hidden setup",
                "no persistence inspection", "no seeded repository state",
                "no direct implementation-module state inspection",
                "no `resetorderrepository()`".replace("`", ""),
                "a fresh application over a freshly evaluated module graph per "
                "hidden case",
                "no cross-case state dependence"):
        assert pin in body, f"P-6 no longer pins: {pin!r}"


# --------------------------------------------------------------------------- #
# PART L.16 — the pre-declared legal alternatives.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("alt", ["alt-a", "alt-c", "alt-f", "alt-h", "alt-i", "alt-k"])
def test_every_declared_alternative_is_legal_and_edge_free(alt):
    """PART L.16: row-scoped, so no family can drift into 'creates an edge'."""
    cells = _row_cells(RECORD_PATH, "6. pre-declared legitimate implementation "
                                    "families", alt)
    assert cells[0] == alt
    assert cells[2] == "yes", f"{alt} must be recorded legal"
    assert cells[3] == "no", f"{alt} must create no forbidden edge"


def test_alt_c_is_the_boundary_only_counterexample_and_is_cheaper():
    """PART L.16 / PART M.6: ALT-C is what makes the forcing natural-path."""
    cells = _row_cells(RECORD_PATH, "6. pre-declared legitimate implementation "
                                    "families", "alt-c")
    assert "boundary-only enforcement" in cells[1]
    assert "createorderusecase returns its computed total" in cells[1]
    assert "features untouched" in cells[1]
    body = _section(RECORD_PATH, "6. pre-declared legitimate implementation families")
    assert (
        "alt-c is the strongest task-createdness counterexample, and it is cheaper "
        "than the feature-side implementation" in body
    )


def test_alt_k_may_reduce_violation_frequency_and_that_is_accepted():
    """PART L.16: the consequence is recorded as expected, not engineered away."""
    cells = _row_cells(RECORD_PATH, "6. pre-declared legitimate implementation "
                                    "families", "alt-k")
    assert "permitted shared facility" in cells[1]
    assert "provided no forbidden `features → api` edge exists".replace("`", "") in cells[1]
    body = _section(RECORD_PATH, "6. pre-declared legitimate implementation families")
    assert "alt-k may also reduce violation frequency" in body
    assert "both consequences are expected and accepted" in body
    assert (
        "no hidden architecture rule may be designed around eliminating these legal "
        "alternatives" in body
    )
    assert "none of these is a recommendation" in body


def test_the_violating_family_is_not_published_here():
    """PART H: the public record must not carry the expected violation shape."""
    body = _section(RECORD_PATH, "6. pre-declared legitimate implementation families")
    assert (
        "the expected violating implementation family is recorded privately and "
        "conceptually only" in body
    )
    assert "must not appear in the eventual public task prose" in body
    # and no dependency-form enumeration leaks into the public record
    flat = _flat(RECORD_PATH)
    for leak in ("static import", "type-only import", "dynamic import()",
                 "require()", "re-export"):
        assert leak not in flat, (
            f"the public record enumerates a violating dependency form: {leak!r}"
        )


# --------------------------------------------------------------------------- #
# PART J — the four P1 closures, and what is still NOT approved.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("finding", ["p1-1", "p1-2", "p1-3", "p1-4"])
def test_each_p1_finding_has_a_closed_row_with_a_named_mechanism(finding):
    """PART J: closed, and closed BY something a reviewer can check."""
    cells = _row_cells(RECORD_PATH, "8. pre-authoring", finding)
    assert cells[0].strip("*` ") == finding or finding in cells[0]
    assert "closed" in cells[-1], f"{finding} must be recorded CLOSED"
    assert len(cells[-1]) > 40, f"{finding}'s disposition must name its mechanism"


def test_the_p1_dispositions_name_the_right_mechanisms():
    body = _section(RECORD_PATH, "8. pre-authoring")
    assert "closed by choosing the public query parameter" in body
    assert "no special-header adjudication required" in body
    assert "closed by study lead acceptance of natural-path forcing" in body
    assert "stage-1 `c1`-only".replace("`", "") in body
    assert "no `c4`/effect-based tuning".replace("`", "") in body
    assert "closed by recording the asymmetry in authoritative governance" in body
    assert "closed by propagating that already-completed re-approval" in body
    assert "p0 count: 0" in body


def test_the_candidate_is_not_finally_approved():
    """PART J: closing the P1 findings is remediation, not approval."""
    body = _section(RECORD_PATH, "8. pre-authoring")
    assert "the overall" in body and "authoring review is not finally approved" in body
    assert "closing the four p1 findings is remediation, not approval" in body
    assert (
        "one focused independent remediation re-review of this record is still "
        "required, and authoring may not begin before it passes" in body
    )
    intro = _section(RECORD_PATH, "1. what this record is")
    assert "it is not an approval" in intro


def test_the_prohibition_list_is_complete():
    """PART E / PART I: each prohibition as its own statement."""
    body = _section(RECORD_PATH, "9. prohibitions attaching to this record")
    for prohibition in (
        "no `pt08` identifier is assigned".replace("`", ""),
        "is not an authored public task",
        "has no private evaluator package",
        "has no manifest",
        "has no eligibility status",
        "enters no `e1` denominator row".replace("`", ""),
        "is not an active opportunity and is not counted as active",
        "forcing strength must not be represented as equal to",
        "is not resolved by this record",
        "nothing here is frozen",
        "no benchmark or model result exists",
    ):
        assert prohibition in body, f"the record no longer prohibits: {prohibition!r}"


# --------------------------------------------------------------------------- #
# PART L.10 / L.11 / L.12 / L.13 / L.14 — the surrounding lifecycle facts.
# --------------------------------------------------------------------------- #
def test_the_e1_construct_definition_is_unchanged():
    """PART L.10: the record must not touch what E1 measures."""
    body = _section(FEASIBILITY_PATH, "2a. task-createdness is not forcing strength")
    assert "does not redefine `e1`".replace("`", "") in body
    # and the construct/endpoint statements themselves are untouched
    claims = (DOCS_V2 / "CLAIMS_CONSTRUCTS_METRICS.csv").read_text(encoding="utf-8")
    assert "CAND-A1" not in claims and "maxTotal" not in claims
    rq = _flat(DOCS_V2 / "RESEARCH_QUESTIONS.md")
    assert "cand-a1" not in rq, (
        "an unauthored candidate must not appear in the research-question record"
    )


def test_the_td_b40_re_approval_is_recorded_publicly():
    """PART L.11: the propagated re-approval, in the registry row itself."""
    text = G.norm(_decision("TD-B40")["decision"])
    assert "td-b40(b) complete migration - independently re-approved" in text
    assert "external independent read-only" in text
    assert "p1-j1 and p1-j2" in text
    assert "no new p0 and no new p1" in text
    assert "migration state unchanged" in text
    assert "fails closed" in text
    assert "precedes the commits that record it" in text
    assert "propagate that result and neither performs it" in text
    assert "none is claimed" in text


def test_td_b40_is_resolved_and_its_closure_is_bounded():
    """PART L.12 / L.13: resolved, and closure passes no gate."""
    row = _decision("TD-B40")
    assert row["status"].strip().lower() == "resolved"
    text = G.norm(row["decision"])
    assert "both residuals of the re-scoped row are complete" in text
    for denial in ("freezes no manifest", "passes no gate including g1",
                   "makes no experiment run-ready",
                   "activates neither pr01 nor pr02",
                   "resolves neither td-b34 nor td-b39",
                   "td-b40 never governed freeze"):
        assert denial in text, f"the TD-B40 row does not deny: {denial!r}"
    # the gates that genuinely govern freeze are untouched
    for still_open in ("TD-B05", "TD-B14", "TD-B32", "TD-B34", "TD-B39"):
        assert _decision(still_open)["status"].strip().lower() == "open", still_open


def test_nothing_is_frozen_and_no_result_exists():
    """PART L.14 / PART O: the protocol state is unchanged."""
    assert "PRE-FREEZE" in (DOCS_V2 / "README.md").read_text(encoding="utf-8")
    assert "PRE-FREEZE" in RECORD_PATH.read_text(encoding="utf-8")
    results = REPO / "experiments" / "v2" / "results"
    assert sorted(p.name for p in results.iterdir()) == ["README.md"], (
        "a result artifact appeared in experiments/v2/results"
    )
    analysis = REPO / "experiments" / "v2" / "analysis"
    assert sorted(p.name for p in analysis.iterdir()) == ["README.md"], (
        "an analysis/power artifact appeared in experiments/v2/analysis"
    )


def test_td_b34_stays_open_and_records_the_candidate_as_progress_only():
    """The candidate is progress toward replication depth, not its resolution."""
    row = _decision("TD-B34")
    assert row["status"].strip().lower() == "open"
    assert row["blocking"] == "yes"
    text = G.norm(row["decision"])
    assert "priority-a pre-authoring progress, not resolution" in text
    assert "cand-a1" in text
    assert "no pt08 identifier is assigned" in text
    assert "td-b34 therefore remains open and blocking" in text
    assert "one focused independent remediation re-review" in text
    assert "priority b" in text and "no candidate review at all" in text
