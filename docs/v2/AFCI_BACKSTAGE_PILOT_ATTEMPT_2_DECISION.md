# SL-V2-BACKSTAGE-PILOT-03 — Attempt 2 of the Backstage pilot, pre-registered

Status when written: **PRE-DATA freeze. 18 planned observations, 0 attempted,
0 completed.**

> **EXECUTED 2026-09-22 — this freeze has since been discharged in full.** All
> 18 observations ran, 18 are valid, 0 infrastructure-invalid, 0 retries, and
> none of the 18 pre-authorised `execution_attempt=2` identities was activated.
> The frozen §11.1 continuation rule returned **NO ARCHITECTURE SIGNAL — DO NOT
> AUTOMATICALLY EXPAND**. Results, per-run rows and the decision clauses are in
> [`study-results/08_backstage_pilot_attempt_2_completed/`](../../study-results/08_backstage_pilot_attempt_2_completed/README.md).
> **Everything below is the pre-data record and is unchanged.** Nothing in it
> was edited after data existed.

This record authorizes a **new** 18-run execution of the science frozen by
[`AFCI_BACKSTAGE_PILOT_DECISION.md`](AFCI_BACKSTAGE_PILOT_DECISION.md)
(`SL-V2-BACKSTAGE-PILOT-01`). It changes **five execution controls** and **no
scientific artifact**.

Attempt 1 remains **halted and excluded wholesale** under
[`AFCI_BACKSTAGE_PILOT_ATTEMPT_1_HALT_DECISION.md`](AFCI_BACKSTAGE_PILOT_ATTEMPT_1_HALT_DECISION.md)
(`SL-V2-BACKSTAGE-PILOT-02`).

---

## 0. The statement this decision most needs to make

**No scientific outcome from Attempt 1 was used to change any task, the
architecture packet, any oracle, the architecture scorer, any threshold, any
endpoint, any metric definition or the continuation rule.**

Attempt 1's five valid rows were never compared, never aggregated into an arm
total, never turned into a ratio, and never evaluated against the continuation
criterion — before this decision or since. The changes below rest entirely on
**execution facts** — turn counts, tool denials, network state, filesystem path
lengths — which are true of `C1` and `C4` alike and which the harness recorded
per row. None of them is a treatment contrast, and none could be, because no
treatment contrast exists.

---

## 1. Attempt 1: retained, excluded, enforced

| Fact | Value |
| --- | --- |
| Status | **HALTED — INFRASTRUCTURE / BUDGET SUITABILITY FAILURE** |
| Authority | `SL-V2-BACKSTAGE-PILOT-02` |
| Attempted | 7 of 18 |
| Scientifically valid executions | 5 |
| `INFRA_API_TRANSPORT` failures | 2 |
| **Eligible for analysis** | **0 — all seven rows** |
| Captured provider cost | **$10.93**, retained in the record |
| Never started | 11 |

Attempt 1 is **not** replaced, **not** re-run, **not** amended and **not**
pooled with Attempt 2. Its rows stay in the public record as provenance and cost
accounting. It is used for one purpose only: **pre-data engineering evidence**
about the harness.

That exclusion is now **enforced rather than stated**: the Attempt-1 execution
entry point refuses every run id with `ATTEMPT_HALTED` before it reads a plan,
composes a prompt or touches a destination, and a test proves that for all 18
scheduled ids and for an invented one.

---

## 2. Science, unchanged

| Field | Value |
| --- | --- |
| Substrate commit | `f285f6e46ba57d30c5be8448fd018b960d7d4748` |
| Model-visible export tree | `4dfadc101db1c9f29b82934db25def67a93a2563` |
| Tasks | T1, T2, T5 — bytes and digests unchanged |
| Architecture packet | `BACKSTAGE_MAD_V1`, `5bab8d931c24834dc268eb2cdad546abbe13b5e2d9e51e6fbdcfeed09754a7cf` |
| T1 | `c3033787506fa7d30e909638ce64f407fbe9a89a26fb4d84eaf52222a0f8385b` |
| T2 | `60dc08a133c47433e01eb62d96b09e52239e632e8f93df9662a09b46f8a1f32f` |
| T5 | `8db333264895b3d6df869adf27cc419c9adbd696da065cead8bbae610d62ba3d` |
| Model | `claude-sonnet-5` (exact id, never an alias) |
| Effort | `high`, pinned and read back after any silent downgrade |
| Runtime | Claude Code CLI 2.1.229 |
| Authentication | subscription OAuth, `apiKeySource: none` |
| Conditions | `C1` (task only), `C4` (task + governed architecture packet) |
| Reset state | `NON_RESET` only |
| Repetitions | 3 |
| **Matrix** | **18 observations, 9 paired blocks** |
| Primary endpoint | architectural placement / ownership |
| Functional endpoint | `FUNCTIONAL_VALID` iff every semantic case passes |
| Efficiency metrics | unchanged (§7.3 of the freeze) |
| Visible gate | unchanged, byte-identical across the three task statements |
| Hidden functional oracles, architecture scorer, frozen baseline | unchanged |
| **Continuation rule** | **unchanged and unevaluated** (§11.1–§11.3 of the freeze) |

Controlled reference validation is re-read rather than re-run, because nothing
it measures has moved: **3/3 legal references** score functional PASS with 1
applicable / 0 violated architecture opportunities, and **3/3 target-violating
references** score functional PASS with 1 applicable / 1 violated.

---

## 3. Change 1 — turn ceiling 64 → 96

**Evidence.** Of Attempt 1's five scientifically valid observations, **four
reached exactly 64/64 turns**; one finished naturally. One of those four never
ran the visible gate at all before exhausting its budget, and its hidden
functional result was consequently "all semantic cases missing" — the candidate
left non-compiling code because it ran out of budget, not because the oracle
failed.

**Why this is not a result.** The ceiling bound **both arms**: of the four rows
that hit it, two were `C1` and two were `C4`. It is a property of a 203-package,
~769k-LOC repository measured against a budget carried over unchanged from a
six-package synthetic substrate. No arm total, ratio, median or continuation
criterion was computed from Attempt 1, and none may be derived from it.

**The change.** `MAX_TURNS = 96`, applied identically to all 18 rows, to both
conditions, and to every pre-authorised replacement identity. 50% headroom on a
finite, identical budget.

The launcher's wall-clock safety guard rises in the same proportion
(10,800 s → 16,200 s) so that it cannot quietly become the real budget.
Attempt 1's longest valid run was 2,693 s of model time.

---

## 4. Change 2 — Bash permission mechanics

**Evidence.** Attempt 1 recorded **28 refused tool calls** across seven rows,
every one a Bash call the frozen eight-rule allowlist did not admit. All 28 were
extracted from the runtime's own `permission_denials` arrays and classified. A
refused call still costs a turn.

| Intent class | Denials | Disposition under Attempt 2 |
| --- | ---: | --- |
| Compound shell pipelines that inspect repository files | 16 | **No rule.** `Grep`, `Glob` and `Read` are granted and confined |
| A frozen gate command wrapped in shell redirection to a log file | 4 | **No rule.** The plain command is already admitted |
| Toolchain identity (`which`, `--version`) | 3 | **Rules added**, and the rules admit all three strings |
| A frozen gate command followed by an exit-status `echo` | 2 | **Rule added**, but §4.1 measured the runtime refusing the `$?` spelling regardless |
| Unconfined filesystem search from the root | 2 | **No rule.** §4.1 measured the runtime confining readers by directory |
| Arbitrary code execution through an interpreter flag | 1 | **No rule.** §4.1 measured `node -e` refused by the engine |

**None of the 28 was destructive.** All were inspection or validation attempts.
That is why the answer is a permission change at all.

**The allowlist.** Eight rules retained verbatim from §8.1 of the freeze, **none
removed**, seven added — fifteen in total, identical for `C1` and `C4` on all 18
rows:

```
# unchanged from SL-V2-BACKSTAGE-PILOT-01 §8.1
Bash(yarn tsc)                      Bash(yarn tsc:*)
Bash(yarn test:*)                   Bash(yarn prettier:*)
Bash(yarn backstage-cli:*)          Bash(yarn backstage-repo-tools:*)
Bash(git status:*)                  Bash(git diff:*)
# added for attempt 2
Bash(yarn --version)                Bash(node --version)
Bash(corepack --version)            Bash(which:*)
Bash(echo:*)                        Bash(git log:*)
Bash(git ls-files:*)
```

Every added rule is read-only: none can create, modify, delete, move, install,
fetch or execute a file, and none can leave the run workspace.
`Bash(node --version)` names an interpreter but is an **exact** rule and cannot
be extended into one.

**What was deliberately not added — and a correction the probes forced.** No
rule admits `grep`, `find`, `cat`, `head`, `tail`, `ls`, `wc`, `tee`, `cd`, an
interpreter, a package manager, a network client, or any writer.

The reason was first written as a contamination control: that Bash is **not**
confined by `--add-dir`, so a `grep` rule would open a file-reading channel
outside the model-visible export. **That reasoning was wrong, and the probes
below found it.** The conclusion survives as a smaller claim: adding those rules
would be **redundant, not dangerous**. What this allowlist genuinely withholds is
everything the runtime does *not* auto-admit — interpreters, package managers,
network clients, writers and history rewriters.

### 4.1 The synthetic probes, and what they overturned

The permission surface could not be established statically: the runtime ships as
a single binary whose matcher is not recoverable as source. So it was measured.
**Five probes** — no task, no architecture packet, no pilot run id, no pilot
destination, **0 observations consumed**, **$0.51** of provider cost in total.
Two of them returned FAIL, and both failures corrected this decision rather than
being corrected away; the final probe agreed with the corrected specification on
all 10 of its commands.

| # | Measured | Result |
| --- | --- | --- |
| 1 | a frozen inspection command followed by `; echo EXIT=$?` — every segment admitted by the rules | **REFUSED**: *"Contains simple_expansion"* |
| 2 | the same list with `; echo done`, and the `&&` form | **ADMITTED** |
| 3 | `head`, `grep`, `cat` and a `\| head` pipe inside the workspace — **no rule names any of them** | **ADMITTED** |
| 4 | `ls ..`, and `cat` / `ls` at an absolute path outside the workspace | **REFUSED**, the runtime naming the directories it would allow |
| 5 | `git commit --allow-empty`, `curl`, `node -e`, `powershell -c` | **REFUSED**: *"This command requires approval"* |
| 6 | `rm`, `git reset --hard`, `git clean -fdx`, `git push` | **not attempted** — the model declined to issue them |

Three consequences, all now encoded rather than assumed:

1. **The blocker on the gate-command denials is the `$?` expansion, not the
   `;`.** The `echo` rule therefore does **not** recover those two denials as
   written, and the specification was corrected to say so.
2. **The allowlist is not the whole permission surface.** The runtime
   auto-admits read-only commands and confines them by directory. The
   contamination control that actually holds is the runtime's — which is
   precisely why no `find` rule is added: an allow rule is the one thing that
   could put that confinement at risk.
3. **The rule-level negative claim now has a second leg.** "No rule admits
   `curl`" was always decidable; "and therefore `curl` is refused" was an
   inference. It is now a measurement, four times over, in the runtime's own
   words.

**The honest accounting.** Under the corrected specification the rules admit
**3 of the 28 recorded command strings** and refuse 25. That is a statement about
**the rules**, not a forecast of the engine: the engine auto-admits commands the
specification cannot enumerate, so a per-denial forecast would be a guess dressed
as a number. **The residual denial rate is not predicted.** It is measured per
run from `permission_denials`, which every observation captures, exactly as §8.1
of the freeze requires. Attempt 2 does **not** claim to have eliminated
denial-driven turn loss.

**The task statements were not edited.** They are frozen, and they were not
changed to tell the model to avoid compound shell commands. A permission change
is an execution control; a prompt change would be a treatment change.

**Negative safety tests.** **32** negative controls are proved to be admitted by
**no rule**, spanning destruction (`rm -rf`, `git clean -fdx`,
`git reset --hard`), history and identity (`git commit`, `git push`,
`git remote add`, `git stash`, disabling the long-path setting), escape
(`curl`, `wget`, `yarn install`, `npm install`, `node -e`, `python -c`,
`bash -c`), and unconfined reads (`find /`, an absolute-path `cat` into the
evaluator tree, a recursive `grep` over the development root, `ls ..`,
`cd .. && ls`). That is sound at the rule level: a command no rule matches
cannot be admitted by any matcher. Probe 3 confirmed the other half against the
**live engine** for four of them. The remaining four destructive controls were
**never attempted** — the model declined to issue them even when told the
workspace was disposable and that refusals were the point. That is recorded as
**not measured**, never as denied.

---

## 5. Change 3 — network preflight and VPN state

**Evidence.** Attempt 1 rows 6 and 7 both exhausted the runtime's ten API
retries and exited 1 **below** the turn ceiling, at 56/64 and 54/64. Confirmed
afterwards: DNS dead against both the configured resolver and a public one,
100% ICMP loss, and a VPN adapter that stayed **up** holding an unresponsive
resolver.

**The control.** Before **every** substantive model invocation, and before the
task is delivered:

1. **no VPN adapter is up** — read from the OS adapter table, matched by adapter
   name *and* interface description;
2. **`api.anthropic.com` resolves** — by `getaddrinfo`, with no shell and no
   parsing of a localised tool's output;
3. **the endpoint answers** — TCP + TLS on 443 and one unauthenticated HTTPS
   request. **`401` is a PASS**: it proves the service answered;
4. **three consecutive passes**, because the fault is intermittent by nature.
   Fewer than three is itself a refusal.

**Failure handling.** A failed preflight raises `NETWORK_PREFLIGHT_FAILED`
**before** the artifact directory is created, before the prompt is written and
before any process exists. **No task is delivered and no observation is
consumed.** The cell's identity stays free, at attempt 1 — a preflight failure
burns no replacement identity, because nothing was spent.

**Condition neutrality.** The preflight imports only the standard library and
cannot reach any module that composes, hashes or delivers a prompt; that is
asserted against its import graph, not its text. It sends no credential and no
study content. Its evidence is recorded in the run artifact as infrastructure
and enters no metric, no endpoint and no comparison. `C1` and `C4` are checked
by the same code, in the same order, against the same thresholds. The dry
validation deliberately does **not** run it: a schedule's validity must not
depend on the weather.

---

## 6. Change 4 — pre-authorised infrastructure retry identities

**Evidence.** Attempt 1 halted not because a retry was forbidden —
[`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md) §2 lists
`INFRA_API_TRANSPORT` as rerun-eligible — but because the infrastructure could
not *express* one without a mid-study protocol amendment.

**The control.** The Attempt-2 plan derives **both** identities for every cell
**before any data**: 18 **scheduled** rows at `execution_attempt = 1`, and 18
**pre-authorised replacements** at `execution_attempt = 2`, derived, reserved,
destinations checked free, and **not scheduled**. 36 reserved identities, all
unique, none overlapping Attempt 1.

**Activation.** A replacement is refused unless all of the following hold: the
attempt-1 row for the **same scientific coordinates** has a run record; that
record is invalid; its failure class — derived from the record's own fields and
its own captured stream, never from an operator's description — is one of the
governed infrastructure classes; the replacement's back-pointer is the attempt-1
row for that cell, located by **coordinates** so a hand-edited pointer cannot
nominate a predecessor; and both destinations are free.

**Eligible classes, enumerated before data:** the seven of
`FAILURE_RERUN_POLICY.md` §2 — `INFRA_API_TRANSPORT`, `INFRA_AUTH_OUTAGE`,
`INFRA_WORKTREE_CORRUPT`, `INFRA_RUNNER_CRASH`, `INFRA_EVALUATOR_MOUNT`,
`INFRA_MISSING_ARTIFACT`, `SETUP_CONTAMINATED` — plus the launcher's own
pre-scientific surfaces: workspace-preparation failure, substrate identity
mismatch, model-identity readback failure, effort readback failure, runtime
version mismatch, non-sterile runtime context, session identity not captured,
runtime process failure before completion, unreadable usage accounting, and a
candidate workspace that was not preserved.

**Never retried, enumerated before data:** `BUDGET_TURNS_EXHAUSTED`,
`MAX_TURNS_REACHED`, `COMPLETED`, `VISIBLE_CI_FAIL`, `HIDDEN_TEST_FAIL`,
`ARCH_VIOLATION`, `INCOMPLETE_IMPLEMENTATION`, `INVALID_CODE`, `NO_PATCH`,
`REFUSAL`, `TIMEOUT`, `BUDGET_TOKENS_EXHAUSTED`, high cost, high token usage,
tool strategy, bad implementation, treatment outcome.

The two lists are **disjoint**, and a run that cannot be classified is **not**
retryable: the classifier fails closed, because that is the only direction that
cannot manufacture a replacement.

**Attempt 3 is not pre-authorised.** §5 of the rerun policy directs that
repeated infrastructure failure on one cell is *"escalated, not silently
re-attempted"*, and names `TD-N06` — an **open** decision — as the escalation
policy. Existing governance does not support a second infrastructure retry, so
none is pre-authorised here.

**Scientific invariance.** Scientific coordinates are
`(task, condition, repetition, reset_state)` and are identical across attempts,
along with the sequence, the block, the position in the block, the budget, the
model, the effort and the frozen payload digests. **The scientific projection
ignores `execution_attempt` entirely**: it is 18 cells, and a replacement adds
no cell.

**Validated against Attempt 1's real records.** Run over Attempt 1's seven spent
run records, with no input from the halt decision, the gate reproduces that
decision's own classification: the 2 severed rows classify as
`INFRA_API_TRANSPORT` and authorise a retry; the 5 valid rows — **four of them
at 64/64 turns** — classify as valid observations and authorise nothing.

---

## 7. Change 5 — real-destination path validation

**Evidence.** Attempt 1's first launch was refused with
`SUBSTRATE_IDENTITY_MISMATCH`: the longest substrate-relative path is **178**
characters and the frozen run roots were **92**, giving 271 — past Windows'
260-character limit. Two tracked fixture files were missing from the workspace
commit. The operating system had long paths enabled, so the files were written
correctly; **git** failed, because `core.longpaths` was unset, and `git add -A`
**warned and exited 0**. Preparation had been validated end to end on five
disposable workspaces — all five at a **30-character** root.

**The controls, all frozen here:**

* **Shorter roots.** Every one of the 36 reserved run roots is **62 characters**,
  against a budget of `259 − 1 − 178 = 80`. The longest substrate file therefore
  lands at 241 — inside the classic limit **even if `core.longpaths` were lost**.
  Attempt 1's 92 would not pass this budget, and a test asserts that.
* **`core.longpaths` verified, not assumed.** Required at **system** scope and
  read back before every run. System scope rather than per-user because the
  launcher pins a sterile `HOME`: a per-user setting would reach preparation and
  not the model, and the model's own `git status` would then report two tracked
  files as deleted at t=0, contaminating both the visible gate's changed-file
  derivation and the scorer's change scoping.
* **The tree hash decides, not git's exit code.** The prepared commit's tree must
  be `4dfadc101db1c9f29b82934db25def67a93a2563` exactly, with one commit and no
  remote, checked before the model is launched. It is the only statement that
  survives the failure mode above.
* **Preparation validated at the REAL length.** Two disposable workspaces are
  prepared at roots of **exactly** the frozen 62 characters — one standing for
  `C1`, one for `C4`, same task — outside every scientific root.

**Dependency isolation, re-proved at that length.** Per workspace: the committed
tree is the frozen export tree, every expected exported file is present, one
commit and no remote, and the dependency digest, junction map, junction count,
file count and total bytes all match the frozen layout manifest, with **zero**
junctions pointing outside the run root — so package resolution cannot reach
another run's sources or the template's. Across the two: identical dependency
digest, junction count, file count and total bytes, disjoint roots, no
pre-warm touched a tracked file, and the **template is byte-identical before and
after**.

---

## 8. The schedule

| Field | Value |
| --- | --- |
| Seed | `AFCI_BACKSTAGE_ATTEMPT_2_V1_20260922` |
| Runs | 18 scheduled, plus 18 pre-authorised replacements = 36 reserved identities |
| Blocks | 9 |
| **Execution plan SHA-256** | `fa096eb09fafd33be160f52a72f1d9ef92ff1f3ca087079aaaa2d136b3fc60e3` |
| **Scientific schedule SHA-256** | `2cca54c3f8bc4beb57a8f9d800fe0ad41d6c6f3a470c548b47b8194de3dca60c` |
| **Scientific projection SHA-256** | `4d41c7d4c2e359f53d11d331cc16a316cc433f893b31614781d336ecd15f5b7f` |
| Scheduled execution attempt | 1 |
| Pre-authorised attempts | 1 and 2. **Not 3** |

Three digests, three questions. The **execution plan** hash covers every field,
science and infrastructure alike. The **scientific schedule** hash covers the 18
scheduled rows reduced to the scheduling facts that *are* the experiment —
pairing, order, budget, model, effort and the frozen payload digests — so moving
an artifact root is visibly not a change to the experiment, and a change to the
experiment cannot hide inside one. The **scientific projection** hash covers the
five values that are the experiment, over the 18 cells, ignoring
`execution_attempt`.

All 36 reserved identities are unique, all 72 destinations are unoccupied, and
**none overlaps an Attempt-1 run id or destination** — proved by deriving
Attempt 1's identities from its own generator rather than from a remembered list.

### One deliberate improvement to the randomisation

Attempt 1 drew the within-block condition order by an unrestricted sort on a
seeded hash and happened to land on 4 `C1`-first of 9. The Attempt-2 seed lands
that same unrestricted draw on **6 of 9** — a two-thirds/one-third split of the
only control protecting the arms from session drift.

So the within-block order is drawn under a **restriction**: the nine blocks are
ranked by a seeded key and the five lowest-ranked run `C1` first. It is exactly
as deterministic and exactly as reproducible — same seed, same schedule, on any
machine and any Python — and it makes first-position balance a property of the
**method** rather than of which seed was tried. Nine is odd, so exact balance is
unavailable; the residual block goes to `C1`-first **by rule**, stated before
any data. The block order itself remains unrestricted: it exists so the tasks
interleave, and no balance property depends on it.

This changes the randomisation *method*, not the matrix. The 18 cells, the 9
blocks and the pairing are identical.

---

## 9. Readiness

**87 pre-data checks, all passing**, re-derived from the artifacts rather than
asserted: the controlled reference matrix, every frozen digest, task and packet
non-leakage, the visible gate's byte-identity across the three statements, the
matrix and pairing, the 96-turn ceiling in both arms, the 15-rule allowlist with
its 32 negative controls, the five probe records and what they measured against
the live runtime, the network preflight, `core.longpaths` at system scope, all
36 real destination lengths, the export tree, dependency isolation at the real
path length, the 36 reserved identities with 72 free destinations, zero overlap
with Attempt 1, and **zero Attempt-2 substantive observations**.

Several of those checks EXERCISE the guard rather than reading a constant: the
readiness gate builds launches at 64, 95, 97 and three malformed ceilings and
requires all six to be refused; it asks the preflight for two passes and
requires that to be refused; and it hands the export check a wrong tree hash and
requires `SUBSTRATE_IDENTITY_MISMATCH`. A guard that had been removed would fail
the readiness check rather than pass it.

Dependency isolation was re-proved end to end at the real 62-character
destination length, on two disposable workspaces standing for `C1` and `C4`:
both committed the frozen export tree, both carried 10,362 tracked files, 204
junctions, 266,599 dependency files and 1,979,103,089 bytes — **identical** —
with zero junctions outside either run root, neither pre-warm touching a tracked
file, and the template unchanged.

---

## 10. What this decision does NOT do

* It does not modify any task, the architecture packet, any oracle, the
  architecture scorer, the frozen baseline, any threshold, any endpoint, any
  metric definition or the continuation rule.
* It does not re-run, replace, amend, re-score or re-read any Attempt-1 row.
* It does not pool Attempt 1 with Attempt 2, in any analysis, ever.
* It does not weaken the visible gate and disables no repository rule.
* It does not authorize a reset arm, select a primary model, pass `G1` or `G2`,
  or confer confirmatory eligibility. `TD-B03` stays open; `primary_model` stays
  `null`.
* It does not authorize expansion. §11 of `SL-V2-BACKSTAGE-PILOT-01` does, on the
  stated evidence, and that rule is unchanged and unevaluated.
* It does not execute anything. **At the moment this decision is written,
  `AFCI_BACKSTAGE_PILOT_ATTEMPT_2` has 18 planned observations and 0 attempted.**

---

## 11. Infrastructure activity performed for this freeze

Recorded for completeness, because "no model was run" would otherwise be
imprecise:

* extraction and classification of Attempt 1's 28 recorded tool denials (no
  model);
* offline validation of the permission surface: every representative legitimate
  command admitted by the rules, all 32 negative controls refused by the rules
  (no model);
* **five synthetic infrastructure probes** (§4.1) — no task, no architecture
  packet, no pilot run id, no pilot destination, 0 observations consumed,
  $0.51 total. They measured the runtime's own permission semantics, and two of
  their findings corrected this decision rather than confirming it;
* the network preflight, executed three consecutive times (no model, no
  credential, no study content);
* dependency-isolation preparation on two disposable workspaces at the real
  destination path length (no model);
* the 69-check readiness derivation (no model).

**No benchmark condition was executed. No task was solved by a model. No `C1` or
`C4` Attempt-2 result exists. No treatment metric was computed.**
