"""`SL-RUNID-01` - repetition identity in `run_id`.

**The defect this closes.** `derive_run_id` hashed only the run's CONTENT
identity: purpose, task, condition, task sha, substrate hash and mode. Every
repetition of one task/condition therefore produced the SAME id. The `PT08`
difficulty diagnostic ran three repetitions and all three minted an identical
`run_id`; they stayed separable only because the operator handed each repetition
its own ``--artifact-root``. A multi-repetition run writing into a single root
would have had `R2` overwrite `R1` silently, and a record set carrying three rows
with one id could not be reconciled against the protocol that asked for three.

**What the fix is, and is not.** The repetition index joins the seed and the
readable prefix, so `R1`/`R2`/`R3` differ. Determinism is unchanged. This is an
ARTIFACT-IDENTITY change: no task body, no opportunity, no denominator, no gate
and no scientific claim moves, and nothing already written is rewritten.

No model is invoked here and no artifact is written to a confirmatory area.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import run_artifacts as art
import run_governance as gov
import run_v2

REPO = Path(__file__).resolve().parents[4]
SCHEMA = json.loads(
    (REPO / "experiments" / "v2" / "harness" / "run_record.schema.json").read_text(
        encoding="utf-8"
    )
)
PURPOSE = gov.RUN_PURPOSES["PT08_DIFFICULTY_DIAGNOSTIC"]

SEED = dict(
    purpose="PT08_DIFFICULTY_DIAGNOSTIC",
    task_id="PT08",
    condition="C1",
    task_sha="a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2",
    substrate_hash="0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3",
    mode="real",
)


# --------------------------------------------------------------------------- #
# 1. The collision is gone.
# --------------------------------------------------------------------------- #
def test_three_repetitions_of_one_run_identity_get_three_distinct_ids():
    ids = [art.derive_run_id(**SEED, repetition=r) for r in (1, 2, 3)]
    assert len(set(ids)) == 3, f"R1/R2/R3 still collide: {ids}"


def test_the_old_derivation_would_have_collided():
    """Guard the guard: the defect was real, and this test would have caught it."""
    without = [
        "|".join([SEED["purpose"], SEED["task_id"], SEED["condition"],
                  SEED["task_sha"], SEED["substrate_hash"], SEED["mode"]])
        for _ in (1, 2, 3)
    ]
    assert len(set(without)) == 1, (
        "the pre-SL-RUNID-01 seed carried no repetition, so all three repetitions "
        "hashed identically; that is the defect this module closes"
    )


def test_many_repetitions_are_pairwise_distinct():
    ids = [art.derive_run_id(**SEED, repetition=r) for r in range(1, 51)]
    assert len(set(ids)) == 50


def test_the_index_is_visible_in_the_id_without_hashing_anything():
    """A reader separates repetitions by eye, not by recomputing a digest."""
    for r in (1, 2, 3, 17):
        assert f"-r{r}-" in art.derive_run_id(**SEED, repetition=r)


# --------------------------------------------------------------------------- #
# 2. Determinism survives.
# --------------------------------------------------------------------------- #
def test_the_same_inputs_still_produce_the_same_id():
    first = art.derive_run_id(**SEED, repetition=2)
    second = art.derive_run_id(**SEED, repetition=2)
    assert first == second


def test_an_undeclared_repetition_is_the_governed_default():
    assert art.derive_run_id(**SEED) == art.derive_run_id(
        **SEED, repetition=art.DEFAULT_REPETITION
    )
    assert art.DEFAULT_REPETITION == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("condition", "C2"),
        ("mode", "dry-run"),
        ("task_id", "PT09"),
        ("task_sha", "0" * 64),
        ("substrate_hash", "1" * 64),
    ],
)
def test_the_content_identity_still_separates_runs(field, value):
    """The repetition index is an ADDITION; it must not mask the other inputs."""
    other = {**SEED, field: value}
    assert art.derive_run_id(**SEED, repetition=1) != art.derive_run_id(
        **other, repetition=1
    )


# --------------------------------------------------------------------------- #
# 3. Backward compatibility: the new ids cannot be confused with the old ones.
# --------------------------------------------------------------------------- #
def test_a_default_repetition_id_differs_from_the_pre_fix_form():
    """Migration: an id minted before this change is not silently re-derived.

    The `PT08` diagnostic artifacts keep the ids they were written with. Because
    the readable prefix now carries ``-r1-``, a post-SL-RUNID-01 id can never be
    mistaken for, or collide with, one of them.
    """
    old_seed = "|".join([SEED["purpose"], SEED["task_id"], SEED["condition"],
                         SEED["task_sha"], SEED["substrate_hash"], SEED["mode"]])
    old_digest = art.sha256_bytes(old_seed.encode("utf-8"))[:12]
    old_id = (
        f"{SEED['purpose'].lower().replace('_', '-')}-{SEED['task_id'].lower()}-"
        f"{SEED['condition'].lower()}-{SEED['mode']}-{old_digest}"
    )
    new_id = art.derive_run_id(**SEED)
    assert new_id != old_id
    assert "-r1-" in new_id and "-r1-" not in old_id


# --------------------------------------------------------------------------- #
# 4. A bad index refuses; it is never coerced.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bad", [0, -1, 1000, "2", 2.0, True])
def test_an_ungoverned_repetition_index_is_refused(bad):
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        art.derive_run_id(**SEED, repetition=bad)
    assert excinfo.value.code == gov.RUN_REPETITION_INVALID


def test_the_boundaries_themselves_are_accepted():
    assert art.normalise_repetition(1) == 1
    assert art.normalise_repetition(art.MAX_REPETITION) == art.MAX_REPETITION


# --------------------------------------------------------------------------- #
# 5. The record carries the repetition, and old records still validate.
# --------------------------------------------------------------------------- #
def _dry_run(tmp_path, repetition):
    return run_v2.run(
        run_v2.RunRequest(
            task_id="PT08",
            condition="C1",
            run_purpose=PURPOSE.name,
            repetition=repetition,
            artifact_root=tmp_path / f"runs-{repetition}",
            generated_at="fixture",
            keep_worktree=False,
        )
    )


def test_the_run_record_records_the_repetition_it_ran(tmp_path):
    result = _dry_run(tmp_path, 3)
    assert result.record is not None, result.refusal_code
    assert result.record["repetition"] == 3
    assert result.record["repetition_declared"] is True
    assert "-r3-" in result.record["run_id"]


def test_an_undeclared_repetition_is_recorded_as_undeclared(tmp_path):
    result = _dry_run(tmp_path, None)
    assert result.record is not None, result.refusal_code
    assert result.record["repetition"] == 1
    assert result.record["repetition_declared"] is False


def test_two_repetitions_write_into_two_directories_under_one_root(tmp_path):
    """The behavioural point: one artifact root is now enough."""
    root = tmp_path / "shared"
    dirs = []
    for repetition in (1, 2):
        result = run_v2.run(
            run_v2.RunRequest(
                task_id="PT08",
                condition="C1",
                run_purpose=PURPOSE.name,
                repetition=repetition,
                artifact_root=root,
                generated_at="fixture",
                keep_worktree=False,
            )
        )
        assert result.record is not None, result.refusal_code
        dirs.append(result.run_dir)
    assert dirs[0] != dirs[1], "two repetitions still share one artifact directory"
    assert dirs[0].is_dir() and dirs[1].is_dir()


def test_a_record_written_before_td_b41_still_validates(tmp_path):
    """Backward compatibility, proved rather than asserted in prose.

    The field is OPTIONAL in the schema precisely so an artifact written before
    this change stays readable. Rewriting the `PT08` diagnostic records to add a
    field is exactly what this package must not do.
    """
    result = _dry_run(tmp_path, 2)
    legacy = dict(result.record)
    legacy.pop("repetition")
    legacy.pop("repetition_declared")
    art.validate_run_record(legacy, SCHEMA)


def test_the_schema_leaves_the_field_optional_and_bounded():
    props = SCHEMA["properties"]
    assert "repetition" in props and "repetition_declared" in props
    assert "repetition" not in SCHEMA["required"], (
        "making it required would invalidate every record written before SL-RUNID-01"
    )
    assert props["repetition"]["minimum"] == 1
    assert props["repetition"]["maximum"] == art.MAX_REPETITION


def test_an_out_of_range_repetition_can_never_reach_a_record():
    """Enforcement is in the derivation, not in the schema.

    ``context_audit.validate_against_schema`` is a deliberate JSON-Schema SUBSET
    and does not implement ``minimum``/``maximum``, so the bounds in the schema
    document the field rather than police it. The policing happens where the
    value enters: an out-of-range index refuses before a record exists at all.
    """
    with pytest.raises(gov.RunnerRefusal) as excinfo:
        art.build_run_record(
            purpose=PURPOSE, run_id="x", task_id="PT08", task_sha256="0" * 64,
            condition="C1", mode="dry-run", repetition=0, state_log=[], model={},
            environment={}, worktree={}, context_audit={}, fresh_launch={},
            invocation={}, model_identity={}, post_run_capture=None,
            evaluation={}, manifest_freeze={}, artifacts={},
            prerequisite_blockers=[], outcome={},
        )
    assert excinfo.value.code == gov.RUN_REPETITION_INVALID


# --------------------------------------------------------------------------- #
# 6. This is an identity change and nothing else.
# --------------------------------------------------------------------------- #
def test_the_repetition_never_touches_the_quarantine_flags(tmp_path):
    for repetition in (1, 2):
        record = _dry_run(tmp_path, repetition).record
        assert record is not None
        block = record["run_purpose"]
        assert block["confirmatory"] is False
        assert block["confirmatory_eligible"] is False
        assert block["enters_confirmatory_dataset"] is False
        assert block["enters_confirmatory_e1_analysis"] is False
        assert block["enters_treatment_effect_analysis"] is False
        assert block["enters_power_estimation"] is False


def test_the_cli_exposes_the_flag():
    parser = run_v2._build_parser()
    args = parser.parse_args(
        ["--task", "PT08", "--condition", "C1",
         "--run-purpose", PURPOSE.name, "--dry-run", "--repetition", "4"]
    )
    assert args.repetition == 4
    default = parser.parse_args(
        ["--task", "PT08", "--condition", "C1",
         "--run-purpose", PURPOSE.name, "--dry-run"]
    )
    assert default.repetition is None, (
        "an omitted flag must stay UNDECLARED so the record can say so, rather "
        "than being pre-filled with 1 and reading as a deliberate choice"
    )
