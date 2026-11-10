import os
import subprocess
import sys


def check_signoff() -> int:
    base_sha = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.getenv("CI_MERGE_REQUEST_DIFF_BASE_SHA")
    )

    if not base_sha and len(sys.argv) == 1:
        print(
            "[ERROR] CI_MERGE_REQUEST_DIFF_BASE_SHA no encontrada. Este check solo se ejecuta en pipelines de MR."
        )
        return 1

    if not base_sha or not base_sha.strip("0"):
        base_sha = "origin/main"

    result = subprocess.run(
        ["git", "rev-list", "--no-merges", f"{base_sha}..HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )

    commits = [c.strip() for c in result.stdout.strip().splitlines() if c.strip()]

    if not commits:
        print("No se encontraron commits en este rango.")
        return 0

    missing_signoff = False
    for commit in commits:
        log_out = subprocess.run(
            ["git", "log", "-1", "--format=%B", commit],
            capture_output=True,
            text=True,
            check=True,
        )
        if "Signed-off-by:" not in log_out.stdout:
            print(f"Commit sin firma: {commit}")
            missing_signoff = True
        else:
            print(f"Commit firmado: {commit}")

    if missing_signoff:
        print("\n[ERROR] Al menos un commit carece de 'Signed-off-by:'.")
        print("Solución en tu rama local:")
        print(f"  git rebase -i {base_sha} --exec 'git commit --amend -s --no-edit'")
        return 1

    print("\nOK: Todos los commits contienen la firma.")
    return 0


if __name__ == "__main__":
    sys.exit(check_signoff())
