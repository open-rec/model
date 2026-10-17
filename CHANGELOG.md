# Changelog

## Unreleased — bootstrap build 17

- Group rank artifacts by target and model family; group recall tables by candidate entity.
- Distinguish ALS neighbor edges (`user_als_u2u.csv`) from user factors (`user_als_emb.csv`).
- Add Qwen3-Embedding-0.6B title/content vectors and rename both text document tables to `text_search.csv`.
- Keep all 41 generated files in the default checksum manifest; remove the Qwen-only sidecar.
- The online item text-search channel remains `sparse`; user text search remains offline.

## 0.1.0 — 2026-10-05

First coordinated release. See [release notes](RELEASE_NOTES.md) for features, compatibility and known limitations.

Bootstrap v18 removes optional `item_content_emb.csv` from the default bundle and retains
`item_title_emb.csv`. The generator supports `--include-content` for explicit offline generation.
The default manifest covers 40 artifacts (27 rank files and 13 recall tables).
