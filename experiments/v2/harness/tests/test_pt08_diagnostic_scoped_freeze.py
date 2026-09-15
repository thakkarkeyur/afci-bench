"""Guards for `SL-PT08-06` — the diagnostic-scoped freeze exception.

WHAT THIS MODULE GUARDS
-----------------------
`SL-PT08-06` narrows the **applicability** of one suite-wide freeze
prerequisite for exactly one triple — task ``PT08``, condition ``C1``, run
purpose ``PT08_DIFFICULTY_DIAGNOSTIC`` — so that the diagnostic `SL-PT08-01`
authorised *before* ``TD-B34`` and *before* priority B is mechanically
executable at all.

AND IN THE OTHER DIRECTION — THE LOAD-BEARING HALF
--------------------------------------------------
Most of this module exists to stop the exception from growing. It proves the
runner refuses every neighbouring case: another condition, another task, another
run purpose, a different exact model, a different runtime version, a context
audit that is not ``CLEAN``, a ``Q1`` or ``Q8`` that is not ``PASS``, a resume, a
continuation, a reused session, an absent freeze record, and a record claiming a
different authority. Each of those is a separate test, because an exception
nobody can show the boundary of is not a narrow exception.

It also proves, in both directions, that the suite-wide facts stay where they
were: gate ``G1`` is **not passed**, the suite is **not frozen**, the global
manifest freeze is **not granted**, and the public lifecycle row is unchanged.
Several tests exist precisely to fail if the repository ever starts claiming
otherwise.

The scoped frozen manifest mount is checked the same way: it is derived from the
shipped package, it differs in exactly two lifecycle fields, it changes no task,
evaluator or opportunity semantics, and it refuses every location it may not
occupy.

Pure file and API inspection. No model is invoked, no benchmark runs, nothing is
frozen suite-wide and no power value is produced.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

import run_evaluation as ev
import run_governance as gov

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"

RECORD = DOCS_V2 / "PT08_DIAGNOSTIC_SCOPED_FREEZE_DECISION.md"
ACCEPTANCE_MATRIX = DOCS_V2 / "TASK_ACCEPTANCE_MATRIX.csv"

PURPOSE_NAME = "PT08_DIFFICULTY_DIAGNOSTIC"
AUTHORITY = "SL-PT08-06"
TASK = "PT08"
CONDITION = "C1"
EXACT_MODEL = "claude-sonnet-5"
CLI_VERSION = "2.1.229"
TASK_SHA = "a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2"


@pytest.fixture()
def purpose() -> gov.RunPurpose:
    return gov.resolve_run_purpose(PURPOSE_NAME)


@pytest.fixture()
def freeze(purpose) -> gov.DiagnosticFreeze:
    f = gov.diagnostic_freeze_for(purpose, TASK, CONDITION)
    assert f is not None, "the authorised triple must resolve a scoped freeze"
    return f


def _codes(problems) -> set:
    return {code for code, _ in problems}


def _mutate_record(tmp_path: Path, key: str, new_value: str) -> Path:
    """Rewrite one applicability row, leaving every other byte alone."""
    text = RECORD.read_text(encoding="utf-8")
    pattern = re.compile(rf"^\|\s*`{re.escape(key)}`\s*\|(.+?)\|\s*$", re.MULTILINE)
    assert pattern.search(text), f"{key} is not an applicability row"
    mutated = pattern.sub(f"| `{key}` | {new_value} |", text, count=1)
    assert mutated != text, f"mutating {key} changed nothing"
    tmp_path.mkdir(parents=True, exist_ok=True)
    out = tmp_path / "mutated_freeze_record.md"
    out.write_text(mutated, encoding="utf-8")
    return out


def _registry_with(tmp_path: Path, old: str, new: str) -> Path:
    text = gov.MODEL_REGISTRY.read_text(encoding="utf-8")
    assert old in text, f"{old!r} is not in the registry"
    out = tmp_path / "mutated_registry.yml"
    out.write_text(text.replace(old, new, 1), encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# 1-4. The exception exists, and exactly what it says it does
# --------------------------------------------------------------------------- #
def test_1_the_authorised_triple_may_use_the_diagnostic_scoped_freeze(purpose):
    assert gov.diagnostic_freeze_problems(purpose, TASK, CONDITION) == []
    state = gov.manifest_freeze_state(
        TASK, condition=CONDITION, run_purpose=PURPOSE_NAME
    )
    assert state["effective_for_this_purpose"] is True


def test_2_the_suite_wide_gate_g1_remains_false(purpose):
    """The exception narrows applicability. It never reports the gate as passed."""
    state = gov.manifest_freeze_state(
        TASK, condition=CONDITION, run_purpose=PURPOSE_NAME
    )
    assert state["global_gate_g1_passed"] is False
    report = ev.freeze_status_report(
        TASK, condition=CONDITION, run_purpose=PURPOSE_NAME
    )
    assert report["global_gate_g1_passed"] is False

    governed = gov.governed_diagnostic_freeze()
    assert governed["global_g1"] is False
    assert governed["global_g1_passed_by_this_record"] is False

    readiness = gov.check_readiness(TASK, CONDITION, PURPOSE_NAME)
    g1 = next(p for p in readiness.prerequisites if p.item == "suite_wide_gate_g1")
    assert g1.status == gov.NOT_APPLICABLE, "G1 is never PASS for this diagnostic"
    assert "NOT PASSED" in g1.detail


def test_3_the_global_and_suite_freezes_remain_false(purpose):
    """The suite-wide lifecycle is untouched, in the record and in the runner."""
    assert gov.manifest_is_frozen(TASK) is False
    state = gov.manifest_freeze_state(
        TASK, condition=CONDITION, run_purpose=PURPOSE_NAME
    )
    assert state["global_frozen"] is False
    assert state["suite_frozen"] is False
    assert state["changed_by_this_runner"] is False

    report = ev.freeze_status_report(
        TASK, condition=CONDITION, run_purpose=PURPOSE_NAME
    )
    assert report["manifest_frozen"] is False, (
        "manifest_frozen keeps its suite-wide meaning and must never be "
        "upgraded by the scoped state"
    )
    assert report["suite_frozen"] is False
    assert report["public_lifecycle_status"] == "validated"
    assert report["changed_by_this_runner"] is False

    governed = gov.governed_diagnostic_freeze()
    assert governed["suite_frozen"] is False
    assert governed["global_manifest_frozen"] is False
    assert governed["public_lifecycle_status_unchanged"] == "validated"


def test_4_the_diagnostic_scoped_freeze_is_true(freeze):
    assert freeze.authority == AUTHORITY
    assert freeze.covers(PURPOSE_NAME, TASK, CONDITION)
    assert freeze.task_sha256 == TASK_SHA
    assert freeze.exact_model_id == EXACT_MODEL
    assert freeze.cli_version == CLI_VERSION
    assert freeze.repetitions == 3
    # Even the object that carries the scoped freeze reports the suite-wide
    # facts, so a consumer reads them rather than inferring them.
    assert freeze.global_g1 is False
    assert freeze.suite_frozen is False
    assert freeze.global_manifest_frozen is False


# --------------------------------------------------------------------------- #
# 5-9. Everything outside the triple is refused
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("condition", ["C2", "C3", "C4"])
def test_5_6_7_other_conditions_are_rejected(purpose, condition):
    problems = gov.diagnostic_freeze_problems(purpose, TASK, condition)
    assert gov.DIAGNOSTIC_FREEZE_SCOPE_EXCEEDED in _codes(problems)
    assert gov.diagnostic_freeze_for(purpose, TASK, condition) is None
    state = gov.manifest_freeze_state(
        TASK, condition=condition, run_purpose=PURPOSE_NAME
    )
    assert state["diagnostic_frozen"] is False
    assert state["effective_for_this_purpose"] is False


@pytest.mark.parametrize("task", ["PT01", "PT04", "PT07", "PR01", "PR02"])
def test_8_other_tasks_are_rejected(purpose, task):
    problems = gov.diagnostic_freeze_problems(purpose, task, CONDITION)
    assert gov.DIAGNOSTIC_FREEZE_SCOPE_EXCEEDED in _codes(problems)
    assert gov.diagnostic_freeze_for(purpose, task, CONDITION) is None
    state = gov.manifest_freeze_state(
        task, condition=CONDITION, run_purpose=PURPOSE_NAME
    )
    assert state["effective_for_this_purpose"] is False


def test_9_another_run_purpose_is_rejected():
    """A purpose that names no authority can never acquire a scoped freeze."""
    with pytest.raises(gov.RunnerRefusal) as exc:
        gov.resolve_run_purpose("PT08_CONFIRMATORY")
    assert exc.value.code == gov.RUN_PURPOSE_UNRECOGNISED

    hypothetical = gov.RunPurpose(
        name="SOME_FUTURE_CONFIRMATORY_PURPOSE",
        decision_id="none",
        description="a purpose no Study-Lead decision grants an exception to",
        confirmatory=True,
        permitted_tasks=(TASK,),
        permitted_conditions=(CONDITION,),
        firewall=tuple((f, False) for f in gov.FIREWALL_FIELDS),
        repetitions=3,
    )
    assert hypothetical.diagnostic_freeze_authority is None
    problems = gov.diagnostic_freeze_problems(hypothetical, TASK, CONDITION)
    assert gov.DIAGNOSTIC_FREEZE_NOT_AUTHORISED in _codes(problems)
    assert gov.diagnostic_freeze_for(hypothetical, TASK, CONDITION) is None

    state = gov.manifest_freeze_state(
        TASK, condition=CONDITION, run_purpose="SOME_FUTURE_CONFIRMATORY_PURPOSE"
    )
    assert state["effective_for_this_purpose"] is False
    assert gov.RUN_PURPOSE_UNRECOGNISED in {
        p["code"] for p in state["diagnostic_freeze_problems"]
    }


def test_9b_no_purpose_inherits_this_exception_as_precedent():
    """`SL-PT08-06` §3: it creates NO precedent for a second exception.

    A second exception has since been adjudicated (`SL-V2-QUAL-01`, for
    `INSTRUMENT_QUALIFICATION_DIAGNOSTIC` over `PT09`/`PT10`), so the original
    form of this test — "exactly one purpose carries an authority" — would now
    fail for a reason that is not the risk it guards. The risk it guards is
    **inheritance**: a purpose acquiring a scoped freeze WITHOUT its own
    Study-Lead decision, or by reading `SL-PT08-06`'s record.

    That is what is asserted here instead, and it is strictly stronger than a
    count: every authority is DISTINCT, every authorised purpose names its own
    RECORD, and no purpose may reach `SL-PT08-06`'s tables but `PT08`'s own.
    """
    granted = {
        p.name: p for p in gov.RUN_PURPOSES.values() if p.diagnostic_freeze_authority
    }
    assert PURPOSE_NAME in granted

    authorities = [p.diagnostic_freeze_authority for p in granted.values()]
    assert len(set(authorities)) == len(authorities), (
        f"two purposes share one freeze authority: {authorities}; SL-PT08-06 is "
        "not precedent and an exception is never inherited"
    )
    records = [p.diagnostic_freeze_record for p in granted.values()]
    assert len(set(records)) == len(records), (
        f"two purposes read one freeze record: {records}"
    )

    pt08 = granted[PURPOSE_NAME]
    assert pt08.diagnostic_freeze_authority == AUTHORITY
    assert pt08.permitted_tasks == (TASK,)
    assert set(pt08.diagnostic_freeze_table_headings) == {TASK}

    # No other authorised purpose may resolve a freeze for PT08, and PT08's
    # purpose may resolve one for no other task.
    for name, purpose in granted.items():
        if name == PURPOSE_NAME:
            continue
        assert gov.diagnostic_freeze_for(purpose, TASK, CONDITION) is None
        for other_task in purpose.permitted_tasks:
            assert gov.diagnostic_freeze_for(pt08, other_task, CONDITION) is None


def test_9c_every_purpose_that_carries_an_authority_names_its_own_decision():
    """A purpose with no authority of its own can never acquire one by default.

    Every (task, CONDITION) the purpose permits must have its own applicability
    section. The condition is part of the lookup because a purpose authorising
    more than one condition — the efficiency pilot runs each task under `C1` and
    `C4` — must table them separately: the two differ in
    ``architecture_delivery``, which is the value a freeze table exists to pin,
    and reading one arm's table as the other's would certify a delivery that arm
    never received.
    """
    for purpose in gov.RUN_PURPOSES.values():
        if purpose.diagnostic_freeze_authority is None:
            assert purpose.diagnostic_freeze_record is None
            assert purpose.diagnostic_freeze_table_headings == {}
            continue
        record = purpose.freeze_record_path()
        assert record is not None and record.is_file(), (
            f"{purpose.name} names a freeze record that does not exist: {record}"
        )
        seen = set()
        for task_id in purpose.permitted_tasks:
            for condition in purpose.permitted_conditions:
                heading = purpose.freeze_table_heading(task_id, condition)
                assert heading, (
                    f"{purpose.name}/{task_id}/{condition} has no applicability "
                    "section"
                )
                table = gov.governed_diagnostic_freeze(record, heading)
                assert table.get("diagnostic_freeze_authority") == (
                    purpose.diagnostic_freeze_authority
                )
                assert table.get("diagnostic_freeze_task") == task_id
                assert table.get("diagnostic_freeze_condition") == condition
                # A shared section would make two arms indistinguishable.
                assert heading not in seen, (
                    f"{purpose.name} reuses section {heading!r} for more than one "
                    "(task, condition)"
                )
                seen.add(heading)


# --------------------------------------------------------------------------- #
# 10-17. The per-repetition conditions the exception does NOT waive
# --------------------------------------------------------------------------- #
def test_10_an_exact_model_mismatch_is_rejected(freeze):
    for wrong in ("sonnet", "claude-opus-4-8", "claude-haiku-4-5-20251001", ""):
        problems = gov.diagnostic_freeze_execution_problems(freeze, model_id=wrong)
        assert gov.DIAGNOSTIC_MODEL_ID_MISMATCH in _codes(problems), wrong
    assert (
        gov.diagnostic_freeze_execution_problems(freeze, model_id=EXACT_MODEL) == []
    )


def test_10b_the_alias_is_never_accepted_in_place_of_the_exact_id(freeze):
    """`sonnet` is what Q1 asked for. It is never what a repetition requests."""
    problems = gov.diagnostic_freeze_execution_problems(freeze, model_id="sonnet")
    assert gov.DIAGNOSTIC_MODEL_ID_MISMATCH in _codes(problems)
    assert gov.governed_diagnostic_freeze()[
        "diagnostic_freeze_model_selector_is_alias"
    ] is False


def test_11_a_runtime_version_mismatch_is_rejected(freeze):
    for wrong in ("2.1.209", "2.1.230", "3.0.0"):
        problems = gov.diagnostic_freeze_execution_problems(freeze, cli_version=wrong)
        assert gov.DIAGNOSTIC_RUNTIME_VERSION_MISMATCH in _codes(problems), wrong
    assert (
        gov.diagnostic_freeze_execution_problems(freeze, cli_version=CLI_VERSION) == []
    )


def test_12_a_missing_or_unclean_context_is_rejected(freeze):
    contaminated = gov.diagnostic_freeze_execution_problems(
        freeze, context_verdict="CONTAMINATED"
    )
    assert gov.CONTEXT_AUDIT_CONTAMINATED in _codes(contaminated)

    unknown = gov.diagnostic_freeze_execution_problems(
        freeze, context_verdict="UNKNOWN"
    )
    assert gov.CONTEXT_AUDIT_UNKNOWN in _codes(unknown)

    # Absent is not the same as clean: when the caller says the verdict is
    # required, silence is a refusal.
    missing = gov.diagnostic_freeze_execution_problems(
        freeze, context_verdict=None, require_all=True
    )
    assert gov.CONTEXT_AUDIT_UNKNOWN in _codes(missing)

    assert gov.diagnostic_freeze_execution_problems(
        freeze, context_verdict="CLEAN"
    ) == []


@pytest.mark.parametrize(
    "field,expected_code",
    [
        ("q1_readback", gov.Q1_READBACK_NOT_VALIDATED_LIVE),
        ("q8_invalid_model_id_rejection", gov.Q8_INVALID_MODEL_ID_NOT_VALIDATED_LIVE),
    ],
)
def test_13_14_q1_or_q8_not_pass_is_rejected(purpose, tmp_path, field, expected_code):
    registry = _registry_with(
        tmp_path, f'{field}: "PASS"', f'{field}: "NOT_VALIDATED"'
    )
    problems = gov.diagnostic_freeze_problems(
        purpose, TASK, CONDITION, registry=registry
    )
    assert expected_code in _codes(problems)
    assert gov.diagnostic_freeze_for(
        purpose, TASK, CONDITION, registry=registry
    ) is None


@pytest.mark.parametrize(
    "flag,expected_code",
    [
        ("--resume", gov.SESSION_RESUME_REJECTED),
        ("-r", gov.SESSION_RESUME_REJECTED),
        ("--continue", gov.SESSION_CONTINUE_REJECTED),
        ("-c", gov.SESSION_CONTINUE_REJECTED),
    ],
)
def test_15_16_resume_and_continue_are_rejected(freeze, flag, expected_code):
    problems = gov.diagnostic_freeze_execution_problems(
        freeze, launch_argv=["claude", flag, "abc", "-p"]
    )
    assert expected_code in _codes(problems)


def test_17_session_reuse_is_rejected(freeze):
    problems = gov.diagnostic_freeze_execution_problems(
        freeze, session_id="s-1", previous_session_ids=["s-0", "s-1"]
    )
    assert gov.SESSION_ID_REUSED in _codes(problems)
    assert gov.diagnostic_freeze_execution_problems(
        freeze, session_id="s-2", previous_session_ids=["s-0", "s-1"]
    ) == []


# --------------------------------------------------------------------------- #
# 18-19. An absent or wrongly-attributed freeze
# --------------------------------------------------------------------------- #
def test_18_a_missing_diagnostic_freeze_record_is_rejected(purpose, tmp_path):
    absent = tmp_path / "no-such-record.md"
    with pytest.raises(gov.RunnerRefusal) as exc:
        gov.governed_diagnostic_freeze(absent)
    assert exc.value.code == gov.GOVERNANCE_RECORD_UNREADABLE

    empty = tmp_path / "empty.md"
    empty.write_text("# a record with no applicability table\n", encoding="utf-8")
    problems = gov.diagnostic_freeze_problems(
        purpose, TASK, CONDITION, record=empty
    )
    assert gov.DIAGNOSTIC_FREEZE_MISSING in _codes(problems)
    assert gov.diagnostic_freeze_for(purpose, TASK, CONDITION, record=empty) is None


def test_19_a_wrong_freeze_authority_is_rejected(purpose, tmp_path):
    for key in ("decision_id", "diagnostic_freeze_authority"):
        record = _mutate_record(tmp_path / key, key, "`SL-PT08-99`")
        problems = gov.diagnostic_freeze_problems(
            purpose, TASK, CONDITION, record=record
        )
        assert gov.DIAGNOSTIC_FREEZE_AUTHORITY_MISMATCH in _codes(problems), key
        assert gov.diagnostic_freeze_for(
            purpose, TASK, CONDITION, record=record
        ) is None


# --------------------------------------------------------------------------- #
# 20. The gate may never be silently flipped
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "key,claim",
    [
        ("global_g1", "`true`"),
        ("global_g1_passed_by_this_record", "`true`"),
        ("suite_frozen", "`true`"),
        ("global_manifest_frozen", "`true`"),
        ("global_td_b32_status", "`closed`"),
        ("td_b12_g6_status", "`closed`"),
        ("td_b34_status", "`closed`"),
        ("priority_b_state", "`complete`"),
        ("td_b03_status", "`closed`"),
    ],
)
def test_20_a_record_claiming_a_suite_wide_pass_is_refused(
    purpose, tmp_path, key, claim
):
    """A scoped freeze that reported a gate as granted would not be scoped."""
    record = _mutate_record(tmp_path / key, key, claim)
    problems = gov.diagnostic_freeze_problems(
        purpose, TASK, CONDITION, record=record
    )
    assert gov.SUITE_WIDE_G1_MUST_NOT_BE_CLAIMED in _codes(problems), key
    assert gov.diagnostic_freeze_for(purpose, TASK, CONDITION, record=record) is None


def test_20b_the_public_lifecycle_row_is_not_edited():
    """The freeze is scoped precisely because the public row does NOT move."""
    row = gov.acceptance_matrix_row(TASK)
    assert row["status"].strip() == "validated"
    assert gov.manifest_is_frozen(TASK) is False
    assert gov.hidden_acceptance_is_validated(TASK) is True


def test_20c_no_other_task_row_became_frozen():
    text = ACCEPTANCE_MATRIX.read_text(encoding="utf-8")
    for row in gov._rows(ACCEPTANCE_MATRIX):
        assert row.get("status", "").strip().lower() != "frozen", row.get("task_id")
    assert "frozen" not in {
        r.get("status", "").strip().lower() for r in gov._rows(ACCEPTANCE_MATRIX)
    }
    assert text  # the file was actually read


# --------------------------------------------------------------------------- #
# Mutation pressure on every remaining pinned row
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "key,mutation,expected_code",
    [
        ("run_purpose", "`SOMETHING_ELSE`", gov.DIAGNOSTIC_FREEZE_SCOPE_EXCEEDED),
        ("diagnostic_freeze_task", "`PT04`", gov.DIAGNOSTIC_FREEZE_SCOPE_EXCEEDED),
        ("diagnostic_freeze_condition", "`C4`", gov.DIAGNOSTIC_FREEZE_SCOPE_EXCEEDED),
        ("diagnostic_freeze_frozen", "`false`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_resume_permitted", "`true`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_continuation_permitted", "`true`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_session_reuse_permitted", "`true`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_api_key_used", "`true`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_fallback_model_permitted", "`true`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_model_selector_is_alias", "`true`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_sterile_context_required", "`false`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_context_audit_required_every_repetition", "`false`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_is_result", "`true`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_scored", "`true`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_process_per_repetition", "`reused`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_session_per_repetition", "`reused`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_architecture_delivery", "`prompt`", gov.DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT),
        ("diagnostic_freeze_task_sha256", "`" + "0" * 64 + "`", gov.TASK_SHA_MISMATCH),
        ("diagnostic_freeze_exact_model_id", "`claude-opus-4-8`", gov.DIAGNOSTIC_MODEL_ID_MISMATCH),
        ("diagnostic_freeze_cli_version", "`2.1.209`", gov.DIAGNOSTIC_RUNTIME_VERSION_MISMATCH),
        ("diagnostic_freeze_repetitions", "`5`", gov.DIAGNOSTIC_REPETITION_DECISION_INCONSISTENT),
    ],
)
def test_every_pinned_row_is_load_bearing(
    purpose, tmp_path, key, mutation, expected_code
):
    """A record row nobody checks is decoration. Each one is mutated and caught."""
    record = _mutate_record(tmp_path / key, key, mutation)
    problems = gov.diagnostic_freeze_problems(
        purpose, TASK, CONDITION, record=record
    )
    assert expected_code in _codes(problems), (key, problems)
    assert gov.diagnostic_freeze_for(purpose, TASK, CONDITION, record=record) is None


def test_the_runner_does_not_take_the_record_at_its_word(purpose, tmp_path):
    """The hash, the model, the runtime and the count are re-derived, not read.

    A record could otherwise widen its own exception by editing a value the rest
    of the repository disagrees with.
    """
    record = _mutate_record(
        tmp_path, "diagnostic_freeze_task_sha256", "`" + "f" * 64 + "`"
    )
    problems = gov.diagnostic_freeze_problems(
        purpose, TASK, CONDITION, record=record
    )
    assert gov.TASK_SHA_MISMATCH in _codes(problems)
    assert gov.expected_task_sha256(TASK) == TASK_SHA


# --------------------------------------------------------------------------- #
# The evaluation boundary honours the same scope
# --------------------------------------------------------------------------- #
def test_scoring_prerequisites_pass_only_for_the_authorised_triple():
    ev.assert_scoring_prerequisites(
        TASK,
        condition=CONDITION,
        run_purpose=PURPOSE_NAME,
        model_id=EXACT_MODEL,
        cli_version=CLI_VERSION,
        context_verdict="CLEAN",
        require_execution_evidence=True,
    )


def test_scoring_prerequisites_still_refuse_without_the_scope():
    """The pre-existing call shape keeps the pre-existing, fail-closed answer."""
    with pytest.raises(gov.RunnerRefusal) as exc:
        ev.assert_scoring_prerequisites(TASK)
    assert exc.value.code == gov.MANIFEST_NOT_FROZEN


@pytest.mark.parametrize("condition", ["C2", "C3", "C4"])
def test_scoring_prerequisites_refuse_other_conditions(condition):
    with pytest.raises(gov.RunnerRefusal) as exc:
        ev.assert_scoring_prerequisites(
            TASK,
            condition=condition,
            run_purpose=PURPOSE_NAME,
            model_id=EXACT_MODEL,
            cli_version=CLI_VERSION,
            context_verdict="CLEAN",
        )
    assert exc.value.code == gov.MANIFEST_NOT_FROZEN


@pytest.mark.parametrize(
    "kwargs,expected_code",
    [
        ({"model_id": "sonnet"}, gov.DIAGNOSTIC_MODEL_ID_MISMATCH),
        ({"cli_version": "2.1.209"}, gov.DIAGNOSTIC_RUNTIME_VERSION_MISMATCH),
        ({"context_verdict": "CONTAMINATED"}, gov.CONTEXT_AUDIT_CONTAMINATED),
        ({"launch_argv": ["claude", "--resume", "x"]}, gov.SESSION_RESUME_REJECTED),
        ({"launch_argv": ["claude", "--continue"]}, gov.SESSION_CONTINUE_REJECTED),
        (
            {"session_id": "s", "previous_session_ids": ["s"]},
            gov.SESSION_ID_REUSED,
        ),
    ],
)
def test_scoring_prerequisites_refuse_each_unwaived_condition(kwargs, expected_code):
    base = dict(
        condition=CONDITION,
        run_purpose=PURPOSE_NAME,
        model_id=EXACT_MODEL,
        cli_version=CLI_VERSION,
        context_verdict="CLEAN",
    )
    base.update(kwargs)
    with pytest.raises(gov.RunnerRefusal) as exc:
        ev.assert_scoring_prerequisites(TASK, **base)
    assert exc.value.code == expected_code


def test_the_architecture_channel_unblocks_only_for_the_authorised_triple(tmp_path):
    blocked = ev.architecture_scoring_channel(TASK)
    assert blocked.status == "BLOCKED" and blocked.code == gov.MANIFEST_NOT_FROZEN

    snapshot = tmp_path / "snapshot"
    mount = tmp_path / "mount"
    snapshot.mkdir()
    mount.mkdir()
    scoped = ev.architecture_scoring_channel(
        TASK,
        snapshot=snapshot,
        manifest_mount=mount,
        coding_worktree=snapshot,
        condition=CONDITION,
        run_purpose=PURPOSE_NAME,
    )
    assert scoped.status == "READY", scoped.detail
    assert scoped.command and "--manifest" in scoped.command


# --------------------------------------------------------------------------- #
# The diagnostic-scoped frozen manifest mount
# --------------------------------------------------------------------------- #
@pytest.fixture()
def private_root() -> Path:
    root = gov.default_private_root()
    if not (root / "tasks" / TASK / "evaluator_manifest.json").is_file():
        pytest.skip("the private evaluator repository is not present")
    return root


def test_the_shipped_manifest_stays_review_and_is_never_written(private_root):
    shipped = json.loads(
        ev.shipped_manifest_path(TASK, private_root).read_text(encoding="utf-8")
    )
    assert shipped["status"] == "review", (
        "the shipped manifest is read-only here; the scoped freeze derives a "
        "mount rather than freezing the package"
    )
    assert shipped["invalidation"]["invalidated"] is False


def test_the_derived_mount_differs_in_exactly_two_lifecycle_fields(private_root):
    shipped = json.loads(
        ev.shipped_manifest_path(TASK, private_root).read_text(encoding="utf-8")
    )
    derived, provenance = ev.derive_diagnostic_frozen_manifest(
        TASK, authority=AUTHORITY, private_root=private_root
    )
    assert derived["status"] == "frozen"
    assert derived["manifest_version"].endswith(ev.DIAGNOSTIC_FROZEN_VERSION_SUFFIX)

    differing = sorted(
        k for k in set(shipped) | set(derived) if shipped.get(k) != derived.get(k)
    )
    assert differing == sorted(ev.DIAGNOSTIC_FROZEN_MANIFEST_LIFECYCLE_FIELDS)
    assert provenance["fields_changed"] == differing
    assert provenance["semantic_fields_changed"] == []
    assert provenance["shipped_manifest_modified"] is False
    assert provenance["suite_frozen"] is False
    assert provenance["global_gate_g1_passed"] is False


def test_the_derived_mount_changes_no_semantics(private_root):
    shipped = json.loads(
        ev.shipped_manifest_path(TASK, private_root).read_text(encoding="utf-8")
    )
    derived, _ = ev.derive_diagnostic_frozen_manifest(
        TASK, authority=AUTHORITY, private_root=private_root
    )
    for field in (
        "task_id",
        "manifest_id",
        "base_sha",
        "opportunities",
        "dependency_policy",
        "applicable_rule_ids",
        "e1_analysis_eligibility",
        "evaluator_hashes",
        "areas",
        "legitimate_alternatives",
        "invalidation",
    ):
        assert derived[field] == shipped[field], field
    assert derived["task_id"] == TASK, (
        "the mount keeps the real task binding, so the approved-index gate still "
        "applies to it"
    )


def test_the_mount_refuses_every_location_it_may_not_occupy(private_root, tmp_path):
    with pytest.raises(gov.RunnerRefusal) as exc:
        ev.write_diagnostic_frozen_manifest_mount(
            TASK,
            REPO / "experiments" / "v2" / "scoped-mount",
            condition=CONDITION,
            run_purpose=PURPOSE_NAME,
            private_root=private_root,
        )
    assert exc.value.code == ev.DIAGNOSTIC_FROZEN_MANIFEST_MOUNT_REFUSED

    with pytest.raises(gov.RunnerRefusal) as exc:
        ev.write_diagnostic_frozen_manifest_mount(
            TASK,
            private_root / "scoped-mount",
            condition=CONDITION,
            run_purpose=PURPOSE_NAME,
            private_root=private_root,
        )
    assert exc.value.code == ev.DIAGNOSTIC_FROZEN_MANIFEST_MOUNT_REFUSED

    worktree = tmp_path / "worktree"
    worktree.mkdir()
    with pytest.raises(gov.RunnerRefusal) as exc:
        ev.write_diagnostic_frozen_manifest_mount(
            TASK,
            worktree / "evaluator",
            condition=CONDITION,
            run_purpose=PURPOSE_NAME,
            coding_worktree=worktree,
            private_root=private_root,
        )
    assert exc.value.code == ev.DIAGNOSTIC_FROZEN_MANIFEST_MOUNT_REFUSED


@pytest.mark.parametrize(
    "condition,run_purpose",
    [("C4", PURPOSE_NAME), (CONDITION, "SOME_OTHER_PURPOSE")],
)
def test_the_mount_refuses_an_unauthorised_triple(
    private_root, tmp_path, condition, run_purpose
):
    with pytest.raises(gov.RunnerRefusal) as exc:
        ev.write_diagnostic_frozen_manifest_mount(
            TASK,
            tmp_path / "mount",
            condition=condition,
            run_purpose=run_purpose,
            private_root=private_root,
        )
    assert exc.value.code == gov.DIAGNOSTIC_FREEZE_NOT_AUTHORISED
    assert not (tmp_path / "mount").exists(), "a refused mount writes nothing"


def test_the_mount_is_written_outside_both_repositories(private_root, tmp_path):
    mount_dir = tmp_path / "evaluator-mount"
    target, provenance = ev.write_diagnostic_frozen_manifest_mount(
        TASK,
        mount_dir,
        condition=CONDITION,
        run_purpose=PURPOSE_NAME,
        coding_worktree=tmp_path / "worktree",
        private_root=private_root,
    )
    assert target.is_file()
    assert REPO.resolve() not in target.resolve().parents
    assert private_root.resolve() not in target.resolve().parents
    assert provenance["authority"] == AUTHORITY
    assert provenance["committed_anywhere"] is False
    assert json.loads(target.read_text(encoding="utf-8"))["status"] == "frozen"


# --------------------------------------------------------------------------- #
# The decision is PRE-DATA, and stays checkable as such
# --------------------------------------------------------------------------- #
def test_no_diagnostic_observation_existed_when_the_decision_was_recorded():
    """`SL-PT08-06` §1.1's zero-data claim, asserted rather than believed.

    The confirmatory artifact areas carry a README and nothing else, so the
    decision cannot have been taken on an outcome: there was none to take it on.
    """
    for area in gov.CONFIRMATORY_ARTIFACT_DIRS:
        entries = sorted(p.name for p in area.iterdir()) if area.is_dir() else []
        assert entries in ([], ["README.md"]), (area, entries)


def test_the_record_states_the_bound_it_does_not_cross():
    text = RECORD.read_text(encoding="utf-8")
    for phrase in (
        "pass the suite-wide gate **`G1`**",
        "close **`TD-B34`**",
        "start or complete **priority B**",
        "close the **global `TD-B32`** row",
        "authorise **confirmatory execution**",
        "authorise **treatment-effect analysis**",
        "waive **`Q1`** or **`Q8`**",
        "waive **exact model pinning**",
    ):
        assert phrase in text, phrase
    assert "**Gate `G1` is NOT passed**" in text
    assert "PRE-FREEZE" in text


def test_the_record_names_the_circularity_it_resolves():
    text = RECORD.read_text(encoding="utf-8")
    assert "mechanically non-executable" in text
    assert "Zero `PT08` diagnostic observations exist at decision time" in text
    assert "cannot be outcome-driven" in text
