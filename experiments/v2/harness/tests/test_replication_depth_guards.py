"""Fail-closed guards for the `TD-B34` replication-depth governance claims.

WHY THIS MODULE EXISTS
----------------------
An independent mutation review demonstrated that the existing governance
assertions for the `TD-B34` re-scope were **not load-bearing**, because they
relied on fixed-width character windows around a match:

* **P2-A — breadth supersession guards caught deletion but not insertion or
  inversion.** A brand-new *live* breadth directive could be inserted inside the
  historical `docs/v2/README.md` section, elsewhere in that README, or in
  `TASK_AUTHORING_REPORT.md`, and every test stayed green: the ±700-character
  window swept up supersession prose belonging to a *neighbouring* passage.
  Stripping the `HISTORICAL`/`SUPERSEDED` classification from the original README
  directive passed for the same reason, because nearby supersession prose rescued
  it.
* **P2-B — the fourth-cluster guard could be inverted.** Changing *"not a
  task-creatable fourth cluster"* to *"a task-creatable fourth cluster"* stayed
  green, because unrelated negations (`not`, `no`, `cannot`, `not task-creatable`)
  inside the same ±260-character window satisfied the denial pattern.

WHAT REPLACES THEM
------------------
:mod:`governance_text` supplies a **passage** model — one table row, one
blockquote run, one top-level list item with its continuations, one paragraph, or
one CSV field — and a **claim register** pinned by ``(file, heading, anchor)``,
where the anchor is a digest of that passage's own normalised text.

There is no character window anywhere in this module. Three independent
directions fail closed:

1. a governed phrase in an **unregistered** passage — anywhere in any governed
   document, including a file that did not exist before — fails;
2. **editing** a registered passage moves its anchor, so it becomes unregistered
   and fails. This is what makes both "insert a live directive into an
   already-marked historical passage" and "invert the denial in place"
   impossible;
3. a registered passage that **loses a required token** (its explicit historical
   classification, or the exact denial it exists to state) or **gains a forbidden
   token** (the inverted form of its own claim) fails.

The register is deliberately strict: a legitimate future edit to any historical
passage must be accompanied by an explicit register update, which is exactly the
governance property "nothing here is rewritten" asks for.

Pure text inspection. No model is invoked, no benchmark runs, nothing is frozen.
"""
from __future__ import annotations

import re

import pytest

import governance_text as G
from governance_text import RegisteredClaim as RC

MARKER = G.BREADTH_HISTORICAL_MARKER


# --------------------------------------------------------------------------- #
# PART 1 — the withdrawn `TD-B34` breadth objective (P2-A, P2-C)
#
# Every passage below is HISTORY. Each must carry the explicit marker
# `TD-B34-BREADTH-HISTORICAL` in its OWN text — an HTML comment in Markdown
# (invisible when rendered) or a bare token in a CSV field. A generic word such as
# "superseded" or "withdrawn" is deliberately NOT accepted as the classification:
# the mutation review showed such words are routinely present for unrelated
# reasons, and one of them ("withdrawn as stale", about a completely different
# statement) was already rescuing a live breadth claim in `docs/v2/README.md`.
# --------------------------------------------------------------------------- #
BREADTH_REGISTER = (
    RC(
        rel="docs/v2/CRITICAL_DESIGN_DECISIONS.md",
        heading="d8 scope narrowing (suite-classification decision d)",
        anchor="2924075b368ce237",
        why="D8's DECISION B bullet: the breadth reading is kept as history and the "
            "live reading is replication depth",
        required=(MARKER, "replication depth", "not missing breadth",
                  "requires no new leaf-rule or source-scope breadth"),
    ),
    RC(
        rel="docs/v2/OPEN_DECISIONS.md",
        heading="added by the pre-authoring opportunity reassessment — td-b34 – td-b37",
        anchor="26a989cc3a237e33",
        why="the re-scoped TD-B34 registry row quotes the original breadth objective; "
            "re-anchored when the row gained the CAND-A1 priority-A pre-authoring "
            "progress, which is progress toward REPLICATION DEPTH and must never be "
            "read as reviving the breadth objective",
        required=(MARKER, "is superseded and structurally unattainable",
                  "replication depth",
                  # the addendum is progress, not resolution, and not breadth
                  "priority-a pre-authoring progress, not resolution",
                  "td-b34 therefore remains open and blocking"),
        forbidden=("the breadth objective is restored",
                   "breadth is again required"),
    ),
    RC(
        rel="docs/v2/PILOT_AND_POWER_POLICY.md",
        heading="stage 0 — non-evidentiary technical dry runs",
        anchor="42b9f78d31d37a1b",
        why="the Stage-0 gate's withdrawn-directive blockquote",
        required=(MARKER, "withdrawn directive",
                  "scientifically obsolete and structurally unattainable"),
    ),
    RC(
        rel="docs/v2/README.md",
        heading="opportunity reassessment — pt05 reclassified, decision b recorded",
        anchor="3a21f17e1679ed0c",
        why="the aggregate-coverage bullet's 'not enough distinct decisions' claim, "
            "now explicitly historical with the live replication-depth reading",
        required=(MARKER, "not missing breadth", "replication depth"),
    ),
    RC(
        rel="docs/v2/README.md",
        heading="opportunity reassessment — pt05 reclassified, decision b recorded",
        anchor="e5ff30966e7f988c",
        why="the DECISION B bullet, preserved verbatim as 'as recorded then'",
        required=(MARKER, "as recorded then"),
    ),
    RC(
        rel="docs/v2/README.md",
        heading="opportunity reassessment — pt05 reclassified, decision b recorded",
        anchor="5c349508b67f7f07",
        why="the README supersession blockquote for the DECISION B directive",
        required=(MARKER, "historical", "superseded",
                  "not current governance", "must not be authored",
                  "withdrawn directive", "replication depth",
                  "3 decision clusters / 2 leaf rules / 2 source scopes / 3 forbidden targets",
                  "dependency_task_feasibility.md"),
    ),
    RC(
        rel="docs/v2/README.md",
        heading="opportunity reassessment — pt05 reclassified, decision b recorded",
        anchor="d490341de0098e80",
        why="the statistical-governance bullet's power precondition, 'as recorded then'",
        required=(MARKER, "as recorded then"),
    ),
    RC(
        rel="docs/v2/README.md",
        heading="opportunity reassessment — pt05 reclassified, decision b recorded",
        anchor="7f92fa30fb0c6f75",
        why="the README supersession blockquote for the power precondition",
        required=(MARKER, "historical", "superseded", "withdrawn",
                  "replication depth", "no power simulation has been run",
                  "no power value is frozen", "decision_cluster_id is mandatory"),
    ),
    RC(
        rel="docs/v2/README.md",
        heading="pt07 authored under decision b — one task, td-b34 still open",
        anchor="b39b4f95b738b381",
        why="the PT07 section's 'TD-B34 is NOT resolved' bullet, rewritten to "
            "replication depth with the breadth wording kept as history",
        required=(MARKER, "replication depth", "not missing breadth",
                  "historical", "superseded", "not current governance"),
    ),
    RC(
        rel="docs/v2/TASK_AUTHORING_POLICY.md",
        heading="12.2b the cleared candidate is now authored as pt07 (td-b34 still open)",
        anchor="2f2ec5b36801450f",
        why="P2-C: §12.2b's stale breadth sentence, retained only as marked history "
            "with a direct pointer to §12.2c",
        required=(MARKER, "historical", "superseded",
                  "not current governance", "must not be authored against",
                  "§12.2c", "dependency_task_feasibility.md",
                  "still open and blocking"),
    ),
    RC(
        rel="docs/v2/OPEN_DECISIONS.csv",
        heading="row TD-B34 / column decision",
        anchor="e5732339c5cec2de",
        why="the machine-readable TD-B34 row quotes the original breadth objective; "
            "re-anchored when the stale TD-B40(B) claim was corrected (P1-4). The row "
            "records progress toward REPLICATION DEPTH, which must never be read as "
            "reviving the breadth objective, and it must not inherit a residual that "
            "belongs to a decision now resolved",
        required=(MARKER, "as originally recorded",
                  "breadth objective is superseded and structurally unattainable",
                  "priority-a pre-authoring progress, not resolution",
                  "td-b34 therefore remains open and blocking",
                  # P1-4: the row states the residual's real state and does not
                  # inherit it, and replication depth stays the only live objective
                  "td-b40 residual (b) is itself complete",
                  "td-b34 neither inherits nor reopens td-b40(b)",
                  "td-b34 remains open and blocking on replication depth alone"),
        forbidden=("the breadth objective is restored",
                   "breadth is again required",
                   "re-approval remains outstanding",
                   "re-approval is still outstanding"),
    ),
    RC(
        rel="experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md",
        heading="four coverage categories, only one of which e1 measures",
        anchor="9661ca7ae57f7a7e",
        why="the coverage-category bullet, rewritten to replication depth with the "
            "breadth wording kept as history",
        required=(MARKER, "replication depth", "not missing breadth", "historical",
                  "superseded", "not current governance"),
    ),
    RC(
        rel="experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md",
        heading="aggregate construct coverage (no private content disclosed)",
        anchor="91f222d7ca74b68f",
        why="the aggregate-coverage bullet, rewritten to replication depth with the "
            "breadth wording kept as history",
        required=(MARKER, "replication depth", "not missing breadth", "historical",
                  "superseded", "not current governance"),
    ),
    RC(
        rel="experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md",
        heading="decision b - additional architecture tasks required before stage 0",
        anchor="a5b81cba9ff5b8e8",
        why="the report's DECISION B supersession blockquote",
        required=(MARKER, "historical record", "superseded",
                  "not current governance", "do not author against this section",
                  "withdrawn directive", "nothing here is rewritten",
                  "replication depth",
                  "3 decision clusters / 2 leaf rules / 2 source scopes / 3 forbidden targets"),
    ),
    RC(
        rel="experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md",
        heading="decision b - additional architecture tasks required before stage 0",
        anchor="b565debe21b5a4c8",
        why="the verbatim DECISION B directive, as originally recorded",
        required=(MARKER, "as originally recorded", "superseded"),
    ),
    RC(
        rel="experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md",
        heading="decision b - additional architecture tasks required before stage 0",
        anchor="8ca8bb1d4940717a",
        why="the DECISION B motivation paragraph: the motivation survives, the "
            "breadth remedy is superseded",
        required=(MARKER, "superseded", "section 12.2c", "replication depth"),
    ),
    RC(
        rel="experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md",
        heading="decision b - additional architecture tasks required before stage 0",
        anchor="c1caa04acc1906bc",
        why="the 'unused implemented leaf relationships already exist' reason",
        required=(MARKER, "superseded reason",
                  "the binding constraint is substrate feasibility"),
    ),
    RC(
        rel="experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md",
        heading="decision b / td-b34 remains open",
        anchor="9cd3fd43b0dab199",
        why="the report addendum's 'TD-B34 remains open' paragraph, kept as history "
            "next to the live replication-depth reading",
        required=(MARKER, "historical", "superseded", "not current governance"),
    ),
)


# --------------------------------------------------------------------------- #
# PART 2 — the fourth-cluster denials (P2-B)
#
# The demonstrated ceiling is THREE task-creatable clusters. Every passage that
# names a fourth (or larger) cluster is registered below with the EXACT sentence
# it must state. `forbidden` pins the polarity: each entry is the inverted form of
# that passage's own claim, chosen so that it cannot occur in the correct text.
# Nearby negations are irrelevant by construction — nothing here looks outside the
# passage.
# --------------------------------------------------------------------------- #
FOURTH_CLUSTER_REGISTER = (
    RC(
        rel="docs/v2/DEPENDENCY_TASK_FEASIBILITY.md",
        heading="3a. inactive-reserve draft rows do not contradict the ceiling",
        anchor="700c279f16638a24",
        why="§3a names the misreading it exists to refute, then refutes it",
        required=("or that a fourth decision cluster is available in reserve. "
                  "neither is the case",),
        forbidden=("a fourth decision cluster is available in reserve. that is the case",
                   "a fourth decision cluster is available in reserve. this is the case"),
    ),
    RC(
        rel="docs/v2/DEPENDENCY_TASK_FEASIBILITY.md",
        heading="3a. inactive-reserve draft rows do not contradict the ceiling",
        anchor="322ea7a0ae9d0644",
        why="THE load-bearing P2-B claim: the legacy infra -> core / AR-DEP-004 "
            "reserve row is not a fourth task-creatable cluster and is barred from E1",
        required=(
            "the legacy infra → core / ar-dep-004 reserve row is not evidence of a "
            "fourth task-creatable decision cluster, and it is permanently barred "
            "from e1",
            "it is therefore not a task-creatable fourth cluster",
            "permanently barred, not merely dormant",
            "cannot enter an e1 denominator on any future activation",
            "no coverage claim, power calculation or novelty assessment may treat it as one",
        ),
        forbidden=(
            "reserve row is evidence of a fourth task-creatable decision cluster",
            "it is therefore a task-creatable fourth cluster",
            "it is therefore an available fourth cluster",
        ),
    ),
    RC(
        rel="docs/v2/DEPENDENCY_TASK_FEASIBILITY.md",
        heading="6. disposition of the earlier provisional coverage targets",
        anchor="4a510a8980b15287",
        why="the superseded provisional target row: >= 4 clusters is not achievable",
        required=("≥ 4 independent decision clusters | not achievable — hard ceiling 3",),
        forbidden=("independent decision clusters | achievable",),
    ),
    RC(
        rel="docs/v2/OPEN_DECISIONS.md",
        heading="added by the pre-authoring functional-evaluator boundary package — td-b39 – td-b40",
        anchor="8df07ee7245b3dae",
        why="the TD-B40 registry row bars any legacy reserve row from being read as a "
            "fourth cluster; re-anchored when the row was resolved. A CLOSED row is "
            "the most dangerous place for this bar to weaken, so the closure text "
            "must carry both the bar and the full statement of what closure does not "
            "confer",
        required=("no legacy reserve row may be read as a task-creatable fourth cluster",
                  "5 opportunities across 3 clusters",
                  # closure is bounded: every denial pinned in the row itself
                  "freezes no manifest",
                  "passes no gate (g1 included)",
                  "activates neither pr01 nor pr02",
                  "resolves neither td-b34 nor td-b39",
                  "td-b40 never governed freeze",
                  "permanently barred"),
        forbidden=("is a task-creatable fourth cluster",
                   "a legacy reserve row may be read as a task-creatable fourth cluster",
                   # closure must never be readable as a freeze or a gate pass
                   "gate g1 is passed",
                   "the migration is frozen"),
    ),
    RC(
        rel="docs/v2/PILOT_AND_POWER_POLICY.md",
        heading="precondition on the power simulation (td-b37)",
        anchor="edfb0e83dff93f9e",
        why="a benign active-count statement; it must never acquire a fourth-cluster claim",
        required=("5 across 3 decision clusters", "replication depth"),
        forbidden=("fourth cluster", "fourth decision cluster", "4th cluster"),
    ),
    RC(
        rel="docs/v2/README.md",
        heading="pt07 authored under decision b — one task, td-b34 still open",
        anchor="5a483cb7850aa077",
        why="the README reserve-reconciliation bullet carries the same denial; "
            "re-anchored when the bullet recorded that the reconciliation has since "
            "been independently re-approved. The historical reading is kept as 'as "
            "recorded then' rather than rewritten",
        required=(
            "the legacy infra → core / ar-dep-004 reserve row is not evidence of a "
            "fourth task-creatable decision cluster, and it is permanently barred "
            "from e1",
            "it is not an available fourth cluster",
            "the active set is unchanged at 5 opportunities over 3 clusters",
            # the superseding fact, and the historical framing it replaces
            "as recorded then",
            "has since been independently re-approved",
        ),
        forbidden=(
            "reserve row is evidence of a fourth task-creatable decision cluster",
            "it is an available fourth cluster",
            "it is therefore a task-creatable fourth cluster",
        ),
    ),
    RC(
        rel="docs/v2/STATISTICAL_ANALYSIS_PLAN.md",
        heading="4a. the current architecture task set is not confirmatory-ready (td-b37)",
        anchor="84558259d7ba86b5",
        why="a benign active-count statement; it must never acquire a fourth-cluster claim",
        required=("5 across 3 decision clusters",),
        forbidden=("fourth cluster", "fourth decision cluster", "4th cluster"),
    ),
    RC(
        rel="docs/v2/TASK_AUTHORING_POLICY.md",
        heading="12.2a coverage of the surviving active set, and one candidate cleared for authoring",
        anchor="bcf23b64919cf2e4",
        why="§12.2a's reserve-reconciliation blockquote carries the authoring-bar "
            "denial; re-anchored when the blockquote recorded TD-B40's closure. The "
            "bar and the reserve denominator must survive that closure verbatim",
        required=("no legacy reserve row is a task-creatable fourth cluster",
                  "permanently barred", "the reserve denominator is 0",
                  # closure did not activate anything
                  "re-approval is not activation",
                  "no reserve may be activated yet",
                  "closure freezes nothing"),
        forbidden=("a legacy reserve row is a task-creatable fourth cluster",
                   "one legacy reserve row is a task-creatable fourth cluster",
                   "a reserve may now be activated"),
    ),
    RC(
        rel="docs/v2/TASK_AUTHORING_POLICY.md",
        heading="12.2d forcing strength, and the priority-a candidate's pre-authoring state",
        anchor="81fbc6e77ad77922",
        why="§12.2d's 'nothing is authored' paragraph states the counts CAND-A1 must "
            "not move. It names the active counts, so it is registered here to stop a "
            "pre-counted second observation being smuggled into it",
        required=("no pt08 identifier",
                  "the active set stays 5 opportunities over 3 clusters at depths "
                  "3 / 1 / 1",
                  "dc-features-api-ar-dep-006 stays at one observation",
                  "the candidate is not finally approved",
                  "td-b34 stays open and blocking"),
        forbidden=("dc-features-api-ar-dep-006 stays at two observations",
                   "at depths 3 / 2 / 1",
                   "6 opportunities over 3 clusters",
                   "5 opportunities over 4 clusters"),
    ),
    RC(
        rel="docs/v2/OPEN_DECISIONS.csv",
        heading="row TD-B40 / column decision",
        anchor="c5840696b992d2a8",
        why="the machine-readable TD-B40 row carries the same bar; re-anchored when "
            "the row was resolved. The CSV row is what a machine reader consumes, so "
            "the bar and the bound on closure must both live in it",
        required=("no legacy reserve row may be read as a task-creatable fourth "
                  "decision cluster",
                  "5 opportunities across 3 decision clusters",
                  "freezes no manifest",
                  "passes no gate including g1",
                  "activates neither pr01 nor pr02",
                  "resolves neither td-b34 nor td-b39",
                  "td-b40 never governed freeze",
                  "no such decision exists"),
        forbidden=("is a task-creatable fourth decision cluster",
                   "gate g1 is passed",
                   "the migration is frozen"),
    ),
    RC(
        rel="experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md",
        heading="private evaluator consequences (nothing private was touched)",
        anchor="1401bb7d249e9d29",
        why="the report's reserve-reconciliation bullet carries the same denial; "
            "re-anchored when the bullet recorded that the reconciliation has since "
            "been independently re-approved, with the historical reading kept as 'as "
            "recorded then'",
        required=("not an available fourth decision cluster", "permanently barred",
                  "the active set is unchanged at 5 opportunities over 3 clusters",
                  "as recorded then",
                  "neither an activation nor a freeze"),
        forbidden=("is an available fourth decision cluster",),
    ),
)


# --------------------------------------------------------------------------- #
# The governed corpus
# --------------------------------------------------------------------------- #
def test_the_governed_document_set_is_glob_derived_and_complete():
    """A directive cannot escape the backstop by living in a new file.

    The set is globbed, not listed, so a new governance document is governed the
    moment it is added. The files the guards were written for must be inside it.
    """
    governed = set(G.governed_files())
    missing = [rel for rel in G.GOVERNED_REQUIRED if rel not in governed]
    assert missing == [], f"governed-document globs stopped matching: {missing}"
    assert len(governed) >= 40, (
        f"the governed set collapsed to {len(governed)} files; the globs are wrong"
    )


def test_every_line_of_every_governed_markdown_file_lands_in_exactly_one_passage():
    """No governed text may fall outside the passage model.

    If a line could belong to no passage, a directive written on that line would
    be invisible to the backstop. Headings and table separators are the only
    non-passage lines, by construction.
    """
    for rel in G.governed_files():
        path = G.REPO / rel
        if path.suffix.lower() == ".csv":
            continue
        covered: set[str] = set()
        for p in G.markdown_passages(path, rel):
            for line in p.raw.split("\n"):
                if line.strip():
                    covered.add(line)
        for line in path.read_text(encoding="utf-8").split("\n"):
            if not line.strip():
                continue
            if re.match(r"^(#{1,6})[ \t]+", line):
                continue
            if re.match(r"^[ \t]*\|[\s:|-]*\|?[ \t]*$", line):
                continue
            assert line in covered, (
                f"{rel}: line falls outside every passage, so the backstop cannot "
                f"see it: {line[:120]!r}"
            )


# --------------------------------------------------------------------------- #
# P2-A / P2-C — the document-wide breadth backstop
# --------------------------------------------------------------------------- #
def test_the_withdrawn_breadth_objective_appears_only_in_registered_history():
    """The document-wide fail-closed backstop.

    Every occurrence of the withdrawn breadth vocabulary, in ANY governed
    document, must sit in a passage this module registers as history and must
    carry the explicit `TD-B34-BREADTH-HISTORICAL` marker in that passage's own
    text. This is what the four demonstrated P2-A mutations violate:

      1. a live directive inserted inside the historical README section is a new,
         unregistered passage;
      2. one inserted elsewhere in README is a new, unregistered passage;
      3. one inserted in TASK_AUTHORING_REPORT.md is a new, unregistered passage;
      4. stripping the HISTORICAL/SUPERSEDED classification from the original
         README directive changes that passage's own text, so its anchor no
         longer matches and its required tokens are gone.
    """
    problems = G.check_register(G.BREADTH_VOCABULARY, BREADTH_REGISTER)
    assert problems == [], (
        "the withdrawn TD-B34 breadth objective is not confined to registered, "
        "explicitly marked history:\n  - " + "\n  - ".join(problems)
    )


@pytest.mark.parametrize(
    "claim", BREADTH_REGISTER,
    ids=lambda c: f"{c.rel.rsplit('/', 1)[-1]}:{c.anchor}",
)
def test_each_registered_breadth_passage_carries_the_explicit_marker(claim):
    """Stated per passage, so a failure names the passage that lost its marker."""
    assert MARKER in claim.required, (
        f"{claim.rel}:{claim.anchor} is registered as breadth history but does not "
        f"require the explicit historical marker"
    )
    matches = [
        p for p, _ in G.matching_passages(G.BREADTH_VOCABULARY)
        if p.address == claim.address
    ]
    assert len(matches) == 1, (
        f"registered breadth passage {claim.rel} / {claim.heading!r} / "
        f"{claim.anchor} is no longer present ({claim.why})"
    )
    assert MARKER in matches[0].flat


def test_no_governed_document_carries_a_live_breadth_requirement():
    """The normative statement, asserted directly.

    `TD-B34` governs replication depth over the complete demonstrated
    task-creatable decision space. No live current instruction may require new
    leaf-rule breadth, new source-scope breadth, "unused implemented dependency
    leaf relationships", or genuinely different source/target boundaries as a
    Stage-0 prerequisite.
    """
    live = [
        f"{p.rel}:{p.line} ({names})"
        for p, names in G.matching_passages(G.BREADTH_VOCABULARY)
        if MARKER not in p.flat
    ]
    assert live == [], (
        "a live (unmarked) breadth requirement is present in the governed "
        f"documents: {live}"
    )


def test_the_current_td_b34_objective_is_replication_depth_everywhere_it_is_stated():
    """The replacement objective, not merely the absence of the old one."""
    for rel, needle in (
        ("docs/v2/TASK_AUTHORING_POLICY.md",
         "td-b34 now governs adequate coverage of the complete task-creatable "
         "dependency-decision space"),
        ("docs/v2/DEPENDENCY_TASK_FEASIBILITY.md", "replication depth"),
        ("docs/v2/README.md", "replication depth"),
        ("docs/v2/PILOT_AND_POWER_POLICY.md",
         "adequate replication depth and balance over the complete demonstrated "
         "task-creatable decision space"),
    ):
        flat = G.norm((G.REPO / rel).read_text(encoding="utf-8"))
        assert needle in flat, f"{rel} no longer states the re-scoped objective"


def test_the_breadth_backstop_is_not_vacuous():
    """Guard the guard, three ways.

    The vocabulary must still match the directive it polices; the marker must not
    be satisfiable by the directive alone; and a synthetic live directive placed
    in a governed file must be reported as UNREGISTERED.
    """
    live = G.norm(
        "New candidates must exercise genuinely different existing "
        "dependency-direction **leaf rules and source/target boundaries** before "
        "Stage 0, because unused implemented dependency leaf relationships already "
        "exist."
    )
    matched = [k for k, rx in G.BREADTH_VOCABULARY.items() if re.search(rx, live)]
    assert set(matched) >= {
        "leaf-rule-breadth-directive",
        "source-target-boundary-breadth",
        "unused-implemented-leaves-reason",
    }, f"the breadth vocabulary no longer matches the directive it polices: {matched}"
    assert MARKER not in live, "a bare live directive must not look classified"

    # A synthetic unregistered passage must be reported, whatever its wording.
    synthetic = G.Passage(
        rel="docs/v2/README.md",
        heading="opportunity reassessment — pt05 reclassified, decision b recorded",
        line=1,
        kind="list-item",
        raw="- New candidates must exercise genuinely different existing "
            "dependency-direction leaf rules and source/target boundaries.",
        flat=live,
    )
    real = G.all_passages()
    problems = G.check_register(
        G.BREADTH_VOCABULARY, BREADTH_REGISTER, passages=list(real) + [synthetic]
    )
    assert any(p.startswith("UNREGISTERED") for p in problems), (
        "an inserted live breadth directive is not reported as unregistered; the "
        f"backstop is vacuous. problems={problems}"
    )


def test_the_marker_is_not_satisfied_by_generic_supersession_prose():
    """The exact rescue the mutation review exploited must stay impossible.

    "withdrawn as stale", said about something else entirely, used to be enough to
    make a live breadth claim look classified. It is not enough now.
    """
    for rescue in (
        "the earlier statement is withdrawn as stale",
        "superseded on the coverage counts only",
        "historical record",
        "as recorded then",
        "obsolete",
    ):
        assert MARKER not in G.norm(rescue), (
            f"generic prose {rescue!r} satisfies the historical marker"
        )


# --------------------------------------------------------------------------- #
# P2-B — the fourth-cluster denials
# --------------------------------------------------------------------------- #
def test_every_fourth_cluster_mention_is_a_registered_exact_denial():
    """No public artifact may read a reserve row as a fourth cluster.

    Registered passage by registered passage, with the exact denial each one must
    state and the inverted forms it must not contain. There is no proximity
    matching, so the two demonstrated P2-B mutations — inverting the claim in
    `DEPENDENCY_TASK_FEASIBILITY.md` and in `docs/v2/README.md` while leaving
    nearby negations intact — both fail: the inversion changes the passage's own
    text, so its anchor no longer matches, and the required sentence is gone.
    """
    problems = G.check_register(G.FOURTH_CLUSTER_VOCABULARY, FOURTH_CLUSTER_REGISTER)
    assert problems == [], (
        "a further decision cluster is asserted, or a required denial has moved:\n"
        "  - " + "\n  - ".join(problems)
    )


@pytest.mark.parametrize(
    "rel",
    ["docs/v2/DEPENDENCY_TASK_FEASIBILITY.md", "docs/v2/README.md"],
    ids=lambda r: r.rsplit("/", 1)[-1],
)
def test_the_permanent_bar_is_stated_unambiguously_in_both_protected_documents(rel):
    """The claim itself, asserted as one exact sentence in each protected file."""
    flat = G.norm((G.REPO / rel).read_text(encoding="utf-8"))
    claim = (
        "the legacy infra → core / ar-dep-004 reserve row is not evidence of a "
        "fourth task-creatable decision cluster, and it is permanently barred from e1"
    )
    assert claim in flat, f"{rel} does not state the permanent bar unambiguously"
    inverted = claim.replace("is not evidence", "is evidence")
    assert inverted not in flat, f"{rel} states the inverted claim"
    # and it is one sentence in one passage, not assembled across the document
    passage = G.find_passage(rel, claim)
    assert "permanently barred" in passage.flat
    assert passage.heading, "the claim must live under a heading"


def test_an_inverted_fourth_cluster_claim_fails_even_with_nearby_negations():
    """The exact mutation that defeated the previous guard, as a unit test.

    The review inverted "not a task-creatable fourth cluster" to "a task-creatable
    fourth cluster" and the old assertion stayed green because `not`, `cannot`,
    `no` and `not task-creatable` were still in the window. Here the inverted
    passage keeps every one of those words and is still rejected, because the
    register looks only at the passage's own claim.
    """
    registered = next(
        c for c in FOURTH_CLUSTER_REGISTER
        if c.rel == "docs/v2/DEPENDENCY_TASK_FEASIBILITY.md"
        and "load-bearing p2-b claim" in c.why.lower()
    )
    original = next(
        p for p, _ in G.matching_passages(G.FOURTH_CLUSTER_VOCABULARY)
        if p.address == registered.address
    )
    inverted_flat = (
        original.flat
        .replace("it is therefore not a task-creatable fourth cluster",
                 "it is therefore a task-creatable fourth cluster")
        .replace("reserve row is not evidence of a fourth task-creatable decision cluster",
                 "reserve row is evidence of a fourth task-creatable decision cluster")
    )
    assert inverted_flat != original.flat, "the inversion did not apply"
    # every rescuing negation the old window relied on is still present
    for word in ("not", "cannot", "no ", "not task-creatable"):
        assert word in inverted_flat, f"the mutation lost the rescuing word {word!r}"

    mutated = G.Passage(
        rel=original.rel, heading=original.heading, line=original.line,
        kind=original.kind, raw=inverted_flat, flat=inverted_flat,
    )
    others = [p for p in G.all_passages() if p.address != original.address]
    problems = G.check_register(
        G.FOURTH_CLUSTER_VOCABULARY, FOURTH_CLUSTER_REGISTER,
        passages=others + [mutated],
    )
    assert any(p.startswith("UNREGISTERED") for p in problems), problems
    assert any(p.startswith("MISSING") for p in problems), problems


def test_the_fourth_cluster_vocabulary_is_not_vacuous():
    """Guard the guard: the vocabulary must match every phrasing of the claim."""
    for claim in (
        "the inactive reserve supplies a task-creatable fourth cluster",
        "a fourth task-creatable cluster is available in reserve",
        "the active set spans four decision clusters",
        "decision clusters: 4",
        "clusters = 5",
        "a 4th decision cluster is available",
    ):
        flat = G.norm(claim)
        assert any(re.search(rx, flat) for rx in G.FOURTH_CLUSTER_VOCABULARY.values()), (
            f"the fourth-cluster vocabulary no longer matches {claim!r}"
        )


def test_the_adjudicated_active_counts_are_still_the_three_cluster_ones():
    """The positive statement the denials protect."""
    flat = G.norm((G.REPO / "docs/v2/DEPENDENCY_TASK_FEASIBILITY.md").read_text(encoding="utf-8"))
    assert "active e1 opportunities: 5" in flat
    assert "decision clusters: 3" in flat
    occupancy = re.search(r"current occupancy is[^.]*\.", flat)
    assert occupancy, "the occupancy statement is missing"
    assert not any(
        re.search(rx, occupancy.group(0)) for rx in G.FOURTH_CLUSTER_VOCABULARY.values()
    ), f"the occupancy statement claims a further cluster: {occupancy.group(0)!r}"


# --------------------------------------------------------------------------- #
# The registers themselves
# --------------------------------------------------------------------------- #
def test_both_registers_are_internally_well_formed():
    for name, register in (("breadth", BREADTH_REGISTER),
                           ("fourth-cluster", FOURTH_CLUSTER_REGISTER)):
        assert register, f"the {name} register is empty"
        G.register_index(register)  # raises on duplicate addresses
        for claim in register:
            assert claim.why.strip(), f"{name}: {claim.anchor} has no recorded reason"
            assert re.fullmatch(r"[0-9a-f]{16}", claim.anchor), claim.anchor
            assert claim.required, f"{name}: {claim.anchor} requires nothing"
            for token in claim.required + claim.forbidden:
                assert token == G.norm(token) or token.strip() == token, token
            overlap = set(claim.required) & set(claim.forbidden)
            assert not overlap, f"{name}: {claim.anchor} both requires and forbids {overlap}"


def test_no_forbidden_token_is_a_substring_of_a_required_token():
    """A polarity pin that can never fire is not a pin.

    If a forbidden string were contained in a required one, the guard would either
    always fail or be silently meaningless. This is the trap the naive inversion
    check falls into: `not a task-creatable fourth cluster` contains
    `a task-creatable fourth cluster`.
    """
    for register in (BREADTH_REGISTER, FOURTH_CLUSTER_REGISTER):
        for claim in register:
            for bad in claim.forbidden:
                for good in claim.required:
                    assert bad not in good, (
                        f"{claim.rel}:{claim.anchor} forbids {bad!r}, which is a "
                        f"substring of required {good!r}; the pin can never hold"
                    )
