#!/usr/bin/env node
/**
 * The marketplace manifest duplicates each plugin's version; they must match
 * the plugin's own .claude-plugin/plugin.json (users only receive updates
 * when the marketplace entry's version bumps).
 */

import { readFileSync } from "node:fs";

const marketplace = JSON.parse(
  readFileSync(".claude-plugin/marketplace.json", "utf-8"),
);

const errors = [];
for (const entry of marketplace.plugins) {
  const pluginJson = JSON.parse(
    readFileSync(`${entry.source}/.claude-plugin/plugin.json`, "utf-8"),
  );
  if (pluginJson.name !== entry.name) {
    errors.push(
      `${entry.source}: marketplace name '${entry.name}' != plugin.json name '${pluginJson.name}'`,
    );
  }
  if (pluginJson.version !== entry.version) {
    errors.push(
      `${entry.name}: marketplace version '${entry.version}' != plugin.json version '${pluginJson.version}'`,
    );
  }
}

if (errors.length > 0) {
  console.error(`marketplace/plugin version sync failed (${errors.length}):`);
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}
console.log(`version sync OK (${marketplace.plugins.length} plugins).`);
