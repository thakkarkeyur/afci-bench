"""Machine-checkable evaluator-mount boundary tests (Part B).

Proves that (1) an evaluator mount inside the coding worktree is rejected, a
sibling mount is accepted; (2) the committed coding-worktree fixture contains no
forbidden (answer-bearing) evaluator artifact; (3) forbidden artifacts are
detected when present; and (4) the boundary/mount-policy docs state the required
clauses. Pure file inspection; no model is invoked.
"""
from pathlib import Path

import evaluator_mount as em  # importable via conftest.py (harness dir on sys.path)

REPO = Path(__file__).resolve().parents[4]
DOCS_V2 = REPO / "docs" / "v2"
CODING_WORKTREE = REPO / "experiments" / "v2" / "oracle" / "fixtures" / "coding_worktree"


def test_mount_inside_worktree_is_rejected(tmp_path):
    worktree = tmp_path / "snapshot"
    worktree.mkdir()
    inside = worktree / "evaluator" / "manifest.json"
    inside.parent.mkdir(parents=True)
    inside.write_text("{}", encoding="utf-8")
    assert em.mount_is_inside_worktree(worktree, inside) is True
    assert em.evaluator_mount_rejected(worktree, inside) is True
    # the worktree path itself also counts as "inside"
    assert em.mount_is_inside_worktree(worktree, worktree) is True


def test_sibling_mount_is_accepted(tmp_path):
    worktree = tmp_path / "snapshot"
    worktree.mkdir()
    sibling = tmp_path / "evaluator" / "manifest.json"
    sibling.parent.mkdir(parents=True)
    sibling.write_text("{}", encoding="utf-8")
    assert em.mount_is_inside_worktree(worktree, sibling) is False
    assert em.evaluator_mount_rejected(worktree, sibling) is False


def test_symlinked_mount_cannot_smuggle_inside(tmp_path):
    worktree = tmp_path / "snapshot"
    worktree.mkdir()
    real_mount = tmp_path / "outside_mount"
    real_mount.mkdir()
    link = worktree / "evaluator"
    try:
        link.symlink_to(real_mount, target_is_directory=True)
    except (OSError, NotImplementedError):
        import pytest

        pytest.skip("symlink creation not permitted on this platform")
    # The link lives inside the worktree, so the mount is rejected even though the
    # real target is outside (real paths are resolved before the check).
    assert em.mount_is_inside_worktree(worktree, link / "manifest.json") is True


def test_coding_worktree_fixture_has_no_hidden_evaluator_artifacts():
    assert CODING_WORKTREE.is_dir(), "coding_worktree fixture missing"
    offenders = em.scan_worktree_for_forbidden(CODING_WORKTREE)
    assert offenders == [], f"coding worktree fixture contains forbidden artifacts: {offenders}"


def test_forbidden_artifacts_are_detected_when_present(tmp_path):
    (tmp_path / "libs" / "core" / "src").mkdir(parents=True)
    (tmp_path / "libs" / "core" / "src" / "index.ts").write_text("export const x = 1;", encoding="utf-8")
    # drop several forbidden artifacts
    (tmp_path / "evaluator_manifest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "oracle_result.json").write_text("{}", encoding="utf-8")
    (tmp_path / "expected_layers.yml").write_text("x: 1", encoding="utf-8")
    (tmp_path / "hidden").mkdir()
    offenders = set(em.scan_worktree_for_forbidden(tmp_path))
    assert "evaluator_manifest.json" in offenders
    assert "oracle_result.json" in offenders
    assert "expected_layers.yml" in offenders
    assert "hidden/" in offenders


def test_boundary_and_policy_docs_state_required_clauses():
    boundary = (DOCS_V2 / "HIDDEN_EVALUATOR_BOUNDARY.md").read_text(encoding="utf-8")
    policy = (DOCS_V2 / "EVALUATOR_MOUNT_POLICY.md").read_text(encoding="utf-8")
    # Boundary doc: the 8 required properties are stated.
    for needle in (
        "must not",
        "outside",
        "only after",
        "blind",
        "content hash",
        "condition",
        "after blind scoring",
    ):
        assert needle.lower() in boundary.lower(), f"boundary doc missing clause: {needle!r}"
    # Policy doc: fail-closed rejection with the correct exit reason and realpath resolution.
    for needle in ("INFRA_EVALUATOR_MOUNT", "outside", "fail", "real", "assertEvaluatorMountOutsideWorktree"):
        assert needle.lower() in policy.lower(), f"policy doc missing clause: {needle!r}"
