"""Verify the recorded source-substrate identity against the actual bytes.

`docs/v2/SOURCE_SUBSTRATE_IDENTITY.md` names the exact substrate every condition's
model-visible worktree is built from. A recorded identity nobody recomputes is a
claim, not a control, so this module recomputes it from the files on disk and
fails if the two disagree.

The identity is the SHA-256 over the sorted ``"<path> <sha256>\\n"`` lines of the
allowlisted files — the same construction as the snapshot ``content_hash`` in the
preparation manifest, so a recorded substrate identity and a recorded run manifest
are directly comparable. It is derived from file bytes rather than from git, so it
survives cloning, platform differences and history rewrites.

Pure file inspection; no model is invoked and no benchmark task is executed.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

import prepare_model_worktree as pmw

REPO = Path(__file__).resolve().parents[4]
IDENTITY_DOC = REPO / "docs" / "v2" / "SOURCE_SUBSTRATE_IDENTITY.md"

OLD_SUBSTRATE_COMMIT = "33dba7ff8917515efe56170cfd45cb7f9e16cde4"
OLD_CONTENT_HASH = "2ec1079efd468ebc46a688e21b342c514ca60930221874c5f3dd9831afcb6123"
NEW_CONTENT_HASH = "361d0fe5bd97ed9f273d52d5ca4cba2a6400e128038c3c3b6e7025ca6ff7bc04"

#: Placeholders the pin commit replaces. Kept as constants so this test states
#: plainly which fields are allowed to be unfilled and which are not.
PENDING_TOKENS = ("PENDING_SUBSTRATE_COMMIT", "PENDING_APPS_TREE", "PENDING_LIBS_TREE")


def _doc() -> str:
    return IDENTITY_DOC.read_text(encoding="utf-8")


def substrate_content_hash() -> str:
    """Recompute the substrate identity from the working tree."""
    entries = sorted(
        (rel, pmw.sha256_file(REPO / rel)) for rel in pmw.iter_allowed_files(REPO)
    )
    digest = hashlib.sha256()
    for path, sha in entries:
        digest.update(f"{path} {sha}\n".encode("utf-8"))
    return digest.hexdigest()


def test_the_identity_document_exists():
    assert IDENTITY_DOC.is_file(), "the substrate identity must be recorded publicly"


def test_the_recorded_new_content_hash_matches_the_actual_substrate():
    actual = substrate_content_hash()
    assert actual == NEW_CONTENT_HASH, (
        "the source substrate changed without re-recording its identity: "
        f"expected {NEW_CONTENT_HASH[:16]}..., computed {actual[:16]}...; "
        "update docs/v2/SOURCE_SUBSTRATE_IDENTITY.md and this test together"
    )
    assert NEW_CONTENT_HASH in _doc(), "the identity document must record the new hash"


def test_the_old_substrate_identity_stays_recorded():
    """Old->new linkage must remain auditable, as for the public task hashes."""
    doc = _doc()
    assert OLD_CONTENT_HASH in doc, "the superseded substrate hash must stay recorded"
    assert OLD_SUBSTRATE_COMMIT in doc, "the superseded substrate commit must stay recorded"
    assert OLD_CONTENT_HASH != NEW_CONTENT_HASH, "the substrate did change"


def test_the_substrate_is_the_allowlisted_file_set():
    files = pmw.iter_allowed_files(REPO)
    assert len(files) == 49, f"substrate file count changed: {len(files)}"
    assert f"| **File count** | 49 | 49 |" in _doc(), "the recorded file count drifted"
    for required in ("apps/api/src/app.ts", "libs/infra/src/index.ts", "libs/features/src/index.ts"):
        assert required in files


def test_the_document_records_the_intended_difference_and_its_proof():
    doc = _doc()
    for claim in ("BOUNDARY VIOLATION EXAMPLE", "deliberate architectural choice",
                  "without directly importing core"):
        assert claim in doc, f"the removed disclosure {claim!r} must stay on record"
    for proof in ("AST fingerprint", "removeComments", "identical"):
        assert proof in doc, f"the equivalence proof must record {proof!r}"
    assert "TD-B23" in doc


def test_the_substrate_itself_discloses_no_architecture_rule():
    """The whole point of the new identity: the recorded bytes state no rule."""
    disclosures = []
    for rel in pmw.iter_allowed_files(REPO):
        path = REPO / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        disclosures += [
            f"{rel}:{line} {reason}"
            for line, reason in pmw.find_comment_disclosures(path, text)
        ]
    assert disclosures == [], f"the recorded substrate still coaches the rules: {disclosures}"


@pytest.mark.parametrize("token", PENDING_TOKENS)
def test_git_identifiers_are_filled_in_by_the_pin_commit(token):
    """Fails until the pin commit replaces each placeholder with a real object id.

    The remediation commit legitimately cannot name its own SHA, so it lands with
    these placeholders and the pin commit immediately replaces them. Leaving one
    unfilled would leave the substrate unversioned, which is exactly the failure
    this document exists to prevent.
    """
    doc = _doc()
    assert token not in doc, (
        f"{token} is still a placeholder; the pin commit must record the real value"
    )


def test_the_recorded_git_identifiers_are_well_formed():
    """Whatever the pin commit wrote must look like real git object ids."""
    doc = _doc()
    row = next(line for line in doc.splitlines() if line.startswith("| **Commit** |"))
    shas = re.findall(r"`([0-9a-f]{40})`", row)
    assert len(shas) == 2, f"the commit row must carry two full object ids: {row}"
    assert shas[0] == OLD_SUBSTRATE_COMMIT
    assert shas[1] != OLD_SUBSTRATE_COMMIT, "the new substrate needs its own commit"
    for label in ("**`apps/` tree**", "**`libs/` tree**"):
        tree_row = next(line for line in doc.splitlines() if line.startswith(f"| {label} |"))
        trees = re.findall(r"`([0-9a-f]{40})`", tree_row)
        assert len(trees) == 2, f"{label} must carry two full tree ids: {tree_row}"
        assert trees[0] != trees[1], f"{label} must differ between old and new substrate"
