# Fluree Claude Plugins

Internal [Claude Code](https://code.claude.com/docs) plugins for Fluree demos and tooling.

This repository is a **Claude Code plugin marketplace**. Add it once, then install any plugin
inside it from Claude Code — either the **Claude Desktop** app (Code mode) or the **Claude
Code CLI** in a terminal.

> New here and just want to make demo data for Fluree? Jump to
> [Installation](#installation), install **fluree-dataset-generator**, then follow its
> [usage guide](plugins/fluree-dataset-generator/README.md).

---

## What's inside

| Plugin                       | What it does                                                                                                                                                                                   | Docs                                                 |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| **fluree-dataset-generator** | Interviews you about a domain and generates a complete, **validated** JSON-LD dataset (RDF model + realistic instance data) ready to upload into a Fluree knowledge graph such as Fluree Solo. | [README](plugins/fluree-dataset-generator/README.md) |
| **fluree-cli**               | Teaches Claude Code to drive the **`fluree` CLI** safely and well — probe-first use of the binary's embedded docs, destructive-op and credential safety rails, and Fluree AI (Solo) remote workflows. Includes `/fluree-cli:setup`. | [README](plugins/fluree-cli/README.md)               |

_Marketplace name: `fluree-plugins` (this is what you reference when installing — see below)._

---

## How Claude Code plugins & skills work

New to this? Here's the whole mental model in four bullets — once it clicks, the steps below
are obvious:

- **Claude Code** is Anthropic's agentic assistant. It runs in two places that **share the
  same plugin system**: the **Claude Desktop** app (flip the top toggle to **`Code`**) and the
  **Claude Code CLI** in a terminal. Everything in this repo works in both.
- A **marketplace** is just a GitHub repo (like this one) that lists plugins. You **add a
  marketplace once**.
- A **plugin** bundles capabilities — most commonly **skills**, but also slash commands,
  subagents, hooks, or MCP servers. You **install** the plugins you want from a marketplace.
- A **skill** is a packaged set of instructions that teaches Claude to do one job well. Skills
  **auto-trigger** when your request matches their purpose, or you can invoke one explicitly.
  You don't "run" a skill like a program — you just talk to Claude, and the skill steers how it
  responds.

So the entire flow is: **add this marketplace → install a plugin → ask Claude to do the
thing** (or pick the skill from a menu). Installed plugins persist across sessions, so you only
do the first two steps once.

> Want the official background? See Anthropic's docs on
> [discovering & installing plugins](https://code.claude.com/docs/en/discover-plugins) and
> [skills](https://code.claude.com/docs/en/skills).

---

## Installation

Installing is two steps: **(1) add this marketplace**, then **(2) install a plugin from it.**
You only add the marketplace once; afterward you can install/update plugins freely.

### Option A — Claude Code CLI (terminal)

```text
/plugin marketplace add fluree/claude-plugins
/plugin install fluree-dataset-generator@fluree-plugins
```

Notes:

- The `owner/repo` shorthand works for public GitHub repos. Claude Code reads
  `.claude-plugin/marketplace.json` from the repo root.
- The `@fluree-plugins` suffix is **required** and is the **marketplace name** (the `name`
  field in `marketplace.json`), _not_ the repo name.
- Prefer a menu? Run `/plugin` to open a tabbed UI — **Discover** (browse/install),
  **Installed** (enable/disable/uninstall), **Marketplaces** (add/update), **Errors**.
- If a freshly-added plugin isn't found, refresh with
  `/plugin marketplace update fluree-plugins`.

### Option B — Claude Desktop app (Code mode)

The click-by-click flow for non-CLI folks. **The Desktop UI evolves**, so treat the exact
button labels below as a snapshot — if one differs in your version, the underlying sequence is
always the same:

> **switch to `Code` → add this marketplace from GitHub → install the plugin → invoke its skill.**

1. Open **Claude Desktop**, updated enough that the top of the app shows the
   **`Chat | Cowork | Code`** toggle.
2. Click **`Code`** to switch to the desktop version of Claude Code.
3. Click **`Select Folder`** and choose a folder Claude Code may write to — e.g.
   `~/Desktop/ClaudeCode/`.
4. Near the input area, find the permission setting (usually **`Ask Permissions`**). Keep it
   on in general. If you're using Claude Code _only_ for these demo plugins, you can switch it
   to **`Auto accept edits`** so they run without you approving every file write.
5. Click the **`+`** icon by the input → **`Add Plugin`** (or, if you already have plugins,
   **`Plugins` → `Manage Plugins`**).
6. Click **`Browse Plugins`**. (Don't see it? Next to **`Personal Plugins`** click **`+`**,
   then **`Browse Plugins`**.)
7. In the modal, you'll see tabs **`By Anthropic | Your organization | Personal`** — click
   **`Personal`**.
8. Click the **`+`** icon to add a plugin repository → **`Add marketplace from GitHub`**.
9. Type **`fluree/claude-plugins`** and click **`Sync`**.
10. A **`Fluree dataset generator`** card appears. Hover it and click **`Install`**. Once
    installed, the button changes to **`Manage`**.
11. Back out to the main session with **`Code`** selected at the top — you're ready to use it.

### Option C — Team / non-interactive (settings.json)

To pre-register the marketplace and auto-enable plugins for a project or team, add to
`.claude/settings.json` (project) or `~/.claude/settings.json` (user):

```json
{
  "extraKnownMarketplaces": {
    "fluree-plugins": {
      "source": { "source": "github", "repo": "fluree/claude-plugins" }
    }
  },
  "enabledPlugins": {
    "fluree-dataset-generator@fluree-plugins": true
  }
}
```

The object key (`fluree-plugins`) is the marketplace name users reference in `/plugin`
commands. Project-scoped marketplaces prompt users to trust them before loading.

---

## Using a plugin

Once installed, each plugin contributes a **Skill** that you can invoke three ways:

- **Ask in plain English** — skills auto-trigger on intent, e.g. _"generate a demo insurance
  dataset for Fluree."_ You don't have to name the plugin.
- **Desktop menu** — `+` → **Plugins → Fluree dataset generator → Skills:
  fluree-dataset-generator** (inserts `/fluree-dataset-generator`, then press **Enter**).
- **CLI slash command** — `/fluree-dataset-generator:fluree-dataset-generator`.

Each plugin's own README has the full usage guide. For the dataset generator — including the
interview questions, scale guidance, and how to **upload the output into Fluree Solo** — see
**[plugins/fluree-dataset-generator/README.md](plugins/fluree-dataset-generator/README.md)**.

---

## Managing & updating

| Action                       | CLI                                                              |
| ---------------------------- | ---------------------------------------------------------------- |
| Open the plugin UI           | `/plugin`                                                        |
| Update this marketplace      | `/plugin marketplace update fluree-plugins`                      |
| Update an installed plugin   | re-run `/plugin install fluree-dataset-generator@fluree-plugins` |
| Enable / disable / uninstall | `/plugin` → **Installed** tab                                    |

In Claude Desktop, the **`Manage`** button on a plugin card (or **Plugins → Manage Plugins**)
covers update/disable/uninstall.

---

## Repository structure

```
claude-plugins/
├── .claude-plugin/
│   └── marketplace.json                 # marketplace manifest (name: "fluree-plugins")
└── plugins/
    └── fluree-dataset-generator/
        ├── .claude-plugin/
        │   └── plugin.json              # plugin manifest (name, version, author)
        ├── README.md                    # plugin usage guide
        └── skills/
            └── fluree-dataset-generator/
                ├── SKILL.md             # the skill's instructions to Claude
                └── scripts/             # Python validators run during generation
                    ├── validate_model.py
                    ├── validate_instances.py
                    └── validate_graph.py
```

---

## For maintainers — adding a plugin

1. Create `plugins/<plugin-name>/` with a `.claude-plugin/plugin.json`:
   ```json
   {
     "name": "<plugin-name>",
     "description": "<one-liner>",
     "version": "1.0.0",
     "author": { "name": "Fluree Dev Rel" }
   }
   ```
2. Add the plugin's capabilities — e.g. a Skill under `skills/<skill-name>/SKILL.md`
   (plus any bundled scripts), or commands/agents/hooks per the
   [plugin reference](https://code.claude.com/docs/en/plugins-reference).
3. Register it in `.claude-plugin/marketplace.json` under `plugins`:
   ```json
   {
     "name": "<plugin-name>",
     "source": "./plugins/<plugin-name>",
     "description": "<one-liner>",
     "version": "1.0.0"
   }
   ```
4. Write a `plugins/<plugin-name>/README.md` and link it from the table above.
5. Commit, push, and have testers run `/plugin marketplace update fluree-plugins` to pull it.

Keep `version` in `plugin.json` and `marketplace.json` in sync, and bump it on changes so
users get updates.

---

## Support

- **Claude Code plugin docs:** <https://code.claude.com/docs/en/discover-plugins>
- Maintained by **Fluree Dev Rel**.
