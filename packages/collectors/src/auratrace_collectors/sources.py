from typing import Protocol

import httpx
from auratrace_core.snapshot import SnapshotReader, SnapshotWriter

from auratrace_collectors import crates, ecosystems, npm


class Source(Protocol):
    def npm(self, purl: str) -> npm.Fact | None: ...
    def crates(self, purl: str) -> crates.Fact | None: ...
    def ecosystems(self, purl: str) -> ecosystems.Fact | None: ...


class LiveSource:
    def __init__(self, writer: SnapshotWriter, client: httpx.Client) -> None:
        self._writer = writer
        self._client = client

    def npm(self, purl: str) -> npm.Fact | None:
        return npm.collect(purl, self._client, self._writer)

    def crates(self, purl: str) -> crates.Fact | None:
        return crates.collect(purl, self._client, self._writer)

    def ecosystems(self, purl: str) -> ecosystems.Fact | None:
        return ecosystems.collect(purl, self._client, self._writer)


class SnapshotSource:
    def __init__(self, reader: SnapshotReader) -> None:
        self._reader = reader

    def npm(self, purl: str) -> npm.Fact | None:
        return npm.replay(self._reader, purl)

    def crates(self, purl: str) -> crates.Fact | None:
        return crates.replay(self._reader, purl)

    def ecosystems(self, purl: str) -> ecosystems.Fact | None:
        return ecosystems.replay(self._reader, purl)
