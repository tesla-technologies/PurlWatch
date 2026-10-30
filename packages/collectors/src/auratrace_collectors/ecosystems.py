import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx
from auratrace_core.snapshot import SnapshotReader, SnapshotWriter

from auratrace_collectors import common


@dataclass(frozen=True)
class Fact:
    repository: str | None
    observed_at: str


def parse_fact(raw_json: dict[str, Any], observed_at: str) -> Fact | None:
    return Fact(raw_json.get("repository_url", None), observed_at)


def resolve_key(purl: str) -> str:
    purl = quote(purl, safe="")

    return f"ecosystems/{purl}/metadata.json"


def replay(reader: SnapshotReader, purl: str) -> Fact | None:
    key = resolve_key(purl)

    response, entry = reader.get_document(key)
    if entry["status"] == 404:
        return None
    parsed_response = json.loads(response)

    if not parsed_response:
        return None

    return parse_fact(parsed_response, entry["time"])


def collect(purl: str, client: httpx.Client, writer: SnapshotWriter) -> Fact | None:
    key = resolve_key(purl)

    collected = common.collect(
        client=client,
        writer=writer,
        url="https://packages.ecosyste.ms/api/v1/packages/lookup",
        key=key,
        collector="ecosyste.ms",
        params={"purl": purl},
    )

    if collected is None:
        return None

    result, observed_at = collected

    return parse_fact(result, observed_at)
