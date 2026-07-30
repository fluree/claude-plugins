#!/usr/bin/env node
/**
 * Validate a plugin's contract/cli-facts.json against a fluree CLI surface
 * manifest (the fluree-cli-manifest.json release asset emitted by the hidden
 * `fluree manifest` command).
 *
 * Usage:
 *   node scripts/check-cli-contract.mjs <cli-facts.json> <manifest.json>
 *
 * Exit codes: 0 ok, 1 contract violations, 2 usage/IO.
 * Entries with `hidden: true` are skipped (hidden commands are deliberately
 * excluded from the manifest). Flags are matched by long name against the
 * command's own flags plus the manifest's global_flags.
 */

import { readFileSync } from "node:fs";

const [factsPath, manifestPath] = process.argv.slice(2);
if (!factsPath || !manifestPath) {
  console.error("usage: check-cli-contract.mjs <cli-facts.json> <manifest.json>");
  process.exit(2);
}

const facts = JSON.parse(readFileSync(factsPath, "utf-8"));
const manifest = JSON.parse(readFileSync(manifestPath, "utf-8"));

if (manifest.manifest_version !== 1) {
  console.error(
    `manifest_version ${manifest.manifest_version} unsupported (checker knows 1); update this script.`,
  );
  process.exit(2);
}

const byPath = new Map(
  manifest.commands.map((c) => [c.path.join(" "), c]),
);
const globalLongs = new Set(
  (manifest.global_flags ?? []).map((f) => f.long).filter(Boolean),
);

const errors = [];

for (const entry of facts.commands) {
  if (entry.hidden) continue;
  const key = entry.path.join(" ");
  const cmd = byPath.get(key);
  if (!cmd) {
    errors.push(`command not in manifest: fluree ${key}`);
    continue;
  }
  const longs = new Set(cmd.flags.map((f) => f.long).filter(Boolean));
  for (const flag of entry.flags ?? []) {
    if (!longs.has(flag) && !globalLongs.has(flag)) {
      errors.push(`flag not in manifest: fluree ${key} --${flag}`);
    }
  }
}

for (const flag of facts.global_flags ?? []) {
  if (!globalLongs.has(flag)) {
    errors.push(`global flag not in manifest: --${flag}`);
  }
}

if (errors.length > 0) {
  console.error(
    `cli-facts contract violated against manifest ${manifest.version} (${errors.length}):`,
  );
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}

console.log(
  `cli-facts contract OK against fluree ${manifest.version} (${facts.commands.length} commands checked).`,
);
