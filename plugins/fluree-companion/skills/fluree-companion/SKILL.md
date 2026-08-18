---
name: fluree-companion
description: "Work against a deployed Fluree AI (Fluree Solo) stack — connect Claude Code to it, then let the stack itself teach you how to use it. Use whenever someone has a Fluree AI / Solo stack URL and wants to connect, register a Space's MCP server, or asks how to do something on their stack (upload and extract documents, expose a Space over MCP, connect an Iceberg catalog, govern a graph, build an app against it). Also trigger when a stack's /.well-known/fluree.json, /api/docs, an /activate device-code page, or a https://<stack>/v1/mcp?space=… URL turns up in the conversation."
---

# Working against a Fluree AI stack

A Fluree AI (Fluree Solo) stack is a **deployment** — one customer's AWS stack, running one release, with its own datasets, Spaces, policies, and capabilities. This skill is the choreography for connecting to one and then working *through* it. It deliberately carries almost no platform reference, because the stack serves its own.

The companion to this one is the **`fluree-cli`** skill, which covers driving the `fluree` binary itself. Reach for that when the work is CLI mechanics (flags, local ledgers, imports, policy authoring); reach for this one when the work is *a stack* (connecting, what this stack can do, where its knowledge lives).

## Rule 1 — the stack is the source of truth; probe, don't recall

Never answer a question about the platform from trained knowledge. Two stacks on different releases genuinely differ, and the stack will tell you which one you're on:

- **Capabilities and compatibility:** `GET /.well-known/fluree.json` — unauthenticated, so it works before anything is configured. It carries `api_base_url`, an `auth` block (OIDC device flow or token), `capabilities`, `import` modes, `cli.min_version`, and a `companion` pointer.
- **How-to knowledge:** if the stack's docs MCP tools (`docs_search`, `docs_get`, `docs_tree`, `docs_examples`) are connected in this session, use them — they are pinned to the release the stack is running. **Probe for them; do not assume them.** They are new, and a stack older than that release won't have them. When they're absent, fall back to fetching `GET /api/docs` (a public llms.txt-style index) and then the `/api/docs/{category}/{slug}` page it points at. Mechanics: `references/stack-knowledge.md`.
- **The exact version** is deliberately *not* in the public discovery document; it lives behind the authenticated `GET /v1/fluree/system/version`. Don't fingerprint a stack you aren't signed in to.

If the docs and your memory disagree, the docs are right. If the docs don't cover it, say so rather than filling the gap from training data.

## Rule 2 — connection choreography, and the human approves

The order matters, and one step is not yours to take:

1. **Discover** — fetch `/.well-known/fluree.json`. Report what the stack advertises, and check `cli.min_version` against the local `fluree --version`.
2. **`fluree remote add <alias> https://<stack>/v1/fluree`** — remotes are named aliases; every later command takes `--remote <alias>`, never a URL.
3. **`fluree auth login --remote <alias>`** — this prints a device code and blocks. **The human approves it in a browser at the stack's `/activate` page.** Never skip it, never try to automate it, never go hunting for a token to shortcut it. Run the command, tell the user to approve, then verify with `fluree auth status --remote <alias>`.
4. **Optionally register the Space MCP server** — `claude mcp add --transport http fluree-space "https://<stack>/v1/mcp?space=<spaceId>"`. Claude Code discovers the OAuth configuration from the stack (RFC 9728 + RFC 8414) and prompts for sign-in; the Space owner must have enabled MCP access first.

Full walkthrough including the failure modes and what each one actually means: `references/connect.md`. The guided version is `/fluree-companion:connect`.

## Rule 3 — division of labor: CLI, Space MCP, UI

Pick the surface by what the user is trying to do, and say which one you're using:

| Surface | Use it for | Don't use it for |
| --- | --- | --- |
| **`fluree` CLI** (`--remote`) | Data and admin work against ledgers: create, insert/update, query, export, branches, imports, Iceberg mapping, governance via `fluree model` | Anything a Space governs — the CLI rides the *user's* credential and sees more than a Space deliberately exposes |
| **Space MCP** (`/v1/mcp?space=…`) | Querying and analysing a Space's governed data with the Space's own tools and agents | Administering the stack; the exposed tool set is the owner's selection, intentionally narrower |
| **The UI** | What only it does: enabling MCP access on a Space, granting dataset access, reviewing identity matches, the visual review gates in extraction workflows | Anything scriptable — if the CLI or API can do it, prefer that so the user gets a repeatable artifact |

When something the user wants is missing from the CLI (a dataset that doesn't appear in `fluree list --remote`, a tool that isn't exposed over MCP), that is governance working. Ask the user to grant it in the UI; never work around it.

## Rule 4 — safety rails

1. **`.fluree/` holds live tokens** after `fluree auth login` — access *and* refresh. Confirm it is gitignored before running `fluree init` inside a repo. To script a token, `fluree auth token --remote <alias>` prints exactly the access token and nothing else.
2. **A `cli.min_version` warning is a stop-and-upgrade signal, not a nag.** If the stack asks for a newer CLI than the one installed, stop and resolve it — the commands the stack's own docs teach may not exist in the older binary, and the failure shows up later as a confusing flag error. `/fluree-cli:setup` handles the upgrade (including the common case where a new binary is shadowed on PATH by an old one).
3. **Destructive operations against a stack get explicit confirmation with the target named** — dropping a dataset, dropping a branch, or overwriting an import destination affects shared, multi-user data, not a local scratch ledger. There is no undo.
4. **Don't paste stack-identifying secrets into the session** — bearer tokens, `config list` output, or `.env` files. Take the stack *origin* from the user; take the credentials from the device flow.

## Rule 5 — knowledge is per-stack, and doesn't travel

The stack's docs *are* its version. Whatever you learn from one stack — a capability, an endpoint, a doc page, whether a tool exists — is a fact about **that** stack at **that** release. Don't carry it to another stack, don't cache it across a version bump, and when the user has more than one stack configured, name which one you probed. Re-probe rather than remember.

## Rule 6 — paved paths: build what the product can see

The API and CLI will let you assemble almost any outcome from raw
primitives — create a ledger, insert rows, trigger an execution directly.
Resist that. Most product stories have a **paved path** whose steps mint
the connective tissue the raw primitives skip: a file that goes through
the documents pipeline shows up in the Uploads surface, carries its source
document into the extraction output, and gets its entities annotated
against the identity graph; a raw `fluree insert` into a fresh ledger
produces none of that, and the user opens their workspace to find data
they cannot trace and files they cannot see.

So, in order:

1. **If the task matches a story, follow the story.** Check
   `references/stories.md` for the route, then fetch the how-to it points
   at and follow that sequence end-to-end — the ordering is usually the
   point (e.g. identity mappings exist BEFORE extraction runs, so the run
   can ground against them).
2. **Reach for raw primitives only when no story fits**, and say so:
   tell the user you're off the paved path and what that costs (results
   may not surface in the product UI; provenance links won't exist).
   Working-but-invisible is a failure mode, not a success.
3. **Never substitute the platform's source code for its docs.** If you
   can see a Fluree repo in your working directory, its schemas and
   handlers describe what the API *accepts* — not what the product
   *intends*. The docs are the steering surface; the code is not.

The test to apply before calling a task done: *if the user opens the UI
right now, can they see what was just built — the files, the sources, the
links?* If not, the task is not done the way the product means it.

## Playbooks

Short skeletons for the common stories — upload and extract, expose a Space over MCP, connect an Iceberg catalog, build an app — each pointing at the stack doc that actually carries the procedure: `references/stories.md`. They are pointers by design; the stack's copy is the one that matches the stack.
