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

Two things this module is careful **not** to do:

* it does not claim ``PT07`` is frozen or approved — the private package is
  ``status=review`` and unreviewed, and the public record must keep saying so;
* it does not close ``TD-B40`` — a genuine residual (inactive-reserve rows and the
  outstanding independent re-approval) survives the migration.

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


def test_td_b40_stays_open_and_blocking():
    """The residual is real, so the row must not be closed by this reconciliation."""
    row = _decision("TD-B40")
    assert row["blocking"] == "yes"
    assert row["status"].strip().lower() == "open"


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


def test_td_b40_is_re_scoped_to_the_genuine_residual_only():
    """Not a relabelled blocker: the row must name what actually remains."""
    text = _norm(_decision("TD-B40")["decision"])
    assert "re-scoped" in text
    # (A) inactive reserves
    assert "inactive-reserve housekeeping" in text
    assert "pr01 and pr02" in text
    assert "no reserve may be activated" in text
    # (B) the migration is performed but not yet independently approved
    assert "independent re-approval" in text
    assert "has not been independently reviewed" in text
    assert "no per-task manifest is frozen" in text
    # and the coverage deficiency is handed to the decision that actually owns it
    assert "replication depth" in text and "td-b34" in text


def test_td_b40_narrative_and_registry_agree():
    md = _flat(DECISIONS_MD)
    assert "re-scoped to the residual inactive-reserve and re-approval housekeeping" in md
    assert "now withdrawn as false" in md, (
        "the narrative row must mark the old active-set facts as withdrawn"
    )
    assert "all three clusters represented" in md
    assert "spanning only two distinct clusters" not in md, (
        "the narrative row still carries the withdrawn two-cluster claim"
    )


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


def test_pt07_is_never_described_as_frozen_or_approved():
    """Accuracy cuts both ways: authored is not validated, approved or frozen."""
    reason = _norm(_by_id(MATRIX_PATH)["PT07"]["e1_eligibility_reason"])
    assert "not_yet_frozen" in reason
    assert "not independently reviewed" in reason
    assert "pre-freeze" in reason
    for path in (RULE_MATRIX, LAYER_MATRIX, ACCEPTANCE_MATRIX):
        assert _by_id(path)["PT07"]["status"] == "candidate-not-frozen", path.name


def test_td_b34_records_pt07s_package_accurately():
    text = _norm(_decision("TD-B34")["decision"])
    assert "has now been authored" in text, (
        "TD-B34 must record that PT07's private package now exists"
    )
    assert "is withdrawn as stale" in text
    assert "not frozen" in text and "not been independently reviewed" in text, (
        "TD-B34 must not imply the authored package is approved"
    )
    assert "gate g1 is not passed" in text
    assert "still cannot enter e1" in text


def test_the_authoring_report_carries_the_same_reconciliation():
    report = _flat(REPORT_PATH)
    assert "has since been authored" in report
    assert "withdrawn as stale" in report
    assert "not frozen" in report and "not independently reviewed" in report


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
