#!/usr/bin/env python3
import re
import sys


def main() -> int:
    files = sys.argv[1:]
    has_emails = False
    pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

    if len(files) == 0:
        return 0

    for file in files:
        try:
            with open(file, "r") as f:
                for line_num, line in enumerate(f, start=1):
                    if pattern.search(line):
                        print(
                            f"Error at {file}:{line_num} -> An email adress was found."
                        )
                        has_emails = True
        except (UnicodeDecodeError, FileNotFoundError):
            continue

    if has_emails:
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
