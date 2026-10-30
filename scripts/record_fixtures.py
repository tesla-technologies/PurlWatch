import hashlib
from datetime import datetime, timezone
from pathlib import Path

from auratrace_cli.resolve import create_http_client, resolve_component
from auratrace_collectors import sources
from auratrace_core import parser, resolve, snapshot

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    [print(item) for item in (ROOT / "examples").iterdir() if item.is_file()]
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    for item in (ROOT / "examples").iterdir():
        if not item.is_file():
            continue

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


if __name__ == "__main__":
    main()
