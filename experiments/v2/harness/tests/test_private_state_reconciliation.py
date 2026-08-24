"""Governance tests pinning the public record's account of the private state.

An independent review found the public governance asserting several things about
the private evaluator repository that authorised private work had already made
false: that only two decision clusters were active, that ``api → core`` /
``AR-DEP-005`` were unrepresented, that ``PT07`` had no private evaluator package
at all, and that the preservation-only opportunities were still physically present
as active rows. Each was corrected; this module makes each correction
**load-bearing**, so restoring any of the stale claims fails the suite.

The assertions here read the **public** record only. They deliberately do not read
private file content: a public test that depended on private bytes would recreate
the coupling problem it exists to police, and the reconciliation itself was a
one-off read-only governance act, not a standing dependency.

A later authorised private package propagated a further true fact: ``PT07``'s
private evaluator package has been **independently reviewed and APPROVED** in an
external read-only review. Recording that exposed a defect in this module's own
guard, which had bundled "not approved" together with "not frozen" in one test, so
the true statement could not be recorded without weakening the freeze guard. The
two are now **four independent facts** (section 2b), mutation-tested in both
directions.

Two things this module is careful **not** to do:

* it does not claim ``PT07`` is **frozen**, that gate ``G1`` is passed, or that
  ``PT07`` is run-eligible. Package approval is none of those, and each is asserted
  separately from the approval so recording one can never relax another;
* it does not let ``TD-B40``'s closure widen. Both of that row's residuals have
  since completed — the reserve-row reconciliation **(A)**, now independently
  re-adjudicated inside the re-review's recorded scope, and the independent
  re-approval of the complete migration **(B)** — so the row is now **resolved**.
  Every assertion about it therefore comes in two halves: the fact that closed it,
  and the bound on what closure confers. Closure freezes no manifest, passes no
  gate (``G1`` included), activates no reserve, and resolves neither ``TD-B34`` nor
  ``TD-B39``; package approval and migration re-approval remain different facts
  even now that both exist.

Pure file inspection; no model is invoked.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"
PUBLIC_TASKS = REPO / "experiments" / "v2" / "tasks" / "public"

DECISIONS_CSV = DOCS_V2 / "OPEN_DECISIONS.csv"
DECISIONS_MD = DOCS_V2 / "OPEN_DECISIONS.md"
REPORT_PATH = PUBLIC_TASKS / "TASK_AUTHORING_REPORT.md"
POLICY_PATH = DOCS_V2 / "TASK_AUTHORING_POLICY.md"
FEASIBILITY_PATH = DOCS_V2 / "DEPENDENCY_TASK_FEASIBILITY.md"
TRACE_PATH = DOCS_V2 / "ORACLE_TRACEABILITY.csv"
MATRIX_PATH = DOCS_V2 / "PILOT_PUBLIC_TASK_MATRIX.csv"
RULE_MATRIX = DOCS_V2 / "TASK_RULE_MATRIX.csv"
LAYER_MATRIX = DOCS_V2 / "TASK_LAYER_MATRIX.csv"
ACCEPTANCE_MATRIX = DOCS_V2 / "TASK_ACCEPTANCE_MATRIX.csv"
DOCS_README = DOCS_V2 / "README.md"

#: Every public artifact that talks about the private state. Scanned wholesale for
#: the withdrawn claims, because a stale claim is a defect wherever it appears.
GOVERNANCE_FILES = (
    DECISIONS_CSV,
    DECISIONS_MD,
    REPORT_PATH,
    POLICY_PATH,
    FEASIBILITY_PATH,
    TRACE_PATH,
    MATRIX_PATH,
    RULE_MATRIX,
    LAYER_MATRIX,
    ACCEPTANCE_MATRIX,
    DOCS_README,
    DOCS_V2 / "HIDDEN_EVALUATOR_BOUNDARY.md",
    DOCS_V2 / "STATISTICAL_ANALYSIS_PLAN.md",
    DOCS_V2 / "PILOT_AND_POWER_POLICY.md",
)

SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".nx", ".pytest_cache", "dist", "coverage"}

#: The historical private HEAD the withdrawn test pinned. No public artifact may
#: pin a private revision again: the private repository is a live review
#: repository and a pin guarantees a false failure at the next authorised commit.
SUPERSEDED_PRIVATE_HEAD = "cffc095b74e2a1c04b92c34ead19871397427329"


def _norm(raw: str) -> str:
    raw = raw.replace("*", "").replace("`", "")
    raw = re.sub(r"(?m)^\s*>\s?", "", raw)
    return re.sub(r"\s+", " ", raw).strip().lower()


def _flat(path: Path) -> str:
    return _norm(path.read_text(encoding="utf-8"))


def _rows(path: Path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _by_id(path: Path, key: str = "task_id"):
    return {r[key]: r for r in _rows(path)}


def _decision(decision_id: str) -> dict[str, str]:
    return _by_id(DECISIONS_CSV, "decision_id")[decision_id]


# --------------------------------------------------------------------------- 1
# TD-B40: re-scoped, still open, and no longer asserting false active-set facts.


def test_td_b40_is_closed_only_because_both_residuals_completed():
    """A closed row must earn its closure and must carry the bound on it.

    Earlier this test asserted `TD-B40` **open**, which was correct while a
    residual survived. Both residuals have since completed — the inactive-reserve
    reconciliation, and the independent re-approval of the complete migration — so
    the row is closed. Closure is only safe if it is bounded, so the row must state
    that both residuals are complete AND that closure confers nothing.
    """
    row = _decision("TD-B40")
    assert row["blocking"] == "yes", (
        "the row's blocking NATURE does not change when its status resolves"
    )
    assert row["status"].strip().lower() == "resolved"
    text = _norm(row["decision"])
    assert "resolved / closed" in text
    assert "both residuals of the re-scoped row are complete" in text
    assert "no longer a blocking gate" in text
    # both residuals, named complete
    assert "residual (a) inactive-reserve re-authoring / reconciliation - complete" in text
    assert "residual (b) independent re-approval of the complete migration - complete" in text
    # and the bound on closure, stated in the row itself
    for denial in ("freezes no manifest", "passes no gate including g1",
                   "makes no experiment run-ready",
                   "activates neither pr01 nor pr02",
                   "resolves neither td-b34 nor td-b39",
                   "td-b40 never governed freeze"):
        assert denial in text, f"the row does not deny: {denial!r}"


def test_closing_td_b40_leaves_the_blockers_that_actually_gate_freeze_open():
    """The register must not have quietly closed anything alongside it."""
    for still_open in ("TD-B05", "TD-B14", "TD-B32", "TD-B34", "TD-B39"):
        row = _decision(still_open)
        assert row["status"].strip().lower() == "open", (
            f"{still_open} must stay open; TD-B40's closure governs only the "
            f"migration and its re-approval"
        )


def test_td_b40_no_longer_claims_api_core_is_unrepresented():
    """The exact false fact the review flagged, pinned as withdrawn."""
    text = _norm(_decision("TD-B40")["decision"])
    assert "are not unrepresented" in text, (
        "TD-B40 must explicitly withdraw the claim that api -> core / AR-DEP-005 "
        "are unrepresented in the active set"
    )
    for stale in (
        "leaf rule are therefore currently unrepresented",
        "are currently unrepresented",
        "spanning only two distinct decision clusters",
    ):
        assert stale not in text, f"TD-B40 still asserts a withdrawn fact: {stale!r}"


def test_td_b40_records_the_active_set_migration_as_discharged():
    text = _norm(_decision("TD-B40")["decision"])
    assert "no longer in the active e1 set" in text, (
        "TD-B40 must record that the ordered removal has been performed"
    )
    assert "none counts toward any e1 denominator" in text
    assert "superseded" in text and "auditable" in text, (
        "the removal was auditable supersession, not silent deletion; say so"
    )


def test_td_b40_closure_names_exactly_the_two_residuals_it_discharged():
    """Not a quietly widened closure: the row closes what it scoped, and no more."""
    text = _norm(_decision("TD-B40")["decision"])
    assert "re-scoped" in text
    # (A) inactive reserves — discharged, and still not activated
    assert "inactive-reserve re-authoring / reconciliation - complete" in text
    assert "pr01 and pr02" in text
    assert "independently re-adjudicated" in text
    assert "no such decision exists" in text, (
        "closure must restate that no reserve-activation decision exists"
    )
    # (B) the migration is now independently re-approved, propagated not performed
    assert "independent re-approval of the complete migration - complete" in text
    assert "external independent read-only" in text
    assert "p1-j1 and p1-j2" in text
    assert "no new p0 and no new p1" in text
    assert "migration state unchanged" in text
    assert "fails closed" in text
    assert "precedes the commits that record it" in text
    assert "propagate that result and neither performs it" in text
    assert "none is claimed" in text
    # closure rationale, and the coverage deficiency still owned by TD-B34
    assert "closure rationale" in text
    assert "replication depth" in text and "td-b34" in text
    # the historical record is not tidied away by closing the row
    assert "historical record preserved" in text


def test_td_b40_narrative_and_registry_agree():
    md = _flat(DECISIONS_MD)
    assert "resolved / closed" in md
    assert "both residuals complete" in md
    assert "now withdrawn as false" in md, (
        "the narrative row must mark the old active-set facts as withdrawn"
    )
    assert "all three clusters represented" in md
    assert "spanning only two distinct clusters" not in md, (
        "the narrative row still carries the withdrawn two-cluster claim"
    )
    # the narrative must carry the same bound on closure as the CSV row
    for denial in ("freezes no manifest", "passes no gate (g1 included)",
                   "activates neither pr01 nor pr02",
                   "resolves neither td-b34 nor td-b39",
                   "td-b40 never governed freeze"):
        assert denial in md, f"the narrative registry does not deny: {denial!r}"


@pytest.mark.parametrize("path", GOVERNANCE_FILES, ids=lambda p: p.name)
def test_no_governance_file_still_asserts_the_two_cluster_active_set(path):
    """Three clusters are active; the two-cluster statement may only be history."""
    flat = _flat(path)
    for match in re.finditer(r"spanning only two distinct (?:decision )?clusters", flat):
        window = flat[max(0, match.start() - 400) : match.end() + 400]
        assert any(
            marker in window
            for marker in ("at that time", "superseded", "withdrawn", "as recorded then", "were ")
        ), f"{path.name} asserts a two-cluster active set as current fact"


@pytest.mark.parametrize("path", GOVERNANCE_FILES, ids=lambda p: p.name)
def test_no_governance_file_says_ar_dep_005_is_currently_unrepresented(path):
    flat = _flat(path)
    assert "currently unrepresented" not in flat, (
        f"{path.name} still says a boundary is currently unrepresented; "
        "api -> core / AR-DEP-005 is represented in the active set"
    )


# --------------------------------------------------------------------------- 2
# PT07: the private package exists, and is neither frozen nor approved.


#: Claims the private state has made false. None may reappear anywhere public.
WITHDRAWN_PT07_CLAIMS = (
    "pt07 has no private evaluator package",
    "no private evaluator package at all",
    "no private evaluator package exists for it",
    "pt07's private package is not yet authored",
    "pt07's private evaluator package has not been authored",
    "not yet authored for pt07",
)


@pytest.mark.parametrize("claim", WITHDRAWN_PT07_CLAIMS)
def test_no_public_artifact_still_says_pt07_has_no_private_package(claim):
    offenders = []
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".csv", ".yml", ".yaml", ".json"}:
            continue
        if SKIP_DIRS & set(path.relative_to(REPO).parts):
            continue
        if claim in _flat(path):
            offenders.append(path.relative_to(REPO).as_posix())
    assert not offenders, (
        f"PT07's private evaluator package has been authored; {claim!r} is stale in: "
        f"{offenders}"
    )


# --------------------------------------------------------------------------- 2b
# PT07's lifecycle, as FOUR INDEPENDENT FACTS.
#
# The withdrawn single test conflated two different things: that PT07 had not been
# approved, and that PT07 was not frozen. That made a legitimate lifecycle
# transition impossible - recording the external independent approval of the
# private package would have had to weaken the freeze guard along with it, or the
# freeze guard would have blocked a true statement.
#
# They are separated below so each fact can be asserted, and can fail, on its own:
#
#   FACT 1  PT07 HAS been independently reviewed and approved.
#   FACT 2  PT07 is NOT frozen.
#   FACT 3  Gate G1 is NOT passed.
#   FACT 4  PT07 is NOT yet actual-run E1 eligible.
#
# test_the_four_pt07_facts_are_independently_guarded mutation-tests both
# directions: removing the approval must fail FACT 1 and leave FACT 2 intact, and
# falsely marking PT07 frozen must fail FACT 2 and leave FACT 1 intact.
# --------------------------------------------------------------------------- #

#: Where each fact is asserted. Keyed so the mutation test can address one fact.
_PT07_REASON = lambda: _norm(_by_id(MATRIX_PATH)["PT07"]["e1_eligibility_reason"])


def test_fact_1_pt07_has_been_independently_reviewed_and_approved():
    """The approval is a POSITIVE claim and must be recorded as one.

    Recording it is what makes the public record true after the private lifecycle
    propagation. It says nothing about freeze - see FACT 2.
    """
    reason = _PT07_REASON()
    assert "independently reviewed and approved" in reason, (
        "the public record must state that PT07's private package has been "
        "independently reviewed and approved"
    )
    assert "external read-only" in reason
    assert "verdict approve" in reason
    assert "p0=0 p1=0 p2=6" in reason
    assert "propagated into the private governance record" in reason
    # and the withdrawn claim is gone
    assert "not independently reviewed" not in reason, (
        "PT07's private package HAS been independently reviewed; that claim is stale"
    )
    # the same fact reaches the decision registry and the authoring report
    b34 = _norm(_decision("TD-B34")["decision"])
    assert "independently reviewed and approved" in b34
    assert "p2=6" in b34
    report = _flat(REPORT_PATH)
    assert "independently reviewed and approved" in report


def test_fact_1b_the_approval_provenance_is_not_fabricated():
    """No reviewer identity, URL or timestamp was supplied, so none is claimed."""
    b34 = _norm(_decision("TD-B34")["decision"])
    assert "no reviewer identity, external url or timestamp was supplied and none " \
           "is claimed" in b34
    assert "review event precedes the commit that records it" in b34 or (
        "review was an external read-only review supplied to the governance process"
        in b34
    )
    report = _flat(REPORT_PATH)
    assert "no reviewer identity, external url or timestamp was supplied and none " \
           "is claimed" in report


def test_fact_2_pt07_is_not_frozen():
    """Independent of FACT 1: approval is not a freeze.

    Nothing that records the approval may make this assertion pass, and nothing
    that removes the approval may make it fail.
    """
    reason = _PT07_REASON()
    assert "not_yet_frozen" in reason
    assert "pre-freeze" in reason
    assert "not a freeze" in reason, (
        "the record must say explicitly that package approval is not a freeze"
    )
    for path in (RULE_MATRIX, LAYER_MATRIX, ACCEPTANCE_MATRIX):
        assert _by_id(path)["PT07"]["status"] == "candidate-not-frozen", path.name
    assert _by_id(MATRIX_PATH)["PT07"]["task_status"] == "candidate"
    b34 = _norm(_decision("TD-B34")["decision"])
    assert "is not frozen" in b34
    assert _flat(REPORT_PATH).count("not frozen") >= 1


def test_fact_3_gate_g1_is_not_passed():
    reason = _PT07_REASON()
    assert "gate g1 is not passed" in reason
    b34 = _norm(_decision("TD-B34")["decision"])
    assert "gate g1 is not passed" in b34
    assert "not a gate pass" in b34
    assert "gate g1 is not passed" in _flat(REPORT_PATH)


def test_fact_4_pt07_is_not_yet_actual_run_e1_eligible():
    reason = _PT07_REASON()
    assert "not yet enterable into e1" in reason
    assert "not yet e1 run-eligible" in reason
    assert "before any run" in reason
    b34 = _norm(_decision("TD-B34")["decision"])
    assert "not yet eligible for an actual e1 run" in b34
    # no result artifact exists to be run against, either
    for directory in (
        REPO / "experiments" / "v2" / "results",
        REPO / "experiments" / "v2" / "analysis",
    ):
        stray = [p.name for p in directory.iterdir() if p.name != "README.md"]
        assert not stray, f"{directory.name}/ holds a result artifact: {stray}"


def test_the_four_pt07_facts_are_independently_guarded():
    """MUTATION PROOF, both directions, over the real artifact text.

    A future legitimate lifecycle transition must be able to record approval
    WITHOUT weakening the freeze guard, and must not be able to record a freeze by
    recording approval. Each direction is checked by mutating the actual reason
    string and asserting that exactly the intended fact's assertions break.
    """
    reason = _PT07_REASON()

    def approval_holds(text: str) -> bool:
        return (
            "independently reviewed and approved" in text
            and "not independently reviewed" not in text
        )

    def freeze_guard_holds(text: str) -> bool:
        return (
            "not_yet_frozen" in text
            and "pre-freeze" in text
            and "not a freeze" in text
        )

    # the live record satisfies both
    assert approval_holds(reason) and freeze_guard_holds(reason)

    # MUTATION A: withdraw the approval. FACT 1 must break; FACT 2 must not.
    withdrawn = reason.replace(
        "independently reviewed and approved", "not independently reviewed"
    )
    assert not approval_holds(withdrawn), "removing the approval was not caught"
    assert freeze_guard_holds(withdrawn), (
        "removing the approval also broke the freeze guard; the two facts are "
        "still coupled"
    )

    # MUTATION B: falsely mark PT07 frozen. FACT 2 must break; FACT 1 must not.
    frozen = (
        reason.replace("not_yet_frozen", "frozen")
        .replace("pre-freeze", "frozen")
        .replace("not a freeze", "a freeze")
    )
    assert not freeze_guard_holds(frozen), "falsely marking PT07 frozen was not caught"
    assert approval_holds(frozen), (
        "falsely marking PT07 frozen also broke the approval fact; the two facts "
        "are still coupled"
    )


def test_td_b34_records_pt07s_package_accurately():
    text = _norm(_decision("TD-B34")["decision"])
    assert "has now been authored" in text, (
        "TD-B34 must record that PT07's private package now exists"
    )
    assert "is withdrawn as stale" in text
    assert "not frozen" in text, "TD-B34 must not imply the package is frozen"
    assert "gate g1 is not passed" in text
    assert "still cannot enter e1" in text
    # The MIGRATION's independent re-approval is a different fact from the
    # PACKAGE's approval, and TD-B34 must not let the second stand in for the first.
    assert "td-b40 residual (b)" in text
    assert "does not cover the opportunity migration" in text


# --------------------------------------------------------------------------- #
# The authoring report's reconciliation, SECTION-SCOPED.
#
# The withdrawn version of this test was a document-wide grep for four short
# phrases. An independent review showed that the specific reconciliation sentence
# could be changed - or removed outright - while some other occurrence elsewhere in
# a 1000-line report kept every assertion green. The phrases are also exactly the
# ones a supersession note legitimately quotes as history, so a whole-document
# search cannot tell a live claim from a withdrawn one.
#
# The assertions below are bound to the ONE section that carries the PT07 private
# reconciliation. A discussion anywhere else in the report cannot satisfy them, and
# the section-resolution helper fails if that section is renamed away or duplicated.
# --------------------------------------------------------------------------- #
_HEADING_RE = re.compile(r"(?m)^(#{1,6})[ \t]+(.+?)[ \t]*$")

#: The section that must carry the reconciliation. Scoping to it is the point.
RECONCILIATION_SECTION = "private evaluator consequences"


def _sections(path: Path) -> dict[str, str]:
    """Each markdown heading mapped to its body, ending at the next same-or-higher."""
    text = path.read_text(encoding="utf-8")
    heads = list(_HEADING_RE.finditer(text))
    out: dict[str, str] = {}
    for i, head in enumerate(heads):
        level = len(head.group(1))
        end = len(text)
        for nxt in heads[i + 1 :]:
            if len(nxt.group(1)) <= level:
                end = nxt.start()
                break
        out[_norm(head.group(2))] = text[head.end() : end]
    return out


def _section_starting_with(path: Path, prefix: str) -> str:
    matches = {k: v for k, v in _sections(path).items() if k.startswith(prefix.lower())}
    assert len(matches) == 1, (
        f"{path.name} must carry exactly one section headed {prefix!r}, found "
        f"{sorted(matches)}"
    )
    return next(iter(matches.values()))


def _reconciliation_section() -> str:
    return _norm(_section_starting_with(REPORT_PATH, RECONCILIATION_SECTION))


def test_the_reconciliation_section_exists_and_is_unique():
    """If the section can be renamed away, everything below becomes vacuous."""
    body = _reconciliation_section()
    assert body, "the private-evaluator reconciliation section is empty"
    assert "pt07" in body


def test_the_reconciliation_section_says_the_private_package_EXISTS():
    """Catches a false 'no private package' claim IN THIS SECTION."""
    body = _reconciliation_section()
    assert "has since been authored" in body, (
        "the reconciliation section must record that PT07's private package exists"
    )
    assert "withdrawn as stale" in body
    for stale in WITHDRAWN_PT07_CLAIMS:
        # the section may recount the withdrawn bullet, but only as withdrawn
        if stale in body:
            i = body.index(stale)
            window = body[max(0, i - 400) : i + len(stale) + 400]
            assert "withdrawn as stale" in window, (
                f"the reconciliation section asserts {stale!r} as current fact"
            )


def test_the_reconciliation_section_says_the_package_WAS_reviewed_and_approved():
    """Catches a false 'never independently reviewed' claim IN THIS SECTION."""
    body = _reconciliation_section()
    assert "independently reviewed and approved" in body, (
        "the reconciliation section must record the external independent approval"
    )
    assert "read-only" in body
    assert "verdict approve" in body
    assert "p2 = 6" in body or "p2=6" in body
    assert "propagated into the private governance record" in body
    # the withdrawn "not independently reviewed" claim may appear ONLY as withdrawn
    for match in re.finditer(r"not independently reviewed", body):
        window = body[max(0, match.start() - 400) : match.end() + 400]
        assert "withdrawn as stale" in window, (
            "the reconciliation section still asserts that PT07's private package "
            "was never independently reviewed"
        )


def test_the_reconciliation_section_says_the_package_is_NOT_frozen():
    """The freeze guard, in the same section, independent of the approval."""
    body = _reconciliation_section()
    assert "not frozen" in body
    assert "status=review" in body
    assert "gate g1 is not passed" in body
    assert "not yet eligible for an actual e1 run" in body
    assert "approval is not a freeze and not a gate pass" in body
    assert "freezing remains a separate" in body


def test_the_reconciliation_section_keeps_package_approval_apart_from_the_migration():
    body = _reconciliation_section()
    assert "the approval is narrow" in body
    assert "td-b40 residual (b)" in body
    assert "remain review_required" in body


def test_the_report_guard_is_section_scoped_not_document_wide():
    """Guard the guard: the section must be load-bearing.

    If these assertions were satisfiable from the rest of the report, deleting the
    section's own sentences would still pass - which is precisely the defect the
    review found. Removing the reconciliation text from the section must break the
    checks even though the phrases still occur elsewhere in the document.
    """
    body = _reconciliation_section()
    whole = _flat(REPORT_PATH)
    for phrase in ("has since been authored", "independently reviewed and approved",
                   "approval is not a freeze and not a gate pass"):
        assert phrase in body, phrase
        # the phrase also occurs elsewhere in the report, which is exactly why a
        # document-wide grep could not have caught its removal from the section
        assert whole.count(phrase) >= 1
    stripped = whole.replace(body, "")
    # the section really is a proper subset of the document, so scoping is real
    assert len(stripped) < len(whole)
    assert body not in stripped


def test_the_public_registries_record_pt07_like_every_other_candidate():
    """The package exists, so PT07's rows carry the same withheld placeholder."""
    assert _by_id(MATRIX_PATH)["PT07"]["hidden_evaluator_manifest_hash"] == (
        "stored_in_private_evaluator_repo"
    )
    for path in (RULE_MATRIX, LAYER_MATRIX, ACCEPTANCE_MATRIX):
        values = ",".join(_by_id(path)["PT07"].values())
        assert "stored_in_private_evaluator_repo" in values, path.name
        assert "not_yet_authored" not in values, path.name


# --------------------------------------------------------------------------- 3
# No public artifact pins a private revision.


def test_no_public_artifact_pins_a_private_revision():
    """The brittle pin that broke on an authorised private commit must not return."""
    offenders = []
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".csv", ".yml", ".yaml", ".json", ".py"}:
            continue
        if SKIP_DIRS & set(path.relative_to(REPO).parts):
            continue
        if path == Path(__file__):
            continue
        if SUPERSEDED_PRIVATE_HEAD[:12] in path.read_text(encoding="utf-8", errors="ignore"):
            offenders.append(path.relative_to(REPO).as_posix())
    assert not offenders, (
        "a superseded private HEAD is pinned in the public repository; the private "
        f"repository is a live review repository and must not be pinned: {offenders}"
    )


def test_the_separation_invariant_is_expressed_as_no_mutation_not_as_a_pin():
    boundary_test = (
        REPO
        / "experiments"
        / "v2"
        / "harness"
        / "tests"
        / "test_functional_acceptance_boundary.py"
    ).read_text(encoding="utf-8")
    assert "def test_public_operations_do_not_mutate_the_private_evaluator_repository" in boundary_test
    assert "PRIVATE_HEAD =" not in boundary_test, (
        "the private-integrity check must not reintroduce a pinned revision"
    )
    for required in (
        "_public_read_only_operation()",
        "before = _private_head()",
        "after = _private_head()",
        "assert after == before",
        "_private_worktree_is_clean()",
    ):
        assert required in boundary_test, f"the before/after invariant is missing {required!r}"


# --------------------------------------------------------------------------- 4
# The feasibility record's own note agrees.


def test_the_feasibility_record_records_the_migration_as_performed():
    flat = _flat(FEASIBILITY_PATH)
    assert "has since been performed" in flat
    assert "physical removal from the private manifests is still outstanding" not in flat, (
        "the feasibility record still says the removal is outstanding"
    )
    assert "not yet re-approved" in flat or "outstanding independent re-approval" in flat, (
        "the residual re-approval must still be recorded"
    )


# --------------------------------------------------------------------------- 5
# No public artifact still says PT07's package was never independently reviewed.
#
# The mirror image of the "no private package" sweep above. The claim is now false,
# so it may survive only where it is explicitly marked withdrawn - which is what a
# supersession note legitimately does, and what this sweep must therefore tolerate
# while still catching a live restatement.
# --------------------------------------------------------------------------- #
#: Ways of saying "PT07's private package has never been independently reviewed".
WITHDRAWN_PT07_REVIEW_CLAIMS = (
    "pt07's private package has never been independently reviewed",
    "pt07's private evaluator package has never been independently reviewed",
    "never independently reviewed",
    "has not been independently reviewed",
    "not independently reviewed",
)

#: A marker within this many characters that turns the claim into recorded history.
_WITHDRAWN_WINDOW = 700
_WITHDRAWN_MARKERS = (
    "withdrawn as stale", "withdrawn", "superseded", "as recorded then",
    "no longer", "is stale", "historical",
)


@pytest.mark.parametrize("claim", WITHDRAWN_PT07_REVIEW_CLAIMS)
def test_no_public_artifact_asserts_pt07s_package_was_never_reviewed(claim):
    """Live restatements are caught; withdrawn quotations are allowed.

    Scoped to the artifacts that talk about PT07's private state, and to occurrences
    that sit in a PT07 context - the same sentence is a true statement about the
    MIGRATION (TD-B40 residual (B)) and about the other eight packages, so a blind
    repository sweep would be wrong.
    """
    offenders = []
    for path in GOVERNANCE_FILES:
        flat = _flat(path)
        for match in re.finditer(re.escape(claim), flat):
            window = flat[
                max(0, match.start() - _WITHDRAWN_WINDOW) : match.end() + _WITHDRAWN_WINDOW
            ]
            # only occurrences in a PT07 context are about PT07's package
            if "pt07" not in window:
                continue
            # the migration and the other packages genuinely are unreviewed
            if any(
                other in window
                for other in ("migration", "td-b40", "review_required",
                              "other private packages", "eight other")
            ):
                continue
            if not any(m in window for m in _WITHDRAWN_MARKERS):
                offenders.append((path.name, window[:200]))
    assert not offenders, (
        f"PT07's private package HAS been independently reviewed and approved; "
        f"{claim!r} is asserted as current fact in: {offenders}"
    )


def test_the_withdrawn_review_claim_is_marked_withdrawn_where_it_survives():
    """It must survive SOMEWHERE, marked, or the correction has no audit trail."""
    found = False
    for path in (DECISIONS_CSV, DECISIONS_MD, REPORT_PATH, DOCS_README):
        flat = _flat(path)
        for match in re.finditer(r"not been independently\s*reviewed|not independently reviewed", flat):
            window = flat[max(0, match.start() - 700) : match.end() + 700]
            if "pt07" in window and any(m in window for m in _WITHDRAWN_MARKERS):
                found = True
    assert found, (
        "the withdrawn 'not independently reviewed' claim about PT07 has been erased "
        "rather than marked withdrawn; the correction must leave an audit trail"
    )


# --------------------------------------------------------------------------- 6
# TD-B40's two residuals, tracked apart.
# --------------------------------------------------------------------------- #
def test_td_b40_residual_a_records_the_reserve_reconciliation_and_its_re_approval():
    text = _norm(_decision("TD-B40")["decision"])
    assert "inactive-reserve re-authoring / reconciliation - complete" in text
    assert "re-assessed every one of those rows under the current governance" in text
    assert "four rows were demoted" in text
    assert "one row survives as a" in text and "task-created reserve candidate" in text
    assert "bars it from ever entering an e1 denominator" in text
    assert "fourth decision cluster" in text
    assert "reserve denominator of 0" in text
    assert "td-b26" in text
    # the re-approval that discharged (A), and what it did NOT do
    assert "independently re-adjudicated" in text
    assert (
        "records the pr01/pr02 reserve reconciliation expressly inside its own scope"
        in text
    ), "the row must say WHY (A) is discharged, not merely that it is"
    assert "remain inactive-reserve" in text
    assert "no such decision exists" in text


def test_td_b40_residual_b_is_re_approved_and_still_confers_no_freeze():
    row = _decision("TD-B40")
    assert row["blocking"] == "yes"
    assert row["status"].strip().lower() == "resolved"
    text = _norm(row["decision"])
    assert "independent re-approval of the complete migration - complete" in text
    assert "td-b40(b) complete migration - independently re-approved" in text
    assert (
        "approve linkage remediation - td-b40(b) re-approved - replication review "
        "may begin" in text
    )
    assert "every manifest remains status=review and unfrozen" in text
    assert "passes no gate including g1" in text
    # the recorded scope must name every element the re-approval covered
    for item in ("six active-set supersessions", "five active opportunities",
                 "pr01/pr02 reserve reconciliation", "active cluster register",
                 "repaired cross-repository linkage"):
        assert item in text, f"the re-approval scope omits: {item!r}"
    # and the PT07 PACKAGE approval must still not be read as the migration's
    assert "package approval and migration re-approval remain" in text
    assert "different facts" in text
    assert "neither may be read off the other" in text
    assert "neither is a freeze" in text


def test_the_narrative_row_agrees_about_both_residuals():
    md = _flat(DECISIONS_MD)
    assert "residual (a) — inactive-reserve re-authoring / reconciliation: complete" in md
    assert "residual (b) — independent re-approval of the complete migration: complete" in md
    assert "permanently barred" in md or "bars it from ever entering" in md
    assert "fourth cluster" in md
    assert "package approval and migration re-approval remain different facts" in md
    assert "propagate" in md and "neither performs it" in md
    assert "none is claimed" in md


def test_td_b39_is_surfaced_as_recorded_privately_but_still_open():
    row = _decision("TD-B39")
    assert row["blocking"] == "yes"
    assert row["status"].strip().lower() == "open"
    md = _flat(DECISIONS_MD)
    assert "now surfaced privately, still not repaired" in md
    assert "eight legacy packages" in md
    assert "already conforming" in md
    assert "documentation-only" in md
    assert "td-b39 is not resolved" in md
