import pytest
from purlwatch_cli.resolve import resolve_component
from purlwatch_core import resolve


class FakeSource:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def npm(self, purl: str) -> None:
        self.calls.append(("npm", purl))

    def crates(self, purl: str) -> None:
        self.calls.append(("crates", purl))

    def ecosystems(self, purl: str) -> None:
        self.calls.append(("ecosystems", purl))


@pytest.mark.parametrize(
    "declared_repo",
    [
        "https://github.com/my-org/my-root-repo",
        None,
    ],
)
def test_resolve_component_never_consults_sources_for_root(declared_repo: str) -> None:
    fake_source = FakeSource()

    root_node = resolve.Node(
        ref="root-project@1.0.0",
        purl="pkg:npm/root-project@1.0.0",
        package="pkg:npm/root-project@1.0.0",
        route=resolve.Route.REGISTRY,
        is_root=True,
        depth=0,
        via=None,
        declared_repo=declared_repo,
    )

    nodes = {"root-project@1.0.0": root_node}

    results = resolve_component(nodes, fake_source)

    assert fake_source.calls == []

    assert len(results) == 1
    _, _, comp, note = results[0]

    assert comp.is_root is True
    if declared_repo:
        assert note == "Note: Repository only path"
    else:
        assert note == "Note: Root component has no declared VCS repository"
