# ADR 0004: the first release signs with keyless Sigstore only

Date 2026-10-04. Status accepted.

sigstore-python supports keyless signing and verifies bundles offline against a pinned trust root, but it has no key-based signing or verification, and its command-line tool accepts only SLSA predicate types, so a custom predicate has to be signed through the library API. GitHub's actions/attest accepts custom predicate types; a public repository gets a Rekor entry on the public-good instance, while a private repository on GitHub Enterprise Cloud uses GitHub's own Sigstore instance, which has no transparency log and embeds a signed timestamp from GitHub's timestamp authority. A key-based mode for regulated environments would need cosign with a key, no transparency-log upload, an RFC 3161 timestamp from a self-hosted sigstore timestamp-authority and a separate verifier built on securesystemslib.

The first release signs keylessly through the sigstore-python library and through actions/attest, and its verify command accepts either the Sigstore public-good trust root or an exported GitHub trust root. The key-based mode is specified in milestone M4 and built in a follow-up.

In every offered mode the signing time is proven by a transparency-log entry or a signed timestamp, which keeps back-dating detectable. Regulated environments that forbid any external signing service wait for the follow-up, and the specification already describes what they will get.
