#!/usr/bin/env node
/**
 * Validate a plugin's contract/cli-facts.json against a fluree CLI surface
 * manifest (the fluree-cli-manifest.json release asset emitted by the hidden
 * `fluree manifest` command).
 *
 * Usage:
 *   node scripts/check-cli-contract.mjs <cli-facts.json> <manifest.json>
 *
 * Exit codes: 0 ok, 1 contract violations, 2 usage/IO/malformed input.
 * Entries with `hidden: true` are expected to be ABSENT from the manifest
 * (hidden commands are deliberately excluded by the producer) — their
 * presence fails the check, catching a hidden→visible promotion. Flags are
 * matched by long name against the command's own flags plus the manifest's
 * global_flags. The facts file's `min_cli_version` must not exceed the
 * manifest's version: a claim that needs a newer CLI than the one being
 * validated is itself a contract violation.
 */

import { readFileSync } from "node:fs";

const [factsPath, manifestPath] = process.argv.slice(2);
if (!factsPath || !manifestPath) {
  console.error("usage: check-cli-contract.mjs <cli-facts.json> <manifest.json>");
  process.exit(2);
}

function loadJson(path, label) {
  let raw;
  try {
    raw = readFileSync(path, "utf-8");
  } catch (e) {
    console.error(`cannot read ${label} at ${path}: ${e.message}`);
    process.exit(2);
  }
  try {
    return JSON.parse(raw);
  } catch (e) {
    // The realistic path here: curl "succeeded" on an HTML error page. That
    // is an infrastructure problem, not a contract violation — exit 2 so a
    // maintainer doesn't start editing cli-facts.json over it.
    console.error(`${label} at ${path} is not valid JSON: ${e.message}`);
    process.exit(2);
  }
}

const facts = loadJson(factsPath, "cli-facts");
const manifest = loadJson(manifestPath, "manifest");

if (manifest.manifest_version !== 1) {
  console.error(
    `manifest_version ${manifest.manifest_version} unsupported (checker knows 1); update this script.`,
  );
  process.exit(2);
}
if (!Array.isArray(manifest.commands) || !Array.isArray(facts.commands)) {
  console.error("malformed input: both files need a `commands` array.");
  process.exit(2);
}

const manifestVersion = manifest.version ?? "(unversioned)";
const byPath = new Map(manifest.commands.map((c) => [c.path.join(" "), c]));
const globalLongs = new Set(
  (manifest.global_flags ?? []).map((f) => f.long).filter(Boolean),
);

/** Lenient x.y.z compare; null when either side doesn't parse. */
function versionLt(a, b) {
  const parse = (v) => {
    const parts = String(v).split(/[-+]/)[0].split(".").map(Number);
    return parts.every(Number.isFinite) ? parts : null;
  };
  const [pa, pb] = [parse(a), parse(b)];
  if (!pa || !pb) return null;
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const [x, y] = [pa[i] ?? 0, pb[i] ?? 0];
    if (x !== y) return x < y;
  }
  return false;
}

const errors = [];

if (
  facts.min_cli_version &&
  versionLt(manifestVersion, facts.min_cli_version) === true
) {
  errors.push(
    `manifest is fluree ${manifestVersion} but the contract claims min_cli_version ${facts.min_cli_version} — the plugin's text needs a newer CLI than the one validated`,
  );
}

let checked = 0;
for (const entry of facts.commands) {
  const key = entry.path.join(" ");
  if (entry.hidden) {
    // Hidden machine plumbing must STAY excluded from the manifest; its
    // appearance means a hidden→visible promotion the contract should record.
    if (byPath.has(key)) {
      errors.push(
        `hidden command now visible in manifest (promote it in cli-facts): fluree ${key}`,
      );
    }
    continue;
  }
  checked += 1;
  const cmd = byPath.get(key);
  if (!cmd) {
    errors.push(`command not in manifest: fluree ${key}`);
    continue;
  }
  const longs = new Set((cmd.flags ?? []).map((f) => f.long).filter(Boolean));
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
    `cli-facts contract violated against manifest ${manifestVersion} (${errors.length}):`,
  );
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}

console.log(
  `cli-facts contract OK against fluree ${manifestVersion} (${checked} commands checked).`,
);
