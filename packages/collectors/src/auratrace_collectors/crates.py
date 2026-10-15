import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx
from auratrace_core.snapshot import SnapshotReader, SnapshotWriter


class PackageNotFound(Exception):
    """Se lanza cuando el paquete no se encuentra en crates.io"""


class ResponseException(Exception):
    """Se lanza cuando hay un error en la petición"""


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

    for v_data in versions_json:
        time = v_data.get("created_at", "")
        publisher = (v_data.get("published_by", {}) or {}).get("login", None)
        yanked = v_data.get("yanked", False)

        dict_versions[v_data.get("num", "")] = Version(time, publisher, [], yanked)

    return Fact(
        versions.get("crate", {}).get("name", None),
        owners.get("users"),
        versions.get("crate", {}).get("repository", None),
        dict_versions,
        True,
    )


def replay(reader: SnapshotReader, key_v: str, key_o: str) -> Fact:
    response_v, _ = reader.get_document(key_v)
    response_o, _ = reader.get_document(key_o)

    parsed_response_v = json.loads(response_v)
    parsed_response_o = json.loads(response_o)

    return parse_fact(parsed_response_v, parsed_response_o)


def collect(name: str, client: httpx.Client, writer: SnapshotWriter) -> Fact:
    headers = {"User-Agent": "auratrace/0.1.0"}
    encoded_name = quote(name, safe="")
    url = f"https://crates.io/api/v1/crates/{encoded_name}"

    try:
        v_response = client.get(url, headers=headers)

        v_response.raise_for_status()

        text = v_response.text
        v_sanitized_text, v_count = re.subn(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "<EMAIL>", text
        )

        writer.add_document(
            "crates.io",
            "0.1.0",
            f"cargo/{encoded_name}/versions_crate.json",
            url,
            v_response.status_code,
            dict(v_response.headers),
            v_count > 0,
            v_sanitized_text,
        )

    except httpx.HTTPStatusError as err:
        if err.response.status_code == 404:
            raise PackageNotFound(f"Package '{name}' was not found") from err
        raise ResponseException(
            f"HTTP error {err.response.status_code} received from registry"
        ) from err
    except httpx.RequestError as err:
        raise ResponseException(
            f"Request failed trying to connect to crates.io server: {err}"
        ) from err

    try:
        o_response = client.get(url + "/owners", headers=headers)

        o_response.raise_for_status()

        text = o_response.text
        o_sanitized_text, o_count = re.subn(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "<EMAIL>", text
        )

        writer.add_document(
            "crates.io",
            "0.1.0",
            f"cargo/{encoded_name}/owners_crate.json",
            url,
            o_response.status_code,
            dict(o_response.headers),
            o_count > 0,
            o_sanitized_text,
        )

    except httpx.HTTPStatusError as err:
        if err.response.status_code == 404:
            raise PackageNotFound(f"Package '{name}' was not found") from err
        raise ResponseException(
            f"HTTP error {err.response.status_code} received from registry"
        ) from err
    except httpx.RequestError as err:
        raise ResponseException(
            f"Request failed trying to connect to crates.io server: {err}"
        ) from err

    return parse_fact(json.loads(v_sanitized_text), json.loads(o_sanitized_text))
