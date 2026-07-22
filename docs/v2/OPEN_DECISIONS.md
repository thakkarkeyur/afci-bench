# docs/v2 — Open Decisions Registry (Blocking & Non-Blocking TODOs)

Status: **authoritative registry of unresolved decisions for study v2**. Every
`TD-*` reference in the v2 protocol resolves to a row here. This is the single
source of truth for what is **not yet decided**, who owns it, whether it
**blocks** data collection, and where it is resolved. Development artifact only:
it does **not** freeze the final benchmark configuration and authorizes **no**
paid model run.

> **Pre-freeze draft.** The protocol is **structurally complete but not
> scientifically frozen** (see [`README.md`](README.md)). **None** of these
> decisions is resolved by the pre-execution design-review reconciliation;
> scientific freeze occurs only after that reconciliation is **independently
> approved** and the relevant blocking decisions are **closed**. Binding *design*
> decisions (D1–D13) are recorded separately in
> [`CRITICAL_DESIGN_DECISIONS.md`](CRITICAL_DESIGN_DECISIONS.md); they are not
> resolutions of these data/artifact-dependent blockers. No `protocol-freeze` tag
> exists.

Machine-readable companion: [`OPEN_DECISIONS.csv`](OPEN_DECISIONS.csv). A test
(`experiments/v2/harness/tests/test_open_decisions.py`) asserts that every `TD-*`
cited anywhere in the protocol appears here, that every entry has an owner, and
that none is yet marked resolved.

## Counts

- **Blocking decisions: 21** (`TD-B01`–`TD-B21`) — must be resolved before the
  corresponding data collection; all are cited inline across the protocol files.
  `TD-B16`–`TD-B21` were added by the pre-execution design-review reconciliation.
- **Non-blocking decisions: 6** (`TD-N01`–`TD-N06`) — refinements that do not
  block the confirmatory design.
- **Total open decisions: 27.** None resolved (pre-freeze draft, not a
  data-collection package).

A **blocking** decision, if left unresolved, would invalidate or bias the
associated result; it maps to a pilot gate (`G1`–`G8`) where feasible. A
**non-blocking** decision improves rigor or reproducibility but does not gate the
confirmatory analysis.

---

## Blocking decisions (TD-B01 – TD-B21)

| ID | Decision | Owner | Resolved during | Gate |
|----|----------|-------|-----------------|------|
| **TD-B01** | **Condition-neutral, non-canonical** reset checkpoint predicates + the pre/post-reset budget split (pre-reset consumption logged separately from **equal** post-reset allowance) per task | Pilot Task Designer | pilot task design | G2 |
| **TD-B02** | Freeze the final model-execution settings after resolving MODEL_EXECUTION_CONTROLS Q1–Q10 by a controlled dry run | Harness Engineer | after dry-run validation | — |
| **TD-B03** | Select the primary benchmark model (do **not** select Sonnet or Opus yet); screen incl **C1/C3/C4**; **never** select on the largest AFCI effect (D10) | Study Lead | after dry-run validation (TD-B02) | — |
| **TD-B04** | Author the approved MAD and machine-checkable architecture-rule catalog (rule ids; severity; evaluator) delivered by C3/C4 | Oracle Designer | pilot task design | G1/G5 |
| **TD-B05** | Author the hidden acceptance criteria, out-of-scope surface, and legitimate alternatives per task (kept hidden) | Oracle Designer | pilot task design | G1 |
| **TD-B06** | Final distribution/family and endpoint specification and degenerate-outcome coding (after dispersion & ceiling checks) | Statistician | pilot | G2 |
| **TD-B07** | Significance level, power target, minimum detectable effect, effect-size boundaries (**NOT** from v1) | Statistician | a-priori + pilot | G3 |
| **TD-B08** | The C2↔C4 token-match tolerance value (from the measured C4 MAD token count) | Study Lead + Statistician | pilot task design | G4 |
| **TD-B09** | Industrial data availability, AFCI adoption date, minimum interpretable sample, raw-data access, anonymization feasibility | Industrial Data Owner (FGC) | feasibility audit | G7 |
| **TD-B10** | Replication count per cell (from pilot dispersion + target precision; **NOT** from v1) | Statistician | pilot | G2/G3 |
| **TD-B11** | Total fixed budget per run (tokens/turns/time) kept equal for reset and non-reset | Harness Engineer | pilot task design | — |
| **TD-B12** | Guard/oracle validation (labelled corpus; mutation tests; **alias + barrel + re-export** resolution; **moved/deleted-code + full-repository** eval; **seeded-violation sensitivity**; **known-good specificity**; legitimate alternatives frozen before confirmatory data; blinded double rating **≥0.70**) | Guard Engineer | pilot | G6 |
| **TD-B13** | Demonstrate benchmark discrimination (tasks/checkpoints distinguish conditions; non-degenerate) | Pilot Task Designer + Statistician | pilot | G2 |
| **TD-B14** | Task-suite selection and layer taxonomy (required/optional/prohibited layers per task) | Task Designer | pilot task design | G1/G2 |
| **TD-B15** | The pre-registered unacceptable-cost tolerance for RQ3 | Statistician + Study Lead | pilot | — |
| **TD-B16** | Agent-visible CI separation enforced in the live runner (`ci:agent` only; hidden acceptance + architecture-oracle checks never in the model workspace/feedback loop) | Harness Engineer | after the runner exists (TD-B02) | — |
| **TD-B17** | Public-task architecture-leakage validation of the authored v2 task suite (validator OK; exceptions justified) | Task Designer | pilot task design | G1 |
| **TD-B18** | Byte-identical C3/C4 frozen architecture-content parity (hashes recorded; no C4-only hard rule; frozen before pilot) | Oracle Designer | pilot task design | G5 |
| **TD-B19** | Isolated container + dedicated identity + CLEAN context audit (managed policy absent) for every counted run | Harness Engineer | container baseline | — |
| **TD-B20** | Interaction-focused power simulation (condition × reset), mandatory before the core grid; final counts simulation-determined | Statistician | pilot | G2/G3 |
| **TD-B21** | Runtime model-id dry runs (Q1 resolved-id readback; Q8 invalid-id rejection), blocking before the paid pilot | Harness Engineer | after dry-run validation (TD-B02) | — |

Added by the pre-execution design-review reconciliation: `TD-B16`–`TD-B21`. Each
is **open** (none resolved here — the CI/leakage **mechanisms** are delivered and
tested, but the runner-time enforcement, authored suite, frozen hashes,
container, pilot simulation, and dry runs all remain outstanding).

---

## Non-blocking decisions (TD-N01 – TD-N06)

| ID | Decision | Owner | Resolved during |
|----|----------|-------|-----------------|
| **TD-N01** | Pin CI to the exact Node patch (`node-version-file: .nvmrc`) so CI and local cannot drift | Harness Engineer | before final config freeze |
| **TD-N02** | Triage the 41 known npm advisories in the transitive tree | Harness Engineer | before final config freeze |
| **TD-N03** | Decide whether to add a workflow/agent experimental arm with a recordable mechanism | Study Lead | optional; later |
| **TD-N04** | Capture the container image digest in `environment_fingerprint` once the container baseline is chosen | Harness Engineer | with the container decision |
| **TD-N05** | Detailed anonymization/pseudonymization scheme for the industrial dataset | Industrial Data Owner (FGC) | with G7 |
| **TD-N06** | Escalation policy for repeated infrastructure failure on a single run cell | Harness Engineer | before runs |

---

## Related open items outside this registry

`MODEL_EXECUTION_CONTROLS.md` §7 lists ten runtime **dry-run-required** questions
(Q1–Q10) about the Claude CLI's effort readback, thinking, workflow mode, and
model-id handling. Those are the concrete validations that must be performed
before `TD-B02` (freeze model-execution settings) and `TD-B03` (select the
primary model) can be resolved. They require a controlled `claude -p` run and are
therefore **out of scope for this protocol-development package**, which performs
no paid model run. The **model-id** items specifically — **Q1** (resolved-id
readback) and **Q8** (invalid-id rejection) — are now tracked as their own
blocking decision **`TD-B21`**, dry-run blockers before the paid pilot.

## Updating this registry

- Add or change a decision in **both** [`OPEN_DECISIONS.csv`](OPEN_DECISIONS.csv)
  (authoritative, test-checked) and this table.
- When a decision is resolved, change its `status` to `resolved` **and** record
  the resolution (value + evidence) in the owning artifact; do not delete the
  row (protocol-version history).
- Any new `TD-*` cited in a protocol file must have a row here, or the
  cross-reference test fails.
