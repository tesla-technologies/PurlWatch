# Data set publication

The data set is the project's primary contribution to the CodeSupply data commons.

## Corpus

The corpus is the most depended-upon packages of npm and crates.io, selected by dependents count from ecosyste.ms and deps.dev and by the OpenSSF Criticality Score. Version 0 of the data set, produced in milestone M3, covers one thousand npm packages. Version 1, produced in M5, covers five to ten thousand packages across both registries. PyPI and Maven Central are follow-up scope.

## Releases

A release is produced every month under a dated identifier such as `2027-09` and receives a DOI on Zenodo. Its notes list the rule and baseline versions, the changes to the corpus and the corrections made. It contains the three tables described in `03-data-model.md` as newline-delimited JSON and as Parquet, together with their JSON Schemas, and catalogue metadata in DCAT-AP 3.0.1 or as a Frictionless Data Package version 2, the profile being confirmed in M1 with NLnet and AboutCode. Each release also ships an import example for PurlDB, tested against a PurlDB instance from M3 onward, and a documented shape for the CodeSupply catalogue.

## What is new

deps.dev and ecosyste.ms already publish repository links. This data set adds agreement across several sources with a confidence class, time-stamping and versioning per release, a dispute path, and tables computed from registries and git so that they are not share-alike. The publisher-history table and the signals table exist nowhere else as open data.

## Disputes and corrections

Anyone may open an issue with the dispute template under `.github/ISSUE_TEMPLATE/`, naming the Package URL, the row and the reason. The maintainers answer within fourteen days with the evidence behind the row, taken from the retained snapshot, and either keep the row, correct it or annotate it. Corrections appear as annotated rows in the next release and the history is kept; nothing is silently removed. An objection by the person behind a keyed-hash identifier, under Article 21 of the GDPR, follows the same path, and when it succeeds the identifier is redacted with an annotation that preserves the row's history, as `11-privacy-and-licensing.md` describes.

## The pipeline

The scheduled pipeline reuses the command-line tool over the corpus: it collects, snapshots, computes signals, aggregates the tables, writes the catalogue metadata and publishes. It runs on a server the applicant contributes, with four cores, sixteen gigabytes of memory and two terabytes of storage. The pipeline itself is published so that a CodeSupply partner can mirror or run it, and the project asks one partner to do so before version 1.0.

## After the grant

The applicant commits to monthly refreshes for twenty-four months after the grant, at eight to twelve hours a month, with a DOI per release and the code deposited in Software Heritage. Should the refresh stop, the last release remains available under its DOI and the pipeline remains runnable by anyone.

## Licence

The preferred licence is CDLA-Permissive-2.0. The decision depends on whether any share-alike input, meaning ecosyste.ms or Libraries.io data under CC BY-SA 4.0, survives into the published tables; the design computes the tables from primary sources precisely so that none does. The decision is taken in M1 with NLnet's licensing support and explained in `11-privacy-and-licensing.md`.
