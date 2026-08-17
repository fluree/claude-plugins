---
description: Connect this session to a Fluree AI (Solo) stack — discovery, device-code login, optional Space MCP, and a knowledge-access check
---

Take a session from "I have a stack URL" to "I can work against that stack." Follow these steps in order, reporting progress as you go. Stop and ask if a step's verification doesn't pass — don't chain past a failure.

The choreography and its failure modes are in the `fluree-companion` skill's `references/connect.md`; this command is the guided run of it.

1. **Binary check**: run `fluree --version`. If it's missing or you need to upgrade, hand that off to **`/fluree-cli:setup`** (the `fluree-cli` plugin, same marketplace) rather than improvising — it also covers the common case where a new binary is shadowed on PATH by an old one. If that plugin isn't installed, point the user at `https://github.com/fluree/db/releases/latest` and stop here.

2. **Get the stack origin**: ask for it if it wasn't given — just the origin, e.g. `https://my-stack.example.com`, no path. If the user only has a UI URL, the origin is its scheme + host.

3. **Discover**: fetch `<origin>/.well-known/fluree.json`. Report back, in plain terms:
   - what the stack advertises (`capabilities`, `import` modes, `api_base_url`),
   - the auth type (`oidc_device` → the device flow below; `token` → the user must supply a token),
   - and an explicit **min-CLI verdict**: `cli.min_version` vs the version from step 1, stated as OK or "upgrade needed before continuing."
   A 404 here means the stack predates the discovery endpoint — you can still connect, but do not infer capabilities you couldn't read.

4. **Project hygiene**: if this is a git repo where `fluree init` will run, confirm `.gitignore` covers `.fluree/` (it holds live access and refresh tokens after login). Add it if missing.

5. **Add the remote**: `fluree init` if needed, then `fluree remote add <alias> <origin>/v1/fluree`. Let the user pick the alias, or propose one from the host. Surface any min-version warning the command prints.

6. **Log in — the human approves**: run `fluree auth login --remote <alias>`. It prints a device code and blocks. **Immediately tell the user to approve it at the stack's `/activate` page in their browser**, and wait for them. Never automate or bypass this. Then verify: `fluree auth status --remote <alias>` and `fluree list --remote <alias>`. An empty dataset list with healthy auth is fine — say so rather than treating it as a failure.

7. **Offer Space MCP registration** (optional — ask, don't assume): if the user wants to query a Space's governed data directly, they need the Space's `spaceId` from its **MCP** tab, where an owner must first have enabled MCP access. Then:
   `claude mcp add --transport http fluree-space "https://<stack>/v1/mcp?space=<spaceId>"`
   Claude Code discovers the OAuth configuration from the stack and prompts for sign-in.

8. **Verify knowledge access**: confirm you can read this stack's own docs, since that's the point of connecting. Probe for the stack's docs MCP tools (`docs_search` and friends) and use one if present; otherwise fetch `<origin>/api/docs` and confirm the index parses. Report which of the two you got — do not report success without having actually read something.

Finish with a one-line status: stack origin, CLI version vs `cli.min_version`, remote alias and auth state, Space MCP registered or not, and the live knowledge path (stack docs tools, or `/api/docs` over HTTP).
