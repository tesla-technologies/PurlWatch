import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx


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


@dataclass(frozen=True)
class Record:
    url: str
    time: str
    status: int
    headers: dict[str, str]
    digest: str


def parse_fact(versions: dict[str, Any], owners: dict[str, Any]) -> Fact:
    versions_json = versions.get("versions", {})

    dict_versions = {}

    for v_data in versions_json:
        time = v_data.get("created_at", "")
        publisher = v_data.get("published_by", None)
        yanked = v_data.get("yanked", False)

        dict_versions[v_data.get("num", "")] = Version(time, publisher, [], yanked)

    return Fact(
        versions.get("crate", {}).get("name", None),
        owners.get("users"),
        versions.get("repository", None),
        dict_versions,
        True,
    )


def replay(versions: Path, owners: Path) -> Fact:
    with open(versions, "r", encoding="utf-8") as v:
        versions_json = json.load(v)
    with open(owners, "r", encoding="utf-8") as o:
        owners_json = json.load(o)

    return parse_fact(versions_json, owners_json)


def collect(name: str, client: httpx.Client) -> tuple[Fact, list[Record]]:
    headers = {"User-Agent": "auratrace/0.1.0"}
    encoded_name = quote(name, safe="")
    url = f"https://crates.io/api/v1/crates/{encoded_name}"

    try:
        v_response = client.get(url, headers=headers)

        v_response.raise_for_status()

        text = v_response.text
        v_sanitized_text = re.sub(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "<EMAIL>", text
        )

        digest = sha256(v_sanitized_text.encode("utf-8")).hexdigest()
        time = datetime.now(timezone.utc).isoformat()

        v_record = Record(url, time, v_response.status_code, headers, digest)

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
        o_sanitized_text = re.sub(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "<EMAIL>", text
        )

        digest = sha256(o_sanitized_text.encode("utf-8")).hexdigest()
        time = datetime.now(timezone.utc).isoformat()

        o_record = Record(
            url + "/owners", time, o_response.status_code, headers, digest
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

    return parse_fact(json.loads(v_sanitized_text), json.loads(o_sanitized_text)), [
        v_record,
        o_record,
    ]
