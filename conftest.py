import gzip
import json
from typing import Any

import pytest
from purlwatch_collectors.common import sanitize_payload


@pytest.fixture(scope="module")
def vcr_config() -> dict[str, Any]:
    return {
        "decode_compressed_response": True,
        "filter_headers": ["authorization", "cookie", "set-cookie"],
        "before_record_response": scrub_response,
    }


def scrub_response(response: dict[str, Any]) -> dict[str, Any]:
    """Sanitize HTTP responses' body before recording cassettes"""
    try:
        raw_body = response["body"]["string"]
        is_gzipped = False

        if isinstance(raw_body, bytes):
            if raw_body.startswith(b"\x1f\x8b"):
                is_gzipped = True
                raw_body = gzip.decompress(raw_body)
            raw_body = raw_body.decode("utf-8")

        payload = json.loads(raw_body)
        clean_json_str, _ = sanitize_payload(payload)
        clean_bytes = clean_json_str.encode("utf-8")

        if is_gzipped:
            clean_bytes = gzip.compress(clean_bytes)

        response["body"]["string"] = clean_bytes

        headers = response.get("headers", {})
        for header_key in headers:
            if header_key.lower() == "content-length":
                headers[header_key] = [str(len(clean_bytes))]

    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, gzip.BadGzipFile):
        pass

    return response
