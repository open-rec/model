# OpenRec deployable artifacts

[![CI](https://github.com/open-rec/model/actions/workflows/ci.yml/badge.svg)](https://github.com/open-rec/model/actions/workflows/ci.yml)
![Manifest](https://img.shields.io/badge/manifest_schema-v1-4C1?logo=json&logoColor=white)
![Models](https://img.shields.io/badge/rank_artifacts-PyTorch%20%2B%20LightGBM-EE4C2C)

This repository is the deployable output cache for OpenRec. Raw inputs belong in
`example/data/<dataset>/{user,item,event}.csv`; recall tables, fitted feature spaces, entity feature
snapshots and rank checkpoints belong here.

Treat deployable model files as generated, versioned artifacts. Do not hand-edit checkpoints,
feature-space sidecars, manifests, feature-value snapshots, or large recall tables; regenerate and
validate the complete bundle instead. The canonical catalog is reviewed source metadata and is
updated through its compatibility rules and validator.

```text
default.manifest.json                  # raw-input and output SHA-256 contract
feature/catalog/
├── feature.catalog.json               # implementation-independent canonical feature registry
├── catalog.schema.json                # machine-readable catalog format
├── validate_catalog.py                # catalog and fitted-sidecar compatibility validation
└── README.md                           # ownership and compatibility rules
rank/item/
├── lr.pth
├── lr.manifest.json
├── fm.pth
├── fm.manifest.json
├── lightgbm.txt
├── lightgbm.manifest.json
├── lr.features.json                   # fitted LR encoding contract
├── fm.features.json                   # fitted FM encoding contract
├── lightgbm.features.json             # fitted LightGBM encoding contract
├── user_feature.csv                   # point-in-time user values for this rank release
└── item_feature.csv                   # point-in-time candidate values for this rank release
rank/user/
├── lr.pth
├── lr.manifest.json
├── fm.pth
├── fm.manifest.json
├── lightgbm.txt
├── lightgbm.manifest.json
├── lr.features.json
├── fm.features.json
├── lightgbm.features.json
└── user_feature.csv
recall/
├── content_i2i.csv
├── item_cf_i2i.csv
├── item_seq_emb.csv
├── hot.csv
├── new.csv
└── user_cf_u2i.csv
```

Each `rank/{target_type}` directory is a self-contained default rank release. Its `*.features.json`
defines model-specific column order, vocabularies, scaling and input dimension and is loaded as a
file by rank-engine. Its feature CSVs hold actual entity values; `InitStandalone` converts their
`event_*` columns into the same JSON snapshot shape used by the streaming data-processor.

`feature/catalog/feature.catalog.json` is the implementation-independent source of truth for the
logical features available to rank models. It defines stable meaning, time, identity, invalid-input,
aggregation, and materialization semantics. A rank model selects an ordered subset and keeps its
model-specific encoding in `*.features.json`; fitted vocabularies and normalization statistics do
not belong in the global catalog. Validate changes with:

```shell
python feature/catalog/validate_catalog.py
```

## Build and reuse

Both example modes run `example/scripts/ensure-model-artifacts.sh`. It hashes the three raw CSVs and
reuses this bundle only when every required output exists and its hash matches
`default.manifest.json`. Otherwise it invokes:

```shell
python -m tool.build_default_artifacts \
  --data /path/to/example/data/test \
  --model-root /path/to/model
```

The build uses the first 80% of event time as frozen feature history and the final 20% as rank
labels. A clicked impression's preceding expose remains in feature history but is not treated as a
negative training label. User ranking derives positives from users sharing positive item behaviour
and balances them with non-cooccurring user pairs. Both sides use the persisted UserFeature space;
the sidecar's `target_type` tells serving whether candidate vectors are Item or User vectors.
Training restores the best temporal-validation checkpoint and Item LR/FM/LightGBM must pass AUC 0.70 before
the bundle is atomically promoted. Recall
generation produces `item_cf_i2i`, `content_i2i`, `user_cf_u2i`, semantic-hash `item_seq_emb`, hot, and new
tables from the same inputs.

Regenerating the default bundle from different raw inputs makes the old bundle stale according
to its manifest. Routine cluster training does not overwrite these defaults or write back to Git.

## Global features and runtime releases

This repository has two roles: `feature/catalog` is reviewed source metadata, while `rank/` and
`recall/` hold generated default artifacts. The packaged copies in rec-algorithm and data-processor
must match the canonical catalog; check or synchronize them from this repository with:

```shell
python feature/catalog/publish_catalog.py --check
# After changing and validating the canonical definitions:
python feature/catalog/publish_catalog.py
```

rec-algorithm's `algorithm/feature/definitions/{lr,fm}.feature-set.json` declare each family's
implemented capabilities and default feature selection. rec-console selects a supported subset
for each training run. Feature engineering, new model adapters, historical backfills and aligned
online/offline computation remain engineering work; selecting a feature does not implement it.

The cluster training path is rec-console → Airflow → rec-algorithm Spark job → offline PyTorch
trainer. Spark prepares samples distributively; LR/FM train on the offline driver CPU. Evaluated
versions are written to the shared `openrec-model-artifacts` volume under
`/models/releases/{target_type}/{scene}/{version}`, with weights, fitted encoders, feature
selection, definition fingerprints, evaluation results and checksums. These runtime versions are
separate from this repository's bootstrap models. Training can finish while rank-engine is stopped.

Publication is an explicit rec-console operation; rank-engine only loads and scores the retained
version. Training never activates a model automatically. Changing the selected features requires
another training run. Moving training between services does not itself change feature semantics
or artifact formats, so compatible default weights and fitted sidecars need not be regenerated.
See [catalog compatibility rules](feature/catalog/README.md) before changing feature definitions.
