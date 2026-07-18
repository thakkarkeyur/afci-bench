# experiments/v2/results — Generated Results (NOT committed)

This directory is the destination for **generated v2 run outputs** (per-run
records, raw transcripts, intermediate aggregates).

**Generated results are intentionally NOT committed to git.** The contents of
this folder are ignored via `.gitignore` (only this `README.md` is tracked), so
results stay out of version control and are instead described by tracked
manifests in `../manifests/` and derived, tracked tables/figures produced by
`../analysis/`.

Rationale:
- Keeps the repository free of large, machine-generated churn.
- Forces every reported number to be reproducible from a manifest + the harness,
  rather than from an opaque committed blob.

Do not `git add -f` files here. If a specific derived artifact must be tracked,
write it to an explicitly tracked location (e.g. under `../analysis/` outputs or
`paper/` for v2), not into this folder.
