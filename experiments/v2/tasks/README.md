# experiments/v2/tasks — Task Suite (v2)

The v2 benchmark **task definitions**: one file per task describing the change to
be made, its inputs, and the acceptance conditions it must satisfy.

This is the v2 successor to `experiments/tasks_v0/` on `main` (T01..T12 +
`TASK_TEMPLATE.md`), which is immutable. v2 tasks should each carry an explicit,
checkable acceptance definition (linked to `../oracle/`) rather than relying on
a repository-wide `npm run ci` gate.

Add task specifications here. Do not copy or edit the v0 tasks; reference them
via [`archive/v1/`](../../../archive/v1/README.md) if needed.
