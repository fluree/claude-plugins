# fluree-cli — Claude Code companion for the Fluree CLI

Teaches Claude Code to drive the [`fluree`](https://github.com/fluree/db) CLI safely and effectively, including against **Fluree AI** (Fluree Solo) stacks.

## What it does

- **A `fluree-cli` skill** that auto-triggers whenever you work with Fluree from the terminal. It carries the *operating doctrine* — not a command reference:
  - **Probe-first:** the installed binary embeds its complete, version-exact docs (`fluree docs`, and the MCP `docs` toolset this plugin auto-connects). The skill makes Claude check them instead of guessing flags from stale training data — so the plugin doesn't go out of date when the CLI changes.
  - **Safety rails:** confirmation-before-destruction (`drop`, `branch drop`), credential hygiene (`.fluree/` tokens, `auth token` vs `config list --reveal`), memory budgets for imports on shared machines, policy-correlation verification.
  - **Fluree AI workflows:** connecting a stack (`remote add` + the device-code login the human approves), scripting tokens, governance via `fluree model`, and what differs between server-routed and `--direct` execution.
- **`/fluree-cli:setup`** — checks/install-guides the binary, verifies docs access, cleans up duplicate MCP registrations, and gitignores `.fluree/`.
- **An MCP server entry** that exposes the binary's embedded docs (`docs_search`, `docs_get`, `docs_examples`, `docs_tree`) to Claude automatically. If `fluree` isn't installed yet, everything else still works and setup walks you through installing.

Requires **fluree ≥ 4.1.3** for the governance (`fluree model`) workflows.

## Install

```text
/plugin marketplace add fluree/claude-plugins
/plugin install fluree-cli@fluree-plugins
```

Then just work — the skill triggers on Fluree tasks — or start with `/fluree-cli:setup`.

## How this stays in sync with the CLI

Everything version-specific lives in the binary (its embedded docs and `--help`), which the skill defers to. The few command paths and flags this plugin's text does hard-code are enumerated in [`contract/cli-facts.json`](contract/cli-facts.json) and validated in CI against the `fluree-cli-manifest.json` release asset that fluree/db publishes — a machine-readable surface description generated from the CLI's own definitions. If a CLI release changes something this plugin says, CI fails here before a user hits it.
