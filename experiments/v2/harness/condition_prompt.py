#!/usr/bin/env python3
"""Compose the prompt each condition actually receives.

Two jobs, kept apart from the runner so they can be tested without starting
anything:

1. :func:`compose_task_prompt` — the opening prompt. ``C1`` gets the task body
   and nothing else. ``C4`` gets the approved architecture payload as primary
   context and the same task body, byte-identical, as secondary context. That is
   the ``prompt_injection`` delivery ``MODEL_VISIBLE_WORKTREE_POLICY.md`` and
   ``prepare_model_worktree`` already define; this module performs it.

2. :func:`compose_continuation_prompt` — the prompt phase B of a reset receives.
   Its wording is **condition-neutral**: byte-identical for ``C1`` and ``C4``
   except for the architecture payload itself, which is the treatment. If the
   continuation sentence differed between arms, the reset would be applying two
   treatments and attributing both to one.

What is never done
------------------
**Phase A is never summarised.** The continuation carries the original task
specification and the state of the repository, and nothing about what the first
process said, tried, concluded or intended. A summary would be exactly the
conversational context the reset exists to remove, reintroduced in a form the
harness wrote rather than the model.

Byte discipline
---------------
The task body is delivered as the same bytes the approved index hashes, and the
architecture payload as the same bytes the rule catalog is traceable to. Both
are read as bytes and decoded once as UTF-8; nothing is re-wrapped, re-indented
or newline-normalised on the way through, because a payload that differs from
the one the record pins is a different payload however small the difference.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Optional

import run_governance as gov

#: The separator between the architecture payload and the task. Fixed text, so
#: the composed prompt is a deterministic function of its two inputs.
ARCHITECTURE_HEADER = (
    "The following is the architecture context for this repository. Treat it as "
    "the primary context for the work that follows.\n\n"
)

TASK_HEADER = "\n\n---\n\nThe task:\n\n"

#: The condition-neutral continuation sentence. Identical for every condition.
#:
#: It says three things and no more: continue, from the repository as it stands,
#: and leave it ready to be evaluated. It does not say a reset happened, does
#: not say how much was done, does not say what remains, and does not hint at an
#: approach — any of which would be information phase A had and phase B is not
#: supposed to inherit.
CONTINUATION_WORDING = (
    "Continue implementing the task from the current repository state. Complete "
    "the task and leave the repository ready for evaluation."
)

CONTINUATION_TASK_HEADER = "\n\n---\n\nThe task:\n\n"


def _architecture_text(repo: Path) -> str:
    return gov.architecture_context_bytes(repo).decode("utf-8")


def compose_task_prompt(
    condition: str, task_body: bytes, *, repo: Path = gov.REPO
) -> str:
    """The opening prompt for one condition."""
    body = task_body.decode("utf-8")
    delivery = gov.architecture_delivery_for(condition)
    if delivery == "none":
        return body
    if delivery != "prompt_injection":
        raise gov.RunnerRefusal(
            gov.ARCHITECTURE_DELIVERY_VIOLATION,
            f"{condition} delivers architecture by {delivery!r}; this composer "
            "performs prompt injection only, and never writes a persistent file",
        )
    return ARCHITECTURE_HEADER + _architecture_text(repo) + TASK_HEADER + body


def compose_continuation_prompt(
    condition: str, task_body: bytes, *, repo: Path = gov.REPO
) -> str:
    """The phase-B prompt for one condition.

    ``C1`` receives the continuation sentence plus the original task. ``C4``
    receives the EXACT SAME architecture bytes again — re-injected, as
    ``RESET_PROTOCOL.md`` §2 step 8 requires — plus the same continuation
    sentence and the same original task.
    """
    body = task_body.decode("utf-8")
    delivery = gov.architecture_delivery_for(condition)
    tail = CONTINUATION_WORDING + CONTINUATION_TASK_HEADER + body
    if delivery == "none":
        return tail
    if delivery != "prompt_injection":
        raise gov.RunnerRefusal(
            gov.ARCHITECTURE_DELIVERY_VIOLATION,
            f"{condition} delivers architecture by {delivery!r}; the reset "
            "continuation performs prompt injection only",
        )
    return ARCHITECTURE_HEADER + _architecture_text(repo) + TASK_HEADER + tail


def architecture_payload_sha256(
    prompt: str, *, repo: Path = gov.REPO
) -> Optional[str]:
    """The hash of the architecture payload a composed prompt actually carries.

    Recomputed from the PROMPT, not from the source document. The point of the
    check is that what the model was handed matches what the record pins, and
    re-hashing the source file would only prove the source file is itself.
    """
    if not prompt.startswith(ARCHITECTURE_HEADER):
        return None
    rest = prompt[len(ARCHITECTURE_HEADER):]
    marker = rest.find(TASK_HEADER)
    if marker < 0:
        return None
    return hashlib.sha256(rest[:marker].encode("utf-8")).hexdigest()


def prompt_manifest(
    condition: str, prompt: str, *, repo: Path = gov.REPO
) -> Dict[str, object]:
    """What was delivered, hashed, without recording the prompt text itself."""
    carried = architecture_payload_sha256(prompt, repo=repo)
    expected = (
        None
        if gov.architecture_delivery_for(condition) == "none"
        else gov.architecture_context_sha256(repo)
    )
    return {
        "condition": condition,
        "architecture_delivery": gov.architecture_delivery_for(condition),
        "architecture_sha256_expected": expected,
        "architecture_sha256_delivered": carried,
        "architecture_matches": carried == expected,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prompt_bytes": len(prompt.encode("utf-8")),
    }


def assert_architecture_payload(
    condition: str, prompt: str, *, repo: Path = gov.REPO, where: str = "prompt"
) -> Dict[str, object]:
    """Refuse a prompt whose architecture payload is not the approved one.

    Fails closed in BOTH directions, because both failures are real. A ``C4``
    prompt missing the payload silently demotes the treatment arm to baseline; a
    ``C1`` prompt carrying one silently contaminates the baseline. Either would
    be invisible in the artifacts and fatal to the comparison.
    """
    manifest = prompt_manifest(condition, prompt, repo=repo)
    if not manifest["architecture_matches"]:
        raise gov.RunnerRefusal(
            gov.ARCHITECTURE_CONTEXT_HASH_MISMATCH,
            f"{where}: {condition} should deliver architecture payload "
            f"{manifest['architecture_sha256_expected']!r} but the composed "
            f"prompt carries {manifest['architecture_sha256_delivered']!r}",
        )
    return manifest
