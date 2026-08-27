# OpenRec deployable artifacts

[![CI](https://github.com/open-rec/model/actions/workflows/ci.yml/badge.svg)](https://github.com/open-rec/model/actions/workflows/ci.yml)
![Manifest](https://img.shields.io/badge/manifest_schema-v1-4C1?logo=json&logoColor=white)
![Models](https://img.shields.io/badge/rank_artifacts-PyTorch-EE4C2C?logo=pytorch&logoColor=white)

This repository is the deployable output cache for OpenRec. Raw inputs belong in
`example/data/<dataset>/{user,item,event}.csv`; recall tables, fitted feature spaces, entity feature
snapshots and rank checkpoints belong here.

```text
default.manifest.json                  # raw-input and output SHA-256 contract
feature/default/
├── user_feature.csv                   # point-in-time values imported into feature:user:{id}
├── item_feature.csv                   # point-in-time values imported into feature:item:{id}
├── lr.features.json                   # fitted LR encoding contract
└── fm.features.json                   # fitted FM encoding contract
rank/default/
├── lr.pth
├── lr.manifest.json
├── fm.pth
└── fm.manifest.json
recall/
├── content_i2i.csv
├── item_cf_i2i.csv
├── item_seq_emb.csv
├── hot.csv
├── new.csv
└── user_cf_u2i.csv
```

`*.features.json` defines model-specific column order, vocabularies, scaling and input dimension. It
is loaded as a file by rank-engine and is not written to Redis. The two feature CSVs hold actual
entity values; `InitStandalone` converts their `event_*` columns into the same JSON snapshot shape
used by the streaming data-processor.

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
negative training label. Training restores the best temporal-validation checkpoint and both LR and
FM must pass AUC 0.70 before the bundle is atomically promoted. Recall
generation produces `item_cf_i2i`, `content_i2i`, `user_cf_u2i`, semantic-hash `item_seq_emb`, hot, and new
tables from the same inputs.

Cluster-produced defaults may overwrite standalone defaults. The manifest makes this safe: a
bundle computed from another raw dataset is stale rather than silently reused.
