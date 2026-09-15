#!/usr/bin/env python3
"""Efficiency measurement over Claude Code 2.1.229 structured output.

Everything here is derived from the runtime's OWN structured events. Nothing is
parsed out of model prose, because prose is the one channel a model can write
to deliberately: a run that narrates "I read 40 files" would otherwise be able
to report a different number from the one it caused.

The token definition, and the double-count that is avoided
----------------------------------------------------------
The terminal ``result`` event carries provider usage in two mirrored shapes.
``usage`` (snake_case) is authoritative and ``modelUsage`` (camelCase, keyed by
exact model id) mirrors it per model.

::

    TOTAL_INPUT_TOKENS = usage.input_tokens
                       + usage.cache_creation_input_tokens
                       + usage.cache_read_input_tokens

Those three categories are **non-overlapping**, which is what makes the sum a
total rather than an overstatement. ``usage.cache_creation`` is a nested
BREAKDOWN of ``cache_creation_input_tokens`` into
``ephemeral_1h_input_tokens`` and ``ephemeral_5m_input_tokens``; adding either
on top would count the same tokens twice, and
:data:`FORBIDDEN_USAGE_SUBCOMPONENTS` names them so a later reader cannot
"complete" the sum by adding them back.

Every input token counts: the MAD's, the cached MAD's, the task's and every
subsequent interaction's. That is the point of the measure. C4 is expected to
carry more input than C1 on the first request and the pilot exists to find out
what happens after that, so excluding the payload would be excluding the
treatment.

Failing closed
--------------
A run with no terminal ``result`` event, no ``usage`` block, or a ``usage``
block whose required fields are missing or non-integer is **invalid**, not
zero. Zero is a number a reader can average; "invalid" is not, and the
difference matters when the endpoint is a ratio.

No model is invoked by this module.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import run_governance as gov

#: The four authoritative usage fields, snake_case, from ``usage``.
REQUIRED_USAGE_FIELDS: Tuple[str, ...] = (
    "input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "output_tokens",
)

#: The three that make up ``TOTAL_INPUT_TOKENS``, in the order they are summed.
INPUT_TOKEN_FIELDS: Tuple[str, ...] = (
    "input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
)

#: Nested BREAKDOWN fields of ``cache_creation_input_tokens``. Never summed.
FORBIDDEN_USAGE_SUBCOMPONENTS: Tuple[str, ...] = (
    "cache_creation.ephemeral_1h_input_tokens",
    "cache_creation.ephemeral_5m_input_tokens",
)

#: Tool names, classified. Anything not named here is counted in
#: ``TOTAL_TOOL_CALLS`` and in ``other_calls``, never silently dropped.
READ_TOOLS: Tuple[str, ...] = ("Read",)
GREP_TOOLS: Tuple[str, ...] = ("Grep",)
GLOB_TOOLS: Tuple[str, ...] = ("Glob",)
BASH_TOOLS: Tuple[str, ...] = ("Bash",)
EDIT_TOOLS: Tuple[str, ...] = ("Edit",)
WRITE_TOOLS: Tuple[str, ...] = ("Write",)

#: Shell commands that count as running the test suite. Deliberately a small,
#: explicit list: a heuristic that tried to recognise "any command that probably
#: runs tests" would count differently for a model that phrased it differently,
#: and the measure would then be partly a measure of phrasing.
TEST_COMMAND_PATTERNS: Tuple[str, ...] = (
    r"(?<![\w:])npm\s+(?:run\s+)?test(?![\w:\-])",
    r"(?<![\w:])npx?\s+jest(?![\w:\-])",
    r"(?<![\w:])npx?\s+nx\s+test(?![\w:\-])",
    r"(?<![\w:])npx?\s+vitest(?![\w:\-])",
)

_TEST_RE = re.compile("|".join(TEST_COMMAND_PATTERNS))


class EfficiencyMetricsError(gov.RunnerRefusal):
    """Usage that cannot be read is invalid, never zero."""


# --------------------------------------------------------------------------- #
# Usage
# --------------------------------------------------------------------------- #
#: Where a usage figure came from. The distinction is load-bearing for reset
#: phase A, which is INTERRUPTED at the checkpoint and therefore never emits a
#: terminal ``result`` event to read usage from.
SOURCE_TERMINAL_RESULT = "terminal_result"
SOURCE_PER_MESSAGE_PARTIAL = "per_message_partial"


@dataclass(frozen=True)
class UsageTotals:
    """One process's provider usage, as the runtime reported it.

    ``output_tokens`` is ``Optional`` for one reason, established by measurement
    rather than assumed. Summing ``message.usage`` across the streamed
    ``assistant`` events reproduces all THREE input categories **exactly** —
    delta 0 on every one of the ten live artifacts checked, including the two
    infrastructure probes. It does NOT reproduce ``output_tokens``: the value
    attached to a streamed assistant message is the figure at message start,
    and summing it recovers about 1-2% of the terminal total (PT09 R1: 244
    against 20,917).

    So a stream that was interrupted before its terminal event yields an EXACT
    input total and NO output total. The output figure is reported as ``None``,
    never as the partial sum and never as zero, because a partial sum presented
    as a total would understate a secondary endpoint by two orders of magnitude.
    """

    input_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    output_tokens: Optional[int]
    cost_usd: Optional[float]
    model_id: Optional[str]
    source: str = SOURCE_TERMINAL_RESULT
    #: True when ``modelUsage`` was present AND agreed with ``usage``.
    model_usage_mirror_consistent: Optional[bool] = None
    mirror_detail: str = ""

    @property
    def total_input_tokens(self) -> int:
        return (
            self.input_tokens
            + self.cache_creation_input_tokens
            + self.cache_read_input_tokens
        )

    @property
    def total_output_tokens(self) -> Optional[int]:
        return self.output_tokens

    def to_dict(self) -> Dict[str, object]:
        return {
            "input_tokens": self.input_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "output_tokens": self.output_tokens,
            "TOTAL_INPUT_TOKENS": self.total_input_tokens,
            "TOTAL_OUTPUT_TOKENS": self.total_output_tokens,
            "cost_usd": self.cost_usd,
            "model_id": self.model_id,
            "source": self.source,
            "model_usage_mirror_consistent": self.model_usage_mirror_consistent,
            "mirror_detail": self.mirror_detail,
            "excluded_subcomponents": list(FORBIDDEN_USAGE_SUBCOMPONENTS),
        }

    def plus(self, other: "UsageTotals") -> "UsageTotals":
        """Aggregate two phases of one reset run.

        The two phases are two separate processes with two separate caches, so
        their totals are genuinely additive: nothing is shared between them that
        would be counted twice.

        An unavailable output total propagates. If phase A was interrupted, the
        reset run's ``TOTAL_OUTPUT_TOKENS`` is ``None`` rather than "phase B's
        output", because phase B's output is not the run's output.
        """
        both = [self.model_usage_mirror_consistent, other.model_usage_mirror_consistent]
        return UsageTotals(
            input_tokens=self.input_tokens + other.input_tokens,
            cache_creation_input_tokens=(
                self.cache_creation_input_tokens + other.cache_creation_input_tokens
            ),
            cache_read_input_tokens=(
                self.cache_read_input_tokens + other.cache_read_input_tokens
            ),
            output_tokens=(
                None
                if self.output_tokens is None or other.output_tokens is None
                else self.output_tokens + other.output_tokens
            ),
            cost_usd=(
                None
                if self.cost_usd is None or other.cost_usd is None
                else self.cost_usd + other.cost_usd
            ),
            model_id=self.model_id if self.model_id == other.model_id else None,
            source=(
                SOURCE_TERMINAL_RESULT
                if self.source == other.source == SOURCE_TERMINAL_RESULT
                else SOURCE_PER_MESSAGE_PARTIAL
            ),
            model_usage_mirror_consistent=(
                None if None in both else all(both)
            ),
            mirror_detail="aggregate of phase A and phase B",
        )


def terminal_result(events: Sequence[dict]) -> Optional[dict]:
    for event in reversed(list(events)):
        if isinstance(event, dict) and event.get("type") == "result":
            return event
    return None


def _int_field(usage: dict, key: str, where: str) -> int:
    value = usage.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise gov.RunnerRefusal(
            gov.EFFICIENCY_USAGE_MALFORMED,
            f"{where}: usage.{key} is {value!r}, not an integer; a run whose "
            "token accounting cannot be read is INVALID, never zero",
        )
    if value < 0:
        raise gov.RunnerRefusal(
            gov.EFFICIENCY_USAGE_MALFORMED,
            f"{where}: usage.{key} is negative ({value})",
        )
    return value


def extract_partial_usage(
    events: Sequence[dict], *, where: str = "interrupted phase"
) -> UsageTotals:
    """Input usage for a stream that was INTERRUPTED before its terminal event.

    Summed over the distinct streamed ``assistant`` messages. Distinct by
    ``message.id``, because one logical assistant message can appear more than
    once in the stream and adding it twice would inflate the primary endpoint.

    Only the input categories are returned. See :class:`UsageTotals` for why the
    output figure is withheld rather than summed.
    """
    totals = {f: 0 for f in INPUT_TOKEN_FIELDS}
    seen: List[str] = []
    for event in events:
        if not isinstance(event, dict) or event.get("type") != "assistant":
            continue
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        mid = message.get("id")
        if not isinstance(mid, str) or mid in seen:
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        seen.append(mid)
        for key in INPUT_TOKEN_FIELDS:
            value = usage.get(key, 0)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise gov.RunnerRefusal(
                    gov.EFFICIENCY_USAGE_MALFORMED,
                    f"{where}: message {mid} reports usage.{key}={value!r}; a "
                    "phase whose token accounting cannot be read is INVALID",
                )
            totals[key] += value
    if not seen:
        raise gov.RunnerRefusal(
            gov.EFFICIENCY_USAGE_MISSING,
            f"{where}: the interrupted stream carries no assistant message with "
            "a usage block, so not one token can be accounted for; the phase is "
            "invalid rather than free",
        )
    return UsageTotals(
        input_tokens=totals["input_tokens"],
        cache_creation_input_tokens=totals["cache_creation_input_tokens"],
        cache_read_input_tokens=totals["cache_read_input_tokens"],
        output_tokens=None,
        cost_usd=None,
        model_id=None,
        source=SOURCE_PER_MESSAGE_PARTIAL,
        model_usage_mirror_consistent=None,
        mirror_detail=(
            f"interrupted before the terminal result event; input reconstructed "
            f"exactly from {len(seen)} streamed assistant message(s), output and "
            "cost unavailable"
        ),
    )


def extract_usage(
    events: Sequence[dict], *, expected_model_id: Optional[str] = None,
    where: str = "run", allow_partial: bool = False,
) -> UsageTotals:
    """The authoritative usage for one process, failing closed on anything odd.

    ``allow_partial`` is set by exactly one caller — reset phase A, which is
    interrupted by design and so has no terminal event to read. It is NOT a
    general tolerance: a NON_RESET run or a phase B with no terminal event is
    still invalid, because for those the missing event means the process died
    rather than that it was stopped on purpose.
    """
    result = terminal_result(events)
    if result is None:
        if allow_partial:
            return extract_partial_usage(events, where=where)
        raise gov.RunnerRefusal(
            gov.EFFICIENCY_USAGE_MISSING,
            f"{where}: the event stream carries no terminal result event, so no "
            "usage was reported; the run is invalid rather than free",
        )
    usage = result.get("usage")
    if not isinstance(usage, dict):
        raise gov.RunnerRefusal(
            gov.EFFICIENCY_USAGE_MISSING,
            f"{where}: the terminal result event carries no usage block",
        )
    values = {k: _int_field(usage, k, where) for k in REQUIRED_USAGE_FIELDS}

    model_usage = result.get("modelUsage")
    model_id: Optional[str] = None
    consistent: Optional[bool] = None
    detail = "modelUsage absent; usage is authoritative and was used alone"
    if isinstance(model_usage, dict) and model_usage:
        keys = [k for k in model_usage if isinstance(k, str)]
        if expected_model_id and expected_model_id in model_usage:
            model_id = expected_model_id
        elif len(keys) == 1:
            model_id = keys[0]
        if model_id is not None:
            mirror = model_usage.get(model_id) or {}
            pairs = (
                ("inputTokens", "input_tokens"),
                ("cacheCreationInputTokens", "cache_creation_input_tokens"),
                ("cacheReadInputTokens", "cache_read_input_tokens"),
                ("outputTokens", "output_tokens"),
            )
            disagreements = [
                f"{camel}={mirror.get(camel)!r} vs usage.{snake}={values[snake]!r}"
                for camel, snake in pairs
                if isinstance(mirror.get(camel), int)
                and mirror.get(camel) != values[snake]
            ]
            consistent = not disagreements
            detail = (
                f"modelUsage[{model_id!r}] mirrors usage exactly"
                if consistent
                else "modelUsage disagrees with usage: " + "; ".join(disagreements[:4])
            )
        else:
            detail = (
                f"modelUsage names {sorted(keys)}; no single model could be "
                "identified, so only usage was read"
            )

    cost: Optional[float] = None
    if model_id is not None:
        raw = (model_usage or {}).get(model_id, {}).get("costUSD")
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            cost = float(raw)

    return UsageTotals(
        input_tokens=values["input_tokens"],
        cache_creation_input_tokens=values["cache_creation_input_tokens"],
        cache_read_input_tokens=values["cache_read_input_tokens"],
        output_tokens=values["output_tokens"],
        cost_usd=cost,
        model_id=model_id,
        source=SOURCE_TERMINAL_RESULT,
        model_usage_mirror_consistent=consistent,
        mirror_detail=detail,
    )


# --------------------------------------------------------------------------- #
# Tools and exploration
# --------------------------------------------------------------------------- #
def normalise_path(value: object) -> Optional[str]:
    """One spelling per file, so a repeated read is recognised as one.

    Windows makes this necessary rather than tidy: the same file legitimately
    appears as ``D:\\x\\y.ts``, ``D:/x/y.ts`` and ``d:\\X\\y.ts`` in one
    transcript, and counting those as three distinct files would make
    ``UNIQUE_FILES_READ`` a measure of how the model typed rather than of what
    it opened. Separators are unified, a drive letter is lower-cased, and a
    trailing separator is dropped. Case is otherwise PRESERVED, because the
    metric must not claim that two genuinely different names on a case-sensitive
    filesystem are one file.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("\\", "/")
    while "//" in text:
        text = text.replace("//", "/")
    if len(text) > 1 and text[1] == ":":
        text = text[0].lower() + text[1:]
    if len(text) > 1 and text.endswith("/"):
        text = text[:-1]
    return text


def parent_directory(path: str) -> Optional[str]:
    if "/" not in path:
        return None
    parent = path.rsplit("/", 1)[0]
    return parent or "/"


@dataclass
class ToolMetrics:
    """What the run DID, counted from the tool channel only."""

    total_tool_calls: int = 0
    read_calls: int = 0
    grep_calls: int = 0
    glob_calls: int = 0
    bash_calls: int = 0
    edit_calls: int = 0
    write_calls: int = 0
    other_calls: int = 0
    other_tool_names: List[str] = field(default_factory=list)
    unique_files_read: int = 0
    unique_files_modified: int = 0
    unique_directories_explored: int = 0
    repeated_file_reads: int = 0
    files_reedited: int = 0
    test_command_runs: int = 0
    ci_command_runs: int = 0
    failed_test_or_ci_cycles: int = 0
    tool_results_seen: int = 0
    errored_tool_results: int = 0

    @property
    def exploration_calls(self) -> int:
        return self.read_calls + self.grep_calls + self.glob_calls

    def to_dict(self) -> Dict[str, object]:
        return {
            "TOTAL_TOOL_CALLS": self.total_tool_calls,
            "READ_CALLS": self.read_calls,
            "GREP_CALLS": self.grep_calls,
            "GLOB_CALLS": self.glob_calls,
            "BASH_CALLS": self.bash_calls,
            "EDIT_CALLS": self.edit_calls,
            "WRITE_CALLS": self.write_calls,
            "OTHER_CALLS": self.other_calls,
            "other_tool_names": sorted(set(self.other_tool_names)),
            "EXPLORATION_CALLS": self.exploration_calls,
            "UNIQUE_FILES_READ": self.unique_files_read,
            "UNIQUE_FILES_MODIFIED": self.unique_files_modified,
            "UNIQUE_DIRECTORIES_EXPLORED": self.unique_directories_explored,
            "REPEATED_FILE_READS": self.repeated_file_reads,
            "FILES_REEDITED": self.files_reedited,
            "TEST_COMMAND_RUNS": self.test_command_runs,
            "CI_COMMAND_RUNS": self.ci_command_runs,
            "FAILED_TEST_OR_CI_CYCLES": self.failed_test_or_ci_cycles,
            "tool_results_seen": self.tool_results_seen,
            "errored_tool_results": self.errored_tool_results,
        }


def _blocks(event: dict) -> Sequence[dict]:
    message = event.get("message")
    if not isinstance(message, dict):
        return ()
    content = message.get("content")
    if not isinstance(content, list):
        return ()
    return [b for b in content if isinstance(b, dict)]


def extract_tool_metrics(
    events: Sequence[dict], *, ci_command: str = "npm run ci:agent"
) -> ToolMetrics:
    """Count tool activity from ``tool_use``/``tool_result`` blocks only."""
    ci_re = re.compile(
        r"(?<![\w:])" + r"\s+".join(re.escape(p) for p in ci_command.split())
        + r"(?![\w:\-])"
    )
    metrics = ToolMetrics()
    read_counts: Dict[str, int] = {}
    edit_counts: Dict[str, int] = {}
    directories: set = set()
    validation_uses: Dict[str, str] = {}

    for event in events:
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        if kind == "assistant":
            for block in _blocks(event):
                if block.get("type") != "tool_use":
                    continue
                name = block.get("name")
                tool_use_id = block.get("id")
                payload = block.get("input") if isinstance(block.get("input"), dict) else {}
                metrics.total_tool_calls += 1

                if name in READ_TOOLS:
                    metrics.read_calls += 1
                    path = normalise_path(payload.get("file_path"))
                    if path:
                        read_counts[path] = read_counts.get(path, 0) + 1
                        parent = parent_directory(path)
                        if parent:
                            directories.add(parent)
                elif name in GREP_TOOLS:
                    metrics.grep_calls += 1
                    scope = normalise_path(payload.get("path"))
                    if scope:
                        directories.add(scope)
                elif name in GLOB_TOOLS:
                    metrics.glob_calls += 1
                    scope = normalise_path(payload.get("path"))
                    if scope:
                        directories.add(scope)
                elif name in EDIT_TOOLS:
                    metrics.edit_calls += 1
                    path = normalise_path(payload.get("file_path"))
                    if path:
                        edit_counts[path] = edit_counts.get(path, 0) + 1
                elif name in WRITE_TOOLS:
                    metrics.write_calls += 1
                    path = normalise_path(payload.get("file_path"))
                    if path:
                        edit_counts[path] = edit_counts.get(path, 0) + 1
                elif name in BASH_TOOLS:
                    metrics.bash_calls += 1
                    command = payload.get("command")
                    if isinstance(command, str):
                        is_ci = bool(ci_re.search(command))
                        is_test = bool(_TEST_RE.search(command))
                        if is_ci:
                            metrics.ci_command_runs += 1
                        if is_test:
                            metrics.test_command_runs += 1
                        if (is_ci or is_test) and isinstance(tool_use_id, str):
                            validation_uses[tool_use_id] = command
                else:
                    metrics.other_calls += 1
                    if isinstance(name, str):
                        metrics.other_tool_names.append(name)
        elif kind == "user":
            for block in _blocks(event):
                if block.get("type") != "tool_result":
                    continue
                metrics.tool_results_seen += 1
                errored = bool(block.get("is_error"))
                if errored:
                    metrics.errored_tool_results += 1
                tool_use_id = block.get("tool_use_id")
                # A validation cycle counts as FAILED when its own tool result
                # says so. The result CONTENT is not searched for words like
                # "failing": that would make the count depend on the wording of
                # someone else's test reporter, and a reporter that changed its
                # phrasing would silently change the measurement.
                if errored and isinstance(tool_use_id, str) and tool_use_id in validation_uses:
                    metrics.failed_test_or_ci_cycles += 1

    metrics.unique_files_read = len(read_counts)
    metrics.unique_files_modified = len(edit_counts)
    metrics.unique_directories_explored = len(directories)
    metrics.repeated_file_reads = sum(max(0, n - 1) for n in read_counts.values())
    metrics.files_reedited = sum(1 for n in edit_counts.values() if n > 1)
    return metrics


def combine_tool_metrics(a: ToolMetrics, b: ToolMetrics) -> ToolMetrics:
    """Aggregate two phases.

    The COUNT metrics add. The UNIQUE metrics are reported as the sum too, and
    that is stated rather than hidden: the two phases are separate processes
    whose transcripts this function does not hold, so it cannot know that a file
    read in both was one file. A caller wanting a true cross-phase unique count
    must use :func:`extract_tool_metrics` over the concatenated streams, which
    :func:`aggregate_reset` does.
    """
    merged = ToolMetrics(
        total_tool_calls=a.total_tool_calls + b.total_tool_calls,
        read_calls=a.read_calls + b.read_calls,
        grep_calls=a.grep_calls + b.grep_calls,
        glob_calls=a.glob_calls + b.glob_calls,
        bash_calls=a.bash_calls + b.bash_calls,
        edit_calls=a.edit_calls + b.edit_calls,
        write_calls=a.write_calls + b.write_calls,
        other_calls=a.other_calls + b.other_calls,
        other_tool_names=list(a.other_tool_names) + list(b.other_tool_names),
        unique_files_read=a.unique_files_read + b.unique_files_read,
        unique_files_modified=a.unique_files_modified + b.unique_files_modified,
        unique_directories_explored=(
            a.unique_directories_explored + b.unique_directories_explored
        ),
        repeated_file_reads=a.repeated_file_reads + b.repeated_file_reads,
        files_reedited=a.files_reedited + b.files_reedited,
        test_command_runs=a.test_command_runs + b.test_command_runs,
        ci_command_runs=a.ci_command_runs + b.ci_command_runs,
        failed_test_or_ci_cycles=a.failed_test_or_ci_cycles + b.failed_test_or_ci_cycles,
        tool_results_seen=a.tool_results_seen + b.tool_results_seen,
        errored_tool_results=a.errored_tool_results + b.errored_tool_results,
    )
    return merged


# --------------------------------------------------------------------------- #
# Timing
# --------------------------------------------------------------------------- #
@dataclass
class Timing:
    """Durations, all from monotonic clocks taken by the runner itself.

    ``MODEL_WALL_SECONDS`` is the time a MODEL PROCESS was running, and nothing
    else. For a reset run it is phase A plus phase B: the handoff between them —
    tearing down one sterile profile, building another, running the second
    context audit — is harness work, and charging it to the model would make
    the reset arm look slower by an amount that depends on how fast this
    harness is.
    """

    phase_a_seconds: Optional[float] = None
    phase_b_seconds: Optional[float] = None
    reset_handoff_seconds: Optional[float] = None
    total_run_seconds: Optional[float] = None
    evaluation_seconds: Optional[float] = None

    @property
    def model_wall_seconds(self) -> Optional[float]:
        parts = [p for p in (self.phase_a_seconds, self.phase_b_seconds) if p is not None]
        return round(sum(parts), 3) if parts else None

    def to_dict(self) -> Dict[str, object]:
        return {
            "MODEL_WALL_SECONDS": self.model_wall_seconds,
            "phase_a_model_seconds": (
                None if self.phase_a_seconds is None else round(self.phase_a_seconds, 3)
            ),
            "phase_b_model_seconds": (
                None if self.phase_b_seconds is None else round(self.phase_b_seconds, 3)
            ),
            "RESET_HANDOFF_SECONDS": (
                None
                if self.reset_handoff_seconds is None
                else round(self.reset_handoff_seconds, 3)
            ),
            "TOTAL_RUN_SECONDS": (
                None if self.total_run_seconds is None else round(self.total_run_seconds, 3)
            ),
            "EVALUATION_SECONDS": (
                None if self.evaluation_seconds is None else round(self.evaluation_seconds, 3)
            ),
        }


# --------------------------------------------------------------------------- #
# Turns
# --------------------------------------------------------------------------- #
def turns_used(events: Sequence[dict]) -> int:
    """Agentic turns actually taken: distinct assistant message ids.

    Derived rather than read from ``result.num_turns``, because that field
    means two different things. On a ``success`` result it counts user
    messages. On an ``error_max_turns`` result it is the index of the turn whose
    completion tripped the ceiling, which is ``max_turns + 1`` — observed
    exactly, ``num_turns: 2`` for ``--max-turns 1`` against a single model
    request. Reporting either as "turns used" would be wrong in one of the two
    cases, so neither is.
    """
    seen: List[str] = []
    for event in events:
        if not isinstance(event, dict) or event.get("type") != "assistant":
            continue
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        mid = message.get("id")
        if isinstance(mid, str) and mid and mid not in seen:
            seen.append(mid)
    return len(seen)


def hit_turn_ceiling(events: Sequence[dict]) -> bool:
    return (terminal_result(events) or {}).get("subtype") == "error_max_turns"


# --------------------------------------------------------------------------- #
# The whole measurement
# --------------------------------------------------------------------------- #
@dataclass
class EfficiencyMeasurement:
    """One observation's efficiency block, phases preserved beside the total."""

    reset_state: str
    usage: UsageTotals
    tools: ToolMetrics
    timing: Timing
    turns: int
    hit_ceiling: bool
    phases: Dict[str, Dict[str, object]] = field(default_factory=dict)
    unknown_event_types: List[str] = field(default_factory=list)
    event_count: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "reset_state": self.reset_state,
            "event_count": self.event_count,
            "TURNS_USED": self.turns,
            "hit_turn_ceiling": self.hit_ceiling,
            "usage": self.usage.to_dict(),
            "tools": self.tools.to_dict(),
            "timing": self.timing.to_dict(),
            "phases": self.phases,
            # Preserved, never dropped: an event type this harness does not
            # recognise is the runtime telling us something we have not modelled,
            # and silently discarding it would make the next schema change
            # invisible.
            "unknown_event_types": sorted(set(self.unknown_event_types)),
        }


#: Event types this harness models. Anything else is preserved and reported.
KNOWN_EVENT_TYPES: Tuple[str, ...] = (
    "system",
    "assistant",
    "user",
    "result",
    "stream_event",
    "rate_limit_event",
)


def unknown_event_types(events: Sequence[dict]) -> List[str]:
    return sorted(
        {
            str(e.get("type"))
            for e in events
            if isinstance(e, dict) and e.get("type") not in KNOWN_EVENT_TYPES
        }
    )


def measure_non_reset(
    events: Sequence[dict],
    *,
    model_id: Optional[str] = None,
    ci_command: str = "npm run ci:agent",
    timing: Optional[Timing] = None,
) -> EfficiencyMeasurement:
    usage = extract_usage(events, expected_model_id=model_id, where="NON_RESET")
    tools = extract_tool_metrics(events, ci_command=ci_command)
    return EfficiencyMeasurement(
        reset_state="NON_RESET",
        usage=usage,
        tools=tools,
        timing=timing or Timing(),
        turns=turns_used(events),
        hit_ceiling=hit_turn_ceiling(events),
        unknown_event_types=unknown_event_types(events),
        event_count=len(events),
    )


def aggregate_reset(
    phase_a: Sequence[dict],
    phase_b: Sequence[dict],
    *,
    model_id: Optional[str] = None,
    ci_command: str = "npm run ci:agent",
    timing: Optional[Timing] = None,
) -> EfficiencyMeasurement:
    """A reset run's measurement: phases aggregated, and phases preserved.

    The aggregate tool metrics are computed over the CONCATENATED streams rather
    than by adding the two phase results, so a file read in both phases counts
    once in ``UNIQUE_FILES_READ``. The per-phase blocks are kept alongside, so
    the recovery question — what did phase B have to redo? — is answerable.
    """
    # Phase A is interrupted BY DESIGN, so a missing terminal event is expected
    # there and only there. Phase B is not interrupted and is held to the full
    # standard: a phase B with no terminal event died, and a run whose second
    # half died is invalid.
    usage_a = extract_usage(
        phase_a, expected_model_id=model_id, where="RESET phase A", allow_partial=True
    )
    usage_b = extract_usage(phase_b, expected_model_id=model_id, where="RESET phase B")
    tools_a = extract_tool_metrics(phase_a, ci_command=ci_command)
    tools_b = extract_tool_metrics(phase_b, ci_command=ci_command)
    combined_events = list(phase_a) + list(phase_b)
    return EfficiencyMeasurement(
        reset_state="RESET",
        usage=usage_a.plus(usage_b),
        tools=extract_tool_metrics(combined_events, ci_command=ci_command),
        timing=timing or Timing(),
        turns=turns_used(phase_a) + turns_used(phase_b),
        hit_ceiling=hit_turn_ceiling(phase_a) or hit_turn_ceiling(phase_b),
        phases={
            "A": {
                "usage": usage_a.to_dict(),
                "tools": tools_a.to_dict(),
                "TURNS_USED": turns_used(phase_a),
                "hit_turn_ceiling": hit_turn_ceiling(phase_a),
                "event_count": len(phase_a),
            },
            "B": {
                "usage": usage_b.to_dict(),
                "tools": tools_b.to_dict(),
                "TURNS_USED": turns_used(phase_b),
                "hit_turn_ceiling": hit_turn_ceiling(phase_b),
                "event_count": len(phase_b),
            },
        },
        unknown_event_types=unknown_event_types(combined_events),
        event_count=len(combined_events),
    )
