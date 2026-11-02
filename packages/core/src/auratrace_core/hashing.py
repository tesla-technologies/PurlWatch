import hashlib
import hmac
import os

import auratrace_core.exceptions as core_exc


def identity_hid(registry: str, handle: str) -> str:
    env_key = os.getenv("AURATRACE_HASH_KEY")

    final_str = registry + "/" + handle

    if not env_key:
        raise core_exc.InputError(
            "Environment variable AURATRACE_HASH_KEY it´s empty or not found."
        )

    encoded_env_key = env_key.encode("utf-8")
    encoded_str = final_str.encode("utf-8")

    return hmac.digest(encoded_env_key, encoded_str, hashlib.sha256).hex()


def short_hid(hid: str) -> str:
    return f"h:{hid[:8]}"
