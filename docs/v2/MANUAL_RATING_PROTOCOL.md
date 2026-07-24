# docs/v2 — Manual Rating Protocol

Status: **development protocol for study v2**. Defines how manual ratings of the
non-automatable architecture rules are conducted so that a manual rule may
contribute to an endpoint only after demonstrated reliability. Development
artifact only: it does **not** freeze the final benchmark configuration,
authorizes **no** paid model run, and **no human ratings are conducted in this
package**.

Related: [`MANUAL_ORACLE_RUBRIC.md`](MANUAL_ORACLE_RUBRIC.md) (the criteria),
[`MANUAL_RATING_TEMPLATE.csv`](MANUAL_RATING_TEMPLATE.csv) (the record),
[`ORACLE_VALIDATION_REQUIREMENTS.md`](ORACLE_VALIDATION_REQUIREMENTS.md) §4.
Blocking decision: **`TD-B12`**.

---

## 1. Blinded rating

Raters see the **patch and repository state only**. The material handed to a
rater is normalized so that **no condition identifier (C1–C4) and no model
identity** appears in any path, filename, commit metadata, or rating record. A
rater must not attempt to infer the condition or model; a rating that references
condition/model is void.

## 2. Two independent raters for the validation sample

For the **validation sample** (the labelled subset used to establish
reliability), **two raters rate independently**, without discussion, each
recording a row per item in [`MANUAL_RATING_TEMPLATE.csv`](MANUAL_RATING_TEMPLATE.csv).
Neither sees the other's ratings before both are recorded.

## 3. Disagreement resolution

Where the two raters disagree:

1. the disagreement is logged;
2. a third adjudicator (also blind to condition/model) resolves it against the
   rubric;
3. if the disagreement reveals rubric ambiguity, the rubric is clarified **before**
   any confirmatory rating (see §6), and the affected items are re-rated under the
   clarified rubric.

## 4. Inter-rater agreement target

A manual rule may contribute to a confirmatory endpoint **only if** inter-rater
agreement on the validation sample reaches **Cohen's κ ≥ 0.70** (or an equivalent
chance-corrected statistic for the rating scale). κ below 0.70 means the rule is
**not** reliable enough to score confirmatorily; it is either re-specified and
re-validated or reported descriptively only. `0.70` is the single agreement
target; no other manual threshold is set here.

## 5. Prohibition on revealing condition/model identity

At no point in rating — sampling, presentation, rating, adjudication, or
recording — is a rater or adjudicator shown the condition or model. The rating
record schema deliberately has **no** condition or model column. Condition/model
are joined to ratings only **after** rating is complete, by the harness, for
analysis.

## 6. Prohibition on changing the rubric after confirmatory results are visible

The rubric ([`MANUAL_ORACLE_RUBRIC.md`](MANUAL_ORACLE_RUBRIC.md)) is frozen and
content-hashed **before** confirmatory data is scored. It **must not** be changed
after any confirmatory result (effect, contrast, or score) is visible. Rubric
refinement driven by the validation sample happens **before** confirmatory
scoring, never after seeing effects.

## 7. Invalidation after a material rubric change

If the rubric changes materially (a criterion is added, removed, or redefined in a
way that could change a rating):

1. the rubric version is bumped and re-hashed;
2. all confirmatory ratings produced under the previous version are marked
   `EXCL_PROTOCOL_MISMATCH` and dropped from the current frozen analysis set
   (see [`FAILURE_RERUN_POLICY.md`](FAILURE_RERUN_POLICY.md));
3. affected items are re-rated under the new version before they re-enter the
   analysis set;
4. ratings are never silently rescored into a pooled result across rubric
   versions.

## 8. Status

The protocol and rubric are **specified** here. The validation sample, the two-
rater ratings, the κ computation, and any confirmatory manual scoring are **not
performed in this package** and remain open under **`TD-B12`** / gate **G1**.
