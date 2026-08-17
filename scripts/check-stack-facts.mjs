#!/usr/bin/env node
/**
 * Validate a plugin's contract/stack-facts.json against the artifacts a
 * Fluree AI (Solo) stack publishes about itself.
 *
 * Usage:
 *   node scripts/check-stack-facts.mjs <stack-facts.json> [<manifest.json|url>]
 *
 * The manifest argument defaults to the facts file's `manifest_source`. A
 * value starting with http(s) is fetched; anything else is read from disk
 * (handy for validating against a solo working tree before the generated
 * artifact is published).
 *
 * Two halves, because a stack's surface has two producers:
 *
 *   1. ROUTER — `src/contracts/generated/router/endpoint-manifest.json`,
 *      generated from the Rust router's own route table. Every path the
 *      plugin's prose hard-codes must resolve against it, and every path the
 *      prose calls unauthenticated must actually carry `requireAuth: false`
 *      (the connect choreography's whole premise is a pre-auth probe).
 *   2. UI LAMBDA — `/api/docs`, `/activate`, `/docs/...` are served by the
 *      Next.js UI, not the router, so the manifest cannot confirm them. What
 *      it CAN falsify is the ownership claim: if one of them appears in the
 *      router manifest, the split the prose describes has moved. Their doc
 *      slugs are checked against a live stack instead, when STACK_ORIGIN is
 *      set — otherwise that half is skipped with a note.
 *
 * Doc slugs carry a `served` field, and both values are assertions:
 * `public` slugs MUST appear in the live `/api/docs` index (the plugin links
 * them as fetchable), and `in-app` slugs must NOT (the plugin tells users to
 * open them in the signed-in UI, and would be wrong to hand out a URL that
 * 404s). The `in-app` direction can't distinguish "withheld from the public
 * allowlist" from "deleted" — it catches the promotion, not the deletion.
 *
 * Exit codes: 0 ok, 1 contract violations, 2 usage/IO/malformed input.
 */

import { readFileSync } from "node:fs";

const [factsPath, manifestArg] = process.argv.slice(2);
if (!factsPath) {
  console.error(
    "usage: check-stack-facts.mjs <stack-facts.json> [<manifest.json|url>]",
  );
  process.exit(2);
}

function parseJson(raw, label, source) {
  try {
    return JSON.parse(raw);
  } catch (e) {
    // The realistic path here: a fetch "succeeded" on an HTML 404 page. That
    // is an infrastructure problem, not a contract violation — exit 2 so a
    // maintainer doesn't start editing stack-facts.json over it.
    console.error(`${label} at ${source} is not valid JSON: ${e.message}`);
    process.exit(2);
  }
}

function loadLocalJson(path, label) {
  let raw;
  try {
    raw = readFileSync(path, "utf-8");
  } catch (e) {
    console.error(`cannot read ${label} at ${path}: ${e.message}`);
    process.exit(2);
  }
  return parseJson(raw, label, path);
}

async function fetchText(url, label) {
  let res;
  try {
    res = await fetch(url);
  } catch (e) {
    console.error(`cannot fetch ${label} from ${url}: ${e.message}`);
    process.exit(2);
  }
  if (!res.ok) {
    console.error(`cannot fetch ${label} from ${url}: HTTP ${res.status}`);
    process.exit(2);
  }
  return res.text();
}

const facts = loadLocalJson(factsPath, "stack-facts");
if (facts.contract_version !== 1) {
  console.error(
    `contract_version ${facts.contract_version} unsupported (checker knows 1); update this script.`,
  );
  process.exit(2);
}

const manifestSource = manifestArg ?? facts.manifest_source;
if (!manifestSource) {
  console.error(
    "no manifest source: pass one as argv[2] or set `manifest_source` in the facts file.",
  );
  process.exit(2);
}

const manifest = /^https?:\/\//.test(manifestSource)
  ? parseJson(
      await fetchText(manifestSource, "endpoint manifest"),
      "endpoint manifest",
      manifestSource,
    )
  : loadLocalJson(manifestSource, "endpoint manifest");

if (manifest.version !== 1) {
  console.error(
    `endpoint manifest version ${manifest.version} unsupported (checker knows 1); update this script.`,
  );
  process.exit(2);
}
if (!manifest.routes || typeof manifest.routes !== "object") {
  console.error("malformed endpoint manifest: no `routes` object.");
  process.exit(2);
}

/** `{ledgerId}` and `{*rest}` are the same hole to a consumer of the manifest. */
const normalizeTemplate = (p) => p.replace(/\{[^}]*\}/g, "{}");
/** A concrete path to test against a regex row. */
const concretize = (p) => p.replace(/\{[^}]*\}/g, "_");

const rows = Object.entries(manifest.routes).map(([key, value]) => {
  const [method, ...rest] = key.split(" ");
  const template = rest.join(" ").replace(/ \[regex\]$/, "");
  return { key, method, template, ...value };
});

const methodMatches = (rowMethod, factMethod) =>
  rowMethod === "*" || factMethod === "*" || rowMethod === factMethod;

function resolveRoute(method, path) {
  const wanted = normalizeTemplate(path);
  // matchit beats regex (the manifest's own precedence), so try it first.
  const exact = rows.find(
    (r) =>
      r.kind === "matchit" &&
      methodMatches(r.method, method) &&
      normalizeTemplate(r.template) === wanted,
  );
  if (exact) return exact;
  const concrete = concretize(path);
  return rows.find(
    (r) =>
      r.kind === "regex" &&
      methodMatches(r.method, method) &&
      r.regex &&
      new RegExp(r.regex).test(concrete),
  );
}

const errors = [];
const notes = [];
let checked = 0;

for (const entry of facts.router_endpoints ?? []) {
  checked += 1;
  const { method = "*", path, public: isPublic } = entry;
  const row = resolveRoute(method, path);
  if (!row) {
    errors.push(`endpoint not in router manifest: ${method} ${path}`);
    continue;
  }
  if (typeof isPublic === "boolean") {
    const requiresAuth = row.authFlags?.requireAuth === true;
    if (isPublic && requiresAuth) {
      errors.push(
        `${method} ${path} is documented as unauthenticated but the manifest has requireAuth: true (matched ${row.key})`,
      );
    } else if (!isPublic && !requiresAuth) {
      errors.push(
        `${method} ${path} is documented as authenticated but the manifest has requireAuth: false (matched ${row.key})`,
      );
    }
  }
}

for (const entry of facts.api_prefixes ?? []) {
  checked += 1;
  const prefix = entry.prefix;
  if (!rows.some((r) => r.template.startsWith(prefix))) {
    errors.push(
      `api prefix matches no router route: ${prefix} (the prose builds URLs on it)`,
    );
  }
}

// UI-Lambda paths: the manifest is the falsifier for the OWNERSHIP claim,
// not for existence. A hit here means a path the plugin describes as
// UI-served is now routed by the router — the split the prose teaches moved.
for (const entry of facts.ui_paths ?? []) {
  checked += 1;
  const { method = "GET", path } = entry;
  const row = resolveRoute(method, path);
  if (row) {
    errors.push(
      `${method} ${path} is documented as UI-Lambda-served but now resolves in the router manifest (${row.key}) — re-check the prose's CLI/UI/API split`,
    );
  }
}

const slugs = facts.doc_slugs ?? [];
const stackOrigin = process.env.STACK_ORIGIN?.replace(/\/+$/, "");
if (slugs.length > 0 && stackOrigin) {
  const indexUrl = `${stackOrigin}/api/docs`;
  const index = await fetchText(indexUrl, "docs index");
  const served = new Set(
    [...index.matchAll(/\/api\/docs\/([a-z0-9-]+)\/([a-zA-Z0-9._-]+)/g)].map(
      (m) => `${m[1]}/${m[2]}`,
    ),
  );
  if (served.size === 0) {
    console.error(
      `docs index at ${indexUrl} listed no /api/docs/{category}/{slug} links — wrong origin, or the index format changed.`,
    );
    process.exit(2);
  }
  for (const entry of slugs) {
    checked += 1;
    const isServed = served.has(entry.slug);
    if (entry.served === "public" && !isServed) {
      errors.push(
        `doc slug missing from ${indexUrl}: ${entry.slug} (the plugin links it as publicly fetchable)`,
      );
    } else if (entry.served === "in-app" && isServed) {
      errors.push(
        `doc slug is now public at ${indexUrl}: ${entry.slug} — the plugin should link the /api/docs URL instead of sending users to the signed-in UI`,
      );
    }
  }
  notes.push(`docs index checked against ${indexUrl} (${served.size} served).`);
} else if (slugs.length > 0) {
  notes.push(
    `docs slugs NOT checked (${slugs.length} skipped): set STACK_ORIGIN=https://<stack> to validate them against a live /api/docs index.`,
  );
}

// Stack MCP tool names have no published producer artifact yet (solo#1040
// B2). The plugin's prose probes for them rather than asserting them, so
// they are recorded here for review, not validated.
const probeTools = (facts.mcp_tools ?? []).filter((t) => t.probe_only);
if (probeTools.length > 0) {
  notes.push(
    `mcp tools unvalidated (probe-only, no producer artifact yet): ${probeTools.map((t) => t.name).join(", ")}.`,
  );
}

for (const note of notes) console.log(`note: ${note}`);

if (errors.length > 0) {
  console.error(`stack-facts contract violated (${errors.length}):`);
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}

console.log(
  `stack-facts contract OK against endpoint manifest v${manifest.version} (${checked} facts checked).`,
);
