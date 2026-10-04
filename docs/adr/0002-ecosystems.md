# ADR 0002: the first data set covers npm and crates.io only

Date 2026-10-03. Status accepted.

The handover and publisher-change signals need to know who published each version over time. npm full packuments expose the `_npmUser` and `maintainers` fields per version, although `_npmUser` is absent before 2014 and shows a continuous-integration identity under trusted publishing. crates.io exposes `published_by` per version, null before 2017 and under trusted publishing, and the current owners in its daily dump. PyPI exposes no owner roles or history in its JSON API, and Maven Central has no owner concept at all, only a PGP key identifier per artefact.

Versions 0 and 1 of the data set cover npm and crates.io. The command-line tool evaluates any Package URL, and for other types it follows the repository path and says which signals could not run.

PyPI and Maven Central become follow-up scope with their own sources, PyPI attestations and status markers in one case and PGP key identifiers in the other. The eight-hundred-hour budget fits two registries and would not fit a third. The reference SBOMs for the per-SBOM warn-rate target are a Node web application, a Rust command-line tool and a Node command-line tool; the project's own Python SBOM exercises only the repository path.
