#!/usr/bin/env bash
# run_one_v1.sh — Execute and record a single v1 benchmark run.
#
# Usage:
#   ./experiments/scripts/run_one_v1.sh <TASK> <CONDITION> <PROMPT_FILE>
#
# Arguments:
#   TASK       — e.g., T01, T02, ... T12
#   CONDITION  — one of: baseline, afci, baseline_reset, afci_reset
#   PROMPT_FILE — path to the prompt.md to use (will be copied into run dir)
#
# Outputs (in experiments/runs_v1/<TASK>/<CONDITION>/):
#   prompt.md, patch.diff, ci_output.txt, metrics.json,
#   conformance.json (best-effort), run_meta.json

set -euo pipefail

# Determine Python command (prefer python3, fallback to python)
if command -v python3 &>/dev/null; then
  PYTHON=python3
elif command -v python &>/dev/null; then
  PYTHON=python
else
  echo "ERROR: Neither python3 nor python found in PATH" >&2
  exit 1
fi

TASK="${1:?Usage: run_one_v1.sh <TASK> <CONDITION> <PROMPT_FILE>}"
CONDITION="${2:?Usage: run_one_v1.sh <TASK> <CONDITION> <PROMPT_FILE>}"
PROMPT_FILE="${3:?Usage: run_one_v1.sh <TASK> <CONDITION> <PROMPT_FILE>}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUN_DIR="$REPO_ROOT/experiments/runs_v1/$TASK/$CONDITION"

echo "=== run_one_v1: $TASK / $CONDITION ==="
echo "Run dir: $RUN_DIR"

# 1. Create run directory
mkdir -p "$RUN_DIR"

# 2. Copy prompt
cp "$PROMPT_FILE" "$RUN_DIR/prompt.md"
echo "Saved prompt.md"

# 3. Capture patch (diff from paper-v0 tag)
cd "$REPO_ROOT"
git diff paper-v0 -- . ':!experiments/runs_v1' ':!experiments/scripts' > "$RUN_DIR/patch.diff" || true
echo "Saved patch.diff ($(wc -l < "$RUN_DIR/patch.diff") lines)"

# 4. Run CI and capture output
echo "Running CI..."
set +e
npm run ci > "$RUN_DIR/ci_output.txt" 2>&1
CI_EXIT=$?
set -e
echo "CI exited with code $CI_EXIT"
echo "=== CI run finished with exit code $CI_EXIT ===" >> "$RUN_DIR/ci_output.txt"

# 5. Extract metrics
$PYTHON "$SCRIPT_DIR/extract_metrics.py" "$RUN_DIR"

# 6. Conformance check (best-effort)
set +e
$PYTHON "$SCRIPT_DIR/afci_guard_check.py" "$RUN_DIR"
set -e

# 7. Write run_meta.json
NODE_VER="$(node --version 2>/dev/null || echo 'unknown')"
NPM_VER="$(npm --version 2>/dev/null || echo 'unknown')"
OS_INFO="$(uname -a 2>/dev/null || echo 'unknown')"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat > "$RUN_DIR/run_meta.json" <<METAEOF
{
  "model": "Opus 7",
  "task": "$TASK",
  "condition": "$CONDITION",
  "timestamp": "$TIMESTAMP",
  "node_version": "$NODE_VER",
  "npm_version": "$NPM_VER",
  "os": "$OS_INFO",
  "ci_exit_code": $CI_EXIT,
  "base_tag": "paper-v0"
}
METAEOF

echo "Saved run_meta.json"
echo "=== run_one_v1 complete: $TASK / $CONDITION ==="
