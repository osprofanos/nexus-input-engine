# X (Twitter) — reference collector

Collects your **own** X bookmarks or likes.

## How X maps to the engine
- Your **Bookmarks** (`https://x.com/i/bookmarks`) or **Likes** (`https://x.com/<you>/likes`) = a `collection`.
- Each post has a stable id, visible in its URL: `https://x.com/<author>/status/<STATUS_ID>`.
  Use `<STATUS_ID>` as the `code`.

## Config (`config.json`)
```json
{ "name": "x-bookmarks", "source": "x", "url": "https://x.com/i/bookmarks" }
```

## Prerequisites
- Logged into X in the browser/tool you'll use.

## Method (in your own session)
Open the bookmarks/likes feed and enumerate posts, collecting per post: `status id`, `author`, the post
text, and the URL. Scroll with a real gesture to trigger lazy-loading; early-stop at the first baseline hit.

Note: the likes feed can be long and not perfectly contiguous — if you can't reach your full baseline in one
pass, mark `state: DISCOVERED_PARTIAL` so the engine treats the pending count as a floor.

## Media & threads
Post text is the `gist`. For threads or media posts, capture the lead post's text (and note it's a thread);
the ficha's meaning is written at catalog time, as usual.

## Build the report
1. Baseline from existing fichas' `id:`/`shortcode:` in `collections/<name>/`.
2. New posts = loaded minus baseline.
3. Write `_system/discovery/<YYYY-MM-DD>_<name>.md` per [`docs/DISCOVERY_CONTRACT.md`](../docs/DISCOVERY_CONTRACT.md);
   `tipo` = `tweet`; `new_count` == rows.
4. `state: DISCOVERED_PARTIAL` where the baseline isn't fully reachable.

## Then
Catalog into `collections/<name>/*.md` and run the engine.

> Runs in *your* session on *your* saved content. No credentials in this repo.
