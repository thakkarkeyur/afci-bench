# experiments/v2/schemas — Data Schemas (v2)

Machine-readable **schemas** for every structured artifact the v2 pipeline
produces or consumes: task definitions, condition specs, per-run records,
oracle verdicts, guard reports, and aggregated result rows.

Schemas make the v2 record self-describing and validatable, so downstream
analysis cannot silently drift from the data contract. Prefer an explicit
format (e.g. JSON Schema) with versioning.

Add schema files here. Keep them in step with `../manifests/` and `../analysis/`.
