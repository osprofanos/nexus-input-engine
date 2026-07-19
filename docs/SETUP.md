# Setup — onboarding interview

Run this once, with your AI assistant, to generate your **`config.json`** — the file that
personalizes the engine to *your* saved lists and *your* projects. Nothing here is engine code;
you are just answering questions so your AI can write a small config file.

## How to use
Paste this whole file to your AI and say: "Interview me and write `config.json`." Your AI should ask
the questions below (one topic at a time), then write `config.json` at the repo root, validated
against `schema/config.schema.json`.

## Interview

### 1. Platforms & saved lists
- Which platforms do you save content on? (e.g. Instagram, X/Twitter, …)
- For **each saved list / collection** you want the engine to track, give:
  - a short `name` (lowercase, no spaces) — becomes a folder under `collections/`;
  - the `source` (`instagram`, `x`, or a custom name);
  - for **Instagram**: the `saved_collection_id` — the long number in the saved-list URL
    `https://www.instagram.com/<your-handle>/saved/<name>/<THIS_NUMBER>/`;
  - for **X / custom**: the list `url` (e.g. `https://x.com/i/bookmarks`).

### 2. Your projects (destinations) and their axes
List the projects/areas a saved idea could feed. For each, pick an **axis**:
- `system_project` — tools/automation/systems that compound (the "Engines" bucket);
- `content_channel` — blog, newsletter, video, social (the "Content" bucket);
- `personal` — personal growth / not for publishing.
Optionally give `aliases` (other words that mean the same project).

### 3. Cadence
- How often will you run collection + cataloging? (e.g. weekly.) This is your rhythm, not a setting —
  it just sets expectations for how fast the backlog turns.

### 4. Gates (already built into the engine — you only tune them)
- **Weekly adoption cap:** the engine enforces **max 3 adoptions per ISO week** (anti-dispersion),
  in `engine/adopt.py` (`WEEK_CAP`). Keep 3 (recommended) or change that constant to your number.
- **Sensitive content:** any ficha whose frontmatter has a non-empty `sensivel:` field is routed to
  your `personal` project and never treated as publishable. Mark sensitive items that way when cataloging.

## Output your AI writes: `config.json`
Shape (see `schema/config.schema.json` and `config.example.json`):
```
{
  "account": "your-handle",
  "dashboard_file": "DASHBOARD.html",
  "collections": [
    {"name": "ideas", "source": "instagram", "saved_collection_id": "<number-from-url>"},
    {"name": "bookmarks", "source": "x", "url": "https://x.com/i/bookmarks"}
  ],
  "projects_canon": [
    {"term": "Automation", "axis": "system_project", "aliases": ["Tooling"]},
    {"term": "Blog", "axis": "content_channel"},
    {"term": "Personal", "axis": "personal"}
  ]
}
```
Your AI should: validate against `schema/config.schema.json`; keep `config.json` **out of git**
(it is git-ignored on purpose — it is your identity); and NOT invent saved_collection_ids
(ask you to paste the real saved-list URLs).

## After onboarding
1. Collect: produce discovery reports per `docs/DISCOVERY_CONTRACT.md` (see `collectors/`).
2. Catalog new items into `collections/<name>/*.md` fichas.
3. Run the engine: `build_index -> engine_status -> promotion_queue -> candidates`, then adopt
   up to your weekly cap with `engine/adopt.py`.
See `demo/` for a runnable fake example.
