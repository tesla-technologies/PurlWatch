# ADR 0005: validation is pre-registered honestly and backed by a prospective register

Date 2026-10-04. Status accepted.

The signal rules were designed with xz-utils and event-stream in view. Claiming that the thresholds were frozen before any incident was examined would be false, and a technical reviewer would call it pre-registration theatre. Handover-class incidents with reconstructable public history before 2024 are rare, and the only out-of-sample test of lead time could end up with no qualifying incident at all.

The protocol states plainly that xz-utils and event-stream informed the rules and reports their lead time as consistency checks. Definitions, thresholds, state rules and the selection rule for a third incident are frozen in a tagged M1 release with a DOI before any validation run; the third incident is chosen under that rule before the tag and is the only out-of-sample test of lead time. From the M3 release onward, once the control-set test has fixed the default set, those defaults run monthly on the live corpus and a time-stamped register of what fired is published, which gives the final report a forward-looking test in any case. Credential-compromise and sabotage incidents serve only as negative controls, without any lead-time claim.

The validation report may contain two consistency checks, one out-of-sample incident or none, and a prospective register, and it says which is which. Warn-rate targets are reported, but lead time is the test, and the per-signal target of two per cent is labelled as what it partly is, a construction of the chosen percentile.
