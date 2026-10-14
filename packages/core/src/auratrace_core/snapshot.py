import dataclasses
import hashlib
import json
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


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
    def __init__(self, execution_id: str):
        self.execution_id: str = execution_id + "atwriter"
        self.start_time = datetime.now(timezone.utc).isoformat()
        self._index: list[Snapshot] = []
        self._base_path: Path = Path("tmp/auratrace/")

    def add_document(
        self,
        collector: str,
        collector_v: str,
        key: str,
        url: str,
        status: int,
        headers: dict[str, str],
        body: str,
    ) -> None:
        encoded_body = body.encode("utf-8")
        digest = hashlib.sha256(encoded_body).hexdigest()
        time = datetime.now(timezone.utc).isoformat()
        size = len(encoded_body)

        snapshot = Snapshot(
            key, url, time, status, headers, digest, size, collector, collector_v, True
        )

        full_path = self._base_path / key
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(encoded_body)

        self._index.append(snapshot)

    def close_document(
        self, ruleset_digest: str, sbom_digest: str, baselines_digest: str
    ) -> tuple[Path, str]:
        end_time = datetime.now(timezone.utc).isoformat()

        index_list = [dataclasses.asdict(item) for item in self._index]

        with open(self._base_path / "index.json", "w", encoding="utf-8") as index:
            json.dump(index_list, index, indent=2)

        services_list = sorted({item.collector for item in self._index})

        manifest_dict = {
            "run_identifier": self.execution_id,
            "tool_version": "0.1.0",  # TODO: Cambiar por la variable de versión
            "ruleset_digest": ruleset_digest,
            "sbom_digest": sbom_digest,
            "baselines_digest": baselines_digest,
            "services": services_list,
            "start_time": self.start_time,
            "end_time": end_time,
        }

        with open(self._base_path / "manifest.json", "w", encoding="utf-8") as manifest:
            json.dump(manifest_dict, manifest, indent=2)

        files = [path for path in self._base_path.rglob("*") if path.is_file()]
        path_list = sorted(
            files, key=lambda path: path.relative_to(self._base_path).as_posix()
        )

        snapshots_dir = Path("snapshots")
        snapshots_dir.mkdir(exist_ok=True)
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

        return tar_path, final_digest

    def tarinfo_filter(self, ti: tarfile.TarInfo) -> tarfile.TarInfo:
        ti.mtime = 0
        ti.uid = 0
        ti.gid = 0
        ti.uname = ""
        ti.gname = ""
        return ti
