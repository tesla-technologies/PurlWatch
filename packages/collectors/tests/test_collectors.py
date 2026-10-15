import hashlib
import json
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from auratrace_collectors.crates import replay as crates_replay
from auratrace_collectors.npm import replay as npm_replay
from auratrace_core.snapshot import SnapshotReader, SnapshotWriter

TEST_DIR = Path(__file__).parent


@pytest.fixture
def snapshot_builder(
    request: pytest.FixtureRequest, tmp_path: Path
) -> Iterator[Callable[..., SnapshotReader]]:
    """Crea snapshots dinámicos al vuelo para cualquier test."""
    readers_to_close: list[SnapshotReader] = []

    def _build(
        documents: list[dict[str, Any]],
        sbom_path: Path = Path(f"{TEST_DIR}/fixtures/test_sbom.json"),
    ) -> SnapshotReader:
        with open(sbom_path, "rb") as f:
            sbom_digest = hashlib.file_digest(f, hashlib.sha256).hexdigest()

        exec_id = datetime.now(timezone.utc).isoformat()
        writer = SnapshotWriter(
            execution_id=exec_id, base_path=tmp_path, out_path=tmp_path / "snapshots"
        )

        for doc in documents:
            key = doc["key"]

            body = doc["body"]
            if isinstance(body, Path):
                body = body.read_text(encoding="utf-8")
            elif isinstance(body, dict):
                body = json.dumps(body)

            writer.add_document(
                collector="test",
                collector_v="0.1.0",
                headers=doc.get("headers", {"User-Agent": "auratrace/0.1.0"}),
                status=doc.get("status", 200),
                key=key,
                body=body,
                url=doc.get("url", f"https://registry.example.org/{key}"),
            )

        tar_path, _ = writer.close_document("test", sbom_digest, "test-ruleset")
        reader = SnapshotReader(tar=tar_path, sbom=sbom_path)

        readers_to_close.append(reader)
        return reader

    yield _build

    for r in readers_to_close:
        r.close()


@pytest.mark.parametrize(
    ("n_versions", "n_maint", "n_trusted"),
    [(6, 6, 0)],
)
def test_npm_replay_fact(
    snapshot_builder: Callable[..., SnapshotReader],
    n_versions: int,
    n_maint: int,
    n_trusted: int,
) -> None:

    reader = snapshot_builder(
        [
            {
                "key": "npm/express/packument.json",
                "body": Path(f"{TEST_DIR}/fixtures/npm/is_sorted.json"),
            }
        ]
    )

    result = npm_replay(reader, "npm/express/packument.json")

    assert len(result.versions) == n_versions

    r_maint = 0
    r_trusted = 0
    for v_data in result.versions.values():
        if v_data.maintainers:
            r_maint += 1

        if v_data.trusted_publishing:
            r_trusted += 1

    assert n_maint == r_maint
    assert n_trusted == r_trusted


@pytest.mark.parametrize(
    ("v_json", "o_json", "n_versions", "n_yanked"),
    [
        (
            "cargo/void/versions_crate.json",
            "cargo/void/owners_crate.json",
            8,
            0,
        )
    ],
)
def test_crates_replay_fact(
    snapshot_builder: Callable[..., SnapshotReader],
    v_json: str,
    o_json: str,
    n_versions: int,
    n_yanked: int,
) -> None:

    reader = snapshot_builder(
        [
            {
                "key": "cargo/void/versions_crate.json",
                "body": Path(f"{TEST_DIR}/fixtures/crates/void_versions.json"),
            },
            {
                "key": "cargo/void/owners_crate.json",
                "body": Path(f"{TEST_DIR}/fixtures/crates/void_owners.json"),
            },
        ]
    )

    result = crates_replay(reader, v_json, o_json)

    assert result.name
    assert result.current_owners is not None
    assert len(result.current_owners) > 0

    assert len(result.versions) == n_versions

    r_yanked = 0
    for v_data in result.versions.values():
        if v_data.yanked:
            r_yanked += 1

    assert n_yanked == r_yanked
