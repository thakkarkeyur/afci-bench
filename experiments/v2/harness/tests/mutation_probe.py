#!/usr/bin/env python3
"""Probe driver for the runner's mutation tests. Run as a subprocess, never imported.

``test_runner_mutations.py`` copies the harness to a disposable directory, edits
one guard out of the copy, and runs this driver against it with ``PYTHONPATH``
pointing at that copy. Each case exercises exactly one guard and prints a single
``RESULT=<token>`` line, so the control copy and the mutated copy can be compared
mechanically rather than by reading the diff.

Usage::

    PYTHONPATH=<disposable harness copy> python mutation_probe.py <case> <scratch>

Every case is read-only with respect to both repositories and invokes no model.
"""
from __future__ import annotations

import copy
import json
import shutil
import sys
from pathlib import Path

import context_audit as ca
import model_adapter as ma
import prepare_model_worktree as pmw
import run_artifacts as art
import run_evaluation as ev
import run_governance as gov
import run_v2
import run_worktree as wt

PURPOSE_NAME = "PT08_DIFFICULTY_DIAGNOSTIC"
PT08_SHA = "a31bb515b79cc1e211a662de2a8761c97082dd8bf266ee5b4f660981435badf2"


def purpose() -> gov.RunPurpose:
    return gov.RUN_PURPOSES[PURPOSE_NAME]


def refusing(fn, *args, **kwargs) -> str:
    """``ACCEPTED`` when the guard let it through, ``REFUSED:<code>`` otherwise."""
    try:
        fn(*args, **kwargs)
    except gov.RunnerRefusal as exc:
        return f"REFUSED:{exc.code}"
    except pmw.WorktreePreparationError as exc:
        return f"REFUSED:{exc.code}"
    return "ACCEPTED"


def _prepare(scratch: Path, name: str = "wt"):
    dest = scratch / name
    if dest.exists():
        shutil.rmtree(dest)
    return pmw.prepare_model_worktree(
        pmw.PreparationRequest(
            condition="C1",
            source_root=gov.REPO,
            dest_root=dest,
            task_path=gov.public_task_path("PT08"),
            task_id="PT08",
        )
    )


def _enforce(prepared, **overrides) -> str:
    kwargs = dict(
        root=prepared.snapshot_root,
        manifest=prepared.manifest,
        condition="C1",
        expected_task_sha=PT08_SHA,
        repo=gov.REPO,
    )
    kwargs.update(overrides)
    return refusing(wt.enforce_prepared_worktree, **kwargs)


def _contaminated_audit(**kwargs) -> ca.AuditResult:
    launch = kwargs["launch"]
    return ca.AuditResult(
        run_id=kwargs["run_id"],
        condition=kwargs["condition"],
        generated_at=kwargs["generated_at"],
        temp_home="<probe>",
        config_dir="<probe>",
        auto_memory_disabled=True,
        autoupdater_disabled=True,
        config_dir_isolated=True,
        home_isolated=True,
        session_restored=False,
        session_status="fresh",
        session_violations=[],
        session_command_supplied=True,
        session_command_source=launch.source,
        session_command_flags=launch.flag_tokens(),
        detected=[],
        approved=[],
        component_status={k: "none" for k in ca.COMPONENT_KINDS},
        verdict="CONTAMINATED",
        reasons=["probe: unapproved context source present"],
    )


# --------------------------------------------------------------------------- #
# Cases
# --------------------------------------------------------------------------- #
def case_condition_gate(scratch: Path) -> str:
    return refusing(
        gov.assert_task_and_condition_permitted, purpose(), "PT08", "C4"
    )


def case_task_gate(scratch: Path) -> str:
    return refusing(
        gov.assert_task_and_condition_permitted, purpose(), "PT01", "C1"
    )


def case_firewall_matches_record(scratch: Path) -> str:
    outcome = refusing(
        gov.assert_firewall_consistent, purpose(), gov.governed_firewall_from_record()
    )
    return "OK" if outcome == "ACCEPTED" else outcome


def case_confirmatory_area(scratch: Path) -> str:
    return refusing(
        gov.assert_artifact_area_permitted,
        gov.REPO / "experiments" / "v2" / "results" / "probe-run",
        purpose(),
    )


def case_audit_enforcement(scratch: Path) -> str:
    result = run_v2.run(
        run_v2.RunRequest(
            task_id="PT08",
            condition="C1",
            run_purpose=PURPOSE_NAME,
            artifact_root=scratch / "runs",
            generated_at="probe",
            audit_provider=_contaminated_audit,
        )
    )
    if result.refusal_code:
        return f"REFUSED:{result.refusal_code}"
    return "COMPLETED" if result.machine.completed else "INCOMPLETE"


def case_resume_gate(scratch: Path) -> str:
    return refusing(
        ma.build_fresh_launch,
        prompt_path="/tmp/p.md",
        workspace="/tmp/wt",
        require_model=False,
        extra=["--resume", "abc"],
    )


def case_continue_gate(scratch: Path) -> str:
    return refusing(
        ma.build_fresh_launch,
        prompt_path="/tmp/p.md",
        workspace="/tmp/wt",
        require_model=False,
        extra=["--continue"],
    )


def case_session_reuse_gate(scratch: Path) -> str:
    return refusing(
        ma.build_fresh_launch,
        prompt_path="/tmp/p.md",
        workspace="/tmp/wt",
        require_model=False,
        session_id="s-1",
        previous_session_ids=["s-1"],
    )


def case_task_hash_gate(scratch: Path) -> str:
    return _enforce(_prepare(scratch), expected_task_sha="0" * 64)


def case_substrate_hash_gate(scratch: Path) -> str:
    return refusing(gov.assert_substrate_identity, gov.REPO, None, "0" * 64)


def case_allowed_tree_gate(scratch: Path) -> str:
    prepared = _prepare(scratch)
    manifest = copy.deepcopy(prepared.manifest)
    manifest["entries"].append(
        {"path": "docs/v2/ARCHITECTURE_CONTEXT.md", "sha256": "0" * 64, "bytes": 1}
    )
    manifest["entry_count"] = len(manifest["entries"])
    manifest["content_hash"] = wt._content_hash_of_entries(manifest["entries"])
    return _enforce(prepared, manifest=manifest)


def case_bytes_gate(scratch: Path) -> str:
    prepared = _prepare(scratch)
    target = Path(prepared.snapshot_root) / "package.json"
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    return _enforce(prepared)


def case_unexpected_file_gate(scratch: Path) -> str:
    prepared = _prepare(scratch)
    (Path(prepared.snapshot_root) / "apps" / "SMUGGLED.ts").write_text(
        "export const x = 1;\n", encoding="utf-8", newline="\n"
    )
    return _enforce(prepared)


def case_primary_model_gate(scratch: Path) -> str:
    adapter = ma.ModelInvocationAdapter(mode="real", registry_primary_model=None)
    return refusing(adapter.assert_real_invocation_permitted, "claude-sonnet-5")


def case_readback_mismatch_gate(scratch: Path) -> str:
    evidence = [{"type": "system", "subtype": "init", "model": "claude-opus-4-8"}]
    return refusing(ma.validate_model_identity, "claude-sonnet-5", evidence)


def case_readback_missing_gate(scratch: Path) -> str:
    return refusing(ma.validate_model_identity, "claude-sonnet-5", [])


#: The hidden-acceptance gate is probed on a task whose acceptance is still
#: UNVALIDATED. A probe task that is VALIDATED answers True under the real
#: harness AND under a mutation that removes the guard - the probe would agree
#: with itself and the mutation test would pass while proving nothing.
#:
#: This constant has now moved twice, for the same reason each time: PT08 was
#: validated first, then PT01, PT04 and PT07 under SL-V2-ORACLE-01. PT02 is still
#: draft_unvalidated with no runtime authored for it, so it still discriminates.
#: Each move preserves the guard's power; none weakens it. If PT02 is ever
#: validated, this must move again rather than the assertion being relaxed.
UNVALIDATED_PROBE_TASK = "PT02"


def case_hidden_acceptance_gate(scratch: Path) -> str:
    return f"VALIDATED={gov.hidden_acceptance_is_validated(UNVALIDATED_PROBE_TASK)}"


def case_hidden_acceptance_gate_pt08_validated(scratch: Path) -> str:
    """The other direction: PT08's acceptance IS validated, and stays so."""
    return f"VALIDATED={gov.hidden_acceptance_is_validated('PT08')}"


def case_manifest_freeze_gate(scratch: Path) -> str:
    return f"FROZEN={gov.manifest_is_frozen('PT08')}"


def _synthetic_matrix(scratch: Path, name: str, status: str, notes: str) -> Path:
    """A one-row acceptance authority, written into disposable scratch.

    Both public helpers take the matrix path, so a redundancy claim about the
    guard PAIR can be exercised on a row built to exercise it - rather than
    depending on whichever real row happens to hit both guards today.
    """
    scratch.mkdir(parents=True, exist_ok=True)
    path = scratch / name
    path.write_text(
        "task_id,status,notes\n" f"PT08,{status},{notes}\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def case_hidden_acceptance_denylist_guard(scratch: Path) -> str:
    """The DENY half alone: a `validated` status that still says draft_unvalidated.

    The allow-list would pass this row. Only the `draft_unvalidated` substring
    guard rejects it, so mutating the allow-list must not turn it True.
    """
    matrix = _synthetic_matrix(
        scratch, "denylist.csv", "validated", "scaffold is draft_unvalidated"
    )
    return f"VALIDATED={gov.hidden_acceptance_is_validated('PT08', matrix)}"


def case_manifest_freeze_denylist_guard(scratch: Path) -> str:
    """The DENY half alone: an explicit not-frozen lifecycle status.

    The `status == "frozen"` allow-list would already answer False, so mutating
    it to `return True` leaves the `not-frozen` substring guard as the only
    defence - which is exactly the redundancy under test.
    """
    matrix = _synthetic_matrix(
        scratch, "freeze.csv", "candidate-not-frozen", "unfrozen lifecycle"
    )
    return f"FROZEN={gov.manifest_is_frozen('PT08', matrix)}"


def case_record_validation_gate(scratch: Path) -> str:
    directory = art.ArtifactDirectory(scratch / "records", "probe", purpose()).create()
    outcome = refusing(
        art.write_run_record, directory, {"schema_version": "1.0.0", "run_id": "probe"}
    )
    if outcome != "ACCEPTED":
        return outcome
    return "WROTE" if (directory.run_dir / "run_record.json").is_file() else "ACCEPTED"


def case_canonical_repo_gate(scratch: Path) -> str:
    return refusing(gov.assert_not_canonical_repository, gov.REPO, gov.REPO)


def case_scoring_prerequisites_gate(scratch: Path) -> str:
    return refusing(ev.assert_scoring_prerequisites, "PT08")


# --------------------------------------------------------------------------- #
# SL-PT08-02 / SL-PT08-03 and the pre-freeze private sync propagation
# --------------------------------------------------------------------------- #
def case_artifact_schema_firewall(scratch: Path) -> str:
    """Does the schema THIS purpose's artifacts use actually pin the quarantine?"""
    problems = gov.artifact_schema_problems(purpose())
    return "FIREWALL_OK" if not problems else "FIREWALL_PROBLEMS"


def _readiness_item(name: str, scratch: Path):
    report = gov.check_readiness(
        "PT08", "C1", PURPOSE_NAME, context_verdict=None,
    )
    for item in report.prerequisites:
        if item.item == name:
            return item
    return None


def case_canonical_gap_scope(scratch: Path) -> str:
    """N/A for a non-result purpose; BLOCKED for a result-bearing one. Never PASS."""
    item = _readiness_item("canonical_confirmatory_run_manifest_firewall", scratch)
    if item is None:
        return "ABSENT"
    return f"{'NOT_APPLICABLE' if item.status == gov.NOT_APPLICABLE else item.status}:{item.code}"


def case_repetition_decision(scratch: Path) -> str:
    item = _readiness_item("diagnostic_repetition_decision", scratch)
    if item is None:
        return "ABSENT"
    if item.status != gov.PASS:
        return f"BLOCKED:{item.code}"
    return f"PASS:{purpose().repetitions}"


def _sync_probe(root: Path, state: str, sha: str) -> str:
    """Build a disposable private tree carrying one sync record and read it back."""
    record_dir = root / "tasks" / "PT08"
    record_dir.mkdir(parents=True, exist_ok=True)
    (record_dir / "pt08_package_record.json").write_text(
        json.dumps(
            {
                "public_synchronisation_required_before_freeze": {
                    "record_id": "PROBE-SYNC",
                    "state": state,
                    "verified_public_sha": sha,
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    ok, _detail = gov.private_sync_prefreeze_state("PT08", root)
    return "PASS" if ok else "BLOCKED"


def case_private_sync_open(scratch: Path) -> str:
    """An OPEN record must never discharge the pre-freeze blocker."""
    return _sync_probe(
        scratch / "private-open",
        "OPEN - REQUIRED BEFORE FREEZE",
        "8b67c4aa88f9ce5b7195bd8f1527aafec8434ced",
    )


def case_private_sync_wrong_sha(scratch: Path) -> str:
    """A SATISFIED record citing a commit this repository never had must not pass."""
    return _sync_probe(
        scratch / "private-wrong-sha",
        "SATISFIED",
        "0" * 40,
    )


CASES = {
    name[len("case_"):]: fn
    for name, fn in sorted(globals().items())
    if name.startswith("case_") and callable(fn)
}


def main(argv) -> int:
    if len(argv) != 3 or argv[1] not in CASES:
        sys.stderr.write(f"usage: mutation_probe.py <case> <scratch>\ncases: {sorted(CASES)}\n")
        return 2
    scratch = Path(argv[2])
    scratch.mkdir(parents=True, exist_ok=True)
    try:
        token = CASES[argv[1]](scratch)
    except Exception as exc:  # a crashed probe is a distinguishable outcome
        token = f"ERROR:{type(exc).__name__}:{exc}"
    print(f"RESULT={token}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
