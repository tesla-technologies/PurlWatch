# Contributing

This project is small and young. The rules in this file exist so that it can grow into a data commons that other people trust, including the maintainers of the packages that will appear in its data set.

Every commit carries a `Signed-off-by` line, which you add with `git commit -s`. By signing off you certify the Developer Certificate of Origin, version 1.1, published at developercertificate.org.

Code in this repository is written by people. A contribution generated with a language model is not accepted unless the commit names the model and version and explains how it was used, in which case the maintainers review it and may still decline it. The project's own practice is to write code by hand, for the reasons given in `docs/14-genai-policy.md`.

A change to a signal, a threshold or a baseline is a change to a published and versioned specification, not an implementation detail. It starts with an issue, continues with a revision of the specification in `spec/` and of the schemas in `schemas/` where needed, and ends with an entry in `CHANGELOG.md`, which follows the Keep a Changelog format. Rules are never changed silently.

Do not add e-mail addresses to fixtures, tests or documentation; a pre-commit hook rejects anything matching an address pattern outside `CODE_OF_CONDUCT.md` and `SECURITY.md`. Public account handles appear only inside evidence snapshots, and the published outputs carry keyed hashes instead. The reasoning is in `docs/11-privacy-and-licensing.md`.

Every collector has to be replayable from a stored snapshot. A pull request that adds a collector also adds a recorded fixture and a replay test that fails if the output ever differs.

The workflow is ordinary. Open an issue before a large change; a small fix can go straight to a pull request. Branch from `main` and name the branch after what it does, such as `feat/npm-packument-collector` or `spec/s1-windows`. Run the tests and the linters locally as described in `docs/12-development-setup.md`. Keep pull requests focused on one signal, one collector or one schema. Write commit subjects in the imperative under seventy-two characters, with a body that explains why, and sign them off.

In October 2026 the most useful contributions are the prototype described in `docs/15-prototype-plan.md`, reviews of the signal definitions in `docs/04-signal-catalogue.md` from people who maintain widely used npm or crates.io packages, and pointers to historical registry data such as archived packuments and crates.io dumps for the validation protocol.

Maintainers of the packages that appear in the data set are people, and the project exists to make handovers visible rather than to accuse anyone. If you believe a row of the data set is wrong or unfair, open an issue with the dispute template under `.github/ISSUE_TEMPLATE/`; the process in `docs/10-dataset-publication.md` answers it within fourteen days. The Contributor Covenant in `CODE_OF_CONDUCT.md` applies to every interaction in the project.
