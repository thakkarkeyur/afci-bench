#!/usr/bin/env python3
"""Structural text model for fail-closed governance-claim guards.

WHY THIS MODULE EXISTS
----------------------
An independent mutation review showed that fixed-width character windows are not
load-bearing guards. Two concrete failures were demonstrated against the
`TD-B34` replication-depth governance:

1. A **new live breadth directive** could be inserted — inside the historical
   `docs/v2/README.md` section, elsewhere in that README, or in
   `TASK_AUTHORING_REPORT.md` — and every assertion stayed green, because the
   supersession prose that the window swept up belonged to a *neighbouring*
   passage, not to the inserted one. Removing the `HISTORICAL`/`SUPERSEDED`
   classification from the original README directive passed for the same reason.
2. The claim *"not a task-creatable fourth cluster"* could be **inverted** to
   *"a task-creatable fourth cluster"* and stayed green, because unrelated
   negations (`not`, `no`, `cannot`, `not task-creatable`) elsewhere in the same
   ±260-character window satisfied the denial pattern.

Both failures share one root cause: proximity is not structure, and a window can
be rescued by text that says nothing about the claim under test.

WHAT THIS MODULE PROVIDES INSTEAD
---------------------------------
A **passage** model plus a **claim register**, with no character windows
anywhere.

*Passage* is the smallest structural unit a Markdown or CSV author can write a
claim in:

  * Markdown — one table row, one blockquote run, one top-level list item with
    its indented continuation lines, or one blank-line-delimited paragraph;
  * CSV — one (row, column) field.

Every passage carries a stable **anchor**: the SHA-256 of its *normalised* text
(emphasis, backticks, blockquote markers and line wrapping collapsed), so
re-flowing a paragraph does not move the anchor but changing a word does.

*Claim register* is an explicit, pinned inventory of the passages that are
allowed to contain a governed vocabulary, with the exact tokens each of them must
carry. A guard built on it is fail-closed in three independent directions:

  * a governed phrase appearing in an **unregistered** passage — anywhere in any
    governed document, including a brand-new file — fails, because the found set
    must equal the registered set;
  * **editing** a registered passage fails, because its anchor moves. This is
    what makes "insert a live directive into an already-marked historical
    passage" and "invert the denial in place" both impossible;
  * **removing** a required token from a registered passage fails, because the
    token is required in *that passage's own text*, never in a neighbourhood.

Pure text inspection. No model is invoked and no benchmark runs.
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Sequence, Tuple

REPO = Path(__file__).resolve().parents[3]

#: Explicit historical classification marker for the withdrawn `TD-B34` breadth
#: objective. Written into the document as an HTML comment (invisible when
#: rendered) or, in a CSV field, as a bare token. It is deliberately a single
#: unmistakable literal: a generic word like "superseded" or "withdrawn" can be
#: satisfied by prose about something else entirely, which is exactly the rescue
#: the mutation review exploited.
BREADTH_HISTORICAL_MARKER = "td-b34-breadth-historical"

#: Rendered form, for authors and for the non-vacuity self-test.
BREADTH_HISTORICAL_MARKER_HTML = "<!-- TD-B34-BREADTH-HISTORICAL -->"


# --------------------------------------------------------------------------- #
# Normalisation
# --------------------------------------------------------------------------- #
def norm(raw: str) -> str:
    """Lower-cased text with markdown emphasis, blockquote markers and wraps collapsed.

    Identical in behaviour to the normaliser the governance tests already use, so
    a phrase written across a line break still matches.
    """
    raw = raw.replace("*", "").replace("`", "")
    raw = re.sub(r"(?m)^\s*>\s?", "", raw)
    return re.sub(r"\s+", " ", raw).strip().lower()


def anchor_of(flat: str) -> str:
    """Stable 16-hex anchor for a normalised passage text."""
    return hashlib.sha256(flat.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# The passage model
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Passage:
    """One structural unit of a governed document."""

    rel: str          #: repository-relative POSIX path
    heading: str      #: innermost markdown heading (normalised), or a CSV row/column key
    line: int         #: 1-based first line of the passage
    kind: str         #: 'paragraph' | 'list-item' | 'blockquote' | 'table-row' | 'csv-field'
    raw: str          #: exact source text of the passage
    flat: str         #: normalised text

    @property
    def anchor(self) -> str:
        return anchor_of(self.flat)

    @property
    def address(self) -> Tuple[str, str, str]:
        """The pinned identity of a passage: (file, heading, anchor).

        The heading is included so that relocating a historical passage into a
        live section is a change, not a silent move.
        """
        return (self.rel, self.heading, self.anchor)

    def __str__(self) -> str:  # pragma: no cover - diagnostics only
        return f"{self.rel}:{self.line} [{self.kind}] under {self.heading!r}"


_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")
_TOP_ITEM_RE = re.compile(r"^(?:[-*+]|\d+[.)])[ \t]+")
_QUOTE_RE = re.compile(r"^[ \t]*>")
_TABLE_RE = re.compile(r"^[ \t]*\|")
_TABLE_SEP_RE = re.compile(r"^[ \t]*\|[\s:|-]*\|?[ \t]*$")


def markdown_passages(path: Path, rel: str) -> List[Passage]:
    """Split a Markdown file into structural passages.

    A heading line is not itself a passage: it names the section its passages sit
    in. A table separator row is dropped. Everything else falls into exactly one
    passage, so no governed phrase can land outside the model.
    """
    lines = path.read_text(encoding="utf-8").split("\n")
    out: List[Passage] = []
    buf: List[str] = []
    start = 1
    heading = "<preamble>"
    kind = "paragraph"

    def flush() -> None:
        if buf and any(s.strip() for s in buf):
            raw = "\n".join(buf)
            out.append(
                Passage(rel=rel, heading=heading, line=start, kind=kind,
                        raw=raw, flat=norm(raw))
            )

    def classify(line: str) -> str:
        if _TABLE_RE.match(line):
            return "table-row"
        if _QUOTE_RE.match(line):
            return "blockquote"
        if _TOP_ITEM_RE.match(line):
            return "list-item"
        return "paragraph"

    for i, line in enumerate(lines, 1):
        head = _HEADING_RE.match(line)
        if head:
            flush()
            buf, start, kind = [], i + 1, "paragraph"
            heading = norm(head.group(2))
            continue
        if not line.strip():
            flush()
            buf, start, kind = [], i + 1, "paragraph"
            continue
        if _TABLE_SEP_RE.match(line) and _TABLE_RE.match(line):
            flush()
            buf, start, kind = [], i + 1, "paragraph"
            continue
        this = classify(line)
        # A new passage begins at every table row, every top-level list item, and
        # at any transition into or out of a blockquote. Indented continuation
        # lines stay with the item or paragraph they belong to.
        starts_new = buf and (
            this == "table-row"
            or this == "list-item"
            or (this == "blockquote") != (kind == "blockquote")
        )
        if starts_new:
            flush()
            buf, start = [], i
        if not buf:
            start, kind = i, this
        buf.append(line)

    flush()
    return out


def csv_passages(path: Path, rel: str) -> List[Passage]:
    """Split a CSV file into one passage per (row, column) field.

    Field granularity is exact: a claim in one cell can never be excused by the
    contents of a neighbouring cell or row.
    """
    text = path.read_text(encoding="utf-8-sig")
    reader = list(csv.reader(io.StringIO(text)))
    if not reader:
        return []
    header = [h.strip() for h in reader[0]]
    out: List[Passage] = []
    for r, row in enumerate(reader[1:], start=2):
        key = row[0].strip() if row else ""
        for c, cell in enumerate(row):
            if not cell.strip():
                continue
            column = header[c] if c < len(header) else f"column{c}"
            out.append(
                Passage(
                    rel=rel,
                    heading=f"row {key} / column {column}",
                    line=r,
                    kind="csv-field",
                    raw=cell,
                    flat=norm(cell),
                )
            )
    return out


#: Directories whose Markdown and CSV carry study-v2 governance prose. Globbed
#: rather than listed, so a NEW governance document is governed the moment it is
#: added: the backstop cannot be escaped by writing a directive in a new file.
GOVERNED_GLOBS: Tuple[str, ...] = (
    "docs/*.md",
    "docs/v2/*.md",
    "docs/v2/*.csv",
    "experiments/v2/tasks/public/*.md",
    "experiments/v2/tasks/public/*.csv",
    "experiments/v2/*/README.md",
    "experiments/v2/README.md",
    "README.md",
)

#: Files that must be inside the governed set. A glob that stops matching one of
#: these is a defect in the guard, not a licence.
GOVERNED_REQUIRED: Tuple[str, ...] = (
    "docs/v2/README.md",
    "docs/v2/CRITICAL_DESIGN_DECISIONS.md",
    "docs/v2/DEPENDENCY_TASK_FEASIBILITY.md",
    "docs/v2/OPEN_DECISIONS.csv",
    "docs/v2/OPEN_DECISIONS.md",
    "docs/v2/PILOT_AND_POWER_POLICY.md",
    "docs/v2/STATISTICAL_ANALYSIS_PLAN.md",
    "docs/v2/TASK_AUTHORING_POLICY.md",
    "experiments/v2/tasks/public/TASK_AUTHORING_REPORT.md",
    "experiments/v2/tasks/public/TASK_INDEX.csv",
)


def governed_files(repo: Path = REPO) -> List[str]:
    """Repository-relative POSIX paths of every governed document."""
    seen: Dict[str, None] = {}
    for pattern in GOVERNED_GLOBS:
        for p in sorted(repo.glob(pattern)):
            if p.is_file():
                seen[p.relative_to(repo).as_posix()] = None
    return list(seen)


def all_passages(repo: Path = REPO) -> List[Passage]:
    """Every structural passage of every governed document."""
    out: List[Passage] = []
    for rel in governed_files(repo):
        path = repo / rel
        if path.suffix.lower() == ".csv":
            out.extend(csv_passages(path, rel))
        else:
            out.extend(markdown_passages(path, rel))
    return out


def matching_passages(
    patterns: Dict[str, str], repo: Path = REPO,
    passages: Sequence[Passage] | None = None,
) -> List[Tuple[Passage, List[str]]]:
    """Passages whose normalised text matches at least one named pattern."""
    compiled = {k: re.compile(v) for k, v in patterns.items()}
    out = []
    for p in (passages if passages is not None else all_passages(repo)):
        hits = sorted(k for k, rx in compiled.items() if rx.search(p.flat))
        if hits:
            out.append((p, hits))
    return out


# --------------------------------------------------------------------------- #
# The claim register
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RegisteredClaim:
    """One passage that is licensed to carry a governed vocabulary.

    ``required`` holds exact normalised substrings that must be present in *this
    passage's own text*. ``forbidden`` holds exact normalised substrings that must
    be absent from it — used to pin the polarity of a claim, so an inversion is a
    failure even when the neighbourhood still reads as a denial.
    """

    rel: str
    heading: str
    anchor: str
    why: str
    required: Tuple[str, ...] = ()
    forbidden: Tuple[str, ...] = ()

    @property
    def address(self) -> Tuple[str, str, str]:
        return (self.rel, self.heading, self.anchor)


def register_index(claims: Iterable[RegisteredClaim]) -> Dict[Tuple[str, str, str], RegisteredClaim]:
    index: Dict[Tuple[str, str, str], RegisteredClaim] = {}
    for claim in claims:
        assert claim.address not in index, f"duplicate register entry {claim.address}"
        index[claim.address] = claim
    return index


def check_register(
    patterns: Dict[str, str],
    claims: Sequence[RegisteredClaim],
    repo: Path = REPO,
    passages: Sequence[Passage] | None = None,
) -> List[str]:
    """Compare the governed documents against a pinned claim register.

    Returns a list of human-readable problems; an empty list means the register
    and the documents agree exactly. Four independent classes are reported:

      * ``UNREGISTERED`` — a governed phrase in a passage the register does not
        license. This is the document-wide backstop: it fires for a new directive
        anywhere, including in a file that did not exist before, and for an edit
        to a registered passage (its anchor moves, so it is no longer the
        registered passage).
      * ``MISSING`` — a registered passage that is no longer present. A guard that
        silently stops policing text is worse than no guard.
      * ``TOKEN`` — a registered passage that lost a required token, e.g. its
        explicit historical classification.
      * ``POLARITY`` — a registered passage that gained a forbidden token, e.g.
        the inverted form of the claim it exists to deny.
    """
    found = {p.address: (p, hits) for p, hits in matching_passages(patterns, repo, passages)}
    index = register_index(claims)
    problems: List[str] = []

    for address, (passage, hits) in sorted(found.items()):
        if address in index:
            continue
        problems.append(
            f"UNREGISTERED {passage} matched {hits}; anchor {passage.anchor}. "
            f"Either this passage is a NEW live claim and must be removed, or it "
            f"is a deliberate change to registered history and the register must "
            f"be updated by an explicit governance decision. Text: {passage.flat[:300]!r}"
        )

    for address, claim in sorted(index.items()):
        if address not in found:
            problems.append(
                f"MISSING registered passage {claim.rel} under {claim.heading!r} "
                f"anchor {claim.anchor} ({claim.why}). It was edited, moved or "
                f"deleted; the guard is no longer policing the text it was written "
                f"for."
            )
            continue
        passage = found[address][0]
        for token in claim.required:
            if token not in passage.flat:
                problems.append(
                    f"TOKEN {passage} is missing its required token {token!r} "
                    f"({claim.why})"
                )
        for token in claim.forbidden:
            if token in passage.flat:
                problems.append(
                    f"POLARITY {passage} contains the forbidden token {token!r} "
                    f"({claim.why})"
                )
    return problems


def passages_by_file(repo: Path = REPO) -> Dict[str, List[Passage]]:
    out: Dict[str, List[Passage]] = {}
    for p in all_passages(repo):
        out.setdefault(p.rel, []).append(p)
    return out


def find_passage(rel: str, contains: str, repo: Path = REPO) -> Passage:
    """The single passage of ``rel`` whose normalised text contains ``contains``.

    Used for section/row-exact assertions: the caller names the claim, and the
    helper refuses to guess when the claim is duplicated or absent.
    """
    hits = [p for p in passages_by_file(repo).get(rel, []) if contains in p.flat]
    assert len(hits) == 1, (
        f"expected exactly one passage in {rel} containing {contains!r}, "
        f"found {len(hits)}"
    )
    return hits[0]


def iter_lines(rel: str, repo: Path = REPO) -> Iterator[str]:  # pragma: no cover
    yield from (repo / rel).read_text(encoding="utf-8").splitlines()


# --------------------------------------------------------------------------- #
# The governed vocabularies
# --------------------------------------------------------------------------- #
#: The WITHDRAWN `TD-B34` breadth objective, in every wording it appears in.
#: Matching text is permitted only in a passage the breadth register licenses, and
#: every such passage must carry BREADTH_HISTORICAL_MARKER in its own text.
BREADTH_VOCABULARY: Dict[str, str] = {
    "leaf-rule-breadth-directive":
        r"genuinely different existing\s+dependency-direction\s+leaf rules",
    "source-target-boundary-breadth":
        r"leaf rules and source/target boundaries",
    "unused-implemented-leaves-reason":
        r"unused implemented dependency leaf relationships",
    "additional-distinct-decisions":
        r"additional distinct decisions",
    "insufficient-distinct-decisions":
        r"(?:enough|sufficient|too few)\s+distinct dependency-direction decisions"
        r"|distinct dependency-direction decisions to support",
}

#: Any way of naming a fourth (or larger) decision cluster. The demonstrated
#: ceiling is THREE task-creatable clusters, so every occurrence must sit in a
#: passage the fourth-cluster register licenses, carrying that passage's own exact
#: denial and none of its inverted forms.
_COUNT_WORD = r"(?:fourth|4th|four|4|fifth|5th|five|5)"
FOURTH_CLUSTER_VOCABULARY: Dict[str, str] = {
    "count-word-cluster": rf"{_COUNT_WORD}\s+(?:[\w/-]+\s+){{0,3}}clusters?",
    "cluster-count-assignment": r"clusters?\s*[:=]\s*(?:4|5)\b",
}
