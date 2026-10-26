import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from packageurl import PackageURL


class Forge(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    CODEBERG = "codeberg"
    SOURCEHUT = "sourcehut"
    GITEA = "gitea"
    SBOM = "sbom"
    OTHER = "other"
    UNKNOWN = "unknown"


FORGE_HOSTS = {
    "github.com": Forge.GITHUB,
    "gitlab.com": Forge.GITLAB,
    "codeberg.org": Forge.CODEBERG,
    "git.sr.ht": Forge.SOURCEHUT,
}


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass(frozen=True)
class Map:
    purl: str
    repository: str
    forge: Forge
    confidence: Confidence
    sources_agreeing: int
    sources: list[str]
    observed_at: str
    release: str
    note: str | None = None


def normalize_url(url: str) -> str | None:
    repo_regex = re.compile(
        r"^(?:[a-zA-Z+]+:)*(?:[a-zA-Z+]+://)?(?:git@)?(?:(?P<forge>[^/:]+)[/:])?(?P<owner>[^/]+)/(?P<repo>[^/#?]+?)(?:\.git)?(?:/[^#?]*)?(?:[#?].*)?$"
    )

    match = repo_regex.search(url.strip())
    if not match:
        return None

    forge = match.group("forge")
    if not forge:
        forge = "github.com"

    owner = match.group("owner")
    repo = match.group("repo")

    domain_regex = re.compile(r"^[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+$")
    if not domain_regex.search(forge):
        forge = forge + ".com"

    final_url = f"https://{forge}/{owner}/{repo}"

    return final_url


def extract_map_fields(candidates: list[tuple[str, str]]) -> dict[str, Any]:
    """In case of low confidence the repository is decided through votes.
    If there is a draw, the registry source has priority deciding the source"""
    repository = None
    forge = Forge.UNKNOWN
    confidence = Confidence.NONE
    sources_agreeing = 0
    sources = [source for source, _ in candidates]

    if not candidates:
        return {
            "repository": repository,
            "forge": forge,
            "confidence": Confidence.NONE,
            "sources_agreeing": sources_agreeing,
            "sources": sources,
        }

    if len(candidates) == 1:
        return {
            "repository": candidates[0][1],
            "forge": extract_forge(candidates[0][1]),
            "confidence": Confidence.MEDIUM
            if candidates[0][0] != "provenance"
            else Confidence.HIGH,
            "sources_agreeing": 1,
            "sources": sources,
        }

    confidence_dict: defaultdict[str, list[str]] = defaultdict(list)
    for src, url in candidates:
        confidence_dict[url].append(src)

    for url, source in confidence_dict.items():
        if ("provenance" in source) or ("registry" in source and len(source) > 1):
            confidence = Confidence.HIGH
            repository = url
            sources_agreeing = len(source)
            break

    if confidence != Confidence.HIGH:
        confidence = Confidence.LOW
        repository = max(
            confidence_dict,
            key=lambda url: (
                len(confidence_dict[url]),
                "registry" in confidence_dict[url],
            ),
        )
        sources_agreeing = len(confidence_dict[repository])

    return {
        "repository": repository,
        "forge": extract_forge(repository),
        "confidence": confidence,
        "sources_agreeing": sources_agreeing,
        "sources": sources,
    }


def extract_forge(url: str | None) -> Forge:
    if url is None:
        return Forge.UNKNOWN
    return FORGE_HOSTS.get(urlparse(url).netloc, Forge.OTHER)


def map_to_repo(
    purl: str, fields: dict[str, Any], release: str, note: str | None = None
) -> Map:
    mapping_purl = PackageURL(
        **{**PackageURL.from_string(purl).to_dict(), "version": None}
    ).to_string()

    return Map(
        purl=mapping_purl,
        repository=fields["repository"],
        forge=fields["forge"],
        confidence=fields["confidence"],
        sources_agreeing=fields["sources_agreeing"],
        sources=fields["sources"],
        observed_at=datetime.now(timezone.utc).isoformat(),
        release=release,
        note=note,
    )
