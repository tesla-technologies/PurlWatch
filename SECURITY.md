# Security policy

Please report security problems privately to the address listed in the **Contact address** section below, encrypting with the OpenPGP key that will be published alongside it if you can. Do not open public issues for security problems, and do not test against third-party infrastructure such as registries, forges or ecosyste.ms on our behalf.

We acknowledge reports within five working days and aim to publish a fix or a mitigation within ninety days, in coordination with the reporter, whom we credit unless they prefer otherwise.

The command-line tool and library, the collectors, the attestation signing and verification path, the data set pipeline and the published schemas are in scope. The reports we most want to receive concern an attestation that verifies although its evidence does not support the finding, an assessment that can be back-dated or a replay that yields a different result than the original run, collectors that reveal the contents of an SBOM beyond the services they are documented to query, and any way to recover e-mail addresses or to de-pseudonymise the identifiers in the published data set.

Vulnerabilities in the third-party packages that the tool analyses are out of scope and should go to their maintainers. Findings about packages that appear in the data set are not security reports either; the dispute process in `docs/10-dataset-publication.md` handles them.

Until version 1.0 only the latest commit on `main` is supported.

The threat model, including evasion of the signals by an adversary who knows the public rules, is described in `docs/07-attestation.md` and will be completed in milestone M4.

### Contact address
security@teslatechnologies.com