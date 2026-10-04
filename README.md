# AuraTrace (working name)

AuraTrace is an open data set and a free software tool that surface early-warning signals of supply-chain risk from the metadata that package registries and code forges already publish. It is a pre-grant prototype as of October 2026 and nothing in it is released yet. The name is a placeholder that collides with an existing PyPI package and will change before 9 October 2026.

## Why it exists

Most supply-chain tooling reacts to advisories. A scanner can only flag a dependency once a vulnerability or a malicious release has been published. The incidents that did the most damage showed their warning signs much earlier, in public metadata. In xz-utils a newcomer took over tagging and building releases more than a year before the backdoor shipped, while the original maintainer's share of the work fell away. In event-stream a new account appeared in the maintainers field and published two versions seventy-two days before anyone reported the problem. Nothing in the standard toolchain looked at either.

This project computes such conditions with deterministic, published rules and publishes the result in two forms. The first is an open data set, keyed by Package URL, covering the most depended-upon packages of npm and crates.io. It has three tables: the mapping from package to repository with a confidence level, the publisher history of every version with pseudonymous identifiers, and the signals themselves with their evidence summaries. It is released monthly with a DOI and catalogue metadata so that PurlDB and the CodeSupply catalogue can import it. The second is a Python command-line tool and library that computes the same signals locally from any CycloneDX or SPDX software bill of materials, explains every finding with its evidence, and can sign the assessment as an in-toto attestation bound to the release artefacts, so that an auditor can later check what was knowable at release time.

The design, the scope and the validation protocol are described in the documentation under `docs/`, starting at `docs/00-index.md`. The project is being proposed to NLnet's CodeSupply fund, whose deadline is 3 November 2026.

## What the prototype must do

Before 9 October 2026 the repository has to show one thing working end to end: a command that takes an SBOM and prints, for every component, its Package URL, the repository it resolves to with a confidence level, and the publisher of each version as the registry exposes it. For npm that is the publishing account per version from the packument; for crates.io it is the `published_by` field per version together with the current owners. The prototype has no signals and no attestations. Its purpose is to prove the collectors and the package graph with a green continuous-integration run. The plan is in `docs/15-prototype-plan.md`.

## How the repository is organised

The code is one Python workspace with several packages that share a version. `packages/core` holds SBOM parsing for CycloneDX 1.5 to 1.7 and SPDX 2.2 and 2.3, the Package URL graph, the package-to-repository mapping and the snapshot format. `packages/collectors` holds the clients for npm packuments, crates.io, git, GitHub, ecosyste.ms, OSV, VulnerableCode and archived packuments. `packages/signals` holds the rule engine, the baselines and the evidence trails. `packages/attest` holds the in-toto predicate and the Sigstore signing and verification path. `packages/dataset` holds the scheduled pipeline that produces the monthly release, and `packages/cli` holds the command itself, whose name will change with the project's. The JSON Schemas live in `schemas/`, the signal specification that will be frozen with a DOI lives in `spec/`, example SBOMs live in `examples/`, cross-package tests live in `tests/`, and the documentation lives in `docs/`. The development setup is described in `docs/12-development-setup.md` and changes are recorded in `CHANGELOG.md`.

## Maintainers

The maintainers are the engineers of Tesla Technologies named in the signed-off commit history; their public profiles will be listed here once the first tag exists. Until `SECURITY.md` carries a contact address, reach them through the issue tracker.

## Licences

The code is licensed under Apache-2.0, see `LICENSE`. The documentation is CC BY 4.0. The data set will be released under CDLA-Permissive-2.0 if its tables can be computed entirely from primary sources, which is the design intent, and under CC BY-SA 4.0 otherwise; the reasoning is in `docs/11-privacy-and-licensing.md`. Contributions are accepted under the Developer Certificate of Origin as explained in `CONTRIBUTING.md`, and the project follows the Contributor Covenant in `CODE_OF_CONDUCT.md`.

## Generative AI

The project follows NLnet's policy on the use of generative AI. Code in this repository is written by its human contributors. A contribution generated with a language model is not accepted unless the commit names the model and version and explains how it was used, in which case the maintainers review it and may still decline it. The initial text of this README, of `CONTRIBUTING.md`, of `SECURITY.md` and of the files under `docs/` was drafted on 4 October 2026 with Claude Fable 5.1 from the maintainers' working notes, and the diagrams and engineering notes added the same day were drafted with Claude Opus 5.5; the maintainers reviewed it and keep it, and the facts in it cite their sources. The policy as the project applies it is in `docs/14-genai-policy.md`.

## Security

Vulnerabilities are reported privately as described in `SECURITY.md`. Please do not open public issues for security problems.

## Acknowledgements

The project builds on Package URL, CycloneDX, SPDX, in-toto, Sigstore, OSV, VulnerableCode, ecosyste.ms, OpenSSF Scorecard, the CHAOSS metric definitions and the research cited in `docs/04-signal-catalogue.md`.
