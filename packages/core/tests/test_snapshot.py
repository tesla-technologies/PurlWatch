from datetime import datetime, timezone
from pathlib import Path

from auratrace_core.snapshot import SnapshotReader, SnapshotWriter

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
    writer = SnapshotWriter(clock=lambda: now, out_path=tmp_path / "snapshots")
    writer2 = SnapshotWriter(clock=lambda: now, out_path=tmp_path / "snapshots")
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

    _, tar_digest2 = writer.close_document(None, None, None)

    assert tar_digest == tar_digest2
