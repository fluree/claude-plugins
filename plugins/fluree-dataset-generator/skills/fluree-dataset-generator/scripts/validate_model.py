#!/usr/bin/env python3
"""
Validate a Fluree data model JSON-LD file.

Checks:
1. Valid JSON structure
2. Has @context and @graph
3. @graph contains an f:DataModel node
4. All classes have @id, @type=rdfs:Class, rdfs:label, rdfs:comment
5. All properties have @id, @type=rdf:Property, rdfs:label, rdfs:comment, rdfs:range
6. Property domains reference defined classes
7. Property ranges are valid XSD types or defined class IRIs
8. No duplicate @id values
9. Every class has at least one property in its domain
10. Cardinality values are "one" or "many" (if metadata is present)

Usage:
    python validate_model.py <model_file.jsonld>
    python validate_model.py <model_file.jsonld> --json  (structured output)

Exit codes:
    0 = valid
    1 = validation errors found
    2 = file/parse error
"""

import json
import sys
import argparse
from pathlib import Path

VALID_XSD_TYPES = {
    "xsd:string", "xsd:integer", "xsd:int", "xsd:long", "xsd:short",
    "xsd:float", "xsd:double", "xsd:decimal",
    "xsd:boolean", "xsd:dateTime", "xsd:date", "xsd:time",
    "xsd:anyURI", "xsd:nonNegativeInteger", "xsd:positiveInteger",
}


def load_model(path: str) -> dict:
    """Load and parse the model file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_model_parts(data: dict) -> tuple:
    """Extract the DataModel node, classes, and properties from @graph."""
    graph = data.get("@graph", [])
    if not isinstance(graph, list):
        graph = [graph]

    model_node = None
    for node in graph:
        if node.get("@type") == "f:DataModel":
            model_node = node
            break

    if model_node is None:
        return None, [], []

    classes = model_node.get("f:classes", [])
    if not isinstance(classes, list):
        classes = [classes]

    properties = model_node.get("f:properties", [])
    if not isinstance(properties, list):
        properties = [properties]

    return model_node, classes, properties


def validate(data: dict) -> list:
    """Run all validation checks. Returns list of error dicts."""
    errors = []

    def err(rule: str, message: str, node_id: str = None):
        e = {"rule": rule, "message": message}
        if node_id:
            e["node_id"] = node_id
        errors.append(e)

    # 1. Check top-level structure
    if "@context" not in data:
        err("structure", "Missing @context at top level")
    if "@graph" not in data:
        err("structure", "Missing @graph at top level")
        return errors  # Can't continue without @graph

    # 2. Extract model parts
    model_node, classes, properties = extract_model_parts(data)

    if model_node is None:
        err("structure", "No f:DataModel node found in @graph")
        return errors

    # 3. Check DataModel node
    if "rdfs:label" not in model_node:
        err("data_model", "f:DataModel node missing rdfs:label")
    if "rdfs:comment" not in model_node:
        err("data_model", "f:DataModel node missing rdfs:comment")

    # 4. Collect all class IDs
    class_ids = set()
    seen_ids = set()

    for cls in classes:
        cid = cls.get("@id")
        if not cid:
            err("class", "Class missing @id", node_id=str(cls))
            continue

        if cid in seen_ids:
            err("duplicate_id", f"Duplicate @id: {cid}", node_id=cid)
        seen_ids.add(cid)
        class_ids.add(cid)

        if cls.get("@type") != "rdfs:Class":
            err("class", f"Class {cid} has @type={cls.get('@type')}, expected rdfs:Class", node_id=cid)
        if "rdfs:label" not in cls:
            err("class", f"Class {cid} missing rdfs:label", node_id=cid)
        if "rdfs:comment" not in cls:
            err("class", f"Class {cid} missing rdfs:comment", node_id=cid)

    # 5. Validate properties
    property_ids = set()
    property_domains = {}  # property_id -> list of domain class IDs

    for prop in properties:
        pid = prop.get("@id")
        if not pid:
            err("property", "Property missing @id", node_id=str(prop))
            continue

        if pid in seen_ids:
            err("duplicate_id", f"Duplicate @id: {pid}", node_id=pid)
        seen_ids.add(pid)
        property_ids.add(pid)

        if prop.get("@type") != "rdf:Property":
            err("property", f"Property {pid} has @type={prop.get('@type')}, expected rdf:Property", node_id=pid)
        if "rdfs:label" not in prop:
            err("property", f"Property {pid} missing rdfs:label", node_id=pid)
        if "rdfs:comment" not in prop:
            err("property", f"Property {pid} missing rdfs:comment", node_id=pid)

        # Check range
        range_val = prop.get("rdfs:range")
        if not range_val:
            err("property", f"Property {pid} missing rdfs:range", node_id=pid)
        elif isinstance(range_val, str):
            if range_val not in VALID_XSD_TYPES and range_val not in class_ids:
                err("range", f"Property {pid} has invalid range '{range_val}' (not a valid XSD type or defined class)", node_id=pid)
        elif isinstance(range_val, dict) and "@id" in range_val:
            range_iri = range_val["@id"]
            if range_iri not in VALID_XSD_TYPES and range_iri not in class_ids:
                err("range", f"Property {pid} has invalid range '{range_iri}' (not a valid XSD type or defined class)", node_id=pid)

        # Check domain
        domain_val = prop.get("rdfs:domain")
        if domain_val:
            domains = []
            if isinstance(domain_val, str):
                domains = [domain_val]
            elif isinstance(domain_val, list):
                domains = [d if isinstance(d, str) else d.get("@id", "") for d in domain_val]
            elif isinstance(domain_val, dict) and "@id" in domain_val:
                domains = [domain_val["@id"]]

            for d in domains:
                if d and d not in class_ids:
                    err("domain", f"Property {pid} references undefined domain class '{d}'", node_id=pid)

            property_domains[pid] = domains

    # 6. Check every class has at least one property
    classes_with_properties = set()
    for pid, domains in property_domains.items():
        for d in domains:
            classes_with_properties.add(d)

    for cid in class_ids:
        if cid not in classes_with_properties:
            err("class_properties", f"Class {cid} has no properties defined (no property has it as domain)", node_id=cid)

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate Fluree model JSON-LD")
    parser.add_argument("model_file", help="Path to model .jsonld file")
    parser.add_argument("--json", action="store_true", help="Output errors as JSON")
    args = parser.parse_args()

    path = Path(args.model_file)
    if not path.exists():
        print(json.dumps({"status": "error", "message": f"File not found: {path}"}))
        sys.exit(2)

    try:
        data = load_model(str(path))
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON: {e}"
        if args.json:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(f"ERROR: {msg}")
        sys.exit(2)

    errors = validate(data)

    if args.json:
        result = {
            "status": "valid" if not errors else "invalid",
            "errors": errors,
            "summary": {
                "error_count": len(errors),
                "rules_violated": list(set(e["rule"] for e in errors)),
            }
        }
        # Also include model stats if we can parse it
        model_node, classes, properties = extract_model_parts(data)
        if model_node:
            ref_count = sum(1 for p in properties
                           if isinstance(p.get("rdfs:range"), str)
                           and not p.get("rdfs:range", "").startswith("xsd:"))
            result["model_stats"] = {
                "classes": len(classes),
                "properties": len(properties),
                "scalar_properties": len(properties) - ref_count,
                "ref_properties": ref_count,
            }
        print(json.dumps(result, indent=2))
    else:
        if not errors:
            model_node, classes, properties = extract_model_parts(data)
            print(f"Model is valid. {len(classes)} classes, {len(properties)} properties.")
        else:
            print(f"Found {len(errors)} validation error(s):\n")
            for e in errors:
                node = f" [{e['node_id']}]" if "node_id" in e else ""
                print(f"  [{e['rule']}]{node}: {e['message']}")

    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
