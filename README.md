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

## Usage
### What the prototype does
The prototype receives a SBOM and for every component prints it's repository URL, the confidence level explained and version history.

### Installation and Set up
Once the project it's downloaded, follow these steps from the root directory to set up your local environment:

1. Create the virtual environment and install all project dependencies using `uv sync --all-packages`.

2. Copy the example environment file to create your local .env using `cp .example.env .env`. Once .env file it's created, open it and set the following variables:
    * **AURATRACE_HASH_KEY (Required)**: A unique secret string used to anonymize public account handles via hashing (as specified in docs/11-privacy-and-licensing.md). This value must never be hardcoded or committed to source control.

    * **AURATRACE_CACHE_DIR (Optional)**: Defines a custom cache path. If left unspecified, auratrace defaults to using your home directory (~/.cache/auratrace).

### Fast offline test
Positioned at root run:

`uv run --env-file .env auratrace resolve --sbom examples/node-cli.cdx.json --offline tests/fixtures/node-cli.tar`

The expected output:
```
================================================================================
Purl: pkg:npm/commander
Repository: https://github.com/tj/commander.js
Confidence: high
Sources agreeing: 2
Sources: ecosystems, registry
Forge: github

Versions:
Version: 0.0.1 | Date: 2011-08-14T22:17:52.365Z | Publisher hid: None | Publisher kind: unknown | Maintainers hids: h:4b3efe36
Version: 0.0.3 | Date: 2011-08-15T15:30:08.289Z | Publisher hid: None | Publisher kind: unknown | Maintainers hids: h:4b3efe36
...
```

#### <ins>Common Errors & Solutions
#### Missing `.env` File
```console
error: No environment file found at: .env
```
**Solution:** Make sure you created the `.env` file in the root directory. If the file already exists, verify that your terminal is positioned at the project root before running the command.

#### Missing `AURATRACE_HASH_KEY`

```console
Error: Environment variable AURATRACE_HASH_KEY it´s empty or not found.
```
**Solution**: Ensure `AURATRACE_HASH_KEY` is defined in your `.env` file. Fill it with any valid string inside quotes and save the changes.

### Command flags and what they do
| Flag | What requires | What does |
|------|---------------|-----------|
| *None* | Just the SBOM after the --sbom flag | Runs the command in **online mode**. Gets the information through petitions, creates a snapshot (`.tar` extension) of the search at `AURATRACE_CACHE_DIR/snapshots` and prints the information in the specified format. |
| `--offline` | The SBOM and a matching snapshot | Runs the command in **offline mode**. Reads the snapshot and prints the information in the specified format. The snapshot must correspond directly to the provided SBOM. |
| `--json` | *Nothing* | Changes the output from a **human-readable** text format to a **machine-readable** format. It can be applied to online and offline mode.|

### Outputs
#### Standard Output (Human-Readable)
When executed without flags, `auratrace` prints one text block per component in the following format:
```
Purl: Package URL
Repository: Package repository URL
Confidence: Confidence level (high, medium, low, none)
Sources agreeing: Quantity of sources agreeing on repository info
Sources: The sources agreeing
Forge: The repository forge

Versions:
Version: Package version | Date: Version's publication date | Publisher hid: Hashed id of version's publisher | Publisher kind: Version's publisher kind | Maintainers hids: Hashed id list of the version's maintainers
```

#### JSON format (Machine-readable)
When the --json flag is provided, auratrace outputs a single JSON object containing three top-level keys:

* mapping: [*Mapping schema*](schemas/mapping.schema.json)

* publisher_history: [*Publisher history schema*](schemas/publisher-history.schema.json)

* run: Object containing execution metadata:

```
{
    "mapping": [mapping schema lines],
    "publisher_history: [publisher-history schema lines],
    "run": {Run object}
}
```

### Supported Inputs & Limitations

#### Supported Formats
* **CycloneDX:** Versions 1.5 – 1.7 (JSON format)
* **SPDX:** Versions 2.2 and 2.3 (JSON format)
* **Package URLs (PURLs):**
  * `npm` and `cargo` PURLs are resolved via their respective registries.
  * Generic PURLs are resolved via their declared repository URLs.

#### Unsupported Formats & Features
* CycloneDX XML
* SPDX tag-value
* SPDX 3.0
* PURL types without a dedicated collector (these will be listed in the output but left unresolved).

> **Current Version Note:** Signals, attestations, and SARIF format export are not supported in the current release.

---

### Exit Codes

For full details on project outputs, refer to [`docs/08-outputs.md`](docs/08-outputs.md). The current release implements the following exit codes:

| Code | Meaning |
| --- | --- |
| 0 | the run completed, with or without findings under the warn policy |
| 2 | input error, such as an unreadable SBOM or an unknown Package URL type |
| 3 | offline mode was requested and a required document was missing |
| 4 | a network or rate-limit failure persisted after retries |

### Privacy
Online mode queries the `packages.ecosyste.ms`, `crates.io`, and `npm Registry` APIs. To protect privacy, email addresses are removed from all output, and public handles are anonymized via hashing.