import json
from typing import Any
from urllib.parse import quote

import httpx
from auratrace_core.snapshot import SnapshotReader, SnapshotWriter

from auratrace_collectors import common


def parse_fact(raw_json: dict[str, Any]) -> str | None:
    return raw_json.get("repository_url", None)


def resolve_key(purl: str) -> str:
    purl = quote(purl, safe="")

    return f"ecosystems/{purl}/metadata.json"


def replay(reader: SnapshotReader, purl: str) -> str | None:
    key = resolve_key(purl)

    response, entry = reader.get_document(key)
    if entry["status"] == 404:
        return None
    parsed_response = json.loads(response)

    if not parsed_response:
        return None

    return parse_fact(parsed_response)


def collect(purl: str, client: httpx.Client, writer: SnapshotWriter) -> str | None:
    key = resolve_key(purl)

    result = common.collect(
        client=client,
        writer=writer,
        url="https://packages.ecosyste.ms/api/v1/packages/lookup",
        key=key,
        collector="ecosyste.ms",
        params={"purl": purl},
    )

    if not result:
        return None
    return parse_fact(result)
