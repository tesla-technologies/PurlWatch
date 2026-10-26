import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from auratrace_collectors.crates import replay as crates_replay
from auratrace_collectors.ecosystems import replay as ecosystems_replay
from auratrace_collectors.npm import replay as npm_replay
from auratrace_core.snapshot import SnapshotReader, SnapshotWriter

TEST_DIR = Path(__file__).parent


@pytest.fixture
def snapshot_builder(
    request: pytest.FixtureRequest, tmp_path: Path
) -> Iterator[Callable[..., SnapshotReader]]:
    """Create dynamic snapshots"""
    readers_to_close: list[SnapshotReader] = []

    def _build(
        documents: list[dict[str, Any]],
    ) -> SnapshotReader:
        writer = SnapshotWriter(out_path=tmp_path / "snapshots")

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
                email_removed=False,
                body=body,
                url=doc.get("url", f"https://registry.example.org/{key}"),
            )

        tar_path, _ = writer.close_document(None, None, None)
        reader = SnapshotReader(tar=tar_path)

        readers_to_close.append(reader)
        return reader

    yield _build

    for r in readers_to_close:
        r.close()


def test_npm_replay_fact(
    snapshot_builder: Callable[..., SnapshotReader],
) -> None:

    reader = snapshot_builder(
        [
            {
                "key": "npm/is-sorted/packument.json",
                "body": Path(f"{TEST_DIR}/fixtures/npm/is_sorted.json"),
            }
        ]
    )

    result = npm_replay(reader, "pkg:npm/is-sorted@1.0.5")
    assert result

    assert result.name == "is-sorted"
    assert result.current_owners == ["dcousens"]
    assert result.repository == "git+https://github.com/dcousens/is-sorted.git"

    specific_version = result.versions["1.0.0"]
    assert specific_version.publisher == "dcousens"
    assert specific_version.maintainers == ["dcousens"]


def test_crates_replay_fact(
    snapshot_builder: Callable[..., SnapshotReader],
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

    result = crates_replay(reader, "pkg:cargo/void")
    assert result

    assert result.name == "void"
    assert result.current_owners == ["reem"]
    assert result.repository == "https://github.com/reem/rust-void.git"

    specific_version = result.versions["1.0.0"]
    assert specific_version.publisher == None
    assert specific_version.maintainers == ["reem"]
    assert specific_version.yanked == False


def test_express_replay_fact(
    snapshot_builder: Callable[..., SnapshotReader],
) -> None:

    reader = snapshot_builder(
        [
            {
                "key": "ecosystems/express/metadata.json",
                "body": Path(f"{TEST_DIR}/fixtures/ecosystems/express.json"),
            }
        ]
    )

    result = ecosystems_replay(reader, "ecosystems/express/metadata.json")

    assert result == "https://github.com/expressjs/express"
