import json
from pathlib import Path
from typing import Any

import pytest
from purlwatch_collectors import common

TEST_DIR = Path(__file__).parent


@pytest.mark.parametrize(
    ("packument", "removed"), [(Path(f"{TEST_DIR}/fixtures/npm/is_sorted.json"), True)]
)
def test_validate_email_validate(packument: Path, removed: bool) -> None:
    with open(packument, "r", encoding="utf-8") as pack:
        pack_json = json.load(pack)
        result_json, email_removed = common.sanitize_payload(pack_json)

        sanitized_json = json.loads(result_json)

        def has_key(data: Any, key: str) -> bool:
            if isinstance(data, dict):
                if key in data:
                    return True
                return any(has_key(v, key) for v in data.values())
            if isinstance(data, list):
                return any(has_key(item, key) for item in data)
            return False

        has_email = has_key(sanitized_json, "email")

        def get_repositories(
            data: Any, repo_list: list[str] | None = None
        ) -> list[str]:
            if repo_list is None:
                repo_list = []

            if isinstance(data, dict):
                if "repository" in data:
                    repo_list.append(data.get("repository", "").get("url", ""))

                for v in data.values():
                    get_repositories(v, repo_list)

            if isinstance(data, list):
                for item in data:
                    get_repositories(item, repo_list)

            return repo_list

        sanitized_list = get_repositories(sanitized_json)
        raw_list = get_repositories(pack_json)

    assert sanitized_list == raw_list
    assert not has_email
    assert email_removed == removed


def test_validate_headers() -> None:
    simulated_headers = {
        "Content-Type": "application/json; charset=utf-8",
        "ETag": 'W/"1a2b3c4d5e"',
        "Last-Modified": "Wed, 21 Oct 2026 07:28:00 GMT",
        "Date": "Wed, 21 Oct 2026 08:00:00 GMT",
        "Cache-Control": "public, max-age=300, must-revalidate",
        "Age": "120",
        "Expires": "Wed, 21 Oct 2026 08:05:00 GMT",
        "Content-Length": "4502",
        "Content-Encoding": "gzip",
        "Vary": "Accept-Encoding",
        "X-RateLimit-Limit": "100",
        "X-RateLimit-Remaining": "42",
        "X-RateLimit-Reset": "1697880000",
        "X-RateLimit-Resource": "core",
        "X-RateLimit-Used": "58",
        "Retry-After": "60",
        "Server": "cloudflare",
        "CF-RAY": "8a1b2c3d4e5f-MAD",
        "Set-Cookie": "session=xyz123; Path=/; HttpOnly; Secure",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Connection": "keep-alive",
        "Keep-Alive": "timeout=5",
        "Transfer-Encoding": "chunked",
    }

    expected_keys = {
        "Content-Type",
        "ETag",
        "Last-Modified",
        "Date",
        "Cache-Control",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "X-RateLimit-Resource",
        "X-RateLimit-Used",
    }

    final_headers = common.extract_allowed_headers(simulated_headers)

    assert set(final_headers.keys()) == expected_keys
