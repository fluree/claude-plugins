---
name: fluree-dataset-generator
description: "Generate synthetic JSON-LD datasets for Fluree semantic graph databases. Creates RDF data models (rdfs:Class, rdf:Property) and realistic instance data with validated relationships. Use this skill whenever the user wants to create demo data, sample datasets, synthetic data, or test data for Fluree, or when they mention generating JSON-LD, RDF, semantic graph data, or knowledge graph datasets. Also trigger when users ask about populating a Fluree database, creating ontologies with instance data, or building demo graphs — even if they don't say Fluree explicitly but describe wanting linked data or semantic datasets with classes and properties."
---

# Fluree Dataset Generator

You generate complete, validated JSON-LD datasets for Fluree semantic graph databases. This involves:
1. Interviewing the user about their desired data domain
2. Generating an RDF data model (classes + properties)
3. Generating realistic instance data that conforms to the model
4. Validating everything programmatically with Python scripts
5. Writing output as `.jsonld` files to the user's chosen directory

## Phase 1: User Interview

Start by gathering requirements conversationally. Ask these questions (adapt phrasing naturally):

1. **Domain**: "What domain should this dataset model?" (e.g., e-commerce, healthcare, insurance, IoT, supply chain)
2. **Description**: "Can you describe the kinds of entities and relationships you'd want? Any specific classes in mind, or should I design the whole thing?"
3. **Scale**: Ask about overall dataset size, NOT per-class counts. Different classes naturally have very different instance counts — a "Size" class might have 5 instances (XS through XXL) while a "Product" class has 150. Frame it as:
   - "How large a dataset overall? ~200 total instances is good for a quick demo, ~500 for a solid one, 1000+ for stress testing."
   - Or if the user gives a per-class number, treat it as a **maximum for the largest class**. The model plan's distribution ratios will determine how many instances each class actually gets, and some classes (reference data, enums, lookup tables) will naturally have far fewer.
4. **Namespace**: "I'll use `ex:` as the default prefix (expanding to something like `https://example.org/yourns#`). Want a custom namespace instead?"
5. **Output location**: "Where should I write the files?" (default: `Desktop/<Domain>-Dataset/` under the user's home directory)
6. **Special requirements**: "Any specific constraints? Certain property types, required relationships, particular data patterns?"

Don't be rigid about asking these as a checklist — read the conversation and skip questions the user has already answered. If they say "make me an insurance dataset with 12 classes and about 100 instances each", you already have most of what you need — treat "100 instances" as the max for the largest class and let distribution ratios drive the rest.

After gathering requirements, summarize back to the user for confirmation. When presenting the plan, show a table with each class and its expected instance count so the user can see that small reference classes (jurisdictions, categories, etc.) will have far fewer instances than the core domain classes. This is where the user should sanity-check the counts.

## Prerequisites Check

Before generating anything, verify that Python 3 is available. The validation scripts require it. Run:
```
python3 --version
```
If that fails, try `python --version` (on Windows, Python 3 is often just `python`). If neither works, tell the user:

> "This skill needs Python 3 for data validation. You can install it from https://www.python.org/downloads/ — or if you're on a Mac, `brew install python3`, or on Windows, `winget install Python.Python.3`. Let me know when it's installed and I'll continue."

Stop and wait — don't proceed without Python, as the validation step is essential to producing correct output.

Once confirmed, note which command worked (`python3` or `python`) and use that consistently for the rest of the session.

## Phase 2: Model Generation

Generate the data model through a structured multi-stage process. Use tool_use for structured output at every stage.

### Stage 1: Model Plan

Generate a high-level plan including:
- Model name and description
- List of class names (PascalCase, no namespace prefix yet)
- Class distribution ratios (what proportion of total instances each class should represent — must sum to 1.0, reflecting realistic domain proportions)

Present the plan to the user for approval. They may want to add/remove classes or adjust ratios.

### Stage 2: Class and Property Enumeration

For each class, define:
- Full IRI with namespace prefix (e.g., `ex:Customer`)
- List of property IRIs belonging to this class

For each property, define:
- Full IRI (e.g., `ex:firstName`)
- Type: `scalar` or `ref`
- Range: XSD datatype for scalars (`xsd:string`, `xsd:integer`, `xsd:float`, `xsd:boolean`, `xsd:dateTime`) or target class IRI for refs

**IRI conventions:**
- Classes: PascalCase (`ex:OrderItem`, `ex:InsurancePlan`)
- Properties: camelCase (`ex:firstName`, `ex:orderDate`, `ex:belongsToCategory`)

**On relationships and circular references:**
Unlike rigid pipeline systems, you have freedom here. Go ahead and model bidirectional relationships naturally if the domain calls for it (e.g., `Order→Customer` and `Customer→orders`). You'll handle generation order and validation flexibly later. The key principle: model the domain truthfully first, handle generation logistics second.

### Stage 3: Class Details

For each class, add:
- `rdfs:label`: Human-readable name
- `rdfs:comment`: 2-3 sentence description of purpose and role

### Stage 4: Property Details

For each property, add:
- `rdfs:label`: Human-readable name
- `rdfs:comment`: 1-2 sentence description
- Metadata:
  - `required`: boolean
  - `cardinality`: `"one"` or `"many"`
  - `min_value` / `max_value`: optional numeric or date constraints
  - `pattern`: optional regex for string validation
  - `enum_values`: optional list of allowed values

### Stage 5: Write and Validate the Model File

Construct the model JSON-LD file and write it. The format is:

```jsonld
{
  "@context": {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "f": "https://ns.flur.ee/ledger#",
    "rdfs:range": { "@type": "@id" },
    "rdfs:domain": { "@type": "@id" },
    "f:classes": { "@type": "@id" },
    "f:properties": { "@type": "@id" },
    "<prefix>": "<namespace_uri>"
  },
  "@graph": [
    {
      "@id": "f:data-model",
      "@type": "f:DataModel",
      "rdfs:label": "<Model Name>",
      "rdfs:comment": "<Model Description>",
      "f:classes": [
        {
          "@id": "<prefix>:<ClassName>",
          "@type": "rdfs:Class",
          "rdfs:label": "<Label>",
          "rdfs:comment": "<Description>",
          "rdfs:range": [{"@id": "<prefix>:<propertyThatRefsThisClass>"}, ...]
        }
      ],
      "f:properties": [
        {
          "@id": "<prefix>:<propertyName>",
          "@type": "rdf:Property",
          "rdfs:label": "<Label>",
          "rdfs:comment": "<Description>",
          "rdfs:domain": "<prefix>:<ClassName>",
          "rdfs:range": "<xsd:type or prefix:ClassName>"
        }
      ]
    }
  ]
}
```

Notes on the model format:
- `rdfs:range` on a class lists properties whose range points TO that class (incoming ref properties)
- `rdfs:domain` on a property can be a single IRI string or an array if the property is shared across classes
- Only include `rdfs:range` on classes that actually have incoming reference properties

After writing, run the model validation script:
```
python3 <SCRIPTS_DIR>/validate_model.py <model_file_path>
```
(Replace `<SCRIPTS_DIR>` with the resolved path from the Scripts Reference section. On Windows, use `python` if `python3` is unavailable.)

Fix any validation errors before proceeding.

## Phase 3: Instance Generation

This is where the skill earns its keep. Instance generation must produce realistic, semantically coherent data that satisfies the model's constraints.

### Planning Instance Generation

Before generating, analyze the model to determine:

1. **Dependency levels**: Which classes can be generated independently (no required refs to other classes), and which depend on others existing first?
   - Level 0: Classes with no required reference properties (or only self-refs)
   - Level 1+: Classes whose required refs point only to classes in lower levels

2. **Semantic clusters**: Groups of related classes where instances need to be coherent with each other (e.g., Products and their Reviews should make sense together)

3. **Instance counts**: Apply class distribution ratios to the user's target scale. The ratios from the model plan determine how many instances each class gets. Small reference classes (lookup tables, jurisdictions, enum-like entities) should have counts that reflect their actual real-world cardinality — 4 regulators, 6 sizes, 8 jurisdictions — rather than being inflated to hit a per-class minimum. The user's scale number is a target for the *largest* class; everything else scales proportionally.

4. **File grouping**: Plan how instances will be grouped into files. Guidelines:
   - Group semantically related classes together (e.g., Products + Reviews + Categories in one file)
   - Keep individual files under ~2000 instances
   - Target 3-10 output files total
   - Name files descriptively: `instances-customers.jsonld`, `instances-products-reviews.jsonld`, etc.

### Generating Instances

Generate instances in dependency-level order. For each batch:

**Scalar properties first**: Generate instances with all scalar properties filled in. Every instance needs:
- `@id`: A unique IRI following the pattern `<prefix>:<ClassName>/<descriptive-slug>` (e.g., `ex:Customer/jane-doe-42`)
- `@type`: The class IRI
- All required scalar properties, plus a realistic subset of optional ones

**Reference properties**: After generating instances for classes at the current dependency level, add reference properties. You now know what entities exist and can assign real IRIs.

**Context grounding for semantic coherence**: When generating instances that reference other entities, use your judgment about how much context to provide. Some scenarios:
- Reviews for products: You probably want to see the product's name, category, and description to write a coherent review
- Order line items: You need to know product names and prices
- Employees in departments: Department name and function matter

Don't follow a rigid formula. Think about what a human would need to know to create realistic data, and provide that context. For large datasets, you won't be able to see every entity — sample representatively.

**Batch sizing**: For larger datasets (100+ instances per class), generate in batches of 20-50 instances per LLM call. Use the Task tool to parallelize independent batches (different classes at the same dependency level can generate simultaneously).

**Keep data out of your context**: For large datasets, write each batch to disk immediately after generation. Use Python scripts to validate rather than reading everything back into context. The Task tool with subagents is invaluable here — a subagent can generate a batch, write it to a temp file, and report back just the summary (count, any issues).

### Instance File Format

Each instance file should be:

```jsonld
{
  "@context": {
    "<prefix>": "<namespace_uri>",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "<prefix>:refProperty1": { "@type": "@id" },
    "<prefix>:refProperty2": { "@type": "@id" },
    "<prefix>:intProperty": { "@type": "xsd:integer" },
    "<prefix>:dateProperty": { "@type": "xsd:dateTime" },
    "<prefix>:boolProperty": { "@type": "xsd:boolean" },
    "<prefix>:floatProperty": { "@type": "xsd:float" }
  },
  "@graph": [
    {
      "@id": "<prefix>:<ClassName>/<slug>",
      "@type": "<prefix>:<ClassName>",
      "<prefix>:scalarProp": "value",
      "<prefix>:refProp": { "@id": "<prefix>:<OtherClass>/<slug>" },
      "<prefix>:multiValueProp": [
        { "@id": "<prefix>:<OtherClass>/<slug1>" },
        { "@id": "<prefix>:<OtherClass>/<slug2>" }
      ]
    }
  ]
}
```

Context rules:
- Reference properties get `{ "@type": "@id" }`
- Non-string scalar properties get their XSD type directive (e.g., `{ "@type": "xsd:integer" }`)
- `xsd:string` properties need no `@type` directive (it's the default)
- Multi-value properties use JSON arrays
- Single reference values use `{ "@id": "..." }` format

## Phase 4: Validation

Run comprehensive validation after all instance files are generated. This is the critical step that ensures data quality.

### Immediate Validations (run per-file as generated)

```
python3 <SCRIPTS_DIR>/validate_instances.py <instance_file> --model <model_file>
```

This checks:
- Valid JSON-LD structure
- Every instance has `@id` and `@type`
- `@type` references a class defined in the model
- All properties are defined in the model for that class
- Required properties are present
- Scalar values match expected XSD types
- `@context` covers all terms used
- No duplicate `@id` values within the file

### Deferred Validations (run after ALL files are generated)

```
python3 <SCRIPTS_DIR>/validate_graph.py <output_directory> --model <model_file>
```

This checks:
- **No orphan references**: Every `{ "@id": "..." }` reference value points to an entity that exists somewhere in the dataset
- **No orphan entities**: Every entity is referenced by at least one other entity (unless it's a "root" class with no incoming ref properties in the model — those are allowed to be unreferenced)
- **Cardinality constraints**: Single-cardinality properties don't have arrays; multi-cardinality properties that are arrays are OK
- **Referential type correctness**: A property with range `ex:Product` only references instances whose `@type` is `ex:Product`
- **Global uniqueness**: No duplicate `@id` across all files
- **Constraint validation**: min/max, pattern, and enum constraints are satisfied

### Handling Validation Failures

When validation fails:
1. Read the error report from the script
2. Fix the specific issues — this might mean:
   - Regenerating a few instances with corrected references
   - Adding missing required properties
   - Fixing type mismatches
   - Patching orphan references (adding a reference to an unreferenced entity, or creating a missing entity)
3. Re-run validation until clean

For orphan/reference issues specifically: rather than regenerating large batches, write targeted Python patches that fix the specific IRIs. The validation scripts output structured JSON errors that can be consumed programmatically.

## Phase 5: Final Output

After validation passes, the output directory should contain:
```
<Domain>-Dataset/
├── model.jsonld
├── instances-<group1>.jsonld
├── instances-<group2>.jsonld
├── ...
└── metadata.json (optional summary)
```

Report to the user:
- Total classes and properties in the model
- Total instances generated, broken down by class
- Number of relationships created
- Any notable statistics (e.g., "average 3.2 relationships per entity")
- The file paths

## Scripts Reference

This skill bundles Python validation scripts in a `scripts/` directory next to this SKILL.md file.

### Locating the scripts (do this once per session)

The scripts live inside the plugin cache after installation. Locate them once and reuse the path. Use Python for this since it works identically on macOS, Linux, and Windows:

```bash
python3 -c "
import pathlib, os
for root in [pathlib.Path.home() / '.claude']:
    for p in root.rglob('fluree-dataset-generator/scripts/validate_model.py'):
        print(p.parent); break
"
```

On **Windows**, use `python` instead of `python3` if `python3` is not on the PATH (this applies to all `python3` commands in this skill — use whichever alias the user's system provides).

Store the resulting path. All validation commands below assume you have this path available. When passing it to subagents, pass the resolved absolute path string directly so they don't need to re-discover it.

| Script | Purpose | When to Run |
|--------|---------|-------------|
| `validate_model.py` | Validate model JSON-LD structure and consistency | After writing model file |
| `validate_instances.py` | Validate instance file against model | After writing each instance file |
| `validate_graph.py` | Cross-file reference integrity and orphan detection | After all instance files are written |

All scripts exit 0 on success, non-zero on failure, and print structured JSON error reports to stdout.

## Important Patterns

### Use Python for All Validation
Never try to validate large datasets by reading them into your context. Always use the bundled scripts. They handle files of any size efficiently and give precise error locations.

### Use Task/Subagents for Parallelism
When generating instances for independent classes, spawn parallel Task subagents. Each one generates a batch, writes to a temp file, validates, and reports back. This dramatically speeds up large datasets.

**When spawning subagents, give them explicit instructions so they don't waste time exploring:**
- Pass the exact validation command to run, with the absolute `<SCRIPTS_DIR>` path already substituted: `python3 /absolute/path/to/scripts/validate_instances.py <output_file> --model <model_file> --json`
- Do NOT tell them to "read the validation script" — they should just execute it
- Include the full model context (classes, properties, IRIs of entities from prior levels) directly in the subagent prompt so they don't need to read files to discover it
- Tell them the exact output file path to write to

### Model File is Read-Only During Instance Generation
Subagents must NEVER modify `model.jsonld`. The model is the contract that all instance files are validated against, and modifying it mid-generation creates cascading problems:
- Instance files written before the change may no longer validate against the updated model
- Parallel subagents would race on the same file
- The parent session's model context becomes stale, causing it to give incorrect instructions to subsequent subagents

If a subagent discovers that the model appears to need a change (e.g., a missing property or relationship), it should:
1. **Complete its task** using only what the model currently defines
2. **Report the gap** back to the parent session (e.g., "Note: the model doesn't have a `cfo:caseNotes` property on Case — I used `cfo:description` instead, but you may want to add it")
3. The parent session can then decide whether to update the model, re-validate affected files, and adjust subsequent generation prompts accordingly

This keeps the model as a stable shared contract throughout the generation process.

### Incremental Generation
Don't try to generate everything in one shot. Generate and validate incrementally:
1. Model → validate → fix
2. Level 0 instances → validate → fix
3. Level 1 instances → validate → fix
4. ... continue through dependency levels
5. Full graph validation → fix any cross-file issues

### IRI Uniqueness
Instance IRIs should be globally unique and descriptive. Use the pattern: `<prefix>:<ClassName>/<kebab-case-descriptor>-<disambiguator>`. The disambiguator can be a number, initials, or other short unique suffix. Avoid purely numeric IDs — `ex:Customer/sarah-chen-7` is better than `ex:Customer/42`.

### Handling Large Datasets
For datasets with 100+ instances per class:
- Generate in batches of 20-50
- Write each batch to a temp file immediately
- Use subagents to parallelize across classes
- Validate incrementally
- Merge batches into final files at the end with a Python script
- Never try to hold the full dataset in context
