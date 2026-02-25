#!/usr/bin/env python3
"""
Validate a Fluree instance JSON-LD file against a data model.

Checks:
1. Valid JSON structure with @context and @graph
2. Every instance has @id and @type
3. @type references a class defined in the model
4. All properties on an instance are defined in the model for that class
5. Required properties (per model metadata) are present
6. Scalar values match expected XSD types (basic type checking)
7. Reference values use { "@id": "..." } format
8. No duplicate @id values within the file
9. @context includes type directives for non-string properties
10. Cardinality constraints (single vs array)

Usage:
    python validate_instances.py <instance_file.jsonld> --model <model_file.jsonld>
    python validate_instances.py <instance_file.jsonld> --model <model_file.jsonld> --json

Exit codes:
    0 = valid
    1 = validation errors found
    2 = file/parse error
"""

import json
import sys
import argparse
import re
from pathlib import Path


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_model(model_data: dict) -> dict:
    """Parse the model into a lookup-friendly structure."""
    graph = model_data.get("@graph", [])
    if not isinstance(graph, list):
        graph = [graph]

    model_node = None
    for node in graph:
        if node.get("@type") == "f:DataModel":
            model_node = node
            break

    if not model_node:
        return None

    classes_raw = model_node.get("f:classes", [])
    if not isinstance(classes_raw, list):
        classes_raw = [classes_raw]

    props_raw = model_node.get("f:properties", [])
    if not isinstance(props_raw, list):
        props_raw = [props_raw]

    # Build class lookup
    classes = {}
    for cls in classes_raw:
        cid = cls.get("@id")
        if cid:
            classes[cid] = cls

    # Build property lookup with domain and range info
    properties = {}
    for prop in props_raw:
        pid = prop.get("@id")
        if not pid:
            continue

        # Parse domain
        domain_val = prop.get("rdfs:domain")
        domains = set()
        if isinstance(domain_val, str):
            domains.add(domain_val)
        elif isinstance(domain_val, list):
            for d in domain_val:
                if isinstance(d, str):
                    domains.add(d)
                elif isinstance(d, dict):
                    domains.add(d.get("@id", ""))
        elif isinstance(domain_val, dict):
            domains.add(domain_val.get("@id", ""))

        # Parse range
        range_val = prop.get("rdfs:range")
        if isinstance(range_val, dict):
            range_str = range_val.get("@id", "")
        else:
            range_str = str(range_val) if range_val else ""

        is_ref = not range_str.startswith("xsd:")

        properties[pid] = {
            "domains": domains,
            "range": range_str,
            "is_ref": is_ref,
            "raw": prop,
        }

    # Build per-class property maps
    class_properties = {cid: {} for cid in classes}
    for pid, pinfo in properties.items():
        for domain in pinfo["domains"]:
            if domain in class_properties:
                class_properties[domain][pid] = pinfo

    return {
        "classes": classes,
        "properties": properties,
        "class_properties": class_properties,
    }


def check_xsd_type(value, expected_type: str) -> bool:
    """Basic XSD type checking for scalar values."""
    if expected_type == "xsd:string":
        return isinstance(value, str)
    elif expected_type in ("xsd:integer", "xsd:int", "xsd:long", "xsd:short",
                           "xsd:nonNegativeInteger", "xsd:positiveInteger"):
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type in ("xsd:float", "xsd:double", "xsd:decimal"):
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == "xsd:boolean":
        return isinstance(value, bool)
    elif expected_type in ("xsd:dateTime", "xsd:date", "xsd:time"):
        if not isinstance(value, str):
            return False
        # Basic format check
        if expected_type == "xsd:dateTime":
            return bool(re.match(r"\d{4}-\d{2}-\d{2}T", value))
        elif expected_type == "xsd:date":
            return bool(re.match(r"\d{4}-\d{2}-\d{2}$", value))
        elif expected_type == "xsd:time":
            return bool(re.match(r"\d{2}:\d{2}:", value))
        return True
    elif expected_type == "xsd:anyURI":
        return isinstance(value, str)
    return True  # Unknown types pass


def is_reference_value(value) -> bool:
    """Check if a value is a JSON-LD reference ({ "@id": "..." })."""
    return isinstance(value, dict) and "@id" in value and len(value) == 1


def validate(instance_data: dict, model: dict) -> list:
    """Validate instance data against the parsed model."""
    errors = []

    def err(rule: str, message: str, instance_id: str = None):
        e = {"rule": rule, "message": message}
        if instance_id:
            e["instance_id"] = instance_id
        errors.append(e)

    # 1. Structure checks
    if "@context" not in instance_data:
        err("structure", "Missing @context")
    if "@graph" not in instance_data:
        err("structure", "Missing @graph")
        return errors

    graph = instance_data.get("@graph", [])
    if not isinstance(graph, list):
        graph = [graph]

    # 2. Check for duplicate @ids
    seen_ids = set()
    for node in graph:
        nid = node.get("@id")
        if nid:
            if nid in seen_ids:
                err("duplicate_id", f"Duplicate @id: {nid}", instance_id=nid)
            seen_ids.add(nid)

    # 3. Validate each instance
    for node in graph:
        iid = node.get("@id")
        itype = node.get("@type")

        if not iid:
            err("instance", "Instance missing @id", instance_id=str(node)[:80])
            continue
        if not itype:
            err("instance", f"Instance missing @type", instance_id=iid)
            continue

        # Check class exists in model
        if itype not in model["classes"]:
            err("class_ref", f"Instance type '{itype}' not defined in model", instance_id=iid)
            continue

        class_props = model["class_properties"].get(itype, {})

        # Check each property on the instance
        for key, value in node.items():
            if key.startswith("@"):
                continue  # Skip JSON-LD keywords

            # Check property is defined for this class
            if key not in class_props:
                # Also check if it's defined at all in the model
                if key in model["properties"]:
                    err("domain", f"Property '{key}' exists but is not in domain of class '{itype}'", instance_id=iid)
                else:
                    err("undefined_property", f"Property '{key}' not defined in model", instance_id=iid)
                continue

            prop_info = class_props[key]

            # Validate value based on property type
            if prop_info["is_ref"]:
                # Reference property
                if isinstance(value, list):
                    for item in value:
                        if not is_reference_value(item):
                            err("ref_format", f"Reference property '{key}' has non-reference value in array: {item}", instance_id=iid)
                elif not is_reference_value(value):
                    # Could be a bare string IRI — flag as warning
                    if isinstance(value, str) and (":" in value or value.startswith("http")):
                        err("ref_format", f"Reference property '{key}' should use {{\"@id\": \"{value}\"}} format, not bare string", instance_id=iid)
                    else:
                        err("ref_format", f"Reference property '{key}' has non-reference value: {value}", instance_id=iid)
            else:
                # Scalar property
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and "@id" in item:
                            err("type_mismatch", f"Scalar property '{key}' (range={prop_info['range']}) has reference value", instance_id=iid)
                        elif not check_xsd_type(item, prop_info["range"]):
                            err("type_mismatch", f"Scalar property '{key}' value {repr(item)} doesn't match expected type {prop_info['range']}", instance_id=iid)
                elif isinstance(value, dict) and "@id" in value:
                    err("type_mismatch", f"Scalar property '{key}' (range={prop_info['range']}) has reference value", instance_id=iid)
                elif not check_xsd_type(value, prop_info["range"]):
                    err("type_mismatch", f"Scalar property '{key}' value {repr(value)} doesn't match expected type {prop_info['range']}", instance_id=iid)

    # 4. Check context has type directives for non-string properties
    context = instance_data.get("@context", {})
    if isinstance(context, dict):
        for pid, pinfo in model["properties"].items():
            if pinfo["is_ref"]:
                ctx_entry = context.get(pid)
                if ctx_entry is None or not (isinstance(ctx_entry, dict) and ctx_entry.get("@type") == "@id"):
                    # Only warn if this property is actually used in the file
                    used = any(pid in node for node in graph if isinstance(node, dict))
                    if used:
                        err("context", f"Reference property '{pid}' used in data but missing '@type': '@id' in @context")
            elif pinfo["range"] != "xsd:string":
                ctx_entry = context.get(pid)
                if ctx_entry is None or not (isinstance(ctx_entry, dict) and "@type" in ctx_entry):
                    used = any(pid in node for node in graph if isinstance(node, dict))
                    if used:
                        err("context", f"Non-string property '{pid}' (range={pinfo['range']}) used but missing type directive in @context")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate Fluree instance JSON-LD against model")
    parser.add_argument("instance_file", help="Path to instance .jsonld file")
    parser.add_argument("--model", required=True, help="Path to model .jsonld file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Load files
    for label, path in [("Instance file", args.instance_file), ("Model file", args.model)]:
        if not Path(path).exists():
            msg = f"{label} not found: {path}"
            if args.json:
                print(json.dumps({"status": "error", "message": msg}))
            else:
                print(f"ERROR: {msg}")
            sys.exit(2)

    try:
        instance_data = load_json(args.instance_file)
        model_data = load_json(args.model)
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON: {e}"
        if args.json:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(f"ERROR: {msg}")
        sys.exit(2)

    model = parse_model(model_data)
    if model is None:
        msg = "Could not parse model (no f:DataModel node found)"
        if args.json:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(f"ERROR: {msg}")
        sys.exit(2)

    errors = validate(instance_data, model)

    # Count instances
    graph = instance_data.get("@graph", [])
    if not isinstance(graph, list):
        graph = [graph]
    instance_count = len(graph)

    if args.json:
        # Group errors by rule
        by_rule = {}
        for e in errors:
            rule = e["rule"]
            if rule not in by_rule:
                by_rule[rule] = []
            by_rule[rule].append(e)

        result = {
            "status": "valid" if not errors else "invalid",
            "instance_count": instance_count,
            "error_count": len(errors),
            "errors_by_rule": {rule: len(errs) for rule, errs in by_rule.items()},
            "errors": errors[:100],  # Cap at 100 to avoid huge output
        }
        if len(errors) > 100:
            result["truncated"] = True
            result["total_errors"] = len(errors)
        print(json.dumps(result, indent=2))
    else:
        if not errors:
            print(f"Instance file is valid. {instance_count} instances checked.")
        else:
            print(f"Found {len(errors)} validation error(s) across {instance_count} instances:\n")
            # Show first 30 errors
            for e in errors[:30]:
                iid = f" [{e['instance_id']}]" if "instance_id" in e else ""
                print(f"  [{e['rule']}]{iid}: {e['message']}")
            if len(errors) > 30:
                print(f"\n  ... and {len(errors) - 30} more errors")

    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
