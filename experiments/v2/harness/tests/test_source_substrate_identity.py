"""Verify the recorded source-substrate identity against the committed objects.

`docs/v2/SOURCE_SUBSTRATE_IDENTITY.md` names the exact substrate every condition's
model-visible worktree is built from. A recorded identity nobody recomputes is a
claim, not a control, so this module recomputes it and fails if the two disagree.

What changed, and why it matters
--------------------------------
The previous version of this module hashed the **working tree**: it walked the
allowlist on disk and hashed whatever bytes the filesystem happened to hold. The
independent review found the consequence — the recorded value passed on the
checkout it was computed on and failed on a fresh clone of the same commit,
because Git materialises the same blob differently depending on ``core.autocrlf``,
``core.eol`` and the ``eol=`` attributes. The recorded hash was therefore an
artifact of one Windows checkout, not an identity of the repository.

The identity is now computed from **committed Git blob bytes**
(:mod:`substrate_identity`), so it is a function of the commit alone. These tests
assert that property directly rather than assuming it: the same commit is hashed
from checkouts materialised with LF and with CRLF, from a fresh clone, and under
several ``core.autocrlf`` settings, and every one must agree.

Pure inspection; no model is invoked and no benchmark task is executed.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

import prepare_model_worktree as pmw
import substrate_identity as si

REPO = Path(__file__).resolve().parents[4]
IDENTITY_DOC = REPO / "docs" / "v2" / "SOURCE_SUBSTRATE_IDENTITY.md"

#: 1. The original historical substrate.
HISTORICAL_COMMIT = "33dba7ff8917515efe56170cfd45cb7f9e16cde4"
HISTORICAL_CONTENT_HASH = "c58fc41d556e3e037deb7eda5e52249c61a9dcdbef9d687bc141bef9bb2fed89"

#: 2. Architecture-rule neutral, but still leaking experiment awareness.
INTERMEDIATE_COMMIT = "15aa99f5f564b1d482843c638174c5c853dc8f1c"
INTERMEDIATE_CONTENT_HASH = "40f38174a612c5abdc09376fb86bff327b2bc1e7cda59120c11cdb500b10a5ce"

#: 3. The final experiment-neutral canonical substrate.
SUBSTRATE_COMMIT = "630d3180af0d02a86330dfb599f559e78df65e94"
SUBSTRATE_CONTENT_HASH = "0198d76c189f38589e872cab4305527c08e86ef736e1550e428e05f9178060f3"

#: Superseded values. The first two are the same commits hashed by the old
#: working-tree algorithm on a CRLF and an LF checkout respectively — the two
#: different answers that proved the old procedure was not an identity at all.
STALE_CRLF_HASH = "361d0fe5bd97ed9f273d52d5ca4cba2a6400e128038c3c3b6e7025ca6ff7bc04"
STALE_LF_HASH = "dee8c40c6b1c2fbda907d2bf16112b8684feca96d6510d57ee31e6a323830928"

SUBSTRATE_FILE_COUNT = 49

git_required = pytest.mark.skipif(
    shutil.which("git") is None, reason="git is required to read committed objects"
)


def _doc() -> str:
    return IDENTITY_DOC.read_text(encoding="utf-8")


def _git(repo, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout.decode("utf-8").strip()


def _has_commit(repo, commit: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{commit}^{{commit}}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


needs_substrate_commit = pytest.mark.skipif(
    shutil.which("git") is None or not _has_commit(REPO, SUBSTRATE_COMMIT),
    reason="the canonical substrate commit is not present in this repository",
)


# --------------------------------------------------------------------------- #
# The recorded identity
# --------------------------------------------------------------------------- #
def test_the_identity_document_exists():
    assert IDENTITY_DOC.is_file(), "the substrate identity must be recorded publicly"


@git_required
@needs_substrate_commit
def test_the_recorded_hash_matches_the_committed_substrate():
    actual = si.substrate_content_hash_at_commit(REPO, SUBSTRATE_COMMIT)
    assert actual == SUBSTRATE_CONTENT_HASH, (
        "the source substrate changed without re-recording its identity: "
        f"expected {SUBSTRATE_CONTENT_HASH[:16]}..., computed {actual[:16]}...; "
        "update docs/v2/SOURCE_SUBSTRATE_IDENTITY.md and this test together"
    )
    assert SUBSTRATE_CONTENT_HASH in _doc(), "the identity document must record the hash"
    assert SUBSTRATE_COMMIT in _doc(), "the identity document must record the commit"


@git_required
@needs_substrate_commit
def test_the_substrate_is_the_allowlisted_file_set():
    paths = si.allowed_paths_at_commit(REPO, SUBSTRATE_COMMIT)
    assert len(paths) == SUBSTRATE_FILE_COUNT, f"substrate file count changed: {len(paths)}"
    for required in ("apps/api/src/app.ts", "libs/infra/src/index.ts",
                     "libs/features/src/index.ts", "package.json", ".gitattributes"):
        assert required in paths, f"{required} must be part of the substrate"


@git_required
@needs_substrate_commit
def test_the_git_enumeration_agrees_with_the_worktree_allowlist():
    """The two enumerations must not drift: same allowlist, different source."""
    from_git = set(si.allowed_paths_at_commit(REPO, SUBSTRATE_COMMIT))
    from_disk = set(pmw.iter_allowed_files(REPO))
    assert from_git == from_disk, (
        "the commit-based and filesystem-based allowlists disagree: "
        f"git-only={sorted(from_git - from_disk)} disk-only={sorted(from_disk - from_git)}"
    )


# --------------------------------------------------------------------------- #
# Lineage
# --------------------------------------------------------------------------- #
@git_required
@pytest.mark.parametrize(
    "label,commit,expected",
    [
        ("historical", HISTORICAL_COMMIT, HISTORICAL_CONTENT_HASH),
        ("intermediate", INTERMEDIATE_COMMIT, INTERMEDIATE_CONTENT_HASH),
    ],
)
def test_the_superseded_substrates_stay_recorded(label, commit, expected):
    """Old->new linkage must remain auditable, as for the public task hashes."""
    if not _has_commit(REPO, commit):
        pytest.skip(f"{label} commit not present")
    assert si.substrate_content_hash_at_commit(REPO, commit) == expected
    doc = _doc()
    assert commit in doc, f"the {label} substrate commit must stay recorded"
    assert expected in doc, f"the {label} substrate hash must stay recorded"


@git_required
@needs_substrate_commit
def test_the_three_substrates_are_distinct():
    hashes = {
        si.substrate_content_hash_at_commit(REPO, c)
        for c in (HISTORICAL_COMMIT, INTERMEDIATE_COMMIT, SUBSTRATE_COMMIT)
        if _has_commit(REPO, c)
    }
    assert len(hashes) == 3, "each substrate revision must have its own identity"


def test_the_stale_checkout_dependent_hashes_are_not_presented_as_canonical():
    """The old procedure produced two answers for one commit; neither may stand."""
    doc = _doc()
    for stale in (STALE_CRLF_HASH, STALE_LF_HASH):
        for line in doc.splitlines():
            if stale in line:
                assert re.search(r"supersed|stale|withdraw|no longer|supersed", line, re.I), (
                    f"{stale[:16]}... may only appear as an explicitly superseded value: {line}"
                )
    assert STALE_CRLF_HASH != SUBSTRATE_CONTENT_HASH
    assert STALE_LF_HASH != SUBSTRATE_CONTENT_HASH


# --------------------------------------------------------------------------- #
# The property the old procedure did not have: checkout independence
# --------------------------------------------------------------------------- #
@git_required
@needs_substrate_commit
@pytest.mark.parametrize("autocrlf", ["true", "false", "input"])
def test_the_hash_is_identical_under_every_autocrlf_setting(tmp_path, autocrlf):
    """`core.autocrlf` decides how blobs hit the filesystem. It must not matter."""
    clone = tmp_path / f"clone-{autocrlf}"
    subprocess.run(
        ["git", "clone", "--quiet", "--no-local", "--no-checkout", str(REPO), str(clone)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    subprocess.run(["git", "-C", str(clone), "config", "core.autocrlf", autocrlf], check=True)
    subprocess.run(
        ["git", "-C", str(clone), "checkout", "--quiet", SUBSTRATE_COMMIT],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert si.substrate_content_hash_at_commit(clone, SUBSTRATE_COMMIT) == SUBSTRATE_CONTENT_HASH


@git_required
@needs_substrate_commit
@pytest.mark.parametrize("eol,marker", [("lf", b"\n"), ("crlf", b"\r\n")])
def test_the_hash_ignores_how_the_working_tree_was_materialised(tmp_path, eol, marker):
    """Materialise the same commit with LF and with CRLF; one identity, both times.

    This is the exact failure the independent review reported: under the old
    working-tree procedure these two checkouts produced two different hashes.
    """
    clone = tmp_path / f"eol-{eol}"
    subprocess.run(
        ["git", "clone", "--quiet", "--no-local", "--no-checkout", str(REPO), str(clone)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    subprocess.run(["git", "-C", str(clone), "config", "core.eol", eol], check=True)
    subprocess.run(["git", "-C", str(clone), "config", "core.autocrlf", "false"], check=True)
    # `* text=auto eol=lf` in .gitattributes pins LF and outranks core.eol, so
    # force the CRLF materialisation the review actually hit by overriding the
    # attribute in the clone's private info/attributes.
    if eol == "crlf":
        info = clone / ".git" / "info"
        info.mkdir(parents=True, exist_ok=True)
        (info / "attributes").write_text("* text=auto eol=crlf\n", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(clone), "checkout", "--quiet", SUBSTRATE_COMMIT],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    # Prove the working trees really do differ before asserting the hash does not.
    materialised = (clone / "package.json").read_bytes()
    assert marker in materialised, f"the {eol} checkout did not materialise as expected"
    if eol == "crlf":
        assert b"\r\n" in materialised, "the CRLF checkout must actually contain CRLF"

    assert si.substrate_content_hash_at_commit(clone, SUBSTRATE_COMMIT) == SUBSTRATE_CONTENT_HASH


@git_required
@needs_substrate_commit
def test_a_fresh_clone_reproduces_the_documented_hash(tmp_path):
    """The headline requirement: a fresh clone must reproduce the recorded value."""
    clone = tmp_path / "fresh"
    subprocess.run(
        ["git", "clone", "--quiet", "--no-local", str(REPO), str(clone)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    computed = si.substrate_content_hash_at_commit(clone, SUBSTRATE_COMMIT)
    assert computed == SUBSTRATE_CONTENT_HASH, (
        "a fresh clone does not reproduce the documented substrate identity: "
        f"{computed} != {SUBSTRATE_CONTENT_HASH}"
    )


@git_required
@needs_substrate_commit
def test_a_governance_only_commit_does_not_change_the_identity():
    """Why the pin can be a second commit: docs/ is not substrate."""
    head = si.resolve_commit(REPO, "HEAD")
    if head == SUBSTRATE_COMMIT:
        pytest.skip("the pin commit does not exist yet")
        return
    changed = _git(REPO, "diff", "--name-only", SUBSTRATE_COMMIT, head).splitlines()
    substrate_changes = [p for p in changed if si.is_allowed_path(p)]
    assert substrate_changes == [], (
        f"commits after the substrate commit touched substrate files: {substrate_changes}"
    )
    assert si.substrate_content_hash_at_commit(REPO, head) == SUBSTRATE_CONTENT_HASH


# --------------------------------------------------------------------------- #
# Algorithm properties
# --------------------------------------------------------------------------- #
def test_reordered_enumeration_produces_the_same_hash():
    """Callers cannot change the answer by presenting the entries differently."""
    entries = [("b.ts", b"two"), ("a.ts", b"one"), ("c/d.ts", b"three")]
    assert si.hash_entries(entries) == si.hash_entries(list(reversed(entries)))
    assert si.hash_entries(entries) == si.hash_entries(sorted(entries))


def test_an_altered_byte_changes_the_hash():
    base = [("a.ts", b"one"), ("b.ts", b"two")]
    altered = [("a.ts", b"one"), ("b.ts", b"twO")]
    assert si.hash_entries(base) != si.hash_entries(altered)


def test_a_renamed_path_changes_the_hash():
    assert si.hash_entries([("a.ts", b"x")]) != si.hash_entries([("b.ts", b"x")])


def test_the_framing_is_unambiguous():
    """Length-prefixing must stop path and content from being re-cut."""
    assert si.hash_entries([("ab", b"c")]) != si.hash_entries([("a", b"bc")])
    assert si.hash_entries([("a", b"b"), ("c", b"d")]) != si.hash_entries([("ac", b"bd")])


def test_a_dropped_entry_changes_the_hash():
    """The entry count is bound in, so truncation cannot go unnoticed."""
    full = [("a.ts", b"one"), ("b.ts", b"two")]
    assert si.hash_entries(full) != si.hash_entries(full[:1])


def test_crlf_inside_a_committed_blob_is_hashed_as_committed():
    """The algorithm normalises nothing; it hashes what is stored, exactly."""
    assert si.hash_entries([("a.ts", b"x\r\ny")]) != si.hash_entries([("a.ts", b"x\ny")])


@git_required
@needs_substrate_commit
def test_altering_a_committed_model_visible_byte_is_detected(tmp_path):
    """Mutate one real committed substrate byte; the identity must reject it."""
    entries = si.substrate_entries_at_commit(REPO, SUBSTRATE_COMMIT)
    assert si.hash_entries(entries) == SUBSTRATE_CONTENT_HASH

    mutated = []
    for path, blob in entries:
        if path == "package.json":
            blob = blob.replace(b"Order management", b"Order  management", 1)
        mutated.append((path, blob))
    assert mutated != entries, "the mutation did not apply"
    assert si.hash_entries(mutated) != SUBSTRATE_CONTENT_HASH, (
        "a changed model-visible byte must change the substrate identity"
    )


# --------------------------------------------------------------------------- #
# What the document must say
# --------------------------------------------------------------------------- #
def test_the_document_records_the_algorithm_and_its_guarantees():
    doc = _doc()
    for claim in ("git-blob-sha256-v2", "core.autocrlf", "fresh clone"):
        assert claim in doc, f"the identity document must state {claim!r}"
    assert "630d3180af0d02a86330dfb599f559e78df65e94" in doc


def test_the_document_records_the_intended_difference_and_its_proof():
    doc = _doc()
    for claim in ("BOUNDARY VIOLATION EXAMPLE", "deliberate architectural choice",
                  "without directly importing core"):
        assert claim in doc, f"the removed disclosure {claim!r} must stay on record"
    for proof in ("AST fingerprint", "removeComments", "identical"):
        assert proof in doc, f"the equivalence proof must record {proof!r}"
    assert "TD-B23" in doc
    assert "TD-B38" in doc, "the awareness remediation must be recorded too"


def test_the_document_names_the_canonical_commit_not_the_pin_commit():
    doc = _doc()
    assert re.search(
        r"canonical (?:source[- ])?substrate is (?:commit )?`?630d3180",
        doc, re.IGNORECASE,
    ), "the document must say plainly which commit is the canonical substrate"


@git_required
@needs_substrate_commit
def test_the_recorded_git_identifiers_are_well_formed():
    doc = _doc()
    shas = set(re.findall(r"`([0-9a-f]{40})`", doc))
    for required in (HISTORICAL_COMMIT, INTERMEDIATE_COMMIT, SUBSTRATE_COMMIT):
        assert required in shas, f"{required[:8]} must be recorded as a full object id"
    for tree in ("apps", "libs"):
        recorded = _git(REPO, "rev-parse", f"{SUBSTRATE_COMMIT}:{tree}")
        assert recorded in doc, f"the {tree}/ tree id of the substrate commit must be recorded"


@git_required
@needs_substrate_commit
def test_the_substrate_itself_discloses_no_architecture_rule():
    """The recorded committed bytes state no scored dependency rule."""
    disclosures = []
    for path, blob in si.substrate_entries_at_commit(REPO, SUBSTRATE_COMMIT):
        try:
            text = blob.decode("utf-8")
        except UnicodeDecodeError:
            continue
        disclosures += [
            f"{path}:{line} {reason}"
            for line, reason in pmw.find_comment_disclosures(Path(path), text)
        ]
    assert disclosures == [], f"the recorded substrate still coaches the rules: {disclosures}"


@git_required
@needs_substrate_commit
def test_the_substrate_itself_discloses_no_experiment_awareness():
    """TD-B38: the recorded committed bytes reveal no benchmark, condition or oracle."""
    disclosures = []
    for path, blob in si.substrate_entries_at_commit(REPO, SUBSTRATE_COMMIT):
        try:
            text = blob.decode("utf-8")
        except UnicodeDecodeError:
            continue
        disclosures += [
            f"{path}:{line} {reason}"
            for line, reason in pmw.find_experiment_awareness(path, text)
        ]
    assert disclosures == [], f"the recorded substrate still reveals the experiment: {disclosures}"
