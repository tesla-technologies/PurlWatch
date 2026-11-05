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
from purlwatch_cli.resolve import run_resolve


@pytest.mark.parametrize(
    ("sbom", "tar"),
    [
        ("nested.cdx.json", "node-cli.tar"),
        ("no-purl.cdx.json", "node-cli.tar"),
    ],
)
def test_resolve_e2e_noroot_replay(tmp_path: Path, sbom: str, tar: str, capsys):
    ROOT = Path(__file__).resolve().parent.parent
    sbom_path = ROOT / "packages" / "core" / "tests" / "fixtures" / "sbom" / sbom
    tar_path = SNAPSHOTS_DIR / tar

    custom_cache = tmp_path / "cache"
    env = os.environ.copy()
    env["PURLWATCH_HASH_KEY"] = "replay-secret-test-key"
    env["PURLWATCH_CACHE_DIR"] = str(custom_cache)

    argv = ["resolve", "--sbom", str(sbom_path), "--offline", str(tar_path)]

    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 0, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )

    assert "Traceback" not in captured.err

    out = captured.out
    assert out.strip()


@pytest.mark.vcr(record_mode="none")
@pytest.mark.parametrize(
    "sbom",
    [
        "node-app.cdx.json",
        "node-cli.cdx.json",
        "rust-cli.cdx.json",
        "multi-dep.spdx.json",
        "purlwatch.cdx.json",
        "sources.cdx.json",
    ],
)
def test_resolve_e2e_collect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sbom: str, capsys
):
    ROOT = Path(__file__).resolve().parent.parent
    sbom_path = ROOT / "examples" / sbom

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    argv = ["resolve", "--sbom", str(sbom_path)]
    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 0, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )

    out = captured.out
    assert out.strip()


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
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sbom: str, capsys
):
    ROOT = Path(__file__).resolve().parent.parent
    sbom_path = ROOT / "packages" / "core" / "tests" / "fixtures" / "sbom" / sbom

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    argv = ["resolve", "--sbom", str(sbom_path)]
    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 0, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )

    out = captured.out
    assert out.strip()


def test_resolve_e2e_collect_error(tmp_path: Path, capsys):
    bad_sbom = tmp_path / "bad.json"
    bad_sbom.write_text("{ json invalido")

    custom_cache = tmp_path / "cache"
    env = os.environ.copy()
    env["PURLWATCH_HASH_KEY"] = "replay-secret-test-key"
    env["PURLWATCH_CACHE_DIR"] = str(custom_cache)

    argv = ["resolve", "--sbom", str(bad_sbom)]

    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 2, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )


def test_resolve_e2e_offline_error(tmp_path: Path, capsys):
    ROOT = Path(__file__).resolve().parent.parent
    sbom = ROOT / "examples" / "node-cli.cdx.json"

    custom_cache = tmp_path / "cache"
    env = os.environ.copy()
    env["PURLWATCH_HASH_KEY"] = "replay-secret-test-key"
    env["PURLWATCH_CACHE_DIR"] = str(custom_cache)

    argv = [
        "resolve",
        "--sbom",
        str(sbom),
        "--offline",
        "examples/fixtures/node.tar",
    ]

    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 2, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )


def test_resolve_e2e_replay_subprocess(tmp_path: Path):
    ROOT = Path(__file__).resolve().parent.parent
    sbom_path = ROOT / "examples" / "node-cli.cdx.json"
    tar_path = SNAPSHOTS_DIR / "node-cli.tar"

    bin = Path(sys.executable).with_name("purlwatch")
    assert bin.exists(), f"Executable was not found at: {bin}"

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
    assert result.stdout.strip()


def schema_path(schema: str, path: Path) -> dict[str, Any]:
    schema = path / schema
    with open(schema, "r", encoding="utf-8") as f:
        return json.load(f)


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
        ("sources", "cdx"),
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
