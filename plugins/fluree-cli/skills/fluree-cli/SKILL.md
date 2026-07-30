---
name: fluree-cli
description: "Drive the fluree CLI safely and effectively. Use whenever the user works with Fluree from the command line — running or composing fluree commands (init, create, insert, query, model, remote, auth, iceberg, branch, export), connecting to or building apps against a Fluree AI / Fluree Solo stack, debugging Fluree queries or policies from a terminal, importing data into Fluree, or asking how to do something with a Fluree database from a terminal. Also trigger when a pasted prompt or README references the fluree CLI, fluree remote add, fluree auth login, or fluree model commands."
---

# Driving the fluree CLI

You are working with `fluree`, the Fluree database CLI. It is local-first (ledgers live under a `.fluree/` project directory) and speaks to remote deployments — including Fluree AI (also called Fluree Solo) stacks — via named remotes. This skill is the **operating doctrine**; it deliberately contains almost no command reference, because the binary carries its own.

One check before steering anyone CLI-ward: if the project has no `.fluree/` directory and no `fluree` binary on PATH, the user may be working SDK-only (`@fluree/client` against a Fluree AI stack) — in that case answer in SDK/platform terms and offer the CLI only if it would genuinely help.

## Rule 1 — the binary is the reference; probe, don't recall

Your trained knowledge of this CLI is stale by construction. The installed binary embeds its complete, version-exact documentation:

- **MCP tools** (if the `fluree-docs` server is connected): `docs_search`, `docs_get`, `docs_examples`, `docs_tree`.
- **Always available as commands**: `fluree docs search "<topic>"`, `fluree docs get <path>`, `fluree <cmd> --help`.
- **Start here for agent workflows** (releases after fluree/db#1571): `fluree docs get ai/claude-code` — the binary's own operating guide for AI agents, authoritative for the installed version's *command surface*. If that path 404s, your binary predates the page; use `fluree docs search "AI agents"` (the bare word "agent" ranks HTTP User-Agent docs first) and rely on the rules below.

Before composing any nontrivial invocation, check the docs or `--help`. Never assert a flag from memory. If a command seems missing from `--help` (`validate`, `cluster`), it is usually a build without that cargo feature, not a user error — the hidden `fluree manifest` command prints a JSON surface description including a `features` array that settles it (recent releases only — if the binary doesn't have it, rely on `--help`).

This project's workflows need **fluree ≥ 4.1.4** (`fluree --version`): `fluree auth token` ships in 4.1.4 and the `fluree model` governance family in 4.1.3. If the binary is missing or old, run `/fluree-cli:setup`.

## Rule 2 — safety rails (stable across versions)

1. **Destructive commands get explicit user confirmation, with the target named.** `fluree drop --force` is a hard, unrecoverable delete. `fluree branch drop` has *no* confirmation flag, permanently deletes leaf-branch storage, and cascades into retracted ancestors — and `main` has no special protection.
2. **Never drop/recreate a ledger under a running server.** The server keeps stale index pointers and fails *partially* (spot-checks pass, other queries die). Stop the server first.
3. **Credentials:** `.fluree/` holds live access and refresh tokens after `fluree auth login` — ensure it is gitignored before ever running `fluree init` inside a repo. To script a token use `fluree auth token` (prints exactly the access token, never the refresh token). **Treat `fluree config list` output as secret: through v4.1.4 it dumps `auth.token` and `refresh_token` in plaintext.** Redaction (with a `--reveal` opt-out) lands in the first release after fluree/db#1571; until you have verified `--reveal` exists on the installed binary, never paste `config list` output into logs, commits, issues, or chat.
4. **Imports on shared machines:** the auto memory budget assumes it owns the box (80% of RAM) and has OOM'd real machines. On anything running an IDE/Docker/browser, pass explicit `--memory-budget-mb` and `--parallelism 2`–`4` to `fluree create --from`.
5. **Policy work:** correlation lives in a single `where`; unknown keys in `f:query` are silently ignored, and a policy that never constrains `?$this` silently allows everything. Verify with `--track-policy` on *direct/local* execution only. Details: `references/policy.md`.

## Rule 3 — machine-readable output where it exists

Prefer structured output when parsing: `query` and `multi-query` take `--format json` (`query --format ndjson --envelope` adds a self-describing head/rows/end wrapper — `--envelope` pairs with ndjson only); `graph list`, `branch diff`, `branch revert --preview`, and the four `docs` subcommands take `--json`. `list`, `info`, and `show` are human-formatted only — don't scrape them; query instead. Errors are human text; the exit code (0/1/2-usage) is the only machine signal.

## Rule 4 — remote work (Fluree AI / Solo stacks)

`--remote <name>` takes a configured **alias**, never a URL. The full connection choreography — `remote add`, the device-code login where the *human* approves in a browser, token scripting, and what differs between local and server-routed execution — is in `references/remote-fluree-ai.md`. The one thing to never forget: **`fluree auth login` blocks on the user approving a device code at the stack's `/activate` page** — run it, tell the user to approve, and verify with `fluree auth status` before continuing.

## Common flows

Step-by-step recipes (create→insert→query, bulk import, branch/merge, Iceberg mapping, app-building against a Fluree AI stack): `references/workflows.md`. Debugging divergences (server-routed vs `--direct`, time-travel formatting rules, auto-routing): `references/troubleshooting.md`.
