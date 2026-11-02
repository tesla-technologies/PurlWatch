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
    trusted_publishing: bool


@dataclass(frozen=True)
class Fact:
    name: str | None
    current_owners: list[str] | None
    repository: str | None
    versions: dict[str, Version]
    owners_current_only: bool
    observed_at: str


def parse_fact(
    versions: dict[str, Any], owners: dict[str, Any], observed_at: str
) -> Fact:
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
        trusted_publishing = v_data.get("trustpub_data", False)

        dict_versions[v_data.get("num", "")] = Version(
            time, publisher, owners_list, yanked, trusted_publishing
        )

    return Fact(
        versions.get("crate", {}).get("name", None),
        owners_list,
        versions.get("crate", {}).get("repository", None),
        dict_versions,
        True,
        observed_at,
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

    return parse_fact(parsed_response_v, parsed_response_o, entry_v["time"])


def collect(
    purl: str | None, client: httpx.Client, writer: SnapshotWriter
) -> Fact | None:
    if not purl:
        return None

    pkg_name = resolve_key(purl)

    collected_v = common.collect(
        client=client,
        writer=writer,
        url=f"https://crates.io/api/v1/crates/{pkg_name}",
        key=f"cargo/{pkg_name}/versions_crate.json",
        collector="crates",
    )

    if collected_v is None:
        return None

    collected_o = common.collect(
        client=client,
        writer=writer,
        url=f"https://crates.io/api/v1/crates/{pkg_name}/owners",
        key=f"cargo/{pkg_name}/owners_crate.json",
        collector="crates",
    )

    if collected_o is None:
        return None

    result_v, observed_at = collected_v
    result_o, _ = collected_o

    return parse_fact(result_v, result_o, observed_at)
