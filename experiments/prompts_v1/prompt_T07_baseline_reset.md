TASK=T07, CONDITION=baseline_reset, BASE=paper-v0-runner, MODEL=Opus 7
BASELINE PROMPT (task-only)
# Task T07: Refactor - extract duplicate pure logic into core

## Goal
Find a small piece of duplicated pure logic in features (or across api/features) and extract it into libs/core.

## Constraints
- core MUST remain pure (no IO).
- api MUST NOT import core directly.
- features may import core.

## Acceptance Criteria
- `npm run ci` passes.
- Duplicate logic removed and replaced by a core helper.
- Tests updated/added to cover the helper.

## Notes
- Keep the refactor small and surgical (one helper, not a large restructure).