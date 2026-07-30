# Policy: the correlation rule and how to verify it

Fluree access policies attach an `f:query` whose `where` decides, per flake, whether the policy's action is allowed. Two facts make this dangerous to write casually:

1. **Unknown keys are silently ignored.** There is exactly one clause key — `where`. Anything else (historically a `$where` second-clause pattern circulated in older docs) is dropped without error.
2. **An uncorrelated policy allows everything.** If the `where` never constrains `?$this` (the entity/flake under evaluation), it matches every flake — a policy written to *restrict* silently *allows*.

## The correct shape

A single `where` — an object, or an array of patterns joined by **shared plain variables** — that includes `?$this`:

```json
"f:query": "{\"where\": [
  {\"@id\": \"?$identity\", \"ex:user\": {\"@id\": \"?user\"}},
  {\"@id\": \"?$this\",     \"ex:owner\": {\"@id\": \"?user\"}}
]}"
```

`?$identity` and `?$this` are the reserved injected bindings; intermediates are plain variables (`?user`, not `?$user`).

## Verify before trusting

```bash
fluree query mydb --direct --as <identity-IRI> --policy-file p.json --track-policy --sparql '...'
```

`--track-policy` prints `policy <allowed>/<evaluated>` — an uncorrelated policy shows itself immediately (everything allowed). Two sharp edges: `--as`/`--policy-class` need **full IRIs** (prefixed names fail to resolve), and `--track-policy` is only reliable on **direct/local** execution — server-routed it can distort the very result it is diagnosing.

For the full worked examples, read the binary's own cookbook: `fluree docs get guides/cookbook-policies` — **with one crucial caveat**: in binaries up to and including v4.1.4, the embedded cookbook's own worked examples (salary-restriction, owner-only, multi-tenant, manager-sees-reports) use the broken `$where` second-clause form this page warns about, and they silently allow everything (live-verified: `policy 2/2` allowed vs the corrected form's `1/2`). The corrected cookbook ships in releases after fluree/db#1571. Until your binary has it, trust THIS page's shape over the cookbook's examples, and always verify with `--track-policy`.
