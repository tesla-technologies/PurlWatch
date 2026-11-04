import dataclasses
import hashlib
import json
import os
import secrets
import tarfile
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from types import TracebackType
from typing import Any, Self
from urllib.parse import urlparse

import purlwatch_core.exceptions as core_exc


class ReaderFileNotFoundError(core_exc.OfflineMissError):
    """Raised when a file is not found by its key in a Snapshot"""


@dataclass(frozen=True)
class Snapshot:
    path: str
    url: str
    time: str
    status: int
    headers: dict[str, str]
    sha256: str
    size: int
    collector: str
    collector_version: str
    email_removed: bool


class SnapshotWriter:
    def __init__(
        self,
        out_path: Path | None = None,
        clock: Callable[[], datetime] | None = None,
        suffix: str | None = None,
    ):
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.suffix = suffix or secrets.token_hex(2)
        self.execution_id: str = self.clock().strftime("%Y%m%d%H%M%S") + self.suffix
        self.start_time = self.clock().isoformat()
        self._index: list[Snapshot] = []
        self._temp_dir = tempfile.TemporaryDirectory(prefix="purlwatch-")
        self._base_path: Path = Path(self._temp_dir.name)
        cache_env = os.getenv("PURLWATCH_CACHE_DIR")
        default_cache = (
            Path(cache_env) if cache_env else (Path.home() / ".cache" / "purlwatch")
        )
        self._out_path: Path = out_path or (default_cache / "snapshots")
        self._closed = False

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.close_document(None, None, None, complete=False)
        self._temp_dir.cleanup()
        if not self._closed:
            self._closed = True

    def add_document(
        self,
        collector: str,
        collector_v: str,
        key: str,
        url: str,
        status: int,
        headers: dict[str, str],
        email_removed: bool,
        body: str,
        time: str,
    ) -> None:
        encoded_body = body.encode("utf-8")
        digest = hashlib.sha256(encoded_body).hexdigest()
        size = len(encoded_body)

        snapshot = Snapshot(
            key,
            url,
            time,
            status,
            headers,
            digest,
            size,
            collector,
            collector_v,
            email_removed,
        )

        full_path = self._base_path / key
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(encoded_body)

        self._index.append(snapshot)

    def close_document(
        self,
        ruleset_digest: str | None,
        sbom_digest: str | None,
        baselines_digest: str | None,
        complete: bool = True,
    ) -> tuple[Path, str, dict[str, Any]]:
        if self._closed:
            raise core_exc.InputError("Writer was close previously")

        self._closed = True

        end_time = self.clock().isoformat()

        index_list = [dataclasses.asdict(item) for item in self._index]

        index_data = (
            json.dumps(index_list, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        )
        (self._base_path / "index.json").write_bytes(index_data)

        services_list = sorted(
            {
                host
                for item in self._index
                if (host := urlparse(getattr(item, "url", "")).hostname) is not None
            }
        )

        manifest_dict = {
            "run_identifier": self.execution_id,
            "tool_version": version("purlwatch-core"),
            "ruleset_digest": ruleset_digest,
            "sbom_digest": sbom_digest,
            "baselines_digest": baselines_digest,
            "services": services_list,
            "start_time": self.start_time,
            "end_time": end_time,
            "complete": complete,
        }

        manifest_data = (
            json.dumps(manifest_dict, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        )
        (self._base_path / "manifest.json").write_bytes(manifest_data)

        files = [path for path in self._base_path.rglob("*") if path.is_file()]
        path_list = sorted(
            files, key=lambda path: path.relative_to(self._base_path).as_posix()
        )

        snapshots_dir = self._out_path
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        tar_path = snapshots_dir / f"{self.execution_id}.tar"
        with tarfile.open(tar_path, "w") as tar:
            for filepath in path_list:
                tar.add(
                    name=filepath,
                    arcname=filepath.relative_to(self._base_path).as_posix(),
                    filter=self.tarinfo_filter,
                    recursive=False,
                )

        with tar_path.open("rb") as file:
            final_digest = hashlib.file_digest(file, hashlib.sha256).hexdigest()

        return tar_path, final_digest, manifest_dict

    def tarinfo_filter(self, ti: tarfile.TarInfo) -> tarfile.TarInfo:
        ti.mtime = 0
        ti.uid = 0
        ti.gid = 0
        ti.uname = ""
        ti.gname = ""
        ti.mode = 0o644
        return ti


class SnapshotReader:
    def __init__(self, tar: Path):
        try:
            archive = tarfile.open(tar, "r")  # noqa: SIM115
        except (KeyError, FileNotFoundError) as err:
            raise ReaderFileNotFoundError(f"File was not found for tar {tar}") from err
        except tarfile.ReadError as err:
            raise core_exc.InputError(f"File {tar} is not a valid tar") from err

        try:
            manifest_file = archive.extractfile("manifest.json")
            if not manifest_file:
                raise ReaderFileNotFoundError(
                    f"File manifest.json was not found for tar {tar}"
                )
            self.manifest = json.load(manifest_file)

            index_file = archive.extractfile("index.json")
            if not index_file:
                raise ReaderFileNotFoundError(
                    f"File index.json was not found for tar {tar}"
                )
            index_list = json.load(index_file)

            self._index = {entry["path"]: entry for entry in index_list}

            self.tar: tarfile.TarFile = archive
        except (KeyError, FileNotFoundError):
            archive.close()
            raise ReaderFileNotFoundError(f"File was not found for tar {tar}")

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def get_document(self, key: str) -> tuple[bytes, dict[str, Any]]:
        if key not in self._index:
            raise ReaderFileNotFoundError(f"Data was not found for: {key}")

        entry = self._index[key]

        body_file = self.tar.extractfile(entry["path"])
        if body_file is None:
            raise ReaderFileNotFoundError(f"File missing in archive for key: {key}")

        body = body_file.read()

        if hashlib.sha256(body).hexdigest() != entry["sha256"]:
            raise core_exc.InputError(f"Digest mismatch for: {key}")

        return body, entry

    def close(self) -> None:
        self.tar.close()
