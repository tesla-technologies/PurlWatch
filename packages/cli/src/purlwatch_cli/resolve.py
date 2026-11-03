import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import httpx
import purlwatch_core.exceptions as core_exc
from packageurl import PackageURL
from purlwatch_collectors import client, crates, npm, sources
from purlwatch_core import hashing, history, mapping, parser, resolve, snapshot

RELEASE_V = "0.1.0"


def main() -> None:
    sys.exit(run_resolve(sys.argv[1:]))


def create_http_client() -> httpx.Client:
    return httpx.Client(
        headers={
            "User-Agent": "purlwatch/0.1.0 (https://github.com/tesla-technologies/purlwatch)"
        },
        transport=client.PurlwatchTransport(min_host_delay=0.5),
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        timeout=15.0,
    )


def format_output_human(
    map_list: list[Any],
) -> None:
    for m in map_list:
        mapp = m[0]
        his = m[1]
        print("=" * 80)
        print(f"Purl: {mapp.purl}")
        print(f"Repository: {mapp.repository}")
        print(f"Confidence: {mapp.confidence.value}")
        print(f"Sources agreeing: {mapp.sources_agreeing}")
        print(f"Sources: {', '.join(mapp.sources)}")
        print(f"Forge: {mapp.forge.value}")

        if m[2]:
            print("Note: Repository only path")

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
        mapp = m[0]
        his = m[1]

        mapping_list.append(asdict(mapp))
        for v in his:
            history_list.append(asdict(v[1]))

    final_obj = {
        "run": manifest,
        "mapping": mapping_list,
        "publisher_history": history_list,
    }

    print(
        json.dumps(
            final_obj,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            indent=1,
        )
    )


def resolve_component(
    nodes: dict[str, resolve.Node], external_dict: dict[str, str], src: sources.Source
) -> list[tuple[mapping.Map, list[tuple[str, Any]], bool]]:
    map_list: list[tuple[mapping.Map, list[tuple[str, Any]], bool]] = []
    history_list: list[tuple[str, Any]] = []
    pkg_mapped: set[str] = set()

    for component in nodes.values():
        history_list = []
        candidates: list[tuple[str, str]] = []

        if (
            component.route == resolve.Route.NO_PURL
            or not component.purl
            or not component.package
            or component.is_root
        ):
            continue

        if component.package in pkg_mapped:
            continue
        pkg_mapped.add(component.package)

        if component.route == resolve.Route.REPOSITORY_ONLY:
            raw_repo = external_dict.get(component.ref)
            if raw_repo:
                repo_url = mapping.normalize_url(raw_repo)
                if repo_url:
                    candidates.append(("sbom", repo_url))

            map_fields = mapping.extract_map_fields(candidates)

            map_item = mapping.map_to_repo(component.package, map_fields, "0.1.0", None)
            map_list.append((map_item, history_list, True))
            continue

        fact: npm.Fact | crates.Fact | None = None

        if component.route == resolve.Route.REGISTRY:
            purl = PackageURL.from_string(component.purl)
            pkg_type = purl.type
            if pkg_type == "npm":
                fact = src.npm(component.purl)

            if pkg_type == "cargo":
                fact = src.crates(component.purl)

        ecosystem_collect = src.ecosystems(component.purl)
        if ecosystem_collect is not None and ecosystem_collect.repository:
            ecosystem_url = mapping.normalize_url(ecosystem_collect.repository)
            if ecosystem_url is not None:
                candidates.append(("ecosystems", ecosystem_url))

        if fact is not None:
            if fact.repository is not None:
                candidate_url = mapping.normalize_url(fact.repository)
                if candidate_url is not None:
                    candidates.append(("registry", candidate_url))

            base = PackageURL.from_string(component.purl)
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
                    RELEASE_V,
                    fact.observed_at,
                )
                history_list.append((key, history_item))

        if fact is not None:
            observed_at = fact.observed_at
        elif ecosystem_collect is not None:
            observed_at = ecosystem_collect.observed_at
        else:
            observed_at = None

        map_fields = mapping.extract_map_fields(candidates)
        map_item = mapping.map_to_repo(
            component.package, map_fields, RELEASE_V, observed_at
        )
        map_list.append((map_item, history_list, False))

    return map_list


def build_parser() -> argparse.ArgumentParser:
    resolve_parser = argparse.ArgumentParser()
    subparsers = resolve_parser.add_subparsers(dest="command", required=True)
    resolve_c = subparsers.add_parser("resolve")
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

    return resolve_parser


def run_resolve(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = build_parser().parse_args(argv)

    try:
        tar_path = None
        parsed_sbom = parser.parse_sbom(args.sbom)
        resolved_sbom = resolve.resolve(parsed_sbom)

        external_dict: dict[str, str] = {}
        for comp in parsed_sbom.comp_list:
            if comp.bom_ref and comp.external_ref:
                external_dict[comp.bom_ref] = comp.external_ref

        if args.offline:
            with snapshot.SnapshotReader(args.offline) as reader:
                snapshot_src = sources.SnapshotSource(reader)
                map_list = resolve_component(
                    resolved_sbom.nodes, external_dict, snapshot_src
                )
                manifest = reader.manifest
                with args.offline.open("rb") as file:
                    snapshot_digest = hashlib.file_digest(
                        file, hashlib.sha256
                    ).hexdigest()
        else:
            httpx_client = create_http_client()
            try:
                with snapshot.SnapshotWriter() as writer:
                    live_src = sources.LiveSource(writer, httpx_client)
                    map_list = resolve_component(
                        resolved_sbom.nodes, external_dict, live_src
                    )
                    with args.sbom.open("rb") as file:
                        sbom_digest = hashlib.file_digest(
                            file, hashlib.sha256
                        ).hexdigest()

                    tar_path, snapshot_digest, manifest = writer.close_document(
                        None, sbom_digest, None
                    )
            finally:
                httpx_client.close()

        if args.json:
            format_output_json(map_list, manifest, snapshot_digest)
        else:
            format_output_human(map_list)

        if tar_path:
            print(
                f"\nSnapshot: {tar_path} (digest: {snapshot_digest})", file=sys.stderr
            )

        return 0
    except core_exc.PurlwatchError as err:
        print(f"purlwatch: {err}", file=sys.stderr)
        return err.exit_code


if __name__ == "__main__":
    main()
