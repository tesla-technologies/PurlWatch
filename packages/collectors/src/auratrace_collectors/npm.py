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
    trusted_publishing: bool


@dataclass(frozen=True)
class Fact:
    name: str
    current_owners: list[str] | None
    repository: str | None
    versions: dict[str, Version]
    owners_current_only: bool


def parse_fact(raw_json: dict[str, Any]) -> Fact:
    json_versions = raw_json.get("versions", {})
    json_time = raw_json.get("time", {})

    json_maintainers = raw_json.get("maintainers", [])
    maintainers = []
    for m in json_maintainers:
        maintainers.append(m.get("name", ""))
    dict_versions = {}

    for v_key, v_data in json_versions.items():
        time = json_time.get(v_key, "")
        npm_user = (v_data.get("_npmUser") or {}).get("name")
        maintainers_list_v = v_data.get("maintainers", [])
        maintainers_v = []
        for m in maintainers_list_v:
            maintainers_v.append(m.get("name", ""))
        is_trusted_publishing = npm_user == "GitHub Actions" and bool(
            v_data.get("trustedPublisher")
        )

        version = Version(time, npm_user, maintainers_v, is_trusted_publishing)
        dict_versions[v_key] = version

    repo_data = raw_json.get("repository")
    repository = None
    if isinstance(repo_data, dict):
        repository = repo_data.get("url")
    elif isinstance(repo_data, str):
        repository = repo_data
    else:
        repository = None

    return Fact(
        raw_json.get("name", ""),
        maintainers,
        repository,
        dict_versions,
        False,
    )


def resolve_key(purl: str) -> str:
    parsed_purl = PackageURL.from_string(purl)
    if parsed_purl.namespace:
        scope = parsed_purl.namespace.lstrip("@")
        pkg_name = f"@{scope}/{parsed_purl.name}"
    else:
        pkg_name = parsed_purl.name

    return pkg_name


def replay(reader: SnapshotReader, purl: str) -> Fact | None:
    pkg_name = resolve_key(purl)

    key = f"npm/{pkg_name}/packument.json"
    response, entry = reader.get_document(key)
    if entry["status"] == 404:
        return None
    parsed_response = json.loads(response)

    return parse_fact(parsed_response)


def collect(
    purl: str | None, client: httpx.Client, writer: SnapshotWriter
) -> Fact | None:
    if not purl:
        return None

    pkg_name = resolve_key(purl)

    result = common.collect(
        client=client,
        writer=writer,
        url=f"https://registry.npmjs.org/{pkg_name}",
        headers={"User-Agent": "auratrace/0.1.0"},
        key=f"npm/{pkg_name}/packument.json",
        collector="npm",
    )

    if not result:
        return None

    return parse_fact(result)
