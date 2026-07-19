# Template — add a new source

To support a new platform (X/Twitter, TikTok, Reddit, Pocket, RSS, …), you don't change the engine.
You just produce discovery reports in the contract format.

## Checklist
1. Add the source to `config.json` under `collections` (a `name`, a `source` string, and a `url` or id).
2. Collect (in your own session/tool) the items saved on that source.
3. Compute the baseline from existing fichas' `id:`/`shortcode:` in `collections/<name>/`.
4. Emit `_system/discovery/<YYYY-MM-DD>_<name>.md` in the contract format.

## Minimal report skeleton
```
---
type: discovery-report
collection: <name>
collection_url: <list-or-bookmarks-url>
account: <your-handle-or-id>
detected_at: <YYYY-MM-DD>
baseline_count: <int>
loaded_count: <int>
new_count: <int>
state: DISCOVERED
---

# | code | tipo | autor | url | gist
---|---|---|---|---|---
1 | <stable-id> | <type> | <author> | <url> | <short gist>
```

## Rules of thumb
- `code` must be a **stable** id for the item (so re-runs dedupe correctly).
- `new_count` must equal the number of rows.
- If your export format has no per-row numbering the engine's worklist extraction degrades gracefully —
  the item count still counts; you just open the report by hand to catalog.
- Keep it in your own session; never commit credentials (nothing here needs them).
