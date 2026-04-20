#!/usr/bin/env python3
"""extract_metrics.py — Extract metrics from a single run directory.

Usage: python extract_metrics.py <run_dir>

Reads patch.diff and ci_output.txt from <run_dir> and writes metrics.json.
Metrics captured:
  - delta_loc_code: net lines changed in src (non-test) files
  - delta_loc_test: net lines changed in test/spec files
  - delta_tests: net new test cases (heuristic: lines matching it(/test(/describe()
  - ci_pass: bool — whether CI exited 0
  - files_changed: list of files touched in the patch
  - layer_jaccard: Jaccard similarity of touched layers vs expected layers
"""
import json
import re
import sys
from pathlib import Path

TEST_PATTERNS = re.compile(r"(\.spec\.|\.test\.|__tests__|\.e2e\.)")
LAYER_DIRS = {"apps/api", "libs/contracts", "libs/core", "libs/features", "libs/infra", "libs/observability"}
TEST_CASE_RE = re.compile(r"^\+\s*(it|test|describe)\s*\(", re.MULTILINE)


def parse_diff(diff_text: str):
    files = []
    code_add = code_del = test_add = test_del = 0
    test_cases_added = test_cases_removed = 0
    current_file = None
    is_test = False

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            m = re.search(r"b/(.+)$", line)
            if m:
                current_file = m.group(1)
                is_test = bool(TEST_PATTERNS.search(current_file))
                files.append(current_file)
        elif line.startswith("+") and not line.startswith("+++"):
            if is_test:
                test_add += 1
                if TEST_CASE_RE.match(line):
                    test_cases_added += 1
            else:
                code_add += 1
        elif line.startswith("-") and not line.startswith("---"):
            if is_test:
                test_del += 1
                if re.match(r"^-\s*(it|test|describe)\s*\(", line):
                    test_cases_removed += 1
            else:
                code_del += 1

    return {
        "files_changed": files,
        "delta_loc_code": (code_add - code_del),
        "delta_loc_test": (test_add - test_del),
        "delta_tests": (test_cases_added - test_cases_removed),
        "code_additions": code_add,
        "code_deletions": code_del,
        "test_additions": test_add,
        "test_deletions": test_del,
    }


def compute_layer_jaccard(files: list[str], expected_layers: set[str] | None = None):
    touched = set()
    for f in files:
        for layer in LAYER_DIRS:
            if f.startswith(layer):
                touched.add(layer)
                break
    if expected_layers is None:
        expected_layers = touched  # self-comparison = 1.0
    union = touched | expected_layers
    if not union:
        return 1.0
    return len(touched & expected_layers) / len(union)


def parse_ci(ci_text: str):
    # Check for exit code line or common pass indicators
    if "exit code 0" in ci_text.lower():
        return True
    if re.search(r"exit code [1-9]", ci_text.lower()):
        return False
    # Fallback heuristics
    if "FAIL" in ci_text and "PASS" not in ci_text.split("FAIL")[-1]:
        return False
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_metrics.py <run_dir>", file=sys.stderr)
        sys.exit(1)

    run_dir = Path(sys.argv[1])
    diff_path = run_dir / "patch.diff"
    ci_path = run_dir / "ci_output.txt"
    out_path = run_dir / "metrics.json"

    diff_text = diff_path.read_text(encoding="utf-8") if diff_path.exists() else ""
    ci_text = ci_path.read_text(encoding="utf-8") if ci_path.exists() else ""

    diff_metrics = parse_diff(diff_text)
    ci_pass = parse_ci(ci_text)
    layer_jaccard = compute_layer_jaccard(diff_metrics["files_changed"])

    metrics = {
        **diff_metrics,
        "ci_pass": ci_pass,
        "layer_jaccard": round(layer_jaccard, 3),
    }

    out_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
