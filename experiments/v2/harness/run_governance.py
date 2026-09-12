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
PRIVATE_PUBLIC_SYNC_PROPAGATION_REQUIRED_BEFORE_FREEZE = (
    "PRIVATE_PUBLIC_SYNC_PROPAGATION_REQUIRED_BEFORE_FREEZE"
)
PRIVATE_LINKAGE_NOT_VERIFIABLE = "PRIVATE_LINKAGE_NOT_VERIFIABLE"
ARCHITECTURE_CORPUS_NOT_AVAILABLE = "ARCHITECTURE_CORPUS_NOT_AVAILABLE"
ISOLATED_ENVIRONMENT_NOT_VERIFIED = "ISOLATED_ENVIRONMENT_NOT_VERIFIED"

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

    def firewall_flags(self) -> Dict[str, bool]:
        return dict(self.firewall)

    def artifact_schema_path(self, repo: Path = REPO) -> Path:
        return Path(repo) / self.artifact_schema


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


def governed_firewall_from_record(path: Path = DIAGNOSTIC_RECORD) -> Dict[str, object]:
    """Re-derive the firewall table from the governance record itself.

    The runner's constants are not trusted on their own: this reads §9's table
    out of ``PT08_C1_DIFFICULTY_DIAGNOSTIC_DECISION.md`` so a drift between the
    code and the adjudication is a mechanical failure rather than a reading.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"cannot read {path}: {exc}"
        ) from exc
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
    path: Path = EXECUTION_DECISIONS_RECORD,
) -> Dict[str, object]:
    """Re-derive ``SL-PT08-02``/``SL-PT08-03``'s tables from the record itself.

    Same discipline as :func:`governed_firewall_from_record`: the runner's
    constants are not trusted on their own, so a drift between the code and the
    adjudication is a mechanical failure rather than a reading.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise RunnerRefusal(
            GOVERNANCE_RECORD_UNREADABLE, f"cannot read {path}: {exc}"
        ) from exc
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
    task_id: str, private_root: Optional[Path] = None
) -> Tuple[bool, str]:
    """Read-only availability check for the task-specific architecture corpus."""
    root = Path(private_root) if private_root else default_private_root()
    corpus = root / "scripts" / f"{task_id.lower()}_corpus.py"
    spec = root / "spec" / "pilot_spec.py"
    if not corpus.is_file() or not spec.is_file():
        return False, f"the {task_id} architecture corpus is not available under {root}"
    return True, (
        f"{corpus.relative_to(root).as_posix()} and "
        f"{spec.relative_to(root).as_posix()} are present (read-only)"
    )


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


def _worktree_preparation_probe(task_id: str, condition: str) -> Prerequisite:
    """Prepare the governed worktree into a throwaway directory and discard it."""
    tmp = Path(tempfile.mkdtemp(prefix="afci-v2-readiness-"))
    try:
        result = pmw.prepare_model_worktree(
            pmw.PreparationRequest(
                condition=condition,
                source_root=REPO,
                dest_root=tmp / "worktree",
                task_path=public_task_path(task_id),
                task_id=task_id,
            )
        )
        delivery = result.manifest["architecture_delivery"]
        if delivery != "none":
            return Prerequisite(
                "c1_worktree_preparation",
                BLOCKED,
                f"architecture_delivery is {delivery!r}",
                ARCHITECTURE_DELIVERY_VIOLATION,
            )
        return Prerequisite(
            "c1_worktree_preparation",
            PASS,
            f"{condition} worktree prepares cleanly: "
            f"{result.manifest['entry_count']} allowlisted files, "
            f"architecture_delivery=none, content_hash "
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


def _repetition_decision_probe(purpose: RunPurpose) -> Prerequisite:
    """Check the runner's repetition constant against the governance record.

    Reports BLOCKED on any disagreement rather than preferring either side: a
    sample size the code and the adjudication do not agree on is not a governed
    sample size at all.
    """
    try:
        governed = governed_execution_decisions()
    except RunnerRefusal as exc:
        return Prerequisite(
            "diagnostic_repetition_decision", BLOCKED, exc.message, exc.code
        )

    problems: List[str] = []
    recorded = governed.get("diagnostic_repetitions")
    if recorded != purpose.repetitions:
        problems.append(
            f"the record pins diagnostic_repetitions={recorded!r} but the runner "
            f"carries {purpose.repetitions!r}"
        )
    for key, expected in REPETITION_PINS:
        if governed.get(key) != expected:
            problems.append(f"{key} is {governed.get(key)!r}, not {expected!r}")
    if governed.get("condition") not in purpose.permitted_conditions:
        problems.append(
            f"the record's condition {governed.get('condition')!r} is outside the "
            f"purpose's permitted conditions {list(purpose.permitted_conditions)}"
        )

    if problems:
        return Prerequisite(
            "diagnostic_repetition_decision",
            BLOCKED,
            "; ".join(problems[:6]),
            DIAGNOSTIC_REPETITION_DECISION_INCONSISTENT,
        )
    return Prerequisite(
        "diagnostic_repetition_decision",
        PASS,
        f"{purpose.repetition_decision_id} pins {purpose.repetitions} independent "
        f"repetitions of {governed.get('task')} under {governed.get('condition')} "
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

    governed = governed_firewall_from_record()
    firewall_ok = governed.get("run_purpose", "").upper() == purpose.name and all(
        governed.get(f) is False for f in FIREWALL_FIELDS
    )
    items.append(
        Prerequisite(
            "diagnostic_governance",
            PASS if firewall_ok else BLOCKED,
            (
                f"{purpose.decision_id} authorises {purpose.description}; the §9 "
                f"firewall table pins run_purpose={purpose.name} with all five "
                "eligibility flags false, and the runner re-derives them from it"
            )
            if firewall_ok
            else f"the §9 firewall table no longer matches the runner: {governed}",
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
        task_id, private_root
    )
    items.append(
        Prerequisite(
            "architecture_corpus_availability",
            PASS if corpus_ok else BLOCKED,
            corpus_detail,
            None if corpus_ok else ARCHITECTURE_CORPUS_NOT_AVAILABLE,
        )
    )

    # ---- BLOCKED items ---------------------------------------------------- #
    selected = primary_model()
    items.append(
        Prerequisite(
            "model_selection",
            PASS if selected else BLOCKED,
            f"MODEL_REGISTRY.yml primary_model is {selected!r}"
            if selected
            else "MODEL_REGISTRY.yml records primary_model: null; selection is a "
            "separate Study-Lead decision (TD-B03) and the runner never chooses "
            "a model or falls back to one",
            None if selected else PRIMARY_MODEL_NOT_SELECTED,
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

    frozen = manifest_is_frozen(task_id)
    items.append(
        Prerequisite(
            "manifest_freeze",
            PASS if frozen else BLOCKED,
            f"{task_id}'s manifest is frozen"
            if frozen
            else f"{task_id}'s evaluator manifest is status=review and NOT frozen; "
            "a scored run requires the applicable manifest frozen under the "
            "existing lifecycle rules (TD-B05/TD-B14/TD-B32, gate G1). The "
            "runner reports this and freezes nothing",
            None if frozen else MANIFEST_NOT_FROZEN,
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
                "the now-closed public accounting synchronization (PT08-PUB-P2-2) "
                "still requires a separate private propagation before PT08's "
                "freeze, and the private record does not yet record it as "
                f"satisfied: {sync_detail}. The private repository is read-only "
                "here and this runner propagates nothing"
            ),
            None if synced else PRIVATE_PUBLIC_SYNC_PROPAGATION_REQUIRED_BEFORE_FREEZE,
        )
    )

    items.append(
        Prerequisite(
            "q1_q8_live_runtime_validation",
            BLOCKED,
            "MODEL_EXECUTION_CONTROLS §7 Q1 (resolved-model-id readback) and Q8 "
            "(invalid-model-id rejection) are dry-run blockers under TD-B21. The "
            "runner implements both validation paths and neither has been "
            "exercised against a live runtime",
            f"{Q1_READBACK_NOT_VALIDATED_LIVE}+{Q8_INVALID_MODEL_ID_NOT_VALIDATED_LIVE}",
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

    # ---- SL-PT08-03: the repetition count, re-derived from the record ------ #
    items.append(_repetition_decision_probe(purpose))

    return ReadinessReport(
        purpose=purpose.name,
        task_id=task_id,
        condition=condition,
        prerequisites=items,
    )


#: Decisions that are explicitly NOT prerequisites for SL-PT08-01 (§8). Kept as
#: data so a test can prove none of them ever reaches the blocker list.
NON_PREREQUISITE_DECISIONS: Tuple[str, ...] = ("TD-B34", "TD-B39", "TD-B37", "TD-B41")
NON_PREREQUISITE_PHRASES: Tuple[str, ...] = ("priority b", "priority-b")
