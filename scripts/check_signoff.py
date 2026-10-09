import os
import subprocess
import sys


def check_signoff() -> int:
    base_sha = os.getenv("CI_MERGE_REQUEST_DIFF_BASE_SHA")
    if not base_sha:
        print(
            "[ERROR] Variable CI_MERGE_REQUEST_DIFF_BASE_SHA no encontrada. "
            "Este script debe ejecutarse en pipelines de Merge Request."
        )
        return 1

    result = subprocess.run(
        ["git", "rev-list", f"{base_sha}..HEAD"],
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
