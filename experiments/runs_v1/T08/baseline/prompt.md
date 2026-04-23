# Task T08: Fix an architecture boundary violation correctly

## Goal
Locate a boundary violation example (commented or subtle) and ensure the codebase has NO boundary violation patterns.
If there is a commented-out violation example, remove it or rewrite it to be MAD-compliant.

## Constraints
- Do not loosen ESLint rules.
- Fix code so desired behavior is achieved without illegal imports.

## Acceptance Criteria
- `npm run ci` passes.
- No enforce-module-boundaries violations exist.
- If you changed behavior, add tests.

## Notes
- Use the "ports/interfaces in contracts" rule if you need shared types.
