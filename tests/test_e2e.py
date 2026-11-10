import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import jsonschema

ROOT = Path(__file__).resolve().parent.parent
cli_pkg_dir = ROOT / "packages" / "cli"
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
SNAPSHOTS_DIR = ROOT / "tests" / "fixtures" / "snapshots"

import pytest
from purlwatch_cli import resolve
from purlwatch_cli.resolve import run_resolve


@pytest.fixture
def time_patcher(monkeypatch: pytest.MonkeyPatch):
    virtual_time = 1000.0

    def fake_sleep(seconds: float) -> None:
        nonlocal virtual_time
        virtual_time += max(0.0, float(seconds))

    def fake_monotonic() -> float:
        nonlocal virtual_time
        return virtual_time

    monkeypatch.setattr("time.sleep", fake_sleep)
    monkeypatch.setattr("time.monotonic", fake_monotonic)


@pytest.mark.parametrize(
    ("sbom", "tar"),
    [
        ("nested.cdx.json", "node-cli.tar"),
        ("no-purl.cdx.json", "node-cli.tar"),
    ],
)
def test_resolve_e2e_noroot_replay(
    tmp_path: Path, sbom: str, tar: str, monkeypatch: pytest.MonkeyPatch, capsys
):
    ROOT = Path(__file__).resolve().parent.parent
    sbom_path = ROOT / "packages" / "core" / "tests" / "fixtures" / "sbom" / sbom
    tar_path = SNAPSHOTS_DIR / tar

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

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


def test_resolve_e2e_noroot_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    ROOT = Path(__file__).resolve().parent.parent
    sbom_path = (
        ROOT / "packages" / "core" / "tests" / "fixtures" / "sbom" / "nested.cdx.json"
    )
    tar_path = SNAPSHOTS_DIR / "node-cli.tar"

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

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
    assert (
        out.count(
            "[WARN] Evaluated SBOM has no root component, depth cannot be calculated\n"
        )
        == 1
    )
    assert out.count("[WARN] Unreachable component") == 0


@pytest.mark.usefixtures("time_patcher")
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


@pytest.mark.usefixtures("time_patcher")
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


def test_resolve_e2e_collect_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    bad_sbom = tmp_path / "bad.json"
    bad_sbom.write_text("{ json invalido")

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    argv = ["resolve", "--sbom", str(bad_sbom)]

    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 2, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )
    assert "purlwatch: File is not a valid JSON" in captured.err.strip()


def test_resolve_e2e_offline_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    ROOT = Path(__file__).resolve().parent.parent
    sbom = ROOT / "examples" / "node-cli.cdx.json"

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

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
    assert "purlwatch: File was not found for tar" in captured.err.strip()


def test_resolve_e2e_missing_hash_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    ROOT = Path(__file__).resolve().parent.parent
    sbom = ROOT / "examples" / "node-cli.cdx.json"

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    argv = [
        "resolve",
        "--sbom",
        str(sbom),
        "--offline",
        "tests/fixtures/snapshots/node-cli.tar",
    ]

    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 2, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )
    assert (
        captured.err.strip()
        == "purlwatch: Environment variable PURLWATCH_HASH_KEY is empty or not found."
    )


def test_resolve_e2e_wrong_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    ROOT = Path(__file__).resolve().parent.parent
    sbom = (
        ROOT
        / "packages"
        / "core"
        / "tests"
        / "fixtures"
        / "sbom"
        / "wrong-version.cdx.json"
    )

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    argv = ["resolve", "--sbom", str(sbom)]

    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 2, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )
    assert "purlwatch: SBOM format or version is not supported" in captured.err.strip()


def test_resolve_e2e_brokenpipe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    ROOT = Path(__file__).resolve().parent.parent
    sbom = ROOT / "examples" / "node-app.cdx.json"
    tar_path = SNAPSHOTS_DIR / "node-app.tar"

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    argv = ["resolve", "--sbom", str(sbom), "--offline", str(tar_path)]

    writes_count = 0

    def fake_write(text: str) -> int:
        nonlocal writes_count
        writes_count += 1
        if writes_count > 10:
            raise BrokenPipeError
        return len(text)

    with (
        patch("sys.stdout.write", side_effect=fake_write),
        patch.object(sys.stdout, "fileno", return_value=1),
        patch("os.dup2"),
    ):
        result = run_resolve(argv)
        assert result == 0


def test_resolve_e2e_bad_encoding_sbom(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    ROOT = Path(__file__).resolve().parent.parent
    sbom = ROOT / "examples" / "node-cli.cdx.json"
    original = sbom.read_text(encoding="utf-8")
    binary_sbom = tmp_path / "sbom.cdx.bin"
    binary_sbom.write_bytes(original.encode("utf-16"))

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    argv = ["resolve", "--sbom", str(binary_sbom)]

    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 2, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )
    assert (
        "purlwatch: Failed to read SBOM as UTF-8: the file appears to be binary or uses an unsupported encoding"
        in captured.err.strip()
    )


def test_resolve_e2e_sbom_is_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    ROOT = Path(__file__).resolve().parent.parent
    sbom = ROOT / "packages" / "core" / "tests" / "fixtures" / "sbom"

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    argv = ["resolve", "--sbom", str(sbom)]

    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 2, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )
    assert (
        "purlwatch: Expected an SBOM file, but received a directory:"
        in captured.err.strip()
    )


def test_resolve_e2e_unreadable_purl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    ROOT = Path(__file__).resolve().parent.parent
    sbom = ROOT / "tests" / "fixtures" / "unreadable-sbom.json"

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    argv = ["resolve", "--sbom", str(sbom)]

    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 2, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )
    assert "purlwatch: PURL string supplied does not parse" in captured.err.strip()


def test_resolve_e2e_no_sbom(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    ROOT = Path(__file__).resolve().parent.parent
    sbom = ROOT / "tests" / "fixtures" / "no_sbom.json"

    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    argv = ["resolve", "--sbom", str(sbom)]

    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 2, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )
    assert "SBOM file not found" in captured.err.strip()


def test_resolve_e2e_offline_key_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    sbom = ROOT / "examples" / "node-cli.cdx.json"
    tar_path = ROOT / "tests" / "fixtures" / "snapshots" / "node-cli.tar"

    extract_dir = tmp_path / "extracted"
    with tarfile.open(tar_path, "r") as tar:
        tar.extractall(extract_dir)

    json_file = extract_dir / "index.json"
    data = json.loads(json_file.read_text(encoding="utf-8"))

    data = [doc for doc in data if "commander" not in doc.get("path", "")]

    json_file.write_text(json.dumps(data), encoding="utf-8")

    corrupt_tar = tmp_path / "corrupt_node_cli.tar"
    with tarfile.open(corrupt_tar, "w") as tar:
        for item in extract_dir.iterdir():
            tar.add(item, arcname=item.name)

    argv = [
        "resolve",
        "--sbom",
        str(sbom),
        "--offline",
        str(corrupt_tar),
    ]

    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 3, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )


def test_resolve_e2e_wrong_index_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    sbom = ROOT / "examples" / "node-cli.cdx.json"
    tar_path = ROOT / "tests" / "fixtures" / "snapshots" / "node-cli.tar"

    extract_dir = tmp_path / "extracted"
    with tarfile.open(tar_path, "r") as tar:
        tar.extractall(extract_dir)

    json_file = extract_dir / "index.json"
    json_file.write_text("{", encoding="utf-8")

    corrupt_tar = tmp_path / "corrupt_node_cli.tar"
    with tarfile.open(corrupt_tar, "w") as tar:
        for item in extract_dir.iterdir():
            tar.add(item, arcname=item.name)

    argv = [
        "resolve",
        "--sbom",
        str(sbom),
        "--offline",
        str(corrupt_tar),
    ]

    result = run_resolve(argv)
    captured = capsys.readouterr()

    assert result == 2, (
        f"Command failed with exit code: {result}.\n"
        f"STDERR:\n{captured.err}\n"
        f"STDOUT:\n{captured.out}"
    )
    assert "Snapshot is corrupt" in captured.err.strip()


def test_resolve_e2e_replay_subprocess(tmp_path: Path):
    ROOT = Path(__file__).resolve().parent.parent
    sbom_path = ROOT / "examples" / "node-cli.cdx.json"
    tar_path = SNAPSHOTS_DIR / "node-cli.tar"

    scripts_dir = str(Path(sys.executable).parent)
    bin_path = shutil.which("purlwatch", path=scripts_dir)
    assert bin_path is not None, (
        f"Executable 'purlwatch' was not found in: {scripts_dir}"
    )

    custom_cache = tmp_path / "cache"
    env = os.environ.copy()
    env["PURLWATCH_HASH_KEY"] = "replay-secret-test-key"
    env["PURLWATCH_CACHE_DIR"] = str(custom_cache)

    cmd = [bin_path, "resolve", "--sbom", str(sbom_path), "--offline", str(tar_path)]

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
COMPONENTS_SCHEMA = schema_path("components.schema.json", SCHEMAS_DIR)
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
    for row in doc["components"]:
        jsonschema.validate(row, COMPONENTS_SCHEMA)

    expected = (GOLDEN / f"{name}.json").read_text(encoding="utf-8")
    if os.getenv("UPDATE_GOLDEN"):
        (GOLDEN / f"{name}.json").write_text(out, encoding="utf-8", newline="\n")
    assert out == expected


@pytest.mark.parametrize(
    ("scenario", "exit_code", "expected_attempts", "expected_sleeps"),
    [
        ("503_persistent", 4, 4, [1.0, 2.0, 4.0]),
        ("429_then_200", 0, 4, [1.0, 1.0]),
        ("connect_error", 4, 4, None),
    ],
)
def test_resolve_e2e_online_errors(
    scenario: str,
    exit_code: int,
    expected_attempts: int,
    expected_sleeps: list[float] | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    custom_cache = tmp_path / "cache"
    monkeypatch.setenv("PURLWATCH_HASH_KEY", "replay-secret-test-key")
    monkeypatch.setenv("PURLWATCH_CACHE_DIR", str(custom_cache))

    sbom_path = tmp_path / "test.cdx.json"
    sbom_path.write_text(
        json.dumps(
            {
                "$schema": "http://cyclonedx.org/schema/bom-1.5.json",
                "bomFormat": "CycloneDX",
                "specVersion": "1.5",
                "metadata": {
                    "component": {
                        "name": "app",
                        "type": "application",
                        "version": "1.0",
                    }
                },
                "components": [
                    {
                        "name": "mock-pkg",
                        "type": "library",
                        "version": "1.0.0",
                        "purl": "pkg:npm/mock-pkg@1.0.0",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    current_time = 1000.0
    sleep_calls: list[float] = []

    def fake_sleep(seconds: float) -> None:
        nonlocal current_time
        sleep_calls.append(float(seconds))
        current_time += seconds

    def fake_monotonic() -> float:
        nonlocal current_time
        current_time += 0.001
        return current_time

    monkeypatch.setattr("time.sleep", fake_sleep)
    monkeypatch.setattr("time.monotonic", fake_monotonic)

    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1

        if scenario == "503_persistent":
            return httpx.Response(
                503,
                headers={"Retry-After": "1"},
                request=request,
            )

        if scenario == "connect_error":
            raise httpx.ConnectError("Network unreachable", request=request)

        if scenario == "429_then_200":
            if attempts < 3:
                return httpx.Response(
                    429,
                    headers={"Retry-After": "1"},
                    request=request,
                )
            return httpx.Response(
                200,
                json={
                    "name": "mock-pkg",
                    "repository": {
                        "type": "git",
                        "url": "https://github.com/org/repo.git",
                    },
                },
                request=request,
            )

        raise ValueError(f"Not defined scenario: {scenario}")

    real_create_http_client = resolve.create_http_client

    def fake_create_http_client(*args, **kwargs):
        kwargs["inner"] = httpx.MockTransport(handler)
        return real_create_http_client(*args, **kwargs)

    monkeypatch.setattr(resolve, "create_http_client", fake_create_http_client)

    argv = ["resolve", "--sbom", str(sbom_path)]
    result = run_resolve(argv)

    assert result == exit_code
    assert attempts == expected_attempts

    if expected_sleeps is not None:
        assert sleep_calls == expected_sleeps
