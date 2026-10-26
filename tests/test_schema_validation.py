import json
from pathlib import Path
from typing import Any

import jsonschema
import pytest

TEST_DIR = Path(__file__).parent
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def schema_path(schema: str, path: Path) -> dict[str, Any]:
    schema = path / schema
    with open(schema, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize(
    ("data", "schema_json"),
    [
        (
            schema_path("valid_mapping.json", FIXTURES_DIR),
            schema_path("mapping.schema.json", SCHEMAS_DIR),
        ),
        (
            schema_path("valid_history.json", FIXTURES_DIR),
            schema_path("publisher-history.schema.json", SCHEMAS_DIR),
        ),
    ],
)
def test_validate_schema(data: dict[str, Any], schema_json: dict[str, Any]) -> None:
    assert jsonschema.validate(instance=data, schema=schema_json) is None


@pytest.mark.parametrize(
    ("data", "schema_json"),
    [
        (
            schema_path("invalid_mapping1.json", FIXTURES_DIR),
            schema_path("mapping.schema.json", SCHEMAS_DIR),
        ),
        (
            schema_path("invalid_mapping2.json", FIXTURES_DIR),
            schema_path("mapping.schema.json", SCHEMAS_DIR),
        ),
        (
            schema_path("invalid_history1.json", FIXTURES_DIR),
            schema_path("publisher-history.schema.json", SCHEMAS_DIR),
        ),
        (
            schema_path("invalid_history2.json", FIXTURES_DIR),
            schema_path("publisher-history.schema.json", SCHEMAS_DIR),
        ),
    ],
)
def test_invalid_schema_raises_error(
    data: dict[str, Any], schema_json: dict[str, Any]
) -> None:
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=data, schema=schema_json)
