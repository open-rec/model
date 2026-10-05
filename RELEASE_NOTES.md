# model v0.1.0

Released: 2026-10-05

Feature catalog and bootstrap artifacts. First coordinated OpenRec source release.

## Features

- Canonical feature catalog version 18, including identity, time, invalid-input and materialization semantics.
- Catalog validation and checks for packaged copies in rec-algorithm and data-processor.
- Separate item/user LR, FM and LightGBM bootstrap artifacts with fitted feature spaces.
- Default collaborative/content/vector/hot/new recall tables.
- Build-version-11 provenance with input/output hashes and selected feature definitions.

## Installation and compatibility

Deploy each checkpoint with its matching fitted sidecar. The distribution may reuse this bundle only after input, catalog and output validation; otherwise it generates a new bundle from committed sample data.

Runtime training releases are stored separately and do not overwrite these bootstrap artifacts. Fixed input data and split boundaries do not guarantee byte-identical PyTorch training output. Do not use experimental or obsolete scratch checkpoints as bootstrap releases.

## Validation and known boundaries

See this repository's README for build/test commands and deployment requirements. The coordinated release's [validation record](https://github.com/open-rec/openrec/blob/v0.1.0/release/VALIDATION.md) distinguishes checks executed for this release from historical integration evidence.

This initial release establishes a versioned source baseline. Source archives and checksums are published; external package registries and container registries are not populated by the source-release workflow. Upgrade the complete compatible distribution, retain data/checkpoints/artifacts, and preserve prior component refs for rollback.
