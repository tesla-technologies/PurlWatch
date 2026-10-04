# Validation protocol

The protocol is frozen in milestone M1 and executed in M6.

## Classification

Incidents are classified by mechanism according to the taxonomy of Ladisa and colleagues (IEEE S&P 2023). Metadata signals address handover, transfer and abandonment. They do not address credential compromise or maintainer sabotage, and the report says so before any result.

## Honest pre-registration

Two incidents shaped the rules, and the protocol treats that fact openly. Definitions, thresholds, state rules and the selection rule for a third incident are frozen in a tagged M1 release deposited with a DOI before any validation run. xz-utils and event-stream are reported as consistency checks. The third incident is chosen under the frozen selection rule before the tag and is the only out-of-sample test of lead time. From the M3 release onward, once the control-set test has fixed the default set, those defaults also run every month on the live corpus, and a time-stamped register of what fired is published, so that the M6 report has a forward-looking test whether or not a third incident qualifies.

The selection rule, in outline, asks for a handover visible in registry or forge metadata, a precursor at least thirty days before disclosure, disclosure before 2024, and a package on npm, on crates.io or reachable on the repository path. The pool of such incidents is thin, because most incidents between 2018 and 2023 were credential compromise or sabotage, so the expected outcome is that lead time is claimed on two incidents and the report says exactly that.

## Calibration

Baselines are computed on a time-split corpus of data before 2021, as of each evaluation date and excluding the package under test. The Libraries.io Open Data release of January 2020, which is CC BY-SA 4.0, and Wayback captures supply the maintainers as of that time; they are used for calibration only and nothing from Libraries.io is republished. The repository-only baseline for Package URLs without a registry is drawn from corpus repositories matched by activity profile rather than by ecosystem.

## The lead-time set

For xz-utils the facts to reconstruct are the organisation membership of 28 October 2022, Lasse Collin's last tagged release 5.4.1 on 11 January 2023, Jia Tan's first tagged release 5.4.2 on 18 March 2023 together with the fact that Jia Tan authored every GitHub release object from the first one on 13 December 2022, so that release-object authorship shows no change while the git tagger does, the malicious 5.6.0 on 24 February and 5.6.1 on 9 March 2024, the disclosure on 29 March 2024 and the build file that existed only in the tarball. The measurement runs on the repository path with the forge-asserted push and release actors from the ClickHouse GitHub events dataset, because the live GitHub API no longer reliably serves those release objects and organisation membership produces no event.

For event-stream the facts are the new account's appearance in the maintainers field and its publication of 3.3.5 on 5 September 2018 and of 3.3.6 with the flatmap-stream dependency on 9 September, the malicious flatmap-stream 0.1.1 on 5 October, the issue of 20 November and the npm advisory of 26 November 2018, which gives seventy-two days from 3.3.6 to the first report. The removed versions come from Wayback captures of the packument, with the npm advisory and the Snyk post-mortem as secondary sources if no capture exists.

The third incident is whatever the frozen rule selects. The npm purescript installer case of July 2019 is not a candidate, because the payload came from the outgoing maintainer's own dependencies within hours of the handover, which is sabotage under the classification; at most it serves as a negative control.

## Procedure per incident

For each incident the protocol defines the precursor date and the disclosure date, freezes the metadata at thirty, ninety and one hundred and eighty days before disclosure using push and release timestamps where a forge event feed exists and flagged committer dates elsewhere, runs the engine, and records which default signals were active and when.

## Negative controls

ua-parser-js, hijacked on 22 October 2021 with the malicious versions 0.7.29, 0.8.0 and 1.0.0, is a credential-compromise case in which the hijacked account itself published, so S3 is not expected to fire. The colors and faker sabotage of January 2022 is a maintainer-sabotage case. No lead time is claimed for either, and the report states what, if anything, fired at publication. left-pad in 2016, node-ipc in 2022 and the purescript installer in 2019 are optional additional controls.

## Control set and warn rates

The control set is matched by ecosystem, age and dependents and drawn from the corpus. The report gives the warn rate per signal with confidence intervals and the per-SBOM aggregate on the three reference SBOMs, together with a base rate within the corpus: of the packages on which S1 fired in 2018, what fraction were later compromised.

## Publication

The frozen snapshots, with e-mail addresses stripped, are published so that others can re-run the protocol, and the report states what could not be reconstructed.

## Targets

Lead time is reported per handover-class incident, and a claim is made only where a frozen default fired at least thirty days before disclosure. The prospective register is published monthly from M3. The binding warn-rate target is at most three per cent of components with any default warning on the three reference SBOMs; the per-signal target is at most two per cent of packages per default signal on the matched control set. Findings must be byte-identical on replay.
