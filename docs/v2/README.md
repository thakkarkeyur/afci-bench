# docs/v2 — Study v2 Design Documentation

Design and methodology documents for **AFCI-Bench study v2**.

This directory holds the v2 study design as it is written: the research
questions, the measurement model, threats-to-validity analysis, the v2 protocol,
and the architecture-conformance rule specification. It is the v2 counterpart to
the v0 documents on `main` (`docs/MAD_v0.md`, `docs/PROMPT_PACK_v0.md`,
`docs/ARCH_RULES.yml`), which remain immutable.

Intended contents (to be authored — do not fabricate):

- The v2 study protocol (conditions, independence, replication count).
- A direct **architectural-conformance** measurement model (v1's guard was
  non-functional; see `archive/v1/REFERENCE_MANIFEST.yml`).
- A **task-acceptance** definition per task (v1 had no oracle beyond `npm run ci`).
- Non-empty, machine-checkable architecture rules for v2.

Nothing here should reference or regenerate v1 results. Cross-reference v1 only
via the pointers in [`archive/v1/`](../../archive/v1/README.md).
