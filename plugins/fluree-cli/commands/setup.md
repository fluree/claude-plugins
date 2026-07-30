---
description: Check/install the fluree CLI, wire up its docs MCP server, and verify the connection
---

Set up this machine for fluree CLI work. Follow these steps in order, reporting progress:

1. **Check the binary**: run `fluree --version`. If missing, offer the user the install commands (their choice, don't run package managers unprompted):
   - macOS: `brew install fluree/tap/fluree`
   - macOS/Linux: `curl --proto '=https' --tlsv1.2 -LsSf https://github.com/fluree/db/releases/latest/download/fluree-db-cli-installer.sh | sh`
   - Windows: `irm https://github.com/fluree/db/releases/latest/download/fluree-db-cli-installer.ps1 | iex`
2. **Check the version**: this plugin's workflows need **4.1.4 or newer** (`fluree auth token` ships in 4.1.4; the `fluree model` family in 4.1.3). If older, recommend upgrading via the user's original install method before continuing.
3. **Check docs access**: if the `fluree-docs` MCP tools (`docs_search` etc.) are available in this session, verify with one `docs_search` probe (e.g. "query"). If the plugin's MCP server isn't connected (it registers automatically when the binary exists — a restart may be needed after installing), note that `fluree docs search` works identically as a plain command.
   - If the user previously ran `fluree mcp init --ide claude-code`, they may have a duplicate user-level `fluree` MCP registration alongside this plugin's `fluree-docs` server. That's harmless but noisy; offer to remove the user-level one (`claude mcp remove fluree`) since the plugin now manages it.
4. **Project hygiene**: if working inside a git repo where `fluree init` will be run, confirm `.gitignore` covers `.fluree/` (it will contain live tokens after `fluree auth login`). Add it if missing.
5. **Remote (optional)**: if the user has a Fluree AI stack to connect, follow the connection choreography in the fluree-cli skill's `references/remote-fluree-ai.md` — including telling the user to approve the device code at the stack's `/activate` page.

Finish with a one-line status: binary version, docs access (MCP or CLI), and whether a remote is configured (`fluree remote list`).
