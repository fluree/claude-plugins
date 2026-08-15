# Connecting to a stack, end to end

Four steps, in order. Each one is verifiable before you move on — don't chain them blind.

## 1. Discover — `GET /.well-known/fluree.json`

Public and unauthenticated, so it is the right first move on a bare URL:

```bash
curl -fsS https://<stack>/.well-known/fluree.json
```

What's in it, and what each field is *for*:

| Field | Why you care |
| --- | --- |
| `api_base_url` | Where the data API lives — `/v1/fluree` by default, absolute on some deployments |
| `auth` | `type: "oidc_device"` (issuer, client_id, scopes → the device flow below) or `type: "token"` (no OIDC; the user supplies a token) |
| `capabilities` | What this stack has switched on |
| `import` | Which upload handshake the CLI should negotiate, plus size ceilings |
| `cli.min_version` | The oldest CLI this stack expects to behave correctly |
| `companion` | Which plugin marketplace and plugins the stack points its users at |

Report this back to the user in plain terms — it is the first thing that tells them their stack is reachable and what shape it's in. Compare `cli.min_version` against `fluree --version` now, not later.

**If it fails:** a non-JSON body usually means you hit a CDN error page — check the origin, and give it no path (discovery ignores paths). A 404 means the stack predates the discovery endpoint; you can still connect, you just have no capability advertisement, so don't infer one.

## 2. Add the remote

```bash
fluree init                                        # once per project directory
fluree remote add mystack https://<stack>/v1/fluree
```

- The `/v1/fluree` suffix is the robust form: discovery ignores the input path, and if discovery is unreachable the suffixed URL is stored as-is and still works.
- Remotes are **named aliases**. Every later command takes `--remote mystack` (or the compound positional `mystack/ledger`) — never a URL.
- `remote add` may warn that the stack expects a newer CLI. Treat that as a stop: resolve it before continuing (`/fluree-cli:setup`), because the commands the stack's docs teach may not exist in the older binary.

## 3. Log in — the human approves

```bash
fluree auth login --remote mystack
```

This prints a short device code and opens the stack's `/activate` page. **The user clicks Approve in their browser** (one click if they're already signed in) while the CLI polls. Your job is to run the command, immediately tell the user to go approve the code, and wait.

Do not skip this, do not try to drive the browser, and do not go looking for a token that would let you bypass it. Verify before continuing:

```bash
fluree auth status --remote mystack
fluree list --remote mystack
```

**If it fails:** an expired code just needs a re-run. `auth.type: "token"` in step 1 means the stack has no OIDC configured — use the manual path (`fluree remote add … --token @token.txt`, or `fluree auth login --remote mystack --token @-`) with a token the user supplies. An empty `fluree list` with a healthy `auth status` is not a failure: the stack may genuinely have no datasets yet, or this user's access may not include them.

## 4. Optional — register the Space MCP server

A **Space** can expose its governed data and agent tools as an MCP server. For Claude Code:

```bash
claude mcp add --transport http fluree-space "https://<stack>/v1/mcp?space=<spaceId>"
```

Claude Code discovers the OAuth configuration from the stack itself (`/.well-known/oauth-protected-resource`, RFC 9728, pointing at `/.well-known/oauth-authorization-server`, RFC 8414) and prompts for sign-in. Each user connects as themselves and sees only what they already have access to.

Two prerequisites live in the UI and are owner-only: **MCP access must be enabled on the Space**, and the owner chooses which tools are exposed. The Space's **MCP** tab is where the server URL, the `spaceId`, and the OAuth discovery URL are displayed — that tab is also where the user goes if the connection 401s.

The full page for this is `how-to/connect-external-mcp-client`. It sits outside the stack's *public* doc set today, so link the user to `https://<stack>/docs/how-to/connect-external-mcp-client` in the signed-in UI rather than trying to fetch it from `/api/docs`.

## 5. Verify knowledge access

Before declaring the session connected, confirm you can actually read this stack's knowledge — that is the whole point of connecting. Probe for the stack's docs tools; if they're absent, fetch `/api/docs`. Either way, name in your status line which of the two you got. Mechanics and the fallback chain: `stack-knowledge.md`.

## Status line

Finish with one line the user can act on: stack origin, CLI version vs `cli.min_version`, remote alias and auth state, Space MCP registered or not, and which knowledge path is live (stack docs tools, or `/api/docs` over HTTP).
