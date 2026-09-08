"""Runner-time enforcement: TD-B22, C1 delivery, fresh launch, model identity.

Each section proves one enforcement surface in isolation, against the real
implementation rather than a description of it. The worktree cases build a real
prepared snapshot and then damage it, so the check under test is the one that
fires; the launch cases build real commands; the identity cases feed real
approved-shape runtime evidence.

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
import run_evaluation as ev
import run_governance as gov
import run_worktree as wt
import runner_fixtures as fx
import substrate_identity as si

REPO = Path(__file__).resolve().parents[4]
PT08 = REPO / "experiments" / "v2" / "tasks" / "public" / "PT08.md"
PT08_SHA = "a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2"


@pytest.fixture
def prepared(tmp_path):
    """A real, governed C1 worktree for PT08."""
    result = pmw.prepare_model_worktree(
        pmw.PreparationRequest(
            condition="C1",
            source_root=REPO,
            dest_root=tmp_path / "worktree",
            task_path=PT08,
            task_id="PT08",
        )
    )
    return result


def _enforce(prepared, **overrides):
    kwargs = dict(
        root=prepared.snapshot_root,
        manifest=prepared.manifest,
        condition="C1",
        expected_task_sha=PT08_SHA,
        repo=REPO,
    )
    kwargs.update(overrides)
    return wt.enforce_prepared_worktree(**kwargs)


# --------------------------------------------------------------------------- #
# TD-B22 — the nine runner-time checks
# --------------------------------------------------------------------------- #
def test_a_governed_worktree_passes_every_runner_time_check(prepared):
    enforcement = _enforce(prepared)
    names = [c["check"] for c in enforcement.checks]
    assert names == [
        "canonical_repository_not_used",
        "prepared_manifest_verified",
        "task_sha_verified",
        "substrate_identity_verified",
        "allowed_tree_enforced",
        "no_unexpected_model_visible_file",
        "architecture_delivery_verified",
        "prepared_bytes_unchanged_before_launch",
        "worktree_content_hash_recorded",
    ]
    assert all(c["result"] == "PASS" for c in enforcement.checks)
    assert enforcement.content_hash == prepared.manifest["content_hash"]
    assert enforcement.substrate["content_hash"] == gov.SUBSTRATE_CONTENT_HASH


def test_the_enforcement_record_does_not_claim_live_runtime_validation(prepared):
    payload = _enforce(prepared).to_dict()
    assert payload["status"] == "ENFORCED"
    assert payload["live_runtime_validated"] is False
    assert payload["decision"] == "TD-B22"


def test_the_worktree_content_hash_is_recorded(prepared):
    enforcement = _enforce(prepared)
    assert enforcement.to_dict()["worktree_content_hash"] == enforcement.content_hash
    assert len(enforcement.content_hash) == 64


def test_a_wrong_task_hash_is_refused(prepared):
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared, expected_task_sha="0" * 64)
    assert exc.value.code == gov.TASK_SHA_MISMATCH


def test_a_wrong_substrate_identity_is_refused(prepared):
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared, expected_substrate_hash="0" * 64)
    assert exc.value.code == gov.SUBSTRATE_IDENTITY_MISMATCH


def test_a_wrong_substrate_entry_count_is_refused(prepared):
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared, expected_substrate_entries=1)
    assert exc.value.code == gov.SUBSTRATE_IDENTITY_MISMATCH


def test_an_unexpected_model_visible_file_is_refused(prepared):
    (prepared.snapshot_root / "libs" / "SMUGGLED.md").write_text("x\n", encoding="utf-8")
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared)
    assert exc.value.code == gov.UNEXPECTED_MODEL_VISIBLE_FILE


def test_a_path_outside_the_allowlist_is_refused(prepared):
    manifest = copy.deepcopy(prepared.manifest)
    manifest["entries"].append(
        {"path": "docs/v2/ARCHITECTURE_CONTEXT.md", "sha256": "0" * 64, "bytes": 1}
    )
    manifest["entry_count"] = len(manifest["entries"])
    manifest["content_hash"] = wt._content_hash_of_entries(manifest["entries"])
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared, manifest=manifest)
    assert exc.value.code == gov.WORKTREE_PATH_NOT_ALLOWLISTED


def test_bytes_edited_after_preparation_are_refused_before_launch(prepared):
    target = prepared.snapshot_root / "package.json"
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared)
    assert exc.value.code == gov.PREPARED_WORKTREE_DIRTY


def test_a_deleted_prepared_file_is_refused_before_launch(prepared):
    (prepared.snapshot_root / "package.json").unlink()
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared)
    assert exc.value.code == gov.PREPARED_WORKTREE_DIRTY


def test_a_manifest_whose_content_hash_does_not_recompute_is_refused(prepared):
    manifest = copy.deepcopy(prepared.manifest)
    manifest["content_hash"] = "0" * 64
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared, manifest=manifest)
    assert exc.value.code == gov.PREPARED_MANIFEST_INVALID


@pytest.mark.parametrize("key", list(wt.REQUIRED_MANIFEST_KEYS))
def test_a_manifest_missing_any_governed_key_is_refused(prepared, key):
    manifest = copy.deepcopy(prepared.manifest)
    manifest.pop(key)
    with pytest.raises(gov.RunnerRefusal) as exc:
        wt.verify_prepared_manifest(manifest)
    assert exc.value.code == gov.PREPARED_MANIFEST_INVALID


def test_the_runner_refuses_to_execute_over_the_canonical_repository(tmp_path):
    with pytest.raises(gov.RunnerRefusal) as exc:
        gov.assert_not_canonical_repository(REPO, REPO)
    assert exc.value.code == gov.CANONICAL_REPOSITORY_EXECUTION_REFUSED
    with pytest.raises(gov.RunnerRefusal):
        gov.assert_not_canonical_repository(REPO / "libs", REPO)
    with pytest.raises(gov.RunnerRefusal):
        gov.assert_not_canonical_repository(REPO.parent, REPO)
    # a git working tree is refused even when it is elsewhere
    (tmp_path / ".git").mkdir()
    with pytest.raises(gov.RunnerRefusal) as exc:
        gov.assert_not_canonical_repository(tmp_path, REPO)
    assert exc.value.code == gov.CANONICAL_REPOSITORY_EXECUTION_REFUSED


def test_the_allowlist_predicate_is_the_approved_one_not_a_copy():
    """Check 5 delegates: a change to the approved allowlist changes the runner."""
    source = (REPO / "experiments" / "v2" / "harness" / "run_worktree.py").read_text(
        encoding="utf-8"
    )
    assert "si.is_allowed_path" in source
    assert si.is_allowed_path("libs/core/src/index.ts")
    assert not si.is_allowed_path("docs/v2/ARCHITECTURE_CONTEXT.md")


# --------------------------------------------------------------------------- #
# C1 architecture delivery
# --------------------------------------------------------------------------- #
def test_c1_delivers_no_architecture_and_the_runner_verifies_it(prepared):
    assert gov.architecture_delivery_for("C1") == "none"
    gov.assert_architecture_delivery_none("C1")
    enforcement = _enforce(prepared)
    assert enforcement.architecture_delivery == "none"


@pytest.mark.parametrize("condition", ["C3", "C4"])
def test_a_condition_that_delivers_architecture_is_refused_for_this_diagnostic(condition):
    with pytest.raises(gov.RunnerRefusal) as exc:
        gov.assert_architecture_delivery_none(condition)
    assert exc.value.code == gov.ARCHITECTURE_DELIVERY_VIOLATION


def test_a_manifest_claiming_the_wrong_delivery_is_refused(prepared):
    manifest = copy.deepcopy(prepared.manifest)
    manifest["architecture_delivery"] = "prompt_injection"
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared, manifest=manifest)
    assert exc.value.code == gov.ARCHITECTURE_DELIVERY_VIOLATION


@pytest.mark.parametrize(
    "field,value",
    [
        ("architecture_sha256", "a" * 64),
        ("architecture_persistent_path", "CLAUDE.md"),
        ("generic_guidance_sha256", "b" * 64),
    ],
)
def test_a_c1_payload_of_any_kind_is_refused(prepared, field, value):
    manifest = copy.deepcopy(prepared.manifest)
    manifest[field] = value
    with pytest.raises(gov.RunnerRefusal) as exc:
        wt.verify_architecture_delivery(prepared.snapshot_root, manifest, "C1")
    assert exc.value.code == gov.ARCHITECTURE_DELIVERY_VIOLATION


def test_an_architecture_file_injected_into_c1_is_caught_at_runner_time(prepared):
    """The payload reaching the tree is caught even when the manifest is silent."""
    injected = prepared.snapshot_root / "ARCHITECTURE_CONTEXT.md"
    injected.write_text(
        (REPO / "docs" / "v2" / "ARCHITECTURE_CONTEXT.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    manifest = copy.deepcopy(prepared.manifest)
    entries = wt._on_disk_entries(prepared.snapshot_root)
    manifest["entries"] = entries
    manifest["entry_count"] = len(entries)
    manifest["content_hash"] = wt._content_hash_of_entries(entries)
    with pytest.raises(gov.RunnerRefusal) as exc:
        _enforce(prepared, manifest=manifest)
    assert exc.value.code in {
        gov.ARCHITECTURE_DELIVERY_VIOLATION,
        gov.WORKTREE_PATH_NOT_ALLOWLISTED,
    }


# --------------------------------------------------------------------------- #
# Per-condition delegation: the enforcement layer is general, not C1-shaped
# --------------------------------------------------------------------------- #
def _prepare_condition(tmp_path, condition, **kwargs):
    return pmw.prepare_model_worktree(
        pmw.PreparationRequest(
            condition=condition, source_root=REPO,
            dest_root=tmp_path / condition.lower(),
            task_path=PT08, task_id="PT08", **kwargs,
        )
    )


@pytest.mark.parametrize(
    "condition,kwargs,expected_delivery",
    [
        ("C1", {}, "none"),
        ("C2", {"generic_guidance_text": "Keep functions small.\n"}, "none"),
        ("C3", {"architecture_text": None}, "persistent_instruction_file"),
        ("C4", {"architecture_text": None}, "prompt_injection"),
    ],
)
def test_the_enforcement_layer_accepts_each_condition_own_governed_delivery(
    tmp_path, condition, kwargs, expected_delivery
):
    """The runner enforces every condition's *own* rule, not C1's rule everywhere.

    A guard that refused a legitimate C2 guidance payload — because C2's
    architecture delivery is also ``none`` — would fail closed on a condition
    that is allowed to carry one. Asserted for all four arms so the general
    delegation cannot regress into a C1-shaped special case.
    """
    if "architecture_text" in kwargs and kwargs["architecture_text"] is None:
        kwargs = dict(kwargs)
        kwargs["architecture_text"] = (
            REPO / "docs" / "v2" / "ARCHITECTURE_CONTEXT.md"
        ).read_text(encoding="utf-8")
    prepared = _prepare_condition(tmp_path, condition, **kwargs)
    enforcement = _enforce(prepared, root=prepared.snapshot_root,
                           manifest=prepared.manifest, condition=condition)
    assert enforcement.architecture_delivery == expected_delivery
    assert all(c["result"] == "PASS" for c in enforcement.checks)


def test_the_permitted_guidance_condition_agrees_with_the_approved_preparer():
    """The named condition is checked against the rule the preparer enforces."""
    permitted = gov.GENERIC_GUIDANCE_CONDITION
    for condition in pmw.CONDITIONS:
        request = pmw.PreparationRequest(
            condition=condition, source_root=REPO, dest_root=Path("unused"),
            generic_guidance_text="x",
            architecture_text=("y" if condition in ("C3", "C4") else None),
        )
        if condition == permitted:
            pmw._validate_condition_payloads(request)  # must not raise
        else:
            with pytest.raises(pmw.WorktreePreparationError) as exc:
                pmw._validate_condition_payloads(request)
            assert exc.value.code == "GUIDANCE_PAYLOAD_NOT_ALLOWED", condition


def test_guidance_supplied_to_a_condition_that_may_not_carry_it_is_refused(tmp_path):
    prepared = _prepare_condition(tmp_path, "C1")
    manifest = copy.deepcopy(prepared.manifest)
    manifest["generic_guidance_sha256"] = "b" * 64
    with pytest.raises(gov.RunnerRefusal) as exc:
        wt.verify_architecture_delivery(prepared.snapshot_root, manifest, "C1")
    assert exc.value.code == gov.ARCHITECTURE_DELIVERY_VIOLATION


# --------------------------------------------------------------------------- #
# Fresh process / session enforcement
# --------------------------------------------------------------------------- #
def _launch(**kwargs):
    base = dict(prompt_path="/tmp/prompt.md", workspace="/tmp/wt", require_model=False)
    base.update(kwargs)
    return ma.build_fresh_launch(**base)


def test_a_fresh_launch_is_built_without_any_session_reuse():
    plan = _launch()
    assert plan.argv[:3] == ("claude", "-p", "--no-session-persistence")
    assert not any(
        tok in plan.argv for tok in ("--resume", "-r", "--continue", "-c", "--from-pr")
    )
    assert ca.check_session_flags(plan.argv) == []
    assert "CLAUDE_CODE_DISABLE_WORKFLOWS" in plan.environment()


@pytest.mark.parametrize(
    "flag,code",
    [
        ("--resume", gov.SESSION_RESUME_REJECTED),
        ("-r", gov.SESSION_RESUME_REJECTED),
        ("--continue", gov.SESSION_CONTINUE_REJECTED),
        ("-c", gov.SESSION_CONTINUE_REJECTED),
        ("--from-pr", gov.SESSION_RESUME_REJECTED),
        ("--fallback-model", gov.FALLBACK_MODEL_REJECTED),
    ],
)
def test_every_restoration_or_substitution_flag_is_rejected(flag, code):
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launch(extra=[flag, "value"])
    assert exc.value.code == code


def test_a_reused_session_id_is_rejected_and_a_fresh_one_is_allowed():
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launch(session_id="abc", previous_session_ids=["abc"])
    assert exc.value.code == gov.SESSION_ID_REUSED
    plan = _launch(session_id="fresh-1", previous_session_ids=["abc"])
    assert "--session-id" in plan.argv and "fresh-1" in plan.argv


def test_an_inline_restoration_flag_is_also_rejected():
    with pytest.raises(gov.RunnerRefusal):
        _launch(extra=["--resume=abc"])
    with pytest.raises(gov.RunnerRefusal) as exc:
        _launch(session_id="abc", previous_session_ids=["abc"])
    assert exc.value.code == gov.SESSION_ID_REUSED


def test_the_launch_manifest_records_argv_only():
    plan = _launch(model_id="claude-sonnet-5", require_model=True)
    assert set(plan.launch_manifest()) == {"argv"}
    assert ca.load_launch_manifest  # the frozen validator is the consumer


# --------------------------------------------------------------------------- #
# Model adapter — no selection, no fallback
# --------------------------------------------------------------------------- #
def test_a_real_invocation_is_refused_while_no_primary_model_is_selected():
    adapter = ma.ModelInvocationAdapter(
        mode="real", registry_primary_model=None, governed_ids=("claude-sonnet-5",)
    )
    with pytest.raises(gov.RunnerRefusal) as exc:
        adapter.assert_real_invocation_permitted("claude-sonnet-5")
    assert exc.value.code == gov.PRIMARY_MODEL_NOT_SELECTED


def test_the_repository_still_records_no_selected_primary_model():
    assert gov.primary_model() is None


def test_a_real_invocation_without_a_model_id_is_refused():
    adapter = ma.ModelInvocationAdapter(mode="real", registry_primary_model="x")
    with pytest.raises(gov.RunnerRefusal) as exc:
        adapter.assert_real_invocation_permitted(None)
    assert exc.value.code == gov.MODEL_SELECTION_REQUIRED


def test_an_ungoverned_model_id_is_refused():
    adapter = ma.ModelInvocationAdapter(
        mode="real", registry_primary_model="x", governed_ids=("claude-sonnet-5",)
    )
    with pytest.raises(gov.RunnerRefusal) as exc:
        adapter.assert_real_invocation_permitted("gpt-made-up")
    assert exc.value.code == gov.MODEL_ID_NOT_GOVERNED


def test_dry_run_reports_model_selection_required_and_never_substitutes_one():
    plan = _launch()
    assert plan.model_id is None
    assert plan.model_status == gov.MODEL_SELECTION_REQUIRED
    assert plan.executable is False
    assert "--model" not in plan.argv
    for banned in ("sonnet", "opus", "haiku", "fable"):
        assert not any(banned in tok for tok in plan.argv), banned


def test_a_dry_run_adapter_never_starts_a_process():
    def exploding(plan):  # pragma: no cover - must never be called
        raise AssertionError("the dry-run adapter started a process")

    adapter = ma.ModelInvocationAdapter(mode="dry-run", process_launcher=exploding)
    outcome = adapter.invoke(_launch())
    assert outcome.invoked is False
    assert outcome.status == "DRY_RUN_NO_INVOKE"


def test_the_default_process_launcher_refuses():
    adapter = ma.ModelInvocationAdapter(
        mode="real", registry_primary_model="claude-sonnet-5",
        governed_ids=("claude-sonnet-5",),
    )
    plan = _launch(model_id="claude-sonnet-5", require_model=True)
    with pytest.raises(gov.RunnerRefusal) as exc:
        adapter.invoke(plan)
    assert exc.value.code == gov.REAL_INVOCATION_NOT_ENABLED


def test_a_non_executable_plan_cannot_be_invoked_for_real():
    adapter = ma.ModelInvocationAdapter(
        mode="real", registry_primary_model="claude-sonnet-5",
        governed_ids=("claude-sonnet-5",),
        process_launcher=lambda p: ma.ModelInvocationOutcome(True, "X"),
    )
    with pytest.raises(gov.RunnerRefusal):
        adapter.invoke(_launch())


# --------------------------------------------------------------------------- #
# Q1 — model-id readback
# --------------------------------------------------------------------------- #
def test_a_matching_readback_validates():
    result = ma.validate_model_identity(
        "claude-sonnet-5", fx.runtime_evidence("claude-sonnet-5")
    )
    assert result.valid and result.resolved == "claude-sonnet-5"
    assert "system.init.model" in result.sources


def test_a_missing_readback_invalidates_the_run():
    with pytest.raises(gov.RunnerRefusal) as exc:
        ma.validate_model_identity("claude-sonnet-5", [{"type": "assistant"}])
    assert exc.value.code == gov.MODEL_READBACK_MISSING


def test_a_mismatched_readback_invalidates_the_run():
    with pytest.raises(gov.RunnerRefusal) as exc:
        ma.validate_model_identity("claude-sonnet-5", fx.runtime_evidence("claude-opus-4-8"))
    assert exc.value.code == gov.MODEL_READBACK_MISMATCH


def test_an_ambiguous_readback_invalidates_the_run():
    evidence = fx.runtime_evidence("claude-sonnet-5", usage_model="claude-opus-4-8")
    with pytest.raises(gov.RunnerRefusal) as exc:
        ma.validate_model_identity("claude-sonnet-5", evidence)
    assert exc.value.code == gov.MODEL_READBACK_AMBIGUOUS


def test_only_the_approved_evidence_fields_count_as_a_readback():
    """An echoed request must never be mistaken for a runtime readback."""
    echoed = [{"type": "user", "requested_model": "claude-sonnet-5"}]
    with pytest.raises(gov.RunnerRefusal) as exc:
        ma.validate_model_identity("claude-sonnet-5", echoed)
    assert exc.value.code == gov.MODEL_READBACK_MISSING


def test_a_dry_run_readback_is_recorded_as_not_performed_never_as_validated():
    result = ma.readback_not_performed("claude-sonnet-5")
    assert result.status == "NOT_PERFORMED_DRY_RUN"
    assert result.valid is False
    assert result.resolved is None


def test_runtime_evidence_loads_from_jsonl(tmp_path):
    path = fx.write_runtime_evidence(
        tmp_path / "run_output.jsonl", fx.runtime_evidence("claude-sonnet-5")
    )
    assert ma.validate_model_identity(
        "claude-sonnet-5", ma.load_runtime_evidence(path)
    ).valid


# --------------------------------------------------------------------------- #
# Q8 — invalid-model-id rejection
# --------------------------------------------------------------------------- #
def test_the_q8_probe_command_can_be_built_without_being_run():
    plan = ma.build_invalid_model_id_probe(
        "claude-not-a-real-model-xyz", prompt_path="/tmp/p.md", workspace="/tmp/wt"
    )
    assert "--model" in plan.argv and "claude-not-a-real-model-xyz" in plan.argv
    assert plan.executable is True  # buildable; building starts nothing


def test_a_governed_id_may_not_be_used_as_a_q8_probe():
    with pytest.raises(gov.RunnerRefusal) as exc:
        ma.build_invalid_model_id_probe(
            "claude-sonnet-5", prompt_path="/tmp/p.md", workspace="/tmp/wt"
        )
    assert exc.value.code == gov.MODEL_ID_NOT_GOVERNED


def test_q8_without_a_live_observation_is_not_validated():
    probe = ma.validate_invalid_model_id_rejection("bogus", exit_status=None)
    assert probe.status == gov.Q8_INVALID_MODEL_ID_NOT_VALIDATED_LIVE


@pytest.mark.parametrize(
    "exit_status,evidence,expected",
    [
        (1, [], "Q8_REJECTED"),
        (0, [], "Q8_NOT_REJECTED"),
        (1, None, "Q8_REJECTED"),
    ],
)
def test_q8_judges_a_supplied_observation(exit_status, evidence, expected):
    probe = ma.validate_invalid_model_id_rejection(
        "bogus", exit_status=exit_status, evidence=evidence
    )
    assert probe.status == expected


def test_q8_treats_a_silent_substitution_as_a_failure_of_the_control():
    probe = ma.validate_invalid_model_id_rejection(
        "bogus", exit_status=1, evidence=fx.runtime_evidence("claude-sonnet-5")
    )
    assert probe.status == "Q8_SILENTLY_DEGRADED"


# --------------------------------------------------------------------------- #
# Evaluation boundary and the freeze gate
# --------------------------------------------------------------------------- #
def test_pt08_hidden_acceptance_blocks_the_functional_channel():
    channel = ev.functional_acceptance_channel("PT08")
    assert channel.ready is False
    assert channel.code == "PT08_HIDDEN_ACCEPTANCE_NOT_VALIDATED"


def test_pt08_manifest_freeze_blocks_the_architecture_channel():
    channel = ev.architecture_scoring_channel("PT08")
    assert channel.ready is False
    assert channel.code == gov.MANIFEST_NOT_FROZEN
    assert channel.command is None


def test_a_scored_run_is_refused_before_execution():
    with pytest.raises(gov.RunnerRefusal) as exc:
        ev.assert_scoring_prerequisites("PT08")
    assert exc.value.code == "PT08_HIDDEN_ACCEPTANCE_NOT_VALIDATED"


def test_the_freeze_status_is_reported_and_never_changed():
    report = ev.freeze_status_report("PT08")
    assert report["manifest_frozen"] is False
    assert report["code"] == gov.MANIFEST_NOT_FROZEN
    assert report["changed_by_this_runner"] is False
    assert report["inspected_only"] is True


def test_the_architecture_channel_points_at_the_governed_oracle_and_copies_none_of_it(
    tmp_path,
):
    """With a synthetic 'frozen' authority the channel builds the oracle command."""
    matrix = tmp_path / "acceptance.csv"
    matrix.write_text(
        "task_id,status\nPT08,frozen\n", encoding="utf-8", newline="\n"
    )
    mount = tmp_path / "mount"
    mount.mkdir()
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    channel = ev.architecture_scoring_channel(
        "PT08",
        snapshot=snapshot,
        manifest_mount=mount,
        coding_worktree=tmp_path / "worktree",
        acceptance_matrix=matrix,
    )
    assert channel.ready
    assert any(
        Path(tok).as_posix().endswith(ev.ORACLE_CLI) for tok in channel.command
    ), channel.command
    source = (REPO / "experiments" / "v2" / "harness" / "run_evaluation.py").read_text(
        encoding="utf-8"
    )
    assert "dependencyDirection" not in source, "the oracle must not be duplicated"


def test_an_evaluator_mount_inside_the_coding_worktree_is_refused(tmp_path):
    matrix = tmp_path / "acceptance.csv"
    matrix.write_text("task_id,status\nPT08,frozen\n", encoding="utf-8", newline="\n")
    worktree = tmp_path / "worktree"
    (worktree / "mount").mkdir(parents=True)
    channel = ev.architecture_scoring_channel(
        "PT08",
        snapshot=tmp_path,
        manifest_mount=worktree / "mount",
        coding_worktree=worktree,
        acceptance_matrix=matrix,
    )
    assert channel.ready is False
    assert channel.code == gov.CANONICAL_REPOSITORY_EXECUTION_REFUSED


def test_the_two_evaluation_channels_stay_separate():
    plan = ev.build_evaluation_plan("PT08")
    assert [c.channel for c in plan.channels] == [
        "functional_hidden_acceptance",
        "architecture_opportunity_scoring",
    ]
    assert plan.ready is False
    assert "neither result is an input to the other" in plan.to_dict()["channel_separation"]
