import argparse
import hashlib
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from purlwatch_cli.resolve import create_http_client, resolve_component
from purlwatch_collectors import sources
from purlwatch_core import exceptions, parser, resolve, snapshot

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS_DIR = ROOT / "tests" / "fixtures" / "snapshots"
GOLDEN_DIR = ROOT / "tests" / "golden"


def record_all_examples(action_def, label: str) -> None:
    for item in sorted((ROOT / "examples").iterdir()):
        if not item.is_file():
            continue
        print(f"Recording {label} for {item.name}")
        try:
            action_def(item)
        except exceptions.PurlwatchError as err:
            print(f"\nError recording {item.name}: \n{err}")


def record_cassette(node_id: str | None = None) -> None:
    CASSETTES_DIR = ROOT / "tests" / "cassettes"

    if node_id:
        test = node_id
    else:
        if CASSETTES_DIR.is_dir():
            for cassette in CASSETTES_DIR.rglob("*.yaml"):
                cassette.unlink()
        test = str(ROOT / "tests" / "test_e2e.py")

    cmd = [sys.executable, "-m", "pytest", "-m", "vcr", "--record-mode=rewrite", test]
    res = subprocess.run(cmd, check=False)
    if res.returncode != 0:
        sys.exit(res.returncode)


def record_snapshot(item: Path) -> None:
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    parsed_sbom = parser.parse_sbom(item)
    resolved_sbom = resolve.resolve(parsed_sbom)

    httpx_client = create_http_client(inner=httpx.HTTPTransport())
    with snapshot.SnapshotWriter(
        out_path=SNAPSHOTS_DIR, clock=lambda: now, suffix="record"
    ) as writer:
        live_src = sources.LiveSource(writer, httpx_client)
        resolve_component(resolved_sbom.nodes, live_src)
        with item.open("rb") as file:
            sbom_digest = hashlib.file_digest(file, hashlib.sha256).hexdigest()

        tar_path, _, _ = writer.close_document(None, sbom_digest, None)

        final_name = (
            item.name.removesuffix(".cdx.json")
            .removesuffix(".spdx.json")
            .removesuffix(".json")
        )
        tar_path.replace(tar_path.with_name(f"{final_name}.tar"))


def record_golden(item: Path) -> None:
    item_stem = item.stem
    item_name = item_stem.removesuffix(".spdx").removesuffix(".cdx")
    snapshot = (SNAPSHOTS_DIR / item_name).with_suffix(".tar")

    if not snapshot.exists():
        raise exceptions.InputError(
            "This file doesn't have a snapshot at tests/fixtures/snapshots"
        )

    env_c = os.environ.copy()
    env_c["PURLWATCH_HASH_KEY"] = "test-key-in-ci"
    cmd = [
        "purlwatch",
        "resolve",
        "--sbom",
        str(item),
        "--offline",
        str(snapshot),
        "--json",
    ]

    golden_file = GOLDEN_DIR / f"{item_name}.json"
    with open(golden_file, "w") as f:
        subprocess.run(cmd, env=env_c, stdout=f, check=False)


def main() -> None:
    record_parser = argparse.ArgumentParser()
    record_parser.add_argument(
        "--all", required=False, action="store_true", help="Record every e2e fixture"
    )
    fixtures_group = record_parser.add_mutually_exclusive_group(required=False)
    fixtures_group.add_argument(
        "--snapshot",
        nargs="?",
        type=Path,
        default=None,
        const=True,
        help="Record snapshots. Incompatible with other fixture type flag.",
    )
    fixtures_group.add_argument(
        "--cassette",
        nargs="?",
        default=None,
        const=True,
        help="Record cassettes. Incompatible with other fixture type flag.",
    )
    fixtures_group.add_argument(
        "--golden",
        nargs="?",
        type=Path,
        default=None,
        const=True,
        help="Record golden files. Incompatible with other fixture type flag.",
    )
    args = record_parser.parse_args()

    if args.all:
        if args.snapshot:
            record_all_examples(record_snapshot, "snapshot")
        elif args.cassette:
            record_cassette()
        elif args.golden:
            record_all_examples(record_golden, "golden file")
        else:
            record_all_examples(record_snapshot, "snapshot")
            record_all_examples(record_golden, "golden file")
            record_cassette()

    else:
        if args.snapshot:
            if args.snapshot is True:
                record_parser.error(
                    "--snapshot requieres an SBOM path if --all is not specified"
                )
            print(f"Recording fixture for {args.snapshot}")
            try:
                record_snapshot(args.snapshot)
            except exceptions.PurlwatchError as err:
                print(f"\nError recording {args.snapshot}: \n{err}")
                sys.exit(1)
            return
        elif args.cassette:
            if args.cassette is True:
                record_parser.error(
                    "--cassette requieres an SBOM path if --all is not specified"
                )
            print(f"Recording cassette for {args.cassette}")
            record_cassette(args.cassette)
        elif args.golden:
            if args.golden is True:
                record_parser.error(
                    "--golden requieres an SBOM path if --all is not specified"
                )
            print(f"Recording golden file for {args.golden}")
            try:
                record_golden(args.golden)
            except exceptions.PurlwatchError as err:
                print(f"\nError recording {args.golden}: \n{err}")
                sys.exit(1)
            return
        else:
            record_parser.error(
                "If --all is not specified a fixture type flag is needed"
            )


if __name__ == "__main__":
    main()
