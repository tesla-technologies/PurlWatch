# Development setup

The repository is one Python workspace with several packages that share a version. Linux and macOS are the supported development platforms; on Windows use WSL, because the canonical tar format of snapshots and the path handling in fixtures assume a POSIX file system.

## Toolchain

The project requires Python 3.12 or later and uv as the workspace package manager; Poetry or pip with editable installs work as well. Each directory under `packages/` is a distribution with its own `pyproject.toml`, and the root `pyproject.toml` declares the workspace. Linting and formatting use ruff; type checking uses mypy in strict mode for `core`, `signals` and `attest`. Tests use pytest, pytest-recording (which drives vcrpy) for recorded HTTP fixtures, and hypothesis for property tests on the parsers and on canonical serialisation. Pre-commit hooks run ruff, mypy, the sign-off check and a scan that fails if anything matching an e-mail address appears in fixtures or documentation outside `CODE_OF_CONDUCT.md` and `SECURITY.md`.

Getting started, once the `pyproject.toml` files exist, is `uv sync`, then `uv run pre-commit install`, then `uv run pytest`. The collectors read `GITHUB_TOKEN` for the GitHub API and, optionally, `ECOSYSTEMS_API_KEY` if ecosyste.ms grants one; the keyed-hash identifiers read `PURLWATCH_HASH_KEY`, and the test suite sets a fixed test key so that fixtures stay stable. `PURLWATCH_CACHE_DIR` overrides the default cache location. Variable names change with the project name.

## Third-party libraries and why

Package URLs are parsed and built with packageurl-python, maintained by the package-url project with contributors from nexB and AboutCode. CycloneDX is read with cyclonedx-python-lib 11, which covers schema versions 1.0 to 1.7; the tool accepts 1.5 to 1.7. SPDX 2.2 and 2.3 are read with spdx-tools 0.8, whose SPDX 3 support is write-only and unstable, which is why 3.0.1 is deferred. The in-toto Statement types come from in-toto-attestation, whose protobuf bindings were last released in December 2023 as version 0.9.3, so the dependency is pinned or vendored. Signing and verification use sigstore-python, which is keyless only and whose command-line tool accepts only SLSA predicates, so custom predicates go through its library API. securesystemslib is reserved for the key-based mode of a later release. HTTP goes through httpx with caching, a descriptive User-Agent, retries with backoff and per-host rate limits. Git is read with pygit2 or dulwich using shallow or partial clones. Data is written with pyarrow for Parquet and orjson for canonical JSON.

## Layout

```
pyproject.toml            workspace root and shared tool configuration
CHANGELOG.md              Keep a Changelog format, one entry per user-visible change
packages/core/            SBOM parsing, Package URL graph, mapping, snapshot format and collector interfaces
packages/collectors/      registry, forge, advisory and archive clients
packages/signals/         rule engine, baselines, evidence trails
packages/attest/          in-toto predicate, Sigstore signing and verification
packages/dataset/         scheduled pipeline, releases, catalogue metadata
packages/cli/             the command, whose name changes with the project's
schemas/                  JSON Schemas, versioned
spec/                     the signal specification, frozen with a DOI in M1
examples/                 the reference SBOMs used by tests and documentation
tests/                    cross-package tests: contract, replay, end to end
docs/                     this documentation
```

Dependencies point one way: `collectors` depends on `core`, `signals` depends on `core`, `attest` depends on `signals`, `cli` depends on everything, and `dataset` depends on `cli`. Nothing else depends on `cli`.

## Defaults before baselines exist

Until the first baselines are published in M3, the engine runs with provisional constants that the tests also use: a commit floor of twenty non-bot commits per twelve-month window for the S1 floor branch, a minimum of ten releases before a project's own diff-size percentile is computed, and a dormancy threshold of eighteen months. The specification replaces them with corpus-derived values and records the change.

## Tests

Each package has unit tests. Contract tests validate every JSON output against its schema in `schemas/`, and a schema change is always a versioned change. Replay tests run the engine on the recorded fixture of every collector and fail if the output differs by a byte from the stored expectation. End-to-end tests run the three reference SBOMs in `examples/`, a Node web application, a Rust command-line tool and a Node command-line tool, in offline mode against a committed snapshot; the project's own Python SBOM runs too but exercises only the repository path. A dedicated test scans the repository for e-mail addresses. The coverage target is eighty per cent of lines in `core`, `signals` and `attest`.

## Continuous integration

One workflow runs on every push and pull request: installation, ruff, mypy, pytest with coverage, schema validation, fixture replay and the sign-off check. A second workflow runs on tags: it builds the distributions, generates the project's own CycloneDX SBOM, runs the tool on it along the repository path and signs the result with actions/attest under the project's predicate type, so that the project attests itself from its first release. The workflow files under `.github/workflows/` are written by the maintainers. GitLab CI (`.gitlab-ci.yml`) remains the authoritative pipeline, as development takes place on GitLab.

## Releases

A release starts with a signed tag `vX.Y.Z` on `main`. Continuous integration builds wheels and source distributions for every package under the same version, publishes them to PyPI through trusted publishing, builds a reproducible container image and attaches the SBOM and the attestation. The specification in `spec/` and the schemas in `schemas/` are versioned independently of the code, and every release notes which versions it ships.

## Running it

## Conventions that save time later

Configuration comes from environment variables and from a single optional TOML file, never from both for the same key, and the command prints the effective configuration at debug level. Errors are typed: input errors, offline misses and network failures are distinct exception classes mapped to the exit codes in `08-outputs.md`, and a collector never catches an exception it cannot turn into a recorded fact. Logging is structured, one JSON object per line when `--log-json` is given, always with the run identifier, and nothing that could be a handle or an e-mail address is logged above debug level. Time is always UTC and always ISO 8601 with a trailing Z; the only place a local time appears is the terminal report, and only when the user asks for it. Every public function in `core` and `signals` has a docstring that states what it reads from the snapshot and what it never reads, because that boundary is the project's main correctness argument. Fixtures are small: a packument fixture is trimmed to the versions the test needs, with a comment saying which ones were removed.

The prototype offers one command, `purlwatch resolve --sbom examples/node-app.cdx.json`, with `--json` for machine output and `--offline snapshots/<id>.tar` for replay. The funded project adds `scan`, which produces findings and their renderings, `attest`, which signs them for a given subject, and `verify`, which checks a bundle against a trust root and optionally replays its snapshot. The command name changes with the project name.
