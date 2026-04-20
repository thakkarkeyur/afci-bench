#!/usr/bin/env python3
"""afci_guard_check.py — Check AFCI architectural conformance for a run.

Usage: python afci_guard_check.py <run_dir>

Reads patch.diff from <run_dir> and writes conformance.json.
Checks:
  P0 (machine-checkable):
    - p0_boundary: dependency rule violations (e.g., core importing infra)
    - p0_ports: port/interface violations (contracts importing other layers)
    - p0_contracts: ad-hoc JSON shapes outside libs/contracts
  P1 (heuristic):
    - p1_observability: missing required log fields in API handlers
"""
import json
import re
import sys
from pathlib import Path

# Forbidden import patterns per MAD §3
BOUNDARY_RULES = [
    # (source_layer_pattern, forbidden_import_pattern, description)
    (r"libs/core/", r"""from\s+['"].*libs/infra""", "core imports infra"),
    (r"libs/core/", r"""from\s+['"].*libs/features""", "core imports features"),
    (r"libs/contracts/", r"""from\s+['"].*libs/(core|features|infra|observability)""", "contracts imports other layer"),
    (r"libs/infra/", r"""from\s+['"].*libs/(features|core)""", "infra imports features/core"),
    (r"libs/features/", r"""from\s+['"].*libs/features/(?!index)""", "feature imports another feature"),
    (r"apps/api/", r"""from\s+['"].*libs/core""", "api imports core directly"),
]

OBSERVABILITY_FIELDS = ["correlationId", "operation", "status", "latencyMs"]


def check_patch(diff_text: str):
    violations = {
        "p0_boundary": 0,
        "p0_ports": 0,
        "p0_contracts": 0,
        "p1_observability": 0,
        "details": [],
    }

    current_file = None
    added_lines = []

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            # Process previous file
            if current_file:
                _check_file(current_file, added_lines, violations)
            m = re.search(r"b/(.+)$", line)
            current_file = m.group(1) if m else None
            added_lines = []
        elif line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])

    # Process last file
    if current_file:
        _check_file(current_file, added_lines, violations)

    violations["total"] = (
        violations["p0_boundary"]
        + violations["p0_ports"]
        + violations["p0_contracts"]
        + violations["p1_observability"]
    )
    return violations


def _check_file(filepath: str, added_lines: list[str], violations: dict):
    joined = "\n".join(added_lines)

    # P0: boundary violations
    for src_pat, imp_pat, desc in BOUNDARY_RULES:
        if re.search(src_pat, filepath):
            for i, line in enumerate(added_lines):
                if re.search(imp_pat, line):
                    violations["p0_boundary"] += 1
                    violations["details"].append(f"BOUNDARY: {desc} in {filepath}: {line.strip()}")

    # P0: contracts purity — contracts should not import other layers
    if "libs/contracts/" in filepath:
        for line in added_lines:
            if re.search(r"""from\s+['"]""", line) and re.search(r"libs/(core|features|infra)", line):
                violations["p0_ports"] += 1
                violations["details"].append(f"PORTS: contracts imports non-contract layer in {filepath}")

    # P0: ad-hoc JSON shapes outside contracts
    if "libs/features/" in filepath or "apps/api/" in filepath:
        # Heuristic: interface/type declarations with request/response in name
        for line in added_lines:
            if re.search(r"(interface|type)\s+\w*(Request|Response|Dto)\b", line):
                violations["p0_contracts"] += 1
                violations["details"].append(f"CONTRACTS: ad-hoc DTO in {filepath}: {line.strip()}")

    # P1: observability in API handlers
    if "apps/api/" in filepath and (filepath.endswith(".ts") or filepath.endswith(".js")):
        if re.search(r"(router\.|app\.|handler)", joined):
            for field in OBSERVABILITY_FIELDS:
                if field not in joined:
                    violations["p1_observability"] += 1
                    violations["details"].append(f"OBSERVABILITY: missing {field} in {filepath}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python afci_guard_check.py <run_dir>", file=sys.stderr)
        sys.exit(1)

    run_dir = Path(sys.argv[1])
    diff_path = run_dir / "patch.diff"
    out_path = run_dir / "conformance.json"

    diff_text = diff_path.read_text(encoding="utf-8") if diff_path.exists() else ""
    result = check_patch(diff_text)

    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
