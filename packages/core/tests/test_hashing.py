import pytest
from auratrace_core.hashing import generate_hashed_key


def test_hash_nonexistance_throws_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AURATRACE_HASH_KEY", raising=False)
    with pytest.raises(ValueError):
        generate_hashed_key("https://github/isaac/is-sorted")


def test_empty_hash_throws_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AURATRACE_HASH_KEY", "")
    with pytest.raises(ValueError):
        generate_hashed_key("https://github/isaac/is-sorted")


def test_valid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AURATRACE_HASH_KEY", "test-key")
    url = "https://github/isaac/is-sorted"

    key1 = generate_hashed_key(url)
    key2 = generate_hashed_key(url)

    assert isinstance(key1, str)
    assert len(key1) == 64
    assert key1 == key2


def test_different_keys_produce_different_hashes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    url = "https://github.com/org/repo"

    monkeypatch.setenv("AURATRACE_HASH_KEY", "key-1")
    key1 = generate_hashed_key(url)

    monkeypatch.setenv("AURATRACE_HASH_KEY", "key-2")
    key2 = generate_hashed_key(url)

    assert key1 != key2
