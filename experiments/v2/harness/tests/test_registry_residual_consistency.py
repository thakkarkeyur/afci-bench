"""Cross-row consistency between a RESOLVED decision and every other current row.

WHY THIS MODULE EXISTS
----------------------
The focused independent `CAND-A1` remediation re-review found `P1-4` **not fully
closed**. `TD-B40` had been correctly recorded as **RESOLVED**, with residual (A)
and residual (B) both **COMPLETE**, but two *other* public statements still
claimed, in unmarked present tense, that the very same residual was outstanding:

* ``docs/v2/OPEN_DECISIONS.csv`` — the `TD-B34` row asserted that the opportunity
  migration's "independent re-approval **remains outstanding** under `TD-B40`
  residual (B)". A machine reader of the registry could therefore read `TD-B40`
  as resolved and, one row away, read its residual as open.
* ``docs/v2/README.md`` — the `PT07`-package-approval bullet said the migration's
  "independent re-approval **is still outstanding** under `TD-B40` residual (B)"
  as live prose, with no historical marking.

Neither statement was a *new* factual error: both were true when written and were
left behind by a read-only re-review that changed no byte. That is precisely the
defect class this module exists to make impossible to reintroduce: **a resolved
decision contradicted by a current row elsewhere in the same registry.**

THE CONSISTENCY RELATION
------------------------
Derived from the registry itself rather than hardcoded, so a future resolved
decision is covered the moment it is written:

  For every row whose ``status`` is ``resolved``, every residual that row records
  as ``- COMPLETE`` is a **completed residual**. No CURRENT statement anywhere in
  the governed corpus may claim that a completed residual *remains outstanding*,
  *is still outstanding*, *remains pending*, *is still pending*, *still requires
  independent re-approval*, or is *not (yet) independently re-approved*.

Two enforcement regimes, matching the two media:

* **CSV (machine-readable):** unconditional. A CSV field is consumed as current
  state and carries no historical-marking convention, so stale wording there is a
  defect however it is phrased. There is no marker escape.
* **Markdown (narrative):** history is preserved, not deleted. Stale wording is
  permitted **only** in a passage that carries an approved historical marker in
  its **own** text — the repository's existing convention, ``as recorded then`` /
  ``as originally recorded`` (plus the pinned ``TD-B34-BREADTH-HISTORICAL``
  token). Generic supersession words are deliberately **not** accepted, for the
  reason :mod:`governance_text` already documents: "superseded", "historical" and
  "withdrawn as stale" occur constantly for unrelated reasons and were shown to
  rescue live claims.

HOW IT ASSERTS
--------------
Row-aware and field-aware, never window-aware. The unit of judgement is a
:class:`governance_text.Passage` — one CSV ``(row, column)`` field, one Markdown
list item with its continuations, one table row, one blockquote run or one
paragraph — and, inside it, one **sentence**. There is no fixed-width proximity
window anywhere in this module, so a stale claim can never be rescued by prose
belonging to a neighbouring passage, nor by a completion statement sitting some
number of characters away in a different sentence.

WHAT IS DELIBERATELY NOT POLICED
--------------------------------
The bare noun phrase "the outstanding independent re-approval" is the residual's
own *name*, and the corpus legitimately uses it in current sentences that
immediately record its completion ("... and both of those residuals are now
complete"). Only **predicate** claims — that the residual remains/is still
outstanding or pending — are stale-claim vocabulary. Equally, "freeze remains
outstanding" is a true current statement about `TD-B05`/`TD-B14`/`TD-B32`/`G1`
and is not a `TD-B40` residual at all; the relation therefore binds the stale
predicate to a residual reference inside one sentence rather than to the mere
presence of a decision id in the passage.

Pure file inspection. No model is invoked, nothing is frozen, no benchmark or
power value is produced.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

import governance_text as G

REPO = G.REPO
DOCS_V2 = REPO / "docs" / "v2"
DECISIONS_CSV = DOCS_V2 / "OPEN_DECISIONS.csv"
DECISIONS_MD = DOCS_V2 / "OPEN_DECISIONS.md"
README = DOCS_V2 / "README.md"
RECORD_PATH = DOCS_V2 / "CAND_A1_PREAUTHORING_DECISION.md"
TASK_INDEX = REPO / "experiments" / "v2" / "tasks" / "public" / "TASK_INDEX.csv"
GATE_MATRIX = DOCS_V2 / "PILOT_GATE_MATRIX.csv"

#: A residual recorded complete inside a resolved row, e.g.
#: "RESIDUAL (B) INDEPENDENT RE-APPROVAL OF THE COMPLETE MIGRATION - COMPLETE".
#: ``[^.]*`` cannot cross a sentence boundary, so a later unrelated "complete"
#: cannot manufacture a completion.
RESIDUAL_COMPLETE_RE = re.compile(r"residual \((?P<label>[a-z])\)(?P<subject>[^.]*?)[-–—] complete")

#: Ways of asserting that something is NOT done. Predicate forms only — see the
#: module docstring for why the residual's own noun phrase is excluded.
STALE_CLAIM_VOCABULARY: Dict[str, str] = {
    "remains-outstanding": r"\bremains? outstanding\b|\bremain outstanding\b",
    "still-outstanding": r"\b(?:is|are|was|were|stays|stayed|remains) still outstanding\b"
                         r"|\bstill outstanding\b",
    "remains-pending": r"\bremains? pending\b|\bremain pending\b",
    "still-pending": r"\b(?:is|are|was|were|stays|stayed|remains) still pending\b"
                     r"|\bstill pending\b",
    "still-requires-re-approval": r"\bstill requires? (?:an )?independent re-approval\b"
                                  r"|\bstill requires? re-approval\b",
    "not-independently-re-approved": r"\bnot (?:yet )?independently re-approved\b"
                                     r"|\bhas not (?:yet )?been independently re-approved\b",
    "awaits-re-approval": r"\bawait(?:s|ing)? independent re-approval\b",
}

#: The repository's established historical/supersession markers. Deliberately
#: narrow: a generic word can be present for unrelated reasons, which is the exact
#: rescue the earlier mutation review exploited.
HISTORICAL_MARKERS: Tuple[str, ...] = (
    "as recorded then",
    "as recorded at the time",
    "as originally recorded",
    G.BREADTH_HISTORICAL_MARKER,
)

#: Sentence boundary: end punctuation followed by whitespace. A sentence is a
#: structural unit of the passage, not a character window.
_SENTENCE_RE = re.compile(r"(?<=[.;:!?])\s+")


# --------------------------------------------------------------------------- #
# Derivation — the relation comes from the registry, not from a constant
# --------------------------------------------------------------------------- #
def _rows() -> List[dict]:
    with open(DECISIONS_CSV, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def completed_residuals() -> Dict[Tuple[str, str], str]:
    """``{(decision_id, label): subject}`` for every residual a RESOLVED row completes.

    Derived from the registry, so another decision that closes with named
    residuals is policed automatically. Only resolved rows contribute: an open
    row's residuals are allowed to be outstanding, which is what "open" means.
    """
    out: Dict[Tuple[str, str], str] = {}
    for row in _rows():
        if row["status"].strip().lower() != "resolved":
            continue
        for m in RESIDUAL_COMPLETE_RE.finditer(G.norm(row["decision"])):
            subject = m.group("subject").strip(" -–—")
            out[(row["decision_id"], m.group("label"))] = subject
    return out


def _reference_patterns(decision_id: str, label: str, subject: str) -> List[str]:
    """Ways one sentence can name this particular residual.

    The label form (``residual (b)``) and the residual's own subject head (the
    part before " of ", e.g. ``independent re-approval``) — nothing broader, so a
    sentence about a *different* obligation of the same decision (a pending
    freeze, say) is not mistaken for a claim about this residual.
    """
    head = subject.split(" of ")[0].strip() if " of " in subject else subject
    patterns = [
        rf"\bresidual \({label}\)",
        rf"\b{re.escape(decision_id.lower())}\({label}\)",
    ]
    if head:
        patterns.append(re.escape(head))
    return patterns


def _sentences(flat: str) -> List[str]:
    return [s for s in _SENTENCE_RE.split(flat) if s.strip()]


def _stale_hits(passages) -> List[Tuple[G.Passage, str, str, List[str]]]:
    """``(passage, residual_key, sentence, vocabulary_names)`` for every stale claim.

    A hit needs, inside ONE sentence of ONE passage: a reference to a completed
    residual and a stale-claim predicate. Cross-sentence and cross-passage
    coincidences cannot produce a hit.
    """
    residuals = completed_residuals()
    assert residuals, "no completed residual was derived from the registry"
    compiled_vocab = {k: re.compile(v) for k, v in STALE_CLAIM_VOCABULARY.items()}
    refs = {
        key: [re.compile(p) for p in _reference_patterns(key[0], key[1], subject)]
        for key, subject in residuals.items()
    }
    hits = []
    for passage in passages:
        for sentence in _sentences(passage.flat):
            names = sorted(k for k, rx in compiled_vocab.items() if rx.search(sentence))
            if not names:
                continue
            for key, patterns in refs.items():
                if any(rx.search(sentence) for rx in patterns):
                    hits.append((passage, f"{key[0]}({key[1].upper()})", sentence, names))
    return hits


def _marked_historical(passage: G.Passage) -> bool:
    return any(marker in passage.flat for marker in HISTORICAL_MARKERS)


# --------------------------------------------------------------------------- #
# PART D.1 — the relation is real and derived
# --------------------------------------------------------------------------- #
def test_the_completed_residuals_are_derived_from_the_registry_itself():
    """A hardcoded list would stop covering the next resolved decision."""
    residuals = completed_residuals()
    assert ("TD-B40", "a") in residuals, (
        "TD-B40 residual (A) is no longer derivable as complete from the registry"
    )
    assert ("TD-B40", "b") in residuals, (
        "TD-B40 residual (B) is no longer derivable as complete from the registry"
    )
    assert "independent re-approval" in residuals[("TD-B40", "b")], (
        f"residual (B)'s recorded subject changed: {residuals[('TD-B40', 'b')]!r}"
    )
    # only resolved rows may contribute: an open row's residuals may be outstanding
    open_ids = {r["decision_id"] for r in _rows() if r["status"].strip().lower() == "open"}
    assert not {d for d, _ in residuals} & open_ids


# --------------------------------------------------------------------------- #
# PART D.2 — CSV: no current machine-readable contradiction, no marker escape
# --------------------------------------------------------------------------- #
def test_no_csv_field_claims_a_completed_residual_is_outstanding():
    """The core machine-readable rule, field-aware and unconditional.

    Every governed CSV is consumed as current state. A field claiming a completed
    residual is outstanding is a defect regardless of wording, and regardless of
    what any neighbouring field, row or document says.
    """
    csv_passages = [p for p in G.all_passages() if p.kind == "csv-field"]
    assert csv_passages, "no CSV field was scanned; the guard would be vacuous"
    offenders = [
        f"{p.rel} {p.heading} claims {key} {names}: {sentence[:200]!r}"
        for p, key, sentence, names in _stale_hits(csv_passages)
    ]
    assert offenders == [], (
        "a machine-readable registry field contradicts a resolved decision by "
        "claiming its completed residual is still outstanding:\n  - "
        + "\n  - ".join(offenders)
    )


def test_the_td_b34_row_is_the_row_this_rule_was_written_for():
    """Named explicitly, so the CSV rule cannot silently stop covering it."""
    field = next(
        p for p in G.csv_passages(DECISIONS_CSV, "docs/v2/OPEN_DECISIONS.csv")
        if p.heading == "row TD-B34 / column decision"
    )
    assert not _stale_hits([field]), "the TD-B34 row still carries a stale residual claim"
    for phrase in ("remains outstanding", "is still outstanding", "remains pending",
                   "is still pending", "still requires independent re-approval"):
        assert phrase not in field.flat, (
            f"the TD-B34 row reintroduced {phrase!r}"
        )


# --------------------------------------------------------------------------- #
# PART D.3 — Markdown: history is kept, but only when structurally marked
# --------------------------------------------------------------------------- #
def test_every_markdown_stale_residual_claim_is_structurally_marked_historical():
    """Narrative history survives; unmarked live prose does not.

    A passage may retain the old wording — nothing is rewritten as though the
    earlier state never existed — but only if it carries an approved historical
    marker in its own text. Removing the marker while keeping the wording turns
    history back into a live claim and fails here.
    """
    md_passages = [p for p in G.all_passages() if p.kind != "csv-field"]
    unmarked = [
        f"{p.rel}:{p.line} [{p.kind}] under {p.heading!r} claims {key} {names}: "
        f"{sentence[:200]!r}"
        for p, key, sentence, names in _stale_hits(md_passages)
        if not _marked_historical(p)
    ]
    assert unmarked == [], (
        "a governed document states as CURRENT prose that a completed residual is "
        "still outstanding; mark it with the repository's historical convention "
        f"({HISTORICAL_MARKERS[0]!r}) or correct it:\n  - " + "\n  - ".join(unmarked)
    )


def test_a_marked_historical_stale_claim_is_accepted():
    """The other direction: the guard must not force history to be deleted."""
    hits = _stale_hits([p for p in G.all_passages() if p.kind != "csv-field"])
    assert hits, (
        "no marked historical residual claim remains anywhere; the README "
        "provenance was deleted rather than marked, or the vocabulary stopped "
        "matching it"
    )
    for passage, _, _, _ in hits:
        assert _marked_historical(passage)


# --------------------------------------------------------------------------- #
# PART D.4 — guard the guard
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "phrasing",
    ["the independent re-approval of the migration remains outstanding under "
     "TD-B40 residual (B)",
     "TD-B40 residual (B) is still outstanding",
     "residual (B) remains pending",
     "TD-B40 residual (B) is still pending",
     "the migration still requires independent re-approval under TD-B40 residual (B)",
     "the complete migration is not yet independently re-approved (TD-B40 residual (B))",
     "TD-B40 residual (B) awaits independent re-approval"],
)
def test_the_stale_vocabulary_matches_every_mandated_phrasing(phrasing):
    """Each phrasing the re-review named must be caught, in either medium."""
    synthetic = G.Passage(
        rel="docs/v2/OPEN_DECISIONS.csv", heading="row TD-B34 / column decision",
        line=35, kind="csv-field", raw=phrasing, flat=G.norm(phrasing),
    )
    assert _stale_hits([synthetic]), f"the vocabulary no longer catches {phrasing!r}"


def test_a_marker_cannot_rescue_a_csv_field():
    """The CSV rule has no marker escape: current state has no 'as recorded then'."""
    phrasing = ("as recorded then, the independent re-approval remains outstanding "
                "under TD-B40 residual (B)")
    synthetic = G.Passage(
        rel="docs/v2/OPEN_DECISIONS.csv", heading="row TD-B34 / column decision",
        line=35, kind="csv-field", raw=phrasing, flat=G.norm(phrasing),
    )
    assert _stale_hits([synthetic])
    offenders = [h for h in _stale_hits([synthetic]) if h[0].kind == "csv-field"]
    assert offenders, "a CSV field must never be excusable by a historical marker"


def test_an_unmarked_markdown_claim_is_reported_and_a_marked_one_is_not():
    """The two Markdown outcomes, as one paired unit test."""
    stale = ("The approval covers the PT07 package only — not the private opportunity "
             "migration, whose independent re-approval is still outstanding under "
             "TD-B40 residual (B).")
    unmarked = G.Passage(
        rel="docs/v2/README.md", heading="pt07 authored under decision b",
        line=1, kind="list-item", raw=stale, flat=G.norm(stale),
    )
    assert _stale_hits([unmarked]), "the vocabulary stopped matching the real defect"
    assert not _marked_historical(unmarked), "unmarked prose must not look marked"

    marked_raw = ("*As recorded then*, that migration's independent re-approval was "
                  "still outstanding under `TD-B40` residual (B); it has since been "
                  "independently re-approved.")
    marked = G.Passage(
        rel="docs/v2/README.md", heading="pt07 authored under decision b",
        line=1, kind="list-item", raw=marked_raw, flat=G.norm(marked_raw),
    )
    assert _stale_hits([marked]), "the claim itself must still be recognised"
    assert _marked_historical(marked), (
        "correctly marked history must be accepted, or the guard would force "
        "history to be deleted"
    )


def test_generic_supersession_prose_is_not_an_approved_marker():
    """The rescue the earlier mutation review exploited stays impossible."""
    for rescue in ("superseded", "historical", "withdrawn as stale", "obsolete",
                   "no longer current", "this is history"):
        passage = G.Passage(
            rel="docs/v2/README.md", heading="h", line=1, kind="paragraph",
            raw=rescue, flat=G.norm(rescue),
        )
        assert not _marked_historical(passage), (
            f"generic prose {rescue!r} is being accepted as a historical marker"
        )


def test_a_true_current_outstanding_statement_is_not_a_residual_claim():
    """Precision: freeze IS outstanding, and saying so must stay legal.

    The TD-B40 row states this explicitly — "a still-pending freeze is NOT a
    TD-B40 residual". A guard that flagged it would push authors to delete a true
    statement.
    """
    legal = ("the package is status=review and not frozen, so validation and freeze "
             "remain outstanding (TD-B05/TD-B14/TD-B32, G1)")
    passage = G.Passage(
        rel="docs/v2/README.md", heading="h", line=1, kind="list-item",
        raw=legal, flat=G.norm(legal),
    )
    assert not _stale_hits([passage]), (
        "a true current statement about freeze was mistaken for a residual claim"
    )


def test_the_residual_name_used_in_a_completion_sentence_is_not_a_stale_claim():
    """The corpus's own idiom must not be criminalised."""
    legal = ("TD-B40 then governed only the residual inactive-reserve rows and the "
             "outstanding independent re-approval, and both of those residuals are "
             "now complete.")
    passage = G.Passage(
        rel="docs/v2/README.md", heading="h", line=1, kind="list-item",
        raw=legal, flat=G.norm(legal),
    )
    assert not _stale_hits([passage])


# --------------------------------------------------------------------------- #
# PART E — direct regression assertions
# --------------------------------------------------------------------------- #
def _decision(decision_id: str) -> dict:
    for row in _rows():
        if row["decision_id"] == decision_id:
            return row
    raise AssertionError(f"{decision_id} is not in the registry")


def test_e1_td_b40_is_resolved():
    """PART E.1."""
    assert _decision("TD-B40")["status"].strip().lower() == "resolved"
    assert G.norm(_decision("TD-B40")["decision"]).startswith("resolved / closed")


def test_e2_residual_b_is_recorded_complete():
    """PART E.2."""
    text = G.norm(_decision("TD-B40")["decision"])
    assert ("residual (b) independent re-approval of the complete migration - complete"
            in text)
    assert "td-b40(b) complete migration - independently re-approved" in text


def test_e3_td_b34_remains_open_and_blocking():
    """PART E.3."""
    row = _decision("TD-B34")
    assert row["status"].strip().lower() == "open"
    assert row["blocking"] == "yes"
    assert row["gate"] == "G1/G2/G6"
    assert "td-b34 therefore remains open and blocking" in G.norm(row["decision"])


def test_e4_td_b34_does_not_say_td_b40_b_remains_outstanding():
    """PART E.4 — the corrected statement, asserted positively and negatively."""
    text = G.norm(_decision("TD-B34")["decision"])
    assert "td-b40 residual (b) is itself complete" in text
    assert "td-b34 neither inherits nor reopens td-b40(b)" in text
    assert "td-b34 remains open and blocking on replication depth alone" in text
    assert "nothing recorded here closes td-b34" in text
    for stale in ("whose independent re-approval remains outstanding",
                  "whose independent re-approval is still outstanding",
                  "re-approval remains outstanding",
                  "re-approval is still outstanding",
                  "re-approval remains pending",
                  "still requires independent re-approval"):
        assert stale not in text, f"the TD-B34 row reintroduced {stale!r}"


def test_e5_the_csv_and_the_markdown_registry_agree_on_td_b34_versus_td_b40():
    """PART E.5 — the two registry renderings must not drift apart.

    Both must scope the `PT07` package approval as excluding the migration, both
    must record the `TD-B40(B)` re-approval as completed and propagated, and
    neither may claim it is outstanding.
    """
    csv_text = G.norm(_decision("TD-B34")["decision"])
    md_row = G.find_passage("docs/v2/OPEN_DECISIONS.md", "decision b (re-scoped)")
    for text, name in ((csv_text, "OPEN_DECISIONS.csv"), (md_row.flat, "OPEN_DECISIONS.md")):
        assert "the approval covers the pt07 package only" in text, name
        assert "eight other private packages" in text, name
        assert "td-b40 residual (b)" in text, name
        assert re.search(r"which is what (?:lets|allows) td-b40", text), name
        assert "closed by propagating that already-completed" in text, name
        assert "td-b34 therefore remains open and blocking" in text, name
        for stale in ("remains outstanding", "is still outstanding", "remains pending",
                      "is still pending", "still requires independent re-approval"):
            assert stale not in text, f"{name} still claims: {stale!r}"


def test_e6_the_readme_stale_sentence_is_structurally_historical():
    """PART E.6 — kept, and marked with the established convention."""
    passage = G.find_passage(
        "docs/v2/README.md",
        "that migration's independent re-approval was still outstanding",
    )
    assert passage.kind == "list-item"
    assert "as recorded then" in passage.flat, (
        "the README's stale sentence lost its historical marker and now reads as a "
        "live claim"
    )
    assert _marked_historical(passage)
    # and the unmarked live form is gone from the file entirely
    flat = G.norm(README.read_text(encoding="utf-8"))
    assert "whose independent re-approval is still outstanding" not in flat
    assert "whose independent re-approval remains outstanding" not in flat


def test_e7_the_readme_clarification_points_at_td_b40_closure():
    """PART E.7 — the forward pointer, in the same passage as the history."""
    passage = G.find_passage(
        "docs/v2/README.md",
        "that migration's independent re-approval was still outstanding",
    )
    for forward in ("it has since been independently re-approved",
                    "that re-approval is now propagated",
                    "td-b40 is now resolved",
                    "history, not current governance",
                    "see the migration-reapproval section below",
                    "everything closure does not confer",
                    "package approval and migration re-approval remain different facts",
                    "neither is a freeze"):
        assert forward in passage.flat, f"the clarification does not state: {forward!r}"
    # the section it points at exists and records the closure
    closure = G.norm(README.read_text(encoding="utf-8"))
    assert "migration re-approval propagated, td-b40 closed" in closure
    assert "td-b40 is resolved and closed, and closure is bounded" in closure


def test_e8_g1_is_not_passed():
    """PART E.8 — nothing in this correction passes a gate."""
    with open(GATE_MATRIX, newline="", encoding="utf-8") as fh:
        gates = {r["gate_id"]: r["status"].strip().lower() for r in csv.DictReader(fh)}
    assert "not evaluated" in gates["G1"], gates["G1"]
    assert "passed" not in gates["G1"]
    for gate_id, status in gates.items():
        assert "passed" not in status, f"{gate_id} is marked passed"
    assert "PRE-FREEZE" in README.read_text(encoding="utf-8")


def test_e9_cand_a1_remains_unauthored():
    """PART E.9 — still a candidate, still not finally approved."""
    record = G.norm(RECORD_PATH.read_text(encoding="utf-8"))
    assert "authoring state | not yet authored" in record.replace("  ", " ")
    assert "closing the four p1 findings is remediation, not approval" in record
    with open(TASK_INDEX, newline="", encoding="utf-8") as fh:
        ids = [r["task_id"] for r in csv.DictReader(fh)]
    assert len(ids) == 9, f"the index must still hold nine tasks, not {len(ids)}"
    assert "CAND-A1" not in ",".join(ids)
    assert "no pt08 identifier is assigned" in G.norm(_decision("TD-B34")["decision"])


def test_e10_no_pt08_exists_anywhere_public():
    """PART E.10 — no identifier, no body, no row, and no affirmative mention.

    Every sentence in every governed document that names ``PT08`` must deny it.
    An added entry — an index row, a matrix row, a "PT08 is authored" sentence —
    is an affirmative mention and fails here even if it never reaches the index.
    """
    with open(TASK_INDEX, newline="", encoding="utf-8") as fh:
        ids = [r["task_id"] for r in csv.DictReader(fh)]
    assert "PT08" not in ids
    assert not (TASK_INDEX.parent / "PT08.md").exists()
    bodies = sorted(p.stem for p in TASK_INDEX.parent.glob("PT*.md"))
    assert bodies == [f"PT0{i}" for i in range(1, 8)], (
        f"the public task bodies changed: {bodies}"
    )
    affirmative = []
    for rel in G.governed_files():
        for sentence in _sentences(G.norm((REPO / rel).read_text(encoding="utf-8"))):
            if "pt08" in sentence and "no pt08" not in sentence:
                affirmative.append(f"{rel}: {sentence[:160]!r}")
    assert affirmative == [], (
        "a governed document mentions PT08 without denying it:\n  - "
        + "\n  - ".join(affirmative)
    )
