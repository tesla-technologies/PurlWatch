# ADR 0003: the assessment is an in-toto Statement with a project predicate

Date 2026-10-03. Status accepted.

The original concept described a bespoke health manifest signed with Sigstore or GPG. A bespoke envelope has no verifiers, and OpenPGP signatures are accepted by no mainstream DSSE or in-toto implementation. An in-toto Statement version 1 inside a DSSE envelope is what Sigstore bundles, GitHub's actions/attest and GUAC verify and store. CycloneDX 1.6 attestations could carry similar claims inside an SBOM but have fewer verifiers today. Among existing predicates, SCAI, VSA and VULNS each cover part of the need and none covers all of it.

The project emits an in-toto Statement whose subject is the release artefacts and whose predicate, under a type URI in the project's domain, carries the assessment: the inputs as ResourceDescriptors for the SBOM, the rule set, the baselines and the evidence snapshot, a summary, and the findings with evidence items as ResourceDescriptors. There is no expiry field. The specification compares the predicate field by field with SCAI and VSA and proposes it to the in-toto attestation repository, where no registration exists and vetting is optional, and it documents the mapping to CycloneDX attestations.

Verification reuses existing tooling. GUAC needs a parser for the new predicate type, which is a follow-up. Identities in the predicate are keyed hashes, and the evidence snapshots that the download location points to are stored by the attesting party rather than published by the project.
