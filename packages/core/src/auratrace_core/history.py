from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from auratrace_core.hashing import identity_hid


class Kind(str, Enum):
    ACCOUNT = "account"
    TRUSTED = "trusted_publisher"
    UNKNOWN = "unknown"


class Source(str, Enum):
    LIVE = "live"
    WAYBACK = "wayback"
    DUMP = "dump"


@dataclass(frozen=True)
class History:
    purl: str
    published_at: str
    publisher_hid: str | None
    publisher_kind: Kind
    maintainers_hids: list[str]
    owners_current_only: bool
    source: Source
    observed_at: str
    release: str


def extract_history_fields(version: dict[str, Any], type: str) -> dict[str, Any]:
    published_at = version["time"]
    publisher_hid = None
    kind = Kind.UNKNOWN
    maintainers_hids = []
    source = Source.LIVE

    if version["publisher"] is not None:
        publisher_hid = identity_hid(type, version["publisher"])
        kind = (
            Kind.TRUSTED if version.get("trusted_publishing", False) else Kind.ACCOUNT
        )

    for m in version["maintainers"]:
        maintainers_hids.append(identity_hid(type, m))

    return {
        "published_at": published_at,
        "publisher_hid": publisher_hid,
        "publisher_kind": kind,
        "maintainers_hids": maintainers_hids,
        "source": source,
    }


def map_to_history(
    purl: str, fields: dict[str, Any], owners_current: bool, release: str
) -> History:
    return History(
        purl=purl,
        published_at=fields["published_at"],
        publisher_hid=fields["publisher_hid"],
        publisher_kind=fields["publisher_kind"],
        maintainers_hids=fields["maintainers_hids"],
        owners_current_only=owners_current,
        source=fields["source"],
        observed_at=datetime.now(timezone.utc).isoformat(),
        release=release,
    )
