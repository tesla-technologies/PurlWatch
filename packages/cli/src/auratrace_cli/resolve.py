import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import httpx
from auratrace_collectors import client, crates, npm, sources
from auratrace_core import hashing, history, mapping, parser, snapshot
from packageurl import PackageURL


def main() -> None:
    parser = argparse.ArgumentParser(exit_on_error=False)
    subparsers = parser.add_subparsers(dest="command", required=True)
    resolve_c = subparsers.add_parser("resolve", exit_on_error=False)
    resolve_c.add_argument(
        "--sbom", required=True, type=Path, help="Specifies the SBOM to read."
    )
    resolve_c.add_argument(
        "--offline",
        required=False,
        type=Path,
        help="Runs the command in offline mode. Reads the snapshot and prints the information in the specified format. The snapshot must correspond directly to the provided SBOM.",
    )
    resolve_c.add_argument(
        "--json",
        action="store_true",
        required=False,
        help="Changes the output from a human-readable text format to a machine-readable format. It can be applied to online and offline mode.",
    )

    try:
        args = parser.parse_args()
    except argparse.ArgumentError as err:
        if "--offline" in err.message or err.argument_name == "--offline":
            sys.exit(3)

    sys.exit(run_resolve(args))


def create_http_client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": "auratrace/0.1.0"},
        transport=client.AuratraceTransport(min_host_delay=0.5),
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        timeout=15.0,
    )


def format_output_human(
    map_list: list[Any],
) -> None:
    for m in map_list:
        map = m[0]
        his = m[1]
        print("=" * 80)
        print(f"Purl: {map.purl}")
        print(f"Repository: {map.repository}")
        print(f"Confidence: {map.confidence.value}")
        print(f"Sources agreeing: {map.sources_agreeing}")
        print(f"Sources: {', '.join(map.sources)}")
        print(f"Forge: {map.forge.value}")

        if not his:
            continue
        print("\nVersions:")
        for v in his:
            pub_hid = (
                hashing.short_hid(v[1].publisher_hid) if v[1].publisher_hid else None
            )
            man_hid_list = [hashing.short_hid(hid) for hid in v[1].maintainers_hids]

            print(
                f"Version: {v[0]} | Date: {v[1].published_at} | Publisher hid: {pub_hid} | Publisher kind: {v[1].publisher_kind.value} | Maintainers hids: {', '.join(man_hid_list)}"
            )


def format_output_json(
    map_list: list[Any], manifest: dict[str, Any], snapshot_digest: str
) -> None:
    manifest["snapshot_digest"] = f"sha256:{snapshot_digest}"

    mapping_list = []
    history_list = []

    for m in map_list:
        map = m[0]
        his = m[1]

        mapping_list.append(asdict(map))
        for v in his:
            history_list.append(asdict(v[1]))

    final_obj = {
        "run": manifest,
        "mapping": mapping_list,
        "publisher_history": history_list,
    }

    print(
        json.dumps(final_obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    )


def resolve_component(
    graph: dict[str, set[str]], external_dict: dict[str, str], src: sources.Source
) -> list[tuple[mapping.Map, list[tuple[str, Any]]]]:
    map_list = []
    history_list: list[tuple[str, Any]] = []

    for component in graph:
        history_list = []
        candidates = []
        purl = PackageURL.from_string(component)
        pkg_type = purl.type

        if pkg_type == "generic":
            raw_repo = external_dict.get(component)
            if raw_repo:
                repo_url = mapping.normalize_url(raw_repo)
                if repo_url:
                    candidates.append(("sbom", repo_url))

            map_fields = mapping.extract_map_fields(candidates)

            map_item = mapping.map_to_repo(component, map_fields, "0.1.0")
            map_list.append((map_item, history_list))
            continue

        fact: npm.Fact | crates.Fact | None = None
        if pkg_type == "npm":
            fact = src.npm(component)

        if pkg_type == "cargo":
            fact = src.crates(component)

        ecosystem_collect = src.ecosystems(component)
        if ecosystem_collect is not None:
            ecosystem_url = mapping.normalize_url(ecosystem_collect)
            if ecosystem_url is not None:
                candidates.append(("ecosystems", ecosystem_url))

        if fact is not None:
            if fact.repository is not None:
                candidate_url = mapping.normalize_url(fact.repository)
                if candidate_url is not None:
                    candidates.append(("registry", candidate_url))

            base = PackageURL.from_string(component)
            for key, val in sorted(fact.versions.items(), key=lambda kv: kv[1].time):
                row_purl = PackageURL(
                    type=base.type,
                    namespace=base.namespace,
                    name=base.name,
                    version=key,
                ).to_string()
                version_dict = asdict(cast(Any, val))
                history_fields = history.extract_history_fields(version_dict, pkg_type)
                history_item = history.map_to_history(
                    row_purl,
                    history_fields,
                    fact.owners_current_only,
                    "0.1.0",
                )
                history_list.append((key, history_item))

        map_fields = mapping.extract_map_fields(candidates)
        map_item = mapping.map_to_repo(component, map_fields, "0.1.0")
        map_list.append((map_item, history_list))

    return map_list


def run_resolve(args: argparse.Namespace) -> int:
    try:
        tar_path = None
        parsed_sbom = parser.parse_sbom(args.sbom)
        direct_graph = parser.build_direct_graph(parsed_sbom)
        transitive_graph = parser.build_transitive_graph(direct_graph)

        external_dict: dict[str, str] = {}
        for comp in parsed_sbom.comp_list:
            if comp.purl and comp.external_ref:
                external_dict[comp.purl] = comp.external_ref

    except (
        parser.InvalidStructureError,
        parser.UnsupportedFormatError,
        FileNotFoundError,
    ) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2

    try:
        if args.offline:
            with snapshot.SnapshotReader(args.offline) as reader:
                snapshot_src = sources.SnapshotSource(reader)
                map_list = resolve_component(
                    transitive_graph, external_dict, snapshot_src
                )
                manifest = reader.manifest
                with args.offline.open("rb") as file:
                    snapshot_digest = hashlib.file_digest(
                        file, hashlib.sha256
                    ).hexdigest()
        else:
            httpx_client = create_http_client()
            with snapshot.SnapshotWriter() as writer:
                live_src = sources.LiveSource(writer, httpx_client)
                map_list = resolve_component(transitive_graph, external_dict, live_src)
                with args.sbom.open("rb") as file:
                    sbom_digest = hashlib.file_digest(file, hashlib.sha256).hexdigest()

                tar_path, snapshot_digest, manifest = writer.close_document(
                    None, sbom_digest, None
                )

        if args.json:
            format_output_json(map_list, manifest, snapshot_digest)
        else:
            format_output_human(map_list)

        if tar_path:
            print(
                f"\nSnapshot: {tar_path} (digest: {snapshot_digest})", file=sys.stderr
            )

        return 0
    except (ValueError, FileNotFoundError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    main()
