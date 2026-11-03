import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from cyclonedx.exception import CycloneDxException
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import (
    Component as CycloneDXComponent,
)
from packageurl import PackageURL
from spdx_tools.spdx.parser.parse_anything import parse_file

import purlwatch_core.exceptions as core_exc


@dataclass(frozen=True)
class Dependency:
    source: str
    target: str | None


@dataclass(frozen=True)
class Component:
    name: str
    version: str | None
    bom_ref: str
    purl: str | None
    external_ref: str | None


@dataclass(frozen=True)
class ParsedSBOM:
    format: str
    version: str
    root_comp: Component | None
    comp_list: list[Component]
    dependencies: list[Dependency]


class UnsupportedFormatError(core_exc.InputError):
    """Raised when file format or version it's not supported."""


class InvalidStructureError(core_exc.InputError):
    """Raised when file structure it's not the expected one"""


class SbomNotFoundError(core_exc.InputError):
    """Raised when sbom it's not added"""


def parse_sbom(sbom: Path) -> ParsedSBOM:
    if not sbom.exists():
        raise SbomNotFoundError(f"SBOM file not found {sbom}")

    try:
        with open(sbom, "r", encoding="utf-8") as s:
            raw_json = json.load(s)
            cyclone_versions = ["1.5", "1.6", "1.7"]
            spdx_versions = ["SPDX-2.2", "SPDX-2.3"]

            if "bomFormat" in raw_json and raw_json["specVersion"] in cyclone_versions:
                return cyclone_parser(sbom)
            elif "spdxVersion" in raw_json and raw_json["spdxVersion"] in spdx_versions:
                return spdx_parser(sbom)
            else:
                raise UnsupportedFormatError("SBOM format or version is not supported")
    except (CycloneDxException, KeyError) as err:
        raise InvalidStructureError(f"File structure it's not valid: {err}")
    except json.JSONDecodeError as err:
        raise InvalidStructureError(f"File it's not a valid JSON: {err}")


def cyclone_parser(sbom: Path) -> ParsedSBOM:
    json_data = json.loads(sbom.read_text(encoding="utf-8"))
    bom: Bom = Bom.from_json(data=json_data)  # type: ignore[attr-defined]

    parsed_root = None
    if bom.metadata.component:
        root_component = bom.metadata.component

        root_external_ref = None
        if root_component.external_references:
            for ref in root_component.external_references:
                if ref.type == "vcs":
                    root_external_ref = str(ref.url)
                    break

        root_ref = root_component.bom_ref.value or f"{root_component.name}_ref"

        parsed_root = Component(
            root_component.name,
            root_component.version,
            root_ref,
            parse_purl(root_component.purl) or None,
            root_external_ref,
        )

    dependencies = []
    comp_list: list[Component] = []
    if bom.dependencies:
        for dependency in bom.dependencies:
            source = dependency.ref.value
            depends_list = [child.ref.value for child in dependency.dependencies]
            if len(depends_list) > 0:
                for target in depends_list:
                    dependencies.append(Dependency(source, target))
            else:
                dependencies.append(Dependency(source, None))

    comp_list = cyclone_recursive_list(bom.components, comp_list)

    return ParsedSBOM(
        "CycloneDX",
        json_data.get("specVersion", ""),
        parsed_root,
        comp_list,
        dependencies,
    )


def cyclone_recursive_list(
    components_list: Iterable[CycloneDXComponent], sbom_list: list[Component]
) -> list[Component]:

    for component in components_list:
        name = component.name
        version = component.version
        purl = parse_purl(component.purl)
        bom_ref = component.bom_ref.value or f"{name}_ref"

        external_ref = None
        if component.external_references:
            for ref in component.external_references:
                if ref.type == "vcs":
                    external_ref = str(ref.url)
                    break

        if component.components:
            cyclone_recursive_list(component.components, sbom_list)

        sbom_list.append(Component(name, version, bom_ref, purl, external_ref))

    return sbom_list


def spdx_parser(sbom: Path) -> ParsedSBOM:
    """Accepted rel_types are DEPENDS_ON, CONTAINS and DYNAMIC_LINK"""
    doc = parse_file(str(sbom))

    rel_types = ["DEPENDS_ON", "CONTAINS", "DYNAMIC_LINK"]
    reverse_rel_types = ["DEPENDENCY_OF", "DEV_DEPENDENCY_OF"]
    VCS_PREFFIX = ("git+", "hg+", "svn+", "bzr+")

    dependencies = []
    described_ids = []
    for rel in doc.relationships:
        rel_type = (
            rel.relationship_type.name
            if hasattr(rel.relationship_type, "name")
            else str(rel.relationship_type)
        )
        if rel_type in rel_types:
            source = rel.spdx_element_id
            target = str(rel.related_spdx_element_id)
            dependencies.append(Dependency(source, target))
        elif rel_type in reverse_rel_types:
            source = str(rel.related_spdx_element_id)
            target = rel.spdx_element_id
            dependencies.append(Dependency(source, target))
        elif rel_type == "DESCRIBES":
            described_ids.append(rel.related_spdx_element_id)

    root_comp = None
    comp_list = []
    for pkg in doc.packages:
        name = pkg.name
        version = getattr(pkg, "version", None)

        purl = None
        external_ref = None
        external_refs = pkg.external_references
        for ref in external_refs:
            ref_type = ref.reference_type
            if ref_type == "purl":
                purl = parse_purl(ref.locator)
                break

        if str(pkg.download_location).startswith(VCS_PREFFIX):
            external_ref = str(pkg.download_location)

        if len(described_ids) > 0 and pkg.spdx_id == described_ids[0]:
            root_comp = Component(name, version, pkg.spdx_id, purl, external_ref)
        else:
            comp_list.append(Component(name, version, pkg.spdx_id, purl, external_ref))

    return ParsedSBOM(
        "SPDX", doc.creation_info.spdx_version, root_comp, comp_list, dependencies
    )


def parse_purl(purl: PackageURL | str | None) -> str | None:
    if not purl:
        return None

    if isinstance(purl, str):
        purl_obj = PackageURL.from_string(purl)
    else:
        purl_obj = purl

    return PackageURL.to_string(purl_obj)
