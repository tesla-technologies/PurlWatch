# Vision and scope

## The problem

Software supply-chain tooling is reactive. Vulnerability databases and SBOM scanners report a component once an advisory or a malicious release has been published, and by then the damage is usually done. The incidents that hurt most showed warning signs in public metadata long before that.

In xz-utils, a contributor was added to the Tukaani organisation on GitHub on 28 October 2022 and was merging their own commits from January 2023. Lasse Collin tagged and built his last release, 5.4.1, on 11 January 2023; the newcomer tagged and built the next one, 5.4.2, on 18 March 2023, while Collin's share of the work declined. The newcomer had also authored every GitHub release object since the first one on 13 December 2022, which is why release-object authorship shows no change in this case and the git tagger does. The malicious 5.6.0 and 5.6.1 followed on 24 February and 9 March 2024 and the backdoor was disclosed on 29 March 2024 as CVE-2024-3094. The sources are the oss-security post of that day and the timeline published at research.swtch.com.

In event-stream, a new account appeared in the npm maintainers field and published version 3.3.5 on 5 September 2018 and version 3.3.6, which added the flatmap-stream dependency, on 9 September. The malicious flatmap-stream 0.1.1 was published on 5 October, the issue was opened on 20 November and the npm advisory followed on 26 November, seventy-two days after 3.3.6. The sources are the npm blog post on the incident and the Snyk post-mortem.

Both cases were visible in registry and repository metadata that is public today, and nothing in the standard toolchain looked at it.

## What the project produces

An open data set keyed by Package URL covers the most depended-upon packages of npm and crates.io in three tables. The mapping table links each package to its repository with a confidence level that records how many independent sources agree. The publisher-history table records, for every version, the account that published it and the maintainers field at that time, as keyed-hash identifiers rather than names. The signals table records, for every package and version, which signals were active, with their evidence summaries and the versions of the rules and baselines that produced them. A release comes out every month with a DOI and with catalogue metadata so that PurlDB and the CodeSupply catalogue can import it.

Alongside the data set there is a Python command-line tool and library. It reads a CycloneDX or SPDX SBOM, resolves every component to a Package URL, collects evidence from registries and forges into a content-addressed snapshot, applies deterministic rules against per-ecosystem baselines, and emits findings that each carry their evidence trail. The assessment can be signed as an in-toto attestation bound to the release artefacts and verified later, offline, against the snapshot.

Underneath both sits a public specification of the signals, with their definitions, evidence requirements, thresholds and state rules, frozen with a DOI before any validation run, together with JSON Schemas for findings, evidence, the attestation predicate and the data set tables.

## Who it is for

Developers and release engineers get a continuous-integration step that explains itself and never blocks by default. Auditors and downstream users get a way to know what was knowable about a dependency tree at release time, which the Cyber Resilience Act asks of manufacturers integrating third-party components under its Article 13(5). Data consumers such as PurlDB, catalogues and dependency tools get time-aware risk signals as open data rather than as a proprietary score. Researchers get a pre-registered and replayable validation of early-warning signals.

## What is left out on purpose

There is no score; findings are rules with evidence and never a single number. There is no blocker; the default policy warns, and hard failure is an explicit choice of the user. There is no claim to detect credential compromise or maintainer sabotage, because metadata signals address handover, transfer and abandonment, and the validation protocol says this before any result. The first data set does not cover PyPI, which exposes no owner history, nor Maven Central, which exposes only PGP key identifiers; both are follow-up scope. The first release signs with keyless Sigstore only, using GitHub's own instance for private repositories; a key-based mode with RFC 3161 timestamps is specified now and built later. There is no GUAC ingestor yet, because GUAC parses only the predicate types it knows.

## Principles

Every rule, threshold and baseline is deterministic, versioned and public, and every attestation names the versions it used. A finding without a replayable evidence trail is a bug. Signals describe how a project's rights and activity changed, and the published outputs never name individuals. The validation protocol admits that xz-utils and event-stream informed the rules and treats them as consistency checks, while out-of-sample evidence comes from a third incident chosen under a frozen rule and from a prospective monthly register. Where a standard exists the project composes it rather than inventing one, which is why it rests on Package URL, CycloneDX, SPDX, in-toto, DSSE, Sigstore, SARIF and DCAT-AP.

## The pre-grant prototype

The prototype proves the collectors and the Package URL graph. It implements no signals, no attestation and no data set pipeline. Its plan is in `15-prototype-plan.md`.
