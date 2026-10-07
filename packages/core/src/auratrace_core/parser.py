import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path

from cyclonedx.model.bom import Bom
from cyclonedx.model.component import (
    Component as CycloneDXComponent,
)
from spdx_tools.spdx.parser.parse_anything import parse_file


@dataclass(frozen=True)
class Dependency:
    source: str
    target: str | None


@dataclass(frozen=True)
class Component:
    name: str
    version: str | None
    bom_ref: str | None
    purl: str | None


@dataclass(frozen=True)
class parsedSBOM:
    format: str
    version: str
    root_comp: Component | None
    comp_list: list[Component]
    dependencies: list[Dependency]


class UnsupportedFormatError(Exception):
    """Se lanza cuando el formato o versión del archivo no está soportado."""


class InvalidStructureError(Exception):
    """Se lanza cuando el contenido del archivo no cumple la estructura esperada."""


def parse_sbom(sbom: Path) -> parsedSBOM:
    if not sbom.exists():
        raise FileNotFoundError("Not SBOM was added")

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
                raise UnsupportedFormatError("Format not supported")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as err:
        raise InvalidStructureError("JSON format it´s not valid") from err


def cyclone_parser(sbom: Path) -> parsedSBOM:
    json_data = json.loads(sbom.read_text(encoding="utf-8"))
    bom: Bom = Bom.from_json(data=json_data)  # type: ignore[attr-defined]

    parsed_root = None
    if bom.metadata.component:
        root_component = bom.metadata.component
        parsed_root = Component(
            root_component.name,
            root_component.version,
            root_component.bom_ref.value or None,
            str(root_component.purl) or None,
        )

    parsed_sbom = parsedSBOM(
        "CycloneDX",
        json_data.get("specVersion", ""),
        parsed_root or None,
        comp_list=[],
        dependencies=[],
    )

    if bom.dependencies:
        for dependency in bom.dependencies:
            source = dependency.ref.value
            depends_list = [child.ref.value for child in dependency.dependencies]
            if len(depends_list) > 0:
                for target in depends_list:
                    parsed_sbom.dependencies.append(Dependency(source, target))
            else:
                parsed_sbom.dependencies.append(Dependency(source, None))

        parsed_sbom = cyclone_recursive_list(bom.components, parsed_sbom)

    return parsed_sbom


def cyclone_recursive_list(
    components_list: Iterable[CycloneDXComponent], parsed_sbom: parsedSBOM
) -> parsedSBOM:

    for component in components_list:
        name = component.name
        version = component.version
        purl = str(component.purl) if component.purl else None
        bom_ref = component.bom_ref.value or None

        if component.components:
            parsed_sbom.comp_list.extend(
                cyclone_recursive_list(component.components, parsed_sbom).comp_list
            )

        parsed_sbom.comp_list.append(Component(name, version, bom_ref, purl))

    return parsed_sbom


def spdx_parser(sbom: Path) -> parsedSBOM:
    """Accepted rel_types are DEPENDS_ON, CONTAINS and DYNAMIC_LINK"""
    doc = parse_file(str(sbom))

    parsed_sbom = parsedSBOM(
        "SPDX",
        doc.creation_info.spdx_version,
        root_comp=None,
        comp_list=[],
        dependencies=[],
    )
    rel_types = ["DEPENDS_ON", "CONTAINS", "DYNAMIC_LINK"]

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
            parsed_sbom.dependencies.append(Dependency(source, target))
        elif rel_type == "DESCRIBES":
            described_ids.append(rel.spdx_element_id)

    for pkg in doc.packages:
        name = pkg.name
        version = getattr(pkg, "version_info", None)

        purl = None
        external_refs = pkg.external_references
        for ref in external_refs:
            ref_type = ref.reference_type
            if ref_type == "purl":
                purl = ref.locator
                break

        if described_ids[0] and pkg.spdx_id == described_ids[0]:
            replace(parsed_sbom, root_comp=Component(name, version, pkg.spdx_id, purl))
        else:
            parsed_sbom.comp_list.append(Component(name, version, pkg.spdx_id, purl))

    return parsed_sbom


def main() -> None:
    target_path = Path(sys.argv[1]).expanduser().resolve()
    if not target_path.exists():
        print(f"Error: File does not exist: {target_path}")
        return

    if not target_path.is_file():
        print(f"Error: Path {target_path} it´s not a file.")
        return

    print(parse_sbom(target_path))


if __name__ == "__main__":
    main()
