# Changelog

## 0.2.0 — 2026-10-18 (bootstrap build 19)

- Default CPU builds contain 39 artifacts: 27 rank files and 12 recall tables.
- The checked-in bundle also retains verified `item_title_emb.csv`, for 40 checksummed outputs.
- Language-vector generation is opt-in; existing vectors are reused when the item input and output checksums match.
- Online text-search channels are `item_search` and `user_search`, reading `item-search` and `user-search` respectively.

## Bootstrap build 17 (historical)

- Group rank artifacts by target and model family; group recall tables by candidate entity.
- Distinguish ALS neighbor edges (`user_als_u2u.csv`) from user factors (`user_als_emb.csv`).
- Add Qwen3-Embedding-0.6B title/content vectors and rename both text document tables to `text_search.csv`.
- Keep all 41 generated files in the default checksum manifest; remove the Qwen-only sidecar.
- Online text-search channels are `item_search` and `user_search`, reading the `item-search` and `user-search` serving tables respectively.

## 0.1.0 — 2026-10-05

First coordinated release. See [release notes](https://github.com/open-rec/model/blob/v0.1.0/RELEASE_NOTES.md) for features, compatibility and known limitations.

Bootstrap v18 removes optional `item_content_emb.csv` from the default bundle and retains
`item_title_emb.csv`. The generator supports `--include-content` for explicit offline generation.
The v18 manifest covered 40 artifacts (27 rank files and 13 recall tables).
