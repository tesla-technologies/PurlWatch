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


def parse_fact(raw_json: dict[str, Any]) -> str | None:
    return raw_json.get("repository_url", None)


def replay(data: Path) -> str | None:
    with open(data, "r", encoding="utf-8") as s:
        raw_json = json.load(s)

    return parse_fact(raw_json)


def collect(name: str, client: httpx.Client) -> tuple[str | None, Record]:
    headers = {"User-Agent": "auratrace/0.1.0"}
    encoded_name = quote(name, safe="")
    url = f"https://packages.ecosyste.ms/api/v1/packages/lookup?purl={encoded_name}"

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

        return parse_fact(json.loads(sanitized_text)), record
    except httpx.HTTPStatusError as err:
        if err.response.status_code == 404:
            raise PackageNotFound(f"Package '{name}' was not found") from err
        raise ResponseException(
            f"HTTP error {err.response.status_code} received from registry"
        ) from err
    except httpx.RequestError as err:
        raise ResponseException(
            f"Request failed trying to connect to ecosyste.ms server: {err}"
        ) from err
