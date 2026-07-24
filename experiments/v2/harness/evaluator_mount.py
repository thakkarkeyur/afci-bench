"""Evaluator-mount boundary predicates (docs/v2/EVALUATOR_MOUNT_POLICY.md).

Pure, dependency-free helpers shared by the harness tests. They decide whether a
hidden-evaluator mount is legally placed relative to a coding worktree and whether
a coding worktree is free of forbidden (answer-bearing) evaluator artifacts.

No model is invoked; nothing here reads secrets or contents beyond file names.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import List

# Exact basenames that must never appear inside a coding worktree.
FORBIDDEN_BASENAMES = {
    "evaluator_manifest.json",
    "oracle_result.json",
    "architecture_finding.json",
    "acceptance_result.json",
    "guard_result.json",
}

# Basename glob patterns (case-insensitive) that must never appear.
FORBIDDEN_GLOBS = (
    "*.evaluator.json",
    "expected_layers.*",
    "prohibited_layers.*",
    "required_areas.*",
    "prohibited_areas.*",
    "legitimate_alternatives.*",
    "legitimate_answers.*",
)

# Directory basenames that must never appear (hidden test suites, expected sets).
FORBIDDEN_DIR_NAMES = {"hidden", "hidden_tests"}


def real(path) -> Path:
    """Canonical, symlink-resolved absolute path (fail-closed base for checks)."""
    return Path(path).resolve()


def mount_is_inside_worktree(worktree, mount) -> bool:
    """True when ``mount`` is the worktree itself or nested inside it (after
    resolving real paths). Such a mount MUST be rejected."""
    w = real(worktree)
    m = real(mount)
    if m == w:
        return True
    return w in m.parents


def evaluator_mount_rejected(worktree, mount) -> bool:
    """A mount is rejected iff it is inside the coding worktree."""
    return mount_is_inside_worktree(worktree, mount)


def _basename_is_forbidden(name: str) -> bool:
    low = name.lower()
    if low in FORBIDDEN_BASENAMES:
        return True
    return any(fnmatch.fnmatch(low, pat) for pat in FORBIDDEN_GLOBS)


def scan_worktree_for_forbidden(worktree) -> List[str]:
    """Return worktree-relative paths of any forbidden evaluator artifacts found
    inside ``worktree``. Empty list means the worktree is clean."""
    root = real(worktree)
    offenders: List[str] = []
    for p in sorted(root.rglob("*")):
        if "__pycache__" in p.parts or ".git" in p.parts:
            continue
        rel = p.relative_to(root).as_posix()
        if p.is_dir():
            if p.name.lower() in FORBIDDEN_DIR_NAMES:
                offenders.append(rel + "/")
        elif _basename_is_forbidden(p.name):
            offenders.append(rel)
    return offenders
