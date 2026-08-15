#!/usr/bin/env python3
"""Prepare the model-visible coding worktree for a study-v2 run (fail-closed).

The coding model's worktree must contain the **development substrate** it needs to
implement a functional task and run `npm run ci:agent`, and nothing that answers
the architecture question or reveals the evaluation machinery. Before this module
existed, the model's worktree was the whole repository, which put
`docs/v2/ARCHITECTURE_CONTEXT.md` and `docs/v2/ARCHITECTURE_RULE_CATALOG.yml` —
the explicit architecture payload and the machine-checkable rule catalog the
oracle scores against — inside the workspace of **every** condition, including the
no-guidance C1 baseline. That would confound the primary C4-vs-C1 contrast.

Policy: docs/v2/MODEL_VISIBLE_WORKTREE_POLICY.md.

Design
------
**Allowlist-first.** Only paths matched by :data:`ALLOWED_TREES` /
:data:`ALLOWED_ROOT_FILES` are copied. Nothing is included because it "was not
excluded"; a new top-level file is invisible to the model until it is explicitly
allowed. An exclusion sweep (:func:`assert_snapshot_clean`) then runs as a
fail-closed backstop over the finished snapshot.

**Content sweep, not just names.** The exclusion sweep also reads the prose the
model can see (:func:`scan_source_comment_disclosures`) and refuses a snapshot
whose *source comments* state a scored dependency rule. Excluding
``ARCHITECTURE_CONTEXT.md`` is not enough if ``apps/api/src/app.ts`` simply says
the rule in a comment: that reached the C1 baseline too, which is what ``TD-B23``
recorded and what a basename-only sweep could never catch (``TD-B24``). Naming a
layer is *not* a disclosure — folder names, scope tags and import edges are meant
to stay visible (D3) — only rule-shaped prose is.

**Condition payloads.** The functional task is always delivered through the
approved out-of-band mechanism (the prompt), never written into the worktree.
The architecture payload is supplied as the *same bytes* to C3 and C4 but through
different channels: C3 persists it as the single approved repository-instruction
file, C4 receives it as explicit prompt injection with **no** persistent file.
C1 and C2 must not be given an architecture payload at all.

**Deterministic manifest.** Every included path is recorded with its SHA-256, and
a single `content_hash` covers the whole snapshot. No timestamps are recorded, so
two preparations of the same substrate produce byte-identical manifests.

Scope: this module prepares the worktree and records what it did. It is **not**
the live model runner, which does not exist yet (`TD-B02`). Runner-time
enforcement of this policy is tracked as **`TD-B22`** and is **not** complete.

No model is invoked and no benchmark task is executed.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[3]

MANIFEST_SCHEMA_VERSION = "1.0.0"
CONDITIONS: Tuple[str, ...] = ("C1", "C2", "C3", "C4")

#: Source trees copied recursively — the realistic development substrate. Their
#: folder names, project tags and code stay visible on purpose (D3): the implicit
#: architectural tension must remain discoverable from the substrate itself.
ALLOWED_TREES: Tuple[str, ...] = ("apps", "libs")

#: Repository-root files copied verbatim — build, type-check, test and the
#: agent-visible lint configuration. `.eslintrc.json` (the architecture-enforcing
#: config) is deliberately absent.
ALLOWED_ROOT_FILES: Tuple[str, ...] = (
    "package.json",
    "package-lock.json",
    "nx.json",
    "tsconfig.base.json",
    "jest.preset.js",
    ".eslintrc.agent.json",
    ".nvmrc",
    ".gitattributes",
)

#: Basenames dropped even inside an allowed tree. The per-project
#: `.eslintrc.json` files only `extends` the architecture-enforcing root config;
#: `ci:agent` runs ESLint with `--no-eslintrc --config .eslintrc.agent.json`, so
#: they are unnecessary, and copying them would leave a dangling pointer to the
#: excluded rule set.
DENIED_BASENAMES_IN_TREES: Tuple[str, ...] = (".eslintrc.json",)

#: Directory names never copied out of an allowed tree.
DENIED_DIR_NAMES_IN_TREES: Tuple[str, ...] = (
    "node_modules",
    "dist",
    "coverage",
    ".nx",
    "__pycache__",
    ".pytest_cache",
)

#: The single approved repository-instruction file for C3.
C3_INSTRUCTION_PATH = "CLAUDE.md"

# --------------------------------------------------------------------------- #
# Fail-closed exclusion sweep
# --------------------------------------------------------------------------- #
#: Explicit architecture-answering artifacts. Never inside a coding worktree.
FORBIDDEN_ARCHITECTURE_BASENAMES: Tuple[str, ...] = (
    "architecture_context.md",
    "architecture_rule_catalog.yml",
    "architecture_rule_catalog.yaml",
    "architecture_rule_traceability.csv",
    "manual_oracle_rubric.md",
    ".eslintrc.json",
)

#: Task-specific evaluator artifacts (HIDDEN_EVALUATOR_BOUNDARY.md section 4).
FORBIDDEN_EVALUATOR_GLOBS: Tuple[str, ...] = (
    "evaluator_manifest.json",
    "*.evaluator.json",
    "oracle_result.json",
    "architecture_finding.json",
    "acceptance_result.json",
    "guard_result.json",
    "expected_layers.*",
    "prohibited_layers.*",
    "required_areas.*",
    "prohibited_areas.*",
    "legitimate_alternatives.*",
    "legitimate_answers.*",
    "hidden_acceptance_plan.*",
)

#: Directories that must never appear inside a coding worktree.
FORBIDDEN_DIR_NAMES: Tuple[str, ...] = (
    "hidden",
    "hidden_tests",
    ".evaluator_mounts",
    "evaluator-mounts",
    "eval_mounts",
    ".claude",
    "docs",
    "experiments",
    "paper",
    "archive",
)

#: Persistent-context files. Any unapproved one contaminates the run; the C3
#: approved instruction file is the single allowed exception.
PERSISTENT_CONTEXT_BASENAMES: Tuple[str, ...] = (
    "claude.md",
    "claude.local.md",
    "agents.md",
    ".cursorrules",
    ".windsurfrules",
    "copilot-instructions.md",
)


# --------------------------------------------------------------------------- #
# Architecture-rule disclosure in model-visible source (TD-B23 / TD-B24)
# --------------------------------------------------------------------------- #
# The basename/directory sweep above cannot see *inside* a file, so a source
# comment that simply states a scored dependency rule reached every condition,
# including the C1 baseline. This section reads the prose the model actually
# sees and refuses the substrate if it coaches the hidden rules.
#
# The detector is deliberately narrow. Naming a layer is not a disclosure —
# folder names, scope tags and import edges are *meant* to stay visible (D3) —
# so an ordinary comment may say what a module is or does. A comment is a
# disclosure only when it states a **rule**: a worked violation example, a named
# rule id, a commented-out cross-package import, or a prohibition/exclusivity
# claim aimed at a named layer. Anything less specific would reject the ordinary
# implementation comments the substrate needs to stay realistic.

#: Model-visible text whose *comments* are scanned, by kind.
_JS_LIKE_SUFFIXES: Tuple[str, ...] = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
_JSON_SUFFIXES: Tuple[str, ...] = (".json",)
_HASH_COMMENT_SUFFIXES: Tuple[str, ...] = (".yml", ".yaml", ".sh", ".toml", ".ini", ".cfg")
_HASH_COMMENT_BASENAMES: Tuple[str, ...] = (
    ".gitattributes", ".gitignore", ".nvmrc", ".npmrc", ".editorconfig",
)
_PROSE_SUFFIXES: Tuple[str, ...] = (".md", ".markdown", ".txt", ".rst")

#: A comment body that is itself a workspace-package import. This is the
#: signature of a worked forbidden-import example: real code is an import
#: statement, but a *commented-out* one demonstrates a boundary rather than
#: using it.
_COMMENTED_OUT_IMPORT = re.compile(
    r"""(?:^|\s)(?:import|export)\b[^\n]*?\bfrom\s*['"]@afci-bench/"""
    r"""|(?:^|\s)require\s*\(\s*['"]@afci-bench/""",
    re.IGNORECASE,
)

#: Phrases that disclose an architecture rule on their own, whatever layer they
#: name. Each is rule-shaped language that no behaviour-describing comment needs.
_SELF_SUFFICIENT_DISCLOSURE: Tuple[Tuple[str, str], ...] = (
    (r"boundary\s+violation", "worked boundary-violation example"),
    (r"violation\s+example", "worked violation example"),
    # "this would violate the architecture boundary" / "violates the module
    # boundary". The independent review named this recall gap: the noun-phrase
    # pattern above only caught the "boundary violation" word order.
    (r"\bviolat\w*\s+(?:\w+\s+){0,3}?boundar(?:y|ies)",
     "describes an action as violating an architectural boundary"),
    (r"\bbreak\w*\s+(?:\w+\s+){0,3}?(?:layering|architectur\w*\s+boundar(?:y|ies))",
     "describes an action as breaking the layering"),
    (r"(?:module|import|layer|layering|architectur\w*)[\s-]+boundar(?:y|ies)\s+rules?",
     "explains the module-boundary rules"),
    (r"\blayering\s+rules?\b", "explains the layering rules"),
    (r"\barchitecture\s+(?:rule|ci)\b", "names the architecture rule/CI"),
    (r"enforce-module-boundaries", "names the boundary-enforcing lint rule"),
    (r"depConstraints", "names the dependency-constraint configuration"),
    (r"\bAR-DEP-\d", "names a dependency-direction rule id"),
    (r"\bOPP-[A-Z0-9]", "names an opportunity id"),
    (r"architectural\s+(?:choice|decision|constraint|rule|requirement)",
     "justifies a dependency choice as an architecture rule"),
    (r"deliberate(?:ly)?\s+architectur", "justifies a dependency choice as an architecture rule"),
)

#: Prohibition / exclusivity claims. On their own these can be ordinary advice
#: ("do not import this at runtime"), so each must be paired with a named layer
#: before it counts as a disclosure.
#:
#: ``reference`` is accepted wherever ``import``/``depend`` is, because "never
#: reference core from here" states exactly the same rule as "never import core
#: from here" and the independent review found only the latter was caught.
_DEP_VERB = r"(?:import|depend|reference|use)\w*"
_PROHIBITION = re.compile(
    r"(?:must|should|shall|may|can|could|do|does|is|are|will)\s+not\s+(?:directly\s+)?"
    + _DEP_VERB
    + r"|(?:cannot|can\s?not|can't|mustn't|shouldn't|won't)\s+(?:directly\s+)?"
    + _DEP_VERB
    + r"|not\s+(?:allowed|permitted)\s+to\s+(?:directly\s+)?" + _DEP_VERB
    + r"|never\s+(?:directly\s+)?" + _DEP_VERB
    + r"|(?:avoid|prevent|forbid|prohibit|disallow)\w*\s+(?:directly\s+)?" + _DEP_VERB
    + r"|without\s+(?:directly\s+)?" + _DEP_VERB
    + r"|instead\s+of\s+(?:directly\s+)?" + _DEP_VERB
    + r"|(?:may|can|must|should)\s+only\s+(?:import|depend|reference)"
    + r"|only\s+depends?\s+on"
    + r"|depends?\s+on\s+[\w@/-]+\s*,\s*not\b"
    # "core must never be reached from api" / "may not be referenced from api"
    + r"|(?:must|should|may|can|shall)\s+(?:never|not)\s+be\s+"
      r"(?:reached|imported|referenced|used|accessed)\b"
    # "importing core here is not permitted" / "... is forbidden"
    + r"|" + _DEP_VERB + r"[^.\n]{0,40}?\b(?:is|are)\s+"
      r"(?:not\s+(?:allowed|permitted)|forbidden|prohibited|banned|disallowed|illegal)\b"
    # "keep core out of api"
    + r"|\bkeep\s+[\w@/-]+\s+out\s+of\b"
    # "core is off-limits from the api layer" / "out of bounds for api"
    + r"|\boff[-\s]?limits\b"
    + r"|\bout\s+of\s+bounds\b",
    re.IGNORECASE,
)

#: An ASCII/arrow dependency edge between two named layers, e.g. ``api -> core``
#: or ``apps/api --> libs/core``. Prohibition-style layer diagrams state a rule
#: without ever using a verb, which every pattern above would miss.
_LAYER_TOKEN = (
    r"(?:@afci-bench/\w+|\b(?:apps?|libs?)/[\w-]+"
    r"|\b(?:core|infra|infrastructure|features?|contracts?|observability|domain|api)\b)"
)
_LAYER_EDGE = re.compile(
    _LAYER_TOKEN + r"\s*(?:-{1,2}>|=>|→|➜|\|)\s*" + _LAYER_TOKEN,
    re.IGNORECASE,
)

#: Words that turn a layer edge into a stated prohibition. Kept tight: an edge
#: on its own is ordinary structural description and stays visible (D3).
_EDGE_PROHIBITION_MARKER = re.compile(
    r"\b(?:forbidden|prohibited|banned|disallowed|illegal|invalid|violation|violates?"
    r"|not\s+allowed|not\s+permitted|never|must\s+not|cannot|can't|off[-\s]?limits"
    r"|out\s+of\s+bounds)\b",
    re.IGNORECASE,
)

#: A named architectural subject. Required to turn a prohibition into a finding.
_LAYER_SUBJECT = re.compile(
    r"@afci-bench/\w+"
    r"|\b(?:core|infra|infrastructure|features?|contracts?|observability|domain|api)\b"
    r"|\b(?:apps?|libs?)/"
    r"|\blayer\b",
    re.IGNORECASE,
)

#: Violation-message prefixes, used to pick the machine-readable refusal code.
_ARCH_FILE_PREFIX = "explicit architecture artifact in model-visible worktree:"
_ARCH_COMMENT_PREFIX = "architecture-rule disclosure in model-visible source:"


def _js_comment_regions(text: str) -> List[Tuple[int, str]]:
    """Return ``(line_number, comment_body)`` for every JS/TS comment in ``text``.

    String and template literals are skipped so a quoted ``//`` is not mistaken
    for a comment, and regex literals are consumed so an escaped slash inside one
    cannot swallow the code that follows.
    """
    regions: List[Tuple[int, str]] = []
    i, n, line = 0, len(text), 1
    prev = ""  # last significant character, for the regex-literal heuristic
    while i < n:
        ch = text[i]
        if ch == "\n":
            line += 1
            i += 1
            continue
        if ch in "'\"`":
            quote = ch
            i += 1
            while i < n:
                c = text[i]
                if c == "\\":
                    i += 2
                    continue
                if c == "\n":
                    line += 1
                if c == quote:
                    i += 1
                    break
                i += 1
            prev = quote
            continue
        if ch == "/" and i + 1 < n:
            nxt = text[i + 1]
            if nxt == "/":
                end = text.find("\n", i)
                end = n if end == -1 else end
                regions.append((line, text[i + 2:end]))
                i = end
                continue
            if nxt == "*":
                end = text.find("*/", i + 2)
                body = text[i + 2:(n if end == -1 else end)]
                regions.append((line, body))
                line += body.count("\n")
                i = n if end == -1 else end + 2
                continue
            if prev == "" or prev in "=(,:[!&|?{};+-*%~^<>":
                # regex literal, not division
                i += 1
                in_class = False
                while i < n:
                    c = text[i]
                    if c == "\\":
                        i += 2
                        continue
                    if c == "\n":
                        break
                    if c == "[":
                        in_class = True
                    elif c == "]":
                        in_class = False
                    elif c == "/" and not in_class:
                        i += 1
                        break
                    i += 1
                prev = "/"
                continue
        if not ch.isspace():
            prev = ch
        i += 1
    return regions


def _hash_comment_regions(text: str) -> List[Tuple[int, str]]:
    """Return ``(line_number, comment_body)`` for ``#``-style comments."""
    return [
        (i, line.split("#", 1)[1])
        for i, line in enumerate(text.splitlines(), 1)
        if line.lstrip().startswith("#")
    ]


def _json_string_values(node, out: List[str]) -> None:
    """Collect every JSON *string value*. Keys are structural, not prose.

    Scanning keys would flag `.eslintrc.agent.json`, whose whole purpose is to
    name `@nx/enforce-module-boundaries` in order to switch it **off** — the one
    file the policy allows to name the rule.
    """
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, list):
        for item in node:
            _json_string_values(item, out)
    elif isinstance(node, dict):
        for value in node.values():
            _json_string_values(value, out)


def comment_regions_for(path: Path, text: str) -> List[Tuple[int, str]]:
    """Return the prose regions of ``path`` that the model can read."""
    suffix = path.suffix.lower()
    name = path.name.lower()
    if suffix in _JS_LIKE_SUFFIXES:
        return _js_comment_regions(text)
    if suffix in _JSON_SUFFIXES:
        try:
            values: List[str] = []
            _json_string_values(json.loads(text), values)
            return [(0, v) for v in values]
        except (ValueError, RecursionError):
            return [(0, text)]
    if suffix in _HASH_COMMENT_SUFFIXES or name in _HASH_COMMENT_BASENAMES:
        return _hash_comment_regions(text)
    if suffix in _PROSE_SUFFIXES:
        return [(0, text)]
    return []


def find_comment_disclosures(path: Path, text: str) -> List[Tuple[int, str]]:
    """Return ``(line, reason)`` for every architecture-rule disclosure in ``text``."""
    findings: List[Tuple[int, str]] = []
    for line, body in comment_regions_for(Path(path), text):
        if _COMMENTED_OUT_IMPORT.search(body):
            findings.append((line, "commented-out workspace-package import (worked violation example)"))
        for pattern, reason in _SELF_SUFFICIENT_DISCLOSURE:
            if re.search(pattern, body, re.IGNORECASE):
                findings.append((line, reason))
        prohibition = _PROHIBITION.search(body)
        if prohibition and _LAYER_SUBJECT.search(body):
            findings.append(
                (line, f"states a dependency prohibition about a named layer "
                       f"({prohibition.group(0).strip()!r})")
            )
        edge = _LAYER_EDGE.search(body)
        if edge and _EDGE_PROHIBITION_MARKER.search(body):
            findings.append(
                (line, f"prohibition-style layer diagram ({edge.group(0).strip()!r})")
            )
    return findings


def scan_source_comment_disclosures(snapshot_root, skip: Sequence[str] = ()) -> List[str]:
    """Return every architecture-rule disclosure found in a snapshot's prose.

    ``skip`` names the approved architecture-delivery paths: C3's single approved
    repository-instruction file *is* the architecture payload, so scanning it
    would refuse the very condition it implements. Every other file in every
    condition — C1's baseline substrate included — is scanned.
    """
    snapshot_root = Path(snapshot_root)
    skipped = {PurePosixPath(p).as_posix() for p in skip}
    violations: List[str] = []
    for path in sorted(snapshot_root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in DENIED_DIR_NAMES_IN_TREES for part in path.relative_to(snapshot_root).parts[:-1]):
            continue
        if path.relative_to(snapshot_root).as_posix() in skipped:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(snapshot_root).as_posix()
        for line, reason in find_comment_disclosures(path, text):
            where = f"{rel}:{line}" if line else rel
            violations.append(f"{_ARCH_COMMENT_PREFIX} {where} {reason}")
    return violations


# --------------------------------------------------------------------------- #
# Experiment / treatment awareness in model-visible content
# --------------------------------------------------------------------------- #
# A SEPARATE threat class from the architecture-rule disclosure above, and the
# distinction matters. TD-B23 was about the substrate *coaching the answer*: a
# comment that states a scored dependency rule hands C1 the finding it is
# supposed to be measured on. This class is about the substrate *revealing the
# experiment*: metadata telling the model it is inside AFCI-Bench, that a
# canonical architecture context exists, that other conditions receive it, or
# that a hidden oracle will score it.
#
# The second is not a weaker form of the first. A C1 model that reads "this is
# the Architecture-First Context Injection Benchmark" learns nothing about which
# dependency direction is legal, yet it now knows architecture is the scored
# construct, which is enough to change its behaviour. Demand characteristics
# make a no-guidance baseline stop being a no-guidance baseline.
#
# Precision requirement: `architecture`, `test`, `condition`, `context` and
# `benchmark` are ordinary words in ordinary application source, and a scanner
# that bans them is unusable. Every pattern below is therefore a *contextual
# combination* - the study's own name, an expanded construct, a condition label
# paired with another condition label, an oracle paired with scoring, or a path
# into the experiment tree - never a bare topic word.

#: The workspace package scope. Adjudicated as retained structural identity: it
#: is baked into `tsconfig.base.json` path aliases and the import statements of
#: `apps/` and `libs/`, so it is an opaque npm scope rather than prose, and it
#: states no benchmark, condition, treatment or oracle. Import specifiers and
#: alias keys are masked before scanning so the retained scope does not swamp
#: the signal; prose that spells out "AFCI-Bench" is still caught below.
_RETAINED_SCOPE_ALIAS = re.compile(r"@afci-bench/[A-Za-z0-9._-]+")

_EXPERIMENT_AWARENESS: Tuple[Tuple[str, str], ...] = (
    (r"\bAFCI\b", "names the AFCI study"),
    (r"\bafci[\s_-]*bench\b", "names AFCI-Bench"),
    (r"architecture[\s-]*first\s+context\s+injection",
     "expands the Architecture-First Context Injection construct"),
    (r"\bcanonical\s+architecture\s+(?:context|payload|injection)",
     "names the canonical architecture context payload"),
    (r"\barchitecture[\s-]*context\s+(?:injection|treatment|payload|benchmark|study|experiment)",
     "names the architecture-context treatment"),
    (r"\brepository[\s-]*instruction\s+(?:condition|delivery|treatment|file|mechanism)",
     "names the repository-instruction delivery mechanism"),
    (r"\b(?:hidden|private)\s+(?:oracle|evaluator)",
     "reveals the hidden oracle/evaluator"),
    (r"\boracle\b[^.\n]{0,40}?\b(?:scor\w+|grade\w*|evaluat\w+|hidden|conformance)\b",
     "reveals a scoring oracle"),
    (r"\b(?:scor\w+|grade\w*|evaluat\w+|hidden|conformance)\b[^.\n]{0,40}?\boracle\b",
     "reveals a scoring oracle"),
    (r"\bC[1-4]\s*(?:/|,|-|\bvs\.?\b|\band\b)\s*C[1-4]\b",
     "names experimental condition labels"),
    (r"\b(?:condition|arm)s?\s+C[1-4]\b", "names an experimental condition label"),
    (r"\bC[1-4]\s+(?:baseline|condition|arm|treatment)\b",
     "names an experimental condition label"),
    (r"\b(?:treatment|control)\s+(?:condition|arm|group)\b",
     "names a controlled experimental arm"),
    (r"\bno[\s-]*guidance\s+baseline\b", "names the no-guidance baseline arm"),
    (r"\btoken[\s-]*matched\s+(?:generic\s+)?guidance\b",
     "names the token-matched guidance payload"),
    (r"\b(?:benchmark|study|experiment)\b[^.\n]{0,60}?"
     r"\b(?:participant|condition|arm|protocol|harness|oracle|treatment|scored)\b",
     "frames the repository as a benchmark/study"),
    (r"\b(?:participant|condition|arm|protocol|harness|oracle|treatment|scored)\b[^.\n]{0,60}?"
     r"\b(?:benchmark|study|experiment)\b",
     "frames the repository as a benchmark/study"),
    (r"\bexperiments?/v\d", "points at the experiment tree"),
    (r"\bstudy\s+v\d\b", "names the study version"),
    (r"\bpre[\s-]?registration\b", "names the study's pre-registration"),
)

_AWARENESS_PREFIX = "experiment-awareness disclosure in model-visible content:"


def _flatten_wrapped_prose(text: str) -> Tuple[str, List[int]]:
    """Collapse wrapped prose to one line, keeping a flat-index -> line map.

    Disclosures are written as prose and prose wraps. The historical
    ``.gitattributes`` leak said "the canonical architecture / context delivered
    identically to the repository-instruction conditions" across a line break,
    so a line-by-line scan sees "canonical architecture" and "context" as
    unrelated fragments and matches neither. Runs of whitespace — including a
    newline plus the next line's indentation and comment leader — become a
    single space, so the phrase is scanned as written.

    A ``*`` is treated as a block-comment leader only when whitespace follows,
    so ``*.png binary`` in ``.gitattributes`` keeps its glob intact.
    """
    flat: List[str] = []
    line_of: List[int] = []
    line, i, n = 1, 0, len(text)
    pending_space = False

    def _emit_space() -> None:
        nonlocal pending_space
        if flat and not pending_space:
            flat.append(" ")
            line_of.append(line)
            pending_space = True

    while i < n:
        ch = text[i]
        if ch == "\r":
            i += 1
            continue
        if ch == "\n":
            line += 1
            i += 1
            while i < n and text[i] in " \t":
                i += 1
            for leader in ("//", "#"):
                if text.startswith(leader, i):
                    i += len(leader)
                    break
            else:
                if text.startswith("*", i) and i + 1 < n and text[i + 1] in " \t":
                    i += 1
            while i < n and text[i] in " \t":
                i += 1
            _emit_space()
            continue
        if ch in " \t":
            _emit_space()
            i += 1
            continue
        flat.append(ch)
        line_of.append(line)
        pending_space = False
        i += 1
    return "".join(flat), line_of


def find_experiment_awareness(path, text: str) -> List[Tuple[int, str]]:
    """Return ``(line, reason)`` for every experiment-awareness disclosure.

    Unlike :func:`find_comment_disclosures`, this reads the **whole file**, not
    only its comment regions. The historical leaks were a ``package.json``
    ``description`` and two npm *script names* — JSON keys and values, not
    comments — so a comment-only sweep would have missed all three.
    """
    masked = _RETAINED_SCOPE_ALIAS.sub("@scope/pkg", str(text))
    flat, line_of = _flatten_wrapped_prose(masked)
    seen = set()
    findings: List[Tuple[int, str]] = []
    for pattern, reason in _EXPERIMENT_AWARENESS:
        for match in re.finditer(pattern, flat, re.IGNORECASE):
            line = line_of[match.start()] if match.start() < len(line_of) else 0
            if (line, reason) not in seen:
                seen.add((line, reason))
                findings.append((line, reason))
    return sorted(findings)


def scan_experiment_awareness(snapshot_root, skip: Sequence[str] = ()) -> List[str]:
    """Return every experiment-awareness disclosure in a snapshot's content.

    ``skip`` names the approved architecture-delivery paths, on the same basis
    as :func:`scan_source_comment_disclosures`: C3's repository-instruction file
    *is* the treatment, so it is exempt by construction. C1 and C2 have no
    exempt path at all.
    """
    snapshot_root = Path(snapshot_root)
    skipped = {PurePosixPath(p).as_posix() for p in skip}
    violations: List[str] = []
    for path in sorted(snapshot_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(snapshot_root)
        if any(part in DENIED_DIR_NAMES_IN_TREES for part in rel.parts[:-1]):
            continue
        if rel.as_posix() in skipped:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line, reason in find_experiment_awareness(path, text):
            violations.append(f"{_AWARENESS_PREFIX} {rel.as_posix()}:{line} {reason}")
    return violations


class WorktreePreparationError(RuntimeError):
    """Fail-closed refusal. ``code`` is the machine-readable refusal reason."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


@dataclass(frozen=True)
class PreparationRequest:
    condition: str
    source_root: Path
    dest_root: Path
    task_path: Optional[Path] = None
    task_id: Optional[str] = None
    architecture_text: Optional[str] = None
    generic_guidance_text: Optional[str] = None


@dataclass
class PreparationResult:
    snapshot_root: Path
    manifest: Dict[str, object]
    included: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def architecture_delivery_for(condition: str) -> str:
    return {
        "C1": "none",
        "C2": "none",
        "C3": "persistent_instruction_file",
        "C4": "prompt_injection",
    }[condition]


def _validate_condition_payloads(req: PreparationRequest) -> None:
    """Refuse any condition/payload combination the protocol forbids."""
    if req.condition not in CONDITIONS:
        raise WorktreePreparationError(
            "UNKNOWN_CONDITION", f"condition must be one of {list(CONDITIONS)}, got {req.condition!r}"
        )

    has_arch = req.architecture_text is not None
    has_guidance = req.generic_guidance_text is not None

    if req.condition in ("C1", "C2") and has_arch:
        raise WorktreePreparationError(
            "ARCH_PAYLOAD_NOT_ALLOWED",
            f"{req.condition} must receive no architecture payload (it is the "
            "no-architecture arm)",
        )
    if req.condition in ("C3", "C4") and not has_arch:
        raise WorktreePreparationError(
            "ARCH_PAYLOAD_REQUIRED",
            f"{req.condition} requires the approved architecture payload",
        )
    if req.condition == "C2" and not has_guidance:
        raise WorktreePreparationError(
            "GUIDANCE_PAYLOAD_REQUIRED",
            "C2 requires the approved token-matched generic guidance",
        )
    if req.condition != "C2" and has_guidance:
        raise WorktreePreparationError(
            "GUIDANCE_PAYLOAD_NOT_ALLOWED",
            f"{req.condition} must receive no generic-guidance payload",
        )
    if has_arch and not str(req.architecture_text).strip():
        raise WorktreePreparationError(
            "ARCH_PAYLOAD_EMPTY", "the architecture payload must not be empty"
        )


def _reject_evaluator_source(path: Path, label: str) -> None:
    """Refuse a source path that points at private evaluator or hidden material."""
    parts = [p.lower() for p in Path(path).parts]
    name = Path(path).name.lower()
    needles = ("evaluator-private", "evaluator_private", "hidden_tests", "hidden")
    if any(needle in part for part in parts for needle in needles):
        raise WorktreePreparationError(
            "EVALUATOR_MATERIAL_REJECTED",
            f"{label} points at private evaluator or hidden material: {path}",
        )
    if any(fnmatch.fnmatch(name, pat) for pat in FORBIDDEN_EVALUATOR_GLOBS):
        raise WorktreePreparationError(
            "EVALUATOR_MATERIAL_REJECTED",
            f"{label} is a task-specific evaluator artifact: {path}",
        )


# --------------------------------------------------------------------------- #
# Allowlist walk
# --------------------------------------------------------------------------- #
def iter_allowed_files(source_root) -> List[str]:
    """Return the sorted, POSIX-style relative paths the snapshot may contain.

    Allowlist-first: a path is included only because it is inside
    :data:`ALLOWED_TREES` or named in :data:`ALLOWED_ROOT_FILES`.
    """
    source_root = Path(source_root)
    if not source_root.is_dir():
        raise WorktreePreparationError("SOURCE_MISSING", f"source root not found: {source_root}")

    included: List[str] = []

    for name in ALLOWED_ROOT_FILES:
        candidate = source_root / name
        if candidate.is_file():
            included.append(name)

    for tree in ALLOWED_TREES:
        root = source_root / tree
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(source_root)
            if any(part in DENIED_DIR_NAMES_IN_TREES for part in rel.parts[:-1]):
                continue
            if path.name in DENIED_BASENAMES_IN_TREES:
                continue
            included.append(rel.as_posix())

    return sorted(set(included))


# --------------------------------------------------------------------------- #
# Exclusion sweep (fail-closed backstop)
# --------------------------------------------------------------------------- #
def scan_snapshot_violations(snapshot_root, allow_persistent: Sequence[str] = ()) -> List[str]:
    """Return every policy violation found inside a prepared snapshot.

    ``allow_persistent`` names the persistent-context paths this condition is
    permitted to carry (only the C3 approved instruction file).
    """
    snapshot_root = Path(snapshot_root)
    allowed = {PurePosixPath(p).as_posix() for p in allow_persistent}
    violations: List[str] = []

    for path in sorted(snapshot_root.rglob("*")):
        rel = path.relative_to(snapshot_root).as_posix()
        name = path.name.lower()

        if path.is_dir():
            if name in FORBIDDEN_DIR_NAMES:
                violations.append(f"forbidden directory in model-visible worktree: {rel}/")
            elif name.endswith(".evalmount"):
                violations.append(f"evaluator mount inside model-visible worktree: {rel}/")
            continue

        if name in FORBIDDEN_ARCHITECTURE_BASENAMES:
            violations.append(f"{_ARCH_FILE_PREFIX} {rel}")
        if any(fnmatch.fnmatch(name, pat) for pat in FORBIDDEN_EVALUATOR_GLOBS):
            violations.append(f"evaluator artifact in model-visible worktree: {rel}")
        if name in PERSISTENT_CONTEXT_BASENAMES and rel not in allowed:
            violations.append(f"unapproved persistent context in model-visible worktree: {rel}")

    # TD-B24: the sweep above never opens a file, so it cannot see a source
    # comment that simply states a scored dependency rule (TD-B23).
    violations.extend(scan_source_comment_disclosures(snapshot_root, allowed))

    # Distinct threat class: content that reveals the experiment itself rather
    # than the scored rule. Kept separate so a failure names which one it is.
    violations.extend(scan_experiment_awareness(snapshot_root, allowed))

    return violations


def assert_snapshot_clean(snapshot_root, allow_persistent: Sequence[str] = ()) -> None:
    """Fail closed if the prepared snapshot violates the policy."""
    violations = scan_snapshot_violations(snapshot_root, allow_persistent)
    if not violations:
        return
    if any(v.startswith(_ARCH_FILE_PREFIX) for v in violations):
        code = "UNEXPECTED_ARCHITECTURE_FILE"
    elif any(v.startswith(_ARCH_COMMENT_PREFIX) for v in violations):
        code = "ARCHITECTURE_COMMENT_DISCLOSURE"
    elif any(v.startswith(_AWARENESS_PREFIX) for v in violations):
        code = "EXPERIMENT_AWARENESS_DISCLOSURE"
    else:
        code = "SETUP_CONTAMINATED"
    raise WorktreePreparationError(code, "; ".join(violations))


# --------------------------------------------------------------------------- #
# Preparation
# --------------------------------------------------------------------------- #
def prepare_model_worktree(req: PreparationRequest) -> PreparationResult:
    """Materialise the model-visible worktree for one condition, fail-closed."""
    _validate_condition_payloads(req)

    source_root = Path(req.source_root)
    dest_root = Path(req.dest_root)

    if req.task_path is not None:
        _reject_evaluator_source(req.task_path, "task path")
        if not Path(req.task_path).is_file():
            raise WorktreePreparationError(
                "TASK_MISSING", f"public task body not found: {req.task_path}"
            )

    if dest_root.exists() and any(dest_root.iterdir()):
        raise WorktreePreparationError(
            "DEST_NOT_EMPTY", f"destination worktree is not empty: {dest_root}"
        )

    included = iter_allowed_files(source_root)
    if not included:
        raise WorktreePreparationError(
            "EMPTY_SUBSTRATE", f"no allowlisted substrate found under {source_root}"
        )

    dest_root.mkdir(parents=True, exist_ok=True)
    for rel in included:
        target = dest_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_root / rel, target)

    allow_persistent: List[str] = []
    architecture_persistent_path: Optional[str] = None
    if req.condition == "C3":
        architecture_persistent_path = C3_INSTRUCTION_PATH
        (dest_root / C3_INSTRUCTION_PATH).write_text(
            str(req.architecture_text), encoding="utf-8", newline="\n"
        )
        allow_persistent.append(C3_INSTRUCTION_PATH)

    # Fail-closed backstop over the finished snapshot.
    assert_snapshot_clean(dest_root, allow_persistent)

    manifest = build_manifest(req, dest_root, architecture_persistent_path)
    return PreparationResult(snapshot_root=dest_root, manifest=manifest, included=included)


def build_manifest(
    req: PreparationRequest, snapshot_root: Path, architecture_persistent_path: Optional[str]
) -> Dict[str, object]:
    """Build the deterministic snapshot manifest (no timestamps, sorted paths)."""
    entries: List[Dict[str, object]] = []
    for path in sorted(Path(snapshot_root).rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            entries.append(
                {
                    "path": path.relative_to(snapshot_root).as_posix(),
                    "sha256": sha256_bytes(data),
                    "bytes": len(data),
                }
            )
    entries.sort(key=lambda e: e["path"])

    digest = hashlib.sha256()
    for e in entries:
        digest.update(f"{e['path']} {e['sha256']}\n".encode("utf-8"))

    task_sha = sha256_file(req.task_path) if req.task_path is not None else None
    arch_sha = (
        sha256_bytes(str(req.architecture_text).encode("utf-8"))
        if req.architecture_text is not None
        else None
    )
    guidance_sha = (
        sha256_bytes(str(req.generic_guidance_text).encode("utf-8"))
        if req.generic_guidance_text is not None
        else None
    )

    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "condition": req.condition,
        "task_id": req.task_id,
        "task_sha256": task_sha,
        "task_delivery": "prompt",
        "architecture_delivery": architecture_delivery_for(req.condition),
        "architecture_sha256": arch_sha,
        "architecture_persistent_path": architecture_persistent_path,
        "generic_guidance_delivery": "prompt_injection" if guidance_sha else "none",
        "generic_guidance_sha256": guidance_sha,
        "allowlist": {
            "trees": list(ALLOWED_TREES),
            "root_files": list(ALLOWED_ROOT_FILES),
            "denied_basenames_in_trees": list(DENIED_BASENAMES_IN_TREES),
        },
        "entry_count": len(entries),
        "entries": entries,
        "content_hash": digest.hexdigest(),
        "runner_enforcement": "not implemented (TD-B22)",
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--condition", required=True, choices=list(CONDITIONS))
    parser.add_argument("--source", default=str(REPO), help="Repository root to snapshot from.")
    parser.add_argument("--dest", required=True, help="Model-visible worktree to create.")
    parser.add_argument("--task", default=None, help="Public task body (prompt-delivered).")
    parser.add_argument("--task-id", default=None)
    parser.add_argument(
        "--architecture-file", default=None, help="Approved architecture payload (C3/C4)."
    )
    parser.add_argument(
        "--guidance-file", default=None, help="Approved generic guidance (C2 only)."
    )
    parser.add_argument("--manifest-out", default=None, help="Where to write the manifest JSON.")
    args = parser.parse_args(argv)

    arch_text = (
        Path(args.architecture_file).read_text(encoding="utf-8") if args.architecture_file else None
    )
    guidance_text = (
        Path(args.guidance_file).read_text(encoding="utf-8") if args.guidance_file else None
    )

    req = PreparationRequest(
        condition=args.condition,
        source_root=Path(args.source),
        dest_root=Path(args.dest),
        task_path=Path(args.task) if args.task else None,
        task_id=args.task_id,
        architecture_text=arch_text,
        generic_guidance_text=guidance_text,
    )

    try:
        result = prepare_model_worktree(req)
    except WorktreePreparationError as exc:
        print(f"REFUSED {exc.code}: {exc.message}", file=sys.stderr)
        return 2

    payload = json.dumps(result.manifest, indent=2, sort_keys=False)
    if args.manifest_out:
        Path(args.manifest_out).write_text(payload + "\n", encoding="utf-8", newline="\n")
    else:
        print(payload)

    print(
        f"prepared {result.manifest['condition']} worktree at {result.snapshot_root} "
        f"({result.manifest['entry_count']} files, content_hash "
        f"{result.manifest['content_hash'][:16]}...)",
        file=sys.stderr,
    )
    print(
        "NOTE: runner-time enforcement of this policy is TD-B22 and is not implemented.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
