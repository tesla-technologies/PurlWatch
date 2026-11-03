from pathlib import Path

import pytest
from purlwatch_core.mapping import extract_map_fields, normalize_url
from purlwatch_core.parser import UnsupportedFormatError, parse_sbom

TEST_DIR = Path(__file__).parent


@pytest.mark.parametrize(
    ("sbom", "n_comp", "n_purl", "n_no_purl", "n_edges"),
    [
        (f"{TEST_DIR}/fixtures/sbom/no-purl.cdx.json", 3, 0, 3, 2),
        (f"{TEST_DIR}/fixtures/sbom/spdx.json", 4, 1, 3, 7),
        (f"{TEST_DIR}/fixtures/sbom/purl.cdx.json", 3, 3, 0, 1),
        (f"{TEST_DIR}/fixtures/sbom/nested.cdx.json", 6, 0, 6, 0),
    ],
)
def test_sbom_parser_content(
    sbom: Path, n_comp: int, n_purl: int, n_no_purl: int, n_edges: int
) -> None:
    sbom_path = Path(sbom)
    result = parse_sbom(sbom_path)

    assert len(result.comp_list) == n_comp

    r_purl = 0
    r_no_purl = 0
    for comp in result.comp_list:
        if comp.purl:
            r_purl += 1
        else:
            r_no_purl += 1
    assert r_purl == n_purl
    assert r_no_purl == n_no_purl

    assert len(result.dependencies) == n_edges


def test_sbom_invalid_version_error() -> None:
    with pytest.raises(UnsupportedFormatError):
        parse_sbom(Path(f"{TEST_DIR}/fixtures/sbom/wrong-version.cdx.json"))


@pytest.mark.parametrize(
    ("url", "normalized"),
    [
        (
            "git+https://github.com/dcousens/is-sorted.git",
            "https://github.com/dcousens/is-sorted",
        ),
        ("git://github.com/isaacs/inherits.git", "https://github.com/isaacs/inherits"),
        ("https://github.com/reem/rust-void.git", "https://github.com/reem/rust-void"),
        ("github:usuario/repo", "https://github.com/usuario/repo"),
        ("usuario/repo", "https://github.com/usuario/repo"),
        (
            "scm:git:https://github.com/google/guava.git",
            "https://github.com/google/guava",
        ),
        (
            "https://github.com/babel/babel/tree/main/packages/babel-core",
            "https://github.com/babel/babel",
        ),
        ("gitlab:org/repo", "https://gitlab.com/org/repo"),
        ("bitbucket:org/repo", "https://bitbucket.org/org/repo"),
        ("https://git.sr.ht/~sircmpwn/scdoc", "https://git.sr.ht/~sircmpwn/scdoc"),
        ("https://gitlab.gnome.org/GNOME/glib", "https://gitlab.gnome.org/GNOME/glib"),
        (
            "https://gitlab.com/group/subgroup/project",
            "https://gitlab.com/group/subgroup/project",
        ),
        ("https://github.com:443/x/y", "https://github.com/x/y"),
        ("https://www.github.com/x/y", "https://github.com/x/y"),
        ("git+ssh://git@github.com/npm/wrappy.git", "https://github.com/npm/wrappy"),
        ("git+https://github.com/x/y.git#main", "https://github.com/x/y"),
    ],
)
def test_normalized_url(url: str, normalized: str) -> None:
    result = normalize_url(url)

    assert result == normalized


@pytest.mark.parametrize(
    ("candidates", "confidence"),
    [
        ([], "none"),
        (
            [
                ("ecosystems", "https://github.com/nuevo-org/repo"),
                ("depsdev", "https://github.com/nuevo-org/repo"),
                ("registry", "https://github.com/viejo-org/repo"),
            ],
            "low",
        ),
        (
            [
                ("ecosystems", "https://github.com/candidato-a/repo"),
                ("depsdev", "https://bitbucket.org/candidato-b/repo"),
            ],
            "low",
        ),
        (
            [
                ("ecosystems", "https://github.com/candidato-a/repo"),
            ],
            "medium",
        ),
        (
            [
                ("ecosystems", "https://github.com/nuevo-org/repo"),
                ("depsdev", "https://github.com/nuevo-org/repo"),
                ("registry", "https://github.com/nuevo-org/repo"),
            ],
            "high",
        ),
        (
            [
                ("ecosystems", "https://github.com/nuevo-org/repo"),
                ("depsdev", "https://github.com/nuevo-org/repo"),
                ("provenance", "https://github.com/viejo-org/repo"),
            ],
            "high",
        ),
        (
            [
                ("provenance", "https://github.com/candidato-a/repo"),
            ],
            "high",
        ),
    ],
)
def test_confidence_from_candidates(
    candidates: list[tuple[str, str]], confidence: str
) -> None:
    result = extract_map_fields(candidates)["confidence"]

    assert result.value == confidence
