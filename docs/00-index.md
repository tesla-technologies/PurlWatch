# Documentation index

This is the development documentation of AuraTrace, which is a working name. Until milestone M1 of the funded project confirms them, these documents record the maintainers' current intent and every number in them is provisional.

| File | What it covers |
| --- | --- |
| 01-vision-and-scope.md | What the project builds, for whom, and what it deliberately leaves out |
| 02-architecture.md | The six stages from SBOM to signed assessment and the three outputs |
| 03-data-model.md | Package URL keys, the three data set tables, findings and evidence |
| 04-signal-catalogue.md | The default, context and experimental signals with definitions and sources |
| 05-collectors.md | Each data source, what it exposes, its limits and its terms |
| 06-evidence-store.md | Content-addressed snapshots, replay and canonical serialisation |
| 07-attestation.md | The in-toto predicate, the signing modes, verification and the threat model |
| 08-outputs.md | Terminal report, JSON, SARIF, GitLab dependency-scanning JSON and the warn policy |
| 09-validation-protocol.md | Pre-registration, the incident set, controls and the prospective register |
| 10-dataset-publication.md | Corpus, releases, DOI, catalogue metadata, PurlDB import and the dispute path |
| 11-privacy-and-licensing.md | Handles versus keyed hashes, the GDPR basis, the data licence and terms of service |
| 12-development-setup.md | Toolchain, workspace layout, tests, continuous integration and releases |
| 13-roadmap-and-milestones.md | The seven milestones with hours and deliverables, and what gets cut first |
| 14-genai-policy.md | How the project applies NLnet's policy on generative AI |
| 15-prototype-plan.md | What to build before 9 October 2026 and how to show it works |
| adr/ | The architecture decision records |

A few words recur throughout. A default signal is one that ships switched on once it has passed the control-set test; a context signal is shown next to findings but is never a finding itself; an experimental signal is switched off unless asked for. A rights grant is the date on which an identity obtained publish rights on a package or merge rights on a repository, and the previous maintainers are the identities that held such rights before that date. A snapshot is a content-addressed bundle of every document fetched during a run. Dates are written in ISO 8601, amounts in euro and effort in person-hours.

Facts about tools, registries and incidents cite their sources where they appear. The maintainers keep the proposal's source archive, with the call pages, incident reports, standards and papers, outside this repository and will reference it from `spec/` once the specification is frozen.


If you are the engineer starting on the prototype, read in this order: `15-prototype-plan.md` for what to build this week, `02-architecture.md` for where each piece sits, `03-data-model.md` for the rows the prototype must emit, `05-collectors.md` for the two collectors it needs, `06-evidence-store.md` for the snapshot format, and `12-development-setup.md` for the toolchain and conventions. The remaining documents describe the funded project and can wait until the first tag exists. The diagrams in these files use Mermaid, which GitHub and GitLab render in place; if your editor does not, the text next to each diagram says the same thing.