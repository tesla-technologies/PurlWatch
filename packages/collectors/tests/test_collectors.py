from pathlib import Path

import pytest
from auratrace_collectors.crates import replay as crates_replay
from auratrace_collectors.npm import replay as npm_replay

TEST_DIR = Path(__file__).parent


@pytest.mark.parametrize(
    ("fixture", "n_versions", "n_maint", "n_trusted"),
    [(Path(f"{TEST_DIR}/fixtures/npm/is_sorted.json"), 6, 6, 0)],
)
def test_npm_replay_fact(
    fixture: Path, n_versions: int, n_maint: int, n_trusted: int
) -> None:
    result = npm_replay(fixture)

    assert len(result.versions) == n_versions

    r_maint = 0
    r_trusted = 0
    for v_data in result.versions.values():
        if v_data.maintainers:
            r_maint += 1

        if v_data.trusted_publishing:
            r_trusted += 1

    assert n_maint == r_maint
    assert n_trusted == r_trusted


@pytest.mark.parametrize(
    ("v_json", "o_json", "n_versions", "n_yanked"),
    [
        (
            Path(f"{TEST_DIR}/fixtures/crates/void_versions.json"),
            Path(f"{TEST_DIR}/fixtures/crates/void_owners.json"),
            8,
            0,
        ),
        (
            Path(f"{TEST_DIR}/fixtures/crates/fuchsia_versions.json"),
            Path(f"{TEST_DIR}/fixtures/crates/fuchsia_owners.json"),
            2,
            1,
        ),
    ],
)
def test_crates_replay_fact(
    v_json: Path, o_json: Path, n_versions: int, n_yanked: int
) -> None:
    result = crates_replay(v_json, o_json)

    assert result.name
    assert result.current_owners is not None
    assert len(result.current_owners) > 0

    assert len(result.versions) == n_versions

    r_yanked = 0
    for v_data in result.versions.values():
        if v_data.yanked:
            r_yanked += 1

    assert n_yanked == r_yanked
