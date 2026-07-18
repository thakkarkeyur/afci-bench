# archive/v1 — v1 Reference Record

This folder is a **reference record**, not a copy of the v1 experiment.

Its purpose is to let AFCI-Bench **study v2** be developed without touching,
depending on, or accidentally regenerating any part of the frozen v0/v1 record.
It contains pointers (git refs, tags, branches, release and DOI identifiers) to
where the v1 record already lives — it does **not** duplicate the large v1
artifacts (run transcripts, aggregated CSVs, figures, tables, or the paper).

## What is here

- [`REFERENCE_MANIFEST.yml`](REFERENCE_MANIFEST.yml) — an annotated inventory
  of the v1 record: the canonical `main` SHA, the v0/v1 tags, the historical
  rerun branches, the GitHub release, the Zenodo DOI, the v1 paper/experiment
  artifacts already tracked on `main`, an explicit immutability statement, and a
  factual list of the known limitations of the v1 execution design.

## What is *not* here (and where to find it)

The actual v1 evidence is **not copied into this folder**. It remains at its
original, immutable locations:

- **v1 paper artifacts** — under `paper/` and `experiments/` on `main`
  (tag `paper-v0`, SHA `2adc8741`).
- **Distributed rerun evidence** — on the `rerun-v1-opus7-*` branches
  (see the manifest for tips and ahead/behind counts). These are strictly
  additive on top of `main`.
- **Published artifact package** — GitHub release
  `ase2026-artifacts-v1`, archived on Zenodo at
  <https://doi.org/10.5281/zenodo.19757261>
  (DOI documented on branch `rerun-v1-opus7-artifacts`).

## Ground rules

1. **v1 is immutable.** Nothing under the refs recorded in the manifest may be
   modified, deleted, renamed, regenerated, or overwritten.
2. **No merges.** No `rerun-v1-*` branch may be merged into `study-v2`.
3. **The paper is not edited.**
4. **No fabricated metadata.** Everything in the manifest is derived from `git`
   and `gh`; anything not derivable is marked `TODO` for human confirmation.

To verify any pointer in the manifest, resolve it directly against git, e.g.:

```sh
git rev-parse paper-v0
git show -s --format='%ci %s' ase2026-artifacts-v1
git log --oneline main..rerun-v1-opus7-artifacts
gh release view ase2026-artifacts-v1
```
