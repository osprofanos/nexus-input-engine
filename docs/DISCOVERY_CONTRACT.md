# Discovery Report Contract

A collector emits, per source list, a file `_system/discovery/<YYYY-MM-DD>_<collection>.md`:

Frontmatter (YAML):
```
---
type: discovery-report
collection: <name>            # matches a key in manifest.collections
collection_url: <url>         # the saved list / bookmarks URL
account: <handle-or-id>
detected_at: <YYYY-MM-DD>
baseline_count: <int>         # items already catalogued on disk
loaded_count: <int>           # items the collector loaded this run
new_count: <int>              # NEW items not yet catalogued  <-- the number the engine uses
state: DISCOVERED             # or DISCOVERED_PARTIAL if the baseline could not be fully reached
---
```

Body: a table, one row per NEW item, each row STARTING with a number and a pipe:
```
# | code | tipo | autor | url | gist
---|---|---|---|---|---
1 | <id-or-shortcode> | <type> | <author> | <url> | <short description>
2 | ...
```

Rules:
- `new_count` MUST equal the number of data rows.
- `code` is the platform's stable id (engine matches baseline on `id:` OR `shortcode:` of fichas).
- If a row's format differs (e.g. DM exports), the engine degrades gracefully — the worklist for
  that collection is just not auto-extracted; open the report by hand.
- `state: DISCOVERED_PARTIAL` tells the engine the pending count may be incomplete.
