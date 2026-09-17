#!/usr/bin/env python3
"""Governed inputs, refusal codes and prerequisite gates for the v2 runner.

Why this module exists
----------------------
The runner must never decide anything the governance record decides. Every
value it enforces — which purposes exist, which task and condition a purpose
admits, which quarantine flags a diagnostic artifact carries, what the approved
task hash is, whether a model is selected, whether a manifest is frozen — is
**read from, or checked against, the public authorities**:

===========================================  =================================
Authority                                    What the runner takes from it
===========================================  =================================
``docs/v2/PT08_C1_DIFFICULTY_DIAGNOSTIC_``   ``SL-PT08-01``: the run purpose
``DECISION.md`` §9                           marker and the five quarantine
                                             flags, re-derived from the table
``experiments/v2/tasks/public/``             the approved public task hash,
``TASK_INDEX.csv``                           eligibility and visible CI command
``docs/v2/TASK_ACCEPTANCE_MATRIX.csv``       hidden-acceptance validation and
                                             manifest lifecycle status
``docs/v2/MODEL_REGISTRY.yml``               ``primary_model`` and the governed
                                             exact model ids
``docs/v2/OPEN_DECISIONS.csv``               the blocking-decision register
``prepare_model_worktree``                   the allowlist and the per-condition
``substrate_identity``                       architecture delivery + substrate
                                             identity algorithm
===========================================  =================================

Nothing here selects a model, chooses a sample size, freezes a manifest,
validates hidden acceptance, passes a gate or runs anything. Every function
either reports a fact or raises :class:`RunnerRefusal`.

**Fail closed** is the only mode. A missing authority, an unparseable authority
and a disagreeing authority are all refusals, never defaults.

No model is invoked and no benchmark task is executed.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import prepare_model_worktree as pmw
import substrate_identity as si

REPO = Path(__file__).resolve().parents[3]
HARNESS = Path(__file__).resolve().parent
DOCS_V2 = REPO / "docs" / "v2"
PUBLIC_TASKS = REPO / "experiments" / "v2" / "tasks" / "public"

TASK_INDEX = PUBLIC_TASKS / "TASK_INDEX.csv"
ACCEPTANCE_MATRIX = DOCS_V2 / "TASK_ACCEPTANCE_MATRIX.csv"
PILOT_TASK_MATRIX = DOCS_V2 / "PILOT_PUBLIC_TASK_MATRIX.csv"
MODEL_REGISTRY = DOCS_V2 / "MODEL_REGISTRY.yml"
OPEN_DECISIONS = DOCS_V2 / "OPEN_DECISIONS.csv"
DIAGNOSTIC_RECORD = DOCS_V2 / "PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md"
EXECUTION_DECISIONS_RECORD = DOCS_V2 / "PT08_DIAGNOSTIC_EXECUTION_DECISIONS.md"
SYNC_RECORD = DOCS_V2 / "PT08_PUBLIC_ACCOUNTING_SYNCHRONIZATION.md"
SUBSTRATE_IDENTITY_DOC = DOCS_V2 / "SOURCE_SUBSTRATE_IDENTITY.md"

#: ``SL-PT08-06``: the diagnostic-scoped freeze exception. The runner re-derives
#: its applicability table from this record rather than trusting a constant.
DIAGNOSTIC_FREEZE_RECORD = DOCS_V2 / "PT08_DIAGNOSTIC_SCOPED_FREEZE_DECISION.md"

#: ``SL-V2-QUAL-01``: the pre-data natural-path escape-hatch policy, the
#: ``INSTRUMENT_QUALIFICATION_DIAGNOSTIC`` run purpose, and the PT09/PT10
#: diagnostic-scoped freezes. One record, section-scoped tables: the parsers below
#: are pointed at a named section rather than at the document, so a second task's
#: table can never silently redefine the first's.
QUALIFICATION_DECISION_RECORD = DOCS_V2 / "V2_QUALIFICATION_DIAGNOSTIC_DECISION.md"

#: The harness-local execution-record schema. ``SL-PT08-02`` makes this the
#: authoritative schema for ``PT08_DIFFICULTY_DIAGNOSTIC`` and for that purpose
#: only, because it already mechanically requires every quarantine field.
DIAGNOSTIC_RECORD_SCHEMA = HARNESS / "run_record.schema.json"

#: The pinned canonical result-manifest schema. It is the governed schema for
#: future confirmatory / result-bearing runs, it carries none of the quarantine
#: fields, and ``SL-PT08-02`` leaves it UNCHANGED and its gap UNRESOLVED.
CANONICAL_RUN_MANIFEST_SCHEMA = (
    REPO / "experiments" / "v2" / "schemas" / "run_manifest.schema.json"
)

#: Confirmatory artifact areas. A non-confirmatory run artifact may never be
#: written into either of them (SL-PT08-01 §9; RUN_ARTIFACT_MATRIX.csv, whose
#: every result-bearing row templates to ``experiments/v2/results/<run_id>/``
#: and names ``analysis`` as the consumer).
CONFIRMATORY_ARTIFACT_DIRS: Tuple[Path, ...] = (
    REPO / "experiments" / "v2" / "results",
    REPO / "experiments" / "v2" / "analysis",
)

#: The canonical source substrate this study scores against
#: (docs/v2/SOURCE_SUBSTRATE_IDENTITY.md; asserted against the doc by a test).
SUBSTRATE_COMMIT = "630d3180af0d02a86330dfb599f559e78df65e94"
SUBSTRATE_CONTENT_HASH = (
    "0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3"
)
SUBSTRATE_ENTRY_COUNT = 49


# --------------------------------------------------------------------------- #
# Refusal
# --------------------------------------------------------------------------- #
class RunnerRefusal(RuntimeError):
    """A fail-closed runner refusal. ``code`` is machine-readable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


# Run-purpose / firewall
RUN_PURPOSE_MISSING = "RUN_PURPOSE_MISSING"
RUN_PURPOSE_UNRECOGNISED = "RUN_PURPOSE_UNRECOGNISED"
TASK_NOT_PERMITTED_FOR_PURPOSE = "TASK_NOT_PERMITTED_FOR_PURPOSE"
CONDITION_NOT_PERMITTED_FOR_PURPOSE = "CONDITION_NOT_PERMITTED_FOR_PURPOSE"
DIAGNOSTIC_FIREWALL_INCONSISTENT = "DIAGNOSTIC_FIREWALL_INCONSISTENT"
RUN_ARTIFACT_PURPOSE_MISSING = "RUN_ARTIFACT_PURPOSE_MISSING"
#: SL-RUNID-01. A declared repetition index that is not a governed one. Artifact
#: identity is never silently repaired: an out-of-range or non-integer index
#: refuses rather than being coerced to a neighbouring run's identity.
RUN_REPETITION_INVALID = "RUN_REPETITION_INVALID"
DIAGNOSTIC_ARTIFACT_IN_CONFIRMATORY_AREA = "DIAGNOSTIC_ARTIFACT_IN_CONFIRMATORY_AREA"
ARTIFACT_ROOT_INSIDE_CANONICAL_REPOSITORY = (
    "ARTIFACT_ROOT_INSIDE_CANONICAL_REPOSITORY"
)
DIAGNOSTIC_ARTIFACT_SCHEMA_LACKS_FIREWALL = (
    "DIAGNOSTIC_ARTIFACT_SCHEMA_LACKS_FIREWALL"
)
DIAGNOSTIC_SCHEMA_APPLICABILITY_INCONSISTENT = (
    "DIAGNOSTIC_SCHEMA_APPLICABILITY_INCONSISTENT"
)
DIAGNOSTIC_REPETITION_DECISION_INCONSISTENT = (
    "DIAGNOSTIC_REPETITION_DECISION_INCONSISTENT"
)
GOVERNANCE_RECORD_UNREADABLE = "GOVERNANCE_RECORD_UNREADABLE"

# Worktree (TD-B22)
PREPARED_MANIFEST_INVALID = "PREPARED_MANIFEST_INVALID"
TASK_SHA_MISMATCH = "TASK_SHA_MISMATCH"
SUBSTRATE_IDENTITY_MISMATCH = "SUBSTRATE_IDENTITY_MISMATCH"
WORKTREE_PATH_NOT_ALLOWLISTED = "WORKTREE_PATH_NOT_ALLOWLISTED"
UNEXPECTED_MODEL_VISIBLE_FILE = "UNEXPECTED_MODEL_VISIBLE_FILE"
PREPARED_WORKTREE_DIRTY = "PREPARED_WORKTREE_DIRTY"
ARCHITECTURE_DELIVERY_VIOLATION = "ARCHITECTURE_DELIVERY_VIOLATION"
CANONICAL_REPOSITORY_EXECUTION_REFUSED = "CANONICAL_REPOSITORY_EXECUTION_REFUSED"
CANONICAL_REPOSITORY_MODIFIED = "CANONICAL_REPOSITORY_MODIFIED"

# Context isolation
CONTEXT_AUDIT_CONTAMINATED = "CONTEXT_AUDIT_CONTAMINATED"
CONTEXT_AUDIT_UNKNOWN = "CONTEXT_AUDIT_UNKNOWN"
CONTEXT_AUDIT_ERROR = "CONTEXT_AUDIT_ERROR"
CONTEXT_AUDIT_MISSING = "CONTEXT_AUDIT_MISSING"

# Fresh launch / model
SESSION_RESUME_REJECTED = "SESSION_RESUME_REJECTED"
SESSION_CONTINUE_REJECTED = "SESSION_CONTINUE_REJECTED"
SESSION_ID_REUSED = "SESSION_ID_REUSED"
FALLBACK_MODEL_REJECTED = "FALLBACK_MODEL_REJECTED"
LAUNCH_COMMAND_DIVERGED_FROM_AUDIT = "LAUNCH_COMMAND_DIVERGED_FROM_AUDIT"
MODEL_SELECTION_REQUIRED = "MODEL_SELECTION_REQUIRED"
PRIMARY_MODEL_NOT_SELECTED = "PRIMARY_MODEL_NOT_SELECTED"
MODEL_ID_NOT_GOVERNED = "MODEL_ID_NOT_GOVERNED"
REAL_INVOCATION_NOT_ENABLED = "REAL_INVOCATION_NOT_ENABLED"
MODEL_READBACK_MISSING = "MODEL_READBACK_MISSING"
MODEL_READBACK_MISMATCH = "MODEL_READBACK_MISMATCH"
MODEL_READBACK_AMBIGUOUS = "MODEL_READBACK_AMBIGUOUS"
Q1_READBACK_NOT_VALIDATED_LIVE = "Q1_READBACK_NOT_VALIDATED_LIVE"
Q8_INVALID_MODEL_ID_NOT_VALIDATED_LIVE = "Q8_INVALID_MODEL_ID_NOT_VALIDATED_LIVE"

# Evaluation / lifecycle
HIDDEN_ACCEPTANCE_NOT_VALIDATED = "HIDDEN_ACCEPTANCE_NOT_VALIDATED"
MANIFEST_NOT_FROZEN = "MANIFEST_NOT_FROZEN"

# SL-PT08-06 — the diagnostic-scoped freeze exception. Every one of these is a
# refusal: the exception narrows the APPLICABILITY of one suite-wide gate for one
# (purpose, task, condition) triple, and anything outside that triple, or any
# record that disagrees with the runner, fails closed.
DIAGNOSTIC_FREEZE_NOT_AUTHORISED = "DIAGNOSTIC_FREEZE_NOT_AUTHORISED"
DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT = "DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT"
DIAGNOSTIC_FREEZE_SCOPE_EXCEEDED = "DIAGNOSTIC_FREEZE_SCOPE_EXCEEDED"
DIAGNOSTIC_FREEZE_AUTHORITY_MISMATCH = "DIAGNOSTIC_FREEZE_AUTHORITY_MISMATCH"
DIAGNOSTIC_FREEZE_MISSING = "DIAGNOSTIC_FREEZE_MISSING"
SUITE_WIDE_G1_MUST_NOT_BE_CLAIMED = "SUITE_WIDE_G1_MUST_NOT_BE_CLAIMED"
DIAGNOSTIC_MODEL_ID_MISMATCH = "DIAGNOSTIC_MODEL_ID_MISMATCH"
DIAGNOSTIC_RUNTIME_VERSION_MISMATCH = "DIAGNOSTIC_RUNTIME_VERSION_MISMATCH"
PRIVATE_PUBLIC_SYNC_PROPAGATION_REQUIRED_BEFORE_FREEZE = (
    "PRIVATE_PUBLIC_SYNC_PROPAGATION_REQUIRED_BEFORE_FREEZE"
)
PRIVATE_LINKAGE_NOT_VERIFIABLE = "PRIVATE_LINKAGE_NOT_VERIFIABLE"
ARCHITECTURE_CORPUS_NOT_AVAILABLE = "ARCHITECTURE_CORPUS_NOT_AVAILABLE"
ISOLATED_ENVIRONMENT_NOT_VERIFIED = "ISOLATED_ENVIRONMENT_NOT_VERIFIED"

#: SL-V2-EFF-ELIG-01. The executed legal / target-violating reference validation
#: a pilot-scoped corpus exemption stands on. It is a REFUSAL in every direction:
#: an absent record, a record not bound to the approved task bytes, a legal
#: reference that violates, a violating reference the scorer misses, or a
#: detected rule/edge that is not the declared target one all fail closed. The
#: exemption never widens — a task that cannot satisfy it is simply blocked by
#: ARCHITECTURE_CORPUS_NOT_AVAILABLE exactly as before.
PILOT_ARCHITECTURE_VALIDATION_NOT_AVAILABLE = (
    "PILOT_ARCHITECTURE_VALIDATION_NOT_AVAILABLE"
)

# Real-process launch outcomes. A launch that cannot be started, cannot be
# completed, or cannot be read back is INVALID; none of these is ever a partial
# success that a repetition could still be scored from.
MODEL_PROCESS_FAILED = "MODEL_PROCESS_FAILED"
MODEL_WORKTREE_NOT_LAUNCHABLE = "MODEL_WORKTREE_NOT_LAUNCHABLE"

# ---- Two-phase reset execution (SL-V2-EFF-RESET-01, pilot-scoped) ---------- #
# Every one of these is a REFUSAL, not a degradation. A reset that cannot be
# performed exactly as the protocol describes produces no observation at all;
# there is no "mostly a reset" and no repair path that spends another run.
RESET_STATE_INVALID = "RESET_STATE_INVALID"
RESET_NOT_AUTHORISED_FOR_PURPOSE = "RESET_NOT_AUTHORISED_FOR_PURPOSE"
RESET_BUDGET_NOT_FROZEN = "RESET_BUDGET_NOT_FROZEN"
RESET_CHECKPOINT_NOT_SELECTED = "RESET_CHECKPOINT_NOT_SELECTED"
RESET_CHECKPOINT_PREDICATE_MISMATCH = "RESET_CHECKPOINT_PREDICATE_MISMATCH"
RESET_PHASE_PROCESS_NOT_STOPPED = "RESET_PHASE_PROCESS_NOT_STOPPED"
RESET_PHASE_SESSION_REUSED = "RESET_PHASE_SESSION_REUSED"
RESET_PHASE_PROFILE_REUSED = "RESET_PHASE_PROFILE_REUSED"
RESET_PHASE_CONVERSATION_REUSED = "RESET_PHASE_CONVERSATION_REUSED"
RESET_PHASE_CONTEXT_AUDIT_MISSING = "RESET_PHASE_CONTEXT_AUDIT_MISSING"
RESET_PHASE_MODEL_CHANGED = "RESET_PHASE_MODEL_CHANGED"
RESET_PHASE_RUNTIME_CHANGED = "RESET_PHASE_RUNTIME_CHANGED"
RESET_PHASE_CONDITION_CHANGED = "RESET_PHASE_CONDITION_CHANGED"
RESET_PHASE_TASK_CHANGED = "RESET_PHASE_TASK_CHANGED"
RESET_PHASE_ARCHITECTURE_CHANGED = "RESET_PHASE_ARCHITECTURE_CHANGED"
RESET_WORKTREE_NOT_PRESERVED = "RESET_WORKTREE_NOT_PRESERVED"

#: NOT a refusal. The substantive observation a reset run produces when phase A
#: exhausts its allowance without the selected checkpoint ever becoming true.
#: It is recorded, never repaired: no phase B is fabricated, no rerun is
#: scheduled, no budget is raised and no alternate checkpoint is substituted.
RESET_CHECKPOINT_NOT_REACHED = "RESET_CHECKPOINT_NOT_REACHED"

# ---- Efficiency measurement (SL-V2-EFF-01, pilot-scoped) ------------------ #
EFFICIENCY_USAGE_MISSING = "EFFICIENCY_USAGE_MISSING"
EFFICIENCY_USAGE_MALFORMED = "EFFICIENCY_USAGE_MALFORMED"
EFFICIENCY_RUN_PLAN_INVALID = "EFFICIENCY_RUN_PLAN_INVALID"
ARCHITECTURE_CONTEXT_HASH_MISMATCH = "ARCHITECTURE_CONTEXT_HASH_MISMATCH"

# ---- Artifact identity and ownership (SL-V2-EFF-ABORT-01) ----------------- #
#: The destination of a run's governed artifacts could not be proved new for
#: THIS observation: it already exists carrying another run's identity, another
#: observation's material, or content whose owner cannot be established.
#:
#: Raised BEFORE model invocation and before anything is written. That timing is
#: the whole control. Attempt 1 of the efficiency pilot refused on the same
#: underlying fact — one observation's directory already held another's — but it
#: refused in ``CAPTURE_WORKTREE``, after the prompt had been delivered, after
#: the model had run to completion, and after the earlier observation's prepared
#: worktree and manifests had already been overwritten on the way in.
ARTIFACT_IDENTITY_COLLISION_PREINVOCATION = (
    "ARTIFACT_IDENTITY_COLLISION_PREINVOCATION"
)

#: A recursive delete was requested for a path that is not this run's own fresh
#: temporary state. Cleanup is permitted; reclaiming another observation's
#: directory because the next run derived the same path is not.
ARTIFACT_DESTRUCTIVE_REUSE_REFUSED = "ARTIFACT_DESTRUCTIVE_REUSE_REFUSED"

#: A declared execution attempt that is not a governed one. Attempt identity is
#: infrastructure provenance, and provenance that was silently repaired is
#: provenance nobody can reconcile against the execution it names.
EXECUTION_ATTEMPT_INVALID = "EXECUTION_ATTEMPT_INVALID"

#: The whole-schedule preflight found two scheduled rows deriving one identity,
#: or one artifact directory. It refuses the WHOLE execution before row 1 rather
#: than the row that happens to collide, because the collision is a property of
#: the schedule and discovering it at row 9 is what cost Attempt 1 an observation.
EFFICIENCY_SCHEDULE_IDENTITY_COLLISION = "EFFICIENCY_SCHEDULE_IDENTITY_COLLISION"

#: The chosen artifact or sterile root descends from the active user profile, or
#: its ancestor chain carries host ``.claude`` material the pre-execution context
#: audit would (correctly) read as CONTAMINATED. Pilot-scoped: it is an operator
#: isolation requirement for the replacement execution, not a treatment change.
ARTIFACT_ROOT_NOT_ISOLATED = "ARTIFACT_ROOT_NOT_ISOLATED"

#: The pinned run-manifest schema (``experiments/v2/schemas``) is byte-pinned by
#: the private evaluator's public linkage and sets ``additionalProperties:false``,
#: so it cannot carry SL-PT08-01 §9's six quarantine fields without a linkage
#: re-approval this package is not authorised to perform. The runner therefore
#: emits its own harness-local ``run_record.json`` and reports this code rather
#: than editing a pinned payload or silently dropping the firewall.
#:
#: ``SL-PT08-02`` adjudicates the APPLICABILITY of this gap and nothing else: the
#: canonical schema is the governed result-manifest schema for future
#: confirmatory / result-bearing runs, it is UNCHANGED, and its gap stays
#: **UNRESOLVED**. It is simply not the schema a non-result diagnostic artifact
#: validates against, so it is NOT_APPLICABLE — never "fixed" — for that purpose.
#: The code is retained so the open global issue keeps a name.
RUN_MANIFEST_SCHEMA_LACKS_DIAGNOSTIC_FIREWALL = (
    "RUN_MANIFEST_SCHEMA_LACKS_DIAGNOSTIC_FIREWALL"
)


# --------------------------------------------------------------------------- #
# Run purpose and the diagnostic firewall (SL-PT08-01 §9)
# --------------------------------------------------------------------------- #
#: The five eligibility flags a non-confirmatory artifact must carry, in the
#: order the governance table lists them.
FIREWALL_FIELDS: Tuple[str, ...] = (
    "confirmatory_eligible",
    "enters_confirmatory_dataset",
    "enters_confirmatory_e1_analysis",
    "enters_treatment_effect_analysis",
    "enters_power_estimation",
)

#: The two outcome flags that say an artifact is not a result. SL-PT08-02 pins
#: both to false for the diagnostic; together with FIREWALL_FIELDS they are the
#: eight fields the authoritative execution-record schema must mechanically
#: require and pin, and the whole set is checked as a set.
NON_RESULT_FIELDS: Tuple[str, ...] = ("is_result", "scored")

#: Everything a non-result execution-record schema must pin to ``false``.
QUARANTINE_FIELDS: Tuple[str, ...] = FIREWALL_FIELDS + NON_RESULT_FIELDS

#: The section of a freeze record whose applicability table the runner
#: re-derives, for the single-task ``SL-PT08-06`` record. A record carries other
#: two-column tables for human readers, and parsing the whole file would let a
#: prose table silently redefine a governed value, so every parse is scoped to a
#: named section rather than to the document.
#:
#: Defined here, above :data:`RUN_PURPOSES`, because each purpose names the
#: sections it is governed by and the dict is evaluated at import.
DIAGNOSTIC_FREEZE_TABLE_HEADING = "### 2.1 The applicability table"

#: The section that pins the frozen execution configuration (SL-PT08-06 §5).
DIAGNOSTIC_FREEZE_CONFIG_HEADING = "## 5. The frozen execution configuration"

#: Values the record must carry for the scoped freeze to exist at all. Kept as
#: data so a relaxation in the record is a mechanical failure, never a reading.
#:
#: Defined here, above :data:`RUN_PURPOSES`, for the same reason the headings
#: are: a purpose may narrow this tuple in its own definition and that dict is
#: evaluated at import.
DIAGNOSTIC_FREEZE_PINS: Tuple[Tuple[str, object], ...] = (
    ("diagnostic_freeze_frozen", True),
    ("diagnostic_freeze_model_selector_is_alias", False),
    ("diagnostic_freeze_api_key_used", False),
    ("diagnostic_freeze_fallback_model_permitted", False),
    ("diagnostic_freeze_process_per_repetition", "fresh"),
    ("diagnostic_freeze_session_per_repetition", "fresh"),
    ("diagnostic_freeze_resume_permitted", False),
    ("diagnostic_freeze_continuation_permitted", False),
    ("diagnostic_freeze_session_reuse_permitted", False),
    ("diagnostic_freeze_sterile_context_required", True),
    ("diagnostic_freeze_context_audit_required_every_repetition", True),
    ("diagnostic_freeze_architecture_delivery", "none"),
    ("diagnostic_freeze_is_result", False),
    ("diagnostic_freeze_scored", False),
)


@dataclass(frozen=True)
class RunPurpose:
    """A governed reason for a run, and the artifact quarantine it implies."""

    name: str
    decision_id: str
    description: str
    confirmatory: bool
    permitted_tasks: Tuple[str, ...]
    permitted_conditions: Tuple[str, ...]
    firewall: Tuple[Tuple[str, bool], ...]
    #: SL-PT08-02: the authoritative execution-record schema for THIS purpose,
    #: repository-relative. A result-bearing purpose names the canonical
    #: result-manifest schema instead; a non-result one names the harness record
    #: schema that already carries the firewall.
    artifact_schema: str = "experiments/v2/harness/run_record.schema.json"
    #: SL-PT08-02 again: True only for a purpose whose artifacts ARE results.
    #: The canonical result-manifest firewall requirement applies to exactly
    #: these purposes, and is never waived for them.
    result_bearing: bool = False
    #: SL-PT08-03: the governed repetition count, or ``None`` when no sample
    #: size is pinned for the purpose. Never defaulted to a number.
    repetitions: Optional[int] = None
    #: The Study-Lead decisions that pin the schema applicability and the
    #: repetition count, recorded so a report can cite them rather than assert.
    schema_decision_id: str = "SL-PT08-02"
    repetition_decision_id: str = "SL-PT08-03"
    #: ``SL-PT08-06``: the Study-Lead decision that grants THIS purpose a
    #: diagnostic-scoped freeze, or ``None`` when no such exception exists for it.
    #: ``None`` is the fail-closed default: a purpose that names no authority can
    #: never acquire a scoped freeze, and the suite-wide gate governs it in full.
    diagnostic_freeze_authority: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Where THIS purpose's governance is written down.
    #
    # ``SL-PT08-06`` was a single-task exception, so the runner could name its
    # record and its table headings as module constants. A second authorised
    # purpose makes that a bug rather than a simplification: two purposes would
    # read one another's tables. Every authority location is therefore carried by
    # the purpose, and every default below reproduces the PT08 behaviour exactly,
    # so the pre-existing purpose is unchanged by this generalisation.
    #
    # A ``None`` heading means "parse the whole document", which is what the PT08
    # records need because each of them carries exactly one governed table set. A
    # record that carries a table set PER TASK names its sections instead, so a
    # later section can never overwrite an earlier one's values.
    # ------------------------------------------------------------------ #
    #: The record carrying the run-purpose firewall table (SL-PT08-01 §9 and its
    #: equivalents), repository-relative, and the section to scope the parse to.
    firewall_record: str = "docs/v2/PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md"
    firewall_heading: Optional[str] = None
    #: The record carrying the repetition / fresh-execution table, and its section.
    execution_decisions_record: str = (
        "docs/v2/PT08_DIAGNOSTIC_EXECUTION_DECISIONS.md"
    )
    execution_decisions_heading: Optional[str] = None
    #: The values that table must carry. PT08's are the module default.
    repetition_pins: Optional[Tuple[Tuple[str, object], ...]] = None
    #: The record carrying the diagnostic-scoped freeze, and the PER-TASK section
    #: headings for its applicability table and its frozen-configuration table.
    #: A task absent from the mapping has no scoped freeze and fails closed.
    diagnostic_freeze_record: Optional[str] = None
    diagnostic_freeze_table_headings: Dict[str, str] = field(default_factory=dict)
    diagnostic_freeze_config_headings: Dict[str, str] = field(default_factory=dict)
    #: The execution values the freeze table must carry, or ``None`` for the
    #: module default. Carried per purpose for the same reason
    #: :data:`diagnostic_freeze_global_pins` is: a purpose authorising more than
    #: one condition cannot pin a single ``architecture_delivery`` statically,
    #: because its arms legitimately differ. Dropping that one key from the tuple
    #: does NOT drop the check — :func:`diagnostic_freeze_problems` still
    #: re-derives the delivery from :func:`architecture_delivery_for` for the
    #: condition in hand and refuses on disagreement, which is the stronger test.
    diagnostic_freeze_pins: Optional[Tuple[Tuple[str, object], ...]] = None
    #: The suite-wide facts the freeze record must report as NOT granted. Carried
    #: per purpose because they are *facts about the study at the time of the
    #: decision*, not constants: ``priority_b_state`` was truthfully ``not
    #: started`` for SL-PT08-06 and is truthfully ``started; not complete`` now.
    #: Pinning a stale value here would force a later record to misreport it.
    diagnostic_freeze_global_pins: Optional[Tuple[Tuple[str, object], ...]] = None
    #: The private architecture-corpus script this purpose's tasks are validated
    #: by, private-root-relative. ``None`` keeps the per-task ``<task>_corpus.py``
    #: convention. Never a guess: an unresolvable script is reported as absent.
    private_corpus_script: Optional[str] = None

    # ------------------------------------------------------------------ #
    # ``SL-V2-EFF-ELIG-01``: the PILOT-SCOPED architecture-corpus exemption.
    #
    # ``None`` is the fail-closed default, and it is the value every existing
    # purpose keeps. A purpose that names no exemption authority is governed by
    # the corpus prerequisite IN FULL, which is what every confirmatory or
    # result-bearing purpose must remain governed by. The exemption cannot be
    # acquired by running, by editing an artifact, or by a task: it exists only
    # where a Study-Lead decision put it, on the purpose itself.
    # ------------------------------------------------------------------ #
    architecture_corpus_exemption: Optional[str] = None
    architecture_corpus_exemption_record: Optional[str] = None
    architecture_corpus_exemption_heading: Optional[str] = None
    #: The values that record's table must carry for the exemption to exist at
    #: all. Carried as data so a relaxation in the record is a mechanical
    #: failure rather than a reading, exactly as the freeze pins are.
    architecture_corpus_exemption_pins: Tuple[Tuple[str, object], ...] = ()

    # ------------------------------------------------------------------ #
    # ``SL-V2-EFF-FUNC-01``: the post-run functional-validity channel, and the
    # architecture reporting it does NOT imply.
    #
    # Both default to the pre-existing behaviour, so no registered purpose
    # changes by acquiring these fields. ``None`` means *this purpose runs no
    # post-run functional evaluation*, which is what every purpose did before;
    # ``True`` means *an architecture result is expected of this purpose*, which
    # is what every purpose's evaluation block already reported.
    # ------------------------------------------------------------------ #
    #: The Study-Lead decision that defines ``FUNCTIONAL_VALID`` for this purpose
    #: and authorises the out-of-band private scorer, or ``None``. A purpose that
    #: names no authority is never handed a candidate worktree to score.
    functional_evaluation_authority: Optional[str] = None
    functional_evaluation_record: Optional[str] = None
    #: False for a purpose whose governance defines it as COST-ONLY. It does not
    #: disable architecture scoring — nothing here could — it stops the run
    #: record from reporting a missing architecture result as an outstanding
    #: BLOCKER, which reads as "an architecture result is owed" for a purpose
    #: that is forbidden to produce one.
    produces_architecture_result: bool = True

    # ------------------------------------------------------------------ #
    # ``SL-V2-LOWER-MODEL-01``: the post-run ARCHITECTURE channel.
    #
    # Deliberately a SEPARATE pair of fields from the functional ones, and
    # deliberately independent of :attr:`produces_architecture_result`. The two
    # answer different questions: that one says whether an architecture result is
    # OWED of this purpose, and this one says whether a live-worktree
    # architecture SCORER is authorised to be invoked for it. A purpose can owe
    # an architecture result through some other route and still name no scorer
    # here, and ``None`` — the default every earlier purpose keeps — means no
    # candidate worktree is ever handed to an architecture scorer at all.
    #
    # It is never merged with the functional channel. A functional verdict that
    # could move because of an architecture finding, or the reverse, would make
    # the two measurements one measurement wearing two names.
    # ------------------------------------------------------------------ #
    architecture_evaluation_authority: Optional[str] = None
    architecture_evaluation_record: Optional[str] = None

    # ------------------------------------------------------------------ #
    # ``SL-V2-EFF-RESTART-01``: the operator-level execution-root isolation
    # requirement, and why it is a PURPOSE field rather than a global one.
    #
    # ``None`` -- the default every other purpose keeps -- means this purpose
    # imposes no isolation requirement on its execution roots beyond the ones
    # :func:`assert_artifact_area_permitted` already imposes on every run. The
    # PT08/PT09/PT10 diagnostics executed under roots this requirement would now
    # refuse, and retro-fitting it to them would invalidate artifacts produced
    # correctly under the rules in force when they ran.
    #
    # The requirement is infrastructure isolation, not a treatment: it changes
    # where a run's files live and nothing a run measures.
    # ------------------------------------------------------------------ #
    requires_isolated_execution_root: Optional[str] = None

    def firewall_flags(self) -> Dict[str, bool]:
        return dict(self.firewall)

    def artifact_schema_path(self, repo: Path = REPO) -> Path:
        return Path(repo) / self.artifact_schema

    def firewall_record_path(self, repo: Path = REPO) -> Path:
        return Path(repo) / self.firewall_record

    def execution_decisions_record_path(self, repo: Path = REPO) -> Path:
        return Path(repo) / self.execution_decisions_record

    def freeze_record_path(self, repo: Path = REPO) -> Optional[Path]:
        return Path(repo) / self.diagnostic_freeze_record if self.diagnostic_freeze_record else None

    @staticmethod
    def _heading(
        headings: Dict[str, str], task_id: str, condition: Optional[str]
    ) -> Optional[str]:
        """Look a section up by ``TASK/CONDITION`` first, then by ``TASK``.

        A purpose authorising ONE condition per task tables its sections by task
        and nothing changes for it. A purpose authorising SEVERAL conditions per
        task — the efficiency pilot runs each of its tasks under both ``C1`` and
        ``C4`` — must table them per (task, condition), because the two differ in
        a load-bearing value: ``C1`` receives no architecture payload and ``C4``
        receives it by prompt injection. Reading one arm's table as the other's
        would let the record certify a delivery that never happened.
        """
        if condition:
            scoped = headings.get(f"{task_id}/{condition}")
            if scoped is not None:
                return scoped
        return headings.get(task_id)

    def freeze_table_heading(
        self, task_id: str, condition: Optional[str] = None
    ) -> Optional[str]:
        return self._heading(
            self.diagnostic_freeze_table_headings, task_id, condition
        )

    def freeze_config_heading(
        self, task_id: str, condition: Optional[str] = None
    ) -> Optional[str]:
        return self._heading(
            self.diagnostic_freeze_config_headings, task_id, condition
        )

    def freeze_pins(self) -> Tuple[Tuple[str, object], ...]:
        return (
            DIAGNOSTIC_FREEZE_PINS
            if self.diagnostic_freeze_pins is None
            else self.diagnostic_freeze_pins
        )

    def global_pins(self) -> Tuple[Tuple[str, object], ...]:
        return (
            DIAGNOSTIC_FREEZE_GLOBAL_PINS
            if self.diagnostic_freeze_global_pins is None
            else self.diagnostic_freeze_global_pins
        )

    def pins_for_repetitions(self) -> Tuple[Tuple[str, object], ...]:
        return REPETITION_PINS if self.repetition_pins is None else self.repetition_pins

    def corpus_script_for(self, task_id: str) -> str:
        return self.private_corpus_script or f"scripts/{task_id.lower()}_corpus.py"

    def corpus_exemption_record_path(self, repo: Path = REPO) -> Optional[Path]:
        return (
            Path(repo) / self.architecture_corpus_exemption_record
            if self.architecture_corpus_exemption_record
            else None
        )


#: The ONLY run purpose this repository currently authorises. No confirmatory
#: purpose is registered, because none is authorised: Stage 0 is gated on
#: TD-B34, which is open. An unregistered purpose fails closed.
RUN_PURPOSES: Dict[str, RunPurpose] = {
    "PT08_DIFFICULTY_DIAGNOSTIC": RunPurpose(
        name="PT08_DIFFICULTY_DIAGNOSTIC",
        decision_id="SL-PT08-01",
        description=(
            "the pre-Stage-0 PT08-only, C1-only, non-confirmatory instrument "
            "difficulty diagnostic authorised by SL-PT08-01"
        ),
        confirmatory=False,
        permitted_tasks=("PT08",),
        permitted_conditions=("C1",),
        firewall=tuple((f, False) for f in FIREWALL_FIELDS),
        # SL-PT08-02. The harness record schema is authoritative for THIS
        # purpose because it already requires every quarantine field; the
        # canonical result-manifest schema is untouched and stays governed for
        # result-bearing runs, whose gap remains unresolved.
        artifact_schema="experiments/v2/harness/run_record.schema.json",
        result_bearing=False,
        # SL-PT08-03. Three repeated difficulty probes of one instrument under
        # one condition. No power calculation justifies it and none is implied.
        repetitions=3,
        # SL-PT08-06. A purpose that carries a diagnostic-scoped freeze. It
        # narrows the APPLICABILITY of the suite-wide G1 freeze prerequisite for
        # this triple and passes no gate; a purpose that leaves this None stays
        # governed by the suite-wide rule in full.
        diagnostic_freeze_authority="SL-PT08-06",
        diagnostic_freeze_record="docs/v2/PT08_DIAGNOSTIC_SCOPED_FREEZE_DECISION.md",
        diagnostic_freeze_table_headings={"PT08": DIAGNOSTIC_FREEZE_TABLE_HEADING},
        diagnostic_freeze_config_headings={"PT08": DIAGNOSTIC_FREEZE_CONFIG_HEADING},
    ),
    "INSTRUMENT_QUALIFICATION_DIAGNOSTIC": RunPurpose(
        name="INSTRUMENT_QUALIFICATION_DIAGNOSTIC",
        decision_id="SL-V2-QUAL-01",
        description=(
            "the pre-Stage-0, PT09/PT10-only, C1-only, NON-CONFIRMATORY instrument "
            "qualification diagnostic authorised by SL-V2-QUAL-01: three repeated "
            "C1 probes per instrument, to determine whether each candidate's "
            "architecture opportunity exerts empirical pressure on an unguided "
            "model. It is not a result, not scored for confirmatory E1, not "
            "treatment-effect eligible and not power eligible"
        ),
        confirmatory=False,
        # TWO instruments, deliberately. They are separate instruments qualified
        # separately under one authority; nothing here pools or compares them.
        permitted_tasks=("PT09", "PT10"),
        permitted_conditions=("C1",),
        firewall=tuple((f, False) for f in FIREWALL_FIELDS),
        # Same reasoning as PT08_DIFFICULTY_DIAGNOSTIC: the harness record schema
        # already requires every quarantine field, and the canonical
        # result-manifest schema is untouched with its gap still UNRESOLVED.
        artifact_schema="experiments/v2/harness/run_record.schema.json",
        result_bearing=False,
        # THREE observations per instrument, frozen before any run. No power
        # calculation justifies the count and none is implied.
        repetitions=3,
        schema_decision_id="SL-V2-QUAL-01",
        repetition_decision_id="SL-V2-QUAL-01",
        diagnostic_freeze_authority="SL-V2-QUAL-01",
        # One record, section-scoped. Every table this purpose is governed by
        # lives in it, and each PER-TASK table names its own section so PT10's
        # values can never be read as PT09's.
        firewall_record="docs/v2/V2_QUALIFICATION_DIAGNOSTIC_DECISION.md",
        firewall_heading="### 3.1 The run-purpose firewall table",
        execution_decisions_record="docs/v2/V2_QUALIFICATION_DIAGNOSTIC_DECISION.md",
        execution_decisions_heading="### 4.1 The repetition table",
        repetition_pins=(
            ("condition", "C1"),
            ("tasks", "PT09, PT10"),
            ("process_per_repetition", "fresh"),
            ("session_per_repetition", "fresh"),
            ("resume_permitted", False),
            ("continuation_permitted", False),
            ("session_reuse_permitted", False),
            ("power_claim", "none"),
            ("precision_claim", "none"),
            ("treatment_effect_claim", "none"),
        ),
        diagnostic_freeze_record="docs/v2/V2_QUALIFICATION_DIAGNOSTIC_DECISION.md",
        diagnostic_freeze_table_headings={
            "PT09": "### 5.1 Applicability table - PT09",
            "PT10": "### 5.2 Applicability table - PT10",
        },
        diagnostic_freeze_config_headings={
            "PT09": "### 6.1 Frozen execution configuration - PT09",
            "PT10": "### 6.2 Frozen execution configuration - PT10",
        },
        # priority B is no longer "not started": SL-QUAL-01 authored PT10 into it.
        # The record must state that truthfully, so the pin states it truthfully.
        diagnostic_freeze_global_pins=(
            ("global_g1", False),
            ("global_g1_passed_by_this_record", False),
            ("suite_frozen", False),
            ("global_manifest_frozen", False),
            ("global_td_b32_status", "open"),
            ("td_b12_g6_status", "open"),
            ("td_b34_status", "open"),
            ("priority_b_state", "started; not complete"),
            ("td_b03_status", "open"),
        ),
        # PT09 and PT10 share one authored corpus module; there is no
        # pt09_corpus.py and inventing one would be a guess, not a check.
        private_corpus_script="scripts/qualification_corpus.py",
    ),
    "AFCI_EFFICIENCY_PILOT": RunPurpose(
        name="AFCI_EFFICIENCY_PILOT",
        decision_id="SL-V2-EFF-01",
        description=(
            "the pre-Stage-0, PT01/PT04/PT07-only, C1-and-C4-only, "
            "NON-CONFIRMATORY AFCI efficiency pilot authorised by SL-V2-EFF-01: "
            "three repetitions of each task in each condition in each reset "
            "state, to see whether supplying the architecture context changes "
            "what a run COSTS. It is not a result, not scored for confirmatory "
            "E1, not treatment-effect eligible and not power eligible, and it "
            "estimates no effect"
        ),
        confirmatory=False,
        # THREE instruments and TWO conditions. This is the first purpose in the
        # repository that authorises C4 at all, and it authorises it for cost
        # measurement only: no architecture score, no violation value and no
        # E1 numerator or denominator is produced, read or implied by it.
        permitted_tasks=("PT01", "PT04", "PT07"),
        permitted_conditions=("C1", "C4"),
        firewall=tuple((f, False) for f in FIREWALL_FIELDS),
        artifact_schema="experiments/v2/harness/run_record.schema.json",
        result_bearing=False,
        # THREE repetitions per (task, condition, reset state) cell, frozen
        # before any efficiency observation exists. No power calculation
        # justifies the count and none is implied.
        repetitions=3,
        schema_decision_id="SL-V2-EFF-01",
        repetition_decision_id="SL-V2-EFF-01",
        diagnostic_freeze_authority="SL-V2-EFF-01",
        firewall_record="docs/v2/AFCI_EFFICIENCY_PILOT_DECISION.md",
        firewall_heading="### 3.1 The run-purpose firewall table",
        execution_decisions_record="docs/v2/AFCI_EFFICIENCY_PILOT_DECISION.md",
        execution_decisions_heading="### 4.1 The repetition table",
        repetition_pins=(
            ("condition", "C1, C4"),
            ("tasks", "PT01, PT04, PT07"),
            ("reset_states", "NON_RESET, RESET"),
            ("process_per_repetition", "fresh"),
            ("session_per_repetition", "fresh"),
            ("resume_permitted", False),
            ("continuation_permitted", False),
            ("session_reuse_permitted", False),
            ("power_claim", "none"),
            ("precision_claim", "none"),
            ("treatment_effect_claim", "none"),
        ),
        diagnostic_freeze_record="docs/v2/AFCI_EFFICIENCY_PILOT_DECISION.md",
        # SIX applicability tables, one per (task, condition). They are NOT
        # collapsed to three: C1 and C4 differ in architecture_delivery, which is
        # the one value a freeze table exists to pin, and a shared table would
        # certify a delivery one of the two arms never received.
        diagnostic_freeze_table_headings={
            "PT01/C1": "### 6.1 Applicability table - PT01 / C1",
            "PT01/C4": "### 6.2 Applicability table - PT01 / C4",
            "PT04/C1": "### 6.3 Applicability table - PT04 / C1",
            "PT04/C4": "### 6.4 Applicability table - PT04 / C4",
            "PT07/C1": "### 6.5 Applicability table - PT07 / C1",
            "PT07/C4": "### 6.6 Applicability table - PT07 / C4",
        },
        diagnostic_freeze_config_headings={
            "PT01/C1": "### 7.1 Frozen execution configuration - PT01 / C1",
            "PT01/C4": "### 7.2 Frozen execution configuration - PT01 / C4",
            "PT04/C1": "### 7.3 Frozen execution configuration - PT04 / C1",
            "PT04/C4": "### 7.4 Frozen execution configuration - PT04 / C4",
            "PT07/C1": "### 7.5 Frozen execution configuration - PT07 / C1",
            "PT07/C4": "### 7.6 Frozen execution configuration - PT07 / C4",
        },
        # The module default minus the single static architecture-delivery pin,
        # which this purpose cannot carry because its two arms legitimately
        # differ. The delivery is still checked, and checked HARDER: it is
        # re-derived from architecture_delivery_for(condition) and compared with
        # the record, so an absent or wrong value still refuses.
        diagnostic_freeze_pins=tuple(
            (k, v)
            for k, v in DIAGNOSTIC_FREEZE_PINS
            if k != "diagnostic_freeze_architecture_delivery"
        ),
        # Truthful at the time of writing, exactly as SL-V2-QUAL-01's were.
        diagnostic_freeze_global_pins=(
            ("global_g1", False),
            ("global_g1_passed_by_this_record", False),
            ("suite_frozen", False),
            ("global_manifest_frozen", False),
            ("global_td_b32_status", "open"),
            ("td_b12_g6_status", "open"),
            ("td_b34_status", "open"),
            ("td_b01_status", "open"),
            ("td_b11_status", "open"),
            ("priority_b_state", "started; not complete"),
            ("td_b03_status", "open"),
        ),
        # SL-V2-EFF-ELIG-01. THE ONLY purpose in the repository that carries an
        # architecture-corpus exemption, and it carries it because this is the
        # only purpose whose architecture measurement is a descriptive guardrail
        # rather than a scored quantity. Every other purpose, registered or
        # future, leaves these fields at their fail-closed defaults and is
        # governed by the corpus prerequisite in full.
        architecture_corpus_exemption="SL-V2-EFF-ELIG-01",
        architecture_corpus_exemption_record=(
            "docs/v2/AFCI_EFFICIENCY_PILOT_ELIGIBILITY_DECISION.md"
        ),
        architecture_corpus_exemption_heading="### 3.1 The eligibility rule table",
        architecture_corpus_exemption_pins=(
            ("decision_id", "SL-V2-EFF-ELIG-01"),
            ("run_purpose", "AFCI_EFFICIENCY_PILOT"),
            ("architecture_corpus_required_for_run_eligibility", False),
            ("pilot_scoped_conditions_required", 8),
            ("architecture_measurement_role", "descriptive quality guardrail"),
            # The four that keep the narrowing a narrowing. If the record ever
            # claimed one of them, the exemption would have stopped being scoped
            # and become a global relaxation, so it is refused outright.
            ("architecture_corpus_requirement_waived_globally", False),
            ("architecture_corpus_required_for_confirmatory_use", True),
            ("private_public_sync_propagation_still_required", True),
            ("enters_confirmatory_e1_analysis", False),
            ("enters_treatment_effect_analysis", False),
            ("enters_power_estimation", False),
            ("passes_g1", False),
            ("passes_g2", False),
            ("closes_td_b32", False),
            ("closes_td_b34", False),
            ("closes_td_b39", False),
            ("changes_e1", False),
            ("admits_new_candidates", False),
            ("makes_pilot_tasks_confirmatory", False),
            ("changes_frozen_pilot_metrics_or_thresholds", False),
            ("observations_when_recorded", 0),
        ),
        # SL-V2-EFF-FUNC-01. THE ONLY purpose that carries a post-run functional
        # evaluation, because it is the only one whose frozen analysis needs a
        # paired functional verdict to admit a cost figure at all. The same
        # decision records that this purpose produces NO architecture result,
        # which is not a change of scope but the removal of a report that
        # implied one was owed.
        functional_evaluation_authority="SL-V2-EFF-FUNC-01",
        functional_evaluation_record=(
            "docs/v2/AFCI_EFFICIENCY_PILOT_FUNCTIONAL_VALIDITY_DECISION.md"
        ),
        produces_architecture_result=False,
        # SL-V2-EFF-RESTART-01. THE ONLY purpose that carries an execution-root
        # isolation requirement, because it is the only purpose with a
        # replacement execution to authorise. Attempt 1 established the fact it
        # encodes: a root under the operator's profile puts the host's real
        # ~/.claude on the ancestor chain the pre-execution audit walks, and the
        # audit then marks the environment CONTAMINATED -- correctly.
        requires_isolated_execution_root="SL-V2-EFF-RESTART-01",
    ),
    "AFCI_LOWER_MODEL_PILOT": RunPurpose(
        name="AFCI_LOWER_MODEL_PILOT",
        decision_id="SL-V2-LOWER-MODEL-01",
        description=(
            "the pre-Stage-0, PT01/PT04/PT07-only, C1-and-C4-only, NON_RESET-only, "
            "NON-CONFIRMATORY lower-capability-model AFCI pilot authorised by "
            "SL-V2-LOWER-MODEL-01: three repetitions of each task in each "
            "condition under a lower-capability coding model, to see whether "
            "explicit architecture guidance becomes more useful when the model "
            "has less ability to infer the architecture from the repository on "
            "its own. It measures architecture quality and efficiency as two "
            "INDEPENDENT channels and combines them into no single score. It is "
            "not a result, not scored for confirmatory E1, not treatment-effect "
            "eligible and not power eligible, it estimates no effect, and it is "
            "NEVER pooled with the claude-sonnet-5 efficiency pilot"
        ),
        confirmatory=False,
        permitted_tasks=("PT01", "PT04", "PT07"),
        permitted_conditions=("C1", "C4"),
        firewall=tuple((f, False) for f in FIREWALL_FIELDS),
        artifact_schema="experiments/v2/harness/run_record.schema.json",
        result_bearing=False,
        # THREE repetitions per (task, condition) cell — 18 observations across
        # 9 paired blocks — frozen before any lower-model observation exists. No
        # power calculation justifies the count and none is implied.
        repetitions=3,
        schema_decision_id="SL-V2-LOWER-MODEL-01",
        repetition_decision_id="SL-V2-LOWER-MODEL-01",
        diagnostic_freeze_authority="SL-V2-LOWER-MODEL-01",
        firewall_record="docs/v2/AFCI_LOWER_MODEL_PILOT_DECISION.md",
        firewall_heading="### 3.1 The run-purpose firewall table",
        execution_decisions_record="docs/v2/AFCI_LOWER_MODEL_PILOT_DECISION.md",
        execution_decisions_heading="### 4.1 The repetition table",
        repetition_pins=(
            ("condition", "C1, C4"),
            ("tasks", "PT01, PT04, PT07"),
            # ONE arm. The reset factor is deliberately excluded so that MODEL
            # CAPABILITY is the only moderator this pilot varies; a difference
            # found while two factors moved would be attributable to either.
            ("reset_states", "NON_RESET"),
            ("process_per_repetition", "fresh"),
            ("session_per_repetition", "fresh"),
            ("resume_permitted", False),
            ("continuation_permitted", False),
            ("session_reuse_permitted", False),
            ("power_claim", "none"),
            ("precision_claim", "none"),
            ("treatment_effect_claim", "none"),
        ),
        diagnostic_freeze_record="docs/v2/AFCI_LOWER_MODEL_PILOT_DECISION.md",
        # SIX tables, one per (task, condition), for the same reason the
        # efficiency pilot carries six: C1 and C4 differ in the one value a
        # freeze table exists to pin.
        diagnostic_freeze_table_headings={
            "PT01/C1": "### 6.1 Applicability table - PT01 / C1",
            "PT01/C4": "### 6.2 Applicability table - PT01 / C4",
            "PT04/C1": "### 6.3 Applicability table - PT04 / C1",
            "PT04/C4": "### 6.4 Applicability table - PT04 / C4",
            "PT07/C1": "### 6.5 Applicability table - PT07 / C1",
            "PT07/C4": "### 6.6 Applicability table - PT07 / C4",
        },
        diagnostic_freeze_config_headings={
            "PT01/C1": "### 7.1 Frozen execution configuration - PT01 / C1",
            "PT01/C4": "### 7.2 Frozen execution configuration - PT01 / C4",
            "PT04/C1": "### 7.3 Frozen execution configuration - PT04 / C1",
            "PT04/C4": "### 7.4 Frozen execution configuration - PT04 / C4",
            "PT07/C1": "### 7.5 Frozen execution configuration - PT07 / C1",
            "PT07/C4": "### 7.6 Frozen execution configuration - PT07 / C4",
        },
        # Same reasoning as the efficiency pilot's: the static architecture
        # delivery pin is dropped because the two arms legitimately differ, and
        # the delivery is then re-derived per condition and compared, which is
        # the stronger check.
        diagnostic_freeze_pins=tuple(
            (k, v)
            for k, v in DIAGNOSTIC_FREEZE_PINS
            if k != "diagnostic_freeze_architecture_delivery"
        ),
        # Truthful at the time of writing. TD-B42 joins the list because it was
        # open when this record was written and this record does not close it.
        diagnostic_freeze_global_pins=(
            ("global_g1", False),
            ("global_g1_passed_by_this_record", False),
            ("suite_frozen", False),
            ("global_manifest_frozen", False),
            ("global_td_b32_status", "open"),
            ("td_b12_g6_status", "open"),
            ("td_b34_status", "open"),
            ("td_b01_status", "open"),
            ("td_b11_status", "open"),
            ("td_b42_status", "open"),
            ("priority_b_state", "started; not complete"),
            ("td_b03_status", "open"),
        ),
        # The corpus exemption is NOT inherited from SL-V2-EFF-ELIG-01: that
        # decision is scoped to that purpose. This purpose carries its own,
        # adjudicated on its own facts in its own record, and evaluated against
        # the SAME eight conditions. The one wording that legitimately differs is
        # the measurement's role: the efficiency pilot produced no architecture
        # result at all, and this one reports a descriptive, non-confirmatory
        # architecture endpoint.
        architecture_corpus_exemption="SL-V2-LOWER-MODEL-01",
        architecture_corpus_exemption_record=(
            "docs/v2/AFCI_LOWER_MODEL_PILOT_DECISION.md"
        ),
        architecture_corpus_exemption_heading="### 9.1 The eligibility rule table",
        architecture_corpus_exemption_pins=(
            ("decision_id", "SL-V2-LOWER-MODEL-01"),
            ("run_purpose", "AFCI_LOWER_MODEL_PILOT"),
            ("architecture_corpus_required_for_run_eligibility", False),
            ("pilot_scoped_conditions_required", 8),
            (
                "architecture_measurement_role",
                "descriptive non-confirmatory quality endpoint",
            ),
            ("architecture_corpus_requirement_waived_globally", False),
            ("architecture_corpus_required_for_confirmatory_use", True),
            ("private_public_sync_propagation_still_required", True),
            ("enters_confirmatory_e1_analysis", False),
            ("enters_treatment_effect_analysis", False),
            ("enters_power_estimation", False),
            ("passes_g1", False),
            ("passes_g2", False),
            ("closes_td_b32", False),
            ("closes_td_b34", False),
            ("closes_td_b39", False),
            ("changes_e1", False),
            ("admits_new_candidates", False),
            ("makes_pilot_tasks_confirmatory", False),
            ("changes_frozen_pilot_metrics_or_thresholds", False),
            ("observations_when_recorded", 0),
        ),
        # FUNCTIONAL_VALID is adopted UNCHANGED from SL-V2-EFF-FUNC-01 rather
        # than redefined: a second definition of "did the run work?" would make
        # the two pilots' functional counts incomparable, which is precisely what
        # the descriptive cross-model comparison needs them to be.
        functional_evaluation_authority="SL-V2-EFF-FUNC-01",
        functional_evaluation_record=(
            "docs/v2/AFCI_EFFICIENCY_PILOT_FUNCTIONAL_VALIDITY_DECISION.md"
        ),
        # THE FIRST purpose that measures live-run architecture quality. The
        # efficiency pilot was COST-ONLY and set this False; this pilot's whole
        # quality question is an architecture question, so it owes one.
        produces_architecture_result=True,
        architecture_evaluation_authority="SL-V2-LOWER-MODEL-01",
        architecture_evaluation_record=(
            "docs/v2/AFCI_LOWER_MODEL_PILOT_DECISION.md"
        ),
        # The same operator-level isolation requirement the replacement
        # efficiency execution carries, and for the same reason: a root under the
        # operator's profile is audited CONTAMINATED, correctly.
        requires_isolated_execution_root="SL-V2-LOWER-MODEL-01",
    ),
}


def resolve_run_purpose(name: Optional[str]) -> RunPurpose:
    """Return the governed purpose for ``name``, failing closed on anything else.

    An absent purpose is an error, never a default: SL-PT08-01 §9 requires that
    an unmarked artifact can never be read as a confirmatory observation.
    """
    if name is None or not str(name).strip():
        raise RunnerRefusal(
            RUN_PURPOSE_MISSING,
            "every run must declare an explicit --run-purpose; an unmarked run "
            "is an error and never defaults to confirmatory (SL-PT08-01 §9)",
        )
    purpose = RUN_PURPOSES.get(str(name).strip())
    if purpose is None:
        raise RunnerRefusal(
            RUN_PURPOSE_UNRECOGNISED,
            f"{name!r} is not a governed run purpose; authorised purposes are "
            f"{sorted(RUN_PURPOSES)}",
        )
    return purpose


def assert_task_and_condition_permitted(
    purpose: RunPurpose, task_id: str, condition: str
) -> None:
    """Refuse any (task, condition) the purpose's authorisation does not cover."""
    if task_id not in purpose.permitted_tasks:
        raise RunnerRefusal(
            TASK_NOT_PERMITTED_FOR_PURPOSE,
            f"{purpose.name} authorises {list(purpose.permitted_tasks)} only; "
            f"got task {task_id!r} ({purpose.decision_id} is one instrument)",
        )
    if condition not in purpose.permitted_conditions:
        raise RunnerRefusal(
            CONDITION_NOT_PERMITTED_FOR_PURPOSE,
            f"{purpose.name} authorises condition "
            f"{list(purpose.permitted_conditions)} only; got {condition!r} "
            f"({purpose.decision_id} is one condition)",
        )


def assert_firewall_consistent(purpose: RunPurpose, flags: Dict[str, object]) -> None:
    """Refuse artifact flags that disagree with the purpose's governed values."""
    expected = purpose.firewall_flags()
    missing = [f for f in FIREWALL_FIELDS if f not in flags]
    if missing:
        raise RunnerRefusal(
            DIAGNOSTIC_FIREWALL_INCONSISTENT,
            f"the run record is missing quarantine flags {missing}",
        )
    wrong = {f: flags[f] for f in FIREWALL_FIELDS if flags[f] is not expected[f]}
    if wrong:
        raise RunnerRefusal(
            DIAGNOSTIC_FIREWALL_INCONSISTENT,
            f"quarantine flags disagree with {purpose.decision_id}: {wrong} "
            f"(required {expected})",
        )


def governed_firewall_from_record(
    path: Path = DIAGNOSTIC_RECORD, heading: Optional[str] = None
) -> Dict[str, object]:
    """Re-derive the firewall table from the governance record itself.

    The runner's constants are not trusted on their own: this reads the table out
    of the adjudication that authorises the purpose, so a drift between the code
    and the adjudication is a mechanical failure rather than a reading.

    ``heading`` scopes the parse to one named section. ``None`` parses the whole
    document, which is what ``PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`` needs
    because it carries exactly one governed firewall table; a record that carries
    several table sets must name its section so a later table cannot overwrite an
    earlier one's values. An absent named section yields ``{}``, which every
    caller reads as "not governed" and refuses on.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"cannot read {path}: {exc}"
        ) from exc
    if heading is not None:
        text = _section(text, heading)
    values: Dict[str, object] = {}
    for row in re.finditer(r"^\|(.+?)\|(.+?)\|\s*$", text, re.MULTILINE):
        key = row.group(1).strip().strip("`").strip()
        val = row.group(2).strip().strip("`").strip()
        if key == "run_purpose":
            values["run_purpose"] = val
        elif key in FIREWALL_FIELDS:
            values[key] = {"true": True, "false": False}.get(val.lower(), val)
    return values


def governed_execution_decisions(
    path: Path = EXECUTION_DECISIONS_RECORD, heading: Optional[str] = None
) -> Dict[str, object]:
    """Re-derive the repetition / fresh-execution table from the record itself.

    Same discipline as :func:`governed_firewall_from_record`: the runner's
    constants are not trusted on their own, so a drift between the code and the
    adjudication is a mechanical failure rather than a reading. ``heading`` scopes
    the parse to one named section, for the same reason and with the same
    fail-closed empty result.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"cannot read {path}: {exc}"
        ) from exc
    if heading is not None:
        text = _section(text, heading)
    values: Dict[str, object] = {}
    for row in re.finditer(r"^\|(.+?)\|(.+?)\|\s*$", text, re.MULTILINE):
        key = row.group(1).strip().strip("`").strip()
        val = row.group(2).strip().strip("`").strip()
        if not key or key.lower() == "field":
            continue
        low = val.lower()
        values[key] = (
            True if low == "true" else False if low == "false"
            else int(val) if val.isdigit() else val
        )
    return values


# --------------------------------------------------------------------------- #
# SL-PT08-02 — does a schema actually enforce the quarantine?
# --------------------------------------------------------------------------- #
def _object_schemas(node) -> List[dict]:
    """Every subschema that declares a ``properties`` map, at any depth."""
    out: List[dict] = []
    if isinstance(node, dict):
        if isinstance(node.get("properties"), dict):
            out.append(node)
        for value in node.values():
            out.extend(_object_schemas(value))
    elif isinstance(node, list):
        for value in node:
            out.extend(_object_schemas(value))
    return out


def schema_firewall_problems(schema: dict) -> List[str]:
    """Report why ``schema`` fails to enforce the SL-PT08-02 quarantine.

    An empty list means the schema mechanically REQUIRES a ``run_purpose`` block
    and pins every one of :data:`QUARANTINE_FIELDS` to ``false`` — not merely
    permits them. A schema that only *allows* the fields is reported as failing,
    because an artifact could then omit the firewall and still validate.
    """
    problems: List[str] = []
    if "run_purpose" not in (schema.get("required") or []):
        problems.append(
            "run_purpose is not a top-level REQUIRED property, so an unmarked "
            "artifact could validate"
        )
    for field in QUARANTINE_FIELDS:
        declared = False
        for obj in _object_schemas(schema):
            spec = obj["properties"].get(field)
            if spec is None:
                continue
            declared = True
            if field not in (obj.get("required") or []):
                problems.append(f"{field} is declared but not REQUIRED")
            if spec.get("type") != "boolean" or spec.get("enum") != [False]:
                problems.append(
                    f"{field} is not pinned to boolean enum [false] "
                    f"(got type={spec.get('type')!r} enum={spec.get('enum')!r})"
                )
        if not declared:
            problems.append(f"{field} is absent from the schema")
    return problems


def load_json_schema(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"cannot read schema {path}: {exc}"
        ) from exc


def artifact_schema_problems(purpose: RunPurpose, repo: Path = REPO) -> List[str]:
    """Problems with the schema THIS purpose's artifacts actually validate against."""
    return schema_firewall_problems(load_json_schema(purpose.artifact_schema_path(repo)))


def canonical_run_manifest_carries_firewall(repo: Path = REPO) -> bool:
    """True only if the pinned canonical result-manifest schema enforces the firewall.

    It does not today, and this package does not change that. The check exists so
    the report states a verified fact rather than a remembered one, in both
    directions: if the canonical gap is ever genuinely remediated by an
    authorised package, this stops reporting it as open.
    """
    return not schema_firewall_problems(
        load_json_schema(Path(repo) / "experiments" / "v2" / "schemas"
                         / "run_manifest.schema.json")
    )


# --------------------------------------------------------------------------- #
# Condition delivery (reused, never re-specified)
# --------------------------------------------------------------------------- #
#: The one condition that legitimately carries a token-matched generic-guidance
#: payload (CONDITION_MATRIX.csv row C2). Every other condition must carry none,
#: exactly as :func:`prepare_model_worktree._validate_condition_payloads`
#: enforces at preparation time. It is named here because the approved rule is
#: expressed in the preparer's code rather than in a data file; a test asserts
#: the two agree, so this constant can never quietly diverge from it.
GENERIC_GUIDANCE_CONDITION = "C2"


def architecture_delivery_for(condition: str) -> str:
    """Delegate to the approved condition definition; never restate it here."""
    try:
        return pmw.architecture_delivery_for(condition)
    except KeyError as exc:
        raise RunnerRefusal(
            CONDITION_NOT_PERMITTED_FOR_PURPOSE, f"unknown condition {condition!r}"
        ) from exc


def assert_architecture_delivery_none(condition: str) -> None:
    """Refuse unless the approved definition says this condition gets nothing."""
    delivery = architecture_delivery_for(condition)
    if delivery != "none":
        raise RunnerRefusal(
            ARCHITECTURE_DELIVERY_VIOLATION,
            f"{condition} architecture_delivery is {delivery!r}, not 'none'; the "
            "authorised diagnostic is the no-architecture baseline arm",
        )


#: The architecture deliveries a run purpose may legitimately carry, derived
#: from the conditions its authority permits. Nothing is widened here: a purpose
#: still cannot run a condition outside ``permitted_conditions``, and the
#: delivery it gets is still the one ``prepare_model_worktree`` defines.
def permitted_architecture_deliveries(purpose: RunPurpose) -> Tuple[str, ...]:
    return tuple(
        sorted({architecture_delivery_for(c) for c in purpose.permitted_conditions})
    )


def assert_architecture_delivery_authorised(
    purpose: RunPurpose, condition: str
) -> None:
    """Refuse a delivery the authorising purpose does not cover.

    The predecessor of this check asserted ``delivery == 'none'`` for every run,
    which was exactly right while every authorised purpose was a baseline-only
    diagnostic and became wrong the moment a purpose authorised ``C4``. It is
    replaced rather than relaxed: the delivery must still be one the purpose's
    own permitted conditions produce, so a ``C4`` run under a ``C1``-only
    authority is refused with the same code it was refused with before.
    """
    delivery = architecture_delivery_for(condition)
    allowed = permitted_architecture_deliveries(purpose)
    if delivery not in allowed:
        raise RunnerRefusal(
            ARCHITECTURE_DELIVERY_VIOLATION,
            f"{condition} architecture_delivery is {delivery!r}; {purpose.name} "
            f"authorises {list(purpose.permitted_conditions)}, whose deliveries "
            f"are {list(allowed)}",
        )


# --------------------------------------------------------------------------- #
# Public authorities
# --------------------------------------------------------------------------- #
def _rows(path: Path) -> List[Dict[str, str]]:
    try:
        with Path(path).open("r", encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    except OSError as exc:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"cannot read {path}: {exc}"
        ) from exc


def task_index_row(task_id: str, path: Path = TASK_INDEX) -> Dict[str, str]:
    for row in _rows(path):
        if row.get("task_id") == task_id:
            return row
    raise RunnerRefusal(
        GOVERNANCE_RECORD_UNREADABLE,
        f"{task_id} is not in the approved task index {path}",
    )


def expected_task_sha256(task_id: str, path: Path = TASK_INDEX) -> str:
    sha = task_index_row(task_id, path).get("public_task_sha256", "")
    if not re.fullmatch(r"[0-9a-f]{64}", sha or ""):
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE,
            f"{task_id} carries no well-formed public_task_sha256 in {path}",
        )
    return sha


def public_task_path(task_id: str, tasks_dir: Path = PUBLIC_TASKS) -> Path:
    path = Path(tasks_dir) / f"{task_id}.md"
    if not path.is_file():
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"public task body not found: {path}"
        )
    return path


def visible_ci_command(task_id: str, path: Path = TASK_INDEX) -> str:
    """The single CI surface the coding model may see (TD-B16 / ci:agent)."""
    return task_index_row(task_id, path).get("visible_ci_command", "").strip()


def acceptance_matrix_row(task_id: str, path: Path = ACCEPTANCE_MATRIX) -> Dict[str, str]:
    for row in _rows(path):
        if row.get("task_id") == task_id:
            return row
    raise RunnerRefusal(
        GOVERNANCE_RECORD_UNREADABLE, f"{task_id} has no acceptance-matrix row in {path}"
    )


def hidden_acceptance_is_validated(task_id: str, path: Path = ACCEPTANCE_MATRIX) -> bool:
    """True only when the public authority says the hidden suite is validated.

    ``draft_unvalidated`` anywhere in the row, or a lifecycle status that is not
    a validated one, is False. The default is False: absence of evidence of
    validation is never evidence of validation.
    """
    row = acceptance_matrix_row(task_id, path)
    blob = " ".join(str(v) for v in row.values()).lower()
    if "draft_unvalidated" in blob:
        return False
    return row.get("status", "").strip().lower() in {"validated", "frozen"}


def manifest_is_frozen(task_id: str, path: Path = ACCEPTANCE_MATRIX) -> bool:
    """True only when the public authority records a frozen manifest lifecycle."""
    row = acceptance_matrix_row(task_id, path)
    status = row.get("status", "").strip().lower()
    if "not-frozen" in status or "not_frozen" in status:
        return False
    return status == "frozen"


def hidden_acceptance_refusal_code(task_id: str) -> str:
    """``PT08_HIDDEN_ACCEPTANCE_NOT_VALIDATED`` for PT08, per task otherwise."""
    return f"{task_id}_{HIDDEN_ACCEPTANCE_NOT_VALIDATED}"


def primary_model(path: Path = MODEL_REGISTRY) -> Optional[str]:
    """``primary_model`` from the registry, or ``None`` when unselected (TD-B03)."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"cannot read {path}: {exc}"
        ) from exc
    match = re.search(r"^primary_model:\s*(\S+)", text, re.MULTILINE)
    if not match:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"{path} declares no primary_model key"
        )
    value = match.group(1).strip().strip('"').strip("'")
    return None if value in {"null", "~", "None"} else value


def diagnostic_primary_model(
    run_purpose: Optional[str], path: Path = MODEL_REGISTRY
) -> Optional[str]:
    """The model pinned for ONE non-confirmatory run purpose, or ``None``.

    Deliberately separate from :func:`primary_model`. ``TD-B03`` governs the
    selection of *the primary benchmark model* for the confirmatory study — the
    one screened across conditions and subject to the anti-selection rule — and
    that decision stays open with ``primary_model: null``. Pinning a model so a
    quarantined difficulty probe can be executed is a different act, it is
    scoped to the purpose named here, and it confers nothing on the confirmatory
    study. A caller that asks for a purpose the registry does not name gets
    ``None`` and is refused, which is why this can never become a default.
    """
    if not run_purpose:
        return None
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"cannot read {path}: {exc}"
        ) from exc
    block = re.search(
        rf"^\s*{re.escape(run_purpose)}:\s*$(.*?)(?=^\S|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not block:
        return None
    match = re.search(r"^\s*exact_model_id:\s*(\S+)", block.group(1), re.MULTILINE)
    if not match:
        return None
    value = match.group(1).split("#")[0].strip().strip('"').strip("'")
    return None if value in {"null", "~", "None"} else value


def live_runtime_validation(
    run_purpose: Optional[str], path: Path = MODEL_REGISTRY
) -> Tuple[str, str, str]:
    """``(q1, q8, validated_cli_version)`` as recorded for one run purpose.

    Reports what was recorded; it does not re-perform the probes. The probes
    themselves live in ``stage0_runtime_probe.py`` and write their evidence
    outside both repositories.
    """
    blank = ("NOT_VALIDATED", "NOT_VALIDATED", "unrecorded")
    if not run_purpose:
        return blank
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return blank
    block = re.search(
        rf"^\s*{re.escape(run_purpose)}:\s*$(.*?)(?=^\S|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not block:
        return blank
    body = block.group(1)

    def _field(name: str, default: str) -> str:
        m = re.search(rf"^\s*{name}:\s*(\S+)", body, re.MULTILINE)
        return m.group(1).strip().strip('"').strip("'") if m else default

    return (
        _field("q1_readback", "NOT_VALIDATED"),
        _field("q8_invalid_model_id_rejection", "NOT_VALIDATED"),
        _field("validated_claude_code_cli_version", "unrecorded"),
    )


def governed_model_ids(path: Path = MODEL_REGISTRY) -> List[str]:
    """Every exact model id the registry records, including context variants."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"cannot read {path}: {exc}"
        ) from exc
    ids: List[str] = []
    for key in ("exact_model_id", "context_variant_id"):
        for m in re.finditer(rf"^\s*{key}:\s*(\S.*)$", text, re.MULTILINE):
            value = m.group(1).split("#")[0].strip().strip('"').strip("'")
            if value and value not in {"null", "~"}:
                ids.append(value)
    return sorted(set(ids))


def open_decision(decision_id: str, path: Path = OPEN_DECISIONS) -> Dict[str, str]:
    for row in _rows(path):
        if row.get("decision_id") == decision_id or (
            list(row.values()) and list(row.values())[0] == decision_id
        ):
            return row
    raise RunnerRefusal(
        GOVERNANCE_RECORD_UNREADABLE, f"{decision_id} is not in {path}"
    )


def decision_is_open(decision_id: str, path: Path = OPEN_DECISIONS) -> bool:
    row = open_decision(decision_id, path)
    return list(row.values())[-1].strip().lower() == "open"


# --------------------------------------------------------------------------- #
# SL-PT08-06 — the diagnostic-scoped freeze exception
# --------------------------------------------------------------------------- #
# DIAGNOSTIC_FREEZE_TABLE_HEADING and DIAGNOSTIC_FREEZE_CONFIG_HEADING are
# defined above RUN_PURPOSES, because each purpose names the sections it is
# governed by and that dict is evaluated at import time.

#: The suite-wide facts the record must continue to report as NOT granted. If a
#: freeze record ever claimed one of them, the exception would have stopped being
#: an applicability narrowing and become a gate pass, so it is refused outright.
DIAGNOSTIC_FREEZE_GLOBAL_PINS: Tuple[Tuple[str, object], ...] = (
    ("global_g1", False),
    ("global_g1_passed_by_this_record", False),
    ("suite_frozen", False),
    ("global_manifest_frozen", False),
    ("global_td_b32_status", "open"),
    ("td_b12_g6_status", "open"),
    ("td_b34_status", "open"),
    ("priority_b_state", "not started"),
    ("td_b03_status", "open"),
)


@dataclass(frozen=True)
class DiagnosticFreeze:
    """One authorised diagnostic-scoped freeze, and the execution it pins.

    It is deliberately a *narrow* object: a triple plus the configuration the
    authority froze. It carries no suite-wide state, so nothing that consumes it
    can accidentally read a global freeze or a passed gate out of it.
    """

    authority: str
    run_purpose: str
    task_id: str
    condition: str
    task_sha256: str
    exact_model_id: str
    cli_version: str
    repetitions: int
    permission_mode: str
    authentication: str
    #: Always false. Present so a consumer reads the fact rather than assumes it.
    global_g1: bool = False
    suite_frozen: bool = False
    global_manifest_frozen: bool = False

    def covers(self, run_purpose: str, task_id: str, condition: str) -> bool:
        return (
            run_purpose == self.run_purpose
            and task_id == self.task_id
            and condition == self.condition
        )

    def to_dict(self) -> dict:
        return {
            "authority": self.authority,
            "run_purpose": self.run_purpose,
            "task": self.task_id,
            "condition": self.condition,
            "frozen": True,
            "task_sha256": self.task_sha256,
            "exact_model_id": self.exact_model_id,
            "cli_version": self.cli_version,
            "repetitions": self.repetitions,
            "permission_mode": self.permission_mode,
            "authentication": self.authentication,
            "global_g1": self.global_g1,
            "suite_frozen": self.suite_frozen,
            "global_manifest_frozen": self.global_manifest_frozen,
        }


def _section(text: str, heading: str) -> str:
    """The body of one markdown section: the heading line to the next heading."""
    start = text.find(heading)
    if start < 0:
        return ""
    body = text[start + len(heading):]
    nxt = re.search(r"^#", body, re.MULTILINE)
    return body[: nxt.start()] if nxt else body


def _table_values(section: str) -> Dict[str, object]:
    """Two-column markdown rows, coerced, with headers and separators dropped."""
    values: Dict[str, object] = {}
    for row in re.finditer(r"^\|(.+?)\|(.+?)\|\s*$", section, re.MULTILINE):
        key = row.group(1).strip().strip("`").strip()
        val = row.group(2).strip().strip("`").strip()
        if not key or key.lower() in {"field", "state"} or set(key) <= {"-", ":"}:
            continue
        low = val.lower()
        values[key] = (
            True if low == "true" else False if low == "false"
            else int(val) if val.isdigit() else val
        )
    return values


def governed_diagnostic_freeze(
    path: Path = DIAGNOSTIC_FREEZE_RECORD,
    heading: str = DIAGNOSTIC_FREEZE_TABLE_HEADING,
) -> Dict[str, object]:
    """Re-derive a scoped freeze's applicability table from the record itself.

    Same discipline as :func:`governed_firewall_from_record`: the runner's
    constants are not trusted on their own, so a drift between the code and the
    adjudication is a mechanical failure rather than a reading. An unreadable
    record is a refusal, never an empty permission; an absent SECTION yields
    ``{}``, which callers read as "no scoped freeze" and refuse on.

    ``heading`` is the per-task section, so a record governing two instruments
    hands each of them its own table and neither can be read as the other's.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"cannot read {path}: {exc}"
        ) from exc
    return _table_values(_section(text, heading))


def governed_diagnostic_freeze_configuration(
    path: Path = DIAGNOSTIC_FREEZE_RECORD,
    heading: str = DIAGNOSTIC_FREEZE_CONFIG_HEADING,
) -> Dict[str, object]:
    """A scoped freeze's frozen execution configuration, from the record."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"cannot read {path}: {exc}"
        ) from exc
    return _table_values(_section(text, heading))


def diagnostic_freeze_problems(
    purpose: RunPurpose,
    task_id: str,
    condition: str,
    *,
    record: Optional[Path] = None,
    registry: Optional[Path] = None,
    task_index: Optional[Path] = None,
) -> List[Tuple[str, str]]:
    """Every reason ``(purpose, task_id, condition)`` has no scoped freeze.

    An empty list means the exception applies. Anything else is a coded refusal,
    and the FIRST code is the one a caller reports: the list is ordered so the
    narrowest, most specific failure is named rather than a generic one.

    The checks are deliberately redundant with the record. The runner does not
    take the record's word for the task hash, the model id, the runtime version
    or the repetition count — it re-derives each from its own authority and
    refuses on disagreement, so a record could not widen the exception by
    editing a value the rest of the repository disagrees with.
    """
    problems: List[Tuple[str, str]] = []
    authority = purpose.diagnostic_freeze_authority
    if not authority:
        return [(
            DIAGNOSTIC_FREEZE_NOT_AUTHORISED,
            f"{purpose.name} carries no diagnostic-scoped freeze authority; the "
            "suite-wide freeze prerequisite governs it in full",
        )]

    # Scope first: an out-of-scope triple is refused before the record is read,
    # so a scope error can never be reported as a record inconsistency.
    if task_id not in purpose.permitted_tasks or condition not in purpose.permitted_conditions:
        return [(
            DIAGNOSTIC_FREEZE_SCOPE_EXCEEDED,
            f"{authority} scopes the freeze to "
            f"{list(purpose.permitted_tasks)}/{list(purpose.permitted_conditions)} "
            f"under {purpose.name}; got {task_id!r}/{condition!r}",
        )]

    heading = purpose.freeze_table_heading(task_id, condition)
    if heading is None:
        return [(
            DIAGNOSTIC_FREEZE_SCOPE_EXCEEDED,
            f"{authority} names no applicability section for {task_id}/{condition} "
            f"under {purpose.name}; a scoped freeze is never assumed for a "
            "(task, condition) the authority does not table",
        )]
    record_path = record or purpose.freeze_record_path() or DIAGNOSTIC_FREEZE_RECORD
    governed = governed_diagnostic_freeze(record_path, heading)
    if not governed:
        return [(
            DIAGNOSTIC_FREEZE_MISSING,
            f"{authority}'s applicability table for {task_id} "
            f"({heading!r} in {Path(record_path).name}) is absent or unparseable; "
            "a scoped freeze is never assumed",
        )]

    # ---- authority ------------------------------------------------------- #
    for key in ("decision_id", "diagnostic_freeze_authority"):
        if governed.get(key) != authority:
            problems.append((
                DIAGNOSTIC_FREEZE_AUTHORITY_MISMATCH,
                f"the record's {key} is {governed.get(key)!r}, not {authority!r}",
            ))

    # ---- the triple the record itself claims ----------------------------- #
    for key, expected in (
        ("run_purpose", purpose.name),
        ("diagnostic_freeze_task", task_id),
        ("diagnostic_freeze_condition", condition),
    ):
        if governed.get(key) != expected:
            problems.append((
                DIAGNOSTIC_FREEZE_SCOPE_EXCEEDED,
                f"the record's {key} is {governed.get(key)!r}, not {expected!r}",
            ))

    # ---- the suite-wide facts the record must NOT claim ------------------ #
    for key, expected in purpose.global_pins():
        if governed.get(key) != expected:
            problems.append((
                SUITE_WIDE_G1_MUST_NOT_BE_CLAIMED,
                f"the record's {key} is {governed.get(key)!r}, not {expected!r}; "
                "a scoped freeze may never report a suite-wide gate as granted",
            ))

    # ---- the execution pins ---------------------------------------------- #
    for key, expected in purpose.freeze_pins():
        if governed.get(key) != expected:
            problems.append((
                DIAGNOSTIC_FREEZE_RECORD_INCONSISTENT,
                f"the record's {key} is {governed.get(key)!r}, not {expected!r}",
            ))

    # ---- re-derived from the other authorities, never taken on trust ----- #
    try:
        expected_sha = expected_task_sha256(task_id, task_index or TASK_INDEX)
    except RunnerRefusal as exc:
        problems.append((exc.code, exc.message))
    else:
        if governed.get("diagnostic_freeze_task_sha256") != expected_sha:
            problems.append((
                TASK_SHA_MISMATCH,
                f"the record pins task sha256 "
                f"{governed.get('diagnostic_freeze_task_sha256')!r}; the approved "
                f"index pins {expected_sha}",
            ))

    registry_path = registry or MODEL_REGISTRY
    pinned_model = diagnostic_primary_model(purpose.name, registry_path)
    if not pinned_model or governed.get("diagnostic_freeze_exact_model_id") != pinned_model:
        problems.append((
            DIAGNOSTIC_MODEL_ID_MISMATCH,
            f"the record pins exact model "
            f"{governed.get('diagnostic_freeze_exact_model_id')!r}; the registry "
            f"pins {pinned_model!r} for {purpose.name}",
        ))

    q1, q8, validated_cli = live_runtime_validation(purpose.name, registry_path)
    if governed.get("diagnostic_freeze_cli_version") != validated_cli:
        problems.append((
            DIAGNOSTIC_RUNTIME_VERSION_MISMATCH,
            f"the record pins runtime {governed.get('diagnostic_freeze_cli_version')!r}; "
            f"the registry records {validated_cli!r} as live-validated",
        ))
    if q1 != "PASS":
        problems.append((
            Q1_READBACK_NOT_VALIDATED_LIVE,
            f"Q1 is {q1!r}, not PASS; the scoped freeze waives neither control",
        ))
    if q8 != "PASS":
        problems.append((
            Q8_INVALID_MODEL_ID_NOT_VALIDATED_LIVE,
            f"Q8 is {q8!r}, not PASS; the scoped freeze waives neither control",
        ))

    if governed.get("diagnostic_freeze_repetitions") != purpose.repetitions:
        problems.append((
            DIAGNOSTIC_REPETITION_DECISION_INCONSISTENT,
            f"the record pins {governed.get('diagnostic_freeze_repetitions')!r} "
            f"repetitions; {purpose.repetition_decision_id} pins "
            f"{purpose.repetitions!r}",
        ))

    delivery = architecture_delivery_for(condition)
    if delivery != governed.get("diagnostic_freeze_architecture_delivery"):
        problems.append((
            ARCHITECTURE_DELIVERY_VIOLATION,
            f"{condition} architecture_delivery is {delivery!r}; the record pins "
            f"{governed.get('diagnostic_freeze_architecture_delivery')!r}",
        ))

    return problems


def diagnostic_freeze_for(
    purpose: RunPurpose,
    task_id: str,
    condition: str,
    **kwargs,
) -> Optional[DiagnosticFreeze]:
    """The scoped freeze for this triple, or ``None``. Never raises for absence.

    ``None`` is the fail-closed answer: a caller that gets it must fall back to
    the suite-wide rule, which is what every other purpose, task and condition
    already does.
    """
    if diagnostic_freeze_problems(purpose, task_id, condition, **kwargs):
        return None
    governed = governed_diagnostic_freeze(
        kwargs.get("record")
        or purpose.freeze_record_path()
        or DIAGNOSTIC_FREEZE_RECORD,
        purpose.freeze_table_heading(task_id, condition)
        or DIAGNOSTIC_FREEZE_TABLE_HEADING,
    )
    return DiagnosticFreeze(
        authority=str(governed["diagnostic_freeze_authority"]),
        run_purpose=str(governed["run_purpose"]),
        task_id=str(governed["diagnostic_freeze_task"]),
        condition=str(governed["diagnostic_freeze_condition"]),
        task_sha256=str(governed["diagnostic_freeze_task_sha256"]),
        exact_model_id=str(governed["diagnostic_freeze_exact_model_id"]),
        cli_version=str(governed["diagnostic_freeze_cli_version"]),
        repetitions=int(governed["diagnostic_freeze_repetitions"]),
        permission_mode=str(governed["diagnostic_freeze_permission_mode"]),
        authentication=str(governed["diagnostic_freeze_authentication"]),
    )


def diagnostic_freeze_execution_problems(
    freeze: DiagnosticFreeze,
    *,
    model_id: Optional[str] = None,
    cli_version: Optional[str] = None,
    context_verdict: Optional[str] = None,
    session_id: Optional[str] = None,
    previous_session_ids: Sequence[str] = (),
    launch_argv: Sequence[str] = (),
    require_all: bool = False,
    require_context_verdict: Optional[bool] = None,
) -> List[Tuple[str, str]]:
    """Per-repetition conditions the scoped freeze does NOT waive.

    ``require_all`` is what makes this fail closed at the point that matters. A
    readiness report legitimately has no model id, no runtime version and no
    context verdict yet, so it passes ``False`` and only the values it actually
    supplies are checked. A real run passes ``True``, before any process is
    started, and an unsupplied value is then a refusal rather than a silence.

    ``require_context_verdict`` is separated out because the audit genuinely has
    not run yet at the pre-launch check: the state machine runs it next and
    refuses on anything but ``CLEAN`` before a process could be created, and the
    post-run check then re-asserts with the verdict it actually observed.
    Defaulting it to ``require_all`` keeps every other caller fail-closed.
    """
    problems: List[Tuple[str, str]] = []
    require_context = (
        require_all if require_context_verdict is None else require_context_verdict
    )

    def _missing(name: str, code: str, required: bool = None) -> None:
        if require_all if required is None else required:
            problems.append((
                code,
                f"{freeze.authority} requires {name} to be demonstrated for every "
                "repetition; none was supplied and the runner assumes none",
            ))

    if model_id is None:
        _missing("the exact model id", DIAGNOSTIC_MODEL_ID_MISMATCH)
    elif model_id != freeze.exact_model_id:
        problems.append((
            DIAGNOSTIC_MODEL_ID_MISMATCH,
            f"the repetition requests {model_id!r}; {freeze.authority} pins the "
            f"exact id {freeze.exact_model_id!r} and forbids the alias",
        ))

    if cli_version is None:
        _missing("the runtime version", DIAGNOSTIC_RUNTIME_VERSION_MISMATCH)
    elif str(cli_version) != freeze.cli_version:
        problems.append((
            DIAGNOSTIC_RUNTIME_VERSION_MISMATCH,
            f"the runtime reports {cli_version!r}; {freeze.authority} pins the "
            f"live-validated {freeze.cli_version!r}",
        ))

    if context_verdict is None:
        _missing("a CLEAN context audit", CONTEXT_AUDIT_UNKNOWN, require_context)
    elif str(context_verdict).upper() != "CLEAN":
        problems.append((
            CONTEXT_AUDIT_CONTAMINATED
            if str(context_verdict).upper() == "CONTAMINATED"
            else CONTEXT_AUDIT_UNKNOWN,
            f"the context-isolation verdict is {context_verdict!r}; the scoped "
            "freeze waives neither the isolation requirement nor the audit",
        ))

    argv = [str(a) for a in launch_argv]
    for flag, code in (
        ("--resume", SESSION_RESUME_REJECTED),
        ("--continue", SESSION_CONTINUE_REJECTED),
        ("-c", SESSION_CONTINUE_REJECTED),
        ("-r", SESSION_RESUME_REJECTED),
    ):
        if flag in argv:
            problems.append((
                code,
                f"{flag} appears in the launch; every repetition is a fresh "
                "process and a fresh session, and the scoped freeze waives neither",
            ))

    if session_id is not None and session_id in {str(s) for s in previous_session_ids}:
        problems.append((
            SESSION_ID_REUSED,
            f"session id {session_id!r} has already been used; session reuse is "
            "forbidden for every repetition",
        ))

    return problems


def manifest_freeze_state(
    task_id: str,
    *,
    condition: Optional[str] = None,
    run_purpose: Optional[str] = None,
    acceptance_matrix: Path = ACCEPTANCE_MATRIX,
    **kwargs,
) -> Dict[str, object]:
    """The two freeze states, reported separately and never merged.

    ``global_frozen`` is the suite-wide lifecycle answer and is exactly what
    :func:`manifest_is_frozen` has always returned — this function never changes
    it and never writes it. ``diagnostic_frozen`` is the ``SL-PT08-06`` scoped
    state, which exists only for the one authorised triple.

    ``effective_for_this_purpose`` is the only value an eligibility check should
    read, and it is true when *either* state holds. A caller that supplies no
    condition and no run purpose gets the suite-wide answer alone, which is the
    fail-closed reading for every existing call site.
    """
    global_frozen = manifest_is_frozen(task_id, acceptance_matrix)
    freeze: Optional[DiagnosticFreeze] = None
    problems: List[Tuple[str, str]] = []
    if condition and run_purpose:
        try:
            purpose = resolve_run_purpose(run_purpose)
            assert_task_and_condition_permitted(purpose, task_id, condition)
        except RunnerRefusal as exc:
            problems = [(exc.code, exc.message)]
        else:
            problems = diagnostic_freeze_problems(
                purpose, task_id, condition, **kwargs
            )
            if not problems:
                freeze = diagnostic_freeze_for(purpose, task_id, condition, **kwargs)
    return {
        "task_id": task_id,
        "condition": condition,
        "run_purpose": run_purpose,
        # The suite-wide lifecycle answer. Unchanged, never written here.
        "global_frozen": global_frozen,
        "suite_frozen": False,
        "global_gate_g1_passed": False,
        # The SL-PT08-06 scoped answer.
        "diagnostic_frozen": freeze is not None,
        "diagnostic_freeze_authority": freeze.authority if freeze else None,
        "diagnostic_freeze": freeze.to_dict() if freeze else None,
        "diagnostic_freeze_problems": [
            {"code": c, "detail": d} for c, d in problems
        ],
        "effective_for_this_purpose": global_frozen or freeze is not None,
        "changed_by_this_runner": False,
    }


# --------------------------------------------------------------------------- #
# Substrate identity (reused from the approved implementation)
# --------------------------------------------------------------------------- #
def substrate_identity_at(repo: Path, commit: str) -> Tuple[str, str, int]:
    """Return ``(resolved commit, content hash, entry count)`` for ``commit``."""
    try:
        resolved = si.resolve_commit(repo, commit)
        entries = si.substrate_entries_at_commit(repo, resolved)
    except si.SubstrateIdentityError as exc:
        raise RunnerRefusal(
            SUBSTRATE_IDENTITY_MISMATCH,
            f"cannot compute the substrate identity of {commit} in {repo}: {exc}",
        ) from exc
    return resolved, si.hash_entries(entries), len(entries)


def assert_substrate_identity(
    repo: Path = REPO,
    commit: Optional[str] = None,
    expected_hash: Optional[str] = None,
    expected_entries: Optional[int] = None,
) -> Dict[str, object]:
    """Refuse unless the substrate the run is built on is the pinned one.

    The pins default to ``None`` and are resolved from the module constants **at
    call time**, not bound into the signature: a default argument would freeze a
    copy of the pin at import, leaving two values that could disagree.
    """
    commit = SUBSTRATE_COMMIT if commit is None else commit
    expected_hash = SUBSTRATE_CONTENT_HASH if expected_hash is None else expected_hash
    expected_entries = (
        SUBSTRATE_ENTRY_COUNT if expected_entries is None else expected_entries
    )
    resolved, content_hash, entry_count = substrate_identity_at(repo, commit)
    if content_hash != expected_hash or entry_count != expected_entries:
        raise RunnerRefusal(
            SUBSTRATE_IDENTITY_MISMATCH,
            f"substrate {resolved} hashes {content_hash} over {entry_count} "
            f"entries; the governed identity is {expected_hash} over "
            f"{expected_entries} entries",
        )
    return {
        "commit": resolved,
        "content_hash": content_hash,
        "entry_count": entry_count,
        "algorithm": si.ALGORITHM_ID,
    }


# --------------------------------------------------------------------------- #
# Private evaluator repository — READ ONLY, and optional
# --------------------------------------------------------------------------- #
def default_private_root(repo: Path = REPO) -> Path:
    return repo.parent / "afci-bench-evaluator-private"


def _contains_value(node, needle: str) -> bool:
    if isinstance(node, str):
        return node == needle
    if isinstance(node, list):
        return any(_contains_value(i, needle) for i in node)
    if isinstance(node, dict):
        return any(_contains_value(v, needle) for v in node.values())
    return False


def private_linkage_records_task_sha(
    task_id: str, expected_sha: str, private_root: Optional[Path] = None
) -> Tuple[bool, str]:
    """Read-only: does the private per-task linkage carry the approved hash?

    Never writes, never imports private code, and treats an absent private
    repository as *not verifiable* rather than as a pass.
    """
    root = Path(private_root) if private_root else default_private_root()
    linkage = root / "tasks" / task_id / "public_linkage.json"
    if not linkage.is_file():
        return False, f"private per-task linkage not available at {linkage}"
    try:
        data = json.loads(linkage.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return False, f"private per-task linkage unreadable: {exc}"
    if _contains_value(data, expected_sha):
        return True, (
            f"{linkage.relative_to(root).as_posix()} records the approved public "
            f"task hash {expected_sha[:16]}..."
        )
    return False, (
        f"{linkage.relative_to(root).as_posix()} does not record {expected_sha[:16]}..."
    )


def private_sync_prefreeze_state(
    task_id: str, private_root: Optional[Path] = None, repo: Path = REPO
) -> Tuple[bool, str]:
    """Read-only: has the private pre-freeze public-sync record been SATISFIED?

    The record is ``PRIVATE-PUBLIC-SYNC-PREFREEZE-001``, rendered into the
    private per-task package record. Two independent conditions must hold, and
    an absent or unreadable private repository is *not verifiable* rather than a
    pass:

    * the record's own ``state`` must read ``SATISFIED``; and
    * the public commit it claims to have verified must actually be an ancestor
      of (or equal to) this repository's ``HEAD``, so a record citing a commit
      this repository has never contained cannot discharge the blocker.

    Never writes, never imports private code, and decides nothing: the private
    adjudication is the authority and this only reports it.
    """
    root = Path(private_root) if private_root else default_private_root()
    record = root / "tasks" / task_id / f"{task_id.lower()}_package_record.json"
    if not record.is_file():
        return False, f"private package record not available at {record}"
    try:
        data = json.loads(record.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return False, f"private package record unreadable: {exc}"
    block = data.get("public_synchronisation_required_before_freeze")
    if not isinstance(block, dict):
        return False, (
            f"{record.name} carries no public_synchronisation_required_before_"
            f"freeze record"
        )
    record_id = block.get("record_id", "<unnamed>")
    state = str(block.get("state", "")).strip()
    if not state.upper().startswith("SATISFIED"):
        return False, f"{record_id} state is {state!r}, not SATISFIED"

    claimed = str(block.get("verified_public_sha", "")).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", claimed):
        return False, (
            f"{record_id} is SATISFIED but records no well-formed "
            f"verified_public_sha (got {claimed!r})"
        )
    proc = subprocess.run(
        ["git", "-C", str(Path(repo)), "merge-base", "--is-ancestor", claimed, "HEAD"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return False, (
            f"{record_id} cites verified_public_sha {claimed[:16]}..., which is "
            f"not an ancestor of this repository's HEAD"
        )
    return True, (
        f"{record_id} is {state} against verified_public_sha {claimed[:16]}..., "
        f"which is an ancestor of (or equal to) public HEAD"
    )


def private_architecture_corpus_available(
    task_id: str,
    private_root: Optional[Path] = None,
    corpus_script: Optional[str] = None,
) -> Tuple[bool, str]:
    """Read-only availability check for the task's architecture corpus.

    ``corpus_script`` is the private-root-relative module the authorising purpose
    NAMES for this task. It defaults to the per-task ``<task>_corpus.py``
    convention the earlier packages use. It is never guessed: two candidates
    authored into one corpus module say so through their purpose, and a purpose
    that names a module which is not present is reported as not available rather
    than searched for.
    """
    root = Path(private_root) if private_root else default_private_root()
    corpus = root / (corpus_script or f"scripts/{task_id.lower()}_corpus.py")
    spec = root / "spec" / "pilot_spec.py"
    if not corpus.is_file() or not spec.is_file():
        return False, f"the {task_id} architecture corpus is not available under {root}"
    return True, (
        f"{corpus.relative_to(root).as_posix()} and "
        f"{spec.relative_to(root).as_posix()} are present (read-only)"
    )


# --------------------------------------------------------------------------- #
# SL-V2-EFF-ELIG-01 — the pilot-scoped architecture-corpus exemption
# --------------------------------------------------------------------------- #
#: The umbrella/raw-detection family rule. It is registered, it is evaluated, and
#: it may NEVER back a scored opportunity — so it may never be the target rule a
#: corpus exemption is validated against either.
UMBRELLA_RULE_ID = "AR-DEP-001"


def catalog_rule_ids(repo: Path = REPO) -> List[str]:
    """Every ``rule_id`` the approved public architecture rule catalog declares.

    Read from the public catalog rather than from a constant, so a target rule
    the catalog does not register can never be validated against.
    """
    path = Path(repo) / "docs" / "v2" / "ARCHITECTURE_RULE_CATALOG.yml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"cannot read {path}: {exc}"
        ) from exc
    return sorted(
        {m.group(1).strip() for m in re.finditer(r"^\s*-?\s*rule_id:\s*(\S+)", text,
                                                 re.MULTILINE)}
    )


def _reference_problems(label: str, block: object, target: Dict[str, object],
                        *, violating: bool) -> List[str]:
    """Why one validated reference fails to establish what it claims.

    The two references are checked by the SAME function in opposite directions,
    because the property that matters is that they DISAGREE on the architecture
    channel while AGREEING on the functional one. Checking them with two
    bespoke readers would let the two drift apart.
    """
    problems: List[str] = []
    if not isinstance(block, dict):
        return [f"{label}_reference validation is absent"]

    if str(block.get("hidden_functional_acceptance", "")).strip().upper() != "PASS":
        problems.append(
            f"the {label} reference does not record hidden functional acceptance "
            f"PASS (got {block.get('hidden_functional_acceptance')!r})"
        )
    failed = block.get("semantic_failed_cases")
    if failed:
        problems.append(f"the {label} reference failed semantic cases {failed}")

    expected_status = "VIOLATION" if violating else "SATISFIED"
    status = str(block.get("architecture_status", "")).strip().upper()
    if status != expected_status:
        problems.append(
            f"the architecture scorer reports {status or '<absent>'} on the "
            f"{label} reference, not {expected_status}"
        )

    if block.get("applicable_opportunity_count") != 1:
        problems.append(
            f"the {label} reference does not record the intended target "
            f"opportunity as applicable exactly once (applicable_opportunity_"
            f"count={block.get('applicable_opportunity_count')!r})"
        )
    expected_violated = 1 if violating else 0
    if block.get("violated_opportunity_count") != expected_violated:
        problems.append(
            f"the {label} reference records violated_opportunity_count="
            f"{block.get('violated_opportunity_count')!r}, not {expected_violated}"
        )

    if violating:
        # The exact intended violation, not merely A violation. A detected rule
        # or edge that is not the declared target one would mean the scorer
        # noticed something else, which establishes nothing about this target.
        for field_name, target_key in (
            ("detected_rule_id", "rule_id"),
            ("detected_source_layer", "source_layer"),
            ("detected_target_layer", "forbidden_target_layer"),
        ):
            got, want = block.get(field_name), target.get(target_key)
            if got != want:
                problems.append(
                    f"the violating reference's {field_name} is {got!r}, not the "
                    f"declared target {target_key} {want!r}"
                )
    elif block.get("detected_target_layer") is not None:
        problems.append(
            "the legal reference records a detected forbidden target layer "
            f"({block.get('detected_target_layer')!r}); a legal reference takes "
            "no forbidden edge"
        )
    return problems


def private_architecture_validation_state(
    task_id: str,
    private_root: Optional[Path] = None,
    repo: Path = REPO,
    expected_task_sha: Optional[str] = None,
) -> Tuple[bool, str, List[str]]:
    """Read-only: has the executed legal / violating validation been recorded?

    This is ``SL-V2-EFF-ELIG-01`` conditions 2 to 6, read out of the private
    per-task package record. It never imports private code, never executes
    anything, never writes, and decides nothing: the private package is the
    authority for what was executed and this only reports it.

    Returns ``(ok, detail, problems)``. An absent or unreadable private
    repository is *not verifiable* rather than a pass, in both directions.
    """
    root = Path(private_root) if private_root else default_private_root()
    record = root / "tasks" / task_id / f"{task_id.lower()}_package_record.json"
    if not record.is_file():
        return False, f"private package record not available at {record}", [
            f"no private package record at {record}"
        ]
    try:
        data = json.loads(record.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return False, f"private package record unreadable: {exc}", [
            f"private package record unreadable: {exc}"
        ]

    block = data.get("architecture_validation")
    if not isinstance(block, dict):
        return False, (
            f"{record.name} carries no architecture_validation record"
        ), [f"{record.name} carries no architecture_validation record"]

    record_id = block.get("record_id", "<unnamed>")
    problems: List[str] = []

    state = str(block.get("state", "")).strip().upper()
    if state != "VALIDATED":
        problems.append(f"{record_id} state is {state or '<absent>'!r}, not VALIDATED")

    # Bound to the EXACT approved bytes. A validation of some other revision of
    # the task establishes nothing about the one the pilot will run.
    if expected_task_sha is not None:
        claimed = str(block.get("public_task_sha256", "")).strip()
        if claimed != expected_task_sha:
            problems.append(
                f"{record_id} is bound to public_task_sha256 "
                f"{claimed[:16] or '<absent>'}..., not the approved "
                f"{expected_task_sha[:16]}..."
            )

    if block.get("hidden_functional_acceptance_validated") is not True:
        problems.append(
            "the record does not state that hidden functional acceptance is "
            "validated"
        )
    if block.get("functional_acceptance_enforces_architecture") is not False:
        problems.append(
            "the record does not state that functional acceptance leaves "
            "architecture alone; a functional oracle that enforced placement "
            "would make the architecture measurement circular"
        )

    target = block.get("target")
    if not isinstance(target, dict):
        problems.append("the record declares no target opportunity")
        target = {}
    else:
        rule_id = str(target.get("rule_id", "")).strip()
        registered = catalog_rule_ids(repo)
        if rule_id not in registered:
            problems.append(
                f"the declared target rule {rule_id or '<absent>'!r} is not a "
                "rule the approved public architecture rule catalog registers"
            )
        elif rule_id == UMBRELLA_RULE_ID:
            problems.append(
                f"the declared target rule is the umbrella {UMBRELLA_RULE_ID}, "
                "which may never back a scored opportunity"
            )
        for key in ("source_layer", "forbidden_target_layer"):
            if not str(target.get(key, "")).strip():
                problems.append(f"the declared target carries no {key}")

    problems += _reference_problems(
        "legal", block.get("legal_reference"), target, violating=False
    )
    problems += _reference_problems(
        "violating", block.get("violating_reference"), target, violating=True
    )

    if problems:
        return False, f"{record_id}: " + "; ".join(problems[:6]), problems
    return True, (
        f"{record_id} is VALIDATED against the approved public task bytes: a "
        f"legal reference passes hidden functional acceptance and scores "
        f"SATISFIED on the single applicable target opportunity with zero "
        f"violations, and a functionally correct target-violating reference "
        f"ALSO passes hidden functional acceptance while the architecture "
        f"scorer reports the exact declared target violation on it"
    ), []


def architecture_corpus_exemption_problems(
    purpose: RunPurpose,
    task_id: str,
    private_root: Optional[Path] = None,
    repo: Path = REPO,
) -> List[str]:
    """Why ``SL-V2-EFF-ELIG-01``'s eight conditions do NOT hold for this task.

    An empty list means all eight are mechanically satisfied. A purpose with no
    exemption authority always gets a problem, because it has no exemption to
    evaluate — that is the fail-closed default and it is what keeps every
    confirmatory purpose governed by the corpus prerequisite in full.
    """
    if not purpose.architecture_corpus_exemption:
        return [
            f"{purpose.name} names no architecture-corpus exemption authority, "
            "so the corpus prerequisite governs it in full"
        ]

    problems: List[str] = []

    # The authorising record itself, re-derived rather than trusted.
    record_path = purpose.corpus_exemption_record_path(repo)
    if record_path is None or not record_path.is_file():
        return [
            f"{purpose.architecture_corpus_exemption}'s record is not available "
            f"at {purpose.architecture_corpus_exemption_record}"
        ]
    try:
        governed = _table_values(
            _section(
                record_path.read_text(encoding="utf-8"),
                purpose.architecture_corpus_exemption_heading or "",
            )
        )
    except OSError as exc:
        return [f"cannot read {record_path}: {exc}"]
    if not governed:
        return [
            f"{purpose.architecture_corpus_exemption}'s eligibility rule table "
            f"is absent from {purpose.architecture_corpus_exemption_record}"
        ]
    for key, want in purpose.architecture_corpus_exemption_pins:
        got = governed.get(key)
        if got != want:
            problems.append(
                f"the eligibility rule table records {key}={got!r}, not {want!r}"
            )

    # Condition 1 — hidden functional acceptance validated (PUBLIC authority).
    if not hidden_acceptance_is_validated(task_id):
        problems.append(
            f"condition 1: TASK_ACCEPTANCE_MATRIX.csv does not record {task_id}'s "
            "hidden functional acceptance as validated"
        )

    # Conditions 2-6 — the executed reference validation (PRIVATE authority).
    try:
        expected_sha = expected_task_sha256(task_id)
    except RunnerRefusal as exc:
        expected_sha = None
        problems.append(f"conditions 2-6: {exc.message}")
    ok, _detail, validation_problems = private_architecture_validation_state(
        task_id, private_root, repo, expected_sha
    )
    if not ok:
        problems += [f"conditions 2-6: {p}" for p in validation_problems]

    # Condition 7 — the architecture measurement is descriptive here, which is
    # true exactly when the purpose is non-confirmatory and non-result-bearing.
    if purpose.confirmatory or purpose.result_bearing:
        problems.append(
            f"condition 7: {purpose.name} is confirmatory={purpose.confirmatory} "
            f"result_bearing={purpose.result_bearing}, so its architecture "
            "measurement is not a descriptive guardrail"
        )

    # Condition 8 — re-derived from the PURPOSE's own firewall table, in the
    # authorising pilot record, rather than from the exemption record. The two
    # are different documents on purpose: a record cannot exempt itself by
    # restating its own firewall.
    firewall = governed_firewall_from_record(
        purpose.firewall_record_path(repo), purpose.firewall_heading
    )
    for flag in (
        "enters_confirmatory_e1_analysis",
        "enters_treatment_effect_analysis",
        "enters_power_estimation",
    ):
        if firewall.get(flag) is not False:
            problems.append(
                f"condition 8: {purpose.firewall_record} does not pin {flag} "
                f"false (got {firewall.get(flag)!r})"
            )
    return problems


# --------------------------------------------------------------------------- #
# Artifact-area governance
# --------------------------------------------------------------------------- #
def assert_artifact_area_permitted(
    out_root: Path, purpose: RunPurpose, repo: Path = REPO
) -> Path:
    """Refuse to write a non-confirmatory artifact into a result-bearing location.

    Two independent refusals, narrowest first so the reported code names the
    actual problem (SL-PT08-01 §9; SL-PT08-02):

    1. the two confirmatory artifact areas themselves — ``experiments/v2/results``
       and ``experiments/v2/analysis``, the directories every result-bearing row
       of ``RUN_ARTIFACT_MATRIX.csv`` templates into or consumes from;
    2. **anywhere inside the canonical repository at all.** A diagnostic artifact
       root that merely avoids those two directories would still deposit run
       output into the governed tree, where a later reader has no structural
       reason to treat it as non-confirmatory. The governed root is a scratch
       directory outside the repository (:func:`default_artifact_root`).
    """
    resolved = Path(out_root).resolve()
    if purpose.confirmatory:
        return resolved
    for area in CONFIRMATORY_ARTIFACT_DIRS:
        try:
            area_resolved = area.resolve()
        except OSError:  # pragma: no cover - area always resolvable in-repo
            continue
        if resolved == area_resolved or area_resolved in resolved.parents:
            raise RunnerRefusal(
                DIAGNOSTIC_ARTIFACT_IN_CONFIRMATORY_AREA,
                f"{purpose.name} is non-confirmatory and may not write into "
                f"{area_resolved}; use a scratch/tmp artifact root",
            )
    canonical = Path(repo).resolve()
    if resolved == canonical or canonical in resolved.parents:
        raise RunnerRefusal(
            ARTIFACT_ROOT_INSIDE_CANONICAL_REPOSITORY,
            f"{purpose.name} is non-confirmatory and may not write anywhere "
            f"inside the canonical repository {canonical}; its artifacts belong "
            f"in a scratch root outside it (got {resolved})",
        )
    return resolved


def default_artifact_root() -> Path:
    """A scratch artifact root outside the repository's confirmatory areas."""
    return Path(tempfile.gettempdir()) / "afci-bench-v2-runs"


# --------------------------------------------------------------------------- #
# Canonical-repository protection
# --------------------------------------------------------------------------- #
def assert_not_canonical_repository(worktree: Path, repo: Path = REPO) -> None:
    """Refuse to execute a model over the canonical repository itself.

    The model-visible worktree must be a prepared snapshot: never the repository,
    never a directory containing it, never a directory inside it, and never a Git
    working tree (which would give the model the history and the excluded trees).
    """
    wt = Path(worktree).resolve()
    canonical = Path(repo).resolve()
    if wt == canonical or canonical in wt.parents or wt in canonical.parents:
        raise RunnerRefusal(
            CANONICAL_REPOSITORY_EXECUTION_REFUSED,
            f"the model-visible worktree {wt} overlaps the canonical repository "
            f"{canonical}; model work must never touch the source repository",
        )
    if (wt / ".git").exists():
        raise RunnerRefusal(
            CANONICAL_REPOSITORY_EXECUTION_REFUSED,
            f"{wt} is a Git working tree; a prepared snapshot carries no .git",
        )


def repository_state(repo: Path = REPO) -> Dict[str, str]:
    """``(head, porcelain)`` for the canonical repository, for before/after proof."""
    def _git(*args: str) -> str:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True
        )
        return proc.stdout.strip() if proc.returncode == 0 else f"<error {proc.returncode}>"

    return {"head": _git("rev-parse", "HEAD"), "porcelain": _git("status", "--porcelain")}


def assert_canonical_repository_unchanged(
    before: Dict[str, str], repo: Path = REPO
) -> None:
    after = repository_state(repo)
    if after != before:
        raise RunnerRefusal(
            CANONICAL_REPOSITORY_MODIFIED,
            f"the canonical repository changed during the run: {before} -> {after}",
        )


# --------------------------------------------------------------------------- #
# Prerequisite report (--check-readiness)
# --------------------------------------------------------------------------- #
PASS = "PASS"
BLOCKED = "BLOCKED"

#: A prerequisite that does not apply to THIS run purpose, while the underlying
#: issue stays open for the purposes it does apply to. It is deliberately not
#: PASS: PASS would read as "resolved", and the canonical result-manifest
#: firewall gap SL-PT08-02 scopes out of this diagnostic is **unresolved**.
NOT_APPLICABLE = "N/A"


@dataclass
class Prerequisite:
    item: str
    status: str
    detail: str
    code: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "item": self.item,
            "status": self.status,
            "code": self.code,
            "detail": self.detail,
        }


@dataclass
class ReadinessReport:
    purpose: str
    task_id: str
    condition: str
    prerequisites: List[Prerequisite] = field(default_factory=list)

    @property
    def blocked(self) -> List[Prerequisite]:
        return [p for p in self.prerequisites if p.status == BLOCKED]

    @property
    def passed(self) -> List[Prerequisite]:
        return [p for p in self.prerequisites if p.status == PASS]

    @property
    def not_applicable(self) -> List[Prerequisite]:
        return [p for p in self.prerequisites if p.status == NOT_APPLICABLE]

    @property
    def run_eligible(self) -> bool:
        return not self.blocked

    def to_dict(self) -> dict:
        return {
            "report": "afci-bench/v2/runner-readiness",
            "run_purpose": self.purpose,
            "task_id": self.task_id,
            "condition": self.condition,
            "run_eligible": self.run_eligible,
            "pass_count": len(self.passed),
            "blocked_count": len(self.blocked),
            "not_applicable_count": len(self.not_applicable),
            "prerequisites": [p.to_dict() for p in self.prerequisites],
        }


#: The approved architecture payload (the MAD), read from the one governed
#: location. ``C3``/``C4`` require it and ``C1``/``C2`` must never see it.
ARCHITECTURE_CONTEXT = REPO / "docs" / "v2" / "ARCHITECTURE_CONTEXT.md"


def architecture_context_bytes(repo: Path = REPO) -> bytes:
    """The EXACT bytes of the approved architecture payload.

    Read as bytes, not as text: ``C4`` delivers the *same bytes* the oracle's
    catalog is traceable to and that the manifest hashes, so a newline or
    encoding normalisation on the way in would silently make the payload a
    different document from the one the record pins.
    """
    path = Path(repo) / "docs" / "v2" / "ARCHITECTURE_CONTEXT.md"
    try:
        return path.read_bytes()
    except OSError as exc:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE,
            f"the approved architecture payload is unreadable at {path}: {exc}",
        ) from exc


def architecture_context_sha256(repo: Path = REPO) -> str:
    return hashlib.sha256(architecture_context_bytes(repo)).hexdigest()


def architecture_payload_for(condition: str, repo: Path = REPO) -> Optional[str]:
    """The payload this condition receives, or ``None`` when it receives none.

    Derived from :func:`architecture_delivery_for` rather than from a second
    list of conditions, so the two can never disagree about which arm is the
    baseline.
    """
    if architecture_delivery_for(condition) == "none":
        return None
    return architecture_context_bytes(repo).decode("utf-8")


def _worktree_preparation_probe(task_id: str, condition: str) -> Prerequisite:
    """Prepare the governed worktree into a throwaway directory and discard it."""
    tmp = Path(tempfile.mkdtemp(prefix="afci-v2-readiness-"))
    expected = architecture_delivery_for(condition)
    try:
        result = pmw.prepare_model_worktree(
            pmw.PreparationRequest(
                condition=condition,
                source_root=REPO,
                dest_root=tmp / "worktree",
                task_path=public_task_path(task_id),
                task_id=task_id,
                architecture_text=architecture_payload_for(condition),
            )
        )
        delivery = result.manifest["architecture_delivery"]
        if delivery != expected:
            return Prerequisite(
                "c1_worktree_preparation",
                BLOCKED,
                f"architecture_delivery is {delivery!r}, not {expected!r}",
                ARCHITECTURE_DELIVERY_VIOLATION,
            )
        return Prerequisite(
            "c1_worktree_preparation",
            PASS,
            f"{condition} worktree prepares cleanly: "
            f"{result.manifest['entry_count']} allowlisted files, "
            f"architecture_delivery={delivery}, content_hash "
            f"{str(result.manifest['content_hash'])[:16]}...",
        )
    except pmw.WorktreePreparationError as exc:
        return Prerequisite(
            "c1_worktree_preparation", BLOCKED, exc.message, exc.code
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


#: SL-PT08-03's fresh-execution requirements, as the record's table spells them.
#: Each must be present and must carry the recorded value, so relaxing one in the
#: record is a mechanical failure rather than a wording change.
REPETITION_PINS: Tuple[Tuple[str, object], ...] = (
    ("condition", "C1"),
    ("task", "PT08"),
    ("process_per_repetition", "fresh"),
    ("session_per_repetition", "fresh"),
    ("resume_permitted", False),
    ("continuation_permitted", False),
    ("session_reuse_permitted", False),
    ("power_claim", "none"),
    ("precision_claim", "none"),
    ("treatment_effect_claim", "none"),
)


def _repetition_decision_probe(
    purpose: RunPurpose, repo: Path = REPO
) -> Prerequisite:
    """Check the runner's repetition constant against the governance record.

    Reports BLOCKED on any disagreement rather than preferring either side: a
    sample size the code and the adjudication do not agree on is not a governed
    sample size at all.
    """
    try:
        governed = governed_execution_decisions(
            purpose.execution_decisions_record_path(repo),
            purpose.execution_decisions_heading,
        )
    except RunnerRefusal as exc:
        return Prerequisite(
            "diagnostic_repetition_decision", BLOCKED, exc.message, exc.code
        )
    if not governed:
        return Prerequisite(
            "diagnostic_repetition_decision",
            BLOCKED,
            f"{purpose.repetition_decision_id}'s repetition table is absent or "
            f"unparseable in {purpose.execution_decisions_record}; a governed "
            "sample size is never assumed",
            DIAGNOSTIC_REPETITION_DECISION_INCONSISTENT,
        )

    problems: List[str] = []
    recorded = governed.get("diagnostic_repetitions")
    if recorded != purpose.repetitions:
        problems.append(
            f"the record pins diagnostic_repetitions={recorded!r} but the runner "
            f"carries {purpose.repetitions!r}"
        )
    for key, expected in purpose.pins_for_repetitions():
        if governed.get(key) != expected:
            problems.append(f"{key} is {governed.get(key)!r}, not {expected!r}")
    # A purpose authorising SEVERAL conditions tables them as one comma-separated
    # cell. Every token must be permitted and the set must be exhaustive: a
    # record naming a subset would let an unlisted arm run unrecorded, and one
    # naming an extra would widen the authority by punctuation.
    declared = [
        c.strip() for c in str(governed.get("condition", "")).split(",") if c.strip()
    ]
    if not declared or sorted(declared) != sorted(purpose.permitted_conditions):
        problems.append(
            f"the record's condition {governed.get('condition')!r} does not match "
            f"the purpose's permitted conditions {list(purpose.permitted_conditions)}"
        )

    if problems:
        return Prerequisite(
            "diagnostic_repetition_decision",
            BLOCKED,
            "; ".join(problems[:6]),
            DIAGNOSTIC_REPETITION_DECISION_INCONSISTENT,
        )
    subject = governed.get("task") or governed.get("tasks")
    return Prerequisite(
        "diagnostic_repetition_decision",
        PASS,
        f"{purpose.repetition_decision_id} pins {purpose.repetitions} independent "
        f"repetitions of {subject} under {governed.get('condition')} "
        "only, each on a fresh process and a fresh session with no resume, no "
        "continuation and no session reuse. No power, precision or "
        "treatment-effect claim attaches to the count, and no power calculation "
        "justifies it",
    )


def check_readiness(
    task_id: str,
    condition: str,
    run_purpose: str,
    *,
    repo: Path = REPO,
    private_root: Optional[Path] = None,
    context_verdict: Optional[str] = None,
) -> ReadinessReport:
    """Report, accurately, what is ready and what blocks the authorised run.

    ``context_verdict`` lets a caller pass a verdict it has already computed
    (the dry run does); when it is ``None`` the item is reported BLOCKED as
    *not demonstrated*, which is the fail-closed reading.

    Deliberately absent from the blocker list: ``TD-B34``, priority-B
    replication authoring and ``TD-B39``. SL-PT08-01 §8 records that none of
    them is a prerequisite for this diagnostic, and listing them here would
    re-impose a gate the adjudication removed.
    """
    purpose = resolve_run_purpose(run_purpose)
    assert_task_and_condition_permitted(purpose, task_id, condition)
    items: List[Prerequisite] = []

    # ---- PASS candidates -------------------------------------------------- #
    expected_sha = expected_task_sha256(task_id)
    body = public_task_path(task_id)
    actual_sha = pmw.sha256_file(body)
    if actual_sha == expected_sha:
        items.append(
            Prerequisite(
                "public_body_identity",
                PASS,
                f"{body.relative_to(repo).as_posix()} hashes {actual_sha}, matching "
                f"the approved TASK_INDEX.csv pin",
            )
        )
    else:
        items.append(
            Prerequisite(
                "public_body_identity",
                BLOCKED,
                f"body hashes {actual_sha}, index pins {expected_sha}",
                TASK_SHA_MISMATCH,
            )
        )

    items.append(_worktree_preparation_probe(task_id, condition))

    governed = governed_firewall_from_record(
        purpose.firewall_record_path(repo), purpose.firewall_heading
    )
    firewall_ok = str(governed.get("run_purpose", "")).upper() == purpose.name and all(
        governed.get(f) is False for f in FIREWALL_FIELDS
    )
    items.append(
        Prerequisite(
            "diagnostic_governance",
            PASS if firewall_ok else BLOCKED,
            (
                f"{purpose.decision_id} authorises {purpose.description}; the "
                f"firewall table in {purpose.firewall_record} pins "
                f"run_purpose={purpose.name} with all five eligibility flags "
                "false, and the runner re-derives them from it"
            )
            if firewall_ok
            else (
                f"the firewall table in {purpose.firewall_record} no longer "
                f"matches the runner: {governed}"
            ),
            None if firewall_ok else DIAGNOSTIC_FIREWALL_INCONSISTENT,
        )
    )

    linked, linkage_detail = private_linkage_records_task_sha(
        task_id, expected_sha, private_root
    )
    items.append(
        Prerequisite(
            "public_private_linkage",
            PASS if linked else BLOCKED,
            linkage_detail,
            None if linked else PRIVATE_LINKAGE_NOT_VERIFIABLE,
        )
    )

    corpus_ok, corpus_detail = private_architecture_corpus_available(
        task_id, private_root, purpose.corpus_script_for(task_id)
    )
    # SL-V2-EFF-ELIG-01. The exemption is evaluated for any purpose that names
    # one, whether or not the corpus happens to be present, so the report states
    # the validation as a fact rather than only when it is load-bearing. A
    # purpose that names none gets the pre-existing behaviour exactly.
    exemption_problems = (
        architecture_corpus_exemption_problems(purpose, task_id, private_root, repo)
        if purpose.architecture_corpus_exemption
        else ["no exemption authority"]
    )
    exempt = purpose.architecture_corpus_exemption is not None and not exemption_problems
    if corpus_ok:
        items.append(
            Prerequisite("architecture_corpus_availability", PASS, corpus_detail)
        )
    elif exempt:
        # NOT_APPLICABLE, never PASS. PASS would read as "the corpus exists" and
        # it does not; the requirement simply does not apply to this purpose, and
        # the corpus work is NOT done, NOT waived and NOT reduced in scope for
        # any purpose it does apply to.
        items.append(
            Prerequisite(
                "architecture_corpus_availability",
                NOT_APPLICABLE,
                (
                    f"NOT APPLICABLE TO {purpose.name}, and NOT RESOLVED. "
                    f"{corpus_detail}. "
                    f"{purpose.architecture_corpus_exemption} adjudicates that a "
                    "full per-task architecture mutation/corpus package is not a "
                    "run-eligibility prerequisite for this COST-ONLY purpose when "
                    "its eight pre-data conditions hold, and they hold and are "
                    "reported separately as pilot_architecture_validation. The "
                    "corpus requirement is UNCHANGED and REQUIRED in full "
                    "everywhere it already applied, including every confirmatory "
                    "and result-bearing purpose; this closes no gate, closes no "
                    "TD row and changes no E1 admission"
                ),
            )
        )
    else:
        items.append(
            Prerequisite(
                "architecture_corpus_availability",
                BLOCKED,
                corpus_detail
                + (
                    "; and "
                    f"{purpose.architecture_corpus_exemption}'s pilot-scoped "
                    "exemption does not apply: "
                    + "; ".join(exemption_problems[:4])
                    if purpose.architecture_corpus_exemption
                    else ""
                ),
                ARCHITECTURE_CORPUS_NOT_AVAILABLE,
            )
        )

    if purpose.architecture_corpus_exemption:
        items.append(
            Prerequisite(
                "pilot_architecture_validation",
                PASS if not exemption_problems else BLOCKED,
                (
                    f"{purpose.architecture_corpus_exemption}'s eight pre-data "
                    f"conditions are mechanically satisfied for {task_id}: hidden "
                    "functional acceptance is validated; a legal reference passes "
                    "it and scores SATISFIED on the single applicable target "
                    "opportunity with zero violations; a functionally correct "
                    "target-violating reference ALSO passes it; the architecture "
                    "scorer reports the exact declared target violation on that "
                    "reference; functional acceptance does not enforce "
                    "architecture; and this purpose is non-confirmatory, "
                    "non-result-bearing and pinned out of E1, treatment-effect "
                    "and power analysis"
                )
                if not exemption_problems
                else (
                    f"{purpose.architecture_corpus_exemption}'s conditions are not "
                    "satisfied: " + "; ".join(exemption_problems[:6])
                ),
                None
                if not exemption_problems
                else PILOT_ARCHITECTURE_VALIDATION_NOT_AVAILABLE,
            )
        )

    # ---- BLOCKED items ---------------------------------------------------- #
    selected = primary_model()
    pinned = diagnostic_primary_model(purpose.name)
    items.append(
        Prerequisite(
            "model_selection",
            PASS if (selected or pinned) else BLOCKED,
            f"MODEL_REGISTRY.yml primary_model is {selected!r}"
            if selected
            else (
                f"MODEL_REGISTRY.yml pins {pinned!r} for {purpose.name} only, "
                f"under {purpose.decision_id}; the global primary_model stays "
                "null and TD-B03 stays open, so this confers no confirmatory "
                "selection"
            )
            if pinned
            else "MODEL_REGISTRY.yml records primary_model: null; selection is a "
            "separate Study-Lead decision (TD-B03) and the runner never chooses "
            "a model or falls back to one",
            None if (selected or pinned) else PRIMARY_MODEL_NOT_SELECTED,
        )
    )

    if context_verdict == "CLEAN":
        items.append(
            Prerequisite(
                "clean_isolated_context",
                PASS,
                "context_audit.py returned CLEAN for this environment",
            )
        )
    else:
        code = {
            "CONTAMINATED": CONTEXT_AUDIT_CONTAMINATED,
            None: CONTEXT_AUDIT_UNKNOWN,
        }.get(context_verdict, CONTEXT_AUDIT_UNKNOWN)
        items.append(
            Prerequisite(
                "clean_isolated_context",
                BLOCKED,
                f"context-isolation verdict is {context_verdict or 'not demonstrated'}; "
                "a counted run requires CLEAN from context_audit.py in a governed "
                "isolated environment and identity (TD-B19)",
                code,
            )
        )

    validated = hidden_acceptance_is_validated(task_id)
    items.append(
        Prerequisite(
            "hidden_acceptance_validation",
            PASS if validated else BLOCKED,
            f"TASK_ACCEPTANCE_MATRIX.csv records {task_id} as validated"
            if validated
            else f"TASK_ACCEPTANCE_MATRIX.csv records {task_id}'s hidden acceptance "
            "as draft_unvalidated and status candidate-not-frozen "
            "(TD-B05/TD-B32); it must be authored, reference/mutation validated "
            "and independently reviewed before any scored run",
            None if validated else hidden_acceptance_refusal_code(task_id),
        )
    )

    freeze_state = manifest_freeze_state(
        task_id, condition=condition, run_purpose=purpose.name
    )
    frozen = bool(freeze_state["effective_for_this_purpose"])
    scoped = bool(freeze_state["diagnostic_frozen"])
    freeze_problems = freeze_state["diagnostic_freeze_problems"]
    items.append(
        Prerequisite(
            "manifest_freeze",
            PASS if frozen else BLOCKED,
            (
                f"{task_id}'s manifest is frozen suite-wide"
                if freeze_state["global_frozen"]
                else (
                    f"{freeze_state['diagnostic_freeze_authority']} grants "
                    f"{task_id}/{condition}/{purpose.name} a DIAGNOSTIC-SCOPED "
                    "freeze: the execution configuration is frozen for this "
                    "triple only. The suite-wide lifecycle freeze is NOT "
                    "granted, gate G1 is NOT passed, the suite is NOT frozen, "
                    f"and the public lifecycle row is unchanged. The runner "
                    "freezes nothing and writes no lifecycle state"
                )
            )
            if frozen
            else (
                f"{task_id}'s evaluator manifest is status=review and NOT frozen; "
                "a scored run requires the applicable manifest frozen under the "
                "existing lifecycle rules (TD-B05/TD-B14/TD-B32, gate G1), and "
                "no diagnostic-scoped freeze applies: "
                + "; ".join(f"<{p['code']}> {p['detail']}" for p in freeze_problems[:4])
                if freeze_problems
                else f"{task_id}'s evaluator manifest is status=review and NOT "
                "frozen, and no diagnostic-scoped freeze applies"
            ),
            None
            if frozen
            else (str(freeze_problems[0]["code"]) if freeze_problems else MANIFEST_NOT_FROZEN),
        )
    )

    # The suite-wide gate, reported explicitly so it can never be read as passed
    # by inference from the scoped freeze above. NOT_APPLICABLE, never PASS: the
    # gate is open, and SL-PT08-06 narrows its applicability rather than its bar.
    items.append(
        Prerequisite(
            "suite_wide_gate_g1",
            NOT_APPLICABLE if (scoped or freeze_state["global_frozen"]) else BLOCKED,
            (
                "the suite-wide lifecycle freeze is in force for this task, so "
                "the ordinary G1-governed path applies and no exception is used"
                if freeze_state["global_frozen"]
                else "NOT PASSED, and NOT APPLICABLE TO THIS DIAGNOSTIC. Gate G1 is a "
                "suite-wide oracle-validity gate over TD-B04/TD-B05/TD-B12 and "
                "remains open and blocking for every confirmatory purpose. "
                f"{freeze_state['diagnostic_freeze_authority']} narrows the "
                "APPLICABILITY of the G1 freeze prerequisite for "
                f"{task_id}/{condition}/{purpose.name} only. It does NOT pass "
                "G1, NOT close G1, NOT close TD-B34, NOT start priority B, NOT "
                "close the global TD-B32 row and NOT change TD-B12/G6. "
                "global_gate_g1_passed is false and suite_frozen is false"
                if scoped
                else "gate G1 is not passed and no diagnostic-scoped exception applies"
            ),
            SUITE_WIDE_G1_MUST_NOT_BE_CLAIMED if not scoped else None,
        )
    )

    synced, sync_detail = private_sync_prefreeze_state(task_id, private_root, repo)
    items.append(
        Prerequisite(
            "private_sync_propagation_before_freeze",
            PASS if synced else BLOCKED,
            sync_detail
            if synced
            else (
                "a public accounting synchronization must be propagated into the "
                f"private package before {task_id} may be frozen, scoped or "
                "otherwise, and the private record does not yet record it as "
                f"satisfied: {sync_detail}. The private repository is read-only "
                "here and this runner propagates nothing"
            ),
            None if synced else PRIVATE_PUBLIC_SYNC_PROPAGATION_REQUIRED_BEFORE_FREEZE,
        )
    )

    q1, q8, validated_cli = live_runtime_validation(purpose.name)
    live_ok = q1 == "PASS" and q8 == "PASS"
    missing = "+".join(
        code
        for code, ok in (
            (Q1_READBACK_NOT_VALIDATED_LIVE, q1 == "PASS"),
            (Q8_INVALID_MODEL_ID_NOT_VALIDATED_LIVE, q8 == "PASS"),
        )
        if not ok
    )
    items.append(
        Prerequisite(
            "q1_q8_live_runtime_validation",
            PASS if live_ok else BLOCKED,
            (
                "MODEL_EXECUTION_CONTROLS §7 Q1 and Q8 have both been exercised "
                f"against a LIVE runtime (CLI {validated_cli}) under SL-PT08-05: "
                "the readback resolved exactly one model id from system.init and "
                "modelUsage, and an unrecognised id was rejected with no model "
                "serving the request and nothing substituted"
            )
            if live_ok
            else (
                "MODEL_EXECUTION_CONTROLS §7 Q1 (resolved-model-id readback) and "
                "Q8 (invalid-model-id rejection) are dry-run blockers under "
                "TD-B21. The runner implements both validation paths and they "
                "have not both been exercised against a live runtime"
            ),
            None if live_ok else (missing or Q1_READBACK_NOT_VALIDATED_LIVE),
        )
    )

    # ---- SL-PT08-02: the schema this purpose's artifacts actually use ----- #
    schema_problems = artifact_schema_problems(purpose, repo)
    items.append(
        Prerequisite(
            "diagnostic_artifact_firewall",
            PASS if not schema_problems else BLOCKED,
            (
                f"{purpose.schema_decision_id} makes {purpose.artifact_schema} "
                f"the authoritative execution-record schema for "
                f"{purpose.name}, and that schema mechanically REQUIRES a "
                f"run_purpose block and pins all "
                f"{len(QUARANTINE_FIELDS)} quarantine fields "
                f"({', '.join(QUARANTINE_FIELDS)}) to false. An artifact that "
                "dropped the firewall could not validate"
            )
            if not schema_problems
            else (
                f"{purpose.artifact_schema} does not enforce the "
                f"{purpose.schema_decision_id} quarantine: "
                + "; ".join(schema_problems[:6])
            ),
            None if not schema_problems else DIAGNOSTIC_ARTIFACT_SCHEMA_LACKS_FIREWALL,
        )
    )

    # ---- the canonical gap: scoped out, never claimed resolved ------------- #
    canonical_ok = canonical_run_manifest_carries_firewall(repo)
    if purpose.result_bearing:
        # A result-bearing purpose is governed by the canonical schema in full,
        # and SL-PT08-02 waives nothing for it.
        items.append(
            Prerequisite(
                "canonical_confirmatory_run_manifest_firewall",
                PASS if canonical_ok else BLOCKED,
                "experiments/v2/schemas/run_manifest.schema.json enforces the "
                "quarantine fields"
                if canonical_ok
                else (
                    f"{purpose.name} is RESULT-BEARING, so the canonical "
                    "result-manifest schema governs its artifacts in full. "
                    "experiments/v2/schemas/run_manifest.schema.json sets "
                    "additionalProperties:false and carries none of the "
                    "quarantine fields, and SL-PT08-02 waives that for no "
                    "confirmatory or result-bearing run"
                ),
                None if canonical_ok else RUN_MANIFEST_SCHEMA_LACKS_DIAGNOSTIC_FIREWALL,
            )
        )
    else:
        items.append(
            Prerequisite(
                "canonical_confirmatory_run_manifest_firewall",
                NOT_APPLICABLE,
                (
                    "UNRESOLVED, and NOT APPLICABLE TO THIS DIAGNOSTIC. "
                    "experiments/v2/schemas/run_manifest.schema.json still sets "
                    "additionalProperties:false and still carries none of the "
                    "quarantine fields; that directory is byte-pinned by the "
                    "private evaluator's public linkage, so remediating it is a "
                    "linkage-relevant change no package here is authorised to "
                    f"make. {purpose.schema_decision_id} adjudicates only that "
                    f"{purpose.name} is a NON-RESULT purpose whose artifacts do "
                    "not validate against that schema, so the gap does not "
                    "apply to it. The gap is NOT fixed, NOT waived and NOT "
                    "reduced in scope, and it remains REQUIRED in full for "
                    "every future confirmatory / result-bearing run"
                )
                if not canonical_ok
                else (
                    "the canonical result-manifest schema now enforces the "
                    "quarantine fields; this diagnostic still does not validate "
                    "against it"
                ),
                RUN_MANIFEST_SCHEMA_LACKS_DIAGNOSTIC_FIREWALL if not canonical_ok else None,
            )
        )

    # ---- the repetition count, re-derived from the authorising record ------ #
    items.append(_repetition_decision_probe(purpose, repo))

    return ReadinessReport(
        purpose=purpose.name,
        task_id=task_id,
        condition=condition,
        prerequisites=items,
    )


#: Decisions that are explicitly NOT prerequisites for SL-PT08-01 (§8). Kept as
#: data so a test can prove none of them ever reaches the blocker list.
NON_PREREQUISITE_DECISIONS: Tuple[str, ...] = ("TD-B34", "TD-B39", "TD-B37", "SL-RUNID-01")
NON_PREREQUISITE_PHRASES: Tuple[str, ...] = ("priority b", "priority-b")
