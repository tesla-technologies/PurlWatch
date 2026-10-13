import re
from dataclasses import dataclass
from enum import Enum


class Forge(Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    CODEBERG = "codeberg"
    SOURCEHUT = "sourcehut"
    GITEA = "gitea"
    OTHER = "other"
    UNKNOWN = "unknown"


class Confidence(Enum):
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


def normalize_url(url: str) -> str | None:
    repo_regex = re.compile(
        r"^(?:[a-zA-Z+]+://)?(?:git@)?(?P<forge>[^/:]+)[/:](?P<owner>[^/]+)/(?P<repo>[^/#?]+?)(?:\.git)?/?$"
    )

    match = repo_regex.search(url.strip())
    if not match:
        return None

    forge = re.sub(r"(\.[a-zA-Z]+)$", "", match.group("forge").lower())
    owner = match.group("owner").lower()
    repo = match.group("repo").lower()

    final_url = f"https://{forge}/{owner}/{repo}"

    print(final_url)
    return final_url
