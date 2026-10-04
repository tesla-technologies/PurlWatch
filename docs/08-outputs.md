# Outputs

## Policy

The tool warns by default and exits with status zero even when it has findings. The options `--fail-on warn` or `--fail-on` with a list of signals opt into failure, and there is no hard block that the user did not ask for. The default signals S1 to S5 are on, the context signal C1 is shown next to findings, and the experimental signals E1 to E3 stay off unless `--experimental` is given. Every rendering carries the rule set version, the baseline version, the snapshot digest and the tool version.

## The terminal report

The report is plain text with one block per finding, and it carries no meaning through colour alone so that it stays readable in logs and by screen readers; `--plain` removes the remaining decoration. A block names the level and the signal, the Package URL, a one-line explanation such as "new publisher (h:9f3a2c71) not in the previous maintainers; previous maintainers inactive (floor branch)", the date the state began and the date it lapses, the evidence with its observation times, the C1 value as context, and the rule and baseline versions.

## JSON

The JSON rendering is the findings array described in `03-data-model.md` together with a `run` object holding the tool version, the rule set, the baselines, the snapshot digest, the services queried and the policy, all serialised canonically.

## SARIF

The SARIF 2.1.0 rendering serves GitHub code scanning and GitLab Ultimate; GitLab ingests SARIF natively since version 18.11, enabled by default in 19.1 and generally available in 19.2, in the Ultimate tier only. Each signal becomes a rule with its identifier, name, short and full descriptions, a help URI into the specification and the rule version in its properties. Each finding becomes a result whose level is warning for warn and note for info, whose message carries the Package URL and whose physical location points at the SBOM file or at the lockfile line that declares the component, because GitHub requires a location per result. Evidence travels as related locations and in the result's properties. GitHub's limits of 25,000 results and ten megabytes per upload are respected by aggregating beyond them.

## The GitLab dependency-scanning report

GitLab's Free and Premium tiers do not ingest SARIF, so the tool also writes a `gl-dependency-scanning-report.json` in the schema GitLab expects, with one vulnerability entry per warn-level finding, a severity mapped from the level, identifiers carrying the signal identifier and rule version, and the package name and version taken from the Package URL.

## Data set rows

The same findings become rows of the signals table, with evidence reduced to summaries that carry no handles and no snapshot paths, as `10-dataset-publication.md` describes.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | the run completed, with or without findings under the warn policy |
| 1 | the run completed and the fail policy matched |
| 2 | input error, such as an unreadable SBOM or an unknown Package URL type |
| 3 | offline mode was requested and a required document was missing |
| 4 | a network or rate-limit failure persisted after retries |
