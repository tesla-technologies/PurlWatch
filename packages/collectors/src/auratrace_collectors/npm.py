import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx
from auratrace_core.snapshot import SnapshotReader, SnapshotWriter


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


class PackageNotFound(Exception):
    """Se lanza cuando el paquete no se encuentra en npm"""


class ResponseException(Exception):
    """Se lanza cuando hay un error en la petición"""


def parse_fact(raw_json: dict[str, Any]) -> Fact:
    json_versions = raw_json.get("versions", {})
    json_time = raw_json.get("time", {})

    dict_versions = {}

    for v_key, v_data in json_versions.items():
        time = json_time.get(v_key, "")
        npm_user = (v_data.get("_npmUser") or {}).get("name")
        maintainers = v_data.get("maintainers", [])
        is_trusted_publishing = npm_user == "GitHub Actions" and bool(
            v_data.get("trustedPublisher")
        )

        version = Version(time, npm_user, maintainers, is_trusted_publishing)
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
        raw_json.get("maintainers", []),
        repository,
        dict_versions,
        False,
    )


def replay(reader: SnapshotReader, key: str) -> Fact:
    response, _ = reader.get_document(key)
    parsed_response = json.loads(response)

    return parse_fact(parsed_response)


def collect(name: str, client: httpx.Client, writer: SnapshotWriter) -> Fact:
    headers = {"User-Agent": "auratrace/0.1.0"}
    encoded_name = quote(name, safe="")
    url = f"https://registry.npmjs.org/{encoded_name}"

    try:
        response = client.get(url, headers=headers)

        response.raise_for_status()

        text = response.text
        sanitized_text, count = re.subn(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "<EMAIL>", text
        )

        writer.add_document(
            "npm",
            "0.1.0",
            f"npm/{encoded_name}/packument.json",
            url,
            response.status_code,
            dict(response.headers),
            count > 0,
            sanitized_text,
        )

        return parse_fact(json.loads(sanitized_text))
    except httpx.HTTPStatusError as err:
        if err.response.status_code == 404:
            raise PackageNotFound(f"Package '{name}' was not found") from err
        raise ResponseException(
            f"HTTP error {err.response.status_code} received from registry"
        ) from err
    except httpx.RequestError as err:
        raise ResponseException(
            f"Request failed trying to connect to npm server: {err}"
        ) from err
