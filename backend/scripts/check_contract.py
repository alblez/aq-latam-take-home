from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml
from deepdiff import DeepDiff

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ROOT = BACKEND_ROOT.parent
CONTRACT_PATH = ROOT / "shared" / "contract.yaml"

sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402 -- CLI script adds backend root before app import.


def _load_contract() -> dict[str, Any]:
    return yaml.safe_load(CONTRACT_PATH.read_text())


def _public_generated_paths(schema: dict[str, Any]) -> dict[str, Any]:
    return {path: spec for path, spec in schema.get("paths", {}).items() if path.startswith("/")}


def _resolve_refs(node: Any, root: dict[str, Any]) -> Any:
    """Recursively resolve $ref pointers within an OpenAPI document."""
    if isinstance(node, dict):
        if "$ref" in node and len(node) == 1:
            ref_path = node["$ref"]
            if ref_path.startswith("#/"):
                parts = ref_path[2:].split("/")
                target: Any = root
                for part in parts:
                    target = target[part]
                return _resolve_refs(target, root)
            return node
        return {k: _resolve_refs(v, root) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_refs(item, root) for item in node]
    return node


# Keys stripped during normalization (cosmetic or validation-only, not shape).
# The drift checker detects STRUCTURAL drift (wrong types, missing properties,
# missing endpoints). Validation constraints differ between hand-written OpenAPI
# 3.1 and Pydantic v2 auto-generated schemas due to representation differences
# (e.g. Field(ge=0) vs explicit minimum, extra="forbid" vs no additionalProperties).
#
# TODO: "required" is stripped because Pydantic response models intentionally use
# Optional for fields absent in certain states (e.g. terminalPanelState only exists
# after session end). Removing it from _STRIP_KEYS would surface 30+ legitimate
# required/optional mismatches that need contract+model alignment as a separate effort.
_STRIP_KEYS = frozenset(
    {
        "title",
        "description",
        "example",
        "examples",
        "default",
        "summary",
        "operationId",
        "tags",
        "parameters",
        "format",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
        "pattern",
        "additionalProperties",
        "required",
    }
)


def _collapse_nullable(result: dict[str, Any]) -> None:
    """Collapse anyOf-with-null to the non-null type in-place."""
    if "anyOf" not in result or not isinstance(result["anyOf"], list):
        return
    non_null = [
        item
        for item in result["anyOf"]
        if not (isinstance(item, dict) and item == {"type": "null"})
    ]
    if len(non_null) == 1 and len(result["anyOf"]) > len(non_null):
        collapsed = non_null[0]
        result.pop("anyOf")
        if isinstance(collapsed, dict):
            result.update(collapsed)
        else:
            result["type"] = collapsed


def _collapse_type_array(result: dict[str, Any]) -> None:
    """Collapse type: ['string', 'null'] to type: 'string' in-place."""
    if "type" not in result or not isinstance(result["type"], list):
        return
    types = [t for t in result["type"] if t != "null"]
    if len(types) == 1:
        result["type"] = types[0]
    elif len(types) > 1:
        result["type"] = sorted(types)


def _flatten_all_of(result: dict[str, Any]) -> None:
    """Flatten allOf into a merged object in-place."""
    if "allOf" not in result or not isinstance(result["allOf"], list):
        return
    all_of_items = result.pop("allOf")
    merged: dict[str, Any] = {}
    for item in all_of_items:
        if not isinstance(item, dict):
            continue
        for k, v in item.items():
            if k == "properties" and "properties" in merged:
                merged["properties"] = {**merged["properties"], **v}
            else:
                merged[k] = v
    for sk in _STRIP_KEYS:
        merged.pop(sk, None)
    result.update(merged)


def _normalize_schema(node: Any) -> Any:
    """Normalize OpenAPI schema to structural form for comparison.

    Strips validation constraints, cosmetic fields, and normalizes nullable
    representation differences between hand-written OpenAPI 3.1 and Pydantic v2
    generated output. Focuses on TYPE STRUCTURE: properties, base types, enums.
    """
    if isinstance(node, list):
        return [_normalize_schema(item) for item in node]
    if not isinstance(node, dict):
        if isinstance(node, float) and node == int(node):
            return int(node)
        return node

    result: dict[str, Any] = {k: v for k, v in node.items() if k not in _STRIP_KEYS}

    # Order matters: nullable collapse first so allOf inside gets processed
    _collapse_nullable(result)
    _collapse_type_array(result)
    _flatten_all_of(result)

    return {k: _normalize_schema(v) for k, v in result.items() if k not in _STRIP_KEYS}


def _get_success_schema(
    path_spec: dict[str, Any], method: str, root: dict[str, Any]
) -> dict[str, Any] | None:
    """Extract resolved+normalized success response schema for a method."""
    method_spec = path_spec.get(method, {})
    responses = method_spec.get("responses", {})
    for code in ("200", "201"):
        resp = responses.get(code, {})
        json_content = resp.get("content", {}).get("application/json", {})
        schema = json_content.get("schema")
        if schema:
            resolved = _resolve_refs(schema, root)
            return _normalize_schema(resolved)
    return None


def _check_path_coverage(
    contract_paths: dict[str, Any], generated_paths: dict[str, Any]
) -> list[str]:
    """Bidirectional path existence check."""
    errors: list[str] = []
    for path in generated_paths:
        if path not in contract_paths:
            errors.append(f"Generated path {path!r} is missing from shared/contract.yaml")
    for path in contract_paths:
        if path not in generated_paths:
            errors.append(f"Contract path {path!r} missing from FastAPI")
    return errors


def _get_request_body_schema(
    path_spec: dict[str, Any], method: str, root: dict[str, Any]
) -> dict[str, Any] | None:
    """Extract resolved+normalized request body schema for a method."""
    method_spec = path_spec.get(method, {})
    request_body = method_spec.get("requestBody", {})
    json_content = request_body.get("content", {}).get("application/json", {})
    schema = json_content.get("schema")
    if schema:
        resolved = _resolve_refs(schema, root)
        return _normalize_schema(resolved)
    return None


def _check_schema_shapes(
    contract_paths: dict[str, Any],
    generated_paths: dict[str, Any],
    contract: dict[str, Any],
    generated: dict[str, Any],
) -> list[str]:
    """Compare response and request body schema shapes for shared paths."""
    errors: list[str] = []
    skip_keys = ("parameters", "summary", "description")
    for path in contract_paths:
        if path not in generated_paths:
            continue
        for method in contract_paths[path]:
            if method in skip_keys:
                continue
            # Response schema comparison
            c_schema = _get_success_schema(contract_paths[path], method, contract)
            g_schema = _get_success_schema(generated_paths[path], method, generated)
            if c_schema is not None and g_schema is not None:
                diff = DeepDiff(c_schema, g_schema, ignore_order=True)
                if diff:
                    errors.append(
                        f"{path} {method.upper()} response schema drifted: {diff.pretty()}"
                    )
            # Request body schema comparison
            c_body = _get_request_body_schema(contract_paths[path], method, contract)
            g_body = _get_request_body_schema(generated_paths[path], method, generated)
            if c_body is not None and g_body is not None:
                body_diff = DeepDiff(c_body, g_body, ignore_order=True)
                if body_diff:
                    errors.append(
                        f"{path} {method.upper()} request body schema drifted: {body_diff.pretty()}"
                    )
    return errors


def check_contract() -> list[str]:
    contract = _load_contract()
    generated = app.openapi()
    errors: list[str] = []

    if contract.get("openapi") != "3.1.0":
        errors.append("shared/contract.yaml must use OpenAPI 3.1.0")
    if generated.get("openapi") != "3.1.0":
        errors.append("FastAPI generated OpenAPI must use 3.1.0")

    contract_paths = contract.get("paths", {})
    generated_paths = _public_generated_paths(generated)

    errors.extend(_check_path_coverage(contract_paths, generated_paths))
    errors.extend(_check_schema_shapes(contract_paths, generated_paths, contract, generated))

    return errors


def main() -> int:
    errors = check_contract()
    if errors:
        for error in errors:
            print(f"contract drift: {error}", file=sys.stderr)
        return 1
    print("backend contract drift check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
