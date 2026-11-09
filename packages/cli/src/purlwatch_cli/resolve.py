import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

import httpx
import purlwatch_core.exceptions as core_exc
from packageurl import PackageURL
from purlwatch_collectors import client, crates, ecosystems, npm, sources
from purlwatch_core import hashing, history, mapping, parser, resolve, snapshot

RELEASE_V = version("purlwatch_collectors")


def main() -> None:
    sys.exit(run_resolve(sys.argv[1:]))


def create_http_client(
    inner: httpx.BaseTransport | None = None,
) -> httpx.Client:
    if inner is None:
        inner = httpx.HTTPTransport()
    return httpx.Client(
        headers={
            "User-Agent": f"purlwatch/{version('purlwatch_cli')} (https://github.com/tesla-technologies/purlwatch)"
        },
        transport=client.PurlwatchTransport(inner=inner, min_host_delay=0.5),
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        timeout=15.0,
    )


def format_output_human(map_list: list[Any], nodes: dict[str, resolve.Node]) -> None:
    has_root = False
    for m in map_list:
        mapp = m[0]
        his = m[1]
        comp = m[2]

        if comp.is_root:
            has_root = True

        print("=" * 80)
        label = "Bom-Ref" if comp.route == resolve.Route.NO_PURL else "Purl"
        print(f"{label}: {mapp.purl}")
        if comp.route not in (
            resolve.Route.NO_PURL,
            resolve.Route.UNSUPPORTED,
        ) and not (comp.is_root and not comp.declared_repo):
            print(f"Repository: {mapp.repository}")
            print(f"Confidence: {mapp.confidence.value}")
            print(f"Sources agreeing: {mapp.sources_agreeing}")
            print(f"Sources: {', '.join(mapp.sources)}")
            print(f"Forge: {mapp.forge.value}")

        if m[3]:
            print(m[3])

        if not his:
            continue
        print("\nVersions:")
        for v in his:
            pub_hid = (
                hashing.short_hid(v[1].publisher_hid) if v[1].publisher_hid else None
            )
            man_hid_list = [hashing.short_hid(hid) for hid in v[1].maintainers_hids]

            print(
                f"Version: {v[0]} | Date: {v[1].published_at} | Publisher hid: {pub_hid if pub_hid else ''} | Publisher kind: {v[1].publisher_kind.value} | Maintainers hids: {', '.join(man_hid_list)}"
            )

    print("\nComponents:")
    if not has_root:
        print(
            "[WARN] Evaluated SBOM has no root component, depth cannot be calculated\n"
        )
    for node in nodes.values():
        print(
            f"Ref: {node.ref} | Purl: {node.purl} | Depth: {node.depth}{'. [WARN] Unreachable component' if (node.depth is None and has_root) else ''} | Via: {node.via} | Route: {node.route.value}"
        )


def format_output_json(
    map_list: list[Any],
    manifest: dict[str, Any],
    snapshot_digest: str,
    nodes: dict[str, resolve.Node],
) -> None:
    manifest["snapshot_digest"] = f"sha256:{snapshot_digest}"

    mapping_list = []
    history_list = []
    components_list = []

    for m in map_list:
        mapp = m[0]
        his = m[1]
        comp = m[2]

        if comp.route not in (
            resolve.Route.NO_PURL,
            resolve.Route.UNSUPPORTED,
        ) and not (comp.is_root and not comp.declared_repo):
            mapping_list.append(asdict(mapp))

        for v in his:
            history_list.append(asdict(v[1]))

    for node in nodes.values():
        components_list.append(
            {
                "ref": node.ref,
                "purl": node.purl,
                "depth": node.depth,
                "via": node.via,
                "route": node.route.value,
            }
        )

    final_obj = {
        "run": manifest,
        "mapping": mapping_list,
        "components": components_list,
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
    nodes: dict[str, resolve.Node], src: sources.Source
) -> list[tuple[mapping.Map, list[tuple[str, Any]], resolve.Node, str | None]]:
    map_list: list[
        tuple[mapping.Map, list[tuple[str, Any]], resolve.Node, str | None]
    ] = []
    history_list: list[tuple[str, Any]] = []
    pkg_mapped: set[str] = set()

    for component in nodes.values():
        history_list = []
        candidates: list[tuple[str, str]] = []
        note: str | None = None
        fact: npm.Fact | crates.Fact | None = None
        ecosystem_collect: ecosystems.Fact | None = None
        map_pkg: str | None = None

        if component.package:
            map_pkg = component.package
            if component.package in pkg_mapped:
                continue
            pkg_mapped.add(component.package)

        if (
            component.route == resolve.Route.NO_PURL
            or not component.purl
            or not component.package
        ):
            map_pkg = component.ref
            note = "Note: Component has no Package URL; not evaluated"
        elif component.is_root and not component.declared_repo:
            note = "Note: Root component has no declared VCS repository"
        elif component.route == resolve.Route.REPOSITORY_ONLY or (
            component.is_root and component.declared_repo
        ):
            raw_repo = component.declared_repo
            for repo in raw_repo:
                repo_from = repo[0]
                repo_url = repo[1]
                if repo_url:
                    if repo_from == resolve.Declared.EXTERNAL:
                        candidate = ("sbom", repo_url)
                    if repo_from in (resolve.Declared.VCS_URL, resolve.Declared.PURL):
                        candidate = ("purl", repo_url)

                    if candidate not in candidates:
                        candidates.append(candidate)

            note = "Note: Repository only path"
        elif component.route == resolve.Route.UNSUPPORTED:
            note = "Note: Unsupported pkg format, not evaluated"
        else:
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
        map_item = mapping.map_to_repo(map_pkg, map_fields, RELEASE_V, observed_at)
        map_list.append((map_item, history_list, component, note))

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

        if args.offline:
            with snapshot.SnapshotReader(args.offline) as reader:
                snapshot_src = sources.SnapshotSource(reader)
                map_list = resolve_component(resolved_sbom.nodes, snapshot_src)
                manifest = reader.manifest
                with args.offline.open("rb") as file:
                    snapshot_digest = hashlib.file_digest(
                        file, hashlib.sha256
                    ).hexdigest()
        else:
            httpx_client = create_http_client(inner=httpx.HTTPTransport())
            try:
                with snapshot.SnapshotWriter() as writer:
                    live_src = sources.LiveSource(writer, httpx_client)
                    map_list = resolve_component(resolved_sbom.nodes, live_src)
                    with args.sbom.open("rb") as file:
                        sbom_digest = hashlib.file_digest(
                            file, hashlib.sha256
                        ).hexdigest()

                    tar_path, snapshot_digest, manifest = writer.close_document(
                        None, sbom_digest, None
                    )
            finally:
                httpx_client.close()
        try:
            if args.json:
                format_output_json(
                    map_list, manifest, snapshot_digest, resolved_sbom.nodes
                )
            else:
                format_output_human(map_list, resolved_sbom.nodes)
        except BrokenPipeError:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
            return 0
        finally:
            if tar_path:
                print(
                    f"\nSnapshot: {tar_path} (digest: {snapshot_digest})",
                    file=sys.stderr,
                )

        return 0
    except core_exc.PurlwatchError as err:
        print(f"purlwatch: {err}", file=sys.stderr)
        return err.exit_code


if __name__ == "__main__":
    main()
