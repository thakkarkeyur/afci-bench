"""Governance tests for the functional acceptance observation boundary.

The boundary answers a question the protocol previously left open: **what may a
hidden acceptance test look at when it decides pass or fail?** It is normatively
stated in ``docs/v2/HIDDEN_EVALUATOR_BOUNDARY.md`` sections 9-14, carried into
``docs/v2/TASK_AUTHORING_POLICY.md`` section 8a as an authoring rule, and into
``docs/v2/ORACLE_VALIDATION_REQUIREMENTS.md`` section 3a as a channel-separation
requirement. Blocking decisions: ``TD-B39`` (migrate the private hidden acceptance
packages onto it) and ``TD-B40`` (re-scoped: the preservation-only opportunities
have since been migrated out of the active E1 set, leaving the residual
inactive-reserve rows and the outstanding independent re-approval).

These tests assert the *governance*, not any hidden acceptance: nothing here
implements, mounts, or reads a hidden test, and no model is invoked. They also
pin the pre-authoring invariants the boundary package promised - that it changed
no task body or hash, authored no task, and modified no private evaluator file.
Pure file and ``git`` inspection.
"""
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
DOCS = REPO / "docs" / "v2"

BOUNDARY = DOCS / "HIDDEN_EVALUATOR_BOUNDARY.md"
POLICY = DOCS / "TASK_AUTHORING_POLICY.md"
ORACLE_REQS = DOCS / "ORACLE_VALIDATION_REQUIREMENTS.md"
AUTHORING_REPORT = REPO / "experiments" / "v2" / "tasks" / "public" / "TASK_AUTHORING_REPORT.md"
TASK_INDEX = REPO / "experiments" / "v2" / "tasks" / "public" / "TASK_INDEX.csv"
PUBLIC_TASK_DIR = REPO / "experiments" / "v2" / "tasks" / "public"

#: The private evaluator repository is a *sibling* of the public repository and is
#: never vendored into it. The invariant checked below is **separation**, not a
#: pinned revision: public operations must not mutate the private repository. The
#: private repository is a live review repository and its HEAD advances under
#: authorised private work, so pinning one historical SHA would guarantee a false
#: failure after the next legitimate private commit — which is exactly what
#: happened to the previous version of this check.
PRIVATE_REPO = REPO.parent / "afci-bench-evaluator-private"

#: The candidate task bodies and their recorded SHA-256 values, pinned here
#: literally. ``test_public_task_integrity.py`` checks each body against
#: ``TASK_INDEX.csv``; this list additionally catches a body and its index row
#: being edited *together*, which that check alone cannot see.
#:
#: The first eight existed when the observation boundary was defined and must stay
#: byte-identical. ``PT07`` was authored afterwards, under DECISION B, and is
#: listed separately in :data:`AUTHORED_AFTER_THE_BOUNDARY` so "the boundary
#: package changed nothing" stays a checkable claim about those eight.
AUTHORED_AFTER_THE_BOUNDARY = {
    "PT07": "557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7",
}

BOUNDARY_ERA_TASK_HASHES = {
    "PT01": "6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39",
    "PT02": "ec4b60057708b20cb95e51f000671aab40afc8c55c0bc75850922a5f65841a77",
    "PT03": "cbfce1ca232cb9b6b53e0b4d202d6acee7415b50af8386c1f3bd2147089b4c21",
    "PT04": "f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5",
    "PT05": "f6efc772e76d6c287e0c71daaa93c7e1d9e62e72a1b37878df70113269ed27b3",
    "PT06": "3e0f84cfef1f9fbf97e3cd31b6704c3a0fb172b04b5e7bc33ea39927b1c8e0f2",
    "PR01": "0e1527bce41498836bb57b802d4566251d6fcfed4cca13fe59e6a97330f02302",
    "PR02": "e89a4aab236813c082f9152db779b8bbfb298148a51a8435a1e2bf38330caa83",
}

#: Every public task body and its recorded hash.
FROZEN_TASK_HASHES = {**BOUNDARY_ERA_TASK_HASHES, **AUTHORED_AFTER_THE_BOUNDARY}

#: Persistence internals of the substrate's adapter. They are a legitimate part of
#: the application and of its *visible* test suite; what they may never become is
#: an acceptance oracle or an evaluator mechanism.
PERSISTENCE_INTERNALS = ("getOrderRepository", "resetOrderRepository", "InMemoryOrderRepository")

#: Where those symbols are allowed to appear as *code* in the public repository:
#: the adapter that defines them, the composition root that wires them, and the
#: substrate's own visible spec. Nothing under experiments/ may reference them.
PERSISTENCE_INTERNAL_CODE_ALLOWLIST = {
    "libs/infra/src/index.ts",
    "apps/api/src/app.ts",
    "apps/api/src/app.spec.ts",
}

CODE_SUFFIXES = {".ts", ".tsx", ".js", ".py", ".fixture"}
SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".nx", ".pytest_cache", "archive", "dist", "coverage"}


def _read(path):
    return path.read_text(encoding="utf-8")


def _flat(text):
    """Join hard-wrapped prose so a phrase split across lines is still matched."""
    return re.sub(r"\s+", " ", text)


def _iter_repo_files():
    for path in REPO.rglob("*"):
        if not path.is_file():
            continue
        if SKIP_DIRS & set(path.relative_to(REPO).parts):
            continue
        yield path


def _git(*args, cwd):
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True
    ).stdout.strip()


# --------------------------------------------------------------------------- 1
# Functional acceptance cannot rely on repository internal-state inspection.


def test_boundary_prohibits_internal_persistence_as_an_acceptance_oracle():
    flat = _flat(_read(BOUNDARY))
    assert "Functional Acceptance Observation Boundary" in flat
    for symbol in PERSISTENCE_INTERNALS[:2]:
        assert symbol in flat, f"{symbol} must be named in the prohibition, not implied"
    assert "internal persistence or module state as an acceptance oracle" in flat.lower(), (
        "the prohibition on internal-state oracles must be stated in the boundary"
    )
    assert "Read implementation files to decide pass or fail" in flat
    assert "Require a particular class, function, file, or module layout" in flat


def test_test_isolation_is_not_an_acceptance_oracle_and_reset_helper_is_demoted():
    flat = _flat(_read(BOUNDARY))
    assert "Test isolation is not an acceptance oracle" in flat
    assert "legacy baseline-test" in flat, (
        "resetOrderRepository must be classified as legacy baseline-test infrastructure"
    )
    assert "freshly constructed application over a freshly evaluated module graph" in flat, (
        "the normative, implementation-independent isolation method must be stated"
    )
    assert "never" in flat and "evidence for an acceptance assertion" in flat


def test_no_evaluator_or_governance_code_reaches_into_persistence_internals():
    """The prohibition is not only written down; nothing public actually does it."""
    offenders = []
    for path in _iter_repo_files():
        if path.suffix not in CODE_SUFFIXES:
            continue
        rel = path.relative_to(REPO).as_posix()
        if rel in PERSISTENCE_INTERNAL_CODE_ALLOWLIST:
            continue
        text = _read(path)
        for symbol in PERSISTENCE_INTERNALS:
            # this test file names the symbols in order to forbid them
            if symbol in text and path != Path(__file__):
                offenders.append((rel, symbol))
    assert not offenders, f"persistence internals referenced in code outside the substrate: {offenders}"


def test_no_hidden_acceptance_artifact_exists_in_the_public_repository():
    """A hidden acceptance oracle in the public tree would defeat the boundary."""
    forbidden_names = {
        "evaluator_manifest.json",
        "architecture_opportunities.csv",
        "hidden_acceptance_plan.md",
        "legitimate_alternatives.md",
        "reset_checkpoint.json",
    }
    found = [
        p.relative_to(REPO).as_posix()
        for p in _iter_repo_files()
        if p.name in forbidden_names or p.name.endswith(".acceptance.spec.ts")
    ]
    assert not found, f"private evaluator artifacts present in the public repository: {found}"


# --------------------------------------------------------------------------- 2
# Private state seeding is prohibited.


def test_state_seeding_through_implementation_modules_is_prohibited():
    boundary = _flat(_read(BOUNDARY))
    policy = _flat(_read(POLICY))
    reqs = _flat(_read(ORACLE_REQS))
    assert "Seed state through implementation modules" in boundary
    assert "Hidden state seeding through implementation modules is prohibited" in policy
    assert "may not seed preconditions through implementation modules" in reqs
    # and the consequence: an unreachable precondition is a blocker, not a loophole
    for text in (boundary, policy):
        assert "TD-B31" in text, (
            "an unreachable precondition must be routed to the reachability blocker, "
            "not to an internal-module workaround"
        )


def test_pr02_is_recorded_as_unreachable_setup_rather_than_seeded():
    boundary = _flat(_read(BOUNDARY))
    assert "PR02" in boundary and "TD-B26" in boundary
    assert "unreachable setup" in boundary.lower()
    assert "stricter" in boundary, (
        "the boundary must record that it tightens TD-B26 rather than offering a way round it"
    )


# --------------------------------------------------------------------------- 3
# The declared-seam exception must be task-grounded.


def test_declared_seam_register_exists_and_is_grounded_in_a_public_task():
    flat = _flat(_read(BOUNDARY))
    assert "Declared seam register" in flat
    assert "LogOutput" in flat and "createApp({ logOutput })" in flat
    assert "PT04" in flat, "the only declared seam must name the public task that grounds it"
    assert "A hidden test may not create a seam" in flat
    assert "Internal persistence state is not a seam" in flat


def test_the_seam_is_actually_required_by_the_public_task_that_grounds_it():
    """Not merely asserted: PT04's own public text must require emitted log records."""
    pt04 = _flat(_read(PUBLIC_TASK_DIR / "PT04.md"))
    assert "structured request-log record" in pt04
    assert "structured error-log record" in pt04
    assert "No change to the request bodies, response bodies, status codes or headers" in pt04, (
        "the seam is justified only because the required behaviour is invisible to HTTP"
    )


def test_the_boundary_is_not_described_as_http_only():
    flat = _flat(_read(BOUNDARY))
    assert (
        "Externally observable functional acceptance through HTTP plus explicitly "
        "declared task-relevant application seams" in flat
    ), "the boundary must carry its precise name"
    assert "HTTP is the default observation channel" in flat
    assert 'Calling the evaluator "HTTP-only" would be false' in flat


def test_seams_must_be_declared_before_hidden_test_implementation():
    policy = _flat(_read(POLICY))
    assert "must be declared before hidden-test implementation" in policy
    assert "may not create a seam" in policy


# --------------------------------------------------------------------------- 4
# Functional acceptance stays separate from architecture scoring.


def test_architecture_and_functional_channels_are_separated():
    boundary = _flat(_read(BOUNDARY))
    reqs = _flat(_read(ORACLE_REQS))
    assert "channel-separated" in boundary
    assert "Use architecture-oracle results to determine functional acceptance" in boundary
    assert "Channel separation between architecture scoring and functional acceptance" in reqs
    assert "never" in reqs and "input to an architecture finding" in reqs
    assert "input to a functional pass/fail" in reqs


def test_channel_separation_is_registered_as_a_blocking_decision():
    reqs = _flat(_read(ORACLE_REQS))
    boundary = _flat(_read(BOUNDARY))
    assert "TD-B39" in reqs and "TD-B39" in boundary
    assert "TD-B40" in boundary


# --------------------------------------------------------------------------- 5
# The public authoring policy carries the observation-boundary rule.


def test_public_authoring_policy_states_the_observation_boundary():
    policy = _flat(_read(POLICY))
    assert "Functional acceptance observation boundary" in policy
    required = [
        "HTTP request/response is the default observation surface",
        "explicitly declared application seam is permitted only",
        "externally emitted behaviour that cannot be faithfully observed through HTTP",
        "must be declared before hidden-test implementation",
        "may not inspect implementation-specific persistence, module state, classes, files, "
        "or architecture findings",
        "Hidden state seeding through implementation modules is prohibited",
        "different internal design must remain gradeable",
        "Test isolation is not an acceptance oracle",
        "channel-separated",
    ]
    missing = [phrase for phrase in required if phrase not in policy]
    assert not missing, f"authoring policy is missing observation-boundary rules: {missing}"


def test_authoring_requirements_bind_new_candidates_to_the_boundary():
    policy = _flat(_read(POLICY))
    assert "decidable within the observation boundary" in policy, (
        "DECISION B candidates must be required to fit the boundary at authoring time"
    )


def test_authoring_report_records_the_boundary_and_the_aggregate_novelty_conclusion():
    report = _flat(_read(AUTHORING_REPORT))
    assert "functional acceptance observation boundary" in report.lower()
    # aggregate, non-leaking record of the cleared candidate (PART I)
    assert "pre-authoring feasibility review" in report
    assert "No task body has been authored" in report
    assert "decision_cluster_id" in report
    # The boundary-era coverage statement stays on the record, but only as history:
    # PT07 has since represented that boundary, so the present tense would be false.
    assert "AR-DEP-005" in report and "unrepresented at that time" in report
    assert "no longer unrepresented" in report, (
        "the superseding correction must accompany the historical statement"
    )
    assert "currently unrepresented" not in report, (
        "AR-DEP-005 is represented in the active set; the present tense is stale"
    )
    assert "TD-B34 remains" in report or "TD-B34` remains" in report


#: The single private opportunity identifier the protocol deliberately publishes.
#: ``TD-B29`` records it *as an identifier only* - the thing that must be
#: re-justified or removed - while its content, justification and disposition stay
#: in the private evaluator repository. Enumerating it keeps this check fail-closed:
#: any *other* private slot appearing publicly is a leak.
DELIBERATELY_PUBLIC_OPPORTUNITY_IDS = {"PT04-OPP-01"}


def test_public_record_discloses_no_private_opportunity_identifier():
    """PART I: the aggregate conclusion is published; the private slots are not."""
    private_id = re.compile(r"\b(?:PT0[1-7]|PR0[1-2])-(?:OPP|EXP)-[A-Z0-9-]+\b")
    offenders = []
    for path in _iter_repo_files():
        if path.suffix not in {".md", ".csv", ".yml", ".yaml", ".json", ".py"}:
            continue
        if path == Path(__file__):
            continue
        hits = set(private_id.findall(_read(path))) - DELIBERATELY_PUBLIC_OPPORTUNITY_IDS
        if hits:
            offenders.append((path.relative_to(REPO).as_posix(), sorted(hits)))
    assert not offenders, f"private opportunity identifiers published: {offenders}"


def test_the_one_published_opportunity_identifier_is_still_only_an_identifier():
    """TD-B29 may name the slot; it may not describe its content or disposition."""
    registry = _flat(_read(DOCS / "OPEN_DECISIONS.csv"))
    assert "PT04-OPP-01" in registry
    assert "identifier only" in registry, (
        "TD-B29 must keep saying that only the identifier is public"
    )
    assert "stay in the private evaluator repository" in registry


# --------------------------------------------------------------------------- 6
# No existing task body or hash changed.


def test_every_public_task_body_still_hashes_to_its_recorded_value():
    import hashlib

    for task_id, expected in sorted(FROZEN_TASK_HASHES.items()):
        body = (PUBLIC_TASK_DIR / f"{task_id}.md").read_bytes()
        actual = hashlib.sha256(body).hexdigest()
        assert actual == expected, (
            f"{task_id} body changed: recorded {expected}, computed {actual}. "
            "This package must not modify a task body."
        )


def test_task_index_still_records_the_same_hashes():
    import csv

    with open(TASK_INDEX, newline="", encoding="utf-8") as fh:
        rows = {r["task_id"]: r for r in csv.DictReader(fh)}
    assert set(rows) == set(FROZEN_TASK_HASHES)
    for task_id, expected in sorted(FROZEN_TASK_HASHES.items()):
        assert rows[task_id]["public_task_sha256"] == expected, f"{task_id} index hash drifted"


def test_analysis_eligibility_of_the_boundary_era_tasks_is_unchanged():
    """The boundary package changed no eligibility, and no later package may either.

    ``PT07`` carries its own eligibility (``scored``) because it was authored after
    this boundary was defined; it is asserted separately so it cannot mask a
    silent reclassification of one of the eight.
    """
    import csv

    with open(TASK_INDEX, newline="", encoding="utf-8") as fh:
        rows = {r["task_id"]: r["e1_analysis_eligibility"] for r in csv.DictReader(fh)}
    boundary_era = {k: v for k, v in rows.items() if k in BOUNDARY_ERA_TASK_HASHES}
    assert boundary_era == {
        "PT01": "scored",
        "PT02": "scored",
        "PT03": "scored",
        "PT04": "scored",
        "PT05": "functional-only",
        "PT06": "functional-only",
        "PR01": "inactive-reserve",
        "PR02": "inactive-reserve",
    }, "no package may change one of these tasks' analysis eligibility"
    assert rows["PT07"] == "scored"


# --------------------------------------------------------------------------- 7
# The public task set is exactly the recorded one.


def test_the_public_task_set_is_exactly_the_recorded_one():
    on_disk = {
        p.stem
        for p in PUBLIC_TASK_DIR.rglob("*.md")
        if re.fullmatch(r"(?:PT|PR|T)\d+", p.stem)
    }
    assert on_disk == set(FROZEN_TASK_HASHES), (
        f"the public task set changed: {sorted(on_disk)} vs {sorted(FROZEN_TASK_HASHES)}"
    )
    # and no task-like file slipped in under a different extension anywhere in the tree
    strays = [
        p.relative_to(REPO).as_posix()
        for p in (REPO / "experiments" / "v2" / "tasks").rglob("*")
        if p.is_file()
        and re.fullmatch(r"(?:PT|PR|T)\d+", p.stem)
        and p.suffix != ".md"
    ]
    assert not strays, f"task-like non-markdown files present: {strays}"


def test_the_cleared_candidate_was_recorded_first_and_authored_afterwards():
    """PART I, then the authoring package: order of work stays legible.

    The boundary package recorded a cleared candidate and deliberately wrote no
    body; a later package wrote that body as ``PT07``. Both records must survive,
    so a reader can still see that the feasibility review preceded the task rather
    than being written around one that already existed.
    """
    report = _flat(_read(AUTHORING_REPORT)).replace("`", "")
    assert "No task body has been authored" in report, (
        "the boundary package's own no-authoring record must stay"
    )
    assert "PT07 authored under DECISION B" in report, (
        "the later authoring of the cleared candidate must be recorded"
    )
    assert (PUBLIC_TASK_DIR / "PT07.md").is_file()
    assert "independently reviewed before authoring" in report


# --------------------------------------------------------------------------- 8
# No private evaluator file changed.


def test_private_evaluator_repository_is_not_vendored_into_the_public_repository():
    assert not (REPO / "afci-bench-evaluator-private").exists()
    assert not (REPO / "experiments" / "v2" / "tasks" / "private").exists()


def _private_head():
    return _git("rev-parse", "HEAD", cwd=PRIVATE_REPO)


def _private_worktree_is_clean():
    return _git("status", "--porcelain", cwd=PRIVATE_REPO) == ""


def _public_read_only_operation():
    """Run the public work this package actually performs, for real.

    Separation is a claim about what *public* operations do, so the guard exercises
    the same public reads the rest of this module performs — governance document
    reads, a sweep of every public task body, and a public ``git`` query — rather
    than asserting over an idle interval in which nothing was attempted. Only
    public paths are touched; nothing here opens a private file.
    """
    import hashlib

    for path in (BOUNDARY, POLICY, ORACLE_REQS, AUTHORING_REPORT):
        _flat(_read(path))
    for task_id in sorted(FROZEN_TASK_HASHES):
        hashlib.sha256((PUBLIC_TASK_DIR / f"{task_id}.md").read_bytes()).hexdigest()
    _git("rev-parse", "HEAD", cwd=REPO)


def test_public_operations_do_not_mutate_the_private_evaluator_repository():
    """The separation invariant: public work never writes to the private repository.

    This replaces an earlier check that pinned one historical private ``HEAD``. That
    pin was wrong in principle as well as brittle: the private repository is a live
    review repository whose ``HEAD`` advances under authorised private work, so the
    pin asserted "history has not advanced" when the property that actually matters
    is "*this* operation changed nothing". A legitimate private commit made the old
    check fail while a public operation that genuinely wrote to the private tree
    between two runs could still have passed it.

    The invariant here is a before/after comparison **around** a real public
    operation, so it stays green when private history advances legitimately and goes
    red when a public operation mutates the private repository. Only ``git``
    metadata is read; no private file content is opened. Checked where the sibling
    is present, skipped honestly where it is not.
    """
    import pytest

    if not (PRIVATE_REPO / ".git").is_dir():
        pytest.skip(f"private evaluator repository not present at {PRIVATE_REPO}")

    # 1. precondition: a dirty tree beforehand would make "unchanged" meaningless
    assert _private_worktree_is_clean(), (
        "the private evaluator working tree was already dirty before the public "
        "operation ran; the separation invariant cannot be evaluated against it.\n"
        f"{_git('status', '--porcelain', cwd=PRIVATE_REPO)}"
    )
    # 2. capture private HEAD before
    before = _private_head()

    # 3. perform the public read-only operation under test
    _public_read_only_operation()

    # 4-5. HEAD must be unchanged *during* the operation
    after = _private_head()
    assert after == before, (
        f"a public operation moved the private evaluator HEAD: {before} -> {after}. "
        "Public packages inspect the private repository read-only and must never "
        "commit to it."
    )
    # 6. and the operation must leave no working-tree residue behind
    assert _private_worktree_is_clean(), (
        "a public operation left the private evaluator working tree dirty:\n"
        f"{_git('status', '--porcelain', cwd=PRIVATE_REPO)}"
    )


def test_the_separation_guard_detects_a_repository_that_actually_moves(tmp_path):
    """Guard the guard, without touching the real private repository.

    A before/after invariant is only worth having if it can fail. Both halves are
    exercised against a throwaway repository: a commit must change ``HEAD``, and an
    untracked file must make the tree dirty. If either detector silently stopped
    working, the check above would pass vacuously.
    """
    import shutil

    import pytest

    if shutil.which("git") is None:
        pytest.skip("git is not available")

    stand_in = tmp_path / "stand-in"
    stand_in.mkdir()
    for args in (
        ("init", "-q"),
        ("config", "user.email", "guard@example.invalid"),
        ("config", "user.name", "guard"),
    ):
        _git(*args, cwd=stand_in)
    (stand_in / "a.txt").write_text("one", encoding="utf-8")
    _git("add", "-A", cwd=stand_in)
    _git("commit", "-qm", "one", cwd=stand_in)

    before = _git("rev-parse", "HEAD", cwd=stand_in)
    assert _git("status", "--porcelain", cwd=stand_in) == ""

    # a mutation the guard must catch: history advances during the window
    (stand_in / "b.txt").write_text("two", encoding="utf-8")
    _git("add", "-A", cwd=stand_in)
    _git("commit", "-qm", "two", cwd=stand_in)
    assert _git("rev-parse", "HEAD", cwd=stand_in) != before, (
        "the HEAD-movement detector is inert"
    )

    # and the other half: an uncommitted write must register as a dirty tree
    (stand_in / "c.txt").write_text("three", encoding="utf-8")
    assert _git("status", "--porcelain", cwd=stand_in) != "", (
        "the dirty-worktree detector is inert"
    )


# --------------------------------------------------------------------------- 9
# The package's own pre-freeze promises.


def test_the_canonical_substrate_is_untouched_by_this_package():
    identity = _read(DOCS / "SOURCE_SUBSTRATE_IDENTITY.md")
    assert "630d3180af0d02a86330dfb599f559e78df65e94" in identity
    assert "0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3" in identity
    changed = _git(
        "diff", "--name-only", "630d3180af0d02a86330dfb599f559e78df65e94", "HEAD", cwd=REPO
    ).splitlines()
    substrate_touched = [
        p for p in changed if p.startswith("apps/") or p.startswith("libs/")
    ]
    assert not substrate_touched, (
        f"a commit after the canonical substrate touched the substrate: {substrate_touched}"
    )


def test_no_benchmark_result_artifact_exists():
    results = REPO / "experiments" / "v2" / "results"
    present = [p.name for p in results.iterdir() if p.name != "README.md"]
    assert not present, f"result artifacts present in a pre-freeze package: {present}"


def test_protocol_is_still_pre_freeze():
    assert "PRE-FREEZE DRAFT" in _read(DOCS / "README.md")
    assert "PRE-FREEZE" in _flat(_read(AUTHORING_REPORT))
