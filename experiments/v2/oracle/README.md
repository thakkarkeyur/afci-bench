# experiments/v2/oracle — Task-Acceptance Oracle

The per-task **acceptance oracle**: the code and fixtures that decide whether a
task's required behavior change was actually achieved.

This directly addresses a v1 limitation: v1 had no per-task acceptance oracle
beyond `npm run ci`, and `ci_pass` was saturated True across all cells, so the
gate did not discriminate task success (see
`archive/v1/REFERENCE_MANIFEST.yml`, limitation `L6`). The v2 oracle should
provide task-specific behavioral checks (e.g. targeted tests / assertions) that
can fail.

Add oracle checks and their fixtures here. Do not commit run outputs.
