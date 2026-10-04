# ADR 0001: the implementation language is Python

Date 2026-10-03. Status accepted.

The original concept named Rust or Go. The team's existing stack, the ResilMesh detection pipeline, is Python, and the libraries this project needs are mature in Python: packageurl-python, cyclonedx-python-lib for CycloneDX 1.0 to 1.7, spdx-tools for SPDX 2.2 and 2.3, sigstore-python for keyless signing and bundle verification, in-toto-attestation for the statement types and securesystemslib for a later key-based mode. In Rust, sigstore-rs does not yet verify attestations, no SPDX 3 parser exists, and cyclonedx-bom covers 1.3 to 1.6.

Every package is written in Python 3.12 or later and distributed on PyPI through trusted publishing together with a reproducible container image.

The credibility of the applicant's experience rests on the team's visible Python work, which exists. The start-up time of a Python command is acceptable for a continuous-integration step whose cost is dominated by network access and caching, and nothing in the design depends on the language, so a Rust port of hot paths behind the same schemas remains possible.
