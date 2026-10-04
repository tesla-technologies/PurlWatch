# The prototype, before 9 October 2026

The prototype exists to give the application public evidence that the team can execute. It is a command that takes an SBOM and prints, for every component, its Package URL, the repository it resolves to with a confidence level, and the publisher history the registries expose. It needs a green continuous-integration run and nothing more.

## What done looks like

Running `auratrace resolve --sbom examples/node-app.cdx.json` prints one block per component. For an npm package the block shows the Package URL, the resolved repository and its confidence, and then one line per version with its publication date, the keyed hash of the publishing account, whether that account was a person or a trusted publisher, and the keyed hashes of the maintainers field at that version. For a crates.io package it shows the same, with the owners marked as current only. For a Package URL without a registry, such as `pkg:generic/xz@5.6.1`, it shows the declared repository with medium confidence and notes that only the repository path applies.

The command works on the three example SBOMs committed under `examples/`, a Node web application, a Rust command-line tool and a Node command-line tool, and on the project's own SBOM along the repository path. With `--offline` and a snapshot it reproduces the same output without the network; the offline mode against the published data set comes later, in M5. With `--json` it emits the mapping and publisher-history rows defined in `03-data-model.md`, validated against the schemas in `schemas/`. No e-mail address appears in output, fixtures or snapshots; handles appear only inside snapshots and keyed hashes in the output. Continuous integration runs ruff, mypy, pytest with recorded fixtures, schema validation, the replay test and the sign-off check, and it is green on `main`.

## The week

| Day | Who | Work |
| --- | --- | --- |
| 1 | both | workspace and `pyproject.toml`, package skeletons, pre-commit, the CI workflow, the sign-off check, and the new project name applied everywhere |
| 1 to 2 | engineer A | `core`: CycloneDX 1.5 to 1.7 and SPDX 2.2 and 2.3 parsing into components and edges with cyclonedx-python-lib and spdx-tools; Package URL normalisation with packageurl-python |
| 2 to 3 | engineer B | `collectors`: the npm full packument client with recording; the `time` map and the `_npmUser` and `maintainers` fields per version; detection of trusted publishing; e-mail stripping at ingestion |
| 3 | engineer B | `collectors`: the crates.io versions endpoint with `published_by`, `created_at` and yanked, the current owners, the crawler policy and the User-Agent |
| 3 to 4 | engineer A | `core`: the package-to-repository mapping from registry fields and ecosyste.ms with the confidence rule, and forge normalisation |
| 4 | engineer A | `core`: keyed-hash identifiers with the key taken from the environment and a test key in CI |
| 4 to 5 | both | the snapshot writer and reader with `index.json` and the canonical tar, the `--offline` option and the replay test |
| 5 | engineer B | `cli`: the `resolve` command, the text and JSON renderers and the exit codes |
| 5 | both | the schemas for mapping and publisher history, the contract tests, the usage section of the README and the tag `v0.0.1-prototype` |

## What stays out

Signals, baselines, attestations, SARIF, the data set pipeline, the GitHub Action, the GitLab template, the Wayback and ClickHouse collectors, and any git analysis beyond the declared repository.

## What the application links to

The repository URL and the tag, the URL of a green CI run, a short recording or a pasted terminal session of the command on an example SBOM, and the names and public profiles of the two engineers as they appear in the signed-off commit history.
