# AFCI-Bench — key findings

Each finding separates **observed fact** from **interpretation** and states what
bounds it.

---

## Finding 1 — Explicit architecture context did not pay for itself

**Fact.** In the 36-run efficiency pilot (`claude-sonnet-5`, 16 paired blocks),
the median C4/C1 input-token ratio was **1.4014**; C4 was cheaper in **4 of 16**
pairs. Wall time 1.2660, exploration calls 1.3939, tool calls 1.1864, unique files
read 1.2111, edit/write calls 1.9167, non-reset provider cost 1.4928. The only
endpoint at parity was CI command runs (1.0000).

**Fact.** Functional quality was essentially equal: **17/18** functionally valid
runs under C1 and **17/18** under C4.

**Interpretation.** Injecting the MAD made the model do *more* of everything
without doing it *better*. The effect is large and consistent across endpoints, not
marginal — the cheapest endpoint still ran ~19% above baseline and the most
expensive nearly doubled.

**Bound.** One model, one substrate, three tasks, 16 pairs. Descriptive medians
only — no p-value, CI or effect size exists or could be justified.

---

## Finding 2 — The pre-registered rule returned STOP, and it was honoured

**Fact.** Endpoints, thresholds and the decision rule were frozen in
`AFCI_EFFICIENCY_PILOT_DECISION.md` §10–§11 **before any observation existed**.
Applying them unchanged yields
`STOP — NO EFFICIENCY SIGNAL JUSTIFIES FULL-SUITE EXPANSION`, with
`efficiency_claim_made = false`. Both functional guardrails and the minimum-pairs
gate passed; every token and secondary threshold failed.

**Interpretation.** This is the strongest methodological evidence in the package.
A rule fixed in advance produced an unwelcome answer and was not renegotiated. Any
later positive result from this programme is more credible because this one was
allowed to be negative.

---

## Finding 3 — A reset-recovery signal runs the other way

**Fact.** Reset overhead is the metric under reset divided by the same
task/condition without reset. C4's overhead was **lower** than C1's in:

- **2 of 3** tasks for input tokens (PT01, PT07)
- **3 of 3** tasks for wall time (PT01, PT04, PT07)
- 2 of 3 for exploration calls and for tool calls

**Fact.** The RESET-SPECIFIC GO branch failed **only** on its overall token clause
(11.3.2). Both of its reset-overhead clauses (11.3.3, 11.3.4) **passed**.

**Interpretation.** This is the one place the mechanism AFCI is actually about —
cheaper re-establishment of architectural intent after context is lost — appears in
the data. A model handed the MAD again after a reset recovers more cheaply than one
that must re-derive the architecture. That is a coherent story and it is the most
interesting thing in the pilot.

**Bound.** Three tasks. Descriptive. It failed the branch that would have made it a
GO. It must not be reported as a result, and it is not one.

---

## Finding 4 — Instrument after instrument sat at the architecture floor

**Fact.**

| instrument | model | arm(s) | functional | target architecture violations |
| --- | --- | --- | ---: | ---: |
| PT08 | Sonnet | C1 | 3/3 | **0/3** |
| PT09 | Sonnet | C1 | 3/3 | **0/3** |
| PT10 | Sonnet | C1 | 3/3 | **1/3** |
| PT01 | Haiku 4.5 | C1 + C4 | 6/6 | **0/3** and **0/3** |
| PT04 | Haiku 4.5 | C1 + C4 | 5/6 | **0/3** and **0/3** |
| PT07 | Haiku 4.5 | C1 + C4 | 6/6 | **0/3** and **0/3** |

PT08's descriptive violation proportion is `0.0`. PT09 classified **FAIL /
ARCHITECTURE FLOOR**; PT10 **REVISE / WEAK PRESSURE**; both **STOP / REASSESS**.

**Interpretation.** PT09 and PT10 were purpose-built to fix exactly what PT08
lacked, and landed in the same place. The lower-model pilot then put PT01, PT04 and
PT07 at the floor too — in **both** arms, and on a *weaker* model, which was the
condition most likely to produce a violation. Six instrument/model combinations at
or near the floor is no longer plausibly a task-design accident: it is evidence
about the **measurement conditions**. An agent on a legible synthetic repository
rarely takes the architectural shortcut the instrument needs it to take, whether
guided or not, and whether strong or weak.

**Bound.** Three observations per instrument per arm. No package has been
independently reviewed (`TD-B32` open). The instruments admit an
architecture-neutral implementation by construction, which `SL-V2-QUAL-01` decided
in advance was not disqualifying — a defensible but challengeable policy call.

**Consequence.** Without a discriminating instrument, the study's central construct
cannot be measured at all. This is the binding constraint on the programme, and the
lower-model pilot has now tightened rather than loosened it: the shortcut does not
appear even when the model is weaker.

---

## Finding 5 — v1's apparent result does not survive its own method

**Fact.** v1 showed AFCI with **+65.7%** code churn and **+41.3%** test churn, and
higher churn on **12/12** tasks; on reset drift, AFCI was lower on only **1/12**.

**Fact.** The v1 harness never reset the working tree between tasks, so edits
accumulate monotonically across T01→T12 (L1), and the harness **did not invoke a
model** at all (L2). AFCI-Guard's regexes never fired, so its all-zero conformance
table is not a measurement (L3). `layer_jaccard` is a constant 1.0 (L5).
`ci_pass` is saturated `True` across all 48 cells, so the success gate does not
discriminate (L6).

**Interpretation.** The v1 numbers are real measurements of a confounded quantity.
They are not a treatment contrast and should not be cited as evidence for or
against the hypothesis. They remain valuable as the record of why v2 was built the
way it was.

---

## Finding 6 — The benchmark machinery works, and proved it by catching itself

**Fact.** Two real defects were found, recorded in full and repaired:

1. **Run-id collision (`SL-RUNID-01`).** `derive_run_id` omitted the reset state,
   so the 36-row pilot derived only 18 identities. It surfaced at sequence 9, after
   the money was spent, when the collision destroyed a completed governed record.
   Attempt 1 was aborted wholesale — **including its 7 intact rows** — because
   which rows survived was a selection mechanism nobody designed.
2. **Infrastructure-invalid non-observation.** A PT09 attempt failed on a cp1252
   encoding error that handed the model an empty prompt. It was recorded as a
   non-observation, did not consume one of the three repetitions, and was re-run.

**Fact.** Across all v2 runs: sterile execution, exact model readback, context
audit `CLEAN`, hidden functional acceptance, out-of-band architecture scoring and
the artifact firewall executed on every repetition.

**Interpretation.** The exclusion rules are enforced in code, not prose:
`assert_single_execution_attempt` refuses any record set spanning execution
attempts and refuses any Attempt-1 record even alone. The evidence base is small,
but what exists is trustworthy and auditable.

---

## Finding 7 — Two rival explanations; the ceiling one has now been tested

**Fact.** Every Sonnet v2 run used `claude-sonnet-5` on one governed substrate:
commit `630d3180`, content hash `0198d76c…`, **49 files**.

**Interpretation — ceiling.** Functional acceptance was saturated everywhere
(3/3, 3/3, 3/3, 17/18, 17/18) and baseline architecture violations were at or near
zero. A saturated outcome cannot improve, and a floor has no room beneath it.

**Interpretation — legibility.** A synthetic Nx monorepo announces its own layering
through its import graph and path aliases. A model can deduce the intended
architecture without the MAD, which attacks the MAD's marginal value directly.

**Update (Finding 8).** The ceiling explanation has now been tested directly and
was **not supported**. The legibility explanation remains untested and is now the
only one of the pair still standing.

---

## Finding 8 — Weakening the model did not rescue AFCI; it cost more

**Fact.** The 18-run lower-model pilot (`claude-haiku-4-5-20251001`, non-reset
only, 8 paired blocks) gave a median C4/C1 input-token ratio of **2.0372**, with
C4 cheaper in **2 of 8** pairs. Wall time 1.5268, exploration calls 1.7308, tool
calls 1.5023, unique files read 1.2500, edit/write calls 1.1741, provider cost
1.8865. CI command runs were again the only endpoint at parity (1.0000).

**Fact.** Side by side, **never pooled**: within-Sonnet non-reset median
**1.5582** (n=9) versus within-Haiku **2.0372** (n=8) — a difference of
**+0.479** in the direction *opposite* to the moderator hypothesis.

**Fact.** Functionally, C4 was the better arm: **9/9** valid versus C1's **8/9**.
The single invalid run was `PT04/C1/R2`, which failed all four semantic cases.

**Fact.** Architecture: 1 applicable opportunity per run, 18 across the set,
**0 violated in both arms** (C1 0/9, C4 0/9 target-violation runs).

**Interpretation.** The hypothesis was that a weaker model, less able to infer the
architecture from the repository, would have more to gain from being told it. The
data run the other way: the weaker model spent *relatively more* to consume the
same document. A plausible mechanism is that the MAD is a fixed cost that a weaker
model amortises worse — it re-read files more than twice as often (43 repeated
reads versus 16) and needed more turns (309 versus 229) — but this pilot was not
designed to test that mechanism and does not establish it.

**Interpretation — the quality channel answered nothing.** Both arms sat at zero
violations. C4 did not fail to beat C1; there was nothing to beat. The frozen rule
records this as a FAIL because it requires *strictly fewer* violations, and a tie
at the floor is not an improvement. Read it as **no information**, not as evidence
against the architecture document.

**Bound.** One lower-capability model, the same single synthetic substrate, three
tasks, 8 paired blocks, 3 repetitions. Descriptive medians only. The two models
are two separate experiments and are never pooled into one treatment estimate.
PT07 is the one task where C4 was directionally cheaper on tokens, time, output
and cost — on 3 blocks.

**Consequence.** The frozen continuation rule returns
`NO LOWER-MODEL SIGNAL — DO NOT EXPAND THE SYNTHETIC LOWER-MODEL MATRIX`. Both
functional guardrails passed; every quality and efficiency trigger failed.

---

## What must not be concluded

1. **Not** that AFCI does not work. The Sonnet cost pilot measured **cost** and
   produced **no architecture endpoint at all**. The lower-model pilot did produce
   one, and it was **uninformative** — both arms at zero. Neither licenses the
   claim that the architecture document has no quality effect.
2. **Not** that AFCI is universally useless because C4 cost more. Cost is one of
   two channels and the frozen design refuses to combine them, precisely so that a
   cost loss cannot be read as a quality loss.
3. **Not** anything with statistical confidence. No p-values, CIs, effect sizes or
   power estimates exist in this programme.
4. **Not** that model capability has been shown to moderate AFCI's value. The
   Sonnet and Haiku pilots are **two separate experiments**, compared descriptively
   and never pooled. Nothing here is a randomised cross-model causal effect, and no
   interaction was estimated.
5. **Not** anything beyond `claude-sonnet-5` and `claude-haiku-4-5-20251001` —
   `primary_model` is still `null` and no study model has been selected.
6. **Not** anything beyond this one synthetic 49-file substrate.
7. **Not** that the reset-recovery signal is a result. It is a motivation.
8. **Not** any number from efficiency Attempt 1, which is excluded in whole and in
   part.
