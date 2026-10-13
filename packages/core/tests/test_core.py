from pathlib import Path

import pytest
from auratrace_core.mapping import normalize_url
from auratrace_core.parser import UnsupportedFormatError, parse_sbom

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
            "https://github/dcousens/is-sorted",
        ),
        ("git://github.com/isaacs/inherits.git", "https://github/isaacs/inherits"),
        ("https://github.com/reem/rust-void.git", "https://github/reem/rust-void"),
    ],
)
def test_normalized_url(url: str, normalized: str) -> None:
    result = normalize_url(url)

    assert result == normalized
