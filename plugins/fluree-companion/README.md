# fluree-companion — Claude Code companion for a Fluree AI stack

Takes you from a bare **Fluree AI** (Fluree Solo) stack URL to a working session — and then keeps the answers coming from *your* stack, at *your* stack's version, instead of from a model's memory of the platform.

Every customer runs their own stack at their own release. So this plugin deliberately carries no platform reference: it carries the choreography for connecting, and the discipline of asking the stack.

## What it does

- **A `fluree-companion` skill** that auto-triggers on stack work. It carries doctrine, not documentation:
  - **The stack is the source of truth.** Probe `/.well-known/fluree.json` for capabilities, auth, and the minimum CLI version; read how-to knowledge from the stack's own docs — its MCP docs tools when present, else the public `/api/docs` index — never from trained recall.
  - **Connection choreography.** Discovery → `fluree remote add` → device-code `fluree auth login`, where the *human* approves at the stack's `/activate` page → optionally registering a Space's MCP server.
  - **Division of labor.** The CLI for data and admin work on ledgers, a Space's MCP server for querying governed data with the Space's tools, the UI for what only it does — and a rule against working around governance.
  - **Safety rails.** `.fluree/` holds live tokens; a `cli.min_version` warning is a stop-and-upgrade signal; destructive operations against shared stack data get named confirmation.
  - **Version awareness.** What you learn from one stack is a fact about that stack at that release, and doesn't travel.
- **`/fluree-companion:connect`** — the guided run: binary check, discovery with a min-CLI verdict, remote + human-approved login, `fluree list` verification, optional Space MCP registration, and a knowledge-access check that has to actually read something before reporting success.

Pairs with **[fluree-cli](../fluree-cli/README.md)**, which covers driving the `fluree` binary itself (flags, local ledgers, imports, policy authoring). Rule of thumb: *this* plugin when the subject is a stack, that one when the subject is the CLI. Both installed is the intended setup.

## Install

```text
/plugin marketplace add fluree/claude-plugins
/plugin install fluree-companion@fluree-plugins
```

Then run `/fluree-companion:connect`, or just say what you're trying to do with your stack.

## How this stays in sync with a stack

Everything version-specific lives on the stack and is fetched at use time. The handful of addresses the choreography can't avoid naming — discovery and OAuth metadata paths, the Space MCP endpoint, the docs index, and the doc slugs the playbooks point at — are enumerated in [`contract/stack-facts.json`](contract/stack-facts.json) and checked in CI by [`scripts/check-stack-facts.mjs`](../../scripts/check-stack-facts.mjs):

- **Router paths** are resolved against solo's generated endpoint manifest (`src/contracts/generated/router/endpoint-manifest.json`), which is produced from the router's own route table. A path the plugin names that no longer exists is a CI failure here, not a 404 for a user. The check also asserts each path's **auth posture** matches what the prose claims — the pre-auth discovery probe stops being pre-auth the moment that changes.
- **UI-Lambda paths** (`/api/docs`, `/activate`, `/docs/…`) aren't in that manifest by design, since the Next.js UI serves them. What the manifest *can* falsify is the ownership split the prose teaches, so the checker fails if one of them starts resolving in the router.
- **Doc slugs** are checked against a live stack's `/api/docs` index when `STACK_ORIGIN` is set. Slugs marked `public` must be listed there; slugs marked `in-app` must not — that inversion catches the day a page is promoted into the public set and the plugin should be handing out a fetchable URL instead of a signed-in one.
- **Stack MCP tool names** (`docs_search` and friends) are recorded but not validated — they have no published producer artifact yet, which is exactly why the skill probes for them rather than assuming them.

The choreography also names `fluree` commands, so this plugin carries its own
[`contract/cli-facts.json`](contract/cli-facts.json) — checked against fluree/db's
`fluree-cli-manifest.json` release asset by the same checker the `fluree-cli` plugin uses. A
plugin that names a command is on the hook for it existing, whichever plugin it is.
