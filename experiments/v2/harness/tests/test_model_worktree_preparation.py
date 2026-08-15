"""Prove the model-visible coding worktree is isolated from architecture answers.

Resolves the independent review's P1-8: before this mechanism existed, the coding
model's worktree was the whole repository, so
``docs/v2/ARCHITECTURE_CONTEXT.md`` (the explicit architecture payload) and
``docs/v2/ARCHITECTURE_RULE_CATALOG.yml`` (the machine-checkable rule catalog the
oracle scores against) were readable in **every** condition, including the
no-guidance C1 baseline — a direct confound on the primary C4-vs-C1 contrast.

Policy: ``docs/v2/MODEL_VISIBLE_WORKTREE_POLICY.md``.
Mechanism: ``experiments/v2/harness/prepare_model_worktree.py``.

The nine proofs required by the review are marked ``PROOF n``. Runner-time
enforcement is ``TD-B22`` and remains open; nothing here builds the live runner,
invokes a model, or executes a benchmark task.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import prepare_model_worktree as pmw

REPO = Path(__file__).resolve().parents[4]
ARCH_CONTEXT = REPO / "docs" / "v2" / "ARCHITECTURE_CONTEXT.md"
ARCH_CATALOG = REPO / "docs" / "v2" / "ARCHITECTURE_RULE_CATALOG.yml"
TASK = REPO / "experiments" / "v2" / "tasks" / "public" / "PT01.md"

GENERIC_GUIDANCE = "Write small, well-named functions and keep tests passing.\n"


def _arch_text() -> str:
    return ARCH_CONTEXT.read_text(encoding="utf-8")


def _prepare(tmp_path: Path, condition: str, name: str = "wt", **kwargs):
    req = pmw.PreparationRequest(
        condition=condition,
        source_root=REPO,
        dest_root=tmp_path / name,
        task_path=TASK,
        task_id="PT01",
        **kwargs,
    )
    return pmw.prepare_model_worktree(req)


def _snapshot_relpaths(root: Path) -> set:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


# --------------------------------------------------------------------------- #
# Preconditions: the artifacts we are isolating actually exist in the repository
# --------------------------------------------------------------------------- #
def test_the_architecture_artifacts_being_isolated_exist():
    assert ARCH_CONTEXT.is_file(), "the architecture payload must exist to be excluded"
    assert ARCH_CATALOG.is_file(), "the rule catalog must exist to be excluded"
    assert (REPO / ".eslintrc.json").is_file(), "the architecture-enforcing lint config must exist"


# --------------------------------------------------------------------------- #
# PROOF 1 — C1 and C2 carry no architecture context, catalog, or normal lint rules
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "condition,kwargs",
    [("C1", {}), ("C2", {"generic_guidance_text": GENERIC_GUIDANCE})],
)
def test_proof1_no_architecture_material_in_c1_or_c2(tmp_path, condition, kwargs):
    result = _prepare(tmp_path, condition, name=condition.lower(), **kwargs)
    files = _snapshot_relpaths(result.snapshot_root)

    assert "docs/v2/ARCHITECTURE_CONTEXT.md" not in files
    assert "docs/v2/ARCHITECTURE_RULE_CATALOG.yml" not in files
    assert ".eslintrc.json" not in files
    assert not any(f.startswith("docs/") for f in files)
    assert not any(f.startswith("experiments/") for f in files)
    assert not any(f.startswith(("paper/", "archive/")) for f in files)
    assert not any(Path(f).name == ".eslintrc.json" for f in files), (
        "per-project configs extend the excluded architecture-enforcing root config"
    )

    # No file in the snapshot states the dependency rules. `.eslintrc.agent.json`
    # is the one file allowed to name the rule, and only to switch it *off* — that
    # is the agent-visible config the model has always been given, and it carries
    # no dependency constraints.
    for rel in files:
        if rel.endswith((".json", ".md", ".yml")):
            text = (result.snapshot_root / rel).read_text(encoding="utf-8", errors="ignore")
            assert "depConstraints" not in text, rel
            assert "onlyDependOnLibsWithTags" not in text, rel
            assert "sourceTag" not in text, rel
            if rel != ".eslintrc.agent.json":
                assert "enforce-module-boundaries" not in text, rel

    agent_cfg = (result.snapshot_root / ".eslintrc.agent.json").read_text(encoding="utf-8")
    assert '"@nx/enforce-module-boundaries": "off"' in agent_cfg

    assert result.manifest["architecture_delivery"] == "none"
    assert result.manifest["architecture_sha256"] is None
    assert result.manifest["architecture_persistent_path"] is None


def test_proof1_c1_carries_no_persistent_context_at_all(tmp_path):
    result = _prepare(tmp_path, "C1")
    files = {Path(f).name.lower() for f in _snapshot_relpaths(result.snapshot_root)}
    for forbidden in pmw.PERSISTENT_CONTEXT_BASENAMES:
        assert forbidden not in files
    assert result.manifest["generic_guidance_delivery"] == "none"


def test_proof1_c2_guidance_is_prompt_delivered_not_persisted(tmp_path):
    result = _prepare(tmp_path, "C2", generic_guidance_text=GENERIC_GUIDANCE)
    files = _snapshot_relpaths(result.snapshot_root)
    assert not any(GENERIC_GUIDANCE.strip() in (result.snapshot_root / f).read_text(
        encoding="utf-8", errors="ignore") for f in files if f.endswith(".md"))
    assert result.manifest["generic_guidance_delivery"] == "prompt_injection"
    assert result.manifest["generic_guidance_sha256"]


# --------------------------------------------------------------------------- #
# PROOF 2 — C3 contains only its approved persistent architecture payload
# --------------------------------------------------------------------------- #
def test_proof2_c3_contains_only_the_approved_instruction_file(tmp_path):
    arch = _arch_text()
    result = _prepare(tmp_path, "C3", architecture_text=arch)
    files = _snapshot_relpaths(result.snapshot_root)

    assert pmw.C3_INSTRUCTION_PATH in files
    assert (result.snapshot_root / pmw.C3_INSTRUCTION_PATH).read_text(encoding="utf-8") == arch

    persistent = [
        f for f in files if Path(f).name.lower() in pmw.PERSISTENT_CONTEXT_BASENAMES
    ]
    assert persistent == [pmw.C3_INSTRUCTION_PATH], persistent

    # the payload arrives as the instruction file, never as the source document
    assert "docs/v2/ARCHITECTURE_CONTEXT.md" not in files
    assert ".eslintrc.json" not in files
    assert result.manifest["architecture_delivery"] == "persistent_instruction_file"
    assert result.manifest["architecture_persistent_path"] == pmw.C3_INSTRUCTION_PATH


# --------------------------------------------------------------------------- #
# PROOF 3 — C4 contains no persistent architecture payload
# --------------------------------------------------------------------------- #
def test_proof3_c4_has_no_persistent_architecture_payload(tmp_path):
    result = _prepare(tmp_path, "C4", architecture_text=_arch_text())
    files = _snapshot_relpaths(result.snapshot_root)

    assert pmw.C3_INSTRUCTION_PATH not in files
    assert not any(Path(f).name.lower() in pmw.PERSISTENT_CONTEXT_BASENAMES for f in files)
    assert "docs/v2/ARCHITECTURE_CONTEXT.md" not in files
    assert result.manifest["architecture_delivery"] == "prompt_injection"
    assert result.manifest["architecture_persistent_path"] is None
    assert result.manifest["architecture_sha256"], "C4 still records the payload hash"


# --------------------------------------------------------------------------- #
# PROOF 4 — C3 and C4 architecture bytes are identical when supplied
# --------------------------------------------------------------------------- #
def test_proof4_c3_and_c4_architecture_bytes_are_identical(tmp_path):
    arch = _arch_text()
    c3 = _prepare(tmp_path, "C3", name="c3", architecture_text=arch)
    c4 = _prepare(tmp_path, "C4", name="c4", architecture_text=arch)

    assert c3.manifest["architecture_sha256"] == c4.manifest["architecture_sha256"]
    assert c3.manifest["architecture_sha256"] == pmw.sha256_bytes(arch.encode("utf-8"))
    # same bytes, different delivery channel — that is the whole point of G5
    assert c3.manifest["architecture_delivery"] != c4.manifest["architecture_delivery"]
    persisted = (c3.snapshot_root / pmw.C3_INSTRUCTION_PATH).read_bytes()
    assert pmw.sha256_bytes(persisted) == c4.manifest["architecture_sha256"]


def test_proof4_substrate_is_identical_across_all_four_conditions(tmp_path):
    """Only the context differs between conditions; the substrate must not."""
    prepared = {
        "C1": _prepare(tmp_path, "C1", name="s1"),
        "C2": _prepare(tmp_path, "C2", name="s2", generic_guidance_text=GENERIC_GUIDANCE),
        "C3": _prepare(tmp_path, "C3", name="s3", architecture_text=_arch_text()),
        "C4": _prepare(tmp_path, "C4", name="s4", architecture_text=_arch_text()),
    }
    substrates = {}
    for cond, res in prepared.items():
        entries = {
            e["path"]: e["sha256"]
            for e in res.manifest["entries"]
            if e["path"] != pmw.C3_INSTRUCTION_PATH
        }
        substrates[cond] = entries
    reference = substrates["C1"]
    for cond, entries in substrates.items():
        assert entries == reference, f"{cond} substrate differs from C1"


# --------------------------------------------------------------------------- #
# PROOF 5 — source folders remain, preserving implicit architecture clues
# --------------------------------------------------------------------------- #
def test_proof5_source_substrate_and_implicit_clues_remain(tmp_path):
    result = _prepare(tmp_path, "C1")
    files = _snapshot_relpaths(result.snapshot_root)

    for required in (
        "apps/api/src/app.ts",
        "apps/api/src/app.spec.ts",
        "apps/api/project.json",
        "libs/core/src/index.ts",
        "libs/features/src/index.ts",
        "libs/infra/src/index.ts",
        "libs/contracts/src/index.ts",
        "libs/observability/src/index.ts",
        "package.json",
        "package-lock.json",
        "nx.json",
        "tsconfig.base.json",
        "jest.preset.js",
        ".eslintrc.agent.json",
    ):
        assert required in files, f"missing substrate file {required}"

    # folder names, scope tags and path aliases stay discoverable (D3)
    assert "scope:core" in (result.snapshot_root / "libs/core/project.json").read_text(
        encoding="utf-8"
    )
    assert "@afci-bench/core" in (result.snapshot_root / "tsconfig.base.json").read_text(
        encoding="utf-8"
    )
    # ...but the rule that governs them is not present
    agent_cfg = json.loads((result.snapshot_root / ".eslintrc.agent.json").read_text(encoding="utf-8"))
    off = [
        o for o in agent_cfg["overrides"]
        if o.get("rules", {}).get("@nx/enforce-module-boundaries") == "off"
    ]
    assert off, "the agent lint config must keep the architecture rule off"


# --------------------------------------------------------------------------- #
# PROOF 6 — ci:agent remains executable in the prepared snapshot
# --------------------------------------------------------------------------- #
def _link_node_modules(snapshot_root: Path) -> bool:
    src = REPO / "node_modules"
    dst = snapshot_root / "node_modules"
    if not src.is_dir():
        return False
    try:
        if os.name == "nt":
            proc = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(dst), str(src)],
                capture_output=True, text=True,
            )
            return proc.returncode == 0
        os.symlink(src, dst, target_is_directory=True)
        return True
    except OSError:
        return False


def test_proof6_ci_agent_is_executable_in_the_prepared_snapshot(tmp_path):
    result = _prepare(tmp_path, "C1")
    if shutil.which("npm") is None:
        pytest.skip("npm not available")
    if not _link_node_modules(result.snapshot_root):
        pytest.skip("cannot link node_modules into the snapshot on this platform")

    env = dict(os.environ, NX_DAEMON="false", CI="true")
    env["NX_CACHE_DIRECTORY"] = str(tmp_path / "nxcache")
    proc = subprocess.run(
        ["npm", "run", "ci:agent"],
        cwd=str(result.snapshot_root),
        capture_output=True,
        text=True,
        shell=(os.name == "nt"),
        env=env,
        timeout=900,
    )
    assert proc.returncode == 0, (
        "ci:agent must pass inside the prepared snapshot\n"
        f"STDOUT tail:\n{proc.stdout[-4000:]}\nSTDERR tail:\n{proc.stderr[-4000:]}"
    )


def test_proof6_agent_lint_config_is_present_and_normal_lint_config_is_not(tmp_path):
    """Structural half of PROOF 6, always run even when the link is unavailable."""
    result = _prepare(tmp_path, "C1")
    assert (result.snapshot_root / ".eslintrc.agent.json").is_file()
    assert not (result.snapshot_root / ".eslintrc.json").exists()
    scripts = json.loads((result.snapshot_root / "package.json").read_text(encoding="utf-8"))["scripts"]
    assert scripts["ci:agent"] == "npm run lint:agent && npm run typecheck && npm run test"
    assert ".eslintrc.agent.json" in scripts["lint:agent"]


# --------------------------------------------------------------------------- #
# PROOF 7 — private evaluator paths and hidden material are rejected
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "relpath",
    [
        "afci-bench-evaluator-private/tasks/PT01.md",
        "evaluator_private/PT01.md",
        "hidden_tests/PT01.md",
        "hidden/PT01.md",
        "mount/evaluator_manifest.json",
        "mount/hidden_acceptance_plan.md",
        "mount/legitimate_alternatives.yml",
    ],
)
def test_proof7_private_evaluator_task_sources_are_refused(tmp_path, relpath):
    path = tmp_path / "src" / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("whatever\n", encoding="utf-8")
    req = pmw.PreparationRequest(
        condition="C1",
        source_root=REPO,
        dest_root=tmp_path / "wt",
        task_path=path,
        task_id="PT01",
    )
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.prepare_model_worktree(req)
    assert exc.value.code == "EVALUATOR_MATERIAL_REJECTED"
    assert not (tmp_path / "wt").exists(), "refusal must not leave a partial worktree"


def test_proof7_evaluator_artifacts_inside_the_snapshot_are_rejected(tmp_path):
    result = _prepare(tmp_path, "C1")
    (result.snapshot_root / "evaluator_manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.assert_snapshot_clean(result.snapshot_root)
    assert "evaluator artifact" in exc.value.message


def test_proof7_hidden_tests_directory_inside_the_snapshot_is_rejected(tmp_path):
    result = _prepare(tmp_path, "C1")
    (result.snapshot_root / "hidden_tests").mkdir()
    with pytest.raises(pmw.WorktreePreparationError):
        pmw.assert_snapshot_clean(result.snapshot_root)


# --------------------------------------------------------------------------- #
# PROOF 8 — an unexpected explicit architecture file fails closed
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "name,source",
    [
        ("ARCHITECTURE_CONTEXT.md", ARCH_CONTEXT),
        ("ARCHITECTURE_RULE_CATALOG.yml", ARCH_CATALOG),
        (".eslintrc.json", REPO / ".eslintrc.json"),
    ],
)
def test_proof8_unexpected_architecture_file_fails_closed(tmp_path, name, source):
    result = _prepare(tmp_path, "C1")
    shutil.copy2(source, result.snapshot_root / name)
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.assert_snapshot_clean(result.snapshot_root)
    assert exc.value.code == "UNEXPECTED_ARCHITECTURE_FILE"
    assert name.lower() in exc.value.message.lower()


def test_proof8_unapproved_persistent_context_fails_closed(tmp_path):
    result = _prepare(tmp_path, "C1")
    (result.snapshot_root / "CLAUDE.md").write_text("do this\n", encoding="utf-8")
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.assert_snapshot_clean(result.snapshot_root)
    assert "unapproved persistent context" in exc.value.message


def test_proof8_docs_tree_inside_the_snapshot_fails_closed(tmp_path):
    result = _prepare(tmp_path, "C1")
    (result.snapshot_root / "docs").mkdir()
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.assert_snapshot_clean(result.snapshot_root)
    assert "forbidden directory" in exc.value.message


# --------------------------------------------------------------------------- #
# PROOF 9 — deterministic manifest with hashes
# --------------------------------------------------------------------------- #
def test_proof9_manifest_records_every_file_with_a_hash(tmp_path):
    result = _prepare(tmp_path, "C1")
    entries = result.manifest["entries"]
    assert entries and result.manifest["entry_count"] == len(entries)

    on_disk = _snapshot_relpaths(result.snapshot_root)
    assert {e["path"] for e in entries} == on_disk
    for e in entries:
        assert len(e["sha256"]) == 64
        assert e["sha256"] == pmw.sha256_file(result.snapshot_root / e["path"])
        assert e["bytes"] >= 0
    assert [e["path"] for e in entries] == sorted(e["path"] for e in entries)
    assert len(result.manifest["content_hash"]) == 64
    assert result.manifest["task_sha256"] == pmw.sha256_file(TASK)


def test_proof9_manifest_is_deterministic_across_preparations(tmp_path):
    a = _prepare(tmp_path, "C1", name="a")
    b = _prepare(tmp_path, "C1", name="b")
    assert a.manifest["content_hash"] == b.manifest["content_hash"]
    assert a.manifest == b.manifest, "manifest must carry no timestamp or other nondeterminism"
    assert json.dumps(a.manifest, sort_keys=True) == json.dumps(b.manifest, sort_keys=True)


def test_proof9_manifest_records_that_runner_enforcement_is_not_implemented(tmp_path):
    result = _prepare(tmp_path, "C1")
    assert "TD-B22" in str(result.manifest["runner_enforcement"])
    assert "not implemented" in str(result.manifest["runner_enforcement"])


# --------------------------------------------------------------------------- #
# Condition-payload refusals (fail-closed contract)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("condition", ["C1", "C2"])
def test_architecture_payload_is_refused_for_c1_and_c2(tmp_path, condition):
    kwargs = {"generic_guidance_text": GENERIC_GUIDANCE} if condition == "C2" else {}
    req = pmw.PreparationRequest(
        condition=condition,
        source_root=REPO,
        dest_root=tmp_path / "wt",
        task_path=TASK,
        architecture_text=_arch_text(),
        **kwargs,
    )
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.prepare_model_worktree(req)
    assert exc.value.code == "ARCH_PAYLOAD_NOT_ALLOWED"


@pytest.mark.parametrize("condition", ["C3", "C4"])
def test_missing_architecture_payload_is_refused_for_c3_and_c4(tmp_path, condition):
    req = pmw.PreparationRequest(
        condition=condition, source_root=REPO, dest_root=tmp_path / "wt", task_path=TASK
    )
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.prepare_model_worktree(req)
    assert exc.value.code == "ARCH_PAYLOAD_REQUIRED"


def test_generic_guidance_is_refused_outside_c2(tmp_path):
    req = pmw.PreparationRequest(
        condition="C1",
        source_root=REPO,
        dest_root=tmp_path / "wt",
        task_path=TASK,
        generic_guidance_text=GENERIC_GUIDANCE,
    )
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.prepare_model_worktree(req)
    assert exc.value.code == "GUIDANCE_PAYLOAD_NOT_ALLOWED"


def test_c2_without_guidance_is_refused(tmp_path):
    req = pmw.PreparationRequest(
        condition="C2", source_root=REPO, dest_root=tmp_path / "wt", task_path=TASK
    )
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.prepare_model_worktree(req)
    assert exc.value.code == "GUIDANCE_PAYLOAD_REQUIRED"


def test_unknown_condition_is_refused(tmp_path):
    req = pmw.PreparationRequest(
        condition="C9", source_root=REPO, dest_root=tmp_path / "wt", task_path=TASK
    )
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.prepare_model_worktree(req)
    assert exc.value.code == "UNKNOWN_CONDITION"


def test_missing_task_body_is_refused(tmp_path):
    req = pmw.PreparationRequest(
        condition="C1",
        source_root=REPO,
        dest_root=tmp_path / "wt",
        task_path=tmp_path / "nope" / "PT01.md",
    )
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.prepare_model_worktree(req)
    assert exc.value.code == "TASK_MISSING"


def test_non_empty_destination_is_refused(tmp_path):
    dest = tmp_path / "wt"
    dest.mkdir()
    (dest / "leftover.txt").write_text("x", encoding="utf-8")
    req = pmw.PreparationRequest(
        condition="C1", source_root=REPO, dest_root=dest, task_path=TASK
    )
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.prepare_model_worktree(req)
    assert exc.value.code == "DEST_NOT_EMPTY"


def test_allowlist_is_first_not_a_denylist(tmp_path):
    """A brand-new top-level file is invisible until it is explicitly allowed."""
    fake = tmp_path / "src"
    (fake / "apps" / "api" / "src").mkdir(parents=True)
    (fake / "apps" / "api" / "src" / "app.ts").write_text("export const x = 1;\n", encoding="utf-8")
    (fake / "package.json").write_text("{}", encoding="utf-8")
    (fake / "SECRET_ARCHITECTURE_NOTES.md").write_text("layers!\n", encoding="utf-8")
    (fake / "docs").mkdir()
    (fake / "docs" / "leak.md").write_text("layers!\n", encoding="utf-8")

    allowed = pmw.iter_allowed_files(fake)
    assert "apps/api/src/app.ts" in allowed
    assert "package.json" in allowed
    assert "SECRET_ARCHITECTURE_NOTES.md" not in allowed
    assert not any(a.startswith("docs/") for a in allowed)


# --------------------------------------------------------------------------- #
# PROOF 10 — model-visible source comments disclose no architecture rule
# --------------------------------------------------------------------------- #
# Closes TD-B24 (the sweep never read file content, so it could not detect the
# TD-B23 disclosure) and regression-proves TD-B23 (the disclosure itself).
LEAKAGE_FIXTURES = REPO / "experiments" / "v2" / "leakage_fixtures"

#: The statements this audit must never again let through, per TD-B23.
REQUIRED_DETECTIONS = {
    "api-cannot-import-core": "// ERROR: api cannot import core directly\n",
    "infra-must-not-import-core": "// infra must not import core\n",
    "boundary-violation-example":
        "// BOUNDARY VIOLATION EXAMPLE (commented out - would fail CI if uncommented):\n",
    "commented-out-forbidden-import-with-architecture-text":
        "// This respects the module boundary rules: api may not depend on core.\n"
        "// import { Order } from '@afci-bench/core';\n",
}

#: Ordinary implementation prose. Rejecting any of these would strip the comments
#: that keep the substrate realistic, which the remediation must not do.
REQUIRED_NON_DETECTIONS = {
    "adapter-conversion": "// Adapter to convert infra's OrderEntity to core's Order\n",
    "port-implemented-by-infra": "// Port interface - implemented by infra layer\n",
    "port-matching-core": "// Port interface (matching core's OrderRepository)\n",
    "reexport-domain-types":
        "// Re-export the domain types that callers of this use case work with\n",
    "infra-implements-repositories": "// Infra layer implements repository interfaces\n",
    "persistence-facing-shape":
        "// OrderEntity is this adapter's own persistence-facing representation of an\n"
        "// order, expressed with the shared contract types.\n",
    "runtime-import-advice": "// Note: do not import this module at runtime; it is types-only\n",
    "third-party-import-advice": "// We avoid importing lodash here to keep the bundle small\n",
    "business-rule":
        "// Totals round to cents because the payment provider rejects sub-cent values\n",
    "framework-behaviour": "// express() must be called before any route is registered\n",
    "real-import-statement": "import { Order } from '@afci-bench/core';\n",
    "rule-text-inside-a-string-literal":
        "const s = '// api cannot import core'; export const x = s;\n",
    "todo": "// TODO: extract this helper once the second caller lands\n",
}


@pytest.mark.parametrize("label", sorted(REQUIRED_DETECTIONS))
def test_proof10_required_architecture_statements_are_detected(label):
    findings = pmw.find_comment_disclosures(Path("x.ts"), REQUIRED_DETECTIONS[label])
    assert findings, f"{label!r} is architecture coaching and must be detected"


@pytest.mark.parametrize("label", sorted(REQUIRED_NON_DETECTIONS))
def test_proof10_ordinary_comments_are_not_flagged(label):
    findings = pmw.find_comment_disclosures(Path("x.ts"), REQUIRED_NON_DETECTIONS[label])
    assert not findings, (
        f"{label!r} is ordinary implementation prose; flagging it makes the audit "
        f"over-broad: {findings}"
    )


def test_proof10_the_scanner_reads_typescript_the_basename_sweep_could_not(tmp_path):
    """TD-B24's actual gap: a .ts file whose *name* is innocuous but whose body leaks."""
    snapshot = tmp_path / "snap"
    (snapshot / "libs" / "infra" / "src").mkdir(parents=True)
    leak = snapshot / "libs" / "infra" / "src" / "index.ts"
    leak.write_text("// infra must not import core\nexport const x = 1;\n", encoding="utf-8")

    # the basename/directory sweep alone sees nothing wrong with this file
    names = [p.name.lower() for p in snapshot.rglob("*") if p.is_file()]
    assert not any(n in pmw.FORBIDDEN_ARCHITECTURE_BASENAMES for n in names)

    violations = pmw.scan_snapshot_violations(snapshot)
    assert any("libs/infra/src/index.ts" in v for v in violations), violations


@pytest.mark.parametrize(
    "fixture_name",
    [
        "td_b23_api_core_boundary.ts.fixture",
        "td_b23_infra_core_avoidance.ts.fixture",
        "td_b23_features_reexport_rationale.ts.fixture",
    ],
)
def test_proof10_the_verbatim_historical_leak_is_detected(fixture_name):
    """The exact bytes removed from the substrate, not a paraphrase of them."""
    path = LEAKAGE_FIXTURES / fixture_name
    assert path.is_file(), f"missing regression fixture {fixture_name}"
    findings = pmw.find_comment_disclosures(Path("x.ts"), path.read_text(encoding="utf-8"))
    assert findings, f"{fixture_name} is the historical TD-B23 leak and must be detected"


def test_proof10_the_neutral_fixture_is_not_flagged():
    path = LEAKAGE_FIXTURES / "neutral_implementation_comments.ts.fixture"
    assert path.is_file()
    findings = pmw.find_comment_disclosures(Path("x.ts"), path.read_text(encoding="utf-8"))
    assert not findings, f"the audit is over-broad; it flagged retained prose: {findings}"


@pytest.mark.parametrize(
    "condition,kwargs",
    [("C1", {}), ("C2", {"generic_guidance_text": GENERIC_GUIDANCE})],
)
def test_proof10_the_real_prepared_snapshot_discloses_no_rule(tmp_path, condition, kwargs):
    """The live C1/C2 substrate — the arms that must be unguided — carries no rule."""
    result = _prepare(tmp_path, condition, name=condition.lower(), **kwargs)
    disclosures = pmw.scan_source_comment_disclosures(result.snapshot_root)
    assert disclosures == [], (
        "the model-visible substrate still states the hidden dependency rules "
        f"to {condition}: {disclosures}"
    )


def test_proof10_the_source_files_that_leaked_are_still_present_and_still_useful(tmp_path):
    """Neutralising the comments must not have deleted the files or their code."""
    result = _prepare(tmp_path, "C1")
    for rel in ("apps/api/src/app.ts", "libs/infra/src/index.ts", "libs/features/src/index.ts"):
        text = (result.snapshot_root / rel).read_text(encoding="utf-8")
        assert "@afci-bench/" in text, f"{rel} lost its workspace imports"
        assert "//" in text, f"{rel} lost every comment; only the rule text had to go"


def test_proof10_an_injected_disclosure_fails_the_snapshot_closed(tmp_path):
    result = _prepare(tmp_path, "C1")
    target = result.snapshot_root / "libs" / "features" / "src" / "index.ts"
    target.write_text(
        "// api cannot import core directly\n" + target.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.assert_snapshot_clean(result.snapshot_root)
    assert exc.value.code == "ARCHITECTURE_COMMENT_DISCLOSURE"
    assert "libs/features/src/index.ts" in exc.value.message


def test_proof10_a_reintroduced_worked_violation_example_fails_closed(tmp_path):
    result = _prepare(tmp_path, "C1")
    target = result.snapshot_root / "apps" / "api" / "src" / "app.ts"
    target.write_text(
        "// BOUNDARY VIOLATION EXAMPLE (would fail CI if uncommented):\n"
        "// import { Order } from '@afci-bench/core';\n" + target.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    with pytest.raises(pmw.WorktreePreparationError) as exc:
        pmw.assert_snapshot_clean(result.snapshot_root)
    assert exc.value.code == "ARCHITECTURE_COMMENT_DISCLOSURE"


def test_proof10_c3_approved_instruction_file_is_exempt(tmp_path):
    """C3's instruction file IS the architecture payload; scanning it would refuse C3."""
    result = _prepare(tmp_path, "C3", architecture_text=_arch_text())
    pmw.assert_snapshot_clean(result.snapshot_root, [pmw.C3_INSTRUCTION_PATH])
    # ...but it is only exempt because it is the approved path
    unapproved = pmw.scan_source_comment_disclosures(result.snapshot_root)
    assert any(pmw.C3_INSTRUCTION_PATH in v for v in unapproved), (
        "the payload must still be detectable when it is not the approved path"
    )


def test_proof10_non_typescript_model_visible_types_are_scanned(tmp_path):
    """TD-B24 asks for `.ts` *and any other model-visible text type* — cover them."""
    snapshot = tmp_path / "snap"
    snapshot.mkdir()
    cases = {
        "jest.preset.js": "// api must not import core\nmodule.exports = {};\n",
        ".gitattributes": "# infra cannot import core\n* text=auto eol=lf\n",
        "project.json": '{"description": "api may not depend on core"}\n',
    }
    for name, body in cases.items():
        (snapshot / name).write_text(body, encoding="utf-8")
    violations = pmw.scan_source_comment_disclosures(snapshot)
    for name in cases:
        assert any(name in v for v in violations), f"{name} was not scanned: {violations}"


def test_proof10_json_keys_do_not_make_the_agent_lint_config_a_violation(tmp_path):
    """`.eslintrc.agent.json` names the boundary rule only to switch it off."""
    result = _prepare(tmp_path, "C1")
    agent_cfg = result.snapshot_root / ".eslintrc.agent.json"
    assert "enforce-module-boundaries" in agent_cfg.read_text(encoding="utf-8")
    assert not any(
        ".eslintrc.agent.json" in v
        for v in pmw.scan_source_comment_disclosures(result.snapshot_root)
    ), "the one file allowed to name the rule must not be flagged for naming it"


def test_proof10_string_literals_are_not_mistaken_for_comments():
    """The tokenizer must not read quoted text as prose, or every import would leak."""
    src = "const doc = 'see // api cannot import core';\nexport const d = doc;\n"
    assert pmw.find_comment_disclosures(Path("x.ts"), src) == []
    regions = pmw._js_comment_regions(src)
    assert regions == [], regions


def test_proof10_block_comments_and_line_numbers_are_reported():
    src = "const a = 1;\n\n/* line three\n   api cannot import core */\n"
    findings = pmw.find_comment_disclosures(Path("x.ts"), src)
    assert findings, "a block comment must be scanned too"
    assert findings[0][0] == 3, f"expected the block to be reported at line 3: {findings}"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def test_cli_prepares_and_writes_a_manifest(tmp_path):
    manifest_path = tmp_path / "snapshot_manifest.json"
    rc = pmw.main(
        [
            "--condition", "C1",
            "--source", str(REPO),
            "--dest", str(tmp_path / "wt"),
            "--task", str(TASK),
            "--task-id", "PT01",
            "--manifest-out", str(manifest_path),
        ]
    )
    assert rc == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["condition"] == "C1"
    assert manifest["architecture_delivery"] == "none"
    assert manifest["entry_count"] > 0


def test_cli_refuses_an_architecture_payload_for_c1(tmp_path):
    rc = pmw.main(
        [
            "--condition", "C1",
            "--source", str(REPO),
            "--dest", str(tmp_path / "wt"),
            "--task", str(TASK),
            "--architecture-file", str(ARCH_CONTEXT),
        ]
    )
    assert rc == 2
