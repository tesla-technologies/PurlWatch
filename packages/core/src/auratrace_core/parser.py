import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from cyclonedx.model.bom import Bom
from spdx_tools.spdx.parser.parse_anything import parse_file


@dataclass(frozen=True)
class DepEdges:
    dep_bom: str
    dependsOn: list[str]


@dataclass(frozen=True)
class Component:
    name: str
    purl: str
    dependencies: DepEdges


class UnsupportedFormatError(Exception):
    """Se lanza cuando el formato o versión del archivo no está soportado."""


class InvalidStructureError(Exception):
    """Se lanza cuando el contenido del archivo no cumple la estructura esperada."""


def parse_sbom(sbom: Path) -> list[Component]:
    if not sbom.exists():
        raise FileNotFoundError("Not SBOM was added")

    try:
        with open(sbom, "r", encoding="utf-8") as s:
            raw_json = json.load(s)
            cyclone_versions = ["1.5", "1.6", "1.7"]

            if "bomFormat" in raw_json and raw_json["specVersion"] in cyclone_versions:
                return cyclone_parser(sbom)
            elif "spdxVersion" in raw_json:
                return spdx_parser(sbom)
            else:
                raise UnsupportedFormatError("Format not supported")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as err:
        raise InvalidStructureError("JSON format it´s not valid") from err


def cyclone_parser(sbom: Path) -> list[Component]:
    json_data = json.loads(sbom.read_text(encoding="utf-8"))
    bom: Bom = Bom.from_json(data=json_data)  # type: ignore[attr-defined]

    parsed_list = []
    deps_map = {}

    if bom.dependencies:
        for dependency in bom.dependencies:
            origen_ref = dependency.ref.value
            lista_destinos = [child.ref.value for child in dependency.dependencies]

            deps_map[origen_ref] = lista_destinos

    for component in bom.components:
        name = component.name
        purl = str(component.purl) if component.purl else ""
        dep_edges = DepEdges(
            component.bom_ref.value, deps_map.get(component.bom_ref.value, [])
        )

        parsed_list.append(Component(name, purl, dep_edges))

    return parsed_list


def spdx_parser(sbom: Path) -> list[Component]:
    parsed_list = []
    deps_map: dict[str, list[str]] = defaultdict(list)
    doc = parse_file(str(sbom))

    for rel in doc.relationships:
        rel_type = (
            rel.relationship_type.name
            if hasattr(rel.relationship_type, "name")
            else str(rel.relationship_type)
        )
        if rel_type == "DEPENDS_ON":
            origen = rel.spdx_element_id
            destino = str(rel.related_spdx_element_id)
            deps_map[origen].append(destino)

    for pkg in doc.packages:
        purl = ""
        name = pkg.name
        dep_edges = DepEdges(pkg.spdx_id, deps_map.get(pkg.spdx_id, []))
        for ref in pkg.external_references:
            if ref.reference_type.lower() == "purl":
                purl = ref.locator
                break
            else:
                purl = ""

        parsed_list.append(Component(name, purl, dep_edges))

    return parsed_list


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
