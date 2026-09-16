"""`SL-V2-EFF-ABORT-01` / `SL-V2-EFF-RESTART-01` — reset-aware run identity.

**The defect this closes.** `derive_run_id` hashed the run's content identity —
purpose, task, condition, task sha, substrate hash, mode — and, since
`SL-RUNID-01`, the repetition index. It did **not** hash the reset state. The
`AFCI_EFFICIENCY_PILOT` crosses every cell with `NON_RESET` and `RESET`, so the
two arms of one (task, condition, repetition) derived the SAME run id and the
same artifact directory: 18 collisions across the frozen 36-row schedule.

Attempt 1 of the pilot hit one of them at scientific sequence 9. Sequence 6
(`PT01 / C4 / RESET / R2`) had completed and written its governed record;
sequence 9 (`PT01 / C4 / NON_RESET / R2`) derived the same directory, delivered
its task to the model, ran to completion, and then refused in `CAPTURE_WORKTREE`
because the destination already held sequence 6's `worktree_post_run` — writing
its refusal record over sequence 6's completed one on the way out.

**What the fix is, and is not.** The reset state joins the seed and the readable
prefix, and an execution-attempt namespace joins both so the replacement
execution cannot land on Attempt 1's artifacts. A pre-invocation ownership guard
refuses a destination that cannot be proved new, BEFORE any prompt is delivered.
This is an ARTIFACT-IDENTITY and ARTIFACT-SAFETY change: no task body, no
condition, no budget, no metric, no threshold and no scientific claim moves, and
nothing already written is rewritten.

No model is invoked anywhere in this module.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import efficiency_pilot_analysis as epa
import efficiency_run_plan as erp
import execution_attempt as ea
import functional_evaluation as fe
import reset_budget as rb
import run_artifacts as art
import run_governance as gov
import run_v2

REPO = Path(__file__).resolve().parents[4]
SCHEMA = json.loads(
    (REPO / "experiments" / "v2" / "harness" / "run_record.schema.json").read_text(
        encoding="utf-8"
    )
)
PILOT = gov.RUN_PURPOSES["AFCI_EFFICIENCY_PILOT"]

#: One pilot cell, as the frozen schedule states it. Everything except the reset
#: state is held fixed, because the reset state is the value under test.
CELL = dict(
    purpose="AFCI_EFFICIENCY_PILOT",
    task_id="PT01",
    condition="C4",
    task_sha="6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39",
    substrate_hash=gov.SUBSTRATE_CONTENT_HASH,
    mode="real",
    repetition=2,
)


# --------------------------------------------------------------------------- #
# PART C. The root cause, reproduced.
# --------------------------------------------------------------------------- #
def test_the_pre_repair_seed_ignored_the_reset_state():
    """Guard the guard: the defect was real, and this is exactly its shape.

    The pre-repair seed is reconstructed here rather than described, so the test
    fails if someone later claims the collision never existed.
    """
    seed = "|".join(
        [
            CELL["purpose"], CELL["task_id"], CELL["condition"], CELL["task_sha"],
            CELL["substrate_hash"], CELL["mode"], f"r{CELL['repetition']}",
        ]
    )
    both = {seed for _ in rb.RESET_STATES}
    assert len(both) == 1, (
        "the pre-repair seed carried no reset state, so RESET and NON_RESET of "
        "one cell hashed identically; that is the defect this module closes"
    )


def test_reset_and_non_reset_of_one_cell_derive_different_ids():
    non_reset = art.derive_run_id(**CELL, reset_state=rb.NON_RESET)
    reset = art.derive_run_id(**CELL, reset_state=rb.RESET)
    assert non_reset != reset, (
        f"the two arms of one pilot cell still collide: {non_reset}"
    )


def test_the_reset_state_is_visible_in_the_id_without_hashing_anything():
    assert "-non-reset-" in art.derive_run_id(**CELL, reset_state=rb.NON_RESET)
    assert "-reset-" in art.derive_run_id(**CELL, reset_state=rb.RESET)


def test_the_reset_state_must_be_the_canonical_governed_value():
    """PART D: never inferred from a path, a prompt or a lowercase spelling."""
    for bad in ("reset", "non_reset", "RESET_STATE", "A", "", "Reset"):
        with pytest.raises(gov.RunnerRefusal) as excinfo:
            art.derive_run_id(**CELL, reset_state=bad)
        assert excinfo.value.code == gov.RESET_STATE_INVALID


# --------------------------------------------------------------------------- #
# PART N.1-6. Determinism, and every other axis still separating runs.
# --------------------------------------------------------------------------- #
def test_the_same_row_in_the_same_attempt_is_deterministic():
    first = art.derive_run_id(
        **CELL, reset_state=rb.RESET, execution_attempt=ea.REPLACEMENT_ATTEMPT
    )
    second = art.derive_run_id(
        **CELL, reset_state=rb.RESET, execution_attempt=ea.REPLACEMENT_ATTEMPT
    )
    assert first == second


def test_the_same_row_in_a_different_attempt_derives_a_different_id():
    ids = {
        art.derive_run_id(**CELL, reset_state=rb.RESET, execution_attempt=a)
        for a in (1, 2, 3)
    }
    assert len(ids) == 3


@pytest.mark.parametrize(
    "field,value",
    [
        ("repetition", 3),
        ("condition", "C1"),
        ("task_id", "PT07"),
        ("task_sha", "0" * 64),
        ("substrate_hash", "1" * 64),
        ("mode", "dry-run"),
    ],
)
def test_every_pre_existing_identity_axis_still_separates_runs(field, value):
    other = {**CELL, field: value}
    assert art.derive_run_id(
        **CELL, reset_state=rb.RESET, execution_attempt=2
    ) != art.derive_run_id(**other, reset_state=rb.RESET, execution_attempt=2)


@pytest.mark.parametrize("bad", [0, -1, 1000, "2", 2.0, True, None])
def test_an_ungoverned_execution_attempt_is_refused(bad):
    if bad is None:  # None means "not declared" and is the legacy form
        assert art.derive_run_id(**CELL, execution_attempt=None) == art.derive_run_id(
            **CELL
        )
        return
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        art.derive_run_id(**CELL, execution_attempt=bad)
    assert excinfo.value.code == gov.EXECUTION_ATTEMPT_INVALID


# --------------------------------------------------------------------------- #
# PART E / N.19-22. Historical identity is untouched.
# --------------------------------------------------------------------------- #
#: The ids the PT08 / PT09 / PT10 diagnostics were actually written with. They
#: are pinned as literals because the point of the check is that a later change
#: to the derivation cannot move them; re-deriving both sides would prove nothing.
HISTORICAL_RUN_IDS = {
    "PT08": dict(
        purpose="PT08_DIFFICULTY_DIAGNOSTIC", task_id="PT08", condition="C1",
        task_sha="a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2",
        substrate_hash=gov.SUBSTRATE_CONTENT_HASH, mode="real",
    ),
    "PT09": dict(
        purpose="INSTRUMENT_QUALIFICATION_DIAGNOSTIC", task_id="PT09", condition="C1",
        task_sha=gov.expected_task_sha256("PT09"),
        substrate_hash=gov.SUBSTRATE_CONTENT_HASH, mode="real",
    ),
    "PT10": dict(
        purpose="INSTRUMENT_QUALIFICATION_DIAGNOSTIC", task_id="PT10", condition="C1",
        task_sha=gov.expected_task_sha256("PT10"),
        substrate_hash=gov.SUBSTRATE_CONTENT_HASH, mode="real",
    ),
}


@pytest.mark.parametrize("task", sorted(HISTORICAL_RUN_IDS))
def test_a_historical_purpose_derives_exactly_the_id_it_always_did(task):
    """A purpose that predates reset-aware identity keeps its identifiers.

    Reconstructed from the SL-RUNID-01 seed, which is the form every artifact on
    disk for these three purposes was written under.
    """
    seed_fields = HISTORICAL_RUN_IDS[task]
    for repetition in (1, 2, 3):
        seed = "|".join(
            [
                seed_fields["purpose"], seed_fields["task_id"],
                seed_fields["condition"], seed_fields["task_sha"],
                seed_fields["substrate_hash"], seed_fields["mode"],
                f"r{repetition}",
            ]
        )
        digest = art.sha256_bytes(seed.encode("utf-8"))[:12]
        expected = (
            f"{seed_fields['purpose'].lower().replace('_', '-')}-"
            f"{seed_fields['task_id'].lower()}-{seed_fields['condition'].lower()}-"
            f"{seed_fields['mode']}-r{repetition}-{digest}"
        )
        assert art.derive_run_id(**seed_fields, repetition=repetition) == expected


def test_a_historical_purpose_can_never_acquire_a_reset_state():
    """The reset state is a property of a reset-aware purpose, not of the id."""
    for task, fields in HISTORICAL_RUN_IDS.items():
        legacy = art.derive_run_id(**fields, repetition=1)
        assert "-reset-" not in legacy and "-a2-" not in legacy


def test_a_record_written_before_this_package_still_validates(tmp_path):
    result = run_v2.run(
        run_v2.RunRequest(
            task_id="PT08", condition="C1",
            run_purpose="PT08_DIFFICULTY_DIAGNOSTIC",
            artifact_root=tmp_path / "legacy", generated_at="fixture",
            keep_worktree=False,
        )
    )
    assert result.record is not None, result.refusal_code
    assert "execution_attempt" not in result.record, (
        "a purpose that declares no execution attempt must produce the record it "
        "produced before this package, field for field"
    )
    assert "run_identity" not in result.record
    art.validate_run_record(result.record, SCHEMA)


def test_the_new_identity_fields_are_optional_in_the_schema():
    props = SCHEMA["properties"]
    assert "execution_attempt" in props and "run_identity" in props
    assert "execution_attempt" not in SCHEMA["required"]
    assert "run_identity" not in SCHEMA["required"]


# --------------------------------------------------------------------------- #
# PART I / N.7-9, 17-18. The WHOLE schedule, before row 1.
# --------------------------------------------------------------------------- #
ROOT = Path("/afci-runs")  # never touched; identity derivation does no I/O


@pytest.fixture(scope="module")
def schedule():
    return erp.load_plan()


@pytest.fixture(scope="module")
def attempt_2(schedule):
    return ea.derive_schedule_identities(
        schedule,
        execution_attempt=ea.REPLACEMENT_ATTEMPT,
        artifact_root=ea.attempt_artifact_root(ROOT, ea.REPLACEMENT_ATTEMPT),
    )


def test_all_thirty_six_replacement_rows_derive_distinct_run_ids(attempt_2):
    assert len(attempt_2) == erp.EXPECTED_RUNS
    assert len({i.run_id for i in attempt_2}) == erp.EXPECTED_RUNS


def test_all_thirty_six_replacement_rows_derive_distinct_artifact_dirs(attempt_2):
    assert len({i.artifact_dir for i in attempt_2}) == erp.EXPECTED_RUNS
    assert ea.identity_problems(attempt_2) == []


def test_the_aborted_execution_really_did_derive_only_eighteen(schedule):
    """The defect, measured on the real schedule rather than on one cell."""
    aborted = ea.attempt_1_identities(schedule, artifact_root=ROOT)
    assert len(aborted) == erp.EXPECTED_RUNS
    assert len({i.run_id for i in aborted}) == erp.EXPECTED_RUNS // 2
    assert len(ea.identity_problems(aborted)) == erp.EXPECTED_RUNS, (
        "36 rows over 18 ids is 18 duplicate run ids and 18 duplicate "
        "directories: 36 reported problems"
    )


def test_the_replacement_shares_no_identity_with_the_aborted_execution(
    schedule, attempt_2
):
    aborted = ea.attempt_1_identities(schedule, artifact_root=ROOT)
    assert ea.overlap_problems(attempt_2, aborted) == []
    assert {i.run_id for i in attempt_2}.isdisjoint({i.run_id for i in aborted})
    assert {Path(i.artifact_dir).name for i in attempt_2}.isdisjoint(
        {Path(i.artifact_dir).name for i in aborted}
    )


def test_a_duplicate_anywhere_in_the_schedule_refuses_the_whole_execution(
    schedule, tmp_path
):
    """PART I: the refusal is global and lands BEFORE row 1, not at the row."""
    duplicated = json.loads(json.dumps(schedule))
    # Make row 36 a copy of row 1's cell, keeping its sequence number: the two
    # now derive one identity, exactly as the two arms of a cell used to.
    for field in ("task_id", "condition", "reset_state", "repetition"):
        duplicated["runs"][35][field] = duplicated["runs"][0][field]

    report = ea.preflight(
        artifact_root=tmp_path / "attempt-2",
        isolation_home=tmp_path / "nowhere-home",
        isolation_ancestors=[],
        plan=duplicated,
    )
    assert report.eligible is False
    codes = {code for code, _ in report.problems}
    assert gov.EFFICIENCY_SCHEDULE_IDENTITY_COLLISION in codes
    assert any("sequence 1" in d and "sequence 36" in d for _, d in report.problems)


def test_the_corrected_schedule_passes_the_global_preflight(tmp_path):
    report = ea.preflight(
        artifact_root=tmp_path / "ext" / "attempt-2",
        sterile_base=tmp_path / "ext" / "sterile-2",
        isolation_home=tmp_path / "nowhere-home",
        isolation_ancestors=[tmp_path / "ext"],
    )
    assert report.eligible is True, report.problems
    payload = report.to_dict()
    assert payload["row_count"] == erp.EXPECTED_RUNS
    assert payload["unique_run_ids"] == erp.EXPECTED_RUNS
    assert payload["unique_artifact_dirs"] == erp.EXPECTED_RUNS
    assert payload["substantive_observations"] == 0
    assert payload["model_invoked"] is False
    assert {c["status"] for c in payload["checks"]} == {"PASS"}


def test_the_preflight_writes_nothing_and_creates_nothing(tmp_path):
    """A preflight that populated the destinations it checks would BE the defect."""
    root = tmp_path / "ext" / "attempt-2"
    ea.preflight(
        artifact_root=root,
        isolation_home=tmp_path / "nowhere-home",
        isolation_ancestors=[tmp_path / "ext"],
    )
    assert not root.exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == []


def test_every_reset_row_allocates_two_distinct_session_phases(schedule):
    slots = ea.session_slots(schedule)
    assert len(slots) == 54, "18 non-reset rows + 18 reset rows x 2 phases"
    assert len(set(slots)) == 54
    for row in schedule["runs"]:
        phases = [p for s, p in slots if s == row["sequence"]]
        if row["reset_state"] == rb.RESET:
            assert sorted(phases) == sorted(rb.PHASES)
            assert phases[0] != phases[1]
        else:
            assert phases == [None]
    assert ea.session_allocation_problems(schedule) == []


def test_a_session_factory_that_reused_an_identity_is_refused(schedule):
    problems = ea.session_allocation_problems(
        schedule, session_id_factory=lambda: "the-same-session-every-time"
    )
    assert any(c == gov.RESET_PHASE_SESSION_REUSED for c, _ in problems)


# --------------------------------------------------------------------------- #
# PART G / N.10-16. The pre-invocation ownership guard.
# --------------------------------------------------------------------------- #
def _occupied_like_attempt_1(run_dir: Path) -> dict:
    """A directory holding a completed observation, as Attempt 1 left one.

    Deliberately carries NO ownership marker: the marker did not exist when
    Attempt 1 ran, so every one of its directories is unattributable, and that
    is the exact state the guard has to refuse.
    """
    run_dir.mkdir(parents=True)
    (run_dir / "run_record.json").write_text(
        json.dumps({"run_id": "the-previous-observation", "outcome": "COMPLETE"}),
        encoding="utf-8",
    )
    (run_dir / "context_audit.json").write_text('{"verdict": "CLEAN"}', encoding="utf-8")
    (run_dir / "prepared_manifest.json").write_text('{"entry_count": 49}', encoding="utf-8")
    (run_dir / "launch_manifest.json").write_text('{"argv": ["claude"]}', encoding="utf-8")
    (run_dir / "readiness.json").write_text('{"run_eligible": true}', encoding="utf-8")
    (run_dir / "phase_a_runtime_evidence.jsonl").write_text("{}\n", encoding="utf-8")
    (run_dir / "worktree").mkdir()
    (run_dir / "worktree" / "stale.ts").write_text("// the previous run's", encoding="utf-8")
    capture = run_dir / "worktree_post_run"
    capture.mkdir()
    (capture / "captured.ts").write_text("// the previous run's EVIDENCE", encoding="utf-8")
    return {
        p.relative_to(run_dir).as_posix(): art.sha256_file(p)
        for p in sorted(run_dir.rglob("*"))
        if p.is_file()
    }


def _colliding_dry_run(tmp_path, root):
    return run_v2.run(
        run_v2.RunRequest(
            task_id="PT08", condition="C1",
            run_purpose="PT08_DIFFICULTY_DIAGNOSTIC",
            artifact_root=root, generated_at="fixture", keep_worktree=False,
        )
    )


@pytest.fixture
def collision(tmp_path):
    """A run whose derived destination is already occupied by another observation."""
    root = tmp_path / "runs"
    run_id = art.derive_run_id(
        purpose="PT08_DIFFICULTY_DIAGNOSTIC", task_id="PT08", condition="C1",
        task_sha=gov.expected_task_sha256("PT08"),
        substrate_hash=gov.SUBSTRATE_CONTENT_HASH, mode="dry-run", repetition=1,
    )
    run_dir = root / run_id
    before = _occupied_like_attempt_1(run_dir)
    result = _colliding_dry_run(tmp_path, root)
    after = {
        p.relative_to(run_dir).as_posix(): art.sha256_file(p)
        for p in sorted(run_dir.rglob("*"))
        if p.is_file()
    }
    return result, run_dir, before, after


def test_an_occupied_destination_refuses(collision):
    result, _, _, _ = collision
    assert result.refusal_code == gov.ARTIFACT_IDENTITY_COLLISION_PREINVOCATION


def test_the_collision_refusal_reaches_no_model_invocation_state(collision):
    """N.11. Proved from the state machine, not from the absence of a process.

    The refusal lands in ``PRECHECK``. Attempt 1's landed in ``CAPTURE_WORKTREE``
    -- five states and one completed model run later -- which is the whole
    difference between this guard and the one that existed.
    """
    result, _, _, _ = collision
    assert result.machine.current == "PRECHECK"
    for state in ("PREPARE_WORKTREE", "CONTEXT_AUDIT", "BUILD_FRESH_LAUNCH",
                  "MODEL_INVOCATION", "CAPTURE_WORKTREE"):
        assert not result.machine.reached(state), (
            f"the refusal reached {state}; a destination that cannot be proved "
            "new must refuse before anything is prepared or delivered"
        )


def test_the_collision_refusal_preserves_every_previous_byte(collision):
    _, _, before, after = collision
    assert after == before, "the colliding run altered the previous observation"


@pytest.mark.parametrize(
    "artifact",
    ["run_record.json", "context_audit.json", "prepared_manifest.json",
     "launch_manifest.json", "readiness.json"],
)
def test_the_collision_refusal_overwrites_no_governed_artifact(collision, artifact):
    """N.13-15, named one at a time so a failure says which one moved."""
    _, _, before, after = collision
    assert after[artifact] == before[artifact]


def test_the_collision_refusal_does_not_delete_the_captured_worktree(collision):
    """N.16. The artifact Attempt 1's refusal would have had to delete to proceed."""
    _, run_dir, before, after = collision
    capture = run_dir / "worktree_post_run" / "captured.ts"
    assert capture.is_file()
    assert after["worktree_post_run/captured.ts"] == before["worktree_post_run/captured.ts"]


def test_the_collision_refusal_writes_no_ownership_marker(collision):
    _, run_dir, _, _ = collision
    assert not (run_dir / art.OWNERSHIP_MARKER).exists(), (
        "a refused run must not stamp its own identity onto someone else's "
        "directory on the way out"
    )


def test_a_foreign_marker_refuses_even_with_no_other_material(tmp_path):
    run_dir = tmp_path / "runs" / "some-run"
    run_dir.mkdir(parents=True)
    (run_dir / art.OWNERSHIP_MARKER).write_text(
        json.dumps({"run_id": "someone-else"}), encoding="utf-8"
    )
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        art.assert_destination_ownable(
            run_dir, identity={"run_id": "me"}, spends_an_observation=False
        )
    assert excinfo.value.code == gov.ARTIFACT_IDENTITY_COLLISION_PREINVOCATION


def test_a_real_run_never_re_enters_its_own_spent_directory(tmp_path):
    """The rule a dry run is exempt from: a paid observation is spent once."""
    identity = {"run_id": "mine"}
    run_dir = tmp_path / "runs" / "mine"
    run_dir.mkdir(parents=True)
    (run_dir / art.OWNERSHIP_MARKER).write_text(
        json.dumps(identity), encoding="utf-8"
    )
    (run_dir / "run_record.json").write_text("{}", encoding="utf-8")

    # A dry run may re-enter it; it spends nothing and observes nothing.
    assert art.assert_destination_ownable(
        run_dir, identity=identity, spends_an_observation=False
    ).status == art.OWNERSHIP_OWNED

    with pytest.raises(gov.RunnerRefusal) as excinfo:
        art.assert_destination_ownable(
            run_dir, identity=identity, spends_an_observation=True
        )
    assert excinfo.value.code == gov.ARTIFACT_IDENTITY_COLLISION_PREINVOCATION


# --------------------------------------------------------------------------- #
# PART H. Destructive reuse.
# --------------------------------------------------------------------------- #
def _owned_directory(tmp_path) -> art.ArtifactDirectory:
    return art.ArtifactDirectory(
        tmp_path / "runs", "owned", PILOT, identity={"run_id": "owned"}
    ).create()


def test_the_captured_worktree_can_never_be_removed_as_temporary_state(tmp_path):
    directory = _owned_directory(tmp_path)
    directory.worktree_post_run.mkdir()
    (directory.worktree_post_run / "evidence.ts").write_text("x", encoding="utf-8")
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        directory.remove_temporary(directory.worktree_post_run)
    assert excinfo.value.code == gov.ARTIFACT_DESTRUCTIVE_REUSE_REFUSED
    assert (directory.worktree_post_run / "evidence.ts").is_file()


@pytest.mark.parametrize("escape", ["..", "../..", "../sibling"])
def test_a_delete_can_never_reach_outside_the_run_directory(tmp_path, escape):
    directory = _owned_directory(tmp_path)
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        directory.remove_temporary(directory.run_dir / escape)
    assert excinfo.value.code == gov.ARTIFACT_DESTRUCTIVE_REUSE_REFUSED


def test_a_directory_that_never_proved_ownership_may_delete_nothing(tmp_path):
    directory = art.ArtifactDirectory(tmp_path / "runs", "unopened", PILOT)
    directory.run_dir.mkdir(parents=True)
    (directory.worktree).mkdir()
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        directory.remove_temporary(directory.worktree)
    assert excinfo.value.code == gov.ARTIFACT_DESTRUCTIVE_REUSE_REFUSED
    assert directory.worktree.is_dir()


def test_a_run_may_still_rebuild_its_own_prepared_worktree(tmp_path):
    directory = _owned_directory(tmp_path)
    directory.worktree.mkdir()
    (directory.worktree / "stale.ts").write_text("x", encoding="utf-8")
    directory.remove_temporary(directory.worktree)
    assert not directory.worktree.exists()


# --------------------------------------------------------------------------- #
# PART J / N.24-25. Execution-root isolation.
# --------------------------------------------------------------------------- #
def test_a_root_beneath_the_user_profile_is_refused(tmp_path):
    home = tmp_path / "home" / "operator"
    root = home / "AppData" / "Local" / "Temp" / "afci-runs"
    root.mkdir(parents=True)
    problems = art.execution_root_isolation_problems(
        root, home=home, ancestors=[]
    )
    assert problems, "a root inside the operator's profile must be refused"
    assert all(c == gov.ARTIFACT_ROOT_NOT_ISOLATED for c, _ in problems)
    assert "descends from the active user profile" in problems[0][1]


def test_a_root_whose_ancestor_chain_carries_host_claude_material_is_refused(tmp_path):
    """Attempt 1's actual finding, reproduced with a synthetic ancestor."""
    base = tmp_path / "profile"
    (base / ".claude" / "agents").mkdir(parents=True)
    (base / ".claude" / "agents" / "an-agent.md").write_text("x", encoding="utf-8")
    root = base / "runs" / "attempt-2"
    root.mkdir(parents=True)
    problems = art.execution_root_isolation_problems(
        root, home=tmp_path / "elsewhere", ancestors=[base, base / "runs"]
    )
    assert problems
    assert any(".claude" in d for _, d in problems)
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        art.assert_execution_root_isolated(
            root, label="artifact root",
            home=tmp_path / "elsewhere", ancestors=[base, base / "runs"],
        )
    assert excinfo.value.code == gov.ARTIFACT_ROOT_NOT_ISOLATED


def test_an_approved_external_root_is_eligible(tmp_path):
    external = tmp_path / "volume" / "afci-runs"
    root = external / "attempt-2"
    root.mkdir(parents=True)
    assert art.execution_root_isolation_problems(
        root, home=tmp_path / "home", ancestors=[external, tmp_path / "volume"]
    ) == []
    assert art.assert_execution_root_isolated(
        root, label="artifact root",
        home=tmp_path / "home", ancestors=[external, tmp_path / "volume"],
    ) == root.resolve()


def test_only_the_pilot_carries_the_isolation_requirement():
    assert PILOT.requires_isolated_execution_root == "SL-V2-EFF-RESTART-01"
    for name, purpose in gov.RUN_PURPOSES.items():
        if name != "AFCI_EFFICIENCY_PILOT":
            assert purpose.requires_isolated_execution_root is None, (
                f"{name} executed under roots this requirement would refuse; "
                "retro-fitting it would invalidate artifacts produced correctly"
            )


# --------------------------------------------------------------------------- #
# PART F. The attempt namespace.
# --------------------------------------------------------------------------- #
def test_the_namespace_is_relative_and_attempt_scoped(tmp_path):
    assert ea.attempt_namespace(2) == "attempt-2"
    assert ea.attempt_artifact_root(tmp_path, 2) == tmp_path / "attempt-2"
    assert ea.attempt_namespace(1) != ea.attempt_namespace(2)


def test_a_namespace_is_never_derived_from_an_undeclared_attempt():
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        ea.attempt_namespace(None)
    assert excinfo.value.code == gov.EXECUTION_ATTEMPT_INVALID


def test_the_runner_records_the_attempt_and_how_it_derived_its_id(tmp_path):
    result = run_v2.run(
        run_v2.RunRequest(
            task_id="PT01", condition="C4", run_purpose=PILOT.name,
            mode="dry-run", reset_state=rb.NON_RESET, repetition=2,
            execution_attempt=ea.REPLACEMENT_ATTEMPT,
            artifact_root=tmp_path / "runs", generated_at="fixture",
            keep_worktree=False,
        )
    )
    assert result.record is not None, result.refusal_code
    assert result.record["execution_attempt"] == ea.REPLACEMENT_ATTEMPT
    identity = result.record["run_identity"]
    assert identity["reset_state"] == rb.NON_RESET
    assert identity["execution_attempt"] == ea.REPLACEMENT_ATTEMPT
    assert identity["run_id"] == result.record["run_id"]
    assert identity["algorithm_version"] == art.IDENTITY_ALGORITHM_RESET_AWARE
    art.validate_run_record(result.record, SCHEMA)


def test_the_two_arms_of_one_cell_now_write_into_two_directories(tmp_path):
    """The behavioural statement: the defect, run rather than described."""
    dirs = []
    for state in rb.RESET_STATES:
        result = run_v2.run(
            run_v2.RunRequest(
                task_id="PT01", condition="C4", run_purpose=PILOT.name,
                mode="dry-run", reset_state=state, repetition=2,
                execution_attempt=ea.REPLACEMENT_ATTEMPT,
                artifact_root=tmp_path / "shared", generated_at="fixture",
                keep_worktree=False,
            )
        )
        assert result.record is not None, result.refusal_code
        dirs.append(result.run_dir)
    assert dirs[0] != dirs[1], "the two arms of one cell still share a directory"
    assert dirs[0].is_dir() and dirs[1].is_dir()


def test_the_cli_exposes_the_execution_attempt():
    parser = run_v2._build_parser()
    args = parser.parse_args(
        ["--task", "PT01", "--condition", "C4", "--run-purpose", PILOT.name,
         "--dry-run", "--reset-state", rb.NON_RESET, "--execution-attempt", "2"]
    )
    assert args.execution_attempt == 2
    default = parser.parse_args(
        ["--task", "PT01", "--condition", "C4", "--run-purpose", PILOT.name,
         "--dry-run", "--reset-state", rb.NON_RESET]
    )
    assert default.execution_attempt is None, (
        "an omitted flag must stay UNDECLARED rather than being pre-filled with "
        "1, which would relabel every historical artifact as attempt 1"
    )


# --------------------------------------------------------------------------- #
# PART L / N.26. The scientific schedule is not touched by a restart.
# --------------------------------------------------------------------------- #
def test_the_committed_scientific_schedule_keeps_its_hash():
    body = (REPO / erp.RUN_PLAN_PATH).read_bytes()
    assert art.sha256_bytes(body) == ea.ORIGINAL_SCIENTIFIC_PLAN_SHA256
    assert erp.plan_sha256(json.loads(body)) == ea.ORIGINAL_SCIENTIFIC_PLAN_SHA256


def test_the_replacement_plan_projects_the_original_order_row_for_row(schedule):
    replacement = ea.load_execution_plan()
    projected = [
        (r["sequence"], r["task_id"], r["condition"], r["reset_state"],
         r["repetition"])
        for r in replacement["identities"]
    ]
    assert projected == [tuple(r) for r in ea.scientific_projection(schedule)]
    assert projected[5][1:] == ("PT01", "C4", rb.RESET, 2), "sequence 6 moved"
    assert projected[8][1:] == ("PT01", "C4", rb.NON_RESET, 2), "sequence 9 moved"


def test_the_replacement_plan_records_both_hashes_and_the_attempt():
    replacement = ea.load_execution_plan()
    assert replacement["execution_attempt"] == ea.REPLACEMENT_ATTEMPT
    assert replacement["supersedes_execution_attempt"] == ea.ABORTED_ATTEMPT
    assert replacement["abort_authority"] == ea.ABORT_DECISION
    assert replacement["authority"] == ea.RESTART_DECISION
    assert replacement["original_scientific_plan_sha256"] == (
        ea.ORIGINAL_SCIENTIFIC_PLAN_SHA256
    )
    assert replacement["reuses_any_attempt_1_observation"] is False
    for flag in ("is_result", "scored", "enters_confirmatory_dataset"):
        assert replacement[flag] is False
    assert replacement["seed"] == erp.SEED, "a restart never chooses a new seed"


def test_the_replacement_plan_on_disk_is_the_one_this_module_derives(tmp_path):
    """The artifact is DERIVED, so a hand-edit is a mechanical failure."""
    committed = ea.load_execution_plan()
    rebuilt = ea.build_execution_plan(
        execution_attempt=committed["execution_attempt"],
        artifact_root=Path(committed["artifact_root"]),
        sterile_base=Path(committed["sterile_base"]),
    )
    assert ea.plan_sha256(rebuilt) == ea.plan_sha256(committed)


def test_the_projection_hash_is_free_of_every_infrastructure_field(schedule):
    replacement = ea.load_execution_plan()
    assert replacement["scientific_projection_sha256"] == ea.projection_sha256(
        schedule
    )
    # And the two plan artifacts' PHYSICAL hashes legitimately differ.
    assert ea.plan_sha256(replacement) != ea.ORIGINAL_SCIENTIFIC_PLAN_SHA256


# --------------------------------------------------------------------------- #
# PART K / N.27. Scientific invariance.
# --------------------------------------------------------------------------- #
def test_the_frozen_scientific_values_are_unchanged():
    plan = erp.load_plan()
    assert gov.architecture_context_sha256() == (
        "bf6f32b162a23b851596d8b489d938bef10d0b8616a50dcc039873d12ffa7a4d"
    )
    assert plan["task_sha256"] == {
        "PT01": "6c938822fe19cd6e87942a6ee24ec8f604c0883da1b7f80d45216be35d7c9c39",
        "PT04": "f349b150b1d8fe5676fed8460b1840b988ee2bb0a78b1966ef82ae9ce9c8a9b5",
        "PT07": "557caed09420354efbc823c8b72e54b0760ac72847aba0d9c07d99e37ff7d2d7",
    }
    assert plan["model_id"] == "claude-sonnet-5"
    assert plan["runtime_version"] == "2.1.229"
    assert (rb.PRE_RESET_MAX_TURNS, rb.POST_RESET_MAX_TURNS,
            rb.NON_RESET_MAX_TURNS) == (32, 32, 64)
    assert rb.PRE_RESET_MAX_TURNS + rb.POST_RESET_MAX_TURNS == rb.NON_RESET_MAX_TURNS
    assert plan["block_count"] == 18 and plan["run_count"] == 36
    assert tuple(plan["tasks"]) == ("PT01", "PT04", "PT07")
    assert tuple(plan["conditions"]) == ("C1", "C4")
    assert tuple(plan["reset_states"]) == (rb.NON_RESET, rb.RESET)
    assert tuple(plan["repetitions"]) == (1, 2, 3)


def test_the_frozen_metrics_and_thresholds_are_unchanged():
    assert epa.PRIMARY_ENDPOINT == "TOTAL_INPUT_TOKENS"
    assert epa.MINIMUM_ELIGIBLE_PAIRS == 12
    assert epa.MAX_C4_FUNCTIONAL_DEFICIT == 1
    assert epa.STRONG_GO_MEDIAN_TOKEN_RATIO == 0.90
    assert epa.STRONG_GO_C4_CHEAPER_FRACTION == 0.60
    assert epa.STRONG_GO_TASK_MAJORITY == 2
    assert epa.QUALIFIED_GO_MEDIAN_TOKEN_RATIO == 1.10
    assert epa.RESET_SPECIFIC_GO_MEDIAN_TOKEN_RATIO == 1.10
    assert epa.FUNCTIONAL_VALIDITY_SOURCE == (
        "record.functional_evaluation.functional_valid"
    )
    assert fe.FUNCTIONAL_EVALUATION_AUTHORITY == "SL-V2-EFF-FUNC-01"


# --------------------------------------------------------------------------- #
# PART A.8-9. The exclusion is ENFORCED, not merely declared.
# --------------------------------------------------------------------------- #
def test_the_replacement_attempt_constant_agrees_across_modules():
    """The analysis restates it to stay standalone; the restatement is checked."""
    assert epa.REPLACEMENT_EXECUTION_ATTEMPT == ea.REPLACEMENT_ATTEMPT
    assert epa.ABORTED_EXECUTION_ATTEMPT == ea.ABORTED_ATTEMPT
    assert epa.ABORT_DECISION == ea.ABORT_DECISION


def test_the_frozen_analysis_is_still_computable():
    """PART P: it runs end to end over synthetic records and emits a decision."""
    report = epa.self_check()
    assert report["computable"] is True, report
    assert report["observations_read"] == 0
    assert {s["execution_attempt"] for s in report["scenarios"].values()} == {
        ea.REPLACEMENT_ATTEMPT
    }
    assert all(s["decision"] for s in report["scenarios"].values())


def _pilot_record(attempt, task="PT01"):
    records = epa.synthetic_records()
    record = json.loads(json.dumps(records[0]))
    record["task_id"] = task
    if attempt is None:
        record.pop("execution_attempt")
    else:
        record["execution_attempt"] = attempt
    return record


def test_pooling_two_executions_is_refused():
    """The failure mode: two sibling artifact roots under one parent directory."""
    with pytest.raises(epa.AnalysisRefusal) as excinfo:
        epa.analyse(
            [_pilot_record(2), _pilot_record(None, task="PT04")],
            sources=["attempt-2/r/run_record.json", "obs/r/run_record.json"],
        )
    assert excinfo.value.code == epa.ANALYSIS_SPANS_EXECUTION_ATTEMPTS
    assert ea.ABORT_DECISION in excinfo.value.message


def test_an_aborted_attempt_record_is_refused_even_on_its_own():
    """The seven intact Attempt-1 rows are excluded too; that is the whole rule."""
    for attempt in (None, ea.ABORTED_ATTEMPT):
        with pytest.raises(epa.AnalysisRefusal) as excinfo:
            epa.analyse([_pilot_record(attempt)], sources=["obs/r/run_record.json"])
        assert excinfo.value.code == epa.ANALYSIS_INCLUDES_ABORTED_ATTEMPT


def test_the_replacement_executions_records_analyse_normally():
    report = epa.analyse(epa.synthetic_records())
    assert report["execution_attempt"] == ea.REPLACEMENT_ATTEMPT
    assert report["aborted_execution_attempt_excluded"] == ea.ABORTED_ATTEMPT


def test_a_dry_run_record_is_not_an_observation_and_does_not_trip_the_guard():
    dry = _pilot_record(None)
    dry["mode"] = "dry-run"
    assert epa.assert_single_execution_attempt([dry], ["x"]) is None


def test_a_restart_is_not_expressible_as_a_pilot_analysis_outcome():
    """PART A: the abort is not, and cannot be mistaken for, an analysis verdict."""
    inventory = _inventory()
    assert inventory["disposition"] == "ABORTED_INFRASTRUCTURE_ATTEMPT"
    for outcome in (epa.STRONG_GO, epa.QUALIFIED_GO, epa.RESET_SPECIFIC_GO,
                    epa.NO_SIGNAL, epa.INCONCLUSIVE):
        assert inventory["disposition"] != outcome


# --------------------------------------------------------------------------- #
# PART B / N.23. The aborted execution's evidence.
# --------------------------------------------------------------------------- #
INVENTORY_PATH = (
    REPO / "docs" / "v2" / "AFCI_EFFICIENCY_PILOT_ATTEMPT_1_EVIDENCE_INVENTORY.json"
)


def _inventory() -> dict:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def test_the_inventory_reports_the_aborted_execution_as_it_was():
    inv = _inventory()
    assert inv["scheduled_rows"] == 36
    assert inv["rows_attempted"] == 9
    assert inv["rows_not_started"] == 27
    assert inv["intact_governed_observations"] == 7
    assert inv["damaged_observations"] == 2
    assert inv["intact_sequences"] == [1, 2, 3, 4, 5, 7, 8]
    assert inv["damaged_sequences"] == [6, 9]
    assert inv["collision_pairs_in_schedule"] == 18
    assert len(inv["rows"]) == 9


def test_the_inventory_records_that_no_analysis_preceded_the_abort():
    inv = _inventory()
    assert inv["comparative_analysis_performed"] is False
    assert inv["token_ratio_analysis_performed"] is False
    assert inv["pilot_decision_emitted"] is False
    assert inv["continuation_threshold_evaluated"] is False
    assert inv["excluded_from_every_efficiency_analysis"] is True
    assert inv["poolable_with_replacement_execution"] is False
    assert inv["any_artifact_reconstructed"] is False
    assert inv["is_result"] is False and inv["scored"] is False


def test_the_two_damaged_rows_are_damaged_in_two_different_ways():
    rows = {r["sequence"]: r for r in _inventory()["rows"]}
    six, nine = rows[6], rows[9]
    assert six["status"] == ea.ROW_RECORD_OVERWRITTEN
    assert nine["status"] == ea.ROW_POST_DELIVERY_REFUSAL

    # Both really ran. Sequence 9 is a post-delivery damaged observation, not a
    # pre-observation invalid attempt, and the inventory says so from evidence.
    assert six["model_invoked"] is True and nine["model_invoked"] is True
    assert six["reset_state"] == rb.RESET and nine["reset_state"] == rb.NON_RESET
    assert six["artifact_dir"] == nine["artifact_dir"]
    assert six["collision_partner_attempted"] == [9]
    assert nine["collision_partner_attempted"] == [6]

    # The shared directory's undiscriminated artifacts belong to sequence 6.
    assert six["captured_worktree_attributable_to_this_row"] is True
    assert nine["captured_worktree_attributable_to_this_row"] is False
    assert six["functional_evaluation_attributable_to_this_row"] is True
    assert nine["functional_evaluation_attributable_to_this_row"] is False

    # Sequence 6's own governed record is gone and is NOT reconstructed.
    assert six["governed_record_intact_for_this_row"] is False
    assert nine["governed_record_attributed_to_arm"] == rb.NON_RESET


def test_every_intact_row_really_is_intact():
    for row in _inventory()["rows"]:
        if row["status"] != ea.ROW_INTACT:
            continue
        assert row["model_invoked"] is True
        assert row["governed_record_intact_for_this_row"] is True
        assert row["captured_worktree_present"] is True
        assert row["captured_worktree_attributable_to_this_row"] is True
        assert row["collision_partner_attempted"] == [], (
            "an intact row shares its directory with no OTHER attempted row; it "
            "is intact because its partner was scheduled later, not because it "
            "was protected"
        )


def test_the_inventory_derives_the_aborted_executions_real_directory_names():
    """The inventory describes what is on disk, not an idealised reconstruction."""
    inv = _inventory()
    assert inv["run_id_algorithm_version"] == art.IDENTITY_ALGORITHM_LEGACY
    for row in inv["rows"]:
        assert "-reset-" not in row["derived_run_id"]
        assert "-a1-" not in row["derived_run_id"] and "-a2-" not in row["derived_run_id"]
        assert row["derived_run_id"] in row["artifact_dir"]


def test_the_replacement_cannot_address_any_inventoried_attempt_1_directory(
    attempt_2,
):
    """N.9 / N.23, against the REAL Attempt-1 names rather than derived ones."""
    prior = {Path(r["artifact_dir"]).name for r in _inventory()["rows"]}
    assert prior, "the inventory named no directories"
    assert {Path(i.artifact_dir).name for i in attempt_2}.isdisjoint(prior)
    assert {i.run_id for i in attempt_2}.isdisjoint(
        {r["derived_run_id"] for r in _inventory()["rows"]}
    )


def test_the_preserved_evidence_is_exactly_as_inventoried():
    """N.23. Re-hashed against the live tree when it is present; skipped when not.

    The inventory is a claim about bytes on a particular machine, so it can only
    be verified where those bytes are. It is checked for internal consistency
    everywhere (the tests above), and re-hashed here.
    """
    inv = _inventory()
    roots = {Path(r["artifact_dir"]).parent for r in inv["rows"]}
    if not all(root.is_dir() for root in roots):
        pytest.skip("the Attempt-1 artifact tree is not present on this machine")
    rebuilt = ea.inventory_attempt_1(
        obs_root=sorted(roots)[0],
        log_root=sorted(roots)[0].parent / "logs",
        rows_attempted=inv["rows_attempted"],
    )
    assert rebuilt == inv, (
        "the preserved Attempt-1 evidence differs from the inventory taken when "
        "the attempt was aborted; nothing in this package may modify it"
    )
