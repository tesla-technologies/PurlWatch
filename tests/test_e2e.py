import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import jsonschema

root_dir = Path(__file__).resolve().parent.parent
cli_pkg_dir = root_dir / "packages" / "cli"
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"

if str(cli_pkg_dir) not in sys.path:
    sys.path.insert(0, str(cli_pkg_dir))

import pytest
from auratrace_cli.resolve import (
    main,
)


@pytest.mark.parametrize(
    ("sbom", "tar"),
    [
        ("node-web-app.cdx.json", "node-web-app.tar"),
        ("node-cli.cdx.json", "node-cli.tar"),
        ("rust-cli.cdx.json", "rust-cli.tar"),
    ],
)
def test_resolve_e2e_replay(tmp_path: Path, sbom: str, tar: str):
    root_dir = Path(__file__).resolve().parent.parent
    sbom_path = root_dir / "examples" / sbom
    tar_path = root_dir / "tests" / "fixtures" / tar

    custom_cache = tmp_path / "cache"
    env = os.environ.copy()
    env["AURATRACE_HASH_KEY"] = "replay-secret-test-key"
    env["AURATRACE_CACHE_DIR"] = str(custom_cache)

    cmd = ["auratrace", "resolve", "--sbom", str(sbom_path), "--offline", str(tar_path)]

    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env, cwd=root_dir, check=False
    )

    assert result.returncode == 0, (
        f"El comando falló con código {result.returncode}.\n"
        f"STDERR:\n{result.stderr}\n"
        f"STDOUT:\n{result.stdout}"
    )

    assert "Traceback" not in result.stderr


@pytest.mark.vcr(record_mode="none")
@pytest.mark.parametrize(
    "sbom",
    [
        "node-web-app.cdx.json",
        "node-cli.cdx.json",
        "rust-cli.cdx.json",
    ],
)
def test_resolve_e2e_collect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sbom: str
):
    root_dir = Path(__file__).resolve().parent.parent
    sbom_path = root_dir / "examples" / sbom

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("AURATRACE_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("AURATRACE_CACHE_DIR", str(custom_cache))

    test_args = ["auratrace", "resolve", "--sbom", str(sbom_path)]
    monkeypatch.setattr(sys, "argv", test_args)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0


def test_resolve_e2e_collect_error(tmp_path: Path):
    root_dir = Path(__file__).resolve().parent.parent
    bad_sbom = tmp_path / "bad.json"
    bad_sbom.write_text("{ json invalido")

    custom_cache = tmp_path / "cache"
    env = os.environ.copy()
    env["AURATRACE_HASH_KEY"] = "replay-secret-test-key"
    env["AURATRACE_CACHE_DIR"] = str(custom_cache)

    cmd = ["auratrace", "resolve", "--sbom", str(bad_sbom)]

    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env, cwd=root_dir, check=False
    )

    assert result.returncode == 2


def schema_path(schema: str, path: Path) -> dict[str, Any]:
    schema = path / schema
    with open(schema, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize(
    ("sbom", "tar"),
    [
        ("node-web-app.cdx.json", "node-web-app.tar"),
        ("node-cli.cdx.json", "node-cli.tar"),
        ("rust-cli.cdx.json", "rust-cli.tar"),
    ],
)
def test_resolve_e2e_json_schema(tmp_path: Path, sbom: str, tar: str):
    root_dir = Path(__file__).resolve().parent.parent
    sbom_path = root_dir / "examples" / sbom
    tar_path = root_dir / "tests" / "fixtures" / tar

    custom_cache = tmp_path / "cache"
    env = os.environ.copy()
    env["AURATRACE_HASH_KEY"] = "replay-secret-test-key"
    env["AURATRACE_CACHE_DIR"] = str(custom_cache)

    cmd = [
        "auratrace",
        "resolve",
        "--sbom",
        str(sbom_path),
        "--offline",
        str(tar_path),
        "--json",
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env, cwd=root_dir, check=False
    )

    assert result.returncode == 0

    output = json.loads(result.stdout)

    assert "mapping" in output
    mapping_list = output.get("mapping")
    map_schema = schema_path("mapping.schema.json", SCHEMAS_DIR)
    for m in mapping_list:
        jsonschema.validate(instance=m, schema=map_schema)

    assert "publisher_history" in output
    history_list = output.get("publisher_history")
    history_schema = schema_path("publisher-history.schema.json", SCHEMAS_DIR)
    for h in history_list:
        jsonschema.validate(instance=h, schema=history_schema)
