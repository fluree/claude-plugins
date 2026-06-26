# Fluree Dataset Generator

> A Claude Code plugin that interviews you about a domain, then generates a complete,
> **validated** JSON-LD dataset — an RDF data model plus realistic instance data — ready to
> drop straight into a Fluree knowledge graph (e.g. **Fluree Solo**) for demos, prototypes,
> and testing.

This is the demo-data path for Fluree: instead of hand-building a model and faking instances,
you describe what you want ("an insurance dataset", "a supply-chain graph", "IoT telemetry")
and the plugin produces clean, internally-consistent `.jsonld` files with **no dangling
references and no type mismatches** — because every file is checked by bundled Python
validators before you ever see it.

> **Why this exists:** until the AI Demo Generator app works directly with Fluree Solo, this
> plugin is the supported way to generate demo data on your machine and then upload it into a
> Solo knowledge graph.

---

## What you get

When the skill finishes, a single output folder (default `~/Desktop/<Domain>-Dataset/`)
contains:

```
Insurance-Demo-Graph/
├── model.jsonld                      # the RDF data model: classes + properties
├── instances-policies-claims.jsonld  # instance data, grouped by topic
├── instances-customers.jsonld
├── instances-...jsonld
└── metadata.json                     # optional run summary (counts, stats)
```

Everything is **JSON-LD** using Fluree's ledger context, so Fluree understands the classes,
properties, datatypes, and the `@id` references that link entities together.

---

## Prerequisites

| Requirement                | Why                         | Notes                                                                                                                                                                                  |
| -------------------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Claude Code**            | runs the plugin             | Either the **Claude Desktop** app (switch to **Code** mode) or the **Claude Code CLI** in a terminal.                                                                                  |
| **Python 3**               | runs the validation scripts | The skill checks for this and stops if it's missing. Install from <https://www.python.org/downloads/>, or `brew install python3` (macOS) / `winget install Python.Python.3` (Windows). |
| **A writable folder**      | the plugin writes files     | In Desktop, you pick this when you select a working folder (e.g. `~/Desktop/ClaudeCode/`).                                                                                             |
| **A Fluree Solo instance** | to actually load the data   | Only needed for the final upload step. The generation itself is fully local.                                                                                                           |

No prior knowledge of RDF, JSON-LD, or SPARQL is required to _use_ this — the plugin handles
the modeling for you.

---

## Install

If you haven't added the marketplace yet, do that first (one-time). Full instructions —
including the click-by-click Claude Desktop walkthrough — are in the
[repository README](../../README.md#installation). The short version:

**Claude Code CLI**

```text
/plugin marketplace add fluree/claude-plugins
/plugin install fluree-dataset-generator@fluree-plugins
```

**Claude Desktop (Code mode):** `+` → **Add Plugin** → **Browse Plugins** → **Personal**
tab → add marketplace `fluree/claude-plugins` → **Sync** → **Install** on the
_Fluree dataset generator_ card.

---

## Running it

You can launch the skill three ways — pick whichever fits:

1. **Just ask, in plain English.** The skill auto-triggers on intent. Try:

   > "Generate a demo insurance dataset for Fluree with about 500 instances."

   or even just _"make me some sample knowledge-graph data."_ You don't have to name the
   plugin.

2. **Claude Desktop menu.** Click `+` near the input → **Plugins → Fluree dataset generator →
   Skills: fluree-dataset-generator**. This drops `/fluree-dataset-generator` into the input;
   press **Enter**.

3. **CLI slash command.** `/fluree-dataset-generator:fluree-dataset-generator`

> **Permissions tip (Desktop):** the plugin writes files and runs validation scripts. If you
> keep the default **Ask Permissions**, you'll approve each write/run — fine, but you'll need
> to check back as it works. If you're _only_ using Claude Code for this generator, switching
> to **Auto accept edits** lets it run start-to-finish without babysitting. (General rule:
> keep Ask Permissions on for everything else.)

---

## What it asks you (the interview)

The skill runs a short, conversational interview. Answer what you know; it fills in sensible
defaults for the rest. If you front-load details ("12-class insurance model, ~100 instances
per class, namespace `acme:`"), it skips the questions you've already answered.

| Question                 | What it's for                                 | Default / guidance                                                                                |
| ------------------------ | --------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Domain**               | the subject of the dataset                    | e.g. e-commerce, healthcare, insurance, IoT, supply chain                                         |
| **Description**          | which entities & relationships you care about | Say "design the whole thing" to let it choose.                                                    |
| **Scale**                | _overall_ dataset size                        | ~200 = quick demo · ~500 = solid demo · 1000+ = stress test. See note below.                      |
| **Namespace**            | the IRI prefix for your data                  | Default `ex:` → `https://example.org/yourns#`. Provide your own (e.g. `acme:`) for branded demos. |
| **Output location**      | where files are written                       | Default `~/Desktop/<Domain>-Dataset/`. It confirms before writing.                                |
| **Special requirements** | any constraints                               | Required relationships, specific property types, value patterns, enums, etc.                      |

**About "scale":** give a _total_ size, not a per-class count. Real domains have lopsided
cardinality — a `Size` class has ~5 instances (XS–XXL) while a `Product` class has 150. If you
do give a per-class number, it's treated as a **maximum for the largest class**, and
realistic distribution ratios size everything else down from there. Before generating, the
skill shows you a **table of each class and its planned instance count** so you can sanity-check
it.

---

## What happens under the hood

You don't need to drive any of this — but it helps to know why the output is trustworthy. The
skill works in validated phases:

1. **Interview** → confirms a plan with you (classes + per-class counts).
2. **Model generation** → builds the RDF model (classes, properties, datatypes,
   relationships) and runs `validate_model.py`.
3. **Instance generation** → generates realistic instances in dependency order (referenced
   entities first), parallelizing independent batches. Each file is checked with
   `validate_instances.py` as it's written.
4. **Graph validation** → after all files exist, `validate_graph.py` runs cross-file checks:
   - no **orphan references** (every `@id` link points at something real),
   - no unintended **orphan entities**,
   - **referential type correctness** (a `Product` ref really points at a `Product`),
   - **global `@id` uniqueness** across all files,
   - **cardinality** and **min/max / pattern / enum** constraints satisfied.
5. **Final report** → totals by class, relationship counts, notable stats, and the file paths.

If anything fails validation, the skill fixes it and re-runs until clean. That's the core
value: the data you get is **semantically coherent and loads without reference errors**.

<details>
<summary>Output format reference (for the curious)</summary>

**Model** uses Fluree's ledger context and a single `f:DataModel` node holding `f:classes` and
`f:properties`:

```jsonc
{
  "@context": {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "f": "https://ns.flur.ee/ledger#",
    "ex": "https://example.org/yourns#",
  },
  "@graph": [
    {
      "@id": "f:data-model",
      "@type": "f:DataModel",
      "f:classes": [
        {
          "@id": "ex:Customer",
          "@type": "rdfs:Class",
          "rdfs:label": "Customer",
          "rdfs:comment": "…",
        },
      ],
      "f:properties": [
        {
          "@id": "ex:firstName",
          "@type": "rdf:Property",
          "rdfs:domain": "ex:Customer",
          "rdfs:range": "xsd:string",
        },
      ],
    },
  ],
}
```

**Instances** declare datatypes/refs once in `@context`, then list entities in `@graph`:

```jsonc
{
  "@context": {
    "ex": "https://example.org/yourns#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "ex:placedBy": { "@type": "@id" }, // reference property
    "ex:total": { "@type": "xsd:float" }, // typed scalar
  },
  "@graph": [
    {
      "@id": "ex:Order/jane-doe-1042",
      "@type": "ex:Order",
      "ex:total": 129.99,
      "ex:placedBy": { "@id": "ex:Customer/jane-doe-7" },
    },
  ],
}
```

Conventions: classes are `PascalCase`, properties `camelCase`, instance IRIs are
`ex:ClassName/descriptive-slug` (not bare numbers).

</details>

---

## Loading the data into Fluree Solo

Once the files are generated:

1. Open your **Fluree Solo** instance.
2. Create a **Blank Knowledge Graph**.
3. Go to the **Uploads** tab.
4. Use the file picker to select **all** the `.jsonld` files from the output folder (the
   `model.jsonld` _and_ every `instances-*.jsonld`).
5. Click **Start Upload**.

That's it — Solo ingests the model and instance data, and you can immediately query it
(SPARQL/FlureeQL) for your demo.

> **Ordering:** uploading the model and all instance files together is the simplest path. If
> you ever load piecemeal, load `model.jsonld` first.

---

## Tips for great demos

- **Use a branded namespace.** Set the prefix to your prospect's or product's name (e.g.
  `acme:`) so the data reads as theirs, not generic.
- **Right-size it.** ~500 total instances looks rich in a UI without being slow to upload. Go
  1000+ only when you specifically want to show scale.
- **Name the domain specifically.** "Commercial property & casualty insurance" yields a more
  convincing model than just "insurance."
- **Iterate.** Don't like the model? Tell the skill what to change (add/remove a class, adjust
  counts, add a relationship) before instance generation — it's cheap to revise the plan,
  more expensive after thousands of instances exist.
- **Keep the folder.** The generated files are reusable — re-upload them to any fresh graph
  any time. Regenerate only when you want different data.

---

## FAQ / troubleshooting

**"It stopped and asked me to install Python."**
The validators need Python 3. Install it (see [Prerequisites](#prerequisites)), then tell the
skill to continue. On Windows, `python` may work where `python3` doesn't — the skill handles
either.

**Nothing got written / it keeps asking permission.**
You're in **Ask Permissions** mode. Either approve each prompt, or (for this generator only)
switch to **Auto accept edits** so it can write and validate without interruption.

**Can I load my own real-world RDF (`.ttl`/OWL) instead?**
This plugin _generates synthetic_ demo data — it does not ingest your existing real-world
files. To load real `.ttl`/OWL/JSON-LD you already have, upload those directly into Fluree
Solo via the same **Uploads** tab; you don't need this plugin for that.

**Can I change the data after it's generated?**
Yes — the output is plain `.jsonld` you can hand-edit, or just ask the skill to regenerate or
extend it. If you hand-edit, keep `@id`s unique and references pointing at real entities (the
same rules the validators enforce).

**How big can it go?**
It's designed to scale: instances generate in batches, write to disk immediately, and
validate incrementally, so it doesn't choke on large datasets. Very large graphs (tens of
thousands of instances) just take longer.

**Where did the validation scripts go?**
They ship inside the plugin at
`skills/fluree-dataset-generator/scripts/` (`validate_model.py`, `validate_instances.py`,
`validate_graph.py`) and run automatically. You normally never call them by hand.

---

_Part of the [Fluree Claude Plugins](../../README.md) marketplace · maintained by Fluree Dev Rel._
