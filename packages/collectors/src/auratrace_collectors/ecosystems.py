import json
import re
from typing import Any
from urllib.parse import quote

import httpx
from auratrace_core.snapshot import SnapshotReader, SnapshotWriter


class PackageNotFound(Exception):
    """Se lanza cuando el paquete no se encuentra en npm"""


class ResponseException(Exception):
    """Se lanza cuando hay un error en la petición"""


def parse_fact(raw_json: dict[str, Any]) -> str | None:
    return raw_json.get("repository_url", None)


def replay(reader: SnapshotReader, key: str) -> str | None:
    response = reader.get_document(key)

    return parse_fact(response[0])


def collect(name: str, client: httpx.Client, writer: SnapshotWriter) -> str | None:
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

        writer.add_document(
            "ecosyste.ms",
            "0.1.0",
            f"ecosystems/{encoded_name}/metadata.json",
            url,
            response.status_code,
            headers,
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
            f"Request failed trying to connect to ecosyste.ms server: {err}"
        ) from err
