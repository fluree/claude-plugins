# Common fluree workflows

Recipes for the flows users ask for most. Flags shown are the stable spine — verify anything beyond them with `--help`/`fluree docs` (Rule 1).

## Local create → insert → query

```bash
fluree init                      # creates .fluree/ (required before anything)
fluree create mydb               # new ledger; becomes active
fluree insert 'ex:alice a ex:Person ; ex:name "Alice" .'
fluree query 'SELECT ?name WHERE { ?s <http://example.org/name> ?name }'
fluree query --format json --sparql '...'     # machine-readable
fluree query --explain --sparql '...'         # plan without executing
```

`fluree use <ledger>` switches the active ledger; most commands also take `-l/--ledger`.

## Bulk import

```bash
fluree create mydb --from data.ttl --memory-budget-mb 4096 --parallelism 4
```

- Always explicit budget + parallelism on a shared machine (SKILL Rule 2.4).
- `.ttl`/`.nt` stream; other formats load whole-file — prefer Turtle/N-Triples for large data. `.gz`/`.zst` are transparent.
- An import directory must contain only the intended files (`create --from <dir>` will interpret stray `.csv` files as Neo4j-convention CSV).

## CSV → graph (`LOAD CSV` analog)

`fluree load` streams a CSV through a per-row Cypher or JSON-LD template in batched transactions. Its `--help` is unusually rich (cell typing, null semantics, `UNWIND $batch AS row` shape) — read it before writing the template.

## Branch / merge

```bash
fluree branch create dev --at t:42
fluree branch diff main dev          # read-only preview: ahead/behind, conflicts, FF eligibility
fluree branch merge dev
fluree branch revert t:42 --preview  # undo-commit without history rewrite; preview first
```

`branch drop` is the sharpest destructive edge in the CLI — see SKILL Rule 2.1.

## Iceberg → queryable graph

```bash
fluree iceberg map --catalog-uri <uri> --table ns.table ...   # creates a graph source
fluree iceberg list
fluree query <graph-source> --sparql '...'
```

Auth flags (`--oauth2-*`, `--auth-bearer`) put secrets in argv — prefer having the user run these, and never echo the invocation back into durable text. `iceberg map`/`list`/`info`/`drop` all take `--remote`.

## Building an app against a Fluree AI stack

The stack itself serves the authoritative recipe, per-stack and unauthenticated — fetch `https://<stack>/api/docs/reference/building-apps` and follow it (it covers the app template, `@fluree/client`, Space grants, and publishing). Use this skill's rails on top of it; where the two conflict, the stack's recipe wins for platform behavior and the binary's docs win for CLI behavior.

## Moving a local ledger to a stack

```bash
fluree publish mystack mydb     # create-on-remote + push + set upstream
# or archive-based:
fluree export mydb -o mydb.flpack && fluree create mydb --remote mystack --from mydb.flpack
```

`export` refuses to write a binary `.flpack` to a TTY — always `-o <file>`.
