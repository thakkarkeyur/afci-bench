#!/usr/bin/env python3
"""Runner-time enforcement of the model-visible worktree policy (``TD-B22``).

``prepare_model_worktree`` builds the snapshot and records what it built. That
is the *preparation* half of the policy. This module is the *runner-time* half
the policy was always missing: before a model may be launched, the runner
re-derives every claim the preparation made and refuses if any of them no
longer holds.

The nine checks, each with its own refusal code so a failure names itself:

===  ==================================================  ==========================
#    Check                                               Refusal code
===  ==================================================  ==========================
1    the worktree was built by the governed preparer     (delegated: preparer)
2    the manifest is structurally what the preparer      ``PREPARED_MANIFEST_INVALID``
     emits, and its ``content_hash`` recomputes
3    the task body hash equals the approved pin          ``TASK_SHA_MISMATCH``
4    the substrate identity equals the governed one      ``SUBSTRATE_IDENTITY_MISMATCH``
5    every included path is allowlisted                  ``WORKTREE_PATH_NOT_ALLOWLISTED``
6    no file exists that the manifest does not list      ``UNEXPECTED_MODEL_VISIBLE_FILE``
7    architecture delivery is the condition's own, and   ``ARCHITECTURE_DELIVERY_VIOLATION``
     for C1 that is ``none`` with no payload anywhere
8    the bytes on disk still match the manifest          ``PREPARED_WORKTREE_DIRTY``
9    the worktree content hash is recorded               (recorded, not refused)
===  ==================================================  ==========================

Check 5 reuses :func:`substrate_identity.is_allowed_path` and check 7 reuses
:func:`prepare_model_worktree.architecture_delivery_for` and
:func:`prepare_model_worktree.scan_snapshot_violations`, so the runner enforces
the *same* allowlist and the *same* condition semantics the preparer
implements, rather than a second copy that could drift.

**This module does not resolve ``TD-B22``.** It implements runner-time
enforcement; whether that enforcement holds in a live run is a separate,
unperformed validation. It also does not modify ``prepare_model_worktree.py``,
whose manifest still records ``runner_enforcement: "not implemented (TD-B22)"``:
that file is byte-pinned by the private evaluator's public linkage, so editing
it is a linkage-relevant change this package is not authorised to make. The
runner records its own enforcement result in the run record instead.

No model is invoked and no benchmark task is executed.
"""
from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import evaluator_mount as em
import prepare_model_worktree as pmw
import run_governance as gov
import substrate_identity as si

#: Keys the preparer always emits. A manifest missing any of them is not the
#: governed preparer's output and is refused rather than partially trusted.
REQUIRED_MANIFEST_KEYS: Tuple[str, ...] = (
    "schema_version",
    "condition",
    "task_id",
    "task_sha256",
    "task_delivery",
    "architecture_delivery",
    "architecture_sha256",
    "architecture_persistent_path",
    "generic_guidance_delivery",
    "generic_guidance_sha256",
    "allowlist",
    "entry_count",
    "entries",
    "content_hash",
)


@dataclass
class WorktreeEnforcement:
    """The recorded result of runner-time worktree enforcement."""

    condition: str
    task_id: str
    task_sha256: str
    architecture_delivery: str
    entry_count: int
    content_hash: str
    substrate: Dict[str, object]
    checks: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "policy": "docs/v2/MODEL_VISIBLE_WORKTREE_POLICY.md",
            "decision": "TD-B22",
            "enforced_at": "runner-time, before model invocation",
            "condition": self.condition,
            "task_id": self.task_id,
            "task_sha256": self.task_sha256,
            "architecture_delivery": self.architecture_delivery,
            "entry_count": self.entry_count,
            "worktree_content_hash": self.content_hash,
            "substrate": dict(self.substrate),
            "checks": list(self.checks),
            "status": "ENFORCED",
            "live_runtime_validated": False,
        }


def _content_hash_of_entries(entries: Sequence[Dict[str, object]]) -> str:
    """Recompute the preparer's snapshot ``content_hash`` from its entries."""
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda e: str(e["path"])):
        digest.update(f"{entry['path']} {entry['sha256']}\n".encode("utf-8"))
    return digest.hexdigest()


def _on_disk_entries(root: Path) -> List[Dict[str, object]]:
    entries: List[Dict[str, object]] = []
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            entries.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data),
                }
            )
    entries.sort(key=lambda e: str(e["path"]))
    return entries


def verify_prepared_manifest(manifest: Dict[str, object]) -> None:
    """Check 2 — the manifest is the governed preparer's own shape."""
    missing = [k for k in REQUIRED_MANIFEST_KEYS if k not in manifest]
    if missing:
        raise gov.RunnerRefusal(
            gov.PREPARED_MANIFEST_INVALID,
            f"the prepared manifest is missing {missing}; it is not the governed "
            "preparer's output and is not trusted",
        )
    entries = manifest["entries"]
    if not isinstance(entries, list) or not entries:
        raise gov.RunnerRefusal(
            gov.PREPARED_MANIFEST_INVALID, "the prepared manifest lists no entries"
        )
    if manifest["entry_count"] != len(entries):
        raise gov.RunnerRefusal(
            gov.PREPARED_MANIFEST_INVALID,
            f"entry_count {manifest['entry_count']} != {len(entries)} listed entries",
        )
    recomputed = _content_hash_of_entries(entries)
    if recomputed != manifest["content_hash"]:
        raise gov.RunnerRefusal(
            gov.PREPARED_MANIFEST_INVALID,
            f"the manifest content_hash {manifest['content_hash']} does not "
            f"recompute from its own entries ({recomputed})",
        )


def verify_task_identity(manifest: Dict[str, object], expected_sha: str) -> None:
    """Check 3 — the body the model is asked to implement is the approved one."""
    actual = manifest.get("task_sha256")
    if actual != expected_sha:
        raise gov.RunnerRefusal(
            gov.TASK_SHA_MISMATCH,
            f"the prepared run carries task hash {actual}; the approved public "
            f"pin is {expected_sha}",
        )


def verify_allowed_tree(manifest: Dict[str, object], allow_extra: Sequence[str] = ()) -> None:
    """Check 5 — every included path is one the model-visible allowlist admits.

    ``allow_extra`` carries the approved per-condition delivery paths (only C3's
    single repository-instruction file), which are written *after* the allowlist
    walk and are therefore legitimately outside it.
    """
    permitted = {str(p) for p in allow_extra}
    offenders = [
        str(entry["path"])
        for entry in manifest["entries"]
        if str(entry["path"]) not in permitted and not si.is_allowed_path(str(entry["path"]))
    ]
    if offenders:
        raise gov.RunnerRefusal(
            gov.WORKTREE_PATH_NOT_ALLOWLISTED,
            f"the prepared worktree lists paths the allowlist does not admit: "
            f"{sorted(offenders)[:10]}",
        )


def verify_no_unexpected_files(
    root: Path, manifest: Dict[str, object], on_disk: Sequence[Dict[str, object]]
) -> None:
    """Check 6 — the tree contains exactly what the manifest says it contains."""
    listed = {str(e["path"]) for e in manifest["entries"]}
    present = {str(e["path"]) for e in on_disk}
    extra = sorted(present - listed)
    absent = sorted(listed - present)
    if extra:
        raise gov.RunnerRefusal(
            gov.UNEXPECTED_MODEL_VISIBLE_FILE,
            f"{len(extra)} file(s) exist in the model-visible worktree that the "
            f"prepared manifest does not list: {extra[:10]}",
        )
    if absent:
        raise gov.RunnerRefusal(
            gov.PREPARED_WORKTREE_DIRTY,
            f"{len(absent)} manifest entry/entries are missing from the worktree "
            f"before launch: {absent[:10]}",
        )


def verify_architecture_delivery(
    root: Path, manifest: Dict[str, object], condition: str
) -> None:
    """Check 7 — the condition's own delivery, and for C1 that means nothing.

    Three independent ways of being wrong are all caught: the manifest claiming
    the wrong delivery, a payload hash or persistent path existing under a
    no-architecture arm, and an architecture artifact physically present in the
    tree (which the preparer's own sweep detects, reused here rather than
    reimplemented).
    """
    governed = gov.architecture_delivery_for(condition)
    claimed = manifest.get("architecture_delivery")
    if claimed != governed:
        raise gov.RunnerRefusal(
            gov.ARCHITECTURE_DELIVERY_VIOLATION,
            f"{condition} must deliver architecture as {governed!r}; the prepared "
            f"manifest claims {claimed!r}",
        )
    if governed == "none":
        if manifest.get("architecture_sha256") is not None:
            raise gov.RunnerRefusal(
                gov.ARCHITECTURE_DELIVERY_VIOLATION,
                f"{condition} carries an architecture payload hash "
                f"{manifest['architecture_sha256']!r}; the baseline arm receives none",
            )
        if manifest.get("architecture_persistent_path") is not None:
            raise gov.RunnerRefusal(
                gov.ARCHITECTURE_DELIVERY_VIOLATION,
                f"{condition} carries a persistent architecture file "
                f"{manifest['architecture_persistent_path']!r}",
            )
        if manifest.get("generic_guidance_sha256") is not None:
            raise gov.RunnerRefusal(
                gov.ARCHITECTURE_DELIVERY_VIOLATION,
                f"{condition} carries a generic-guidance payload; only C2 may",
            )

    allow_persistent: List[str] = []
    persistent = manifest.get("architecture_persistent_path")
    if isinstance(persistent, str) and persistent:
        allow_persistent.append(persistent)
    violations = pmw.scan_snapshot_violations(root, allow_persistent)
    if violations:
        raise gov.RunnerRefusal(
            gov.ARCHITECTURE_DELIVERY_VIOLATION,
            "the model-visible worktree violates the worktree policy at runner "
            "time: " + "; ".join(violations[:5]),
        )


def verify_bytes_match_manifest(
    manifest: Dict[str, object], on_disk: Sequence[Dict[str, object]]
) -> str:
    """Check 8 — nothing edited the prepared worktree between preparation and launch."""
    listed = {str(e["path"]): str(e["sha256"]) for e in manifest["entries"]}
    drifted = [
        str(e["path"])
        for e in on_disk
        if listed.get(str(e["path"])) != str(e["sha256"])
    ]
    if drifted:
        raise gov.RunnerRefusal(
            gov.PREPARED_WORKTREE_DIRTY,
            f"{len(drifted)} model-visible file(s) differ from the prepared "
            f"manifest before launch: {sorted(drifted)[:10]}",
        )
    recomputed = _content_hash_of_entries(on_disk)
    if recomputed != manifest["content_hash"]:
        raise gov.RunnerRefusal(
            gov.PREPARED_WORKTREE_DIRTY,
            f"the worktree on disk hashes {recomputed}, the prepared manifest "
            f"records {manifest['content_hash']}",
        )
    return recomputed


def enforce_prepared_worktree(
    *,
    root: Path,
    manifest: Dict[str, object],
    condition: str,
    expected_task_sha: str,
    repo: Path = gov.REPO,
    substrate_commit: Optional[str] = None,
    expected_substrate_hash: Optional[str] = None,
    expected_substrate_entries: Optional[int] = None,
) -> WorktreeEnforcement:
    """Run every runner-time worktree check, in order, failing closed."""
    root = Path(root)
    checks: List[Dict[str, str]] = []

    gov.assert_not_canonical_repository(root, repo)
    checks.append(
        {"check": "canonical_repository_not_used", "result": "PASS",
         "detail": f"model-visible worktree {root} is a prepared snapshot outside "
                   f"the canonical repository"}
    )

    verify_prepared_manifest(manifest)
    checks.append(
        {"check": "prepared_manifest_verified", "result": "PASS",
         "detail": f"content_hash recomputes over {manifest['entry_count']} entries"}
    )

    verify_task_identity(manifest, expected_task_sha)
    checks.append(
        {"check": "task_sha_verified", "result": "PASS",
         "detail": f"task body hash {expected_task_sha} matches the approved pin"}
    )

    substrate = gov.assert_substrate_identity(
        repo, substrate_commit, expected_substrate_hash, expected_substrate_entries
    )
    checks.append(
        {"check": "substrate_identity_verified", "result": "PASS",
         "detail": f"{substrate['commit']} hashes {substrate['content_hash']} over "
                   f"{substrate['entry_count']} entries ({substrate['algorithm']})"}
    )

    persistent = manifest.get("architecture_persistent_path")
    verify_allowed_tree(manifest, [persistent] if isinstance(persistent, str) and persistent else [])
    checks.append(
        {"check": "allowed_tree_enforced", "result": "PASS",
         "detail": f"all {manifest['entry_count']} paths are admitted by the "
                   f"model-visible allowlist"}
    )

    on_disk = _on_disk_entries(root)
    verify_no_unexpected_files(root, manifest, on_disk)
    checks.append(
        {"check": "no_unexpected_model_visible_file", "result": "PASS",
         "detail": "the tree contains exactly the manifest's entries"}
    )

    verify_architecture_delivery(root, manifest, condition)
    checks.append(
        {"check": "architecture_delivery_verified", "result": "PASS",
         "detail": f"{condition} architecture_delivery="
                   f"{manifest['architecture_delivery']} with no payload present"}
    )

    content_hash = verify_bytes_match_manifest(manifest, on_disk)
    checks.append(
        {"check": "prepared_bytes_unchanged_before_launch", "result": "PASS",
         "detail": f"worktree bytes hash {content_hash}"}
    )

    checks.append(
        {"check": "worktree_content_hash_recorded", "result": "PASS",
         "detail": content_hash}
    )

    return WorktreeEnforcement(
        condition=condition,
        task_id=str(manifest.get("task_id")),
        task_sha256=str(manifest.get("task_sha256")),
        architecture_delivery=str(manifest.get("architecture_delivery")),
        entry_count=int(manifest["entry_count"]),
        content_hash=content_hash,
        substrate=substrate,
        checks=checks,
    )


# --------------------------------------------------------------------------- #
# Post-run capture
# --------------------------------------------------------------------------- #
@dataclass
class WorktreeCapture:
    """The model-modified worktree, captured with enough provenance to re-score."""

    prepared_content_hash: str
    post_run_content_hash: str
    capture_root: str
    added: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    deleted: List[str] = field(default_factory=list)
    entry_count: int = 0
    unchanged: bool = False

    def to_dict(self) -> dict:
        return {
            "capture_root": self.capture_root,
            "prepared_content_hash": self.prepared_content_hash,
            "post_run_content_hash": self.post_run_content_hash,
            "unchanged": self.unchanged,
            "entry_count": self.entry_count,
            "changed_paths": {
                "added": list(self.added),
                "modified": list(self.modified),
                "deleted": list(self.deleted),
            },
        }


def capture_post_run_worktree(
    *,
    worktree: Path,
    capture_root: Path,
    prepared_manifest: Dict[str, object],
    repo: Path = gov.REPO,
    repository_state_before: Optional[Dict[str, str]] = None,
) -> WorktreeCapture:
    """Copy the model-modified worktree aside and record what changed.

    The prepared starting hash is preserved from the prepared manifest (never
    recomputed from a tree the model has already touched), the post-run state is
    copied to an immutable capture directory that hidden evaluation can mount,
    and the canonical repository is proved unmodified.
    """
    worktree = Path(worktree)
    capture_root = Path(capture_root)
    gov.assert_not_canonical_repository(worktree, repo)

    if repository_state_before is not None:
        gov.assert_canonical_repository_unchanged(repository_state_before, repo)

    if capture_root.exists() and any(capture_root.iterdir()):
        raise gov.RunnerRefusal(
            gov.PREPARED_WORKTREE_DIRTY,
            f"the post-run capture destination is not empty: {capture_root}",
        )
    capture_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(worktree, capture_root, dirs_exist_ok=False)

    # The evaluator mount must live outside the coding worktree.
    if em.evaluator_mount_rejected(worktree, capture_root):
        raise gov.RunnerRefusal(
            gov.CANONICAL_REPOSITORY_EXECUTION_REFUSED,
            f"the post-run capture {capture_root} is inside the coding worktree "
            f"{worktree}; evaluation material must never be reachable from it",
        )

    before = {str(e["path"]): str(e["sha256"]) for e in prepared_manifest["entries"]}
    after_entries = _on_disk_entries(capture_root)
    after = {str(e["path"]): str(e["sha256"]) for e in after_entries}

    added = sorted(set(after) - set(before))
    deleted = sorted(set(before) - set(after))
    modified = sorted(p for p in set(before) & set(after) if before[p] != after[p])
    post_hash = _content_hash_of_entries(after_entries)

    return WorktreeCapture(
        prepared_content_hash=str(prepared_manifest["content_hash"]),
        post_run_content_hash=post_hash,
        capture_root=str(capture_root),
        added=added,
        modified=modified,
        deleted=deleted,
        entry_count=len(after_entries),
        unchanged=not (added or modified or deleted),
    )
