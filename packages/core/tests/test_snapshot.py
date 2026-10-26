import io
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from auratrace_core.snapshot import (
    ReaderFileNotFoundError,
    SnapshotReader,
    SnapshotWriter,
)

TEST_DIR = Path(__file__).parent


def test_snapshot_workflow(tmp_path: Path) -> None:
    with SnapshotWriter(out_path=tmp_path / "snapshots") as writer:
        payload_list = [
            {"key": "npm/express/packument.json", "body": '{"body1": "body"}'},
            {"key": "cargo/void/versions_crate.json", "body": '{"body2": "body"}'},
            {"key": "cargo/void/owners_crate.json", "body": '{"body3": "body"}'},
        ]

        for payload in payload_list:
            writer.add_document(
                collector="test",
                collector_v="0.1.0",
                headers={"User-Agent": "auratrace/0.1.0"},
                status=200,
                key=payload["key"],
                body=payload["body"],
                email_removed=False,
                url=f"https://registry.example.org/{payload['key']}",
            )

        tar_path, _ = writer.close_document(None, None, None)

        with SnapshotReader(tar_path) as reader:
            for payload in payload_list:
                content, _ = reader.get_document(payload["key"])
                expected_bytes = payload["body"].encode("utf-8")

                assert content == expected_bytes


def test_tar_digest(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    writer = SnapshotWriter(
        suffix="test123", clock=lambda: now, out_path=tmp_path / "snapshots"
    )
    writer2 = SnapshotWriter(
        suffix="test123", clock=lambda: now, out_path=tmp_path / "snapshots"
    )
    payload_list = [
        {"key": "npm/express/packument.json", "body": '{"body1": "body"}'},
        {"key": "cargo/void/versions_crate.json", "body": '{"body2": "body"}'},
        {"key": "cargo/void/owners_crate.json", "body": '{"body3": "body"}'},
    ]

    for payload in payload_list:
        writer.add_document(
            collector="test",
            collector_v="0.1.0",
            headers={"User-Agent": "auratrace/0.1.0"},
            status=200,
            key=payload["key"],
            body=payload["body"],
            email_removed=False,
            url=f"https://registry.example.org/{payload['key']}",
        )

    _, tar_digest = writer.close_document(None, None, None)

    for payload in payload_list:
        writer2.add_document(
            collector="test",
            collector_v="0.1.0",
            headers={"User-Agent": "auratrace/0.1.0"},
            status=200,
            key=payload["key"],
            body=payload["body"],
            email_removed=False,
            url=f"https://registry.example.org/{payload['key']}",
        )

    _, tar_digest2 = writer2.close_document(None, None, None)

    assert tar_digest == tar_digest2


def test_tar_incomplete(tmp_path: Path) -> None:
    snapshots_dir = tmp_path / "snapshots"
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert list(snapshots_dir.glob("*.tar")) == []

    with (
        pytest.raises(RuntimeError, match="Test simulated error"),
        SnapshotWriter(
            suffix="test123", clock=lambda: now, out_path=snapshots_dir
        ) as writer,
    ):
        payload_list = [
            {"key": "npm/express/packument.json", "body": '{"body1": "body"}'},
            {"key": "cargo/void/versions_crate.json", "body": '{"body2": "body"}'},
            {"key": "cargo/void/owners_crate.json", "body": '{"body3": "body"}'},
        ]

        for payload in payload_list:
            writer.add_document(
                collector="test",
                collector_v="0.1.0",
                headers={"User-Agent": "auratrace/0.1.0"},
                status=200,
                key=payload["key"],
                body=payload["body"],
                email_removed=False,
                url=f"https://registry.example.org/{payload['key']}",
            )

        raise RuntimeError("Test simulated error")

    tar_files = list(snapshots_dir.glob("*.tar"))
    assert len(tar_files) == 1, "No .tar file was found"

    tar_path = tar_files[0]
    assert tar_path.exists()

    with tarfile.open(tar_path, "r") as tar:
        manifest_member = next(
            (m for m in tar.getmembers() if m.name.endswith("manifest.json")), None
        )
        assert manifest_member is not None, "manifest.json does not exist at .tar file"

        extracted = tar.extractfile(manifest_member)
        assert extracted is not None

        manifest = json.loads(extracted.read().decode("utf-8"))

        assert manifest["complete"] is False


def test_incomplete_reader(tmp_path: Path) -> None:
    incomplete_tar = tmp_path / "only_index.tar"

    with tarfile.open(incomplete_tar, "w") as tar:
        data = b"[]"
        ti = tarfile.TarInfo(name="index.json")
        ti.size = len(data)
        tar.addfile(ti, io.BytesIO(data))

    with pytest.raises(ReaderFileNotFoundError):
        SnapshotReader(incomplete_tar)
