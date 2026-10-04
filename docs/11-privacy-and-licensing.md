# Privacy and licensing

This chapter is reviewed with NLnet's licensing support in milestone M1 and again before version 1.0.

## Identities

Evidence snapshots, whether held by the attesting party or published for the validation protocol, keep public account handles exactly as the registry or forge shows them, because an auditor who replays a finding from public packuments must be able to recompute it and because those handles are already public. They never contain e-mail addresses, which are stripped at ingestion.

The published data set and the attestation summary carry keyed-hash identifiers instead, computed as HMAC-SHA256 with a key the project holds. No person is named in the data set or in the attestation summary. Because handles can be enumerated, the hashes are pseudonymous rather than anonymous, and every place they appear says so. When someone disputes a row or objects to it, the project re-identifies the hash with its key in order to answer them.

Signals describe how a project's rights and activity changed. They never rank individuals and are never presented as accusations.

## The GDPR basis

The controller is Tesla Technologies, to be confirmed with the company's data protection contact. The legal basis is legitimate interest under Article 6(1)(f), with a written assessment published on the project site. Because informing every maintainer individually would be disproportionate, the project relies on Article 14(5)(b) and publishes a notice on its site. Objections under Article 21 follow the dispute process, and a successful objection ends in the redaction of the identifier with an annotation that keeps the row's history; access requests are answered from the retained snapshot. Snapshots are kept for eighteen months after the release they belong to and then deleted, and the published tables carry no e-mail addresses and only keyed hashes.

## Terms of service of the sources

The terms of npm and GitHub are checked for the redistribution of user data, and only derived facts are republished, with a descriptive User-Agent and respect for rate limits. The crates.io crawler policy is to be verified at crates.io/data-access before the first scheduled run. GH Archive and its ClickHouse copy have no formal licence beyond a statement that the data is redistributable for research, so again only derived facts are republished. The data of ecosyste.ms is CC BY-SA 4.0 and its code AGPL-3, and bulk access remains to be agreed. The Libraries.io Open Data release is CC BY-SA 4.0 and is used for calibration only.

## The project's own licences

The code is Apache-2.0, which is permissive and carries a patent grant. The documentation and the specification are CC BY 4.0. The data set is CDLA-Permissive-2.0 by preference, or CC BY-SA 4.0 if share-alike inputs cannot be kept out of the published tables, a decision taken in M1. Contributions are accepted under the Developer Certificate of Origin with a sign-off on every commit.

## The share-alike question

Share-alike under CC BY-SA 4.0 reaches a derived database only when a substantial portion of the licensed data is included in it. ecosyste.ms is operated from the United Kingdom, so in Spain copyright and the licence's substantial-portion clause apply rather than the European Union's sui generis database right; the United Kingdom has a database right of its own, which the licence also covers in its section 4. The design therefore computes the published tables from primary sources, meaning the registries, git and the GitHub events dataset, and uses ecosyste.ms for discovery and cross-checking only. If that separation cannot be maintained for some table, that table is published under CC BY-SA 4.0.

## Security review

NLnet offers a security review to the projects it funds, and this project requests it before version 1.0. The threat model is in `07-attestation.md`.
