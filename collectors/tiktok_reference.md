# TikTok — reference collector

Collects your **own** saved/favorited TikTok videos. Nearly identical in shape to the Instagram collector.

## How TikTok maps to the engine
- A saved list (Favorites, or a **Collection** you created) = a `collection`.
- Each video has a stable id, visible in its URL: `https://www.tiktok.com/@<author>/video/<VIDEO_ID>`.
  Use `<VIDEO_ID>` as the `code`.

## Config (`config.json`)
```json
{ "name": "tiktok-saves", "source": "tiktok", "url": "https://www.tiktok.com/@you/favorites" }
```

## Prerequisites
- Logged into TikTok in the browser/tool you'll use.
- You know the URL of the saved list / collection.

## Method (in your own session)
Open the saved list and enumerate videos, collecting per video: `video id`, `author`, `caption/description`,
and the video URL. Scroll with a real gesture to trigger lazy-loading; early-stop at the first baseline hit.

## Media & video — how "content" is captured
Same as Instagram/Pinterest: the engine does not watch the video. The `gist` in the discovery report is the
**caption/description**; the ficha's meaning is written at catalog time from the caption (and, optionally, a
transcript if you fetch one). Short-form video captions are usually enough to route the idea to a project.

## Build the report
1. Baseline from existing fichas' `id:`/`shortcode:` in `collections/<name>/`.
2. New videos = loaded minus baseline.
3. Write `_system/discovery/<YYYY-MM-DD>_<name>.md` per [`docs/DISCOVERY_CONTRACT.md`](../docs/DISCOVERY_CONTRACT.md);
   `tipo` = `video`; `new_count` == rows.
4. `state: DISCOVERED_PARTIAL` if you can't reach the full list.

## Then
Catalog into `collections/<name>/*.md` and run the engine.

> Runs in *your* session on *your* saved content. No credentials in this repo.
