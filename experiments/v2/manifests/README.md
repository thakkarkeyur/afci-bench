# experiments/v2/manifests — Run Manifests (v2)

**Manifests** that pin down exactly what each v2 run/batch executed: the task
and condition identities, model and version, environment, git base SHA, seeds/
parameters, and the schema versions in effect.

A manifest is the provenance record for a batch of results — it should be
sufficient, together with the harness and the pinned base, to explain how a
given result set was produced. Manifests are tracked; the bulk run outputs they
describe are not (see `../results/`).

Add run manifests here. Derive base SHAs and identifiers from git/tooling — do
not invent provenance.
