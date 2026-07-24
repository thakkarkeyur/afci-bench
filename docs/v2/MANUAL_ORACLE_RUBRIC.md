# docs/v2 — Manual Oracle Rubric

Status: **development rubric for study v2**. Defines, for the architecture rules
that **cannot** be fully automated, the criteria a human rater uses to decide
whether a change satisfies or violates the rule. Development artifact only: it
does **not** freeze the final benchmark configuration, authorizes **no** paid
model run, and **no human ratings are conducted in this package**.

Related: [`MANUAL_RATING_PROTOCOL.md`](MANUAL_RATING_PROTOCOL.md) (how rating is
run: blinding, two raters, κ ≥ 0.70), [`ARCHITECTURE_RULE_CATALOG.yml`](ARCHITECTURE_RULE_CATALOG.yml)
(rule definitions), [`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md)
§4. Blocking decision: **`TD-B12`** (oracle validation incl. blinded double
rating).

---

## 1. When manual judgment is allowed

Manual judgment is allowed **only** for rules whose catalog `evaluation` is
`manual` or `hybrid` and whose `oracle_implementation_status` is not
`implemented`:

- `AR-CONTRACT-001` — externally visible shapes live only in contracts;
- `AR-OBSERV-001` — request/error logging completeness;
- `AR-CODE-001` — coding and change discipline.

A rule whose catalog `evaluation` is `automated` and
`oracle_implementation_status: implemented` (the `AR-DEP-*` family) is **not**
manually rated; its verdict comes from the oracle.

## 2. When automated evidence takes precedence

Where the automated oracle produces a finding for a rule, the **automated
evidence takes precedence** over a manual impression:

- A rater must not overturn an automated `VIOLATION`/`SATISFIED` for an
  `implemented` rule.
- For a `hybrid` rule, the automated candidate signal (when present) frames the
  question; the rater confirms or refutes it with reasons, and disagreement with
  a *deterministic* automated check is resolved in favour of the automated check.
- A rater never infers the condition or model, and never uses runtime behaviour
  the oracle did not measure.

## 3. Per-rule satisfied / violated criteria

### AR-CONTRACT-001 — Externally visible shapes live only in contracts
- **Satisfied** when every externally visible request/response shape used at the
  HTTP boundary is declared in `contracts`, and no ad-hoc externally visible
  shape is declared in `features`/`api`.
- **Violated** when an externally visible shape is declared or inlined outside
  `contracts` (e.g. a response object shape defined in `api`), or a contract
  change is not propagated to its consumers/tests.
- **Not applicable** when the change touches no externally visible shape.
- **Excluded evidence:** internal-only DTOs/view models that are never serialized
  at the boundary are not contract violations.

### AR-OBSERV-001 — Request and error logging completeness
- **Satisfied** when every request handler records correlationId, operation,
  status, and latency, and every error record includes correlationId, errorType,
  and message, through the observability layer.
- **Violated** when a handler omits a required request field, an error path omits
  a required error field, or logging is done ad hoc outside observability.
- **Not applicable** when the change adds no handler and no error path.
- **Excluded evidence:** fields supplied indirectly through a logging
  helper/middleware count as present.

### AR-CODE-001 — Coding and change discipline
- **Satisfied** when functions remain small and single-purpose, business logic is
  not duplicated across layers, behavior changes are accompanied by added/adjusted
  tests, and the change does not refactor unrelated modules.
- **Violated** when a mega-function is introduced, business logic is duplicated
  across layers, a behavior change ships without tests, or unrelated modules are
  refactored beyond the change's scope.
- **Not applicable** to purely mechanical, behavior-preserving edits with no test
  implications.
- **Excluded evidence:** a legitimately large-but-cohesive function is not a
  violation; multiple valid decompositions are acceptable.

## 4. Recording a rating

Each rating is recorded in [`MANUAL_RATING_TEMPLATE.csv`](MANUAL_RATING_TEMPLATE.csv)
with the rule id, the validation sample id, the rater id, the rating
(`satisfied` / `violated` / `not-applicable`), a confidence, an evidence
reference (path/line), the rubric version, and the blinded flag. The row carries
**no** condition or model column, by design.

## 5. Governance

The rubric is content-hashed and versioned. It is authored and frozen **before**
confirmatory data is collected and is **not** changed after confirmatory results
are visible (see [`MANUAL_RATING_PROTOCOL.md`](MANUAL_RATING_PROTOCOL.md) §6). A
material change bumps the rubric version and invalidates affected confirmatory
ratings.
