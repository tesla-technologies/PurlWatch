import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
