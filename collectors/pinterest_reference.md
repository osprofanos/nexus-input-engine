# Pinterest — reference collector

Collects saved Pins from your **own** Pinterest boards. Works for image, video, and idea/story pins.

## How Pinterest maps to the engine
- A **Board** = a `collection`. Its URL is `https://www.pinterest.com/<your-username>/<board-slug>/`.
- A **Pin** = an item. Each pin has a stable id, visible in its URL: `https://www.pinterest.com/pin/<PIN_ID>/`.
  Use that `<PIN_ID>` as the `code` in the discovery report (the engine dedupes on it).

## Config (`config.json`)
Add each board you want to track. Pinterest boards are identified by their URL, not a numeric
saved-collection id, so use `source: "pinterest"` and put the board URL in `url`:

```json
{ "name": "recipes", "source": "pinterest", "url": "https://www.pinterest.com/you/recipes/" }
```

## Prerequisites
- You are logged into Pinterest in the browser/tool you'll use.
- You know each board's URL.

## Method (in your own session)
Ask your browser assistant (or work manually) to open the board and enumerate its pins, collecting per pin:
`pin id`, `title`, `description`, media type (image / video / idea), the pin URL, and — importantly — the
**source/destination link** (many pins link out to the original recipe, tutorial, or article). Do it in
small resumable passes; stop early when you reach a pin already in your baseline.

## Media & video pins — how "content" is captured
The engine does **not** watch videos or analyze images. Understanding comes from **text + your curation**:
- In the **discovery report**, the `gist` for a video/idea pin is its title + description (and, if useful,
  the source link).
- The real meaning ("what is this, how do I reuse it") is written into the **ficha** when you catalog it —
  by you or your AI, from the title/description/**source link**. If the linked source has a transcript or
  article (YouTube, blog, recipe), your AI can summarize that at catalog time. This is optional enrichment;
  the engine only needs a gist for the report and a summary for the ficha.

This is exactly how Instagram Reels are handled (caption/alt → ficha). Pinterest is often *easier*, because
pins usually carry a title, a description, and an outbound link.

## Build the report
1. **Baseline:** read the `id:`/`shortcode:` of every ficha in `collections/<board-name>/`.
2. **New pins:** anything you loaded that isn't in the baseline.
3. Write `_system/discovery/<YYYY-MM-DD>_<board-name>.md` per
   [`docs/DISCOVERY_CONTRACT.md`](../docs/DISCOVERY_CONTRACT.md): frontmatter (`collection`, `collection_url`,
   `account`, `detected_at`, `baseline_count`, `loaded_count`, `new_count`, `state`), then one row per NEW
   pin — `# | code | tipo | autor | url | gist` — where `tipo` is `video`/`image`/`idea`, `url` is the pin
   or source link, and `new_count` == number of rows.
4. If you couldn't reach the full board (very large boards load lazily), set `state: DISCOVERED_PARTIAL`.

## Then
Catalog the new pins into `collections/<board-name>/*.md` fichas (summary, themes, target projects, reuse
angle) and run the engine (`build_index → engine_status → promotion_queue → candidates`).

> Honesty note: like every collector, this reads *your* private saved content and runs in *your* session.
> No credentials live in this repo, and nothing you save ships with the engine.
