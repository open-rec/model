# OpenRec deployable artifacts

[Release v0.1.0](RELEASE_NOTES.md) · [Changelog](CHANGELOG.md)

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
rank/{item,user}/{lr,fm,lightgbm}/
├── {model}.pth / lightgbm.txt          # model weights
├── {model}.manifest.json              # evaluation and provenance
├── {model}.features.json              # fitted encoding contract
├── user_feature.csv                   # frozen user values for this model
└── item_feature.csv                   # item targets only
recall/item/
├── content_i2i.csv
├── item_cf_i2i.csv
├── user_cf_u2i.csv                     # candidate items, despite user triggers
├── item_seq_emb.csv
├── item_title_emb.csv                 # Qwen3 title vectors
├── text_search.csv                    # scene,item,text BM25 documents
├── hot.csv
└── new.csv
recall/user/
├── user_cf_u2u.csv                     # scene,left_user,right_user,score
├── content_u2u.csv                     # same U2U schema
├── user_als_u2u.csv                    # scene,left_user,right_user,score
├── user_als_emb.csv                   # scene,user,vector; local ALS factors
└── text_search.csv                    # scene,user,text BM25 documents
```

Each `rank/{target_type}/{model_type}` directory is a self-contained default rank release.
Its fitted sidecar defines column order, vocabularies, scaling and input dimension. Feature CSVs
hold actual entity values; identical default snapshots are copied into each model release so future
model-specific snapshots can evolve independently. `InitStandalone` uses the item LR snapshots.

Recall directories are classified by **candidate entity**, not trigger type.
The vector CSVs use the following algorithms:

- `recall/item/item_title_emb.csv`: real language-model vectors;
  the default is Qwen3-Embedding-0.6B (1024 dimensions). Query text must be encoded using
  the same model/revision and query instruction; the reusable Python encoder is available,
  and rec-server can call a configured embedding endpoint online; there is no fixed query CSV. The previous duplicate
  hash-based item query CSV is removed.
- `recall/user/user_als_emb.csv`: normalized 10-dimensional implicit-ALS user factors,
  distinct from `user_als_u2u.csv`, which contains precomputed similar-user edges.

For sequence recall, the existing bootstrap `item_seq_emb.csv` still uses its legacy hash fallback;
the Spark sequence job uses Word2Vec. Correcting that separate bootstrap fallback is deferred.

The optional online `query_title_emb` channel uses Qwen3-Embedding-0.6B (1024D).
With `EMBEDDING_ENABLED=true`, the shared initializer loads `item_title_emb.csv` into the global
`query-title-emb-index` alias; rec-server encodes query text through vLLM.
Startup first checks sampled online document vectors against this bundle.
The historical Music CRS experiment uses Qwen3-Embedding-8B (4096D); those vectors
must not be mixed with this bootstrap index. Historical experiment caches keep their
upstream `query_embeddings.npy` filenames. `text_search.csv` files contain searchable documents.

Layout build version 18 requires companion updates to rec-algorithm's builder/checker,
example's initializer/startup checks, and rank-engine's Compose bootstrap paths. Existing verified
v11/v12/v13/v14/v15/v16/v17 bundles can migrate without changing rank weights or evaluation records:

```shell
cd ../rec-algorithm
.venv/bin/python -m tool.migrate_default_layout --data ../example/data/test --model-root ../model
```

Migration validates input/output checksums, stages and validates the complete new bundle, then
promotes it and removes only obsolete manifest-listed files. The already removed Qwen-only
manifest is accepted as missing during migration and is dropped from the output inventory. Recall CSVs are generated from raw
inputs; do not edit them or their checksums by hand. Full rebuilds use the same v18 layout.

`feature/catalog/feature.catalog.json` is the implementation-independent source of truth for the
logical features available to rank models. It defines stable meaning, time, identity, invalid-input,
aggregation, and materialization semantics. A rank model selects an ordered subset and keeps its
model-specific encoding in `*.features.json`; fitted vocabularies and normalization statistics do
not belong in the global catalog. Validate changes with:

```shell
python feature/catalog/validate_catalog.py
```

## Build and reuse

The Qwen title-vector CSV uses Git LFS. After cloning, run `git lfs install`
and `git lfs pull` before validating or loading the bundle. Source archives may contain
LFS pointer files instead of the full CSVs; use an LFS-enabled checkout for these artifacts.


Both example modes run `example/scripts/ensure-model-artifacts.sh`. It hashes the three raw CSVs and
reuses this bundle only when every required output exists and its hash matches
`default.manifest.json`. Otherwise it invokes:

```shell
python -m tool.build_default_artifacts \
  --data /path/to/example/data/test \
  --model-root /path/to/model
```

Generating new title vectors requires the rec-algorithm text dependencies and a model
selected by `OPENREC_TEXT_EMBEDDING_MODEL` (default `Qwen/Qwen3-Embedding-0.6B`).
Set `OPENREC_MODEL_CACHE` to the operator-managed model cache; model paths are not hardcoded.
A verified v16-to-v17 migration only renames files and requires no model inference.

The build uses the first 80% of event time as frozen feature history and the final 20% as rank
labels. A clicked impression's preceding expose remains in feature history but is not treated as a
negative training label. User ranking derives positives from users sharing positive item behaviour
and balances them with non-cooccurring user pairs. Both sides use the persisted UserFeature space;
the sidecar's `target_type` tells serving whether candidate vectors are Item or User vectors.
Training restores the best temporal-validation checkpoint and Item LR/FM/LightGBM must pass AUC 0.70 before
the staged bundle is validated and its files are promoted. Recall
generation produces `item_cf_i2i`, `content_i2i`, `user_cf_u2i`, semantic-hash `item_seq_emb`, hot, and new
tables, plus user CF/content/ALS neighbor tables, Qwen title vectors, ALS user vectors,
and item/user text-search documents from the same inputs.

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

rec-algorithm's `algorithm/feature/definitions/{lr,fm,lightgbm}.feature-set.json` declare each family's
implemented capabilities and default feature selection. rec-console selects a supported subset
for each training run. Feature engineering, new model adapters, historical backfills and aligned
online/offline computation remain engineering work; selecting a feature does not implement it.

The cluster training path is rec-console → Airflow → rec-algorithm Spark job → offline trainer.
Spark prepares samples distributively; LR/FM use PyTorch and LightGBM uses its native CPU learner. Evaluated
versions are written to the shared `openrec-model-artifacts` volume under
`/models/releases/{target_type}/{scene}/{version}`, with weights, fitted encoders, feature
selection, definition fingerprints, evaluation results and checksums. These runtime versions are
separate from this repository's bootstrap models. Training can finish while rank-engine is stopped.

Publication is an explicit rec-console operation; rank-engine only loads and scores the retained
version. Training never activates a model automatically. Changing the selected features requires
another training run. Moving training between services does not itself change feature semantics
or artifact formats, so compatible default weights and fitted sidecars need not be regenerated.
See [catalog compatibility rules](feature/catalog/README.md) before changing feature definitions.


The committed default bundle may predate additive catalog updates. Passing
`feature/catalog/validate_catalog.py` validates its selected definitions; it does
not mean the whole bundle is current. The distribution's
`ensure-model-artifacts.sh` checks catalog provenance, build version and input
hashes before reuse. The current bootstrap builder selects only features actually
materialized in the CSV snapshots and records that subset in model manifests;
new session/context/commerce declarations are not silently trained as zeros.
Regenerate defaults through that script instead of editing checkpoints or hashes.

## Reproducing startup acceptance

The distribution manifest does not check out this repository in CI: fresh runners generate the
bootstrap bundle from `example/data/test`, whereas local startup may reuse a validated bundle.
Matching input hashes does not imply that separately trained LR/FM checkpoints are byte-identical;
the default builder fixes the validation split but does not fix all PyTorch training randomness.
Record the bundle's output hashes when comparing local and CI recommendations.

Final top-N membership can change across valid bundles. Recall availability is checked using
rec-server's pre-selection `recallDiagnostics`, not by requiring all channel labels in the final
results. Keep the failing bundle for regression checks instead of editing weights or recall tables
to force particular items into the result. The Java 21 migration changes application/engine
runtimes, not the requirement to deploy each model together with its matching feature sidecars.

## Recall naming contract

CSV basenames and Airflow algorithm IDs use underscores. Airflow writes Hive tables as
`openrec.recall_{algorithm}` (user text search uses `openrec.recall_user_text_search`). The publisher maps these to the graph's serving `tableName`:

| CSV (under `recall/`) | Airflow algorithm | Graph tableName | Graph recallType |
| --- | --- | --- | --- |
| item/hot.csv | hot | hot | hot |
| item/new.csv | new | new | new |
| item/item_cf_i2i.csv | item_cf_i2i | item-cf-i2i | item_cf_i2i |
| item/content_i2i.csv | content_i2i | content-i2i | content_i2i |
| item/user_cf_u2i.csv | user_cf_u2i | user-cf-u2i | user_cf_u2i |
| item/item_seq_emb.csv | item_seq_emb | item-seq-emb | item_seq_emb |
| item/item_title_emb.csv | query_title_emb | query-title-emb | query_title_emb |
| item/text_search.csv | text_search | item-search | item_search |
| user/user_cf_u2u.csv | user_cf_u2u | user-cf-u2u | user_cf_u2u |
| user/content_u2u.csv | content_u2u | content-u2u | content_u2u |
| user/user_als_u2u.csv | user_als_u2u | user-als-u2u | user_als_u2u |
| user/user_als_emb.csv | offline only | — | — |
| user/text_search.csv | text_search (target_type=user) | user-search | user_search |

Ordinary recall uses `openrec-recall-{tableName}-active`; sequence vectors use the per-scene
`{scene}-item-seq-emb-index` alias. `query_title_emb` uses the global title-vector index and is
excluded from the default item daily DAG. GPU deployments can explicitly enable the
query provider and add `query_title_emb` to the published DAG configuration. Query and candidate vectors must share the exact model
and preprocessing recipe. User embedding serving consumes precomputed U2U edges, despite
the graph node being named EmbeddingNode.

The item/user text document snapshots are named `text_search.csv` in build v17.
The graphs use `item_search` and `user_search` channels, with separate `item-search` and `user-search`
serving tables. Standalone and cluster initialize both tables from these model CSVs. The Qwen-only manifest is no longer emitted or required.

## Manifest scope

`default.manifest.json` schema v1 / build v18 covers all 40 generated files: 27 rank
artifacts and 13 recall CSVs. It records the three raw-input hashes, feature catalog identity,
feature cutoff and output hashes. Its `created_at` and `source` describe the original bundle
build; `layout_migration` describes the subsequent layout migration. These are not new training dates.

Each of the six rank manifests references its model and fitted feature file relative to its own
model-family directory, and records feature identity, dimensions and evaluation results.
The default manifest provides the checkpoint checksums. Recall artifacts currently share the
bundle-level input/output hash contract; a complete per-algorithm parameter/provenance schema
has not yet been added. No Qwen-specific manifest is required or generated.

## Current recall inventory

Counts below describe the build-18 bundle for `example/data/test`. Entity keys are scoped by
`scene`; the same user may appear in multiple scenes. Vector values are finite and L2-normalized.

| File under `recall/` | Schema | Rows | Vector dimension |
| --- | --- | ---: | ---: |
| item/content_i2i.csv | scene,left_item,right_item,score | 200000 | — |
| item/item_cf_i2i.csv | scene,left_item,right_item,score | 5860 | — |
| item/user_cf_u2i.csv | scene,user,item,score | 18913 | — |
| item/hot.csv | scene,item,score | 5353 | — |
| item/new.csv | scene,item,score | 6000 | — |
| item/item_seq_emb.csv | scene,item,vector | 10000 | 10 |
| item/item_title_emb.csv | scene,item,vector | 10000 | 1024 |
| item/text_search.csv | scene,item,text | 10000 | — |
| user/content_u2u.csv | scene,left_user,right_user,score | 530750 | — |
| user/user_cf_u2u.csv | scene,left_user,right_user,score | 40550 | — |
| user/user_als_u2u.csv | scene,left_user,right_user,score | 530750 | — |
| user/user_als_emb.csv | scene,user,vector | 10615 | 10 |
| user/text_search.csv | scene,user,text | 10615 | — |

Item text-search documents concatenate `title/category/tags`; user documents concatenate
`name/gender/country/city/tags`, omitting missing fields. User recall entities are scoped by
positive interactions (`click`, `collect`, `buy`) in each scene. The local ALS edge scores
are cosine similarities of the vectors in `user_als_emb.csv`. Neighbor tables contain no
self-edges or duplicate scene/left/right keys. These are data integrity properties, not a
new measurement of recommendation quality.

Build v18 omits `item_content_emb.csv` from the default bundle to reduce download size.
The generator can still produce it explicitly with `--include-content`; it is not a default
required artifact. Only `item_title_emb.csv` is stored in Git LFS.
