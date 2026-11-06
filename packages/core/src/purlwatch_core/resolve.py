from collections import deque
from dataclasses import dataclass
from enum import Enum

from packageurl import PackageURL

from purlwatch_core.parser import Component, ParsedSBOM


class Route(str, Enum):
    REGISTRY = "registry"
    REPOSITORY_ONLY = "repository"
    UNSUPPORTED = "unsupported"
    NO_PURL = "no_purl"


class Declared(str, Enum):
    EXTERNAL = "external"
    VCS_URL = "vcs_url"
    PURL = "purl"


@dataclass(frozen=True)
class Node:
    ref: str
    purl: str | None
    package: str | None
    route: Route
    is_root: bool
    depth: int | None
    via: str | None
    declared_repo: list[tuple[Declared, str]]


@dataclass(frozen=True)
class Resolved:
    root: str | None
    nodes: dict[str, Node]
    edges: dict[str, frozenset[str]]


REGISTRY_TYPES = {"npm", "cargo"}

REPOSITORY_TYPES = {"generic", "github", "bitbucket", "deb"}


def get_purl_without_version(purl: str | None) -> str | None:
    if not purl:
        return None

    parsed_purl = PackageURL.from_string(purl)

    clean_purl = PackageURL(
        type=parsed_purl.type,
        namespace=parsed_purl.namespace,
        name=parsed_purl.name,
    )

    return str(clean_purl)


def get_node_route(purl: str | None) -> Route:
    if not purl:
        return Route.NO_PURL

    purl_type = PackageURL.from_string(purl).type

    if purl_type in REGISTRY_TYPES:
        return Route.REGISTRY
    elif purl_type in REPOSITORY_TYPES:
        return Route.REPOSITORY_ONLY
    else:
        return Route.UNSUPPORTED


def extract_repo_from_purl(purl_str: str | None) -> list[tuple[Declared, str]]:
    if not purl_str:
        return []

    purl = PackageURL.from_string(purl_str)
    declared_list = []

    if purl.type == "github" and purl.name:
        if purl.namespace:
            declared_list.append(
                (Declared.PURL, f"https://github.com/{purl.namespace}/{purl.name}")
            )
        else:
            declared_list.append((Declared.PURL, f"https://github.com/{purl.name}"))

    if purl.type == "bitbucket" and purl.name:
        if purl.namespace:
            declared_list.append(
                (Declared.PURL, f"https://bitbucket.org/{purl.namespace}/{purl.name}"),
            )
        else:
            declared_list.append((Declared.PURL, f"https://bitbucket.org/{purl.name}"))

    vcs_url = purl.qualifiers.get("vcs_url") if purl.qualifiers else None
    if vcs_url and (not declared_list or declared_list[0][1] == vcs_url):
        declared_list.append((Declared.VCS_URL, vcs_url))

    return declared_list


def extract_declared_repo(comp: Component) -> list[tuple[Declared, str]]:
    declared_list = extract_repo_from_purl(comp.purl)

    if comp.external_ref is not None and (
        not declared_list or declared_list[0][1] == comp.external_ref
    ):
        declared_list.append((Declared.EXTERNAL, comp.external_ref))

    return declared_list


def resolve(sbom: ParsedSBOM) -> Resolved:
    node_dict = {}
    edges = build_edges(sbom)
    root_ref = None
    depth: dict[str, int] = {}
    via: dict[str, str] = {}

    if sbom.root_comp:
        root = sbom.root_comp
        depth, via = bfs_from_root(root.bom_ref, edges)
        root_ref = root.bom_ref
        declared_root = extract_declared_repo(root)

        node_dict[root.bom_ref] = Node(
            ref=root.bom_ref,
            purl=root.purl,
            package=get_purl_without_version(root.purl),
            route=get_node_route(root.purl),
            is_root=True,
            depth=depth[root.bom_ref],
            via=None,
            declared_repo=declared_root,
        )

    for comp in sbom.comp_list:
        declared = extract_declared_repo(comp)
        node = Node(
            ref=comp.bom_ref,
            purl=comp.purl,
            package=get_purl_without_version(comp.purl),
            route=get_node_route(comp.purl),
            is_root=(comp.bom_ref == root_ref),
            depth=depth.get(comp.bom_ref),
            via=via.get(comp.bom_ref),
            declared_repo=declared,
        )

        node_dict[comp.bom_ref] = node

    return Resolved(root_ref, node_dict, edges)


def build_edges(sbom: ParsedSBOM) -> dict[str, frozenset[str]]:
    ref_dict: dict[str, str] = {}
    graph: dict[str, set[str]] = {}

    if sbom.root_comp:
        ref_dict[sbom.root_comp.bom_ref] = sbom.root_comp.bom_ref

    for comp in sbom.comp_list:
        if comp.bom_ref:
            ref_dict[comp.bom_ref] = comp.bom_ref

        if comp.bom_ref not in graph:
            graph[comp.bom_ref] = set()

    for dep in sbom.dependencies:
        src = ref_dict.get(dep.source) if dep.source else None
        if not src:
            continue

        if src not in graph:
            graph[src] = set()

        tgt = ref_dict.get(dep.target) if dep.target else None
        if tgt:
            graph[src].add(tgt)

    return {ref: frozenset(children) for ref, children in graph.items()}


def bfs_from_root(
    root: str, edges: dict[str, frozenset[str]]
) -> tuple[dict[str, int], dict[str, str]]:
    depth = {root: 0}
    via: dict[str, str] = {}
    queue = deque([root])
    while queue:
        node = queue.popleft()
        for child in sorted(edges.get(node, ())):
            if child not in depth:
                depth[child] = depth[node] + 1
                via[child] = node
                queue.append(child)
    return depth, via


def path_to(node: str, via: dict[str, str]) -> list[str]:
    out = [node]
    while out[-1] in via:
        out.append(via[out[-1]])
    return out[::-1]
