# Reading a stack's own knowledge

## Three corpora, and they are not interchangeable

| Source | Covers | Pinned to |
| --- | --- | --- |
| The `fluree` binary's embedded docs (`fluree docs search`, or the `fluree-docs` MCP server the `fluree-cli` plugin connects) | The **CLI's** command surface — flags, subcommands, local ledger mechanics | The installed binary's version |
| The **stack's** docs (`docs_search` etc. if present, else `GET /api/docs`) | The **platform** — Spaces, agents, datasets, imports, policies, Iceberg, apps, the UI, the HTTP API | The release that stack is running |
| This plugin | Choreography and doctrine only | Nothing — which is why it must not carry platform reference |

A CLI flag question goes to the binary. "How do I do X in Fluree AI" goes to the stack. Answering either from training data is the failure mode this whole design exists to prevent.

## Path A — the stack's docs MCP tools

If `docs_search`, `docs_get`, `docs_tree`, or `docs_examples` are available in the session, use them. They are the good path: search is section-level, and results come back pinned to the stack's release.

**Probe, don't assume.** These tools are new. A stack running an older release will not have them, and neither will a session that hasn't registered the stack's MCP server. Check what tools you actually have before planning around them; on absence, fall straight to Path B without commentary.

## Path B — HTTP fallback via `/api/docs`

Every stack serves an llms.txt-style index at `GET /api/docs`, unauthenticated, as markdown:

```bash
curl -fsS https://<stack>/api/docs
```

It opens with a header, then one section per category (Tutorials, How-to Guides, Concepts, Reference), each a list of lines shaped like:

```
- [How to Upload and Import Data](/api/docs/how-to/upload-and-import-data) — <one-line description>
```

So the chain is: **fetch the index → pick slugs by title and description → fetch each page's raw markdown.**

```bash
curl -fsS https://<stack>/api/docs/how-to/upload-and-import-data
```

Newer stacks also serve ranked search at `GET /api/docs/search?q=…` — and their `/api/docs` index says so in its header. Probe it first; on 404 (an older stack), the index *is* the search surface, and it is small enough to read in full. Either way, pick real slugs rather than guessing: fetching an unknown slug returns 404, and a slug that exists on one stack may not exist on another.

## What the public index leaves out

On some stack releases the `/api/docs` set is narrower than the docs a signed-in user sees in the UI (newer releases serve the whole corpus publicly). A withheld page 404s on `/api/docs/...` while rendering fine at `https://<stack>/docs/{category}/{slug}` for a signed-in user — the MCP/agent how-tos were the commonly withheld ones.

So: if a page you expect isn't in the index, that is not evidence the stack lacks the feature. Point the user at the signed-in `/docs/...` URL instead, and say why.

## Citing what you read

When you answer from a stack doc, say which page and which stack. "Per `how-to/upload-and-import-data` on your stack" is a checkable claim; "Fluree supports…" is not, and is exactly the kind of statement that ages badly across releases.
