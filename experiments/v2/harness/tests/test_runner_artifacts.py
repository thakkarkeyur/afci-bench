"""Run artifacts: the layout, the provenance, the firewall, and the capture.

The three properties that matter are (1) a diagnostic artifact carries its
purpose and its five quarantine flags or is never written, (2) it never lands in
a confirmatory area, and (3) the post-run capture carries enough provenance to
re-score the run without the model having touched the source repository.

Post-run capture is exercised with synthetic edits. No model is invoked, and no
artifact is written into experiments/v2/results or experiments/v2/analysis.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import prepare_model_worktree as pmw
import run_artifacts as art
import run_governance as gov
import run_v2
import run_worktree as wt
import runner_fixtures as fx

REPO = Path(__file__).resolve().parents[4]
PT08 = REPO / "experiments" / "v2" / "tasks" / "public" / "PT08.md"
PT08_SHA = "a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2"
PURPOSE = gov.RUN_PURPOSES["PT08_DIFFICULTY_DIAGNOSTIC"]


@pytest.fixture
def dry_run(tmp_path):
    result = run_v2.run(
        run_v2.RunRequest(
            task_id="PT08",
            condition="C1",
            run_purpose=PURPOSE.name,
            artifact_root=tmp_path / "runs",
            generated_at="fixture",
            audit_provider=fx.synthetic_clean_audit,
        )
    )
    assert result.refusal_code is None, result.refusal_detail
    return result


# --------------------------------------------------------------------------- #
# Layout and determinism
# --------------------------------------------------------------------------- #
def test_the_run_directory_carries_the_governed_artifact_set(dry_run):
    run_dir = Path(dry_run.run_dir)
    for name in (
        "run_record.json",
        "readiness.json",
        "context_audit.json",
        "launch_manifest.json",
        "prepared_manifest.json",
        "prompts/task_prompt.md",
    ):
        assert (run_dir / name).is_file(), name
    assert (run_dir / "worktree").is_dir()


def test_the_run_id_is_deterministic_and_carries_its_own_provenance():
    kwargs = dict(
        purpose=PURPOSE.name, task_id="PT08", condition="C1", task_sha=PT08_SHA,
        substrate_hash=gov.SUBSTRATE_CONTENT_HASH, mode="dry-run",
    )
    first = art.derive_run_id(**kwargs)
    assert first == art.derive_run_id(**kwargs)
    assert "pt08" in first and "c1" in first and "dry-run" in first
    changed = dict(kwargs)
    changed["task_sha"] = "0" * 64
    assert art.derive_run_id(**changed) != first


def test_two_identical_dry_runs_produce_the_same_record(tmp_path):
    def once(root):
        return run_v2.run(
            run_v2.RunRequest(
                task_id="PT08", condition="C1", run_purpose=PURPOSE.name,
                artifact_root=root, generated_at="fixture",
                audit_provider=fx.synthetic_clean_audit,
            )
        ).record

    first, second = once(tmp_path / "a"), once(tmp_path / "b")
    for block in ("run_purpose", "protocol_versions", "task_sha256", "condition"):
        assert first[block] == second[block], block
    assert first["worktree"]["content_hash"] == second["worktree"]["content_hash"]


def test_the_prompt_is_the_public_task_body_delivered_out_of_band(dry_run):
    prompt = Path(dry_run.run_dir) / "prompts" / "task_prompt.md"
    assert pmw.sha256_file(prompt) == PT08_SHA
    worktree = Path(dry_run.run_dir) / "worktree"
    assert not (worktree / "PT08.md").exists()
    assert not any(p.name == "task_prompt.md" for p in worktree.rglob("*"))


# --------------------------------------------------------------------------- #
# Part K field coverage
# --------------------------------------------------------------------------- #
def test_the_record_carries_every_governed_field(dry_run):
    record = dry_run.record
    assert record["run_id"] and record["run_purpose"]["name"] == PURPOSE.name
    assert record["task_id"] == "PT08"
    assert record["task_sha256"] == PT08_SHA
    assert record["condition"] == "C1"
    assert record["model"]["requested_model_id"] is None
    assert record["model"]["resolved_model_id"] is None
    assert record["environment"]["governed_cli_version"] == "2.1.209"
    assert record["environment"]["observed_cli_version"] is None
    assert set(record["protocol_versions"]) == set(art.PROTOCOL_DOCS)
    assert record["worktree"]["content_hash"]
    assert record["worktree"]["enforcement"]["substrate"]["content_hash"] == (
        gov.SUBSTRATE_CONTENT_HASH
    )
    assert record["context_audit"]["verdict"] == "CLEAN"
    assert record["context_audit"]["report_sha256"]
    assert record["fresh_launch"]["argv"]
    assert record["invocation"]["exit_status"] is None
    assert record["invocation"]["wall_clock_seconds"] is None
    assert record["post_run_capture"] is None
    assert record["evaluation"]["channels"]
    assert record["manifest_freeze"]["manifest_frozen"] is False
    assert record["artifacts"]
    assert record["prerequisite_blockers"]


def test_protocol_versions_are_content_addressed_so_they_cannot_drift():
    versions = art.protocol_versions()
    for key, value in versions.items():
        rel, _, digest = value.partition("@sha256:")
        assert rel == art.PROTOCOL_DOCS[key]
        assert digest == art.sha256_file(REPO / rel)[:16]


def test_the_environment_block_separates_governed_pins_from_observations():
    block = art.environment_block()
    assert block["governed_cli_version"] == "2.1.209"
    assert block["governed_agent_sdk_version"] == "0.3.212"
    assert block["observed_cli_version"] is None
    assert block["isolated_environment_verified"] is False


# --------------------------------------------------------------------------- #
# The firewall
# --------------------------------------------------------------------------- #
def test_the_record_carries_the_purpose_and_all_five_quarantine_flags(dry_run):
    block = dry_run.record["run_purpose"]
    assert block["name"] == "PT08_DIFFICULTY_DIAGNOSTIC"
    assert block["decision_id"] == "SL-PT08-01"
    assert block["confirmatory"] is False
    for field in gov.FIREWALL_FIELDS:
        assert block[field] is False, field


def test_a_record_with_no_purpose_is_refused(dry_run):
    record = copy.deepcopy(dry_run.record)
    record.pop("run_purpose")
    with pytest.raises(gov.RunnerRefusal) as exc:
        art.validate_run_record(record)
    assert exc.value.code in {
        gov.RUN_ARTIFACT_PURPOSE_MISSING, gov.PREPARED_MANIFEST_INVALID
    }


@pytest.mark.parametrize("field", list(gov.FIREWALL_FIELDS))
def test_a_flag_flipped_to_confirmatory_is_refused(dry_run, field):
    record = copy.deepcopy(dry_run.record)
    record["run_purpose"][field] = True
    with pytest.raises(gov.RunnerRefusal):
        art.validate_run_record(record)


@pytest.mark.parametrize("field", list(gov.FIREWALL_FIELDS))
def test_a_dropped_flag_is_refused(dry_run, field):
    record = copy.deepcopy(dry_run.record)
    record["run_purpose"].pop(field)
    with pytest.raises(gov.RunnerRefusal):
        art.validate_run_record(record)


def test_the_record_can_never_describe_a_scored_result(dry_run):
    record = copy.deepcopy(dry_run.record)
    record["outcome"]["scored"] = True
    with pytest.raises(gov.RunnerRefusal):
        art.validate_run_record(record)
    record = copy.deepcopy(dry_run.record)
    record["outcome"]["is_result"] = True
    with pytest.raises(gov.RunnerRefusal):
        art.validate_run_record(record)


def test_an_invalid_record_is_never_written(tmp_path):
    directory = art.ArtifactDirectory(tmp_path / "runs", "r1", PURPOSE).create()
    with pytest.raises(gov.RunnerRefusal):
        art.write_run_record(directory, {"schema_version": "1.0.0"})
    assert not (directory.run_dir / "run_record.json").exists()


def test_the_firewall_matches_the_governance_record_itself():
    governed = gov.governed_firewall_from_record()
    assert governed["run_purpose"] == "PT08_DIFFICULTY_DIAGNOSTIC"
    for field in gov.FIREWALL_FIELDS:
        assert governed[field] is False, field
    assert PURPOSE.firewall_flags() == {f: False for f in gov.FIREWALL_FIELDS}


# --------------------------------------------------------------------------- #
# Confirmatory-area refusal
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("area", ["results", "analysis"])
def test_a_diagnostic_artifact_may_not_be_written_into_a_confirmatory_area(area):
    target = REPO / "experiments" / "v2" / area
    with pytest.raises(gov.RunnerRefusal) as exc:
        gov.assert_artifact_area_permitted(target, PURPOSE)
    assert exc.value.code == gov.DIAGNOSTIC_ARTIFACT_IN_CONFIRMATORY_AREA
    with pytest.raises(gov.RunnerRefusal):
        gov.assert_artifact_area_permitted(target / "nested" / "deep", PURPOSE)


def test_the_dry_run_writes_nothing_into_the_confirmatory_areas(dry_run):
    for area in ("results", "analysis"):
        stray = [
            p.name
            for p in (REPO / "experiments" / "v2" / area).rglob("*")
            if p.is_file() and p.name != "README.md"
        ]
        assert not stray, f"experiments/v2/{area} gained {stray}"


def test_the_default_artifact_root_is_outside_the_repository():
    root = gov.default_artifact_root()
    assert REPO.resolve() not in root.resolve().parents
    assert root.resolve() != REPO.resolve()


# --------------------------------------------------------------------------- #
# Post-run capture (synthetic edits)
# --------------------------------------------------------------------------- #
@pytest.fixture
def prepared(tmp_path):
    return pmw.prepare_model_worktree(
        pmw.PreparationRequest(
            condition="C1", source_root=REPO, dest_root=tmp_path / "worktree",
            task_path=PT08, task_id="PT08",
        )
    )


def test_the_capture_records_added_modified_and_deleted_paths(tmp_path, prepared):
    root = prepared.snapshot_root
    (root / "libs" / "features" / "src" / "ceiling.ts").write_text(
        "export const ceiling = 1;\n", encoding="utf-8", newline="\n"
    )
    target = root / "package.json"
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    (root / "jest.preset.js").unlink()

    capture = wt.capture_post_run_worktree(
        worktree=root,
        capture_root=tmp_path / "post",
        prepared_manifest=prepared.manifest,
        repo=REPO,
    )
    assert capture.added == ["libs/features/src/ceiling.ts"]
    assert capture.modified == ["package.json"]
    assert capture.deleted == ["jest.preset.js"]
    assert capture.unchanged is False


def test_the_capture_preserves_the_prepared_starting_hash(tmp_path, prepared):
    prepared_hash = prepared.manifest["content_hash"]
    (prepared.snapshot_root / "libs" / "x.ts").write_text("1\n", encoding="utf-8")
    capture = wt.capture_post_run_worktree(
        worktree=prepared.snapshot_root,
        capture_root=tmp_path / "post",
        prepared_manifest=prepared.manifest,
        repo=REPO,
    )
    assert capture.prepared_content_hash == prepared_hash
    assert capture.post_run_content_hash != prepared_hash
    assert len(capture.post_run_content_hash) == 64


def test_an_unchanged_worktree_is_recorded_as_unchanged(tmp_path, prepared):
    capture = wt.capture_post_run_worktree(
        worktree=prepared.snapshot_root,
        capture_root=tmp_path / "post",
        prepared_manifest=prepared.manifest,
        repo=REPO,
    )
    assert capture.unchanged is True
    assert capture.post_run_content_hash == prepared.manifest["content_hash"]


def test_the_capture_is_available_to_evaluation_outside_the_coding_worktree(
    tmp_path, prepared
):
    capture = wt.capture_post_run_worktree(
        worktree=prepared.snapshot_root,
        capture_root=tmp_path / "post",
        prepared_manifest=prepared.manifest,
        repo=REPO,
    )
    capture_root = Path(capture.capture_root)
    assert capture_root.is_dir()
    assert prepared.snapshot_root not in capture_root.parents
    assert (capture_root / "package.json").is_file()


def test_the_capture_refuses_a_non_empty_destination(tmp_path, prepared):
    dest = tmp_path / "post"
    dest.mkdir()
    (dest / "stale").write_text("x", encoding="utf-8")
    with pytest.raises(gov.RunnerRefusal) as exc:
        wt.capture_post_run_worktree(
            worktree=prepared.snapshot_root,
            capture_root=dest,
            prepared_manifest=prepared.manifest,
            repo=REPO,
        )
    assert exc.value.code == gov.PREPARED_WORKTREE_DIRTY


def test_the_capture_refuses_if_the_canonical_repository_moved(tmp_path, prepared):
    stale = {"head": "0" * 40, "porcelain": ""}
    with pytest.raises(gov.RunnerRefusal) as exc:
        wt.capture_post_run_worktree(
            worktree=prepared.snapshot_root,
            capture_root=tmp_path / "post",
            prepared_manifest=prepared.manifest,
            repo=REPO,
            repository_state_before=stale,
        )
    assert exc.value.code == gov.CANONICAL_REPOSITORY_MODIFIED


def test_the_capture_refuses_the_canonical_repository_as_its_source(tmp_path, prepared):
    with pytest.raises(gov.RunnerRefusal) as exc:
        wt.capture_post_run_worktree(
            worktree=REPO,
            capture_root=tmp_path / "post",
            prepared_manifest=prepared.manifest,
            repo=REPO,
        )
    assert exc.value.code == gov.CANONICAL_REPOSITORY_EXECUTION_REFUSED


def test_the_capture_provenance_is_enough_to_reproduce_evaluation(tmp_path, prepared):
    (prepared.snapshot_root / "libs" / "y.ts").write_text("2\n", encoding="utf-8")
    payload = wt.capture_post_run_worktree(
        worktree=prepared.snapshot_root,
        capture_root=tmp_path / "post",
        prepared_manifest=prepared.manifest,
        repo=REPO,
    ).to_dict()
    assert set(payload) == {
        "capture_root", "prepared_content_hash", "post_run_content_hash",
        "unchanged", "entry_count", "changed_paths",
    }
    assert set(payload["changed_paths"]) == {"added", "modified", "deleted"}


# --------------------------------------------------------------------------- #
# The record schema lives in the harness, and why
# --------------------------------------------------------------------------- #
def test_the_runner_schema_is_harness_local_and_the_pinned_schemas_are_untouched():
    """The pinned schema directory must gain nothing: it is linkage-relevant."""
    assert art.SCHEMA_PATH.is_file()
    assert art.SCHEMA_PATH.parent.name == "harness"
    pinned = REPO / "experiments" / "v2" / "schemas"
    assert not (pinned / "run_record.schema.json").exists()
    schema = json.loads(art.SCHEMA_PATH.read_text(encoding="utf-8"))
    assert "byte-pinned" in schema["description"]


def test_the_pinned_run_manifest_schema_still_cannot_carry_the_firewall():
    """The reason the runner reports a blocker instead of editing the schema."""
    pinned = json.loads(
        (REPO / "experiments" / "v2" / "schemas" / "run_manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert pinned["additionalProperties"] is False
    for field in ("run_purpose", *gov.FIREWALL_FIELDS):
        assert field not in pinned["properties"], field
