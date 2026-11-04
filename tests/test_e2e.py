import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
cli_pkg_dir = ROOT / "packages" / "cli"
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
SNAPSHOTS_DIR = ROOT / "tests" / "fixtures" / "snapshots"

import pytest
from purlwatch_cli.resolve import main, run_resolve


@pytest.mark.parametrize(
    ("sbom", "tar"),
    [
        ("node-app.cdx.json", "node-app.tar"),
        ("node-cli.cdx.json", "node-cli.tar"),
        ("rust-cli.cdx.json", "rust-cli.tar"),
        ("multi-dep.spdx.json", "multi-dep.tar"),
        ("purlwatch.cdx.json", "purlwatch.tar"),
    ],
)
def test_resolve_e2e_replay(tmp_path: Path, sbom: str, tar: str):
    ROOT = Path(__file__).resolve().parent.parent
    sbom_path = ROOT / "examples" / sbom
    tar_path = SNAPSHOTS_DIR / tar

    custom_cache = tmp_path / "cache"
    env = os.environ.copy()
    env["PURLWATCH_HASH_KEY"] = "replay-secret-test-key"
    env["PURLWATCH_CACHE_DIR"] = str(custom_cache)

    cmd = ["purlwatch", "resolve", "--sbom", str(sbom_path), "--offline", str(tar_path)]

    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env, cwd=ROOT, check=False
    )

    assert result.returncode == 0, (
        f"El comando falló con código {result.returncode}.\n"
        f"STDERR:\n{result.stderr}\n"
        f"STDOUT:\n{result.stdout}"
    )

    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    ("sbom", "tar"),
    [
        ("nested.cdx.json", "node-cli.tar"),
        ("no-purl.cdx.json", "node-cli.tar"),
    ],
)
def test_resolve_e2e_noroot_replay(tmp_path: Path, sbom: str, tar: str):
    ROOT = Path(__file__).resolve().parent.parent
    sbom_path = ROOT / "packages" / "core" / "tests" / "fixtures" / "sbom" / sbom
    tar_path = SNAPSHOTS_DIR / tar

    custom_cache = tmp_path / "cache"
    env = os.environ.copy()
    env["PURLWATCH_HASH_KEY"] = "replay-secret-test-key"
    env["PURLWATCH_CACHE_DIR"] = str(custom_cache)

    cmd = ["purlwatch", "resolve", "--sbom", str(sbom_path), "--offline", str(tar_path)]

    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env, cwd=ROOT, check=False
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
        "node-app.cdx.json",
        "node-cli.cdx.json",
        "rust-cli.cdx.json",
        "multi-dep.spdx.json",
        "purlwatch.cdx.json",
    ],
)
def test_resolve_e2e_collect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sbom: str
):
    ROOT = Path(__file__).resolve().parent.parent
    sbom_path = ROOT / "examples" / sbom

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    test_args = ["purlwatch", "resolve", "--sbom", str(sbom_path)]
    monkeypatch.setattr(sys, "argv", test_args)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0


@pytest.mark.vcr(record_mode="none")
@pytest.mark.parametrize(
    "sbom",
    [
        "spdx.json",
        "nested.cdx.json",
        "no-purl.cdx.json",
    ],
)
def test_resolve_e2e_noroot_collect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sbom: str
):
    ROOT = Path(__file__).resolve().parent.parent
    sbom_path = ROOT / "packages" / "core" / "tests" / "fixtures" / "sbom" / sbom

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    test_args = ["purlwatch", "resolve", "--sbom", str(sbom_path)]
    monkeypatch.setattr(sys, "argv", test_args)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0


def test_resolve_e2e_collect_error(tmp_path: Path):
    ROOT = Path(__file__).resolve().parent.parent
    bad_sbom = tmp_path / "bad.json"
    bad_sbom.write_text("{ json invalido")

    custom_cache = tmp_path / "cache"
    env = os.environ.copy()
    env["PURLWATCH_HASH_KEY"] = "replay-secret-test-key"
    env["PURLWATCH_CACHE_DIR"] = str(custom_cache)

    cmd = ["purlwatch", "resolve", "--sbom", str(bad_sbom)]

    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env, cwd=ROOT, check=False
    )

    assert result.returncode == 2


def test_resolve_e2e_offline_error(tmp_path: Path):
    ROOT = Path(__file__).resolve().parent.parent
    sbom = ROOT / "examples" / "node-cli.cdx.json"

    custom_cache = tmp_path / "cache"
    env = os.environ.copy()
    env["PURLWATCH_HASH_KEY"] = "replay-secret-test-key"
    env["PURLWATCH_CACHE_DIR"] = str(custom_cache)

    cmd = [
        "purlwatch",
        "resolve",
        "--sbom",
        str(sbom),
        "--offline",
        "examples/fixtures/node.tar",
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env, cwd=ROOT, check=False
    )

    assert result.returncode == 3


def schema_path(schema: str, path: Path) -> dict[str, Any]:
    schema = path / schema
    with open(schema, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize(
    ("sbom", "tar"),
    [
        ("node-app.cdx.json", "node-app.tar"),
        ("node-cli.cdx.json", "node-cli.tar"),
        ("rust-cli.cdx.json", "rust-cli.tar"),
        ("multi-dep.spdx.json", "multi-dep.tar"),
        ("purlwatch.cdx.json", "purlwatch.tar"),
    ],
)
def test_resolve_e2e_json_schema(tmp_path: Path, sbom: str, tar: str):
    ROOT = Path(__file__).resolve().parent.parent
    sbom_path = ROOT / "examples" / sbom
    tar_path = SNAPSHOTS_DIR / tar

    custom_cache = tmp_path / "cache"
    env = os.environ.copy()
    env["PURLWATCH_HASH_KEY"] = "replay-secret-test-key"
    env["PURLWATCH_CACHE_DIR"] = str(custom_cache)

    cmd = [
        "purlwatch",
        "resolve",
        "--sbom",
        str(sbom_path),
        "--offline",
        str(tar_path),
        "--json",
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env, cwd=ROOT, check=False
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

    assert "components" in output
    components_list = output.get("components")
    components_schema = schema_path("components.schema.json", SCHEMAS_DIR)
    for c in components_list:
        jsonschema.validate(instance=c, schema=components_schema)


MAPPING_SCHEMA = schema_path("mapping.schema.json", SCHEMAS_DIR)
HISTORY_SCHEMA = schema_path("publisher-history.schema.json", SCHEMAS_DIR)
GOLDEN = ROOT / "tests" / "golden"


@pytest.mark.parametrize(
    ("name", "sbom_type"),
    [
        ("node-cli", "cdx"),
        ("node-app", "cdx"),
        ("rust-cli", "cdx"),
        ("multi-dep", "spdx"),
        ("purlwatch", "cdx"),
    ],
)
def test_replay_matches_golden(
    name: str, sbom_type: str, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "test-key-in-ci")
    code = run_resolve(
        [
            "resolve",
            "--sbom",
            f"examples/{name}.{sbom_type}.json",
            "--offline",
            f"tests/fixtures/snapshots/{name}.tar",
            "--json",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0

    doc = json.loads(out)
    for row in doc["mapping"]:
        jsonschema.validate(row, MAPPING_SCHEMA)
    for row in doc["publisher_history"]:
        jsonschema.validate(row, HISTORY_SCHEMA)

    expected = (GOLDEN / f"{name}.json").read_text(encoding="utf-8")
    if os.getenv("UPDATE_GOLDEN"):
        (GOLDEN / f"{name}.json").write_text(out, encoding="utf-8", newline="\n")
    assert out == expected
