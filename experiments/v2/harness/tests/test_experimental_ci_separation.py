"""Prove the experimental agent-visible CI is separated from architecture.

`npm run ci` (repository validation) MUST include architecture enforcement
(`@nx/enforce-module-boundaries`); `npm run ci:agent` (the only CI visible to the
coding model) MUST exclude it while still catching type/test/ordinary-lint
failures. This test covers Part B validation requirements 1-5 of the
pre-execution design-review reconciliation.

The behavioural checks materialize the committed
`experiments/v2/ci_fixtures/boundary_violation.ts.fixture` into a tagged library
source directory, run the real ESLint under both configs, and always remove it
(``try/finally``) so the working tree and ``npm run ci`` stay green. No model is
invoked and no benchmark run occurs.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
ESLINT_BIN = REPO / "node_modules" / "eslint" / "bin" / "eslint.js"
AGENT_CONFIG = REPO / ".eslintrc.agent.json"
NORMAL_CONFIG = REPO / ".eslintrc.json"
PKG = REPO / "package.json"
FIXTURE = REPO / "experiments" / "v2" / "ci_fixtures" / "boundary_violation.ts.fixture"
# scope:observability source dir (observability may depend on nothing), so the
# fixture's import from @afci-bench/contracts is an architecture-boundary violation.
MATERIALIZED = REPO / "libs" / "observability" / "src" / "__arch_boundary_fixture__.ts"
ARCH_RULE = "@nx/enforce-module-boundaries"

NODE = shutil.which("node")
requires_eslint = pytest.mark.skipif(
    NODE is None or not ESLINT_BIN.is_file(),
    reason="node / node_modules eslint not installed (run `npm ci` first)",
)


def _rule_ids(args):
    """Run eslint with the given args and return the list of reported ruleIds."""
    proc = subprocess.run(
        [NODE, str(ESLINT_BIN), *args, "--format", "json"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    try:
        report = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        raise AssertionError(f"eslint produced no JSON. stderr={proc.stderr[:2000]}")
    return [m.get("ruleId") for f in report for m in f.get("messages", [])]


# --------------------------------------------------------------------------- #
# Structural checks (no eslint process needed)
# --------------------------------------------------------------------------- #
def test_package_scripts_separate_ci_from_ci_agent():
    scripts = json.loads(PKG.read_text(encoding="utf-8"))["scripts"]
    # (1) normal CI still runs the architecture-enforcing lint
    assert scripts["ci"] == "npm run lint && npm run typecheck && npm run test"
    # (2) agent CI exists and uses the agent lint, not the architecture lint
    assert "lint:agent" in scripts and "ci:agent" in scripts
    assert scripts["ci:agent"] == "npm run lint:agent && npm run typecheck && npm run test"
    assert ".eslintrc.agent.json" in scripts["lint:agent"]
    # normal lint (architecture-enforcing) must NOT be invoked by ci:agent
    assert "npm run lint " not in scripts["ci:agent"] + " "
    assert scripts["ci:agent"].split("&&")[0].strip() == "npm run lint:agent"


def test_normal_eslint_config_enforces_architecture():
    cfg = json.loads(NORMAL_CONFIG.read_text(encoding="utf-8"))
    rules = cfg["overrides"][0]["rules"]
    assert ARCH_RULE in rules, "normal config must contain the architecture rule"
    assert rules[ARCH_RULE][0] == "error", "architecture rule must be an error in normal CI"


def test_agent_eslint_config_disables_only_the_architecture_rule():
    cfg = json.loads(AGENT_CONFIG.read_text(encoding="utf-8"))
    arch_off = any(o.get("rules", {}).get(ARCH_RULE) == "off" for o in cfg["overrides"])
    assert arch_off, "agent config must set the architecture rule to off"
    # ordinary non-architecture lint is retained (proves it is not a blanket disable)
    ts_rules = {}
    for o in cfg["overrides"]:
        if "*.ts" in o.get("files", []):
            ts_rules.update(o.get("rules", {}))
    assert ts_rules.get("@typescript-eslint/no-explicit-any") == "error"


# --------------------------------------------------------------------------- #
# Behavioural checks (real eslint on the materialized fixture)
# --------------------------------------------------------------------------- #
@requires_eslint
def test_fixture_flagged_by_normal_config_not_by_agent_config():
    MATERIALIZED.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        # (4) the boundary-violating fixture IS detectable by the normal config
        normal_ids = _rule_ids([str(MATERIALIZED)])
        assert ARCH_RULE in normal_ids, f"normal config should flag the violation: {normal_ids}"
        # (3) the SAME fixture is NOT rejected by ci:agent for architectural reasons
        agent_ids = _rule_ids(
            [
                "--no-eslintrc",
                "--config",
                str(AGENT_CONFIG),
                "--resolve-plugins-relative-to",
                ".",
                str(MATERIALIZED),
            ]
        )
        assert ARCH_RULE not in agent_ids, f"agent config must not flag architecture: {agent_ids}"
    finally:
        MATERIALIZED.unlink(missing_ok=True)


@requires_eslint
def test_agent_ci_still_catches_ordinary_lint_failures():
    # (5) a normal (non-architecture) lint failure is still caught by the agent lint
    MATERIALIZED.write_text(
        "export function bad(x: any): any {\n  return x;\n}\n", encoding="utf-8"
    )
    try:
        agent_ids = _rule_ids(
            [
                "--no-eslintrc",
                "--config",
                str(AGENT_CONFIG),
                "--resolve-plugins-relative-to",
                ".",
                str(MATERIALIZED),
            ]
        )
        assert "@typescript-eslint/no-explicit-any" in agent_ids, agent_ids
        assert ARCH_RULE not in agent_ids
    finally:
        MATERIALIZED.unlink(missing_ok=True)
