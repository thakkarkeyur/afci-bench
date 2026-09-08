"""Mutation tests: every runner guard is proved load-bearing.

Method
------
A guard that is never observed to *matter* is decoration. So for each guard the
package claims, this file makes a **disposable copy** of the harness, edits that
one guard out of the copy, and runs the same probe against the untouched control
copy and the mutated copy in separate subprocesses. The mutation is CAUGHT when
the two observations differ. Neither repository is touched: the mutants live
under pytest's ``tmp_path`` and the real harness is never written to.

The copy step rewrites one line — each module's ``REPO = ...parents[3]`` — so a
harness sitting in a temporary directory still resolves the real repository. That
rewrite is applied identically to the control and to every mutant, and
``test_the_control_copy_behaves_exactly_like_the_real_harness`` proves it changes
no behaviour, so it cannot be doing the work the mutations are meant to reveal.

Defence in depth is measured rather than assumed: where two independent guards
cover one hazard, a single-site mutation is expected to be **survived** (the
redundant guard still refuses) and the two-site mutation is the one that gets
through. Both facts are asserted, so a redundant guard is never mistaken for a
load-bearing one and vice versa.

No model is invoked.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import pytest

REPO = Path(__file__).resolve().parents[4]
HARNESS = REPO / "experiments" / "v2" / "harness"
PROBE = Path(__file__).resolve().parent / "mutation_probe.py"

_REPO_LINE = "REPO = Path(__file__).resolve().parents[3]"

#: A single edit: (module filename, exact source to find, replacement).
Edit = Tuple[str, str, str]


def _copy_harness(dest: Path) -> Path:
    """A disposable copy of the harness, repository-anchored to the real repo."""
    dest.mkdir(parents=True, exist_ok=True)
    for path in sorted(HARNESS.iterdir()):
        if path.is_file() and path.suffix in {".py", ".json"}:
            shutil.copy2(path, dest / path.name)
    fixed = f'REPO = Path(r"{REPO}")'
    for path in sorted(dest.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if _REPO_LINE in text:
            path.write_text(
                text.replace(_REPO_LINE, fixed), encoding="utf-8", newline="\n"
            )
    return dest


def _apply(dest: Path, edits: Sequence[Edit]) -> None:
    for module, old, new in edits:
        path = dest / module
        text = path.read_text(encoding="utf-8")
        count = text.count(old)
        assert count == 1, (
            f"the mutation target is not unique in {module} ({count} matches): "
            f"{old!r}. A non-unique target would mutate the wrong line."
        )
        path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def _probe(harness_dir: Path, case: str, scratch: Path) -> str:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(harness_dir)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        [sys.executable, str(PROBE), case, str(scratch)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        env=env,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("RESULT="):
            return line[len("RESULT="):].strip()
    return f"NO_RESULT(rc={proc.returncode}):{proc.stderr.strip()[:300]}"


@pytest.fixture(scope="module")
def control(tmp_path_factory) -> Path:
    return _copy_harness(tmp_path_factory.mktemp("control") / "harness")


# --------------------------------------------------------------------------- #
# The mutation matrix
#
# Each row is (id, edits, probe case, control observation, mutant observation).
# The twenty mutations the package requires are marked with their number; the
# extra rows cover guards the same machinery makes cheap to prove.
# --------------------------------------------------------------------------- #
MUTATIONS: List[Tuple[str, List[Edit], str, str, str]] = [
    # 1. remove the C1-only restriction
    (
        "01-remove-c1-only-restriction",
        [("run_governance.py",
          "    if condition not in purpose.permitted_conditions:",
          "    if False:")],
        "condition_gate",
        "REFUSED:CONDITION_NOT_PERMITTED_FOR_PURPOSE",
        "ACCEPTED",
    ),
    # 2. permit C4
    (
        "02-permit-c4",
        [("run_governance.py",
          '        permitted_conditions=("C1",),',
          '        permitted_conditions=("C1", "C4"),')],
        "condition_gate",
        "REFUSED:CONDITION_NOT_PERMITTED_FOR_PURPOSE",
        "ACCEPTED",
    ),
    # (extra) remove the PT08-only restriction
    (
        "02b-remove-task-restriction",
        [("run_governance.py",
          "    if task_id not in purpose.permitted_tasks:",
          "    if False:")],
        "task_gate",
        "REFUSED:TASK_NOT_PERMITTED_FOR_PURPOSE",
        "ACCEPTED",
    ),
    # 3. diagnostic -> confirmatory (the quarantine flags)
    (
        "03-diagnostic-to-confirmatory-flags",
        [("run_governance.py",
          "        firewall=tuple((f, False) for f in FIREWALL_FIELDS),",
          "        firewall=tuple((f, True) for f in FIREWALL_FIELDS),")],
        "firewall_matches_record",
        "OK",
        "REFUSED:DIAGNOSTIC_FIREWALL_INCONSISTENT",
    ),
    # 3b. diagnostic -> confirmatory (the purpose itself)
    (
        "03b-diagnostic-to-confirmatory-purpose",
        [("run_governance.py", "        confirmatory=False,", "        confirmatory=True,")],
        "confirmatory_area",
        "REFUSED:DIAGNOSTIC_ARTIFACT_IN_CONFIRMATORY_AREA",
        "ACCEPTED",
    ),
    # 4. skip the context audit
    (
        "04-skip-context-audit",
        [("run_v2.py", '        if verdict != "CLEAN":', "        if False:")],
        "audit_enforcement",
        "REFUSED:CONTEXT_AUDIT_CONTAMINATED",
        "COMPLETED",
    ),
    # 5. treat CONTAMINATED as a warning
    (
        "05-contaminated-as-warning",
        [("run_v2.py",
          '        if verdict != "CLEAN":',
          '        if verdict not in {"CLEAN", "CONTAMINATED"}:')],
        "audit_enforcement",
        "REFUSED:CONTEXT_AUDIT_CONTAMINATED",
        "COMPLETED",
    ),
    # 6. allow --resume (both gates)
    (
        "06-allow-resume",
        [("model_adapter.py", '    "--resume": gov.SESSION_RESUME_REJECTED,\n', ""),
         ("context_audit.py",
          'RESTORATION_FLAGS = {"-c", "--continue", "-r", "--resume", "--from-pr"}',
          'RESTORATION_FLAGS = {"-c", "--continue", "-r", "--from-pr"}')],
        "resume_gate",
        "REFUSED:SESSION_RESUME_REJECTED",
        "ACCEPTED",
    ),
    # 7. allow --continue (both gates)
    (
        "07-allow-continue",
        [("model_adapter.py", '    "--continue": gov.SESSION_CONTINUE_REJECTED,\n', ""),
         ("context_audit.py",
          'RESTORATION_FLAGS = {"-c", "--continue", "-r", "--resume", "--from-pr"}',
          'RESTORATION_FLAGS = {"-c", "-r", "--resume", "--from-pr"}')],
        "continue_gate",
        "REFUSED:SESSION_CONTINUE_REJECTED",
        "ACCEPTED",
    ),
    # 7b. allow session-id reuse (both gates)
    (
        "07b-allow-session-id-reuse",
        [("model_adapter.py",
          "    if session_id is not None and session_id in previous:",
          "    if False:"),
         ("context_audit.py",
          'SESSION_ID_FLAGS = {"--session-id"}',
          "SESSION_ID_FLAGS = set()")],
        "session_reuse_gate",
        "REFUSED:SESSION_ID_REUSED",
        "ACCEPTED",
    ),
    # 8. skip task-hash verification
    (
        "08-skip-task-hash-verification",
        [("run_worktree.py", "    if actual != expected_sha:", "    if False:")],
        "task_hash_gate",
        "REFUSED:TASK_SHA_MISMATCH",
        "ACCEPTED",
    ),
    # 9. skip substrate-hash verification
    (
        "09-skip-substrate-hash-verification",
        [("run_governance.py",
          "    if content_hash != expected_hash or entry_count != expected_entries:",
          "    if False:")],
        "substrate_hash_gate",
        "REFUSED:SUBSTRATE_IDENTITY_MISMATCH",
        "ACCEPTED",
    ),
    # 10. remove allowed-tree enforcement
    (
        "10-remove-allowed-tree-enforcement",
        [("run_worktree.py", "    if offenders:", "    if False:")],
        "allowed_tree_gate",
        "REFUSED:WORKTREE_PATH_NOT_ALLOWLISTED",
        "REFUSED:PREPARED_WORKTREE_DIRTY",
    ),
    # 11. remove prepared-worktree byte verification (both halves)
    (
        "11-remove-prepared-bytes-verification",
        [("run_worktree.py", "    if drifted:", "    if False:"),
         ("run_worktree.py",
          '    recomputed = _content_hash_of_entries(on_disk)\n'
          '    if recomputed != manifest["content_hash"]:',
          "    recomputed = _content_hash_of_entries(on_disk)\n    if False:")],
        "bytes_gate",
        "REFUSED:PREPARED_WORKTREE_DIRTY",
        "ACCEPTED",
    ),
    # 12. permit primary_model null in real mode
    (
        "12-permit-primary-model-null",
        [("model_adapter.py",
          "        if self.registry_primary_model is None:",
          "        if False:")],
        "primary_model_gate",
        "REFUSED:PRIMARY_MODEL_NOT_SELECTED",
        "ACCEPTED",
    ),
    # 13. ignore a model-id mismatch
    (
        "13-ignore-model-id-mismatch",
        [("model_adapter.py",
          "    elif requested is None or distinct[0] != requested:",
          "    elif False:")],
        "readback_mismatch_gate",
        "REFUSED:MODEL_READBACK_MISMATCH",
        "ACCEPTED",
    ),
    # 13b. disable readback enforcement entirely
    (
        "13b-disable-readback-enforcement",
        [("model_adapter.py",
          "    if strict and not result.valid:",
          "    if False:")],
        "readback_mismatch_gate",
        "REFUSED:MODEL_READBACK_MISMATCH",
        "ACCEPTED",
    ),
    # 14. accept a missing model readback
    (
        "14-accept-missing-model-readback",
        [("model_adapter.py",
          "            status=gov.MODEL_READBACK_MISSING,",
          '            status="VALIDATED",')],
        "readback_missing_gate",
        "REFUSED:MODEL_READBACK_MISSING",
        "ACCEPTED",
    ),
    # 15. permit unvalidated hidden acceptance (both halves)
    (
        "15-permit-hidden-acceptance-unvalidated",
        [("run_governance.py",
          '    if "draft_unvalidated" in blob:',
          "    if False:"),
         ("run_governance.py",
          '    return row.get("status", "").strip().lower() in {"validated", "frozen"}',
          "    return True")],
        "hidden_acceptance_gate",
        "VALIDATED=False",
        "VALIDATED=True",
    ),
    # 16. permit an unfrozen manifest (both halves)
    (
        "16-permit-unfrozen-manifest",
        [("run_governance.py",
          '    if "not-frozen" in status or "not_frozen" in status:',
          "    if False:"),
         ("run_governance.py", '    return status == "frozen"', "    return True")],
        "manifest_freeze_gate",
        "FROZEN=False",
        "FROZEN=True",
    ),
    # 17. omit the run purpose from artifacts
    (
        "17-omit-run-purpose-from-artifacts",
        [("run_artifacts.py",
          '    validate_run_record(record)\n    return directory.write_json("run_record.json", record)',
          '    return directory.write_json("run_record.json", record)')],
        "record_validation_gate",
        "REFUSED:PREPARED_MANIFEST_INVALID",
        "WROTE",
    ),
    # 18. permit direct execution in the canonical repository (both halves)
    (
        "18-permit-canonical-repo-execution",
        [("run_governance.py",
          "    if wt == canonical or canonical in wt.parents or wt in canonical.parents:",
          "    if False:"),
         ("run_governance.py", '    if (wt / ".git").exists():', "    if False:")],
        "canonical_repo_gate",
        "REFUSED:CANONICAL_REPOSITORY_EXECUTION_REFUSED",
        "ACCEPTED",
    ),
    # 19. allow an unexpected model-visible file
    (
        "19-allow-unexpected-model-visible-file",
        [("run_worktree.py", "    if extra:", "    if False:")],
        "unexpected_file_gate",
        "REFUSED:UNEXPECTED_MODEL_VISIBLE_FILE",
        "REFUSED:PREPARED_WORKTREE_DIRTY",
    ),
    # 20. allow a diagnostic artifact into the confirmatory dataset area
    (
        "20-allow-diagnostic-artifact-into-confirmatory-area",
        [("run_governance.py",
          "        if resolved == area_resolved or area_resolved in resolved.parents:",
          "        if False:")],
        "confirmatory_area",
        "REFUSED:DIAGNOSTIC_ARTIFACT_IN_CONFIRMATORY_AREA",
        "ACCEPTED",
    ),
]

#: Single-site mutations of hazards two independent guards cover. These must be
#: SURVIVED: the surviving guard keeps refusing, which is what defence in depth
#: means. Asserted so a redundant guard is never reported as load-bearing.
REDUNDANT_MUTATIONS: List[Tuple[str, List[Edit], str, str]] = [
    (
        "R1-resume-runner-gate-only",
        [("model_adapter.py", '    "--resume": gov.SESSION_RESUME_REJECTED,\n', "")],
        "resume_gate",
        "REFUSED:SESSION_RESUME_REJECTED",
    ),
    (
        "R2-resume-frozen-guard-only",
        [("context_audit.py",
          'RESTORATION_FLAGS = {"-c", "--continue", "-r", "--resume", "--from-pr"}',
          'RESTORATION_FLAGS = {"-c", "--continue", "-r", "--from-pr"}')],
        "resume_gate",
        "REFUSED:SESSION_RESUME_REJECTED",
    ),
    (
        "R3-bytes-drift-check-only",
        [("run_worktree.py", "    if drifted:", "    if False:")],
        "bytes_gate",
        "REFUSED:PREPARED_WORKTREE_DIRTY",
    ),
    (
        "R4-canonical-path-check-only",
        [("run_governance.py",
          "    if wt == canonical or canonical in wt.parents or wt in canonical.parents:",
          "    if False:")],
        "canonical_repo_gate",
        "REFUSED:CANONICAL_REPOSITORY_EXECUTION_REFUSED",
    ),
    (
        "R5-hidden-acceptance-status-check-only",
        [("run_governance.py",
          '    return row.get("status", "").strip().lower() in {"validated", "frozen"}',
          "    return True")],
        "hidden_acceptance_gate",
        "VALIDATED=False",
    ),
    (
        "R6-manifest-freeze-status-check-only",
        [("run_governance.py", '    return status == "frozen"', "    return True")],
        "manifest_freeze_gate",
        "FROZEN=False",
    ),
]


# --------------------------------------------------------------------------- #
# The control copy must behave exactly like the shipped harness
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "case,expected",
    sorted({(m[2], m[3]) for m in MUTATIONS}),
)
def test_the_control_copy_behaves_exactly_like_the_real_harness(
    control, tmp_path, case, expected
):
    """The copy + repo-anchor rewrite changes no behaviour."""
    assert _probe(control, case, tmp_path / "scratch") == expected


def test_the_real_harness_gives_the_same_observation_as_the_control(control, tmp_path):
    """Spot-check the shipped modules directly, not only the copy."""
    for case in ("condition_gate", "canonical_repo_gate", "manifest_freeze_gate"):
        assert _probe(HARNESS, case, tmp_path / f"real-{case}") == _probe(
            control, case, tmp_path / f"ctl-{case}"
        ), case


# --------------------------------------------------------------------------- #
# Every mutation must be CAUGHT
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "mutation_id,edits,case,control_expected,mutant_expected",
    MUTATIONS,
    ids=[m[0] for m in MUTATIONS],
)
def test_every_mutation_is_caught(
    control, tmp_path, mutation_id, edits, case, control_expected, mutant_expected
):
    mutant = _copy_harness(tmp_path / "mutant" / "harness")
    _apply(mutant, edits)

    observed_control = _probe(control, case, tmp_path / "scratch-control")
    observed_mutant = _probe(mutant, case, tmp_path / "scratch-mutant")

    assert observed_control == control_expected, (
        f"{mutation_id}: the control observation moved; the probe is unsound"
    )
    assert observed_mutant == mutant_expected, (
        f"{mutation_id}: the mutant behaved unexpectedly ({observed_mutant!r})"
    )
    assert observed_mutant != observed_control, (
        f"{mutation_id}: MUTATION SURVIVED — removing this guard changed nothing, "
        f"so it is not load-bearing (both observations {observed_control!r})"
    )
    shutil.rmtree(tmp_path / "mutant", ignore_errors=True)


@pytest.mark.parametrize(
    "mutation_id,edits,case,expected",
    REDUNDANT_MUTATIONS,
    ids=[m[0] for m in REDUNDANT_MUTATIONS],
)
def test_a_single_site_mutation_is_survived_by_the_redundant_guard(
    control, tmp_path, mutation_id, edits, case, expected
):
    mutant = _copy_harness(tmp_path / "redundant" / "harness")
    _apply(mutant, edits)
    assert _probe(mutant, case, tmp_path / "scratch") == expected, (
        f"{mutation_id}: the hazard was NOT covered by a second guard; the "
        "defence-in-depth claim is false"
    )
    shutil.rmtree(tmp_path / "redundant", ignore_errors=True)


# --------------------------------------------------------------------------- #
# Coverage of the required matrix
# --------------------------------------------------------------------------- #
def test_the_matrix_covers_every_required_mutation():
    required = {
        "remove-c1-only-restriction", "permit-c4",
        "diagnostic-to-confirmatory", "skip-context-audit",
        "contaminated-as-warning", "allow-resume", "allow-continue",
        "skip-task-hash-verification", "skip-substrate-hash-verification",
        "remove-allowed-tree-enforcement", "remove-prepared-bytes-verification",
        "permit-primary-model-null", "ignore-model-id-mismatch",
        "accept-missing-model-readback", "permit-hidden-acceptance-unvalidated",
        "permit-unfrozen-manifest", "omit-run-purpose-from-artifacts",
        "permit-canonical-repo-execution", "allow-unexpected-model-visible-file",
        "allow-diagnostic-artifact-into-confirmatory-area",
    }
    ids = " ".join(m[0] for m in MUTATIONS)
    missing = [name for name in sorted(required) if name not in ids]
    assert missing == [], missing
    assert len(MUTATIONS) >= 20


def test_no_mutant_or_probe_touched_either_repository():
    public = subprocess.run(
        ["git", "-C", str(REPO), "status", "--porcelain"],
        capture_output=True, text=True,
    ).stdout
    dirty = [
        line for line in public.splitlines()
        if line.strip() and "experiments/v2/harness" not in line
    ]
    assert dirty == [], f"the mutation run dirtied unrelated public paths: {dirty}"
    private = REPO.parent / "afci-bench-evaluator-private"
    if (private / ".git").is_dir():
        assert subprocess.run(
            ["git", "-C", str(private), "status", "--porcelain"],
            capture_output=True, text=True,
        ).stdout.strip() == "", "the private repository was modified"
