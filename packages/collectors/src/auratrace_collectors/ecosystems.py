import json
from typing import Any

import httpx
from auratrace_core.snapshot import SnapshotReader, SnapshotWriter

from auratrace_collectors import common


def parse_fact(raw_json: dict[str, Any]) -> str | None:
    return raw_json.get("repository_url", None)


def replay(reader: SnapshotReader, key: str) -> str | None:
    response, entry = reader.get_document(key)
    if entry["status"] == 404:
        return None
    parsed_response = json.loads(response)

    if not parsed_response:
        return None

    return parse_fact(parsed_response)


def collect(purl: str, client: httpx.Client, writer: SnapshotWriter) -> str | None:
    result = common.collect(
        client=client,
        writer=writer,
        url="https://packages.ecosyste.ms/api/v1/packages/lookup",
        key=f"ecosystems/{purl}/metadata.json",
        collector="ecosyste.ms",
        params={"purl": purl},
    )

    if not result:
        return None
    return parse_fact(result)
