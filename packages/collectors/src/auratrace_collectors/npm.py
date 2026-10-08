import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx


@dataclass(frozen=True)
class Version:
    time: str
    _npmUser: str | None
    maintainers: list[str]
    trusted_publishing: bool


@dataclass(frozen=True)
class Fact:
    name: str
    versions: dict[str, Version]
    owners_current_only: bool


@dataclass(frozen=True)
class Record:
    url: str
    time: str
    status: int
    headers: dict[str, str]
    digest: str


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
        is_trusted_publishing = "attestations" in v_data.get("dist", {})

        version = Version(time, npm_user, maintainers, is_trusted_publishing)
        dict_versions[v_key] = version

    return Fact(raw_json.get("name", ""), dict_versions, False)


def replay(data: Path) -> Fact:
    with open(data, "r", encoding="utf-8") as s:
        raw_json = json.load(s)

    return parse_fact(raw_json)


def collect(name: str, client: httpx.Client) -> Fact:
    headers = {"User-Agent": "auratrace/0.1.0"}
    encoded_name = quote(name, safe="")
    url = f"https://registry.npmjs.org/{encoded_name}"

    try:
        response = client.get(url, headers=headers)

        response.raise_for_status()

        text = response.text
        sanitized_text = re.sub(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "<EMAIL>", text
        )

        digest = sha256(sanitized_text.encode("utf-8")).hexdigest()
        time = datetime.now(timezone.utc).isoformat()

        record = Record(url, time, response.status_code, headers, digest)
        print(f"[RECORD]:\n{record}")

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
