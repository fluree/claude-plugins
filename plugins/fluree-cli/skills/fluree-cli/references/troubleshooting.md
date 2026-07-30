# Troubleshooting: when fluree behaves unexpectedly

## First moves

- `"no .fluree/ directory found"` → run `fluree init`. `"no active ledger set"` → `fluree use <ledger>` or pass `-l`.
- A command absent from `--help` → feature-gated build, not a typo. Releases after fluree/db#1571 have a hidden `fluree manifest` command whose `features` array settles it; on 4.1.4 and earlier rely on `--help`.
- Reread the error text: this CLI's errors usually name the fix (`use --force to confirm deletion`, `run 'fluree init'`, `'X' is a graph source, but this build lacks Iceberg/R2RML support`).

## Auto-routing: the silent execution-target switch

If a local `fluree server` is running for the project, data commands silently route **through it** (a stderr notice is the only sign). Consequences: behavior can differ from local execution, and results reflect the server's view. `--direct` forces local execution. **Whenever results look wrong, first establish which path you're on** — rerun with `--direct` and compare before concluding anything.

Known server-routed divergences to recognize:

- **Time travel `--at`** injects a `FROM <ledger@t:N>` by scanning the query for the literal ` where ` substring — keep `WHERE` on the same line as `SELECT` (multi-line bodies after that are fine). An explicit `FROM` and `--at` are mutually exclusive: encode time travel in the `FROM` IRI *or* use `--at`, never both.
- **`--track-policy`** can zero out the very results it diagnoses when server-routed — policy verification is a `--direct` activity.
- **Decimal rendering** may come back in E-notation server-routed; for human-readable score columns, project an integer (`xsd:integer(ROUND(?x * 100))`).

## Stale-index symptoms after drop/recreate

Dropping and recreating a ledger while a server holds it produces *partial* failures: simple counts succeed while complex queries die with CAS `Not found` leaf errors, and `--direct` works — which misleads toward "query bug". It's staleness: reset with the server **down**.

## Import problems

- OOM / machine freeze during `create --from` → the auto memory budget assumed a dedicated machine; rerun with explicit `--memory-budget-mb` and `--parallelism 2-4`. Check whether `FLUREE_IMPORT_THREADS` is set — it silently overrides `--parallelism`.
- Large non-Turtle files load whole-file into memory; convert to `.ttl`/`.nt` for streaming.

## When stuck

Search the embedded docs — they include a troubleshooting tree written for the exact installed version: `fluree docs search "<symptom>"`. On releases after fluree/db#1571, `fluree docs get ai/claude-code` carries the agent-specific rules (a 404 there just means an older binary).
