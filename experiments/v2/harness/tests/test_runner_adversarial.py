"""Twenty-two adversarial cases. Every one must fail closed.

These are the ways a run could be made to look legitimate while being something
else: an unmarked purpose, a widened condition, a smuggled architecture payload,
a drifted hash, a reused session, an unselected model, an unvalidated oracle, a
promoted diagnostic artifact, or execution against the source repository itself.

Where a case can be driven through the whole runner it is, because a guard that
only fires in a unit test is not a guard. Faults that must appear *inside* the
pipeline are injected by monkeypatching the authority the runner reads, so the
code under test is the shipped orchestration and not a re-enactment of it.

No model is invoked.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import context_audit as ca
import model_adapter as ma
import prepare_model_worktree as pmw
import run_artifacts as art
import run_evaluation as ev
import run_governance as gov
import run_v2
import run_worktree as wt
import runner_fixtures as fx

REPO = Path(__file__).resolve().parents[4]
PT08 = REPO / "experiments" / "v2" / "tasks" / "public" / "PT08.md"
PT08_SHA = "a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2"
PURPOSE = "PT08_DIFFICULTY_DIAGNOSTIC"


def _run(tmp_path, **kwargs) -> run_v2.RunResult:
    base = dict(
        task_id="PT08",
        condition="C1",
        run_purpose=PURPOSE,
        artifact_root=tmp_path / "runs",
        generated_at="adversarial",
        audit_provider=fx.synthetic_clean_audit,
    )
    base.update(kwargs)
    return run_v2.run(run_v2.RunRequest(**base))


def _prepared(tmp_path, name="worktree"):
    return pmw.prepare_model_worktree(
        pmw.PreparationRequest(
            condition="C1", source_root=REPO, dest_root=tmp_path / name,
            task_path=PT08, task_id="PT08",
        )
    )


def _enforce(prepared, **overrides):
    kwargs = dict(
        root=prepared.snapshot_root, manifest=prepared.manifest, condition="C1",
        expected_task_sha=PT08_SHA, repo=REPO,
    )
    kwargs.update(overrides)
    return wt.enforce_prepared_worktree(**kwargs)


# --------------------------------------------------------------------------- #
# 1-2. The run purpose
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("missing", [None, "", "   "])
def test_case_01_a_missing_run_purpose_fails_closed(tmp_path, missing):
    result = _run(tmp_path, run_purpose=missing)
    assert result.refusal_code == gov.RUN_PURPOSE_MISSING
    assert result.record is None, "no artifact may be produced for an unmarked run"


@pytest.mark.parametrize(
    "wrong",
    ["CONFIRMATORY", "STAGE_1_PILOT", "pt08_difficulty_diagnostic ", "E1_CORE_GRID"],
)
def test_case_02_a_wrong_run_purpose_fails_closed(tmp_path, wrong):
    result = _run(tmp_path, run_purpose=wrong)
    assert result.refusal_code == gov.RUN_PURPOSE_UNRECOGNISED


def test_case_02b_no_confirmatory_purpose_is_registered_at_all():
    """Nothing confirmatory is authorised, so nothing confirmatory is expressible."""
    assert list(gov.RUN_PURPOSES) == [PURPOSE]
    assert all(not p.confirmatory for p in gov.RUN_PURPOSES.values())


# --------------------------------------------------------------------------- #
# 3-4. Condition and task
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("condition", ["C2", "C3", "C4"])
def test_case_03_a_non_c1_condition_fails_closed(tmp_path, condition):
    result = _run(tmp_path, condition=condition)
    assert result.refusal_code == gov.CONDITION_NOT_PERMITTED_FOR_PURPOSE


@pytest.mark.parametrize("task", ["PT01", "PT04", "PT07", "PR01", "CAND-A1"])
def test_case_04_another_task_fails_closed(tmp_path, task):
    result = _run(tmp_path, task_id=task)
    assert result.refusal_code == gov.TASK_NOT_PERMITTED_FOR_PURPOSE


# --------------------------------------------------------------------------- #
# 5. Architecture context injected into C1
# --------------------------------------------------------------------------- #
def test_case_05_an_architecture_payload_cannot_be_requested_for_c1(tmp_path):
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.prepare_model_worktree(
            pmw.PreparationRequest(
                condition="C1", source_root=REPO, dest_root=tmp_path / "wt",
                task_path=PT08, task_id="PT08",
                architecture_text="never allowed in the baseline arm",
            )
        )
    assert exc.value.code == "ARCH_PAYLOAD_NOT_ALLOWED"


def test_case_05b_an_architecture_file_smuggled_into_c1_is_refused(tmp_path):
    prepared = _prepared(tmp_path)
    (prepared.snapshot_root / "libs" / "core" / "ARCHITECTURE_CONTEXT.md").write_text(
        (REPO / "docs" / "v2" / "ARCHITECTURE_CONTEXT.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared)
    assert exc.value.code in {
        gov.UNEXPECTED_MODEL_VISIBLE_FILE, gov.ARCHITECTURE_DELIVERY_VIOLATION
    }


def test_case_05c_a_persistent_instruction_file_smuggled_into_c1_is_refused(tmp_path):
    prepared = _prepared(tmp_path)
    (prepared.snapshot_root / "CLAUDE.md").write_text(
        "Never import api from features.\n", encoding="utf-8"
    )
    manifest = copy.deepcopy(prepared.manifest)
    entries = wt._on_disk_entries(prepared.snapshot_root)
    manifest["entries"] = entries
    manifest["entry_count"] = len(entries)
    manifest["content_hash"] = wt._content_hash_of_entries(entries)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared, manifest=manifest)
    assert exc.value.code in {
        gov.WORKTREE_PATH_NOT_ALLOWLISTED, gov.ARCHITECTURE_DELIVERY_VIOLATION
    }


# --------------------------------------------------------------------------- #
# 6-7. Identity drift
# --------------------------------------------------------------------------- #
def test_case_06_a_task_hash_mismatch_fails_closed_in_the_pipeline(tmp_path, monkeypatch):
    monkeypatch.setattr(gov, "expected_task_sha256", lambda *a, **k: "0" * 64)
    result = _run(tmp_path)
    assert result.refusal_code == gov.TASK_SHA_MISMATCH
    assert "PREPARE_WORKTREE" not in {e["state"] for e in result.machine.log}


def test_case_06b_a_task_hash_mismatch_fails_closed_at_the_worktree_gate(tmp_path):
    prepared = _prepared(tmp_path)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared, expected_task_sha="f" * 64)
    assert exc.value.code == gov.TASK_SHA_MISMATCH


def test_case_07_a_substrate_hash_mismatch_fails_closed_in_the_pipeline(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(gov, "SUBSTRATE_CONTENT_HASH", "0" * 64)
    result = _run(tmp_path)
    assert result.refusal_code == gov.SUBSTRATE_IDENTITY_MISMATCH


# --------------------------------------------------------------------------- #
# 8-9. Worktree integrity
# --------------------------------------------------------------------------- #
def test_case_08_an_extra_model_visible_file_fails_closed(tmp_path):
    prepared = _prepared(tmp_path)
    (prepared.snapshot_root / "apps" / "EXTRA.ts").write_text("//\n", encoding="utf-8")
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared)
    assert exc.value.code == gov.UNEXPECTED_MODEL_VISIBLE_FILE


def test_case_08b_an_extra_file_injected_between_preparation_and_launch_fails_closed(
    tmp_path, monkeypatch
):
    """Injected inside the pipeline, after the preparer has already succeeded."""
    real = pmw.prepare_model_worktree

    def sabotaged(request):
        result = real(request)
        (Path(result.snapshot_root) / "libs" / "INJECTED.ts").write_text(
            "export const x = 1;\n", encoding="utf-8", newline="\n"
        )
        return result

    monkeypatch.setattr(run_v2.pmw, "prepare_model_worktree", sabotaged)
    result = _run(tmp_path)
    assert result.refusal_code == gov.UNEXPECTED_MODEL_VISIBLE_FILE
    assert "CONTEXT_AUDIT" not in {e["state"] for e in result.machine.log}


def test_case_09_a_dirty_prepared_worktree_fails_closed(tmp_path, monkeypatch):
    real = pmw.prepare_model_worktree

    def sabotaged(request):
        result = real(request)
        target = Path(result.snapshot_root) / "package.json"
        target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        return result

    monkeypatch.setattr(run_v2.pmw, "prepare_model_worktree", sabotaged)
    result = _run(tmp_path)
    assert result.refusal_code == gov.PREPARED_WORKTREE_DIRTY


# --------------------------------------------------------------------------- #
# 10-11. Context audit
# --------------------------------------------------------------------------- #
def test_case_10_a_contaminated_audit_fails_closed(tmp_path):
    result = _run(tmp_path, audit_provider=fx.synthetic_contaminated_audit)
    assert result.refusal_code == gov.CONTEXT_AUDIT_CONTAMINATED
    assert result.record["invocation"]["invoked"] is False


def test_case_11_a_missing_or_broken_audit_fails_closed(tmp_path):
    assert _run(tmp_path, audit_provider=fx.missing_audit).refusal_code == (
        gov.CONTEXT_AUDIT_MISSING
    )
    assert _run(tmp_path, audit_provider=fx.exploding_audit).refusal_code == (
        gov.CONTEXT_AUDIT_ERROR
    )
    assert _run(
        tmp_path, audit_provider=fx.synthetic_unknown_verdict_audit
    ).refusal_code == gov.CONTEXT_AUDIT_UNKNOWN


# --------------------------------------------------------------------------- #
# 12-14. Session freshness
# --------------------------------------------------------------------------- #
def test_case_12_a_resume_flag_fails_closed(tmp_path):
    result = _run(tmp_path, extra_launch_args=("--resume", "abc"))
    assert result.refusal_code == gov.SESSION_RESUME_REJECTED


def test_case_13_a_continue_flag_fails_closed(tmp_path):
    result = _run(tmp_path, extra_launch_args=("--continue",))
    assert result.refusal_code == gov.SESSION_CONTINUE_REJECTED
    assert _run(tmp_path, extra_launch_args=("-c",)).refusal_code == (
        gov.SESSION_CONTINUE_REJECTED
    )


def test_case_14_a_reused_session_id_fails_closed(tmp_path):
    result = _run(tmp_path, session_id="s-1", previous_session_ids=("s-1",))
    assert result.refusal_code == gov.SESSION_ID_REUSED


def test_case_14b_the_frozen_guard_is_a_second_independent_gate():
    """Both gates hold: the runner's own, and context_audit's frozen guard."""
    assert ca.check_session_flags(["claude", "--resume", "x"])
    assert ca.check_session_flags(["claude", "--session-id", "s"], ["s"])


# --------------------------------------------------------------------------- #
# 15. Model selection
# --------------------------------------------------------------------------- #
def test_case_15_a_real_invocation_with_no_selected_primary_model_fails_closed(tmp_path):
    result = _run(tmp_path, mode="real", model_id="claude-sonnet-5")
    # It fails even earlier than the model gate: a real run needs a validated
    # oracle first. Both refusals are correct; neither is a model being chosen.
    assert result.refusal_code in {
        "PT08_HIDDEN_ACCEPTANCE_NOT_VALIDATED",
        gov.PRIMARY_MODEL_NOT_SELECTED,
        gov.ISOLATED_ENVIRONMENT_NOT_VERIFIED,
    }
    adapter = ma.ModelInvocationAdapter(mode="real", registry_primary_model=None)
    with pytest.raises(gov.RunnerRefusal) as exc:
        adapter.assert_real_invocation_permitted("claude-sonnet-5")
    assert exc.value.code == gov.PRIMARY_MODEL_NOT_SELECTED


def test_case_15b_the_dry_run_never_substitutes_a_model(tmp_path):
    record = _run(tmp_path).record
    assert record["model"]["requested_model_id"] is None
    assert record["model"]["selection_status"] == gov.MODEL_SELECTION_REQUIRED
    assert "--model" not in record["fresh_launch"]["argv"]


# --------------------------------------------------------------------------- #
# 16-17. Model readback
# --------------------------------------------------------------------------- #
def test_case_16_a_model_readback_mismatch_fails_closed():
    with pytest.raises(gov.RunnerRefusal) as exc:
        ma.validate_model_identity(
            "claude-sonnet-5", fx.runtime_evidence("claude-haiku-4-5-20251001")
        )
    assert exc.value.code == gov.MODEL_READBACK_MISMATCH


def test_case_17_a_missing_model_readback_fails_closed():
    for empty in ([], [{"type": "assistant"}], {}, None):
        with pytest.raises(gov.RunnerRefusal) as exc:
            ma.validate_model_identity("claude-sonnet-5", empty)
        assert exc.value.code == gov.MODEL_READBACK_MISSING


def test_case_17b_a_dry_run_never_fabricates_a_readback(tmp_path):
    record = _run(tmp_path).record
    assert record["model_identity"]["status"] == "NOT_PERFORMED_DRY_RUN"
    assert record["model_identity"]["resolved_model_id"] is None


# --------------------------------------------------------------------------- #
# 18-19. Oracle lifecycle
# --------------------------------------------------------------------------- #
def test_case_18_an_unvalidated_hidden_acceptance_fails_closed():
    with pytest.raises(gov.RunnerRefusal) as exc:
        ev.assert_scoring_prerequisites("PT08")
    assert exc.value.code == "PT08_HIDDEN_ACCEPTANCE_NOT_VALIDATED"


def test_case_18b_a_scored_run_is_refused_before_any_worktree_is_prepared(tmp_path):
    result = _run(tmp_path, scored=True)
    assert result.refusal_code == "PT08_HIDDEN_ACCEPTANCE_NOT_VALIDATED"
    assert {e["state"] for e in result.machine.log} == {"PRECHECK"}


def test_case_19_an_unfrozen_manifest_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(gov, "hidden_acceptance_is_validated", lambda *a, **k: True)
    with pytest.raises(gov.RunnerRefusal) as exc:
        ev.assert_scoring_prerequisites("PT08")
    assert exc.value.code == gov.MANIFEST_NOT_FROZEN


def test_case_19b_the_dry_run_reports_the_freeze_status_without_changing_it(tmp_path):
    record = _run(tmp_path).record
    assert record["manifest_freeze"]["manifest_frozen"] is False
    assert record["manifest_freeze"]["changed_by_this_runner"] is False
    private = gov.default_private_root() / "tasks" / "PT08" / "evaluator_manifest.json"
    if private.is_file():
        assert json.loads(private.read_text(encoding="utf-8"))["status"] == "review"


# --------------------------------------------------------------------------- #
# 20-21. Artifact integrity
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("field", list(gov.FIREWALL_FIELDS))
def test_case_20_a_diagnostic_flag_flipped_to_confirmatory_fails_closed(field):
    purpose = gov.RUN_PURPOSES[PURPOSE]
    flags = purpose.firewall_flags()
    flags[field] = True
    with pytest.raises(gov.RunnerRefusal) as exc:
        gov.assert_firewall_consistent(purpose, flags)
    assert exc.value.code == gov.DIAGNOSTIC_FIREWALL_INCONSISTENT


def test_case_21_a_run_artifact_missing_its_purpose_fails_closed(tmp_path):
    directory = art.ArtifactDirectory(
        tmp_path / "runs", "r", gov.RUN_PURPOSES[PURPOSE]
    ).create()
    with pytest.raises(gov.RunnerRefusal):
        art.write_run_record(directory, {"schema_version": "1.0.0", "run_id": "r"})
    assert not (directory.run_dir / "run_record.json").exists()


def test_case_21b_a_diagnostic_artifact_may_not_enter_the_confirmatory_dataset():
    purpose = gov.RUN_PURPOSES[PURPOSE]
    with pytest.raises(gov.RunnerRefusal) as exc:
        gov.assert_artifact_area_permitted(
            REPO / "experiments" / "v2" / "results" / "run-1", purpose
        )
    assert exc.value.code == gov.DIAGNOSTIC_ARTIFACT_IN_CONFIRMATORY_AREA


# --------------------------------------------------------------------------- #
# 22. Execution against the canonical repository
# --------------------------------------------------------------------------- #
def test_case_22_direct_canonical_repository_execution_fails_closed(tmp_path):
    with pytest.raises(gov.RunnerRefusal) as exc:
        gov.assert_not_canonical_repository(REPO, REPO)
    assert exc.value.code == gov.CANONICAL_REPOSITORY_EXECUTION_REFUSED


def test_case_22b_the_pipeline_never_points_the_model_at_the_repository(tmp_path):
    record = _run(tmp_path).record
    workspace = Path(record["worktree"]["prepared_root"]).resolve()
    assert REPO.resolve() not in workspace.parents
    assert workspace != REPO.resolve()
    argv = record["fresh_launch"]["argv"]
    assert str(REPO) not in " ".join(argv)


def test_case_22c_the_canonical_repository_is_unchanged_by_a_dry_run(tmp_path):
    before = gov.repository_state(REPO)
    _run(tmp_path)
    gov.assert_canonical_repository_unchanged(before, REPO)
