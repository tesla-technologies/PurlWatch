import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from purlwatch_cli.resolve import create_http_client, resolve_component
from purlwatch_collectors import sources
from purlwatch_core import exceptions, parser, resolve, snapshot

ROOT = Path(__file__).resolve().parent.parent


def record_cassettes() -> None:
    CASSETTES_DIR = ROOT / "tests" / "cassettes"
    if CASSETTES_DIR.exists():
        for item in CASSETTES_DIR.rglob("*.yaml"):
            item.unlink()

    cmd = ["pytest", f"{ROOT}/tests/test_e2e.py", "-m", "vcr", "--record-mode=rewrite"]
    subprocess.run(cmd, check=False)


def record_tar(item: Path) -> None:
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    parsed_sbom = parser.parse_sbom(item)
    resolved_sbom = resolve.resolve(parsed_sbom)
    external_dict: dict[str, str] = {}
    for comp in parsed_sbom.comp_list:
        if comp.bom_ref and comp.external_ref:
            external_dict[comp.bom_ref] = comp.external_ref

    httpx_client = create_http_client()
    with snapshot.SnapshotWriter(
        out_path=ROOT / "tests" / "fixtures", clock=lambda: now, suffix="record"
    ) as writer:
        live_src = sources.LiveSource(writer, httpx_client)
        resolve_component(resolved_sbom.nodes, external_dict, live_src)
        with item.open("rb") as file:
            sbom_digest = hashlib.file_digest(file, hashlib.sha256).hexdigest()

        tar_path, _, _ = writer.close_document(None, sbom_digest, None)

        final_name = (
            item.name.removesuffix(".cdx.json")
            .removesuffix(".spdx.json")
            .removesuffix(".json")
        )
        tar_path.replace(tar_path.with_name(f"{final_name}.tar"))


def main() -> None:
    if len(sys.argv) > 1:
        print(f"Recording fixture for {sys.argv[1]}")
        try:
            record_tar(Path(sys.argv[1]))
        except exceptions.PurlwatchError as err:
            print(f"\nError recording {sys.argv[1]}: \n{err}")
            sys.exit(1)
        return
    else:
        for item in (ROOT / "examples").iterdir():
            if not item.is_file():
                continue
            print(f"Recording fixture for {item}")
            try:
                record_tar(item)
            except exceptions.PurlwatchError as err:
                print(f"\nError recording {item}: \n{err}")


if __name__ == "__main__":
    main()
