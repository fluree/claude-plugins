# Working against a Fluree AI (Solo) stack

The remote model: the CLI stores named remotes in `.fluree/config.toml`; every data command takes `--remote <alias>` (or the compound positional `alias/ledger`). There are **no environment-variable credentials** — tokens live in the remote config.

## Connect

```bash
fluree init                                        # once per project directory
fluree remote add mystack https://<stack>/v1/fluree
fluree auth login --remote mystack
```

- The `/v1/fluree`-suffixed URL is the robust form: discovery of `/.well-known/fluree.json` ignores the input path, and if discovery is unreachable a `/fluree`-suffixed input is stored as-is.
- `remote add` may warn that the stack expects a newer CLI (`cli.min_version` discovery) — resolve that before continuing; commands the stack's docs teach may not exist in an older binary.
- **`auth login` needs the human.** It prints a short device code and opens the stack's `/activate` page; the *user* clicks approve in their browser (one click if already signed in) while the CLI polls. Run the command, immediately tell the user to approve the code, and only continue after `fluree auth status --remote mystack` shows a configured token.
- Manual-token alternative: `fluree remote add mystack <url> --token @token.txt` (or `fluree auth login --remote mystack --token @-` from stdin).

## Scripting a token

`fluree auth token --remote mystack` prints exactly the access token — compose it into `.env` files or `curl` headers. It never prints the refresh token. Do not harvest tokens any other way.

## What the CLI sees vs what an app sees

The CLI rides the **user's** credential and may see more than an app token would (`fluree list --remote mystack` can show datasets a Space deliberately excludes). That difference is governance working, not a bug — never work around a missing dataset; ask the user to grant access in the stack's UI.

## Governance from the CLI (fluree ≥ 4.1.3; the full flow here needs 4.1.4 for `auth token`)

`fluree model` is a compiler, not a separate config system: `model entity define` transacts a SHACL shape, `model access enable` transacts policy data — into the ledger, as ordinary queryable data. Read back what is actually enforced with `model entity show` / `model access show`. Anything the CLI grammar can't express is authored directly as SHACL/policy JSON-LD via a normal `fluree insert`/`update` — enforcement is identical. For exact flags: `fluree model --help` or `fluree docs search "model entity define"`.

## Query-side alternative: connect Claude Code to the stack's own MCP server

For read/analysis work a Space can expose its data directly as MCP tools (`sparql_query`, `get_data_model`, …) — no CLI required. The stack's Data Admin **MCP** tab documents Claude Desktop; for **Claude Code** the same endpoint connects with:

```bash
claude mcp add --transport http fluree-space "https://<stack>/v1/mcp?space=<spaceId>"
```

Claude Code discovers the OAuth configuration automatically (the stack serves RFC 8414 metadata, including the device grant) and prompts for login. The MCP server URL and spaceId come from the Space's MCP tab; MCP access must be enabled there by the Space owner first. Use this when the user wants to *query* a Space's data; use the CLI when they need to *administer* it (schema, access, imports, branches).

## Server-routed execution differs from local

Behind a stack (or a detected local server — see auto-routing in `troubleshooting.md`), a few behaviors differ from `--direct` local execution. Notables: `--track-policy` is unreliable server-routed (verify policies locally); decimal rendering can differ; per-request options generally travel as HTTP headers on the stack's own API rather than CLI flags. When output looks wrong server-routed, reproduce with `--direct` before concluding anything.
