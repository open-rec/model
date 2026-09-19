# OpenRec feature catalog

This directory is the implementation-independent registry of features that rank models may use.
It defines the meaning of a feature, not how a particular model encodes it and not how Flink,
Spark, pandas, Redis, or PyTorch computes or stores it.

The four feature layers are deliberately separate:

1. `feature.catalog.json` defines canonical logical features and their stable semantics.
2. rec-algorithm's `algorithm/feature/definitions/{lr,fm,lightgbm}.feature-set.json` declare supported
   features and defaults; each training run selects an ordered subset through rec-console.
3. `rank/{item,user}/*.features.json` records the fitted encoding for one model family,
   including vocabularies and normalization statistics.
4. `*_feature.csv` contains point-in-time feature values.

## Compatibility rules

- A feature id always has one meaning. Change `definition_version` and introduce a new id when a
  change affects values, including its source field, filter, aggregation, window, time boundary,
  deduplication, null/default behavior, or exact-versus-approximate semantics.
- Model-specific transforms such as normalization, clipping, bucketization, hashing, vocabulary,
  embedding size, and feature crosses do not belong in this catalog.
- Storage keys, engine state, watermark implementation, SQL, and physical table names do not
  belong in this catalog. `materialization` only declares whether the same logical value is
  expected to be available online and/or offline.
- Catalog membership does not require every model to consume a feature. Each rank model selects an
  ordered subset and publishes that selection with its fitted feature space.

Run `python feature/catalog/validate_catalog.py` before publishing a change. The validator checks
the catalog structure and ensures every feature referenced by the checked-in fitted rank sidecars
exists in the catalog.

Run `python feature/catalog/publish_catalog.py` after an approved catalog change. It creates the
self-contained copies packaged by rec-algorithm and data-processor; `--check` is the CI drift gate.
Catalog version and SHA-256 identify provenance in fitted spaces, model manifests and realtime
snapshots. New fitted spaces also record fingerprints of the selected feature definitions:
serving validates those definitions against its packaged catalog, allowing unrelated additions.
Legacy fitted spaces retain whole-catalog validation. Realtime snapshot compatibility is checked
separately; subset compatibility does not permit arbitrary producer schema changes.

The catalog defines business values, not fitted vocabularies or model transforms. Runtime training
releases keep their own selected subset and fitted encoders in the shared model artifact volume;
they do not rewrite this catalog or the default artifacts in this repository. New feature semantics
require coordinated catalog publication, producer implementation, backfill where needed, and
online/offline verification before training and explicit deployment.
