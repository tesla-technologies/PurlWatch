from pathlib import Path

import pytest
from auratrace_collectors.npm import replay

TEST_DIR = Path(__file__).parent


@pytest.mark.parametrize(
    ("fixture", "n_versions", "n_maint", "n_trusted"),
    [(Path(f"{TEST_DIR}/fixtures/npm/is_sorted.json"), 6, 6, 0)],
)
def test_replay_fact(
    fixture: Path, n_versions: int, n_maint: int, n_trusted: int
) -> None:
    result = replay(fixture)

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
