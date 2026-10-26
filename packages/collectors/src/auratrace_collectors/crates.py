import json
from dataclasses import dataclass
from typing import Any

import httpx
from auratrace_core.snapshot import SnapshotReader, SnapshotWriter
from packageurl import PackageURL

from auratrace_collectors import common


@dataclass(frozen=True)
class Version:
    time: str
    publisher: str | None
    maintainers: list[str]
    yanked: bool


@dataclass(frozen=True)
class Fact:
    name: str | None
    current_owners: list[str] | None
    repository: str | None
    versions: dict[str, Version]
    owners_current_only: bool


def parse_fact(versions: dict[str, Any], owners: dict[str, Any]) -> Fact:
    versions_json = versions.get("versions", {})

    dict_versions = {}

    owners_list = []
    for owner in owners.get("users", []):
        if owner.get("login") is not None:
            owners_list.append(owner.get("login", None))

    for v_data in versions_json:
        time = v_data.get("created_at", "")
        publisher = (v_data.get("published_by", {}) or {}).get("login", None)
        yanked = v_data.get("yanked", False)

        dict_versions[v_data.get("num", "")] = Version(
            time, publisher, owners_list, yanked
        )

    return Fact(
        versions.get("crate", {}).get("name", None),
        owners_list,
        versions.get("crate", {}).get("repository", None),
        dict_versions,
        True,
    )


def resolve_key(purl: str) -> str:
    parsed_purl = PackageURL.from_string(purl)
    if parsed_purl.namespace:
        pkg_name = f"{parsed_purl.namespace}/{parsed_purl.name}"
    else:
        pkg_name = parsed_purl.name

    return pkg_name


def replay(reader: SnapshotReader, purl: str) -> Fact | None:
    pkg_name = resolve_key(purl)

    key_v = f"cargo/{pkg_name}/versions_crate.json"
    key_o = f"cargo/{pkg_name}/owners_crate.json"

    response_v, entry_v = reader.get_document(key_v)
    response_o, entry_o = reader.get_document(key_o)

    if entry_v["status"] == 404 or entry_o["status"] == 404:
        return None

    parsed_response_v = json.loads(response_v)
    parsed_response_o = json.loads(response_o)

    return parse_fact(parsed_response_v, parsed_response_o)


def collect(
    purl: str | None, client: httpx.Client, writer: SnapshotWriter
) -> Fact | None:
    if not purl:
        return None

    pkg_name = resolve_key(purl)

    result_v = common.collect(
        client=client,
        writer=writer,
        url=f"https://crates.io/api/v1/crates/{pkg_name}",
        headers={"User-Agent": "auratrace/0.1.0"},
        key=f"cargo/{pkg_name}/versions_crate.json",
        collector="crates",
    )

    result_o = common.collect(
        client=client,
        writer=writer,
        url=f"https://crates.io/api/v1/crates/{pkg_name}/owners",
        headers={"User-Agent": "auratrace/0.1.0"},
        key=f"cargo/{pkg_name}/owners_crate.json",
        collector="crates",
    )

    if not result_o or not result_v:
        return None

    return parse_fact(result_v, result_o)
