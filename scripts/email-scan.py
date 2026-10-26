import base64
import binascii
import gzip
import io
import re
import sys
import tarfile
from collections.abc import Iterable
from pathlib import Path

ALLOWED_EMAIL_DOMAINS = (
    "@example.com",
    "@example.org",
    "@example.net",
)


def extract_tarfile(file: Path, pattern: re.Pattern) -> bool:
    has_email = False

    try:
        with tarfile.open(file, "r:*", encoding="utf-8") as tar:
            for member in tar:
                try:
                    if not member.isfile():
                        continue

                    member_bytes = tar.extractfile(member)
                    if not member_bytes:
                        continue

                    wrapper = io.TextIOWrapper(
                        member_bytes, encoding="utf-8", errors="replace"
                    )
                    if scan_for_email(wrapper, f"{file}:{member.name}", pattern):
                        has_email = True

                except (tarfile.TarError, OSError) as err:
                    print(
                        f"Warning: could not process {file}:{member.name}: {err}",
                        file=sys.stderr,
                    )
                    continue

    except (tarfile.TarError, OSError) as err:
        print(f"Warning: could not open archive {file}: {err}", file=sys.stderr)

    return has_email


def extract_cassette(file: Path, pattern: re.Pattern) -> bool:
    has_emails = False

    def process_buffer(body_buffer: list[str]) -> bool:
        try:
            b64_str = "".join(body_buffer).strip()
            bytes_str = base64.b64decode(b64_str)

            if bytes_str.startswith(b"\x1f\x8b"):
                bytes_str = gzip.decompress(bytes_str)
            lines = bytes_str.decode("utf-8", errors="replace").splitlines()

            if scan_for_email(lines, file, pattern):
                return True
        except (binascii.Error, ValueError, gzip.BadGzipFile) as err:
            print(
                f"Warning: cassette data is corrupt or incomplete {file}: {err}",
                file=sys.stderr,
            )

        return False

    try:
        with open(file, "r", encoding="utf-8", errors="replace") as f:
            body_buffer = []
            reading_body = False
            base_indent = 0

            for line in f:
                curr_indent = len(line) - len(line.lstrip(" "))

                if not reading_body and "!!binary" in line:
                    base_indent = curr_indent
                    reading_body = True
                    continue

                if reading_body:
                    if not line.strip():
                        continue
                    if curr_indent <= base_indent:
                        reading_body = False
                        has_emails = process_buffer(body_buffer)
                        body_buffer = []
                    else:
                        body_buffer.append(line)

            if len(body_buffer) > 0:
                has_emails = process_buffer(body_buffer)

    except OSError as err:
        print(f"Warning: could not open cassette {file}: {err}", file=sys.stderr)

    return has_emails


def scan_for_email(f: Iterable[str], file: Path | str, pattern: re.Pattern) -> bool:
    has_emails = False

    try:
        for line_num, line in enumerate(f, start=1):
            email = pattern.search(line)
            if email:
                if email.group(0).lower().endswith(ALLOWED_EMAIL_DOMAINS):
                    continue

                print(f"Error at {file}: {line_num} -> An email address was found.")
                print(f"Email -> {email.group(0)}")
                for match in pattern.finditer(line):
                    start = max(0, match.start() - 30)
                    end = min(len(line), match.end() + 30)
                    snippet = line[start:end].replace("\n", " ").strip()

                    print(
                        f"{file}:{line_num}: email detected -> {match.group(0)} | Context: ...{snippet}..."
                    )
                has_emails = True

    except UnicodeDecodeError as err:
        print(f"Warning: could not process {file}: {err}", file=sys.stderr)

    return has_emails


def main() -> int:
    files = [Path(file) for file in sys.argv[1:]]
    has_emails = False
    pattern = re.compile(
        r"(?<!://)(?<!:)\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )

    if len(files) == 0:
        return 0

    for file in files:
        if file.name.endswith((".tar", ".tar.gz", ".tgz")) and extract_tarfile(
            file, pattern
        ):
            has_emails = True

        if "cassettes" in file.parts and file.name.endswith((".yaml", ".yml")):
            if extract_cassette(file, pattern):
                has_emails = True

        else:
            try:
                with open(file, "r", encoding="utf-8", errors="replace") as f:
                    if scan_for_email(f, file, pattern):
                        has_emails = True
            except OSError as err:
                print(f"Warning: could not process {file}: {err}", file=sys.stderr)

    return 1 if has_emails else 0


if __name__ == "__main__":
    sys.exit(main())
