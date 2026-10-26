import os
import subprocess
import sys
from pathlib import Path

import pytest

TEST_DIR = Path(__file__).resolve()
ROOT_DIR = Path(__file__).parent.parent
SCAN_SCRIPT = ROOT_DIR / "scripts" / "email-scan.py"
PYTHON_BIN = sys.executable
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "node_modules",
    "dist",
    "build",
}


def test_fixtures_without_emails() -> None:

    fixture_paths: list[str] = []

    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        root_path = Path(root)

        if "fixtures" in root_path.parts or "cassettes" in root_path.parts:
            for filename in files:
                file_path = root_path / filename
                fixture_paths.append(str(file_path))

    if not fixture_paths:
        pytest.skip("Not fixtures were found")

    cmd = [sys.executable, str(SCAN_SCRIPT)] + fixture_paths

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    assert result.returncode == 0, (
        f"{'=' * 20} STDOUT (Emails found) {'=' * 20}\n{result.stdout}"
    )
