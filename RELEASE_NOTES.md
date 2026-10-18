# model v0.2.0

Released: 2026-10-18

Part of the coordinated OpenRec v0.2.0 source release.

## Changes since v0.1.0

- Publish bootstrap build 19 with rank/{item,user}/{lr,fm,lightgbm} and recall/{item,user} directories.
- Retain 40 checksummed outputs, including verified optional title vectors; CPU-only generation produces 39 artifacts.
- Align ALS vectors/edges and text-search names; preserve checkpoints and fitted feature sidecars together.

## Installation and compatibility

This release does not regenerate or modify model weights, data tables or checksums. Use the matching rec-algorithm v0.2.0 builder/checker and preserve fitted feature sidecars. Runtime training releases remain separate from this bootstrap bundle.

See the [distribution upgrade and rollback instructions](https://github.com/open-rec/openrec/blob/v0.2.0/RELEASE_NOTES.md) for the complete compatible component set and persisted configuration migrations.

## Validation and publication

The [validation record](https://github.com/open-rec/openrec/blob/v0.2.0/release/VALIDATION.md) distinguishes release checks from maintainer-reported prior CI and integration results. GitHub Actions publishes source archives and SHA-256 checksums; Maven Central, PyPI and versioned container registries are not populated by this workflow.
