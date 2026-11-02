from dataclasses import dataclass
from typing import cast

from purlwatch_core import parser, resolve


@dataclass(frozen=True)
class DummyComponent:
    bom_ref: str
    purl: str | None = None
    external_ref: str | None = None


@dataclass(frozen=True)
class DummyDependency:
    source: str
    target: str


@dataclass(frozen=True)
class DummySBOM:
    root_comp: DummyComponent
    comp_list: list[DummyComponent]
    dependencies: list[DummyDependency]


def make_sbom(
    root: str,
    components: list[tuple[str, str | None]],
    deps: list[tuple[str, str]],
) -> parser.ParsedSBOM:
    comp_objects = [DummyComponent(bom_ref=ref, purl=purl) for ref, purl in components]
    root_obj = next(c for c in comp_objects if c.bom_ref == root)
    dep_objects = [DummyDependency(source=src, target=tgt) for src, tgt in deps]

    dummy = DummySBOM(
        root_comp=root_obj, comp_list=comp_objects, dependencies=dep_objects
    )
    return cast(parser.ParsedSBOM, dummy)


def test_chain_resolution() -> None:
    sbom = make_sbom(
        root="A",
        components=[
            ("A", "pkg:npm/a@1.0.0"),
            ("B", "pkg:npm/b@1.0.0"),
            ("C", "pkg:npm/c@1.0.0"),
        ],
        deps=[("A", "B"), ("B", "C")],
    )

    resolved = resolve.resolve(sbom)

    assert resolved.nodes["A"].depth == 0
    assert resolved.nodes["B"].depth == 1
    assert resolved.nodes["C"].depth == 2
    assert resolved.nodes["C"].via == "B"

    via_map = {ref: node.via for ref, node in resolved.nodes.items() if node.via}
    assert resolve.path_to("C", via_map) == ["A", "B", "C"]


def test_diamond_resolution() -> None:
    sbom = make_sbom(
        root="A",
        components=[
            ("A", "pkg:npm/a@1.0.0"),
            ("B", "pkg:npm/b@1.0.0"),
            ("C", "pkg:npm/c@1.0.0"),
            ("D", "pkg:npm/d@1.0.0"),
        ],
        deps=[("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")],
    )

    resolved = resolve.resolve(sbom)

    assert len(resolved.nodes) == 4
    assert resolved.nodes["D"].depth == 2
    assert resolved.nodes["D"].via == "B"


def test_cycle_resolution() -> None:
    sbom = make_sbom(
        root="A",
        components=[
            ("A", "pkg:npm/a@1.0.0"),
            ("B", "pkg:npm/b@1.0.0"),
            ("C", "pkg:npm/c@1.0.0"),
        ],
        deps=[("A", "B"), ("B", "C"), ("C", "B")],
    )

    resolved = resolve.resolve(sbom)

    assert resolved.nodes["B"].depth == 1
    assert resolved.nodes["C"].depth == 2
    assert resolved.nodes["B"].via == "A"
    assert resolved.nodes["C"].via == "B"


def test_no_purl_middle_resolution() -> None:
    sbom = make_sbom(
        root="A",
        components=[
            ("A", "pkg:npm/a@1.0.0"),
            ("X", None),
            ("B", "pkg:npm/b@1.0.0"),
        ],
        deps=[("A", "X"), ("X", "B")],
    )

    resolved = resolve.resolve(sbom)

    assert resolved.nodes["X"].route == resolve.Route.NO_PURL
    assert resolved.nodes["B"].depth == 2
    assert resolved.nodes["B"].via == "X"


def test_unreachable_node_resolution() -> None:
    sbom = make_sbom(
        root="A",
        components=[
            ("A", "pkg:npm/a@1.0.0"),
            ("B", "pkg:npm/b@1.0.0"),
            ("Z", "pkg:npm/z@1.0.0"),
        ],
        deps=[("A", "B")],
    )

    resolved = resolve.resolve(sbom)

    assert "Z" in resolved.nodes
    assert resolved.nodes["Z"].depth is None
    assert resolved.nodes["Z"].via is None


def test_dual_version_deduplication_key() -> None:
    sbom = make_sbom(
        root="A",
        components=[
            ("A", "pkg:npm/a@1.0.0"),
            ("lodash-v1", "pkg:npm/lodash@4.17.20"),
            ("lodash-v2", "pkg:npm/lodash@4.17.21"),
        ],
        deps=[("A", "lodash-v1"), ("A", "lodash-v2")],
    )

    resolved = resolve.resolve(sbom)

    assert resolved.nodes["lodash-v1"].package == "pkg:npm/lodash"
    assert resolved.nodes["lodash-v2"].package == "pkg:npm/lodash"
    assert resolved.nodes["lodash-v1"].ref != resolved.nodes["lodash-v2"].ref


def test_root_node_flags() -> None:
    sbom = make_sbom(
        root="A",
        components=[
            ("A", "pkg:npm/express@4.18.2"),
            ("B", "pkg:npm/debug@4.3.4"),
        ],
        deps=[("A", "B")],
    )

    resolved = resolve.resolve(sbom)

    assert resolved.nodes["A"].is_root is True
    assert resolved.nodes["A"].depth == 0
    assert resolved.nodes["A"].via is None
    assert resolved.nodes["B"].is_root is False
