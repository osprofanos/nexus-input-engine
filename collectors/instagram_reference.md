# Instagram — reference collector

Collects a saved collection from **your own** logged-in Instagram session.

## Prerequisites
- You are logged into Instagram in the browser/tool you'll use.
- You know the saved list's `name` and `saved_collection_id` (see below).

## Find your `saved_collection_id`
Open the saved list in a browser. The URL looks like:
`https://www.instagram.com/<your-handle>/saved/<name>/<SAVED_COLLECTION_ID>/`
The long number is the id. Put it in `config.json` under that collection.

## Method (either works)
Both run in *your* session; neither stores credentials.

1. **Authenticated read (preferred).** Ask your browser assistant (or a small script in your session) to
   page through the saved collection's items and collect each item's shortcode/id. Do it in small resumable
   passes; stop early when you reach an item already in your baseline.
2. **Scroll + DOM.** Open the saved list, scroll with a real gesture to trigger lazy-loading, and read the
   post codes from the page as they appear; early-stop at the first baseline hit.

## Build the report
1. **Baseline:** read the `id:`/`shortcode:` of every ficha in `collections/<name>/`. That's what you've
   already catalogued.
2. **New items:** anything you loaded that isn't in the baseline.
3. Write `_system/discovery/<YYYY-MM-DD>_<name>.md` per `docs/DISCOVERY_CONTRACT.md`:
   frontmatter with `collection`, `collection_url`, `account`, `detected_at`, `baseline_count`,
   `loaded_count`, `new_count`, `state`; then one table row per NEW item
   (`# | code | tipo | autor | url | gist`), with `new_count` == number of rows.
4. If you couldn't reach the full baseline (e.g. a very long list, or a likes feed), set
   `state: DISCOVERED_PARTIAL`.

## Then
Catalog the new items into `collections/<name>/*.md` fichas and run the engine
(`build_index → engine_status → promotion_queue → candidates`).

> Honesty note: this step is the one thing that can't be "run and forget" — it needs your authenticated
> session, because it reads your private saved items. The rest of the engine is plain file processing.
