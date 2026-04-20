#!/usr/bin/env bash
# run_ci.sh — Run the project CI suite and capture output.
# Usage: ./run_ci.sh [output_file]
# If output_file is omitted, prints to stdout.

set -euo pipefail

OUT="${1:-/dev/stdout}"

echo "=== CI run started at $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee "$OUT"
npm run ci 2>&1 | tee -a "$OUT"
EXIT_CODE=${PIPESTATUS[0]}
echo "=== CI run finished with exit code $EXIT_CODE ===" | tee -a "$OUT"
exit $EXIT_CODE
