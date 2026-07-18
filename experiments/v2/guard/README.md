# experiments/v2/guard — Architecture Conformance Guard (v2)

The v2 **architecture-conformance guard**: the checker that decides whether a
produced change respects the declared module boundaries, plus its validation
tests.

This replaces the v1 AFCI-Guard, which was non-functional: it matched literal
`libs/core` import paths while the codebase uses `@afci-bench/*` path aliases, so
its regexes never fired and every conformance record was zero, with no tests
(see `archive/v1/REFERENCE_MANIFEST.yml`, limitations `L3`/`L4`). The v2 guard
must resolve the aliases actually used, be validated against known-violating and
known-conforming inputs, and read non-empty, machine-checkable rules.

Add the guard implementation and its test suite here. Do not fabricate
conformance results.
