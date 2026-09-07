"""Governance tests for the remaining-leaf feasibility result and the `TD-B34` re-scope.

An independent review assessed every *remaining* implemented dependency leaf
against the canonical substrate and the functional acceptance observation
boundary, and found that `AR-DEP-002` (contracts), `AR-DEP-003` (core) and
`AR-DEP-004` (infra) are **detectable but not task-creatable** here. The
consequence is a hard ceiling — **3 decision clusters / 2 leaf rules / 2 source
scopes / 3 forbidden targets** — with all three achievable clusters already
represented, so `TD-B34`'s original breadth objective is unattainable and it is
re-scoped to **replication depth**.

That conclusion is only worth anything if it is mechanically pinned, so this
module asserts:

* `TD-B34` stays open and blocking, and no longer directs authoring toward
  impossible leaf/source-scope breadth;
* the ceiling and the current occupancy are documented exactly;
* each remaining leaf carries its explicit not-task-creatable classification, and
  the two task-creatable leaves stay task-creatable;
* the active set is 5 opportunities over 3 clusters, with the two singleton
  clusters named;
* the superseded numeric breadth targets are recorded as pre-freeze provisional
  and adjudicated, not silently dropped;
* `observability` is documented as an umbrella-only source scope, matching the
  oracle it describes;
* substrate redesign appears only as a declared, unselected alternative;
* the statistical plan handles G = 3 explicitly and governs pseudo-replication
  through `decision_cluster_id`;
* and the package changed nothing it must not change: no task body or hash, no
  reserve activation, no model-visible substrate byte, no power value, and the
  protocol is still PRE-FREEZE.

Pure file inspection plus read-only git object reads; no model is invoked and no
benchmark runs.

MUTATION REPAIR (P2-A / P2-B). Two families of assertion in this module used
fixed-width character windows, and an independent mutation review proved neither
was load-bearing: a restored live breadth directive and an inverted
fourth-cluster denial both stayed green because unrelated text in the window
rescued them. Those windows are gone. Classification and denial are now
passage-exact and pinned, and the document-wide fail-closed backstop lives in
``test_replication_depth_guards.py``, which this module delegates to so there is
one authority rather than two that can drift apart.
"""
from __future__ import annotations

import csv
import hashlib
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import governance_text as G

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"
PUBLIC_TASKS_DIR = REPO / "experiments" / "v2" / "tasks" / "public"

FEASIBILITY_PATH = DOCS_V2 / "DEPENDENCY_TASK_FEASIBILITY.md"
POLICY_PATH = DOCS_V2 / "TASK_AUTHORING_POLICY.md"
REPORT_PATH = PUBLIC_TASKS_DIR / "TASK_AUTHORING_REPORT.md"
DECISIONS_CSV = DOCS_V2 / "OPEN_DECISIONS.csv"
DECISIONS_MD = DOCS_V2 / "OPEN_DECISIONS.md"
SAP_PATH = DOCS_V2 / "STATISTICAL_ANALYSIS_PLAN.md"
RQ_PATH = DOCS_V2 / "RESEARCH_QUESTIONS.md"
ORACLE_REQS_PATH = DOCS_V2 / "ORACLE_VALIDATION_REQUIREMENTS.md"
POWER_POLICY_PATH = DOCS_V2 / "PILOT_AND_POWER_POLICY.md"
DOCS_V2_README = DOCS_V2 / "README.md"
INDEX_PATH = PUBLIC_TASKS_DIR / "TASK_INDEX.csv"
MATRIX_PATH = DOCS_V2 / "PILOT_PUBLIC_TASK_MATRIX.csv"
DEP_CHECKER = REPO / "experiments" / "v2" / "oracle" / "src" / "checkers" / "dependencyDirection.ts"
RESULTS_DIR = REPO / "experiments" / "v2" / "results"
ANALYSIS_DIR = REPO / "experiments" / "v2" / "analysis"

#: The canonical substrate this feasibility result is asserted against. A
#: different substrate would need its own feasibility review (§7 of the record).
SUBSTRATE_COMMIT = "630d3180af0d02a86330dfb599f559e78df65e94"
SUBSTRATE_CONTENT_HASH = "0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3"

#: The demonstrated task-creatable ceiling. These four numbers are the whole
#: point of the re-scope: if any of them moves, the objective `TD-B34` now
#: carries is no longer the objective the substrate supports.
CEILING = {
    "decision clusters": 3,
    "leaf rules": 2,
    "source scopes": 2,
    "forbidden targets": 3,
}

#: Active E1 coverage as independently adjudicated (suite level only — no task is
#: mapped to a cluster anywhere in the public repository). These are the CURRENT
#: counts, after PT08's opportunity was admitted.
ACTIVE_OPPORTUNITIES = 6
CLUSTER_DEPTHS = {
    "DC-FEATURES-INFRA-AR-DEP-006": 3,
    "DC-FEATURES-API-AR-DEP-006": 2,
    "DC-API-CORE-AR-DEP-005": 1,
}
PRE_ADMISSION_OPPORTUNITIES = 5

#: Clusters that still carry exactly ONE active observation. Admission of PT08's
#: opportunity took the priority-A cluster out of this set; priority B is still in
#: it, and TD-B34 stays open on exactly that.
SINGLETON_CLUSTERS = {"DC-API-CORE-AR-DEP-005"}

#: The clusters TD-B34 names as replication targets, in priority order. Kept
#: separate from :data:`SINGLETON_CLUSTERS` because a cluster stays a named
#: replication target after it has been replicated — the priority list is a
#: governance fact, not a depth reading.
REPLICATION_PRIORITY_CLUSTERS = {
    "DC-FEATURES-API-AR-DEP-006",
    "DC-API-CORE-AR-DEP-005",
}

NOT_TASK_CREATABLE_LEAVES = {
    "AR-DEP-002": "contracts",
    "AR-DEP-003": "core",
    "AR-DEP-004": "infra",
}
TASK_CREATABLE_LEAVES = {"AR-DEP-005": "api", "AR-DEP-006": "features"}

#: Every public task body, with the hash this package must not move.
FROZEN_HASHES = {
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

EXPECTED_ELIGIBILITY = {
    "PT01": "scored",
    "PT02": "scored",
    "PT03": "scored",
    "PT04": "scored",
    "PT05": "functional-only",
    "PT06": "functional-only",
    "PT07": "scored",
    # authored later as the priority-A replication instrument; `scored` records
    # intent only - its public-authoring review is pending, it has no private
    # evaluator package, and it contributes to no denominator
    "PT08": "scored",
    "PR01": "inactive-reserve",
    "PR02": "inactive-reserve",
}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _norm(raw: str) -> str:
    """Lower-cased text with markdown emphasis, blockquote markers and wraps collapsed."""
    raw = raw.replace("*", "").replace("`", "")
    raw = re.sub(r"(?m)^\s*>\s?", "", raw)
    return re.sub(r"\s+", " ", raw).strip().lower()


def _flat(path: Path) -> str:
    return _norm(_text(path))


# --------------------------------------------------------------------------- #
# Structural scoping helpers.
#
# Fixed-width character windows around the first occurrence of a rule id are not
# load-bearing: an independent mutation review showed that flipping AR-DEP-002 or
# AR-DEP-003 to task-creatable, or restoring the >= 3 leaf-rule and >= 3
# source-scope targets as live, left every window assertion green because the
# window swept up a neighbouring row's verdict. The helpers below bind each
# assertion to *one* markdown section or *one* table row, so a claim about a rule
# can only be satisfied by that rule's own text.
# --------------------------------------------------------------------------- #

_HEADING_RE = re.compile(r"(?m)^(#{1,6})[ \t]+(.+?)[ \t]*$")


def _sections(path: Path) -> dict[str, str]:
    """Map each markdown heading to its body, ending at the next same-or-higher heading."""
    text = _text(path)
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
    """The body of the single heading whose normalised text starts with ``prefix``."""
    matches = {k: v for k, v in _sections(path).items() if k.startswith(prefix.lower())}
    assert len(matches) == 1, (
        f"{path.name} must carry exactly one section headed {prefix!r}, found "
        f"{sorted(matches)}"
    )
    return next(iter(matches.values()))


def _table_rows(body: str) -> list[list[str]]:
    """Normalised cells of every markdown table row in ``body`` (separators dropped)."""
    rows = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        rows.append([_norm(c) for c in cells])
    return rows


def _row(body: str, first_cell: str) -> list[str]:
    """The single table row whose first cell equals ``first_cell`` (normalised)."""
    want = _norm(first_cell)
    hits = [cells for cells in _table_rows(body) if cells and cells[0] == want]
    assert len(hits) == 1, (
        f"expected exactly one table row keyed {first_cell!r}, found {len(hits)}"
    )
    return hits[0]


def _rows(path: Path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _decision(decision_id: str) -> str:
    rows = {r["decision_id"]: r for r in _rows(DECISIONS_CSV)}
    assert decision_id in rows, f"{decision_id} is not registered"
    return rows[decision_id]["decision"].lower()


def _decision_row(decision_id: str):
    return {r["decision_id"]: r for r in _rows(DECISIONS_CSV)}[decision_id]


def _git(*args: str) -> str:
    return (
        subprocess.run(
            ["git", "-C", str(REPO), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        .stdout.decode("utf-8")
        .strip()
    )


def _has_commit(commit: str) -> bool:
    return (
        subprocess.run(
            ["git", "-C", str(REPO), "cat-file", "-e", f"{commit}^{{commit}}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


needs_substrate_commit = pytest.mark.skipif(
    shutil.which("git") is None or not _has_commit(SUBSTRATE_COMMIT),
    reason="the canonical substrate commit is not present in this repository",
)


# --------------------------------------------------------------------------- #
# 1. The feasibility record exists and is normative
# --------------------------------------------------------------------------- #
def test_the_feasibility_record_exists_and_is_pre_freeze():
    assert FEASIBILITY_PATH.is_file(), "the feasibility record must be a public artifact"
    flat = _flat(FEASIBILITY_PATH)
    assert "pre-freeze" in flat
    for phrase in (
        "authorizes no paid model run",
        "authors no task",
        "runs no power simulation",
    ):
        assert phrase in flat, f"the record must disclaim: {phrase!r}"


def test_detectability_is_never_equated_with_task_creatability():
    flat = _flat(FEASIBILITY_PATH)
    assert "a mechanically detectable relationship is not automatically an experimentally usable one" in flat
    # and the same warning must reach the two boundary-space inventories
    for path in (POLICY_PATH, REPORT_PATH):
        assert "are not 15 feasible benchmark decisions" in _flat(path).replace(
            "the 15 theoretical (source scope, forbidden target) pairs below ", ""
        ), f"{path.name} must warn that the theoretical pairs are not feasible decisions"


# --------------------------------------------------------------------------- #
# 2-3. Per-leaf classification (PART B)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("leaf,scope", sorted(NOT_TASK_CREATABLE_LEAVES.items()))
def test_the_remaining_leaves_are_classified_not_task_creatable(leaf, scope):
    """Scoped to the leaf's own §2 section — a neighbour's verdict cannot satisfy it."""
    section = _norm(_section_starting_with(FEASIBILITY_PATH, leaf))
    assert f"source scope {scope}" in _norm(
        [k for k in _sections(FEASIBILITY_PATH) if k.startswith(leaf.lower())][0]
    ), f"{leaf}'s section heading must name source scope {scope}"
    assert (
        "classification: theoretically detectable but not task-creatable on current "
        "substrate." in section
    ), (
        f"{leaf} must carry the verbatim classification THEORETICALLY DETECTABLE BUT "
        f"NOT TASK-CREATABLE ON CURRENT SUBSTRATE in its own section"
    )
    assert "classification: task-creatable." not in section, (
        f"{leaf} must not also be declared task-creatable"
    )


@pytest.mark.parametrize("leaf", sorted(NOT_TASK_CREATABLE_LEAVES))
def test_the_pair_space_row_agrees_that_the_leaf_is_not_task_creatable(leaf):
    """The §4 inventory row for this exact leaf, not a nearby row."""
    body = _section_starting_with(FEASIBILITY_PATH, "4. the theoretical pair space")
    verdict = _row(body, leaf)[-1]
    assert "not task-creatable on current substrate" in verdict, (
        f"§4's {leaf} row must read NOT TASK-CREATABLE ON CURRENT SUBSTRATE, got {verdict!r}"
    )
    assert "mechanically detectable only" in verdict, (
        f"§4's {leaf} row must keep the detectable/creatable distinction"
    )
    assert "task-creatable / represented" not in verdict


def test_the_recorded_reasons_are_the_reviewed_ones():
    flat = _flat(FEASIBILITY_PATH)
    for reason in (
        # AR-DEP-002 / contracts
        "type/interface-only",
        "erased at runtime",
        "structural typing allows local declarations",
        "preservation-only",
        # AR-DEP-003 / core
        "cannot force placement in core",
        "pure and self-sufficient",
        "persistence and logging are already served through ports/injection",
        "cannot distinguish where the computation lives",
        # AR-DEP-004 / infra
        "can be satisfied at api level",
        "structurally mirror the core domain shapes",
        "without implementation-specific wording",
    ):
        assert reason in flat, f"the feasibility reason must be recorded: {reason!r}"


@pytest.mark.parametrize("leaf,scope", sorted(TASK_CREATABLE_LEAVES.items()))
def test_the_two_working_leaves_remain_task_creatable(leaf, scope):
    """Scoped to the leaf's own §2 section and its own §4 row."""
    section = _norm(_section_starting_with(FEASIBILITY_PATH, leaf))
    assert "classification: task-creatable." in section, (
        f"{leaf} ({scope}) must remain classified TASK-CREATABLE in its own section"
    )
    assert "not task-creatable" not in section, f"{leaf} must not be downgraded"
    assert "currently represented by" in section, (
        f"{leaf} must record that it is represented in the active set"
    )

    body = _section_starting_with(FEASIBILITY_PATH, "4. the theoretical pair space")
    verdict = _row(body, leaf)[-1]
    assert "task-creatable / represented" in verdict, (
        f"§4's {leaf} row must read TASK-CREATABLE / REPRESENTED, got {verdict!r}"
    )
    assert "not task-creatable" not in verdict


# --------------------------------------------------------------------------- #
# 4. The ceiling and the current occupancy (PART C)
# --------------------------------------------------------------------------- #
def test_the_ceiling_is_documented_exactly():
    flat = _flat(FEASIBILITY_PATH)
    assert SUBSTRATE_COMMIT in _text(FEASIBILITY_PATH)
    assert SUBSTRATE_CONTENT_HASH in _text(FEASIBILITY_PATH)
    for label, value in CEILING.items():
        assert re.search(rf"{re.escape(label)}[^|]*\|\s*{value}\b", flat), (
            f"the ceiling must state {label} = {value}"
        )
    assert "3 / 3 clusters" in flat or "3 of 3" in flat, "current occupancy must be stated"


def test_the_active_set_is_five_opportunities_over_three_clusters():
    flat = _flat(FEASIBILITY_PATH)
    assert f"active e1 opportunities: {ACTIVE_OPPORTUNITIES}" in flat
    assert "decision clusters: 3" in flat
    assert "leaf rules: 2" in flat
    assert "source scopes: 2" in flat
    assert "forbidden targets: 3" in flat


@pytest.mark.parametrize("cluster,depth", sorted(CLUSTER_DEPTHS.items()))
def test_each_cluster_records_its_observation_depth(cluster, depth):
    """The occupancy table's own row, not a character window around a name.

    MUTATION REPAIR. This used ``flat.index(cluster)`` plus a 200-character
    window, so it read whichever mention of the cluster came first in the
    document. Adding the forcing-strength table of §2a — which names both
    ``AR-DEP-006`` clusters *before* the occupancy table of §3 — made the window
    land on the wrong table, and the assertion failed for a reason that had
    nothing to do with observation depth. Worse, the same fragility could have
    made it pass against an unrelated table that happened to carry the right
    digit.

    The row is now located structurally: the one table row of the occupancy
    section that names this cluster, with the depth read from that row's own
    final cell.
    """
    rel = FEASIBILITY_PATH.relative_to(REPO).as_posix()
    rows = [
        p for p in G.markdown_passages(FEASIBILITY_PATH, rel)
        if p.kind == "table-row"
        and p.heading.startswith("3. the demonstrated feasibility ceiling")
        and cluster.lower() in p.flat
    ]
    assert len(rows) == 1, (
        f"expected exactly one occupancy row naming {cluster} under the ceiling "
        f"section, found {len(rows)}"
    )
    cells = [c.strip() for c in rows[0].flat.strip("|").split("|")]
    assert cells[0] == cluster.lower(), (
        f"the occupancy row must start with {cluster}, not {cells[0]!r}"
    )
    assert cells[-1] == str(depth), (
        f"{cluster} must record {depth} active observation(s), not {cells[-1]!r}"
    )


@pytest.mark.parametrize("cluster", sorted(CLUSTER_DEPTHS))
def test_the_forcing_strength_table_does_not_restate_observation_depth(cluster):
    """§2a records forcing strength; it must never carry a depth that can drift.

    Two tables naming the same clusters is two places a depth could disagree. §2a
    is deliberately about forcing strength only, so no cell of it may be a bare
    observation count.
    """
    rel = FEASIBILITY_PATH.relative_to(REPO).as_posix()
    rows = [
        p for p in G.markdown_passages(FEASIBILITY_PATH, rel)
        if p.kind == "table-row"
        and p.heading.startswith("2a. task-createdness is not forcing strength")
        and cluster.lower() in p.flat
    ]
    for row in rows:
        cells = [c.strip() for c in row.flat.strip("|").split("|")]
        numeric = [c for c in cells if re.fullmatch(r"\d+", c)]
        assert numeric == [], (
            f"the §2a forcing-strength row for {cluster} carries a bare count "
            f"{numeric}; observation depth belongs only to the §3 occupancy table"
        )


def test_the_singleton_clusters_are_the_named_replication_priorities():
    policy = _flat(POLICY_PATH)
    for cluster in sorted(SINGLETON_CLUSTERS):
        assert cluster.lower() in policy, f"{cluster} must be a named replication target"
    # the already-replicated cluster is explicitly NOT the immediate priority
    assert "not the immediate replication priority" in policy or (
        "not the immediate priority" in policy
    )
    assert "dc-features-infra-ar-dep-006" in policy


def test_the_deficiency_is_recorded_as_replication_depth_not_breadth():
    flat = _flat(FEASIBILITY_PATH)
    assert "cluster replication depth" in flat
    assert "structurally impossible on this substrate" in flat


# --------------------------------------------------------------------------- #
# 5. TD-B34 is re-scoped, open and blocking (PART D)
# --------------------------------------------------------------------------- #
def test_td_b34_stays_open_and_blocking():
    row = _decision_row("TD-B34")
    assert row["blocking"] == "yes"
    assert row["status"].strip().lower() == "open"


def test_td_b34_no_longer_directs_authoring_toward_impossible_breadth():
    """The superseded objective may only appear as explicitly marked history.

    The ±320-character window this test used to apply was not load-bearing: an
    independent mutation review showed that supersession prose belonging to a
    neighbouring clause rescued a restored live directive. Classification is now
    field-exact and explicit — the TD-B34 registry field must carry the
    `TD-B34-BREADTH-HISTORICAL` marker in its own text — and the document-wide
    backstop lives in test_replication_depth_guards.py.
    """
    text = _decision("TD-B34")
    if re.search(r"genuinely different existing dependency-direction leaf rules", text):
        assert G.BREADTH_HISTORICAL_MARKER in text, (
            "the TD-B34 registry field restates the breadth objective without the "
            "explicit historical marker"
        )
        assert "as originally recorded" in text
    assert "superseded and structurally unattainable" in text
    assert "replication depth" in text
    assert "not task-creatable on the current substrate" in text


def test_td_b34_carries_the_re_scoped_objective():
    text = _decision("TD-B34")
    for phrase in (
        "retain all three demonstrated clusters",
        "add independent functional instruments to the singleton clusters",
        "do not author artificial tasks created only to hit mechanically implemented leaves",
        "construct-validity limitation",
        "substrate redesign",
    ):
        assert phrase in text, f"TD-B34 must state its re-scoped objective: {phrase!r}"
    assert "dc-features-api-ar-dep-006" in text and "dc-api-core-ar-dep-005" in text
    assert "not the immediate replication priority" in text


def test_td_b34_does_not_promise_that_replication_tasks_exist():
    text = _decision("TD-B34")
    assert "it is not asserted that two suitable new tasks exist" in text
    assert "no exact new task body is specified" in text
    assert "separate pre-authoring review" in text


def test_the_ceiling_is_also_recorded_in_the_registry_and_the_policy():
    text = _decision("TD-B34")
    assert "3 decision clusters, 2 leaf rules, 2 source scopes and 3 forbidden targets" in text
    policy = _flat(POLICY_PATH)
    assert "3 decision clusters, 2 leaf rules, 2 source scopes and 3 forbidden targets" in policy
    assert "all three achievable clusters are already represented" in policy


# --------------------------------------------------------------------------- #
# 6. The old numeric targets are adjudicated, not deleted (PART E)
# --------------------------------------------------------------------------- #
#: Each superseded provisional target and the adjudication its own §6 row must
#: carry. ``forbidden`` phrases must NOT appear in that same row — this is what
#: stops "≥ 3 leaf rules" being quietly restored as a live target while a
#: neighbouring row's "not achievable" keeps the assertion green.
PROVISIONAL_TARGETS = {
    "≥ 3 leaf rules": (["not achievable", "hard ceiling 2"], ["achieved —", "achieved -"]),
    "≥ 3 source scopes": (["not achievable", "hard ceiling 2"], ["achieved —", "achieved -"]),
    "≥ 3 forbidden targets": (["achieved", "currently 3"], ["not achievable"]),
    "≥ 4 independent decision clusters": (
        ["not achievable", "hard ceiling 3"],
        ["achieved —", "achieved -"],
    ),
    "≥ 2 observations per cluster": (
        ["replication-depth objective", "not currently achieved universally"],
        ["not achievable"],
    ),
    "≥ 8 e1-scored tasks": (
        ["not a scientifically meaningful standalone target"],
        ["achieved", "not achievable"],
    ),
}


@pytest.mark.parametrize("target", sorted(PROVISIONAL_TARGETS))
def test_each_superseded_numeric_target_is_adjudicated_in_its_own_row(target):
    """Row-scoped: the verdict must be in *this* target's row, not a neighbour's."""
    body = _section_starting_with(
        FEASIBILITY_PATH, "6. disposition of the earlier provisional coverage targets"
    )
    required, forbidden = PROVISIONAL_TARGETS[target]
    verdict = _row(body, target)[-1]
    for phrase in required:
        assert phrase in verdict, (
            f"{target!r} must be adjudicated {phrase!r} in its own row, got {verdict!r}"
        )
    for phrase in forbidden:
        assert phrase not in verdict, (
            f"{target!r}'s row must not read {phrase!r}: {verdict!r}"
        )


def test_the_superseded_numeric_targets_are_recorded_as_pre_freeze_provisional():
    body = _section_starting_with(
        FEASIBILITY_PATH, "6. disposition of the earlier provisional coverage targets"
    )
    prose = _norm(body)
    assert "provisional design targets" in prose
    assert "pre-freeze" in prose
    assert "never pinned in a public artifact" in prose, (
        "the targets must stay recorded as provisional, never as an acceptance bar"
    )
    # every target still on the record, none silently dropped
    keys = {cells[0] for cells in _table_rows(body)}
    missing = {_norm(t) for t in PROVISIONAL_TARGETS} - keys
    assert not missing, f"provisional targets dropped from the record: {sorted(missing)}"


def test_task_count_is_never_offered_as_a_coverage_substitute():
    flat = _flat(FEASIBILITY_PATH)
    assert "task count must not substitute for decision diversity or independence" in flat
    assert "must not be optimised toward a task count" in flat


# --------------------------------------------------------------------------- #
# 7. Substrate expansion is an alternative only (PART F)
# --------------------------------------------------------------------------- #
def test_substrate_redesign_is_declared_but_not_selected():
    flat = _flat(FEASIBILITY_PATH)
    assert "declared alternative — not selected by this governance package" in flat or (
        "declared alternative - not selected by this governance package" in flat
    )
    assert "this package performs none of it" in flat
    for cost in (
        "new canonical substrate identity",
        "renewed model-visible leakage review",
        "re-validation of c1/c2/c3/c4 substrate equivalence",
        "re-validation of every existing task",
        "public task linkage review",
        "private evaluator relink/migration",
        "renewed architecture-opportunity review",
    ):
        assert cost in flat, f"the redesign cost must be recorded: {cost!r}"
    assert "nothing here forecloses a later decision" in flat


def test_no_artifact_announces_a_substrate_change():
    """A redesign would re-identify the substrate; nothing may imply one happened."""
    for path in (FEASIBILITY_PATH, DOCS_V2_README, POLICY_PATH, REPORT_PATH):
        flat = _flat(path)
        for match in re.finditer(r"substrate redesign|substrate expansion", flat):
            window = flat[max(0, match.start() - 240) : match.end() + 240]
            assert any(
                marker in window
                for marker in ("alternative", "not selected", "would require", "defer", "declared")
            ), f"{path.name} discusses a substrate redesign without marking it unselected"


# --------------------------------------------------------------------------- #
# 8. E1's construct claim is narrowed, not broadened (PART G)
# --------------------------------------------------------------------------- #
def test_e1_effects_are_scoped_to_the_represented_decision_families():
    sentence = (
        "generalise directly to the represented dependency-decision families, not "
        "automatically to all architecture rules or all layer pairs"
    )
    for path in (SAP_PATH, RQ_PATH):
        assert sentence in _flat(path), f"{path.name} must carry the generalisation limit"
    reqs = _flat(ORACLE_REQS_PATH)
    assert "represented decision families" in reqs
    assert "not automatically to all architecture rules or all layer pairs" in reqs


def test_the_narrowing_does_not_broaden_e1():
    sap = _flat(SAP_PATH)
    assert "this does not broaden e1" in sap
    for dimension in (
        "contract ownership",
        "observability completeness",
        "duplicated logic",
        "port/interface placement",
        "general business-logic placement",
    ):
        assert dimension in sap, f"{dimension} must stay named as CON-ACB evidence"


# --------------------------------------------------------------------------- #
# 9. The G = 3 statistical method (PART H)
# --------------------------------------------------------------------------- #
def test_the_statistical_plan_handles_g_equals_three_explicitly():
    sap = _flat(SAP_PATH)
    assert "g = 3" in sap, "the plan must state the cluster count explicitly"
    assert "decision_cluster_id enters as a fixed factor" in sap
    assert "no cluster-level variance component is estimated" in sap
    assert "exhaustively enumerated" in sap


def test_the_plan_refuses_a_random_intercept_over_three_clusters():
    sap = _flat(SAP_PATH)
    for match in re.finditer(r"random intercept", sap):
        window = sap[max(0, match.start() - 400) : match.end() + 400]
        assert any(
            marker in window
            for marker in ("not identified", "superseded", "only where", "only if", "constrained by")
        ), f"an unqualified cluster random intercept survives: ...{window[300:520]!r}"
    assert "superseded" in sap


def test_the_condition_effect_stays_the_inferential_target():
    sap = _flat(SAP_PATH)
    assert "the condition effect remains the inferential target" in sap
    assert "identified within clusters" in sap
    assert "nested observations inside the three known clusters" in sap
    assert "never entered as independent architecture decisions" in sap


def test_a_sensitivity_analysis_is_defined_and_honest_about_small_g():
    sap = _flat(SAP_PATH)
    assert "cr2" in sap and "satterthwaite" in sap
    assert "randomisation inference" in sap
    assert "leave-one-cluster-out" in sap
    assert "bounded sensitivity, never the primary basis of inference" in sap


def test_the_residual_specification_is_a_registered_blocking_decision():
    row = _decision_row("TD-B41")
    assert row["blocking"] == "yes"
    assert row["status"].strip().lower() == "open"
    text = row["decision"].lower()
    assert "permitted options" in text
    assert "before the td-b37 power simulation" in text
    assert "never by which option gives the larger effect" in text


#: §4c pre-registers what happens at each realised cluster count. Scoped to that
#: section so a stray mention of "G = 2" elsewhere cannot satisfy the check.
def _realised_g_section() -> str:
    return _section_starting_with(SAP_PATH, "4c. the realised cluster count")


def test_the_realised_cluster_count_is_defined_before_any_power_simulation():
    flat = _norm(_realised_g_section())
    assert (
        "number of decision_cluster_id levels containing at least one final, frozen, "
        "e1-eligible opportunity" in flat
    ), "G must be defined as eligible-cluster count, not assumed"
    assert "after the eligibility gates are resolved" in flat
    assert "g is therefore not known" in flat
    assert "no analysis, simulation or report may assume g = 3 beforehand" in flat


def test_the_g_equals_three_branch_retains_the_existing_fixed_specification():
    flat = _norm(_realised_g_section())
    assert "current expectation" in flat
    assert "existing §4b specification is retained unchanged" in flat
    assert "fixed 3-level blocking factor" in flat


def test_the_g_equals_two_contingency_is_pre_registered():
    """The whole point of P1-4: G = 2 must be decided now, not after data."""
    flat = _norm(_realised_g_section())
    assert "pre-registered contingency" in flat
    assert "fixed 2-level blocking factor" in flat
    # the inferential contrasts stay identified within clusters
    assert "identified within clusters" in flat
    assert "conditions are crossed within every eligible task" in flat
    # and each binding constraint the review required
    for constraint in (
        "no cluster random-intercept variance is estimated",
        "not identified at two groups",
        "never treated as independent architecture decisions",
        "nesting and repetition are retained",
        "randomisation inference remains a principal small-g sensitivity",
        "cr2/cr3 is not promoted to primary evidence",
        "omitted at g = 2, or reported and explicitly labelled unreliable",
        "two deterministic exclusions",
        "descriptive robustness only",
        "exactly one between-cluster contrast",
    ):
        assert constraint in flat, f"the G = 2 contingency must state: {constraint!r}"


def test_the_g_below_two_blocking_rule_is_pre_registered():
    flat = _norm(_realised_g_section())
    assert "pre-registered blocking rule" in flat
    assert (
        "confirmatory e1 condition model requiring architecture-decision blocking is not run"
        in flat
    ), "at G < 2 the confirmatory blocked model must not be run"
    assert "stage-0 e1 eligibility remains blocked" in flat
    assert "re-adjudicated" in flat
    assert "no post-hoc fallback model may be invented once data exist" in flat


def test_the_contingencies_are_not_a_post_hoc_fallback():
    flat = _norm(_realised_g_section())
    assert "nothing here is a fallback chosen after data" in flat
    assert "before the td-b37 power simulation" in flat
    assert "produces no power value" in flat


def test_td_b41_no_longer_claims_the_cluster_count_can_only_be_three():
    text = _decision("TD-B41")
    assert "no longer claims that it can only ever be three" in text, (
        "TD-B41 must stop asserting that G can only realise as three"
    )
    assert "g=2 contingency" in text and "g<2 blocking rule" in text, (
        "TD-B41 must point at both pre-registered contingencies"
    )
    assert "not a guaranteed realisation" in text
    assert "carrying at least one final, frozen, e1-eligible opportunity" in text, (
        "TD-B41 must carry the eligibility-based definition of G"
    )


def test_pseudo_replication_is_governed_by_the_cluster_identifier():
    b30 = _decision("TD-B30")
    assert "decision_cluster_id" in b30
    assert "source_scope + forbidden_target + leaf_rule" in b30
    assert "fixed factor" in b30
    sap = _flat(SAP_PATH)
    assert "decision_cluster_id" in sap


def test_the_stage_0_gate_no_longer_demands_impossible_breadth():
    """The live Stage-0 directive must match the feasibility ceiling.

    The gate previously required additional tasks exercising *genuinely different*
    leaf rules and source/target boundaries before Stage 0. With a demonstrated
    ceiling of 2 leaf rules and 2 source scopes, all of them already represented,
    that is an instruction to author something the substrate cannot support. It is
    scoped here to the Stage-0 section so a discussion elsewhere cannot satisfy it.
    """
    body = _section_starting_with(
        POWER_POLICY_PATH, "stage 0 — non-evidentiary technical dry runs"
    )
    flat = _norm(body)

    # The withdrawn directive may appear only inside a passage that carries the
    # explicit historical marker in its OWN text. The ±400-character window this
    # used to apply was rescuable by neighbouring prose; classification is now
    # passage-exact, and the document-wide backstop is in
    # test_replication_depth_guards.py.
    for passage in G.markdown_passages(
        POWER_POLICY_PATH, POWER_POLICY_PATH.relative_to(REPO).as_posix()
    ):
        if not re.search(
            r"genuinely different (?:existing )?dependency-direction\s*leaf rules",
            passage.flat,
        ):
            continue
        assert G.BREADTH_HISTORICAL_MARKER in passage.flat, (
            "the impossible breadth directive is live in the Stage-0 gate: "
            f"{passage} ...{passage.flat[:220]!r}"
        )
    assert "withdrawn directive" in flat, (
        "the Stage-0 gate must record that the breadth directive was withdrawn"
    )
    assert "structurally unattainable" in flat or "obsolete" in flat

    # and the re-scoped requirement must be what the gate now states
    assert "replication depth" in flat, "Stage 0 must now be gated on replication depth"
    assert "3 decision clusters / 2 leaf rules / 2 source scopes / 3 forbidden targets" in flat
    assert "all three clusters are already represented" in flat
    for cluster in sorted(SINGLETON_CLUSTERS):
        assert cluster.lower() in flat, f"{cluster} must be named as a replication target"
    assert "not the immediate priority" in flat


def test_the_stage_0_gate_does_not_assume_replication_candidates_exist():
    """Singleton replicates are not presumed available; each needs its own review.

    Priority A's review has since happened and its instrument is admitted, so the
    gate can no longer say the review has not happened *at all*. What it must still
    say — and what the assertion moved to — is that priority B's review has not
    happened and priority B is not started.
    """
    flat = _norm(
        _section_starting_with(POWER_POLICY_PATH, "stage 0 — non-evidentiary technical dry runs")
    )
    assert "not asserted that a suitable replication task exists" in flat, (
        "the gate must not assume a replicate exists for the remaining singleton"
    )
    assert "separate pre-authoring review" in flat
    assert "for priority b that review has still not happened" in flat
    assert "priority b is not started" in flat
    # and priority A's review is recorded as having happened without closing TD-B34
    assert "the priority-a review has since happened" in flat
    assert "did not close td-b34" in flat
    assert "td-b34" in flat and "open and blocking" in flat


def test_td_b37_stays_open_and_lists_its_preconditions():
    row = _decision_row("TD-B37")
    assert row["blocking"] == "yes"
    assert row["status"].strip().lower() == "open"
    text = row["decision"].lower()
    for precondition in (
        "td-b34 re-scope to replication depth is complete",
        "replication design is known",
        "pre-registered",
        "final e1 denominator structure is known",
    ):
        assert precondition in text, f"TD-B37 must list precondition: {precondition!r}"
    assert "no power simulation was run" in text
    assert "g = 3" in _flat(POWER_POLICY_PATH)


# --------------------------------------------------------------------------- #
# 10. observability is umbrella-only (PART K)
# --------------------------------------------------------------------------- #
def test_observability_is_documented_umbrella_only():
    flat = _flat(FEASIBILITY_PATH)
    assert "observability has no leaf rule" in flat
    assert "leafrulefor('observability', target) returns null" in flat
    assert "umbrella-only under ar-dep-001" in flat
    assert "never eligible as a scored opportunity" in flat
    assert "no oracle behaviour changes here" in flat
    for path in (POLICY_PATH, REPORT_PATH, ORACLE_REQS_PATH):
        assert "umbrella-only" in _flat(path), f"{path.name} must record the umbrella-only status"


def test_the_documentation_matches_the_oracle_it_describes():
    """Guard the guard: the prose is only true because the checker says so."""
    src = _text(DEP_CHECKER)
    assert "export function leafRuleFor" in src
    body = src[src.index("export function leafRuleFor") :]
    body = body[: body.index("\n}")]
    assert "case 'observability'" not in body, (
        "observability must fall through to the null default, not gain a leaf clause"
    )
    assert "default:\n      return null;" in body


# --------------------------------------------------------------------------- #
# 11. Boundary-space inventories carry feasibility status (PART J)
# --------------------------------------------------------------------------- #
#: The boundary-space inventory table in each public artifact that publishes one.
#: Keyed by leaf id, so the feasibility verdict is read from that leaf's own row.
BOUNDARY_TABLE_SECTIONS = {
    POLICY_PATH: "12.2 the boundary space available under already-implemented leaf rules",
    REPORT_PATH: "boundary space available under the already-implemented leaf rules",
    FEASIBILITY_PATH: "4. the theoretical pair space",
}


def _boundary_table_body(path: Path) -> str:
    return _section_starting_with(path, BOUNDARY_TABLE_SECTIONS[path])


@pytest.mark.parametrize("path", sorted(BOUNDARY_TABLE_SECTIONS), ids=lambda p: p.name)
def test_every_boundary_table_annotates_feasibility(path):
    """Row-scoped in all three inventories, so no row can borrow another's verdict."""
    body = _boundary_table_body(path)
    for leaf in sorted(NOT_TASK_CREATABLE_LEAVES):
        verdict = _row(body, leaf)[-1]
        assert "not task-creatable on current substrate" in verdict, (
            f"{path.name}: {leaf}'s own row must read NOT TASK-CREATABLE, got {verdict!r}"
        )
        assert "task-creatable / represented" not in verdict, (
            f"{path.name}: {leaf} must not be marked represented"
        )
    for leaf in sorted(TASK_CREATABLE_LEAVES):
        verdict = _row(body, leaf)[-1]
        assert "task-creatable / represented" in verdict, (
            f"{path.name}: {leaf}'s own row must read TASK-CREATABLE / REPRESENTED, "
            f"got {verdict!r}"
        )
        assert "not task-creatable" not in verdict, (
            f"{path.name}: {leaf} must not be downgraded"
        )
    assert "umbrella-only" in _norm(body), f"{path.name} must keep the observability row"


def test_the_investigate_list_is_closed_rather_than_left_open():
    for path in (POLICY_PATH, REPORT_PATH):
        flat = _flat(path)
        assert "investigated and closed" in flat, (
            f"{path.name} must close the earlier candidate-decision list"
        )


# --------------------------------------------------------------------------- #
# 12-15. Invariants: nothing that must not change, changed (PARTS N/P)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("task_id", sorted(FROZEN_HASHES))
def test_no_task_body_or_hash_changed(task_id):
    body = (PUBLIC_TASKS_DIR / f"{task_id}.md").read_bytes()
    assert hashlib.sha256(body).hexdigest() == FROZEN_HASHES[task_id], (
        f"{task_id}'s body changed; this is a governance package and must not touch a task"
    )
    index = {r["task_id"]: r for r in _rows(INDEX_PATH)}
    assert index[task_id]["public_task_sha256"] == FROZEN_HASHES[task_id]
    matrix = {r["task_id"]: r for r in _rows(MATRIX_PATH)}
    assert matrix[task_id]["public_task_sha256"] == FROZEN_HASHES[task_id]


def test_no_reserve_was_activated():
    index = {r["task_id"]: r["e1_analysis_eligibility"] for r in _rows(INDEX_PATH)}
    matrix = {r["task_id"]: r["e1_analysis_eligibility"] for r in _rows(MATRIX_PATH)}
    assert index == EXPECTED_ELIGIBILITY, "task eligibility drifted"
    assert matrix == EXPECTED_ELIGIBILITY, "the public matrix disagrees with the index"
    for reserve in ("PR01", "PR02"):
        assert index[reserve] == "inactive-reserve"
    assert "no reserve was activated" in _flat(REPORT_PATH)


@needs_substrate_commit
def test_the_model_visible_substrate_is_unchanged():
    """`apps/` and `libs/` must be byte-identical to the canonical substrate."""
    for tree in ("apps", "libs"):
        head = _git("rev-parse", f"HEAD:{tree}")
        canonical = _git("rev-parse", f"{SUBSTRATE_COMMIT}:{tree}")
        assert head == canonical, (
            f"{tree}/ diverged from the canonical substrate: {head} != {canonical}"
        )


@needs_substrate_commit
def test_the_canonical_substrate_identity_is_unchanged():
    import substrate_identity as si  # conftest puts the harness on sys.path

    computed = si.substrate_content_hash_at_commit(REPO, SUBSTRATE_COMMIT)
    assert computed == SUBSTRATE_CONTENT_HASH, (
        f"the canonical substrate identity moved: {computed}"
    )


def test_no_power_simulation_result_was_introduced():
    for flat, name in (
        (_flat(SAP_PATH), SAP_PATH.name),
        (_flat(POWER_POLICY_PATH), POWER_POLICY_PATH.name),
        (_flat(FEASIBILITY_PATH), FEASIBILITY_PATH.name),
    ):
        assert any(
            phrase in flat
            for phrase in (
                "no power value is frozen",
                "no final power value is frozen",
                "produces no power value",
            )
        ), name
    # and no result artifact exists at all
    for directory in (RESULTS_DIR, ANALYSIS_DIR):
        stray = [p.name for p in directory.iterdir() if p.name != "README.md"]
        assert not stray, f"{directory.name}/ must hold no result artifact, found {stray}"


def test_the_protocol_is_still_pre_freeze():
    assert "PRE-FREEZE" in _text(DOCS_V2_README)
    assert "PRE-FREEZE" in _text(FEASIBILITY_PATH)
    tags = _git("tag", "--list").split()
    assert "protocol-freeze" not in tags, "no protocol-freeze tag may exist"


def test_the_registry_records_the_feasibility_package_without_closing_its_own_blockers():
    """The feasibility package opened `TD-B41` and closed nothing of its own.

    `TD-B40` has since been closed by a **later** governance package, once both of
    its residuals completed. That is recorded here rather than asserted away: the
    resolved set is pinned exactly, and the blockers this package must never close
    — `TD-B34`, `TD-B37`, `TD-B41` — are asserted open by name.
    """
    md = _text(DECISIONS_MD)
    assert "Blocking decisions: 41**" in md
    assert "Total decisions: 47**" in md
    rows = _rows(DECISIONS_CSV)
    resolved = {r["decision_id"] for r in rows if r["status"].strip().lower() == "resolved"}
    assert resolved == {"TD-B23", "TD-B24", "TD-B38", "TD-B40"}, (
        f"unexpected resolved set: {sorted(resolved)}"
    )
    assert f"**{len(resolved)} are resolved**" in md, "resolved count drifted"
    assert f"**{len(rows) - len(resolved)} remain open**" in md, "open count drifted"
    by_id = {r["decision_id"]: r for r in rows}
    for still_open in ("TD-B34", "TD-B37", "TD-B41", "TD-B39"):
        assert by_id[still_open]["status"].strip().lower() == "open", (
            f"{still_open} must stay open; the feasibility re-scope closes nothing"
        )


# --------------------------------------------------------------------------- #
# 16. The breadth directive is SUPERSEDED wherever it still appears (PART I / J).
#
# The re-scope was already pinned in the TD-B34 registry row and in the Stage-0
# gate. A later review found two places it had NOT reached, both still reading as
# live instruction:
#
#   * docs/v2/README.md - the DECISION B bullet, telling the next authoring
#     packages that additional tasks must exercise "genuinely different existing
#     dependency-direction leaf rules and source/target boundaries" before Stage 0,
#     plus the power sentence in the same historical section gating the power
#     simulation on "additional distinct decisions";
#   * TASK_AUTHORING_REPORT.md - the original DECISION B section, stating the same
#     directive and its "unused implemented dependency leaf relationships already
#     exist" reason.
#
# Neither is rewritten. Each is marked HISTORICAL / SUPERSEDED in place, with a
# forward pointer to the current governance.
#
# MUTATION-REPAIRED (P2-A). The original guards here were section-scoped but then
# applied a +/-700-character window, and an independent mutation review proved that
# is not load-bearing. All four demonstrated mutations passed:
#
#   1. a NEW live breadth directive inserted inside the historical README section;
#   2. one inserted elsewhere in README;
#   3. one inserted in TASK_AUTHORING_REPORT.md;
#   4. removing the HISTORICAL/SUPERSEDED classification from the original README
#      directive while retaining nearby supersession prose.
#
# (1) and (4) passed because the window swept up a NEIGHBOURING passage's
# supersession prose; (2) and (3) passed because the section scoping meant the
# guard never looked there at all.
#
# The window is gone. Classification is now PASSAGE-EXACT and EXPLICIT: an
# occurrence is history only if its own passage carries the
# `TD-B34-BREADTH-HISTORICAL` marker, and the document-wide fail-closed backstop -
# every governed document, every passage, pinned by anchor - lives in
# test_replication_depth_guards.py. The assertions below remain as the LOCAL
# section checks the repaired design keeps in addition to that backstop.
# --------------------------------------------------------------------------- #
#: The withdrawn breadth wording, as it actually appears.
BREADTH_DIRECTIVE_RE = re.compile(
    r"genuinely different existing\s*dependency-direction\s*leaf rules",
    re.IGNORECASE,
)
#: Prose that reads as supersession. Retained only for the non-vacuity check that
#: proves a bare live directive carries none of it; it is NEVER accepted as the
#: classification of an occurrence, because the mutation review showed such words
#: are routinely present for unrelated reasons ("withdrawn as stale", said about a
#: different statement entirely, was already rescuing a live breadth claim).
SUPERSESSION_MARKERS = (
    "superseded", "withdrawn", "as recorded then", "as originally recorded",
    "historical", "obsolete", "no longer current",
)

#: Where the withdrawn directive survives, and which section must carry the marker.
BREADTH_HISTORY_SECTIONS = {
    DOCS_V2_README: "opportunity reassessment",
    REPORT_PATH: "decision b - additional architecture tasks required before stage 0",
}


@pytest.mark.parametrize(
    "path", sorted(BREADTH_HISTORY_SECTIONS, key=lambda p: p.name), ids=lambda p: p.name
)
def test_the_breadth_directive_survives_only_as_superseded_history(path):
    """Every occurrence must be marked in its OWN passage, not its neighbourhood.

    Section-scoped for the "did it move?" check, passage-exact for the
    classification check. No character window.
    """
    rel = path.relative_to(REPO).as_posix()
    body = _section_starting_with(path, BREADTH_HISTORY_SECTIONS[path])
    assert BREADTH_DIRECTIVE_RE.search(_norm(body)), (
        f"{path.name}: the historical breadth directive is not in the section this "
        f"guard scopes to; if it moved, the guard must move with it"
    )
    section_lines = {ln for ln in body.split("\n") if ln.strip()}
    checked = 0
    for passage in G.markdown_passages(path, rel):
        if not BREADTH_DIRECTIVE_RE.search(passage.flat):
            continue
        if not any(ln in section_lines for ln in passage.raw.split("\n") if ln.strip()):
            continue  # a different section's occurrence; the backstop covers it
        checked += 1
        assert G.BREADTH_HISTORICAL_MARKER in passage.flat, (
            f"{path.name}: the breadth directive reads as LIVE instruction - its own "
            f"passage carries no explicit historical marker: {passage} "
            f"...{passage.flat[:240]!r}"
        )
    assert checked, f"{path.name}: no passage of the scoped section was checked"


@pytest.mark.parametrize(
    "path", sorted(BREADTH_HISTORY_SECTIONS, key=lambda p: p.name), ids=lambda p: p.name
)
def test_each_breadth_section_carries_a_supersession_and_forward_pointer(path):
    """A marker alone is not enough: the reader needs the CURRENT rule and why."""
    flat = _norm(_section_starting_with(path, BREADTH_HISTORY_SECTIONS[path]))
    assert "superseded" in flat
    assert "structurally unattainable" in flat or (
        "not task-creatable on the current substrate" in flat
    )
    assert "replication depth" in flat, (
        f"{path.name}: the superseded section must point at the current objective"
    )
    assert "3 decision clusters / 2 leaf rules / 2 source scopes / 3 forbidden targets" in flat, (
        f"{path.name}: the superseded section must state the demonstrated ceiling"
    )
    assert "dependency_task_feasibility.md" in flat, (
        f"{path.name}: the supersession note must point at the normative record"
    )
    for cluster in sorted(SINGLETON_CLUSTERS):
        assert cluster.lower() in flat, f"{path.name} must name {cluster}"


def test_the_readme_marks_the_directive_as_not_to_be_authored_against():
    """The README is the entry point, so its note must be unmistakable."""
    flat = _norm(_section_starting_with(DOCS_V2_README, "opportunity reassessment"))
    assert "not current governance" in flat
    assert "must not be authored against" in flat
    assert "withdrawn directive" in flat
    # the "no new rule family" REASON is superseded, not just the directive
    assert "binding constraint is substrate feasibility" in flat


def test_the_report_marks_the_decision_b_section_as_not_to_be_authored_against():
    flat = _norm(
        _section_starting_with(
            REPORT_PATH,
            "decision b - additional architecture tasks required before stage 0",
        )
    )
    assert "historical record" in flat
    assert "not current governance" in flat
    assert "do not author against this section" in flat
    assert "withdrawn directive" in flat
    # history is preserved, not rewritten
    assert "as originally recorded" in flat
    assert "nothing here is rewritten" in flat
    # the motivation survives; only the remedy is superseded
    assert "the motivation is unchanged and still current" in flat


def test_the_report_supersedes_the_unused_leaf_relationships_reason():
    """The reason, not only the directive.

    "Unused implemented dependency leaf relationships already exist" is WHY the
    breadth objective looked achievable. Left live it would justify re-adopting it,
    so it carries its own supersession.
    """
    rel = REPORT_PATH.relative_to(REPO).as_posix()
    seen = 0
    for passage in G.markdown_passages(REPORT_PATH, rel):
        if "unused implemented dependency leaf relationships already exist" not in passage.flat:
            continue
        seen += 1
        assert G.BREADTH_HISTORICAL_MARKER in passage.flat, (
            f"the 'unused leaves already exist' reason reads as live: {passage} "
            f"...{passage.flat[:240]!r}"
        )
    assert seen, "the 'unused leaves already exist' reason is no longer present"
    assert "binding constraint is substrate feasibility" in _flat(REPORT_PATH)


def test_the_readme_power_precondition_is_superseded_too():
    """The power sentence in the same historical section is part of the directive.

    "The final power simulation runs only after additional DISTINCT DECISIONS are
    authored and approved" is the breadth objective wearing a statistical hat: no
    additional distinct decision is available, so left live it would block the
    power simulation on something unattainable.
    """
    flat = _norm(_section_starting_with(DOCS_V2_README, "opportunity reassessment"))
    assert re.search(r"additional distinct decisions are\s*authored", flat), (
        "the historical power precondition is not in the scoped section"
    )
    rel = DOCS_V2_README.relative_to(REPO).as_posix()
    seen = 0
    for passage in G.markdown_passages(DOCS_V2_README, rel):
        if not re.search(r"additional distinct decisions are\s*authored", passage.flat):
            continue
        seen += 1
        assert G.BREADTH_HISTORICAL_MARKER in passage.flat, (
            f"the README power precondition reads as live: {passage} "
            f"...{passage.flat[:240]!r}"
        )
    assert seen, "the historical power precondition is no longer present"
    assert "the power precondition above is superseded" in flat
    assert "replication depth" in flat
    # what has NOT changed is restated, so the supersession is not read as a
    # licence to run a power simulation
    assert "no power simulation has been run" in flat
    assert "no power value is frozen" in flat
    assert "decision_cluster_id is mandatory" in flat


def test_the_breadth_guard_is_not_vacuous():
    """Guard the guard: the pattern must match the wording it polices."""
    live = _norm(
        "New candidates must exercise genuinely different existing "
        "dependency-direction **leaf rules and source/target boundaries**."
    )
    assert BREADTH_DIRECTIVE_RE.search(live), (
        "the breadth-directive pattern no longer matches the directive it exists to "
        "police; restoring the live instruction would go unnoticed"
    )
    assert not any(m in live for m in SUPERSESSION_MARKERS)


# --------------------------------------------------------------------------- #
# 17. Inactive-reserve draft rows do not contradict the ceiling (PART K).
# --------------------------------------------------------------------------- #
RESERVE_SECTION = "3a. inactive-reserve draft rows do not contradict"


def test_the_feasibility_record_explains_the_inactive_reserve_draft_rows():
    body = _norm(_section_starting_with(FEASIBILITY_PATH, RESERVE_SECTION))
    assert "pr01" in body and "pr02" in body
    # the exact misreading the section exists to prevent
    assert "ar-dep-004" in body
    assert "fourth cluster" in body
    assert "permanently barred" in body
    # historical / pre-reassessment material, entering no active endpoint
    assert "historical, pre-reassessment material" in body
    assert "contributes to no endpoint" in body
    assert "no active cluster register" in body
    assert "zero" in body and "denominator" in body
    # being inactive was never a licence to leave an invalid row standing
    assert "being inactive was never a licence" in body
    # the dispositions are machine-readable, not only prose
    assert "machine-readable" in body
    assert "checkable rather than a matter of reading prose" in body
    # nothing private is disclosed
    assert "no private identifier" in body
    assert "no task-to-cluster mapping is published" in body
    # The reconciliation is now independently re-approved, and the section must say
    # so WITHOUT that reading as an activation. Both halves are required: a section
    # that recorded only the re-approval would let a reader take the reserve as live.
    assert "independently re-approved" in body
    assert "re-approval is not activation and not a freeze" in body
    assert "both reserves stay inactive-reserve" in body
    assert "gate g1 is not passed" in body
    assert (
        "activation still requires a separately recorded, independently approved "
        "pre-run activation decision" in body
    )
    assert "td-b40" in body


def test_the_reserve_explanation_is_carried_into_the_policy_and_the_report():
    """One record explaining it is not enough: the authoring bar must carry it."""
    policy = _flat(POLICY_PATH)
    assert "the reserve rows have since been re-authored" in policy
    assert "permanently barred" in policy
    assert "no legacy reserve row is a task-creatable fourth cluster" in policy
    assert "reserve denominator is 0" in policy
    report = _flat(REPORT_PATH)
    assert "the private reserve rows are reconciled, and no reserve was activated" in report
    assert "permanently barred" in report
    assert "not an available fourth decision cluster" in report


#: Any way of naming a fourth (or larger) decision cluster. The ceiling is three,
#: so every occurrence must be a DENIAL. Word order is deliberately not assumed:
#: "a task-creatable fourth cluster" and "a fourth task-creatable cluster" are the
#: same false claim, and an earlier draft of this guard missed the first.
#:
#: Shared with the exact register in test_replication_depth_guards.py so there is
#: one vocabulary, not two that can drift apart.
FOURTH_CLUSTER_RE = re.compile(
    "|".join(G.FOURTH_CLUSTER_VOCABULARY.values()), re.IGNORECASE
)


def test_no_public_artifact_reads_a_reserve_row_as_active_coverage():
    """The load-bearing negative: a reserve row is never active coverage.

    MUTATION-REPAIRED (P2-B). This test used to accept any denial word inside a
    +/-260-character window. An independent mutation review inverted
    *"not a task-creatable fourth cluster"* to *"a task-creatable fourth cluster"*
    and the test stayed green, because `not`, `cannot`, `no` and
    `not task-creatable` elsewhere in the window satisfied the denial pattern.

    Proximity matching is gone. Each mention now has to be a REGISTERED passage
    stating its OWN exact denial and containing none of its own inverted forms -
    see FOURTH_CLUSTER_REGISTER in test_replication_depth_guards.py, which this
    test delegates to so there is exactly one authority.
    """
    from test_replication_depth_guards import FOURTH_CLUSTER_REGISTER

    problems = G.check_register(G.FOURTH_CLUSTER_VOCABULARY, FOURTH_CLUSTER_REGISTER)
    assert problems == [], (
        "a public artifact asserts a further decision cluster as available "
        "coverage, or a required denial has moved:\n  - " + "\n  - ".join(problems)
    )

    # Every document this test historically covered must still be inside the
    # governed corpus the register is evaluated over, so delegation cannot narrow
    # the blast radius.
    governed = set(G.governed_files())
    for path in (FEASIBILITY_PATH, POLICY_PATH, REPORT_PATH, DECISIONS_CSV,
                 DECISIONS_MD, DOCS_V2_README):
        rel = path.relative_to(REPO).as_posix()
        assert rel in governed, f"{rel} dropped out of the governed corpus"

    # the adjudicated active counts are still the three-cluster ones
    flat = _flat(FEASIBILITY_PATH)
    assert f"active e1 opportunities: {ACTIVE_OPPORTUNITIES}" in flat
    assert "decision clusters: 3" in flat
    # and the occupancy statement itself is not padded with an extra cluster
    occupancy = re.search(r"current occupancy is[^.]*\.", flat)
    assert occupancy, "the occupancy statement is missing"
    assert not FOURTH_CLUSTER_RE.search(occupancy.group(0)), (
        f"the occupancy statement claims a further cluster: {occupancy.group(0)!r}"
    )


def test_the_fourth_cluster_guard_is_not_vacuous():
    """Guard the guard: the pattern must match the claim it exists to police."""
    for claim in (
        "the inactive reserve supplies a task-creatable fourth cluster",
        "a fourth task-creatable cluster is available in reserve",
        "the active set spans four decision clusters",
        "decision clusters: 4",
    ):
        assert FOURTH_CLUSTER_RE.search(_norm(claim)), claim
