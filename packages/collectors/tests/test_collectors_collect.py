from pathlib import Path

import httpx
import pytest
from auratrace_collectors.client import AuratraceTransport
from auratrace_collectors.crates import collect as crates_collect
from auratrace_collectors.ecosystems import collect as ecosystems_collect
from auratrace_collectors.npm import collect as npm_collect
from auratrace_core.parser import parse_purl
from auratrace_core.snapshot import SnapshotWriter

TEST_DIR = Path(__file__).parent


@pytest.mark.vcr(record_mode="none")
def test_npm_collect_fact(
    tmp_path: Path,
) -> None:

    client = httpx.Client(
        headers={"User-Agent": "auratrace/0.1.0 (https://gitlab.com/code-supply)"},
        transport=AuratraceTransport(min_host_delay=0.5),
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        timeout=15.0,
    )

    pkg_name = parse_purl("pkg:npm/is-sorted@1.0.5")

    with SnapshotWriter(out_path=tmp_path / "snapshots") as writer:
        result = npm_collect(pkg_name, client, writer)

        assert result

        assert result.name == "is-sorted"
        assert result.current_owners == ["dcousens"]
        assert result.repository == "git+https://github.com/dcousens/is-sorted.git"

        specific_version = result.versions["1.0.0"]
        assert specific_version.publisher == "dcousens"
        assert specific_version.maintainers == ["dcousens"]


@pytest.mark.vcr(record_mode="none")
def test_crates_collect_fact(
    tmp_path: Path,
) -> None:

    client = httpx.Client(
        headers={"User-Agent": "auratrace/0.1.0 (https://gitlab.com/code-supply)"},
        transport=AuratraceTransport(min_host_delay=0.5),
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        timeout=15.0,
    )

    pkg_name = parse_purl("pkg:cargo/void")

    with SnapshotWriter(out_path=tmp_path / "snapshots") as writer:
        result = crates_collect(pkg_name, client, writer)
        assert result

        assert result.name == "void"
        assert result.current_owners == ["reem"]
        assert result.repository == "https://github.com/reem/rust-void.git"

        specific_version = result.versions["1.0.0"]
        assert specific_version.publisher == None
        assert specific_version.maintainers == ["reem"]
        assert specific_version.yanked == False


@pytest.mark.vcr(record_mode="none")
def test_ecosystems_collect_fact(
    tmp_path: Path,
) -> None:

    client = httpx.Client(
        headers={"User-Agent": "auratrace/0.1.0 (https://gitlab.com/code-supply)"},
        transport=AuratraceTransport(min_host_delay=0.5),
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        timeout=15.0,
    )

    parsed_purl = parse_purl("pkg:npm/express")
    assert parsed_purl is not None

    with SnapshotWriter(out_path=tmp_path / "snapshots") as writer:
        result = ecosystems_collect(parsed_purl, client, writer)
        assert result

        assert result == "https://github.com/expressjs/express"
