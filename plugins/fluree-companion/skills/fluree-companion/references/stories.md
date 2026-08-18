# Playbook skeletons

Each entry is a **route**, not a procedure: the goal, the stack doc that carries the actual steps, and the entry point to start from. Fetch the doc (see `stack-knowledge.md`) before doing any of it — the stack's copy matches the stack, and this file cannot.

These routes are **paved paths** (SKILL.md Rule 6): their sequences mint the provenance and UI visibility that equivalent-looking raw API/CLI assemblies skip. Deviating is sometimes necessary — but it's a thing to surface to the user, not a shortcut to take silently.

Slugs below are `category/slug` on the stack's own docs: `https://<stack>/api/docs/<slug>` for raw markdown, `https://<stack>/docs/<slug>` signed-in.

---

## Get files into the knowledge graph

**Goal:** documents or structured files land in a dataset as queryable graph data.
**Knowledge:** `how-to/upload-and-import-data`, then `how-to/map-files-into-a-knowledge-graph` for the extraction/mapping half. `concepts/how-data-gets-in` explains why the paths have different size ceilings.
**Entry points:** the UI's Upload tab for the interactive path; `fluree create --from` for a bulk local import (mind the memory budget on a shared machine — the `fluree-cli` skill's rail); the negotiated upload handshake for large archives, whose modes the stack advertises in `/.well-known/fluree.json` under `import`.

## Publish a local ledger to the stack

**Goal:** work built locally with the CLI becomes a dataset on the stack.
**Knowledge:** `how-to/publish-a-ledger-with-the-cli`. `how-to/connect-a-remote-fluree` covers the other direction — mounting someone else's Fluree as read-only datasets.
**Entry points:** `fluree publish`, against a remote already connected per `connect.md`.

## Expose a Space over MCP

**Goal:** a Space's governed data and tools become an MCP server that Claude Code (or Claude Desktop, or claude.ai) can use.
**Knowledge:** `how-to/connect-external-mcp-client` — if the public `/api/docs` fetch 404s (older stacks withhold this page), send the user to the signed-in `https://<stack>/docs/how-to/connect-external-mcp-client`. `concepts/spaces-tasks-and-agents` for what a Space is.
**Entry points:** the Space's **MCP** tab (owner-only: enable access, choose exposed tools, read off the server URL and `spaceId`), then `claude mcp add --transport http fluree-space "https://<stack>/v1/mcp?space=<spaceId>"`.

## Connect an Iceberg catalog

**Goal:** query Iceberg tables as graph data without copying them.
**Knowledge:** `how-to/connect-an-iceberg-catalog`, then `how-to/create-a-dataset-from-iceberg`. `concepts/iceberg-r2rml-mapping` explains what the mapping actually does.
**Entry points:** the `fluree iceberg` command family (`map`, `list`, `info`) — check the installed binary's `--help` or its embedded docs for flags, per the `fluree-cli` skill.

## Govern a graph

**Goal:** policies and shapes that constrain what a dataset accepts and who can read it.
**Knowledge:** `how-to/access-policies` and `concepts/policies-and-data-governance`.
**Entry points:** the `fluree model` family (it compiles to ordinary SHACL/policy data in the ledger — read back what's enforced with `model entity show` / `model access show`). Verify policy behaviour on **local/direct** execution; the `fluree-cli` skill's policy reference explains why server-routed verification misleads.

## Build an app against the stack

**Goal:** application code talking to the stack's HTTP API.
**Knowledge:** `reference/building-apps` is the recipe and is deliberately inside the public doc set, so it is fetchable with no credentials at all; `reference/api` is the endpoint reference; `reference/cli` covers the CLI-side surface.
**Entry points:** the stack origin and a Space id are the only instance-specific inputs; everything else comes from those pages.
