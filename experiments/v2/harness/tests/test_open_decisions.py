"""Cross-check the open-decisions registry.

Every ``TD-*`` reference anywhere in the v2 protocol must resolve to a row in
docs/v2/OPEN_DECISIONS.csv, every entry must have an owner and a valid blocking
flag, only the explicitly enumerated decisions in :data:`RESOLVED_IDS` may be
resolved (every other row must still be ``open``, and the Stage 0 blockers in
:data:`MUST_STAY_OPEN` are asserted open by name), and the counts must be exactly
41 blocking + 6 non-blocking (TD-B16..TD-B21 were added by the pre-execution design-review
reconciliation; TD-B22 by the independent public review of the pilot task
package; TD-B23..TD-B33 by the suite-classification decision that narrowed the
confirmatory construct to dependency-direction conformance; TD-B34..TD-B37 by the
pre-authoring opportunity reassessment that recorded DECISION B, reclassified
PT05 functional-only, isolated production-source scoring, and deferred the power
simulation; TD-B38 by the architecture-neutral-substrate review that found the
model-visible package metadata still announcing the experiment itself;
TD-B39..TD-B40 by the pre-authoring functional-evaluator boundary package that
defined the functional acceptance observation boundary and recorded that the
reassessment's preservation-only opportunities had not yet been migrated out of the
private manifests (TD-B40 was then re-scoped to the residual inactive-reserve and
re-approval housekeeping that survives that migration, and is now RESOLVED because
both of those residuals completed - a closure that freezes nothing and passes no
gate); TD-B41 by the
remaining-leaf feasibility package that re-scoped TD-B34 to replication depth and
had to settle how a fixed, very small decision space is analysed at the realised
cluster count). Pure file inspection; no model is invoked.
"""
import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
REGISTRY = REPO / "docs" / "v2" / "OPEN_DECISIONS.csv"
SCAN_DIRS = [REPO / "docs" / "v2", REPO / "experiments" / "v2"]
TEXT_EXT = {".md", ".csv", ".json", ".yml", ".yaml", ".py"}
TD_RE = re.compile(r"TD-[BN][0-9]+")

#: The only decisions any package has resolved so far: the model-visible
#: architecture-comment remediation (TD-B23), the leakage audit that proves it
#: (TD-B24), the experiment-awareness remediation (TD-B38), and the opportunity
#: migration whose two residuals - the inactive-reserve reconciliation and the
#: independent re-approval of the complete migration - are both complete (TD-B40).
#: Enumerating them keeps the registry fail-closed — a blocker quietly flipped to
#: ``resolved`` still fails this suite.
RESOLVED_IDS = {"TD-B23", "TD-B24", "TD-B38", "TD-B40"}

#: What each resolved row must name as the evidence that closes it. A resolved row
#: with no closure evidence is an assertion, not a decision, so the requirement is
#: per row rather than one shared string: the three leakage/substrate remediations
#: are closed by a regression proof over committed fixtures, while TD-B40 is closed
#: by both residuals completing and by the propagated independent re-approval.
RESOLUTION_EVIDENCE = {
    "TD-B23": ("PROOF 10", "leakage_fixtures"),
    "TD-B24": ("PROOF 10",),
    "TD-B38": ("PROOF 11", "leakage_fixtures"),
    "TD-B40": ("INDEPENDENTLY RE-APPROVED", "P1-J1", "P1-J2"),
}

#: Blockers that must never be closed as a side effect of unrelated work. The
#: task-authoring blockers in particular gate Stage 0 and are not this package's
#: to resolve.
MUST_STAY_OPEN = {
    "TD-B34",  # DECISION B - more public architecture tasks before Stage 0
    "TD-B26",  # PR02 terminal-state criterion unreachable
    "TD-B31",  # suite-wide public-interface reachability validation
    "TD-B22",  # runner-time enforcement of the worktree policy
    "TD-B05",  # hidden acceptance criteria
    "TD-B14",  # private opportunity-set adequacy
    "TD-B39",  # hidden acceptance packages migrated onto the observation boundary
    "TD-B41",  # residual small-cluster (G = 3) analysis specification
}


def _referenced_ids():
    found = set()
    for base in SCAN_DIRS:
        for p in base.rglob("*"):
            if p.is_file() and p.suffix in TEXT_EXT and "__pycache__" not in p.parts:
                found.update(TD_RE.findall(p.read_text(encoding="utf-8", errors="ignore")))
    return found


def _registry_rows():
    with open(REGISTRY, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_registry_columns_and_integrity():
    rows = _registry_rows()
    assert rows, "empty registry"
    ids = [r["decision_id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate decision ids"
    for r in rows:
        assert r["blocking"] in {"yes", "no"}, r
        assert r["owner"].strip(), f"{r['decision_id']} has no owner"
        assert r["decision"].strip(), f"{r['decision_id']} has no decision text"
        status = r["status"].strip().lower()
        assert status in {"open", "resolved"}, f"{r['decision_id']} has status {status!r}"
        if r["decision_id"] in RESOLVED_IDS:
            assert status == "resolved", (
                f"{r['decision_id']} is recorded as resolved in RESOLVED_IDS but the "
                "registry still calls it open"
            )
        else:
            assert status == "open", (
                f"{r['decision_id']} must be open: this is a pre-freeze draft and only "
                f"{sorted(RESOLVED_IDS)} have been resolved"
            )


def test_task_authoring_and_runner_blockers_are_still_open():
    """Guard the guard: unrelated work must not quietly close a Stage 0 blocker."""
    by_id = {r["decision_id"]: r for r in _registry_rows()}
    for decision_id in sorted(MUST_STAY_OPEN):
        assert decision_id in by_id, f"{decision_id} vanished from the registry"
        assert by_id[decision_id]["status"].strip().lower() == "open", (
            f"{decision_id} must remain open"
        )
    assert not (MUST_STAY_OPEN & RESOLVED_IDS)


def test_resolved_decisions_record_what_was_done_and_how_it_is_proven():
    """A resolved row must carry its disposition and its closure evidence."""
    by_id = {r["decision_id"]: r for r in _registry_rows()}
    assert set(RESOLUTION_EVIDENCE) == RESOLVED_IDS, (
        "every resolved decision must declare what evidence closes it"
    )
    for decision_id in sorted(RESOLVED_IDS):
        text = by_id[decision_id]["decision"]
        assert text.strip().upper().startswith("RESOLVED"), (
            f"{decision_id} must state its resolution first"
        )
        for needle in RESOLUTION_EVIDENCE[decision_id]:
            assert needle in text, (
                f"{decision_id} must name the evidence that closes it: {needle!r}"
            )
    # TD-B23's disposition was a real choice between two options; record which.
    assert "NEUTRALISE" in by_id["TD-B23"]["decision"].upper(), (
        "TD-B23 offered neutralise-or-pre-register; the registry must say which was taken"
    )


def test_closing_td_b40_confers_no_freeze_and_no_gate_pass():
    """A closed row must carry the bound on its own closure.

    ``TD-B40`` is the first resolved row that is not a substrate remediation, and
    the risk it introduces is a reader taking "the migration row is closed" for
    "the migration is frozen" or "``G1`` is passed". The row must therefore state
    what closure does NOT do, must record that the re-approval was PROPAGATED
    rather than performed, and must not have quietly resolved the blockers that
    genuinely gate freeze.
    """
    by_id = {r["decision_id"]: r for r in _registry_rows()}
    text = by_id["TD-B40"]["decision"]
    for denial in (
        "FREEZES NO MANIFEST",
        "PASSES NO GATE INCLUDING G1",
        "MAKES NO EXPERIMENT RUN-READY",
        "ACTIVATES NEITHER PR01 NOR PR02",
        "RESOLVES NEITHER TD-B34 NOR TD-B39",
        "Every manifest remains status=review and unfrozen",
        "TD-B40 NEVER GOVERNED FREEZE",
    ):
        assert denial in text, f"the TD-B40 row does not deny: {denial!r}"
    # propagated, not performed, and with honest provenance
    assert "PRECEDES the commits that record it" in text
    assert "PROPAGATE that result and NEITHER PERFORMS IT" in text
    assert "NONE IS CLAIMED" in text, (
        "the row must state that no reviewer identity/URL/timestamp is claimed"
    )
    # both residuals named complete, and the standing constraints preserved
    assert "RESIDUAL (A) INACTIVE-RESERVE RE-AUTHORING / RECONCILIATION - COMPLETE" in text
    assert "RESIDUAL (B) INDEPENDENT RE-APPROVAL OF THE COMPLETE MIGRATION - COMPLETE" in text
    assert "NO SUCH DECISION EXISTS" in text, (
        "closure must not relax the reserve-activation requirement"
    )
    assert "PERMANENTLY BARRED" in text
    assert "HISTORICAL RECORD PRESERVED" in text
    # the blockers that actually gate freeze are untouched
    for still_open in ("TD-B05", "TD-B14", "TD-B32", "TD-B39"):
        assert by_id[still_open]["status"].strip().lower() == "open", (
            f"{still_open} gates freeze and must not close with TD-B40"
        )


def test_counts_are_41_blocking_6_nonblocking():
    rows = _registry_rows()
    blocking = [r["decision_id"] for r in rows if r["blocking"] == "yes"]
    nonblocking = [r["decision_id"] for r in rows if r["blocking"] == "no"]
    assert sorted(blocking) == [f"TD-B{i:02d}" for i in range(1, 42)], blocking
    assert sorted(nonblocking) == [f"TD-N{i:02d}" for i in range(1, 7)], nonblocking
    assert len(blocking) == 41 and len(nonblocking) == 6


def test_markdown_registry_counts_match_the_csv():
    """The narrative table and the machine-readable CSV must not drift apart."""
    md = (REPO / "docs" / "v2" / "OPEN_DECISIONS.md").read_text(encoding="utf-8")
    rows = _registry_rows()
    blocking = sum(1 for r in rows if r["blocking"] == "yes")
    nonblocking = len(rows) - blocking
    resolved = [r["decision_id"] for r in rows if r["status"].strip().lower() == "resolved"]
    assert f"Blocking decisions: {blocking}**" in md, "OPEN_DECISIONS.md blocking count drifted"
    assert f"Non-blocking decisions: {nonblocking}**" in md
    assert f"Total decisions: {len(rows)}**" in md
    assert f"**{len(resolved)} are resolved**" in md, "resolved count drifted"
    assert f"**{len(rows) - len(resolved)} remain open**" in md, "open count drifted"
    # every blocking id must appear in the prose table too
    for r in rows:
        assert r["decision_id"] in md, f"{r['decision_id']} missing from OPEN_DECISIONS.md"


def test_every_referenced_todo_is_registered():
    registry_ids = {r["decision_id"] for r in _registry_rows()}
    referenced = _referenced_ids()
    missing = referenced - registry_ids
    assert not missing, f"referenced TODOs with no registry row: {sorted(missing)}"
    # and every registered id is actually referenced somewhere (no dead rows)
    dead = registry_ids - referenced
    assert not dead, f"registry rows never referenced: {sorted(dead)}"
