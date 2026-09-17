#!/usr/bin/env python3
"""Deterministic run-artifact layout and the run record's firewall.

Layout, under ``<artifact_root>/<run_id>/``::

    run_record.json          the top-level record (carries the quarantine flags)
    readiness.json           the prerequisite report
    context_audit.json       context_audit.py's own artifact, unmodified
    launch_manifest.json     ART-LAUNCH: the exact argv, no free-text values
    prepared_manifest.json   prepare_model_worktree.py's snapshot manifest
    worktree/                the prepared model-visible worktree
    worktree_post_run/       the captured model-modified worktree (real runs)
    run_output.jsonl         ART-RUNLOG: runtime output, when one exists

Three properties are load-bearing:

**The purpose is mandatory.** :func:`build_run_record` derives the five
eligibility flags from the governed purpose and refuses to write a record that
lacks a purpose or carries flags disagreeing with it. A caller cannot promote a
diagnostic artifact by handing in different flags.

**Non-confirmatory artifacts stay out of the confirmatory areas.**
``experiments/v2/results/`` and ``experiments/v2/analysis/`` are refused as
artifact roots for a non-confirmatory purpose; the default root is a scratch
directory outside the repository.

**Records are deterministic.** ``run_id`` is derived from the run's own identity
(purpose, task, condition, task hash, substrate hash, mode, **repetition index**)
and timestamps are caller-supplied, matching ``context_audit.py``'s
``--generated-at`` convention. Two identical runs produce identical records, and
two *repetitions* of one run identity produce different ones (``SL-RUNID-01``).

A run record is not a result. The schema pins ``is_result: false`` and
``scored: false``, so no record this runner can currently emit is expressible as
a scored observation.

No model is invoked and no benchmark task is executed.
"""
from __future__ import annotations

import hashlib
import json
import platform
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

#: The only names under a run directory a run may rebuild. ``worktree`` is the
#: prepared model-visible snapshot, which is derived and reproducible.
#: ``worktree_post_run`` is deliberately ABSENT: it is the captured evidence.
REBUILDABLE_TEMPORARY_NAMES: Sequence[str] = ("worktree",)

import architecture_evaluation as ae
import context_audit as ca
import functional_evaluation as fe
import reset_budget as rb
import run_governance as gov

SCHEMA_PATH = Path(__file__).resolve().parent / "run_record.schema.json"
RECORD_SCHEMA_VERSION = "1.0.0"

#: The governing documents whose identities are recorded as protocol versions.
PROTOCOL_DOCS: Dict[str, str] = {
    "condition_spec": "docs/v2/CONDITIONS.md",
    "oracle_spec": "docs/v2/ORACLE_VALIDATION_REQUIREMENTS.md",
    "acceptance_spec": "docs/v2/HIDDEN_EVALUATOR_BOUNDARY.md",
    "reset_protocol": "docs/v2/RESET_PROTOCOL.md",
    "model_execution_config": "docs/v2/MODEL_EXECUTION_CONTROLS.md",
    "guard_spec": "docs/v2/ARCHITECTURE_RULE_CATALOG.yml",
    "worktree_policy": "docs/v2/MODEL_VISIBLE_WORKTREE_POLICY.md",
    "diagnostic_decision": "docs/v2/PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def protocol_versions(repo: Path = gov.REPO) -> Dict[str, str]:
    """Identify each governing document by path and content hash.

    A protocol "version" that is a hand-written number drifts silently. A
    content hash cannot: if the governing text changes, the recorded version
    changes with it.
    """
    versions: Dict[str, str] = {}
    for key, rel in PROTOCOL_DOCS.items():
        path = Path(repo) / rel
        if not path.is_file():
            raise gov.RunnerRefusal(
                gov.GOVERNANCE_RECORD_UNREADABLE,
                f"the {key} protocol document is missing: {rel}",
            )
        versions[key] = f"{rel}@sha256:{sha256_file(path)[:16]}"
    return versions


def governed_toolchain(path: Path = gov.MODEL_REGISTRY) -> Dict[str, Optional[str]]:
    """The pinned CLI / SDK versions, read from the registry (never guessed)."""
    text = Path(path).read_text(encoding="utf-8")

    def pin(key: str) -> Optional[str]:
        m = re.search(rf"^\s*{key}:\s*\"?([^\"#\s]+)\"?", text, re.MULTILINE)
        return m.group(1) if m else None

    return {
        "claude_code_cli_version": pin("claude_code_cli_version"),
        "claude_agent_sdk_version": pin("claude_agent_sdk_version"),
    }


#: The repetition index a run carries when the caller declares none.
#:
#: Chosen as 1 rather than 0 so the recorded index reads as "repetition R1" in
#: the same vocabulary the protocol uses (R1/R2/R3), and so a single run's
#: record is interpretable without knowing whether the caller passed the flag.
DEFAULT_REPETITION = 1

#: The inclusive ceiling on a declared repetition index. A run beyond it is far
#: likelier to be a typo or a loop variable than a governed repetition, and the
#: identity of an artifact is not the place to be permissive.
MAX_REPETITION = 999


def normalise_repetition(repetition: Optional[int]) -> int:
    """Validate a declared repetition index, or supply the governed default.

    Fails closed: a non-integer, a zero, a negative index or one beyond
    :data:`MAX_REPETITION` is refused rather than coerced, because an artifact
    whose identity was silently repaired is an artifact nobody can reconcile
    against the protocol that asked for it.
    """
    if repetition is None:
        return DEFAULT_REPETITION
    if isinstance(repetition, bool) or not isinstance(repetition, int):
        raise gov.RunnerRefusal(
            gov.RUN_REPETITION_INVALID,
            f"the repetition index must be an integer, got {repetition!r}",
        )
    if repetition < 1 or repetition > MAX_REPETITION:
        raise gov.RunnerRefusal(
            gov.RUN_REPETITION_INVALID,
            f"the repetition index must be between 1 and {MAX_REPETITION}, "
            f"got {repetition}",
        )
    return repetition


#: The inclusive ceiling on a declared execution attempt. An execution attempt is
#: a *restart of a whole protocol*, not a retry of a row; a study that claimed a
#: hundred of them would be describing something other than an execution.
MAX_EXECUTION_ATTEMPT = 99


def normalise_execution_attempt(execution_attempt: Optional[int]) -> Optional[int]:
    """Validate a declared execution attempt, or report that none was declared.

    ``None`` is returned unchanged and means *this purpose declares no execution
    attempt*, which is every purpose that existed before ``SL-V2-EFF-RESTART-01``.
    It is deliberately NOT defaulted to 1: defaulting would silently relabel every
    historical artifact as "attempt 1 of something", and would change the ids
    those artifacts were written with.

    Everything else fails closed, for the same reason
    :func:`normalise_repetition` does.
    """
    if execution_attempt is None:
        return None
    if isinstance(execution_attempt, bool) or not isinstance(execution_attempt, int):
        raise gov.RunnerRefusal(
            gov.EXECUTION_ATTEMPT_INVALID,
            f"the execution attempt must be an integer, got {execution_attempt!r}",
        )
    if execution_attempt < 1 or execution_attempt > MAX_EXECUTION_ATTEMPT:
        raise gov.RunnerRefusal(
            gov.EXECUTION_ATTEMPT_INVALID,
            f"the execution attempt must be between 1 and {MAX_EXECUTION_ATTEMPT}, "
            f"got {execution_attempt}",
        )
    return execution_attempt


#: The identity algorithm a run id was minted under. Recorded rather than
#: inferred, so a reader never has to guess which fields a given id hashed.
IDENTITY_ALGORITHM_LEGACY = 1
IDENTITY_ALGORITHM_RESET_AWARE = 2


def derive_run_id(
    *, purpose: str, task_id: str, condition: str, task_sha: str,
    substrate_hash: str, mode: str, repetition: Optional[int] = None,
    reset_state: Optional[str] = None,
    execution_attempt: Optional[int] = None,
) -> str:
    """A deterministic, collision-resistant run id carrying its own provenance.

    **Repetition identity (`SL-RUNID-01`).** The seed carries the repetition index as
    well as the run's content identity. Before this, every repetition of one
    (purpose, task, condition, task hash, substrate hash, mode) hashed to the
    SAME id, so `R1`/`R2`/`R3` of the `PT08` diagnostic collided and stayed
    separable only because each was handed its own ``--artifact-root``. A
    multi-repetition run writing into one root would have overwritten itself.

    **Reset identity (`SL-V2-EFF-ABORT-01`).** The seed now also carries the reset
    state, when the run declares one. It did not, and the `AFCI_EFFICIENCY_PILOT`
    crosses every cell with ``NON_RESET`` and ``RESET`` — so the two arms of one
    (task, condition, repetition) derived one id and one artifact directory. The
    frozen 36-row schedule therefore held **18 collisions**, and Attempt 1 of the
    pilot hit the first one whose partner had already executed: scientific
    sequence 9 landed on scientific sequence 6's completed observation.

    The reset state is taken as its canonical governed value and validated
    against :data:`reset_budget.RESET_STATES`. It is never inferred from a path,
    a prompt, a directory name or a lowercase spelling, because a reset state
    read out of a filename is a reset state that can be wrong without anything
    failing.

    **Attempt identity (`SL-V2-EFF-RESTART-01`).** An execution attempt, when
    declared, joins the seed too. It is INFRASTRUCTURE PROVENANCE and nothing
    else: it distinguishes a replacement execution's artifacts from an aborted
    one's so the replacement cannot land on them, and it touches no task, no
    condition, no budget, no metric and no threshold.

    Determinism is unchanged on every axis: the same row, in the same attempt,
    still produces the same id. The repetition, the reset state and the attempt
    all appear in the readable prefix, so rows are distinguishable by eye.

    **Backward compatibility.** Both new parameters default to ``None``, and when
    both are ``None`` the seed and the readable prefix are byte-identical to the
    `SL-RUNID-01` form. A purpose that declares neither — `PT08_DIFFICULTY_DIAGNOSTIC`,
    `INSTRUMENT_QUALIFICATION_DIAGNOSTIC`, and Attempt 1's own artifacts — derives
    exactly the ids it always did. Nothing on disk is renamed or re-derived.
    """
    index = normalise_repetition(repetition)
    attempt = normalise_execution_attempt(execution_attempt)

    seed_parts = [
        purpose, task_id, condition, task_sha, substrate_hash, mode, f"r{index}",
    ]
    slug_parts = [
        purpose.lower().replace("_", "-"), task_id.lower(), condition.lower(),
        mode, f"r{index}",
    ]
    if reset_state is not None:
        state = rb.assert_reset_state(reset_state)
        # Prefixed tokens, so a seed component can never be confused with the
        # value of a different field.
        seed_parts.append(f"reset:{state}")
        slug_parts.append(state.lower().replace("_", "-"))
    if attempt is not None:
        seed_parts.append(f"attempt:{attempt}")
        slug_parts.append(f"a{attempt}")

    digest = sha256_bytes("|".join(seed_parts).encode("utf-8"))[:12]
    return "-".join([*slug_parts, digest])


def run_identity_block(
    *, purpose: str, task_id: str, condition: str, task_sha: str,
    substrate_hash: str, mode: str, repetition: Optional[int] = None,
    reset_state: Optional[str] = None,
    execution_attempt: Optional[int] = None,
) -> Optional[Dict[str, object]]:
    """The record's account of HOW its run id was derived, or ``None``.

    ``None`` — and therefore no block at all — for a run that declares neither a
    reset state nor an execution attempt, so a record written by a purpose that
    predates reset-aware identity is byte-identical to the one it produced
    before this field existed.

    It exists because a reader holding a record should be able to re-derive its
    ``run_id`` without knowing which algorithm minted it. The fields are listed,
    not just their values, so an id whose derivation later changes again is
    distinguishable from one that did not.
    """
    if reset_state is None and execution_attempt is None:
        return None
    fields = [
        "run_purpose", "task_id", "condition", "task_sha256",
        "substrate_content_hash", "mode", "repetition",
    ]
    if reset_state is not None:
        fields.append("reset_state")
    if execution_attempt is not None:
        fields.append("execution_attempt")
    return {
        "algorithm_version": IDENTITY_ALGORITHM_RESET_AWARE,
        "authority": "SL-V2-EFF-ABORT-01",
        "fields": fields,
        "repetition": normalise_repetition(repetition),
        "reset_state": (
            rb.assert_reset_state(reset_state) if reset_state is not None else None
        ),
        "execution_attempt": normalise_execution_attempt(execution_attempt),
        "run_id": derive_run_id(
            purpose=purpose, task_id=task_id, condition=condition,
            task_sha=task_sha, substrate_hash=substrate_hash, mode=mode,
            repetition=repetition, reset_state=reset_state,
            execution_attempt=execution_attempt,
        ),
    }


#: The file that says who a governed artifact directory belongs to. It is
#: written FIRST, before the prompt, before the readiness report and before any
#: manifest, so a directory that exists at all is already attributable.
OWNERSHIP_MARKER = "run_identity.json"

#: The artifacts whose presence means "another observation lives here". Named
#: explicitly rather than inferred from "the directory is not empty", so the
#: refusal message can say WHICH governed material it found — and so a stray
#: editor swapfile is not reported as a scientific observation.
GOVERNED_OBSERVATION_ARTIFACTS: tuple = (
    "run_record.json",
    "readiness.json",
    "context_audit.json",
    "phase_a_context_audit.json",
    "phase_b_context_audit.json",
    "prepared_manifest.json",
    "launch_manifest.json",
    "prompt_manifest.json",
    "functional_evaluation.json",
    "functional_evaluation_result.json",
    "architecture_evaluation.json",
    "architecture_evaluation_result.json",
    "runtime_evidence.jsonl",
    "phase_a_runtime_evidence.jsonl",
    "phase_b_runtime_evidence.jsonl",
    "prompts",
    "worktree_post_run",
)

OWNERSHIP_NEW = "NEW"
OWNERSHIP_EMPTY = "EMPTY"
OWNERSHIP_OWNED = "OWNED"


class ArtifactOwnership:
    """The proof that a destination belongs to the observation about to use it."""

    def __init__(
        self, status: str, run_dir: Path, material: Sequence[str], detail: str
    ) -> None:
        self.status = status
        self.run_dir = Path(run_dir)
        self.material = tuple(material)
        self.detail = detail

    @property
    def is_owned(self) -> bool:
        """True when the destination belongs to the run holding this proof.

        Every status :func:`assert_destination_ownable` can RETURN satisfies it —
        that function refuses rather than returning for everything else — so this
        reads as a tautology and is deliberately written anyway. It is the
        property ``remove_temporary`` depends on, and a later status added to the
        enumeration without being added here would fail closed instead of
        silently acquiring permission to delete.
        """
        return self.status in {OWNERSHIP_NEW, OWNERSHIP_EMPTY, OWNERSHIP_OWNED}

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "run_dir": str(self.run_dir),
            "pre_existing_observation_material": list(self.material),
            "detail": self.detail,
        }


def assert_destination_ownable(
    run_dir: Path,
    *,
    identity: Dict[str, object],
    spends_an_observation: bool,
) -> ArtifactOwnership:
    """Prove the destination is this observation's to write, or refuse.

    ``SL-V2-EFF-ABORT-01``, Part G. Called BEFORE the prompt is composed, before
    the readiness report is written and before any model process could be
    created, because every one of those steps writes into the destination and
    each of them is a step Attempt 1 took on the way to overwriting scientific
    sequence 6.

    Four things refuse, and all four say the same thing — *this directory cannot
    be proved new for this observation*:

    * it exists and is not a directory;
    * it exists, is non-empty, and carries no ownership marker, so its contents
      cannot be attributed to anyone. Every Attempt-1 directory is in exactly
      this state, which is what makes the replacement execution unable to touch
      them even if an operator pointed it at the wrong root;
    * it carries a marker naming a DIFFERENT identity;
    * it carries this run's own marker AND this run spends a real observation.
      A paid observation is spent once: re-entering its directory would mean
      either overwriting evidence or measuring a run that had already happened.

    A ``dry-run`` re-entering its own directory is permitted and is the one case
    that returns ``OWNED``. It spends nothing, produces no observation, and is
    how ``--check-readiness --live-context-audit`` re-probes an environment.
    """
    run_dir = Path(run_dir)
    if not run_dir.exists():
        return ArtifactOwnership(
            OWNERSHIP_NEW, run_dir, (), "the destination did not exist"
        )
    if not run_dir.is_dir():
        raise gov.RunnerRefusal(
            gov.ARTIFACT_IDENTITY_COLLISION_PREINVOCATION,
            f"the governed artifact destination {run_dir} exists and is not a "
            "directory; nothing is written and no model is invoked",
        )

    entries = sorted(p.name for p in run_dir.iterdir())
    material = tuple(n for n in entries if n in GOVERNED_OBSERVATION_ARTIFACTS)
    if not entries:
        return ArtifactOwnership(
            OWNERSHIP_EMPTY, run_dir, (), "the destination existed and was empty"
        )

    marker = run_dir / OWNERSHIP_MARKER
    if not marker.is_file():
        raise gov.RunnerRefusal(
            gov.ARTIFACT_IDENTITY_COLLISION_PREINVOCATION,
            f"the governed artifact destination {run_dir} already exists and "
            f"carries no {OWNERSHIP_MARKER}, so its contents cannot be attributed "
            f"to this observation. It holds {list(material) or entries[:8]}. "
            "Nothing is written, nothing is deleted and no model is invoked",
        )
    try:
        recorded = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise gov.RunnerRefusal(
            gov.ARTIFACT_IDENTITY_COLLISION_PREINVOCATION,
            f"the ownership marker at {marker} is unreadable ({exc}); an "
            "unattributable destination is never assumed to be free",
        ) from exc
    if recorded != identity:
        raise gov.RunnerRefusal(
            gov.ARTIFACT_IDENTITY_COLLISION_PREINVOCATION,
            f"the governed artifact destination {run_dir} belongs to run "
            f"{recorded.get('run_id')!r} and this run is "
            f"{identity.get('run_id')!r}. Two observations deriving one "
            "directory is the defect SL-V2-EFF-ABORT-01 was raised for; nothing "
            "is written, nothing is deleted and no model is invoked",
        )
    if spends_an_observation and material:
        raise gov.RunnerRefusal(
            gov.ARTIFACT_IDENTITY_COLLISION_PREINVOCATION,
            f"the governed artifact destination {run_dir} already holds this "
            f"observation's material {list(material)}. A real observation is "
            "spent once and is never re-entered; re-running it would overwrite "
            "the evidence of the run that already happened",
        )
    return ArtifactOwnership(
        OWNERSHIP_OWNED,
        run_dir,
        material,
        f"the destination carries this run's own {OWNERSHIP_MARKER}",
    )


class ArtifactDirectory:
    """The on-disk home of one run's artifacts, created fail-closed."""

    def __init__(
        self,
        root: Path,
        run_id: str,
        purpose: gov.RunPurpose,
        identity: Optional[Dict[str, object]] = None,
        spends_an_observation: bool = False,
    ) -> None:
        self.purpose = purpose
        self.root = gov.assert_artifact_area_permitted(Path(root), purpose)
        self.run_dir = self.root / run_id
        self.run_id = run_id
        #: What this directory's contents belong to. Defaulted to the narrowest
        #: truthful statement — the run id and the purpose — so a caller that
        #: supplies none is still guarded rather than exempt.
        self.identity: Dict[str, object] = (
            dict(identity)
            if identity is not None
            else {"run_id": run_id, "run_purpose": purpose.name}
        )
        self.spends_an_observation = spends_an_observation
        self.ownership: Optional[ArtifactOwnership] = None

    def create(self) -> "ArtifactDirectory":
        """Prove ownership, then create. The order is the control.

        The check happens before ``mkdir``, so a refusal leaves the destination
        exactly as it was found: no directory created, no marker written, and —
        because the caller's ``directory`` binding is never assigned — no
        refusal record written over the run that owns it.
        """
        self.ownership = assert_destination_ownable(
            self.run_dir,
            identity=self.identity,
            spends_an_observation=self.spends_an_observation,
        )
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / OWNERSHIP_MARKER).write_text(
            json.dumps(self.identity, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return self

    # -- destructive-reuse prevention (SL-V2-EFF-ABORT-01, Part H) --------- #
    def remove_temporary(self, path: Path, *, ignore_errors: bool = False) -> None:
        """Recursively delete this run's OWN fresh temporary state, or refuse.

        Attempt 1's ``PREPARE_WORKTREE`` deleted whatever stood at
        ``<run_dir>/worktree`` because the next run derived the same path. That
        is right for a directory this run built moments ago and catastrophic for
        one a previous observation left behind, and nothing in the call
        distinguished the two.

        Three conditions, all required:

        * the path is strictly inside this run's own directory, so a delete can
          never reach outside it;
        * it is one of :data:`REBUILDABLE_TEMPORARY_NAMES`. ``worktree_post_run``
          is deliberately absent from that tuple: the captured worktree is
          evidence, and evidence is never cleared to make room for a rerun;
        * the destination was PROVED ownable by :meth:`create`. That is what
          separates this run's own state from a previous observation's, and it
          is why the proof is required rather than assumed — a directory holding
          another identity, or holding governed material under a real run, never
          gets as far as being opened, so nothing here can reclaim it.
        """
        target = Path(path)
        try:
            inside = target.resolve().is_relative_to(self.run_dir.resolve())
        except OSError:  # pragma: no cover - unresolvable path
            inside = False
        if not inside or target.resolve() == self.run_dir.resolve():
            raise gov.RunnerRefusal(
                gov.ARTIFACT_DESTRUCTIVE_REUSE_REFUSED,
                f"{target} is not inside this run's own artifact directory "
                f"{self.run_dir}; a recursive delete never reaches outside it",
            )
        if target.name not in REBUILDABLE_TEMPORARY_NAMES:
            raise gov.RunnerRefusal(
                gov.ARTIFACT_DESTRUCTIVE_REUSE_REFUSED,
                f"{target.name!r} is not rebuildable temporary state; only "
                f"{list(REBUILDABLE_TEMPORARY_NAMES)} may be recreated, and "
                "governed evidence is never deleted to make room for a rerun",
            )
        if self.ownership is None or not self.ownership.is_owned:
            raise gov.RunnerRefusal(
                gov.ARTIFACT_DESTRUCTIVE_REUSE_REFUSED,
                f"{self.run_dir} was never proved ownable by this run, so "
                f"{target} cannot be shown to be this run's own temporary state. "
                "A recursive delete is refused rather than attempted",
            )
        if target.exists():
            shutil.rmtree(target, ignore_errors=ignore_errors)

    # -- paths ------------------------------------------------------------ #
    @property
    def worktree(self) -> Path:
        return self.run_dir / "worktree"

    @property
    def worktree_post_run(self) -> Path:
        return self.run_dir / "worktree_post_run"

    def path(self, name: str) -> Path:
        return self.run_dir / name

    # -- writing ---------------------------------------------------------- #
    def write_json(self, name: str, payload) -> Path:
        target = self.path(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return target

    def relative(self, path: Optional[Path]) -> Optional[str]:
        if path is None:
            return None
        return str(Path(path))


def _validated_functional_evaluation(block: Dict[str, object]) -> Dict[str, object]:
    """Re-derive ``functional_valid`` at record-assembly time, and refuse a lie.

    ``SL-V2-EFF-FUNC-01`` says the verdict is DERIVED. That has to be true of the
    record as well as of the module that produced it, or the derivation would be
    a convention rather than a property: a caller could assemble a block by hand,
    set the flag, and the record would carry it. The counts are the only input;
    a block whose flag disagrees with them is refused rather than corrected,
    because silently rewriting someone's claimed verdict is worse than failing.
    """
    missing = [f for f in fe.REQUIRED_COUNTS if f not in block]
    if missing:
        raise gov.RunnerRefusal(
            fe.FUNCTIONAL_EVALUATOR_MALFORMED_RESULT,
            f"the functional evaluation block omits {missing}; it is assembled "
            "from a scorer result, never by hand",
        )
    derived = fe.derive_functional_valid(block) and bool(block.get("executed"))
    if bool(block.get("functional_valid")) != derived:
        raise gov.RunnerRefusal(
            fe.FUNCTIONAL_VALID_NOT_DERIVABLE,
            f"the functional evaluation block claims functional_valid="
            f"{block.get('functional_valid')!r} while its own counts derive "
            f"{derived!r}; the verdict is not a supplied value",
        )
    return dict(block)


def _validated_architecture_evaluation(block: Dict[str, object]) -> Dict[str, object]:
    """Re-derive the architecture verdict at record-assembly time, and refuse a lie.

    The architecture counterpart of :func:`_validated_functional_evaluation`, and
    it exists for the same reason: ``SL-V2-LOWER-MODEL-01`` says the verdict is
    DERIVED from the opportunity accounting, and that has to be a property of the
    record rather than a convention of the module that wrote it.

    A block that was never scored is passed through unchanged. That is not a
    hole: an unscored block carries ``architecture_violation_present: null``, and
    null is exactly what "nobody measured this" must read as. What is refused is
    a block that claims a scored measurement its own counts do not support.
    """
    if not block.get("architecture_scored"):
        if block.get("architecture_violation_present") is not None:
            raise gov.RunnerRefusal(
                ae.ARCHITECTURE_RESULT_NOT_DERIVABLE,
                "the architecture evaluation block reports a violation verdict "
                f"({block.get('architecture_violation_present')!r}) while "
                "recording that nothing was scored; an unmeasured run has no "
                "architecture verdict in either direction",
            )
        return dict(block)

    missing = [f for f in ae.REQUIRED_COUNTS if block.get(f) is None]
    if missing:
        raise gov.RunnerRefusal(
            ae.ARCHITECTURE_EVALUATOR_MALFORMED_RESULT,
            f"the architecture evaluation block claims to be scored but omits "
            f"{missing}; it is assembled from a scorer result, never by hand",
        )
    derived = ae.derive_violation_present(block)
    if bool(block.get("architecture_violation_present")) != derived:
        raise gov.RunnerRefusal(
            ae.ARCHITECTURE_RESULT_NOT_DERIVABLE,
            f"the architecture evaluation block claims "
            f"architecture_violation_present="
            f"{block.get('architecture_violation_present')!r} while its own "
            f"counts derive {derived!r}; the verdict is not a supplied value",
        )
    return dict(block)


def build_run_record(
    *,
    purpose: gov.RunPurpose,
    run_id: str,
    task_id: str,
    task_sha256: str,
    condition: str,
    mode: str,
    repetition: Optional[int] = None,
    state_log: Sequence[Dict[str, object]],
    model: Dict[str, object],
    environment: Dict[str, object],
    worktree: Dict[str, object],
    context_audit: Dict[str, object],
    fresh_launch: Dict[str, object],
    invocation: Dict[str, object],
    model_identity: Dict[str, object],
    post_run_capture: Optional[Dict[str, object]],
    evaluation: Dict[str, object],
    manifest_freeze: Dict[str, object],
    artifacts: Dict[str, str],
    prerequisite_blockers: Sequence[Dict[str, str]],
    outcome: Dict[str, object],
    generated_at: str = "unspecified",
    repo: Path = gov.REPO,
    #: SL-V2-EFF-01 / SL-V2-EFF-RESET-01. Both default to ``None`` and both are
    #: OMITTED from the record when they are ``None``, so a record written by a
    #: purpose that has neither is byte-identical to the one it produced before
    #: these fields existed.
    reset: Optional[Dict[str, object]] = None,
    efficiency: Optional[Dict[str, object]] = None,
    #: SL-V2-EFF-FUNC-01. Same contract as the two above: ``None`` is omitted, so
    #: a record written by a purpose that carries no functional evaluation is
    #: byte-identical to the one it produced before this field existed, and the
    #: PT08/PT09/PT10 records already on disk stay schema-valid unchanged.
    functional_evaluation: Optional[Dict[str, object]] = None,
    #: SL-V2-LOWER-MODEL-01. Same contract again, and deliberately a SEPARATE
    #: field from ``functional_evaluation``: the two channels are different
    #: measurements of the same candidate and neither is derivable from the
    #: other. ``None`` is omitted, so every record written by a purpose that
    #: carries no architecture evaluation — which is every purpose before this
    #: decision — is byte-identical to the one it produced before this existed.
    architecture_evaluation: Optional[Dict[str, object]] = None,
    #: SL-V2-EFF-ABORT-01 / SL-V2-EFF-RESTART-01. Same contract again: both are
    #: OMITTED when ``None``, so a record written by a purpose that declares no
    #: execution attempt and no reset-aware identity is byte-identical to the one
    #: it produced before these fields existed.
    execution_attempt: Optional[int] = None,
    run_identity: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    """Assemble the run record, deriving the firewall from the purpose itself."""
    firewall = purpose.firewall_flags()
    run_purpose_block: Dict[str, object] = {
        "name": purpose.name,
        "decision_id": purpose.decision_id,
        "confirmatory": purpose.confirmatory,
    }
    run_purpose_block.update(firewall)

    # The flags are re-checked against the purpose even though they were just
    # derived from it: the check is what makes a hand-edited or mutated record
    # fail closed instead of being written.
    gov.assert_firewall_consistent(purpose, run_purpose_block)

    extra: Dict[str, object] = {}
    if reset is not None:
        extra["reset"] = reset
    if efficiency is not None:
        extra["efficiency"] = efficiency
    if execution_attempt is not None:
        extra["execution_attempt"] = normalise_execution_attempt(execution_attempt)
    if run_identity is not None:
        extra["run_identity"] = dict(run_identity)
    if functional_evaluation is not None:
        extra["functional_evaluation"] = _validated_functional_evaluation(
            functional_evaluation
        )
    if architecture_evaluation is not None:
        extra["architecture_evaluation"] = _validated_architecture_evaluation(
            architecture_evaluation
        )

    return {
        **extra,
        "schema_version": RECORD_SCHEMA_VERSION,
        "record_kind": "runner_run_record",
        "run_id": run_id,
        "generated_at": generated_at,
        "run_purpose": run_purpose_block,
        "task_id": task_id,
        "task_sha256": task_sha256,
        "condition": condition,
        "mode": mode,
        # SL-RUNID-01: always emitted, so every record written from here on carries the
        # repetition that produced it. The schema keeps the field OPTIONAL so a
        # record written before SL-RUNID-01 still validates and is never rewritten.
        "repetition": normalise_repetition(repetition),
        "repetition_declared": repetition is not None,
        "state_log": list(state_log),
        "model": model,
        "environment": environment,
        "protocol_versions": protocol_versions(repo),
        "worktree": worktree,
        "context_audit": context_audit,
        "fresh_launch": fresh_launch,
        "invocation": invocation,
        "model_identity": model_identity,
        "post_run_capture": post_run_capture,
        "evaluation": evaluation,
        "manifest_freeze": manifest_freeze,
        "artifacts": dict(artifacts),
        "prerequisite_blockers": [dict(b) for b in prerequisite_blockers],
        "outcome": outcome,
    }


def load_schema(path: Path = SCHEMA_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_run_record(record: Dict[str, object], schema: Optional[dict] = None) -> None:
    """Validate a record and re-check its firewall; refuse rather than warn."""
    schema = schema if schema is not None else load_schema()
    errors = ca.validate_against_schema(record, schema)
    if errors:
        raise gov.RunnerRefusal(
            gov.PREPARED_MANIFEST_INVALID,
            "the run record does not validate: " + "; ".join(errors[:6]),
        )
    block = record.get("run_purpose")
    if not isinstance(block, dict) or not block.get("name"):
        raise gov.RunnerRefusal(
            gov.RUN_ARTIFACT_PURPOSE_MISSING,
            "the run record carries no run purpose; an unmarked artifact is an "
            "error and is never read as a confirmatory observation",
        )
    purpose = gov.resolve_run_purpose(str(block["name"]))
    gov.assert_firewall_consistent(purpose, block)


def write_run_record(
    directory: ArtifactDirectory, record: Dict[str, object]
) -> Path:
    """Validate then write. A record that does not validate is never written."""
    validate_run_record(record)
    return directory.write_json("run_record.json", record)


# --------------------------------------------------------------------------- #
# Execution-root isolation (SL-V2-EFF-RESTART-01, Part J)
# --------------------------------------------------------------------------- #
#: The scopes ``context_audit`` assigns to material found beside the workspace
#: or above it. A root whose fixed ancestor chain carries either is a root whose
#: every run will be audited CONTAMINATED, and discovering that per repetition
#: rather than per execution is how Attempt 1 spent operator time.
_HOST_CONTEXT_SCOPES = ("workspace", "ancestor")


def execution_root_isolation_problems(
    root: Path,
    *,
    home: Optional[Path] = None,
    ancestors: Optional[Sequence[Path]] = None,
) -> List[tuple]:
    """Every reason a root is not an isolated execution root. Empty means it is.

    Attempt 1 surfaced this as an infrastructure fact rather than a theory: an
    artifact root under the operator's own profile puts the host's real
    ``~/.claude`` on the ancestor chain the pre-execution audit walks, so the
    audit marks the environment CONTAMINATED and does so CORRECTLY. The audit was
    not wrong and is not relaxed; the ROOT is what moves.

    Two independent checks:

    1. **Profile descent.** The root is, or descends from, the active user
       profile. This is the structural statement, and it holds even on a machine
       where the profile happens to carry no configuration today.
    2. **Host material on the ancestor chain**, judged by
       :func:`context_audit.scan_context_sources` itself rather than by a second
       definition written here. A check that re-implemented "what counts as
       contamination" could drift away from the audit that actually gates the
       run, and then a root this function blessed would still refuse at
       ``CONTEXT_AUDIT``.

    ``home`` and ``ancestors`` are injectable for the same reason every other
    scan root in this harness is: a test must be able to describe a filesystem
    rather than inherit the one it happens to run on.
    """
    resolved = Path(root).resolve()
    profile = Path(home).resolve() if home is not None else Path.home().resolve()
    problems: List[tuple] = []

    if resolved == profile or profile in resolved.parents:
        problems.append((
            gov.ARTIFACT_ROOT_NOT_ISOLATED,
            f"{resolved} descends from the active user profile {profile}; the "
            "profile's own configuration is then on the ancestor chain the "
            "pre-execution context audit walks, and every run under it is "
            "audited CONTAMINATED",
        ))

    chain = list(ancestors) if ancestors is not None else list(resolved.parents)
    # A directory that does not exist yet has no host material in it, and the
    # probe home/config are pointed at a path that cannot exist so they
    # contribute nothing: this call judges the CHAIN, not the run.
    probe = resolved / "__isolation_probe_never_created__"
    roots = ca.ScanRoots(
        workspace=resolved,
        home=probe,
        config_dir=probe,
        ancestors=[Path(a) for a in chain],
        managed_settings=[],
    )
    for source in ca.scan_context_sources(roots):
        if source.scope in _HOST_CONTEXT_SCOPES:
            problems.append((
                gov.ARTIFACT_ROOT_NOT_ISOLATED,
                f"{resolved} has host context material on its ancestor chain: "
                f"{source.kind} at {source.path} ({source.detail}). The "
                "pre-execution context audit reads it, and reads it correctly, "
                "as contamination",
            ))
    return problems


def assert_execution_root_isolated(
    root: Path,
    *,
    label: str,
    home: Optional[Path] = None,
    ancestors: Optional[Sequence[Path]] = None,
) -> Path:
    """Refuse an execution root that is not isolated. Reports every reason."""
    problems = execution_root_isolation_problems(
        root, home=home, ancestors=ancestors
    )
    if problems:
        detail = "; ".join(d for _, d in problems)
        raise gov.RunnerRefusal(
            gov.ARTIFACT_ROOT_NOT_ISOLATED,
            f"the {label} is not an isolated execution root: {detail}",
        )
    return Path(root).resolve()


def environment_block(
    *, observed_cli_version: Optional[str] = None,
    isolated_environment_verified: bool = False,
    registry: Path = gov.MODEL_REGISTRY,
) -> Dict[str, object]:
    """Environment facts, separating what is *governed* from what is *observed*."""
    pins = governed_toolchain(registry)
    return {
        "os": f"{platform.system()} {platform.release()}",
        "governed_cli_version": pins["claude_code_cli_version"],
        "observed_cli_version": observed_cli_version,
        "governed_agent_sdk_version": pins["claude_agent_sdk_version"],
        "python_version": platform.python_version(),
        "isolated_environment_verified": isolated_environment_verified,
    }
