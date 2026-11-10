import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any
from urllib.parse import urlparse, urlsplit


class Forge(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    CODEBERG = "codeberg"
    SOURCEHUT = "sourcehut"
    GITEA = "gitea"
    OTHER = "other"
    UNKNOWN = "unknown"


FORGE_HOSTS = {
    "github.com": Forge.GITHUB,
    "gitlab.com": Forge.GITLAB,
    "codeberg.org": Forge.CODEBERG,
    "git.sr.ht": Forge.SOURCEHUT,
}


SHORT_FORMS = {
    "github:": "github.com/",
    "gitlab:": "gitlab.com/",
    "bitbucket:": "bitbucket.org/",
    "gist:": "gist.github.com/",
}


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass(frozen=True)
class Map:
    purl: str | None
    repository: str
    forge: Forge
    confidence: Confidence
    sources_agreeing: int
    sources: list[str]
    observed_at: str | None
    release: str


def process_url(url: str) -> str:
    for key, value in SHORT_FORMS.items():
        if url.startswith(key):
            url = "https://" + url.replace(key, value, 1)

    if re.match(r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$", url):
        url = "https://github.com/" + url

    if match := re.match(r"^([a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+):(.+)$", url):
        url = f"ssh://{match.group(1)}/{match.group(2)}"

    return url


def normalize_url(url: str) -> str | None:
    s_url = url.strip()
    s_url = process_url(s_url)
    s_url = s_url.removeprefix("git+")
    s_url = s_url.removeprefix("scm:git:")
    s_url = s_url.removeprefix("scm:")
    s_url = s_url.removesuffix(".git")

    parsed_url = urlsplit(s_url)

    host = parsed_url.hostname
    if host:
        host = host.lower().removeprefix("www.")
    else:
        return None

    scheme = parsed_url.scheme
    if scheme in ("git", "http", "ssh", ""):
        scheme = "https"

    path = parsed_url.path

    segments = path.strip("/").split("/")

    if host in ("github.com", "codeberg.org", "bitbucket.org"):
        valid_segments = segments[:2]
    elif "gitlab" in host:
        if "/-/" in path:
            valid_segments = segments[: segments.index("-")]
        else:
            valid_segments = segments
    elif "sr.ht" in host:
        user_idx = next(
            (i for i, seg in enumerate(segments) if seg.startswith("~")), None
        )
        if user_idx is not None and user_idx + 1 < len(segments):
            valid_segments = segments[user_idx : user_idx + 2]
        else:
            valid_segments = segments[:2]
    else:
        valid_segments = segments[:2]

    clean_path = "/".join(valid_segments)
    final_url = f"{scheme}://{host}/{clean_path}"
    return final_url.removesuffix(".git")


def extract_map_fields(candidates: list[tuple[str, str]] | None) -> dict[str, Any]:
    """In case of low confidence the repository is decided through votes.
    If there is a draw, the registry source has priority deciding the source"""
    repository = None
    forge = Forge.UNKNOWN
    confidence = Confidence.NONE
    sources_agreeing = 0
    sources = [source for source, _ in candidates] if candidates else []

    if not candidates:
        return {
            "repository": repository,
            "forge": forge,
            "confidence": confidence,
            "sources_agreeing": sources_agreeing,
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
        if len(confidence_dict) > 1:
            confidence = Confidence.LOW
            repository = max(
                confidence_dict,
                key=lambda url: (
                    len(confidence_dict[url]),
                    "registry" in confidence_dict[url],
                ),
            )
        else:
            confidence = Confidence.MEDIUM
            repository = next(iter(confidence_dict.keys()))

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
    purl: str | None, fields: dict[str, Any], release: str, observed_at: str | None
) -> Map:
    return Map(
        purl=purl,
        repository=fields["repository"],
        forge=fields["forge"],
        confidence=fields["confidence"],
        sources_agreeing=fields["sources_agreeing"],
        sources=fields["sources"],
        observed_at=observed_at,
        release=release,
    )
