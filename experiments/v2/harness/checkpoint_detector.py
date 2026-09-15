#!/usr/bin/env python3
"""The reset checkpoint detector: ``SL-V2-EFF-CHK-01``'s predicate, executed.

The predicate, quoted
---------------------
``SL-V2-EFF-CHK-01`` selected, pre-data, the same already-authored predicate for
all three pilot instruments:

    The first agent-initiated ``npm run ci:agent`` invocation after at least one
    implementation edit to the working tree.

This module executes exactly that sentence and nothing else. It authors no
predicate, relaxes none, and has no per-task variant: ``PT01``, ``PT04`` and
``PT07`` are detected by the same function over the same inputs.

What the detector may look at
-----------------------------
A deliberately tiny allowlist of structured fields:

* an event's ``type``;
* inside an assistant message, a ``tool_use`` block's ``name``, ``id`` and — for
  ``Bash`` only — ``input.command``;
* inside a user message, a ``tool_result`` block's ``tool_use_id`` and
  ``is_error``.

That is the whole surface. :data:`READABLE_FIELDS` states it as data and
:func:`readable_fields` returns it, so the restriction is testable rather than
merely intended.

What the detector may NOT look at, and why
------------------------------------------
* **The architecture score.** It is produced out of band, after the run, by the
  private oracle. If the stop boundary could see it, the reset would be applied
  at a point that depends on how architecturally good the work was — which is
  the treatment, so the reset would be confounded with it.
* **The hidden functional result.** Same reason, and it does not exist during
  the run either.
* **Model prose.** A model that wrote "I am about to run CI" would move the
  checkpoint. The predicate is about what the agent DID, observed through the
  tool channel, not about what it said.
* **The condition.** ``C1`` and ``C4`` are detected identically. The detector is
  not given the condition and has nowhere to put it.

The detector is also **invisible to the model**: it observes a stream the
runtime is emitting anyway, injects nothing, and answers no question the model
can ask.

Why the stop waits for the tool RESULT
--------------------------------------
The naive reading of "the first ``npm run ci:agent`` invocation" is the
``tool_use`` block — the moment the agent *asks* for the command. Stopping there
would terminate the process while ``npm`` and its children were mid-flight,
leaving a half-written build tree and a genuinely ambiguous worktree, and the
"partially modified repository" the reset protocol preserves would be partially
modified by an interrupted build rather than by the model.

So the checkpoint becomes true when the structured evidence shows the matching
``Bash`` invocation has **COMPLETED and returned its tool result**. The
``tool_use`` is recorded as the *trigger* and the ``tool_result`` as the
*boundary*; both indices are kept, so a reader can see that the predicate became
true at one point and the process was stopped at the next safe one.

No model is invoked by this module.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

#: The predicate, quoted VERBATIM from ``SL-V2-EFF-CHK-01``. A drift between
#: this string and the private record is a refusal, not a paraphrase.
FALLBACK_CHECKPOINT_PREDICATE = (
    "The first agent-initiated `npm run ci:agent` invocation after at least one "
    "implementation edit to the working tree."
)

#: The checkpoint identity. One id for all three instruments, because one
#: predicate is used for all three.
CHECKPOINT_ID = "CK-EFF-FALLBACK-CI-AGENT-AFTER-EDIT"

#: The authority that SELECTED this predicate (it did not author it).
CHECKPOINT_AUTHORITY = "SL-V2-EFF-CHK-01"

#: The instruments the selection covers.
CHECKPOINT_TASKS: Tuple[str, ...] = ("PT01", "PT04", "PT07")

#: Tool names whose successful completion counts as "an implementation edit to
#: the working tree".
#:
#: Defined by TOOL IDENTITY, never by inspecting a path. A path-based rule would
#: have to say which files are "implementation", and any such list either names
#: layers — which would make the checkpoint presuppose an architecture and
#: advantage the guided arm (``CRITICAL_DESIGN_DECISIONS.md`` D7) — or is
#: arbitrary. Tool identity is condition-neutral by construction.
#:
#: ``Bash`` is deliberately absent even though a shell command can write files.
#: Detecting that would mean parsing command text and guessing at effects; the
#: predicate is executed over what the tool channel states, not over what a
#: command might have done.
EDIT_TOOLS: Tuple[str, ...] = ("Edit", "Write")

#: The one CI surface a coding repetition may see (``TD-B16``). Supplied by the
#: caller from ``run_governance.visible_ci_command``; restated here only as the
#: default so the module is usable standalone in a test.
DEFAULT_CI_COMMAND = "npm run ci:agent"

#: Exactly what this detector is permitted to read. Asserted by test, not just
#: documented.
READABLE_FIELDS: Tuple[str, ...] = (
    "type",
    "message.content[].type",
    "message.content[].name",
    "message.content[].id",
    "message.content[].input.command",
    "message.content[].tool_use_id",
    "message.content[].is_error",
)

def readable_fields() -> Tuple[str, ...]:
    return READABLE_FIELDS


def ci_command_pattern(ci_command: str = DEFAULT_CI_COMMAND) -> "re.Pattern[str]":
    """A whole-invocation matcher for the governed CI command.

    Loose enough to survive the shapes a model actually types — a redirect
    (``npm run ci:agent 2>&1``), a prefix (``cd app && npm run ci:agent``),
    irregular spacing — and tight enough that a DIFFERENT command never matches.
    ``npm run ci``, ``npm test`` and ``npm run ci:agent:watch`` are all rejected:
    the trailing guard refuses a word character, a hyphen or a further ``:``.
    """
    parts = [re.escape(p) for p in ci_command.split()]
    body = r"\s+".join(parts)
    return re.compile(rf"(?<![\w:]){body}(?![\w:\-])")


@dataclass
class CheckpointEvidence:
    """Everything the run record needs to justify where it stopped."""

    checkpoint_id: str = CHECKPOINT_ID
    authority: str = CHECKPOINT_AUTHORITY
    predicate: str = FALLBACK_CHECKPOINT_PREDICATE
    implementation_edit_seen: bool = False
    implementation_edit_tool: Optional[str] = None
    implementation_edit_event_index: Optional[int] = None
    matching_ci_agent_tool_use_id: Optional[str] = None
    matching_ci_agent_event_index: Optional[int] = None
    matching_ci_agent_result_seen: bool = False
    checkpoint_reached: bool = False
    checkpoint_event_index: Optional[int] = None
    checkpoint_timestamp: Optional[str] = None
    #: Every completed edit, in order. Recorded for audit; the predicate needs
    #: only the first.
    completed_edit_tool_use_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "authority": self.authority,
            "predicate": self.predicate,
            "implementation_edit_seen": self.implementation_edit_seen,
            "implementation_edit_tool": self.implementation_edit_tool,
            "implementation_edit_event_index": self.implementation_edit_event_index,
            "matching_ci_agent_tool_use_id": self.matching_ci_agent_tool_use_id,
            "matching_ci_agent_event_index": self.matching_ci_agent_event_index,
            "matching_ci_agent_result_seen": self.matching_ci_agent_result_seen,
            "checkpoint_reached": self.checkpoint_reached,
            "checkpoint_event_index": self.checkpoint_event_index,
            "checkpoint_timestamp": self.checkpoint_timestamp,
            "completed_edit_count": len(self.completed_edit_tool_use_ids),
        }


def _content_blocks(event: dict) -> Sequence[dict]:
    message = event.get("message")
    if not isinstance(message, dict):
        return ()
    content = message.get("content")
    if not isinstance(content, list):
        return ()
    return [b for b in content if isinstance(b, dict)]


class CiAgentAfterEditDetector:
    """Execute ``SL-V2-EFF-CHK-01``'s predicate over a live event stream.

    Stateful and single-use: feed it every event in order via :meth:`observe`
    and it answers, once, that the checkpoint has just become true. It never
    un-reaches a checkpoint and never reaches one twice.
    """

    def __init__(
        self,
        *,
        ci_command: str = DEFAULT_CI_COMMAND,
        checkpoint_id: str = CHECKPOINT_ID,
        predicate: str = FALLBACK_CHECKPOINT_PREDICATE,
    ) -> None:
        self.ci_command = ci_command
        self._pattern = ci_command_pattern(ci_command)
        self.evidence = CheckpointEvidence(
            checkpoint_id=checkpoint_id, predicate=predicate
        )
        #: tool_use ids of Edit/Write calls whose result has not arrived yet.
        self._pending_edits: Dict[str, str] = {}

    # -- introspection ---------------------------------------------------- #
    @property
    def reached(self) -> bool:
        return self.evidence.checkpoint_reached

    def to_dict(self) -> Dict[str, object]:
        return self.evidence.to_dict()

    # -- the predicate ---------------------------------------------------- #
    def observe(self, index: int, event: dict) -> bool:
        """Feed one event. Return True on the event that MAKES the checkpoint true.

        Returns True exactly once, on the ``tool_result`` event that closes the
        first ``npm run ci:agent`` invocation issued after at least one completed
        implementation edit. Every later event returns False.
        """
        if self.evidence.checkpoint_reached or not isinstance(event, dict):
            return False

        kind = event.get("type")
        if kind == "assistant":
            self._observe_tool_uses(index, event)
            return False
        if kind == "user":
            return self._observe_tool_results(index, event)
        return False

    def _observe_tool_uses(self, index: int, event: dict) -> None:
        for block in _content_blocks(event):
            if block.get("type") != "tool_use":
                continue
            name = block.get("name")
            tool_use_id = block.get("id")
            if not isinstance(tool_use_id, str) or not tool_use_id:
                continue

            if name in EDIT_TOOLS:
                # Recorded as PENDING, not as seen: an edit that errors did not
                # modify the working tree, and the predicate says the tree was
                # modified.
                self._pending_edits[tool_use_id] = str(name)
                continue

            if name != "Bash":
                continue
            # The CI invocation only counts once an edit has ALREADY completed.
            # A ci:agent run before any edit is the agent looking at a red
            # baseline, which is not the checkpoint.
            if not self.evidence.implementation_edit_seen:
                continue
            if self.evidence.matching_ci_agent_tool_use_id is not None:
                continue
            command = (block.get("input") or {}).get("command")
            if not isinstance(command, str) or not self._pattern.search(command):
                continue
            self.evidence.matching_ci_agent_tool_use_id = tool_use_id
            self.evidence.matching_ci_agent_event_index = index

    def _observe_tool_results(self, index: int, event: dict) -> bool:
        for block in _content_blocks(event):
            if block.get("type") != "tool_result":
                continue
            tool_use_id = block.get("tool_use_id")
            if not isinstance(tool_use_id, str):
                continue
            errored = bool(block.get("is_error"))

            pending = self._pending_edits.pop(tool_use_id, None)
            if pending is not None and not errored:
                self.evidence.completed_edit_tool_use_ids.append(tool_use_id)
                if not self.evidence.implementation_edit_seen:
                    self.evidence.implementation_edit_seen = True
                    self.evidence.implementation_edit_tool = pending
                    self.evidence.implementation_edit_event_index = index
                continue

            if tool_use_id != self.evidence.matching_ci_agent_tool_use_id:
                continue
            # THE boundary. The CI command has completed and returned; nothing
            # of it is mid-flight, so stopping here cannot kill npm or a child
            # process. A FAILING ci:agent still closes the checkpoint: the
            # predicate is about the invocation, not about its verdict, and
            # making it conditional on success would make the stop point depend
            # on how well the work was going.
            self.evidence.matching_ci_agent_result_seen = True
            self.evidence.checkpoint_reached = True
            self.evidence.checkpoint_event_index = index
            timestamp = event.get("timestamp")
            self.evidence.checkpoint_timestamp = (
                timestamp if isinstance(timestamp, str) else None
            )
            return True
        return False


def detect_over(events: Sequence[dict], *, ci_command: str = DEFAULT_CI_COMMAND):
    """Replay a finished stream through the detector. Used by tests and audits."""
    detector = CiAgentAfterEditDetector(ci_command=ci_command)
    for index, event in enumerate(events):
        if detector.observe(index, event):
            break
    return detector.evidence
