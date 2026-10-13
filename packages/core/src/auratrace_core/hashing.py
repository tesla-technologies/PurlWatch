import hashlib
import hmac
import os


def generate_hashed_key(url: str) -> str:
    env_key = os.getenv("AURATRACE_HASH_KEY")

    if not env_key:
        raise ValueError(
            "Environment variable AURATRACE_HASH_KEY it´s empty or not found."
        )

    encoded_env_key = env_key.encode("utf-8")
    encoded_url = url.encode("utf-8")

    digest = hmac.digest(encoded_env_key, encoded_url, hashlib.sha256).hex()

    return digest
