# Changelog

All notable changes to this project are recorded here. The format follows Keep a Changelog 1.1 and the project uses semantic versioning once it has a first tag.

## Unreleased

## 0.0.4-prototype - 2026-11-11
### Added
* Components output: Added a components section to human- and machine-readable outputs, displaying the ref, purl, package, is-root, depth, via, and route for each resolved component.

* Coverage for collectors/client.py: Added tests for scenarios that should exit with code 4.

* Close method for PurlwatchTransport: Added a close() method to the PurlwatchTransport class.

* Declared repository detection: Added detection of declared repositories via purl for pkg:github, pkg:bitbucket, and vcs_url qualifiers.

### Fixed
* Test execution in cli/resolve.py: Replaced subprocess calls across tests with direct calls to run_resolve, and added a dedicated subprocess test.

* Root package in output: Fixed root component handling to ensure it is properly listed when expected.

* Tests in core/tests/test_resolve.py: Updated the make_sbom helper to match parse_sbom behavior by excluding the SBOM root package from the component list, updating dependent test parameters accordingly.

* Test in test/test_e2e.py: Added assertion to verify the expected error message on exit code 2.

### Changed
* Confidence calculation in mapping: Changed the confidence rule so various sources (excluding "provenance" and "registry") with matching urls return medium confidence instead of low confidence.

## 0.0.3-prototype - 2026-11-03
### Fixed
* Root component resolution: Prevented root components (is_root=True) from being queried against registries and misattributed to unrelated public packages.

* SSH URL normalization: Fixed normalize_url to transform ssh:// and git+ssh:// schemes to https:// (resolving confidence mismatches between registries and ecosyste.ms) and stripped trailing .git suffixes after fragment removal.

* Graph traversal from root: Included the root component in ref_dict during build_edges so its dependencies are retained, allowing breadth-first search to calculate depth and via paths.

* Rootless SBOM handling: Fixed UnboundLocalError: cannot access local variable 'depth' when resolving SBOMs without an explicit root component (e.g., SPDX, nested components, or non-PURL manifests) by scoping tracking dictionaries outside the root conditional.

* CLI argument handling: Removed unhandled exit_on_error=False from argument parsing to prevent raw argparse.ArgumentError tracebacks on missing arguments or invalid subcommands, restoring standard exit code 2.

* Host rate limiting: Corrected rate-limiter elapsed time calculation in client.py by using time.monotonic() consistently instead of subtracting from time.time(), properly enforcing registry request limits (such as the 1-second delay for crates.io).

* Mapping row deduplication: Deduplicated packages by canonical PURL before collection, ensuring multi-version components in the SBOM (e.g., pkg:npm/content-type) produce a single row in the final mapping output.

* Canonical PURL consistency: Standardized repository-only route rows to use unversioned package identifiers (component.package) matching registry route outputs.

* Repository route classification: Updated the "Repository only path" condition to evaluate component.route rather than relying solely on the SBOM source type.

* Exception handling and exit codes: Replaced unhandled runtime exceptions with standard error handling—returning exit code 2 for non-tar --offline fixtures, wrapping digest mismatches in PurlwatchError, and making SnapshotWriter.close() idempotent to prevent RuntimeError.

* CLI error output formatting: Cleaned up error messages to prevent appending numerical status codes to error strings (e.g., purlwatch: SBOM file not found: <path>) and corrected grammar in hash key warnings.

* Resource management & cleanup: Ensured HTTP client instances are closed via context managers, eliminated Publisher hid: None display output, removed unused PackageNotFound exception, and centralized hardcoded version strings.

* Project deliverables & fixtures: Restored the missing repository SBOM (purlwatch.cdx.json), reconciled fixture naming between documentation and examples (node-app.cdx.json), removed unfinished scripts/record_fixtures.py, and refreshed golden JSON test files.

* Documentation alignment: Updated README.md to describe existing features in the present tense, documented active maintainers, fixed CLI example snippets and heading tags, and added contact information to SECURITY.md.

## 0.0.2-prototype - 2026-11-02
Changed name from AuraTrace to PurlWatch, which is available on PyPI, npm, crates.io, and GitHub, and is more descriptive.
