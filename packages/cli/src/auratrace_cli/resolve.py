import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import httpx
from auratrace_collectors import client, crates, ecosystems, npm
from auratrace_core import hashing, history, mapping, parser, snapshot
from packageurl import PackageURL


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    resolve_c = subparsers.add_parser("resolve")
    resolve_c.add_argument("--sbom", required=True, type=Path, help="")
    resolve_c.add_argument("--offline", required=False, help="")
    resolve_c.add_argument("--json", action="store_true", required=False, help="")

    args = parser.parse_args()

    sys.exit(run_resolve(args))


def create_http_client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": "auratrace/0.1.0 (https://gitlab.com/code-supply)"},
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


def resolve_collect(
    graph: dict[str, set[str]], external_dict: dict[str, str], sbom: Path
) -> tuple[list[Any], dict[str, Any], str]:
    httpx_client = create_http_client()

    with snapshot.SnapshotWriter() as writer:
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
                fact = npm.collect(component, httpx_client, writer)

            if pkg_type == "cargo":
                fact = crates.collect(component, httpx_client, writer)

            ecosystem_collect = ecosystems.collect(component, httpx_client, writer)
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
                for key, val in sorted(
                    fact.versions.items(), key=lambda kv: kv[1].time
                ):
                    row_purl = PackageURL(
                        type=base.type,
                        namespace=base.namespace,
                        name=base.name,
                        version=key,
                    ).to_string()
                    version_dict = asdict(cast(Any, val))
                    history_fields = history.extract_history_fields(
                        version_dict, pkg_type
                    )
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

            with sbom.open("rb") as file:
                sbom_digest = hashlib.file_digest(file, hashlib.sha256).hexdigest()
            _, snapshot_digest, manifest = writer.close_document(
                None, sbom_digest, None
            )

    return map_list, manifest, snapshot_digest


def resolve_replay(
    graph: dict[str, set[str]], tar: Path, external_dict: dict[str, str]
) -> tuple[list[Any], dict[str, Any], str]:
    with tar.open("rb") as file:
        final_digest = hashlib.file_digest(file, hashlib.sha256).hexdigest()

    with snapshot.SnapshotReader(tar) as reader:
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
                fact = npm.replay(reader, component)

            if pkg_type == "cargo":
                fact = crates.replay(reader, component)

            ecosystem_collect = ecosystems.replay(
                reader, f"ecosystems/{component}/metadata.json"
            )
            if ecosystem_collect is not None:
                ecosystem_url = mapping.normalize_url(ecosystem_collect)
                if ecosystem_url is not None:
                    candidates.append(("ecosystems", ecosystem_url))

            if fact is not None:
                if fact.repository is not None:
                    candidate_url = mapping.normalize_url(fact.repository)
                    if candidate_url is not None:
                        candidates.append(("registry", candidate_url))

                for key, val in fact.versions.items():
                    version_dict = asdict(val)
                    history_fields = history.extract_history_fields(
                        version_dict, pkg_type
                    )
                    history_item = history.map_to_history(
                        component,
                        history_fields,
                        fact.owners_current_only,
                        "0.1.0",
                    )
                    history_list.append((key, history_item))

            map_fields = mapping.extract_map_fields(candidates)
            map_item = mapping.map_to_repo(component, map_fields, "0.1.0")
            map_list.append((map_item, history_list))

    return map_list, reader.manifest, final_digest


def run_resolve(args: argparse.Namespace) -> int:
    try:
        parsed_sbom = parser.parse_sbom(args.sbom)
        direct_graph = parser.build_direct_graph(parsed_sbom)
        transitive_graph = parser.build_transitive_graph(direct_graph)

        external_dict: dict[str, str] = {}
        for comp in parsed_sbom.comp_list:
            if comp.purl and comp.external_ref:
                external_dict[comp.purl] = comp.external_ref

    except parser.InvalidStructureError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 2

    try:
        if args.offline:
            map_list, manifest, snapshot_digest = resolve_replay(
                transitive_graph, Path(args.offline), external_dict
            )
        else:
            map_list, manifest, snapshot_digest = resolve_collect(
                transitive_graph, external_dict, Path(args.sbom)
            )

        if args.json:
            format_output_json(map_list, manifest, snapshot_digest)
        else:
            format_output_human(map_list)

        return 0
    except ValueError as err:
        print(f"Error: Bad form PURL: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    main()
