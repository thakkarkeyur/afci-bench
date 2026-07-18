# experiments/v2/analysis — Analysis & Aggregation (v2)

The v2 **analysis code**: scripts that turn recorded run outputs into the
metrics, tables, and figures reported for study v2.

Every published number must be produced by a script that lives here (v1 had
figures/tables with no generator script, and a degenerate `layer_jaccard`
constant of 1.0 reported as a metric — see
`archive/v1/REFERENCE_MANIFEST.yml`, limitation `L5`). v2 analysis should
prioritize direct measures (conformance, task acceptance) over indirect churn/
drift proxies.

Add analysis scripts here. They read from `../results/` (gitignored generated
outputs) and write derived tables/figures to tracked locations you designate.
Do not commit raw generated run outputs.
