#!/usr/bin/env python3
"""Public-task leakage validator for AFCI-Bench study v2.

Enforces CRITICAL_DESIGN_DECISIONS D2: a PUBLIC v2 task file must contain
functional requirements and observable behaviour only, and must never carry a
hidden design detail — architecture instructions (MAD rules, boundary/layer/
dependency direction, contract/port placement), prescribed repository paths or
source filenames, hidden-test or withheld-grading clues, reset/checkpoint clues,
condition names, opportunity/rule ids, evaluator/oracle clues, expected
implementations, or legitimate-alternative disclosures. Term patterns live in
docs/v2/TASK_LEAKAGE_TERMS.yml.

Two tiers (see the terms file):

* ``hard_leak``       - hidden-design instructions or clues. Fail closed; never
  exceptable.
* ``review_required`` - ambiguous terms that can be legitimate functional
  language. A finding passes only if a matching **approved** reviewed exception
  covers it (front-matter ``leakage_exceptions`` with ``id``, ``location``,
  ``justification``, ``reviewer`` and ``approved``). Malformed, unapproved, or
  mislocated governance fails closed.

What is scanned (all of it, for every discovered task):

1. **Front matter** — every string value and key, at any nesting depth, in any
   list or mapping. YAML metadata is not treated as safe. The
   ``leakage_exceptions`` subtree is excluded, because a justification must be
   able to quote the term it excepts.
2. **Body physical lines** — for precise line numbers.
3. **Body logical text** — wrapped prose joined within a paragraph or list item,
   so a phrase split across adjacent lines is still detected. Headings, blank
   lines, list-item starts and fenced code blocks are unit boundaries, so
   unrelated paragraphs are never glued together.

Discovery is recursive with an explicit extension allowlist, refuses v1/v0
material, never treats the authoring report or a README as a benchmark task, and
is reconciled against ``experiments/v2/tasks/public/TASK_INDEX.csv``.

A clean result means **no detected leakage**. It is not proof that a task is
scientifically valid, well specified, or feasible — those are separate reviews
(see docs/v2/TASK_AUTHORING_POLICY.md).

Pure file inspection; no model is invoked.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import yaml  # PyYAML; part of the study-v2 dependency base

REPO = Path(__file__).resolve().parents[3]
TERMS_PATH = REPO / "docs" / "v2" / "TASK_LEAKAGE_TERMS.yml"
DEFAULT_TASKS_DIR = REPO / "experiments" / "v2" / "tasks"
INDEX_RELPATH = Path("public") / "TASK_INDEX.csv"

#: The only extensions a public task body may use.
TASK_EXTENSIONS = {".md"}
#: Extensions that look like a task body but are not supported. A task-like file
#: with one of these is a hard failure, never a silent skip.
UNSUPPORTED_TASK_EXTENSIONS = {
    ".markdown", ".mdx", ".txt", ".text", ".rst", ".org", ".adoc", ".html", ".htm",
}
#: Documented non-task Markdown files inside the tasks tree.
NON_TASK_STEMS = {"readme", "task_authoring_report"}
#: A file whose stem looks like a task id (PT01, PR02, T07, ...).
TASK_ID_RE = re.compile(r"^(?:PT|PR|T)\d{2,}$", re.IGNORECASE)
#: Directories inside the tasks tree that hold no task bodies.
SKIP_DIR_NAMES = {"tests", "__pycache__", ".pytest_cache", ".mypy_cache", "fixtures"}

#: Accepted spellings of an approved exception.
_APPROVED_VALUES = {"approved", "true", "yes"}


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Term:
    id: str
    tier: str  # "hard_leak" | "review_required"
    category: str
    regex: "re.Pattern"
    why: str = ""


@dataclass
class Finding:
    location: str  # "body:42" | "front-matter:title"
    line: int  # 0 for front-matter findings
    term_id: str
    tier: str
    category: str
    text: str
    line_text: str = ""
    wrapped: bool = False  # matched only after joining wrapped lines
    covered: bool = False


@dataclass
class TaskValidation:
    path: str
    findings: List[Finding] = field(default_factory=list)
    exception_errors: List[str] = field(default_factory=list)

    @property
    def hard_leaks(self) -> List[Finding]:
        return [f for f in self.findings if f.tier == "hard_leak"]

    @property
    def uncovered_reviews(self) -> List[Finding]:
        return [f for f in self.findings if f.tier == "review_required" and not f.covered]

    @property
    def ok(self) -> bool:
        return not self.hard_leaks and not self.uncovered_reviews and not self.exception_errors


@dataclass
class Discovery:
    """Result of recursive public-task discovery."""

    tasks: List[Path] = field(default_factory=list)
    rejections: List[str] = field(default_factory=list)


@dataclass
class LogicalUnit:
    start_line: int
    text: str
    physical: List[Tuple[int, str]]


# --------------------------------------------------------------------------- #
# Term loading
# --------------------------------------------------------------------------- #
def load_terms(path: Path = TERMS_PATH) -> List[Term]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    terms: List[Term] = []
    for tier in ("hard_leak", "review_required"):
        for entry in data.get(tier, []) or []:
            terms.append(
                Term(
                    id=entry["id"],
                    tier=tier,
                    category=entry.get("category", ""),
                    regex=re.compile(entry["pattern"], re.IGNORECASE),
                    why=entry.get("why", ""),
                )
            )
    if not terms:
        raise ValueError(f"no leakage terms loaded from {path}")
    return terms


def term_ids(terms: Sequence[Term], tier: str) -> set:
    return {t.id for t in terms if t.tier == tier}


# --------------------------------------------------------------------------- #
# Front matter
# --------------------------------------------------------------------------- #
def split_front_matter(text: str):
    """Return (front_matter_text, body_text, body_start_line). A front-matter
    block is a leading ``---`` line up to the next ``---`` line."""
    lines = text.splitlines(keepends=True)
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                fm = "".join(lines[1:i])
                body = "".join(lines[i + 1:])
                return fm, body, i + 2  # 1-indexed line of first body line
    return "", text, 1


def iter_front_matter_strings(node, prefix: str = "") -> Iterator[Tuple[str, str]]:
    """Yield ``(dotted_key, text)`` for every string reachable in parsed front
    matter — values at any depth, plus mapping keys. The ``leakage_exceptions``
    subtree is skipped so a justification may quote the term it excepts."""
    if isinstance(node, dict):
        for key, value in node.items():
            key_str = str(key)
            if key_str == "leakage_exceptions":
                continue
            path = f"{prefix}.{key_str}" if prefix else key_str
            yield (f"{path} (key)", key_str)
            yield from iter_front_matter_strings(value, path)
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            yield from iter_front_matter_strings(item, f"{prefix}[{idx}]")
    elif isinstance(node, str):
        yield (prefix or "<root>", node)
    elif node is not None and not isinstance(node, (int, float, bool)):
        yield (prefix or "<root>", str(node))


# --------------------------------------------------------------------------- #
# Body normalisation: physical lines + wrap-aware logical units
# --------------------------------------------------------------------------- #
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_TABLE_ROW_RE = re.compile(r"^\s*\|")


def logical_units(body: str, body_start_line: int) -> List[LogicalUnit]:
    """Join hard-wrapped prose into logical units so a phrase split across
    adjacent lines is detectable, while preserving section boundaries.

    Boundaries (a unit never spans one): a blank line, a heading, the start of a
    list item, a table row, and a fenced code block. Lines inside a fence are
    each their own unit, so code samples are still scanned but never glued to
    surrounding prose.
    """
    units: List[LogicalUnit] = []
    current: Optional[LogicalUnit] = None
    in_fence = False

    def flush() -> None:
        nonlocal current
        if current is not None:
            units.append(current)
            current = None

    for idx, raw in enumerate(body.splitlines()):
        lineno = body_start_line + idx
        stripped = raw.strip()

        if _FENCE_RE.match(raw):
            flush()
            in_fence = not in_fence
            units.append(LogicalUnit(lineno, stripped, [(lineno, raw)]))
            continue

        if in_fence:
            flush()
            if stripped:
                units.append(LogicalUnit(lineno, stripped, [(lineno, raw)]))
            continue

        if not stripped:
            flush()
            continue

        if _HEADING_RE.match(raw) or _TABLE_ROW_RE.match(raw):
            flush()
            units.append(LogicalUnit(lineno, stripped, [(lineno, raw)]))
            continue

        if _LIST_ITEM_RE.match(raw):
            flush()
            current = LogicalUnit(lineno, stripped, [(lineno, raw)])
            continue

        if current is None:
            current = LogicalUnit(lineno, stripped, [(lineno, raw)])
        else:
            current.text = f"{current.text} {stripped}"
            current.physical.append((lineno, raw))

    flush()
    return units


def scan_body(body: str, body_start_line: int, terms: Sequence[Term]) -> List[Finding]:
    """Scan a task body on both physical lines and wrap-normalised logical text.

    A term found on a single physical line is reported at that line. A term found
    only after joining wrapped lines is reported at the unit's first line and
    flagged ``wrapped``. Findings are de-duplicated per (term, line).
    """
    findings: List[Finding] = []
    seen: set = set()

    for idx, line in enumerate(body.splitlines()):
        lineno = body_start_line + idx
        for term in terms:
            m = term.regex.search(line)
            if m and (term.id, lineno) not in seen:
                seen.add((term.id, lineno))
                findings.append(
                    Finding(
                        location=f"body:{lineno}",
                        line=lineno,
                        term_id=term.id,
                        tier=term.tier,
                        category=term.category,
                        text=m.group(0),
                        line_text=line,
                    )
                )

    for unit in logical_units(body, body_start_line):
        if len(unit.physical) < 2:
            continue  # single-line units are already covered above
        for term in terms:
            m = term.regex.search(unit.text)
            if not m:
                continue
            if any(term.regex.search(raw) for _, raw in unit.physical):
                continue  # already reported on a physical line
            key = (term.id, unit.start_line)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                Finding(
                    location=f"body:{unit.start_line}",
                    line=unit.start_line,
                    term_id=term.id,
                    tier=term.tier,
                    category=term.category,
                    text=m.group(0),
                    line_text=unit.text,
                    wrapped=True,
                )
            )

    findings.sort(key=lambda f: (f.line, f.term_id))
    return findings


def scan_front_matter(fm_data, terms: Sequence[Term]) -> List[Finding]:
    """Scan every string in parsed front matter. Metadata is not safe by virtue
    of being YAML: a leaky title or note is leakage."""
    findings: List[Finding] = []
    seen: set = set()
    for key_path, text in iter_front_matter_strings(fm_data):
        for term in terms:
            m = term.regex.search(text)
            if not m:
                continue
            key = (term.id, key_path)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                Finding(
                    location=f"front-matter:{key_path}",
                    line=0,
                    term_id=term.id,
                    tier=term.tier,
                    category=term.category,
                    text=m.group(0),
                    line_text=text,
                )
            )
    findings.sort(key=lambda f: (f.location, f.term_id))
    return findings


# --------------------------------------------------------------------------- #
# Exceptions (fail closed)
# --------------------------------------------------------------------------- #
def _parse_exceptions(
    raw_exceptions, review_ids: set, hard_ids: set, errors: List[str]
) -> List[dict]:
    """Validate reviewed exceptions. Every exception must carry a review-required
    pattern id, an exact location, a justification, a reviewer, and an approval
    state. Anything else fails closed."""
    valid: List[dict] = []
    if raw_exceptions is None:
        return valid
    if not isinstance(raw_exceptions, list):
        errors.append("leakage_exceptions must be a list")
        return valid

    for exc in raw_exceptions:
        if not isinstance(exc, dict):
            errors.append(f"exception is not a mapping: {exc!r}")
            continue
        eid = exc.get("id")
        location = str(exc.get("location") or "").strip()
        justification = str(exc.get("justification") or "").strip()
        reviewer = str(exc.get("reviewer") or "").strip()
        approved_raw = exc.get("approved")
        if isinstance(approved_raw, bool):
            approved = approved_raw
        else:
            approved = str(approved_raw or "").strip().lower() in _APPROVED_VALUES

        if eid in hard_ids:
            errors.append(
                f"exception targets hard-leak id {eid!r}; hidden-design instructions "
                "are never exceptable"
            )
            continue
        if eid not in review_ids:
            errors.append(f"exception targets unknown term id {eid!r}")
            continue
        if not location:
            errors.append(f"exception for {eid!r} has no exact location (fail closed)")
            continue
        if not justification:
            errors.append(f"exception for {eid!r} has no justification (fail closed)")
            continue
        if not reviewer:
            errors.append(f"exception for {eid!r} has no reviewer (fail closed)")
            continue
        if not approved:
            errors.append(
                f"exception for {eid!r} is not approved (approved={approved_raw!r}; fail closed)"
            )
            continue
        valid.append(
            {
                "id": eid,
                "location": location,
                "match": exc.get("match"),
                "justification": justification,
                "reviewer": reviewer,
            }
        )
    return valid


def validate_task_text(text: str, terms: Sequence[Term], path: str = "<text>") -> TaskValidation:
    fm, body, body_start = split_front_matter(text)
    result = TaskValidation(path=path)

    fm_data: dict = {}
    if fm.strip():
        try:
            loaded = yaml.safe_load(fm)
            fm_data = loaded if isinstance(loaded, dict) else {}
            if loaded is not None and not isinstance(loaded, dict):
                result.exception_errors.append("front matter must be a mapping")
        except yaml.YAMLError as exc:
            result.exception_errors.append(f"front matter is not valid YAML: {exc}")

    result.findings = scan_front_matter(fm_data, terms) + scan_body(body, body_start, terms)

    review_ids = term_ids(terms, "review_required")
    hard_ids = term_ids(terms, "hard_leak")
    valid_exceptions = _parse_exceptions(
        fm_data.get("leakage_exceptions"), review_ids, hard_ids, result.exception_errors
    )

    for f in result.findings:
        if f.tier != "review_required":
            continue
        for exc in valid_exceptions:
            if exc["id"] != f.term_id:
                continue
            if exc["location"] != f.location:
                continue
            match = exc.get("match")
            if match and str(match).lower() not in f.line_text.lower():
                continue
            f.covered = True
            break

    return result


def validate_task_file(path, terms: Optional[Sequence[Term]] = None) -> TaskValidation:
    terms = terms if terms is not None else load_terms()
    text = Path(path).read_text(encoding="utf-8")
    return validate_task_text(text, terms, path=str(path))


# --------------------------------------------------------------------------- #
# v1 protection + recursive discovery
# --------------------------------------------------------------------------- #
def is_v1_path(path) -> bool:
    """True if the path belongs to v1 / v0 material, which must never be scanned."""
    p = Path(path).as_posix().lower()
    return (
        "/archive/" in p
        or p.endswith("/archive")
        or "tasks_v0" in p
        or "/v1/" in p
        or p.endswith("/v1")
    )


def discover(tasks_dir=DEFAULT_TASKS_DIR) -> Discovery:
    """Recursively discover public v2 task bodies.

    * Recurses through the whole tasks tree, so a nested task cannot escape.
    * Accepts only ``TASK_EXTENSIONS``.
    * **Rejects** a task-like file (stem PT01/PR02/T07...) that uses an
      unsupported extension, instead of silently skipping it.
    * Never returns a README, the authoring report, or any v1/v0 path.
    """
    tasks_dir = Path(tasks_dir)
    result = Discovery()
    if not tasks_dir.is_dir():
        return result

    for p in sorted(tasks_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(tasks_dir)
        if any(part in SKIP_DIR_NAMES for part in rel.parts[:-1]):
            continue
        if is_v1_path(p):
            continue
        stem_lower = p.stem.lower()
        suffix_lower = p.suffix.lower()
        if stem_lower in NON_TASK_STEMS:
            continue
        if suffix_lower in TASK_EXTENSIONS:
            result.tasks.append(p)
        elif suffix_lower in UNSUPPORTED_TASK_EXTENSIONS and TASK_ID_RE.match(p.stem):
            result.rejections.append(
                f"task-like file with unsupported extension (only "
                f"{sorted(TASK_EXTENSIONS)} are scanned): {rel.as_posix()}"
            )
    result.tasks.sort()
    return result


def discover_public_tasks(tasks_dir=DEFAULT_TASKS_DIR) -> List[Path]:
    """Backwards-compatible view of :func:`discover` returning task paths only."""
    return discover(tasks_dir).tasks


# --------------------------------------------------------------------------- #
# Index reconciliation
# --------------------------------------------------------------------------- #
def read_index_ids(index_path) -> List[str]:
    index_path = Path(index_path)
    with open(index_path, newline="", encoding="utf-8") as fh:
        return [r["task_id"].strip() for r in csv.DictReader(fh) if r.get("task_id", "").strip()]


def front_matter_id(path) -> Optional[str]:
    fm, _body, _start = split_front_matter(Path(path).read_text(encoding="utf-8"))
    if not fm.strip():
        return None
    try:
        data = yaml.safe_load(fm)
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("id")
    return str(value).strip() if value is not None else None


def reconcile_with_index(discovery: Discovery, index_path) -> List[str]:
    """Cross-check discovered task bodies against TASK_INDEX.csv.

    Fails when an indexed task file is missing, a discovered task is not indexed,
    a task id is duplicated (in the index or across files), or a filename and its
    front-matter id disagree.
    """
    errors: List[str] = list(discovery.rejections)
    index_path = Path(index_path)
    if not index_path.is_file():
        errors.append(f"task index not found: {index_path}")
        return errors

    index_ids = read_index_ids(index_path)
    dupes = sorted({i for i in index_ids if index_ids.count(i) > 1})
    if dupes:
        errors.append(f"duplicate task ids in {index_path.name}: {dupes}")

    by_id: Dict[str, List[str]] = {}
    for p in discovery.tasks:
        fm_id = front_matter_id(p)
        if fm_id is None:
            errors.append(f"{p.name}: no front-matter id")
            continue
        if fm_id != p.stem:
            errors.append(f"{p.name}: front-matter id {fm_id!r} does not match filename stem {p.stem!r}")
        by_id.setdefault(fm_id, []).append(p.as_posix())

    for fm_id, paths in sorted(by_id.items()):
        if len(paths) > 1:
            errors.append(f"duplicate task id {fm_id!r} in: {sorted(paths)}")

    missing = sorted(set(index_ids) - set(by_id))
    if missing:
        errors.append(f"indexed tasks with no discovered task file: {missing}")
    unindexed = sorted(set(by_id) - set(index_ids))
    if unindexed:
        errors.append(f"discovered tasks that are not in {index_path.name}: {unindexed}")

    return errors


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _report(result: TaskValidation) -> None:
    status = "OK" if result.ok else "LEAK"
    print(f"[{status}] {result.path}")
    for f in result.hard_leaks:
        tag = " (wrapped)" if f.wrapped else ""
        print(f"  - HARD  {f.location}{tag}: [{f.term_id}/{f.category}] matched {f.text!r}")
    for f in result.uncovered_reviews:
        tag = " (wrapped)" if f.wrapped else ""
        print(
            f"  - REVIEW {f.location}{tag}: [{f.term_id}/{f.category}] matched {f.text!r} "
            "(no approved reviewed exception)"
        )
    for e in result.exception_errors:
        print(f"  - EXC   {e}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Public-task leakage validator (study v2).")
    parser.add_argument("paths", nargs="*", help="Task .md files (default: scan experiments/v2/tasks/).")
    parser.add_argument(
        "--tasks-dir", default=str(DEFAULT_TASKS_DIR), help="Root of the public tasks tree."
    )
    parser.add_argument(
        "--no-index-check",
        action="store_true",
        help="Skip TASK_INDEX.csv reconciliation (explicit-path runs skip it anyway).",
    )
    args = parser.parse_args(argv)

    terms = load_terms()
    tasks_dir = Path(args.tasks_dir)
    structural_errors: List[str] = []

    if args.paths:
        refused = [p for p in args.paths if is_v1_path(p)]
        if refused:
            print(f"refusing to scan v1/v0 task paths: {refused}", file=sys.stderr)
            return 2
        paths = [Path(p) for p in args.paths]
    else:
        discovery = discover(tasks_dir)
        paths = discovery.tasks
        if not args.no_index_check:
            structural_errors = reconcile_with_index(discovery, tasks_dir / INDEX_RELPATH)
        else:
            structural_errors = list(discovery.rejections)

    if not paths and not structural_errors:
        print("no public v2 task files to validate (none authored yet)")
        return 0

    failed = 0
    for p in paths:
        result = validate_task_file(p, terms)
        _report(result)
        if not result.ok:
            failed += 1

    print(f"\n{len(paths)} task file(s); {failed} with leakage.")

    if structural_errors:
        print("\nstructural failures:")
        for e in structural_errors:
            print(f"  - {e}")

    if failed or structural_errors:
        return 1
    print("no detected leakage (this is not proof of scientific validity)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
