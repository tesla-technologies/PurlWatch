import auratrace_core.exceptions as core_exc
import pytest
from auratrace_core.hashing import identity_hid


def test_hash_nonexistance_throws_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AURATRACE_HASH_KEY", raising=False)
    with pytest.raises(core_exc.InputError):
        identity_hid("npm", "isaacs")


def test_empty_hash_throws_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AURATRACE_HASH_KEY", "")
    with pytest.raises(core_exc.InputError):
        identity_hid("npm", "isaacs")


def test_valid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AURATRACE_HASH_KEY", "test-key")

    key1 = identity_hid("npm", "isaacs")
    key2 = identity_hid("npm", "isaacs")

    assert isinstance(key1, str)
    assert key1 == key2


def test_different_keys_produce_different_hashes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    monkeypatch.setenv("AURATRACE_HASH_KEY", "key-1")
    key1 = identity_hid("npm", "isaacs")

    monkeypatch.setenv("AURATRACE_HASH_KEY", "key-2")
    key2 = identity_hid("npm", "isaacs")

    assert key1 != key2


def test_different_registry_different_hashes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AURATRACE_HASH_KEY", "key")

    hash_1 = identity_hid("npm", "isaacs")
    hash_2 = identity_hid("crates", "isaacs")
    hash_3 = identity_hid("np", "misaacs")

    assert hash_1 != hash_2
    assert hash_1 != hash_3
