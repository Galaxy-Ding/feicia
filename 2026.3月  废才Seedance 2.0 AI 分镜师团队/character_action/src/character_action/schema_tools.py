from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
}


class SchemaValidationError(ValueError):
    pass


class SchemaValidator:
    def __init__(self, schemas_root: Path) -> None:
        self.schemas_root = schemas_root

    def validate(self, schema_name: str, payload: dict[str, Any]) -> None:
        schema = json.loads((self.schemas_root / schema_name).read_text(encoding="utf-8"))
        self._validate_node(payload, schema, path=schema_name)

    def _validate_node(self, value: Any, schema: dict[str, Any], *, path: str) -> None:
        schema_type = schema.get("type")
        if schema_type:
            expected = _TYPE_MAP[schema_type]
            if not isinstance(value, expected) or (schema_type == "integer" and isinstance(value, bool)):
                raise SchemaValidationError(f"{path} expected {schema_type}, got {type(value).__name__}")
        if "enum" in schema and value not in schema["enum"]:
            raise SchemaValidationError(f"{path} expected one of {schema['enum']}, got {value!r}")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in schema and value < schema["minimum"]:
                raise SchemaValidationError(f"{path} expected >= {schema['minimum']}, got {value}")
            if "maximum" in schema and value > schema["maximum"]:
                raise SchemaValidationError(f"{path} expected <= {schema['maximum']}, got {value}")
        if isinstance(value, dict):
            for required in schema.get("required", []):
                if required not in value:
                    raise SchemaValidationError(f"{path} missing required field {required}")
            properties = schema.get("properties", {})
            for key, child in value.items():
                if key in properties:
                    self._validate_node(child, properties[key], path=f"{path}.{key}")
        if isinstance(value, list) and "items" in schema:
            for index, item in enumerate(value):
                self._validate_node(item, schema["items"], path=f"{path}[{index}]")
