# tests: e2e · email_scan · schema_validation
**Version:** 1.0 · **Date:** 2026-11-03 · **Status:** implemented;

Per-package unit tests live under each `packages/<name>/tests/`.

Run from the repo root:
```
uv run pytest tests     # Run all three tests: e2e, email_scan and schema_validation

uv run pytest tests/<specific_test>.py      # Run a specific test
```

## e2e tests
These tests run the full **replay** and **collect** flows for the `purlwatch resolve` command. 

**Replay** flows require an SBOM and a compatible snapshot (a `.tar` file with the matching packages and resolution). The tests use the SBOMs from the `examples/` directory and the snapshots from `tests/fixtures/snapshots`. If the collector logic or the snapshot format changes, SBOM resolution will change, making existing snapshots incompatible.

**Collect** flows perform network requests, so the test suite uses the `pytest-recording` library to avoid hitting external registries on every run. The library records cassettes containing each HTTP request and its corresponding response, which are then replayed offline during test execution. Whenever the collector logic changes, outgoing requests change as well, rendering existing cassettes incompatible.

To avoid recording fixtures manually, use the `scripts/record_fixtures.py` script to generate snapshots and cassettes. The script can be run in two ways:

#### Record all examples fixtures
Depending on the flags used the scripts acts one way or another. There are three posible combinations:
```
uv run --env-file .env scripts/record_fixtures.py --all 
# Records every fixture for the SBOMs in the examples/ directory including snapshots, cassettes and golden files.

uv run --env-file .env scripts/record_fixtures.py --all <fixture flag>
# Records every fixture specified type for the SBOMs in the examples/ directory.

uv run --env-file .env scripts/record_fixtures.py <fixture flag> <file path>
# Records the specified fixture for the specified path.
```

| Fixture Flag | What requires without `--all` |
|------|---------------|
| `--snapshot` | A SBOM |
| `--cassette` | The NodeID for the test |
| `--golden` | A SBOM that presents its snapshot in the `tests/fixtures/snapshots` directory|

> NodeID are build this way: `<test path>::<specific test>[parameter]`.
> Example: `tests/test_e2e.py::test_resolve_e2e_collect[node-cli.cdx.json]`