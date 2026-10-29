"""Export the shared Pydantic contract catalog as JSON Schema and TypeScript."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.contracts.challenge.v1 import CONTRACT_VERSION, ContractCatalog


def _type_for(schema: dict[str, Any]) -> str:
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if "const" in schema:
        return json.dumps(schema["const"], ensure_ascii=False)
    if "enum" in schema:
        return " | ".join(json.dumps(value, ensure_ascii=False) for value in schema["enum"])
    for union_key in ("anyOf", "oneOf"):
        if union_key in schema:
            members = sorted({_type_for(item) for item in schema[union_key]})
            return " | ".join(members)
    if "allOf" in schema:
        return " & ".join(_type_for(item) for item in schema["allOf"])
    kind = schema.get("type")
    if isinstance(kind, list):
        return " | ".join(sorted({_type_for({**schema, "type": item}) for item in kind}))
    if kind == "array":
        item_type = _type_for(schema.get("items", {}))
        if " | " in item_type or " & " in item_type:
            item_type = f"({item_type})"
        return f"{item_type}[]"
    if kind == "object" or "properties" in schema:
        properties = schema.get("properties")
        if properties:
            return "{ " + "; ".join(
                f"{name}{'' if name in schema.get('required', []) else '?'}: {_type_for(value)}"
                for name, value in sorted(properties.items())
            ) + " }"
        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            return f"Record<string, {_type_for(additional)}>"
        return "Record<string, JsonValue>"
    if kind == "string":
        return "string"
    if kind in {"number", "integer"}:
        return "number"
    if kind == "boolean":
        return "boolean"
    if kind == "null":
        return "null"
    return "JsonValue"


def _typescript(schema: dict[str, Any]) -> str:
    lines = [
        "/* Generated from backend/app/contracts/challenge/v1.py. Do not edit by hand. */",
        f'export const CHALLENGE_CONTRACT_VERSION = "{CONTRACT_VERSION}" as const;',
        "export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };",
        "",
    ]
    for name, definition in sorted(schema.get("$defs", {}).items()):
        lines.append(f"export type {name} = {_type_for(definition)};")
    return "\n".join(lines) + "\n"


def generated_artifacts(backend_root: Path) -> dict[Path, str]:
    schema = ContractCatalog.model_json_schema(ref_template="#/$defs/{model}")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://fieldshiftbd.dev/contracts/challenge-v1.schema.json"
    schema_text = json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return {
        backend_root / "contracts" / "jsonschema" / "challenge-v1.schema.json": schema_text,
        backend_root.parent / "frontend" / "src" / "modules" / "shared" / "contracts.generated.ts": _typescript(schema),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated artifacts are stale")
    args = parser.parse_args()
    backend_root = BACKEND_ROOT
    mismatches = []
    for path, contents in generated_artifacts(backend_root).items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != contents:
                mismatches.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8", newline="\n")
    if mismatches:
        print("Generated contract artifacts are stale:")
        for path in mismatches:
            print(f" - {path.relative_to(backend_root.parent).as_posix()}")
        print("Run: python scripts/export_challenge_contracts.py")
        return 1
    print("Challenge JSON Schema and TypeScript artifacts are current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
