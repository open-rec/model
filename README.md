# model

Pre-computed recall tables and a trained rank model for the **Douban** open dataset, produced by
[rec-algorithm](https://github.com/open-rec/rec-algorithm). Import them into a running open-rec
stack instead of training from scratch.

Everything here is for a single scene: `douban_movie`.

## recall

CSVs in the format `example/init` expects, ready to load into Redis / Elasticsearch.

| File | Rows | Size | Columns |
|---|---|---|---|
| `recall/i2i.csv` | 1,067,972 | 54 MB | `scene,left_item,right_item,score` |
| `recall/embedding.csv` | 37,844 | 9.0 MB | `scene,item,vector` |
| `recall/hot.csv` | 2,000 | 82 KB | `scene,item,score` |
| `recall/new.csv` | 2,000 | 49 KB | `scene,item,score` |

`i2i.csv` covers 57,321 distinct `left_item` values. `embedding.csv` vectors are **10-dimensional**,
matching the `dense_vector` mapping in
[recall-engine](https://github.com/open-rec/recall-engine/blob/main/es/design.md).

```
douban_movie,1458424,5218551,0.047553931074042384
douban_movie,27010768,"[-0.12139896303415298, 0.30065250396728516, ...]"
```

## rank

`rank/lr.pth` — a logistic regression `state_dict` saved with `torch.save`, 63 input features.

Load it into [rank-engine](https://github.com/open-rec/rank-engine); `dim` must match the feature
width it was trained with:

```shell
curl -X POST http://127.0.0.1:8000/model/load \
  -H 'Content-Type: application/json' \
  -d '{"type": "lr", "model": "model/lr.pth", "dim": 63}'
```

The feature width is a function of the one-hot cardinality of the user/item data in Redis, so this
checkpoint only fits the Douban dataset. Against a different dataset, retrain rather than reusing it.

## importing the recall data

`InitStandalone` reads a data directory containing `item.csv`, `user.csv`, `event.csv` and a
`recall/` subdirectory. This repo supplies **only the `recall/` part** — the raw `item` / `user` /
`event` tables for Douban are not included (too large for git), so you cannot seed a full stack from
this repo alone.

To use these tables, place them alongside the raw Douban CSVs and point the loader at that directory:

```
example/data/douban/
├── item.csv          # not provided here
├── user.csv          # not provided here
├── event.csv         # not provided here
└── recall/           # <- the four files from this repo
    ├── i2i.csv
    ├── hot.csv
    ├── new.csv
    └── embedding.csv
```

```shell
cd example
java -cp init/target/rec-example-init-1.0-SNAPSHOT-jar-with-dependencies.jar \
  com.openrec.example.InitStandalone 127.0.0.1 6379 127.0.0.1 9200 elastic '<es-password>' data/douban
```

For a runnable end-to-end setup without hunting for the Douban raw tables, use the generated sample
dataset in `example/data/test` instead — it ships with its own `recall/` tables and covers scenes
`scene_0` … `scene_2`.

## regenerating

```shell
cd rec-algorithm/tool
python gen_recall_data.py     # writes ../data/<scene>/recall/*.csv
```

`gen_recall_data.py` has the hot / new / embedding generators commented out by default — only i2i
runs. Enable the ones you need before running it.
