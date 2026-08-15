#!/usr/bin/env python3
"""Canonical source-substrate identity, computed from committed Git blob bytes.

Why this module exists
----------------------
The previous identity procedure hashed the **working tree**: it walked the
allowlist on disk and hashed whatever bytes the filesystem happened to hold.
That made the recorded identity a property of one person's checkout rather than
of the repository. Under Git's end-of-line machinery the same commit
materialises differently on different machines, so the recorded value passed on
the checkout it was computed on and failed everywhere else, including on a fresh
clone of the very same commit. An identity that a fresh clone cannot reproduce
is not an identity.

This module derives the identity from the **committed Git blob bytes** instead.
Blobs are the bytes Git stores, before any smudge/clean or EOL conversion is
applied on the way to the filesystem, so ``core.autocrlf``, ``core.eol`` and the
``eol=`` attributes in ``.gitattributes`` cannot change the result. The hash is a
function of the commit alone.

The algorithm (normative)
-------------------------
Given a repository and a commit:

1. **Enumerate.** Take the commit's tree and keep exactly the paths the
   model-visible allowlist admits, reusing the same constants the worktree
   preparer uses (:data:`~prepare_model_worktree.ALLOWED_ROOT_FILES`,
   :data:`~prepare_model_worktree.ALLOWED_TREES`,
   :data:`~prepare_model_worktree.DENIED_BASENAMES_IN_TREES`,
   :data:`~prepare_model_worktree.DENIED_DIR_NAMES_IN_TREES`). Paths are
   POSIX-style and relative to the repository root.

2. **Order.** Sort the paths ascending by their **UTF-8 encoded bytes**. Byte
   order, not locale collation, so the order is identical on every platform.

3. **Retrieve.** For each path, read the **exact blob bytes** stored at that
   commit. Never read the filesystem.

4. **Frame.** Feed a SHA-256 with, in order:

   ``DOMAIN`` then ``u64be(entry_count)`` then, per entry,
   ``u64be(len(path_utf8))`` ``path_utf8`` ``u64be(len(blob))`` ``blob``

   where ``DOMAIN`` is the ASCII bytes ``b"afci-bench/substrate-content-hash/v2\\n"``
   and ``u64be`` is an unsigned 64-bit big-endian integer.

5. **Result.** The lowercase hex SHA-256 digest.

Every variable-length field is length-prefixed, so no combination of path and
content can be re-cut into a different sequence of entries that hashes the same:
the framing is unambiguous by construction. The entry count is bound in as well,
so a truncated enumeration cannot collide with a complete one. The domain string
keeps this digest from colliding with any other SHA-256 over the same material.

**No normalisation of any kind is applied to the blob bytes.** CRLF inside a
committed blob is hashed as CRLF; the algorithm deliberately does not rewrite it.
That is the point: the hash reflects what is committed, exactly.

Because the identity depends only on the commit, a commit that touches no
allowlisted path leaves it unchanged. That is what lets the substrate commit and
the governance commit that records its identity be two separate commits without
the record becoming circular.

Pure inspection: no model is invoked and no benchmark task is executed.
"""
from __future__ import annotations

import argparse
import hashlib
import struct
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Dict, List, Sequence, Tuple

import prepare_model_worktree as pmw

REPO = Path(__file__).resolve().parents[3]

#: Domain separator. Bound into the digest so this value cannot be confused with
#: any other SHA-256 computed over the same paths and bytes.
DOMAIN = b"afci-bench/substrate-content-hash/v2\n"

#: Identifier for the algorithm, recorded alongside the value it produces.
ALGORITHM_ID = "git-blob-sha256-v2"


class SubstrateIdentityError(RuntimeError):
    """Raised when the identity cannot be computed from Git object data."""


def _u64be(value: int) -> bytes:
    return struct.pack(">Q", value)


def _git(repo, *args: str) -> bytes:
    """Run git in ``repo`` and return raw stdout bytes (never text-decoded)."""
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise SubstrateIdentityError(
            f"git {' '.join(args)} failed in {repo}: "
            f"{proc.stderr.decode('utf-8', 'replace').strip()}"
        )
    return proc.stdout


def is_allowed_path(rel: str) -> bool:
    """Return whether ``rel`` is part of the model-visible substrate.

    Mirrors :func:`prepare_model_worktree.iter_allowed_files` exactly, but as a
    pure predicate over a path string so it can be applied to a Git tree
    listing instead of to a directory walk.
    """
    parts = PurePosixPath(rel).parts
    if not parts:
        return False
    if len(parts) == 1:
        return rel in pmw.ALLOWED_ROOT_FILES
    if parts[0] not in pmw.ALLOWED_TREES:
        return False
    if any(part in pmw.DENIED_DIR_NAMES_IN_TREES for part in parts[:-1]):
        return False
    if parts[-1] in pmw.DENIED_BASENAMES_IN_TREES:
        return False
    return True


def allowed_paths_at_commit(repo, commit: str) -> List[str]:
    """Return the substrate paths at ``commit``, sorted by UTF-8 byte order.

    Enumeration is from the commit's tree, so it is unaffected by what is
    currently checked out, by untracked files, or by a dirty working tree.
    """
    raw = _git(repo, "ls-tree", "-r", "-z", "--name-only", commit)
    paths = [p.decode("utf-8") for p in raw.split(b"\0") if p]
    allowed = [p for p in paths if is_allowed_path(p)]
    # Sort on the encoded bytes: identical on every platform and locale.
    return sorted(set(allowed), key=lambda p: p.encode("utf-8"))


def blob_bytes_at_commit(repo, commit: str, paths: Sequence[str]) -> Dict[str, bytes]:
    """Return ``{path: exact committed blob bytes}`` for ``paths`` at ``commit``.

    Uses ``git cat-file --batch`` over the resolved object ids, so the bytes are
    the stored blob contents with no checkout conversion of any kind.
    """
    if not paths:
        return {}

    # Resolve path -> blob oid from the tree listing.
    raw = _git(repo, "ls-tree", "-r", "-z", commit)
    oid_by_path: Dict[str, str] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, _, path = record.partition(b"\t")
        fields = meta.split(b" ")
        if len(fields) != 3 or fields[1] != b"blob":
            continue
        oid_by_path[path.decode("utf-8")] = fields[2].decode("ascii")

    missing = [p for p in paths if p not in oid_by_path]
    if missing:
        raise SubstrateIdentityError(f"not blobs at {commit}: {missing}")

    # One batch call; stdin is the oid list, stdout is length-delimited binary.
    stdin_payload = "\n".join(oid_by_path[p] for p in paths).encode("ascii") + b"\n"
    proc = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        input=stdin_payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise SubstrateIdentityError(
            "git cat-file --batch failed: "
            f"{proc.stderr.decode('utf-8', 'replace').strip()}"
        )

    out = proc.stdout
    contents: Dict[str, bytes] = {}
    offset = 0
    for path in paths:
        newline = out.find(b"\n", offset)
        if newline == -1:
            raise SubstrateIdentityError(f"truncated cat-file output before {path}")
        header = out[offset:newline].split(b" ")
        if len(header) != 3 or header[1] != b"blob":
            raise SubstrateIdentityError(
                f"unexpected cat-file header for {path}: {out[offset:newline]!r}"
            )
        size = int(header[2])
        start = newline + 1
        contents[path] = out[start:start + size]
        offset = start + size + 1  # trailing newline emitted after each object
    return contents


def substrate_entries_at_commit(repo, commit: str) -> List[Tuple[str, bytes]]:
    """Return the ordered ``(path, blob bytes)`` entries hashed by the identity."""
    paths = allowed_paths_at_commit(repo, commit)
    blobs = blob_bytes_at_commit(repo, commit, paths)
    return [(p, blobs[p]) for p in paths]


def hash_entries(entries: Sequence[Tuple[str, bytes]]) -> str:
    """Hash ``(path, blob)`` entries with the normative framing.

    ``entries`` is sorted here by UTF-8 path bytes, so callers cannot change the
    result by presenting the same set in a different order.
    """
    ordered = sorted(entries, key=lambda e: e[0].encode("utf-8"))
    digest = hashlib.sha256()
    digest.update(DOMAIN)
    digest.update(_u64be(len(ordered)))
    for path, blob in ordered:
        path_bytes = path.encode("utf-8")
        digest.update(_u64be(len(path_bytes)))
        digest.update(path_bytes)
        digest.update(_u64be(len(blob)))
        digest.update(blob)
    return digest.hexdigest()


def substrate_content_hash_at_commit(repo, commit: str) -> str:
    """Return the canonical substrate content hash of ``commit``."""
    return hash_entries(substrate_entries_at_commit(repo, commit))


def resolve_commit(repo, rev: str) -> str:
    """Return the full 40-hex commit id for ``rev``."""
    return _git(repo, "rev-parse", f"{rev}^{{commit}}").decode("ascii").strip()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=str(REPO), help="Repository to read objects from.")
    parser.add_argument("--commit", default="HEAD", help="Commit to identify.")
    parser.add_argument("--list", action="store_true", help="List the hashed paths.")
    args = parser.parse_args(argv)

    commit = resolve_commit(args.repo, args.commit)
    entries = substrate_entries_at_commit(args.repo, commit)
    if args.list:
        for path, blob in entries:
            print(f"{len(blob):>9}  {path}")
    print(f"algorithm    {ALGORITHM_ID}")
    print(f"commit       {commit}")
    print(f"entry_count  {len(entries)}")
    print(f"content_hash {hash_entries(entries)}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
