import json
import re
from dataclasses import dataclass
from typing import Any, cast

import httpx
from auratrace_core.snapshot import SnapshotWriter


@dataclass(frozen=True)
class Version:
    time: str
    publisher: str | None
    maintainers: list[str]
    trusted_publishing: bool = False
    yanked: bool = False


@dataclass(frozen=True)
class Fact:
    name: str
    current_owners: list[str] | None
    repository: str | None
    versions: dict[str, Version]
    owners_current_only: bool


class PackageNotFound(Exception):
    """Raises when package it's not found"""


class ResponseException(Exception):
    """Raises when an exception occurs on the petition"""


def recursive_sanitize(
    data: Any, pattern: re.Pattern[str], removed_email: bool = False
) -> tuple[Any, bool]:
    keys_to_remove = {"email", "readme"}

    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if k in keys_to_remove:
                if k == "email":
                    removed_email = True
                continue
            new_dict[k], removed_email = recursive_sanitize(v, pattern, removed_email)
        return new_dict, removed_email
    elif isinstance(data, list):
        new_list = []
        for obj in data:
            new_obj, removed_email = recursive_sanitize(obj, pattern, removed_email)
            new_list.append(new_obj)
        return new_list, removed_email
    elif isinstance(data, str):
        if pattern.search(data):
            data = pattern.sub("", data)
            removed_email = True
        return data, removed_email
    else:
        return data, removed_email


def sanitize_payload(data: dict[str, Any]) -> tuple[str, bool]:
    pattern = re.compile(
        r"(?!git@[^/:\s]+:)(?<!://)(?<!:)\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )
    new_data, removed_email = recursive_sanitize(data, pattern)

    return json.dumps(
        new_data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ), removed_email


def extract_allowed_headers(headers: httpx.Headers | dict[str, str]) -> dict[str, str]:
    allowed_headers = ["content-type", "etag", "last-modified", "date", "cache-control"]
    headers_dict = {}

    for key, value in headers.items():
        if key.lower() in allowed_headers or key.lower().startswith("x-ratelimit-"):
            headers_dict[key] = value

    return headers_dict


def collect(
    client: httpx.Client,
    writer: SnapshotWriter,
    url: str,
    key: str,
    collector: str,
    params: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    try:
        response = client.get(url, params=params)

        response.raise_for_status()

        payload = response.json()
        if isinstance(payload, list):
            payload = payload[0] if payload else {}
        sanitized_text, email_removed = sanitize_payload(payload)

        headers_dict = extract_allowed_headers(response.headers)

        writer.add_document(
            collector,
            "0.1.0",
            key,
            url,
            response.status_code,
            dict(headers_dict),
            email_removed,
            sanitized_text,
        )

        return cast(dict[str, Any], json.loads(sanitized_text))
    except httpx.HTTPStatusError as err:
        if err.response.status_code == 404:
            writer.add_document(
                collector,
                "0.1.0",
                key,
                url,
                404,
                extract_allowed_headers(response.headers),
                False,
                "",
            )
            return None
        raise ResponseException(
            f"HTTP error {err.response.status_code} received from registry"
        ) from err
    except httpx.RequestError as err:
        raise ResponseException(
            f"Request failed trying to connect to npm server: {err}"
        ) from err
