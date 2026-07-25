#!/usr/bin/env python3
"""Public-task architecture-leakage validator for AFCI-Bench study v2.

Enforces CRITICAL_DESIGN_DECISIONS D2: a PUBLIC v2 task file must contain
functional requirements and observable behaviour only, never the hidden
architecture (MAD rules, boundary/layer/dependency instructions, contract/port
placement, "follow the architecture" language, or architecture-specific
acceptance criteria). Term patterns live in docs/v2/TASK_LEAKAGE_TERMS.yml.

Two tiers (see the terms file):

* ``hard_leak``       - architecture INSTRUCTIONS. Fail closed; never exceptable.
* ``review_required`` - ambiguous terms that can be legitimate functional
  language. A finding passes only if a matching reviewed exception (front-matter
  ``leakage_exceptions`` with a non-empty ``justification`` AND ``reviewer``)
  covers it. Malformed governance (an exception missing a justification/reviewer,
  or targeting a hard-leak / unknown id) fails closed.

This validator applies ONLY to future public v2 task files and NEVER scans or
modifies v1 tasks (``archive/``, ``experiments/tasks_v0/``). Pure file
inspection; no model is invoked.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml  # PyYAML; part of the study-v2 dependency base

REPO = Path(__file__).resolve().parents[3]
TERMS_PATH = REPO / "docs" / "v2" / "TASK_LEAKAGE_TERMS.yml"
DEFAULT_TASKS_DIR = REPO / "experiments" / "v2" / "tasks"


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Term:
    id: str
    tier: str  # "hard_leak" | "review_required"
    category: str
    regex: "re.Pattern"


@dataclass
class Finding:
    line: int
    term_id: str
    tier: str
    category: str
    text: str
    line_text: str = ""
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
                )
            )
    return terms


# --------------------------------------------------------------------------- #
# Front-matter + scanning
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


def scan_body(body: str, body_start_line: int, terms: List[Term]) -> List[Finding]:
    findings: List[Finding] = []
    for idx, line in enumerate(body.splitlines()):
        lineno = body_start_line + idx
        for term in terms:
            m = term.regex.search(line)
            if m:
                findings.append(
                    Finding(
                        line=lineno,
                        term_id=term.id,
                        tier=term.tier,
                        category=term.category,
                        text=m.group(0),
                        line_text=line,
                    )
                )
    return findings


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def validate_task_text(text: str, terms: List[Term], path: str = "<text>") -> TaskValidation:
    fm, body, body_start = split_front_matter(text)
    result = TaskValidation(path=path)
    result.findings = scan_body(body, body_start, terms)

    review_ids = {t.id for t in terms if t.tier == "review_required"}
    hard_ids = {t.id for t in terms if t.tier == "hard_leak"}

    raw_exceptions = []
    if fm.strip():
        try:
            fm_data = yaml.safe_load(fm) or {}
        except yaml.YAMLError as exc:
            result.exception_errors.append(f"front-matter is not valid YAML: {exc}")
            fm_data = {}
        raw_exceptions = (fm_data.get("leakage_exceptions") or []) if isinstance(fm_data, dict) else []

    valid_exceptions = []
    for exc in raw_exceptions:
        if not isinstance(exc, dict):
            result.exception_errors.append(f"exception is not a mapping: {exc!r}")
            continue
        eid = exc.get("id")
        justification = str(exc.get("justification") or "").strip()
        reviewer = str(exc.get("reviewer") or "").strip()
        if eid in hard_ids:
            result.exception_errors.append(
                f"exception targets hard-leak id {eid!r}; architecture instructions are never exceptable"
            )
            continue
        if eid not in review_ids:
            result.exception_errors.append(f"exception targets unknown term id {eid!r}")
            continue
        if not justification or not reviewer:
            result.exception_errors.append(
                f"exception for {eid!r} is missing a justification and/or reviewer (fail closed)"
            )
            continue
        valid_exceptions.append(exc)

    for f in result.findings:
        if f.tier != "review_required":
            continue
        for exc in valid_exceptions:
            if exc["id"] != f.term_id:
                continue
            match = exc.get("match")
            if match and str(match).lower() not in f.line_text.lower():
                continue
            f.covered = True
            break

    return result


def validate_task_file(path, terms: Optional[List[Term]] = None) -> TaskValidation:
    terms = terms if terms is not None else load_terms()
    text = Path(path).read_text(encoding="utf-8")
    return validate_task_text(text, terms, path=str(path))


# --------------------------------------------------------------------------- #
# v1 protection + discovery
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


def discover_public_tasks(tasks_dir=DEFAULT_TASKS_DIR) -> List[Path]:
    """Discover public v2 task files. Scans the top-level tasks directory and the
    ``public/`` subdirectory (the authored pilot task bodies live in
    ``experiments/v2/tasks/public/``). README files and any v1/v0 path are never
    returned."""
    tasks_dir = Path(tasks_dir)
    candidates = list(tasks_dir.glob("*.md")) + list((tasks_dir / "public").glob("*.md"))
    out: List[Path] = []
    for p in sorted(candidates):
        if p.name.lower() == "readme.md":
            continue
        if is_v1_path(p):
            continue
        out.append(p)
    return out


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _report(result: TaskValidation) -> None:
    status = "OK" if result.ok else "LEAK"
    print(f"[{status}] {result.path}")
    for f in result.hard_leaks:
        print(f"  - HARD  line {f.line}: [{f.term_id}/{f.category}] matched {f.text!r}")
    for f in result.uncovered_reviews:
        print(f"  - REVIEW line {f.line}: [{f.term_id}/{f.category}] matched {f.text!r} (no reviewed exception)")
    for e in result.exception_errors:
        print(f"  - EXC   {e}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Task .md files (default: scan experiments/v2/tasks/).")
    args = parser.parse_args(argv)

    terms = load_terms()

    if args.paths:
        refused = [p for p in args.paths if is_v1_path(p)]
        if refused:
            print(f"refusing to scan v1/v0 task paths: {refused}", file=sys.stderr)
            return 2
        paths = [Path(p) for p in args.paths]
    else:
        paths = discover_public_tasks()

    if not paths:
        print("no public v2 task files to validate (none authored yet)")
        return 0

    failed = 0
    for p in paths:
        result = validate_task_file(p, terms)
        _report(result)
        if not result.ok:
            failed += 1
    print(f"\n{len(paths)} task file(s); {failed} with leakage.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
