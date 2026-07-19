# Collectors

A **collector** turns the items you saved on a platform into **discovery reports** the engine can read.
That is its only job.

## The contract (the whole thing)
A collector writes, per saved list, a file `_system/discovery/<YYYY-MM-DD>_<collection>.md` in the format
of [`docs/DISCOVERY_CONTRACT.md`](../docs/DISCOVERY_CONTRACT.md). The engine reads that and nothing else —
it never sees the platform, your login, or how you collected.

## Principles
- **Your session, your data.** A collector runs in *your* authenticated session and reads *your own*
  saved items. Credentials never enter this repo (`config.json` is git-ignored; there are no tokens here).
- **Baseline = what you already catalogued.** Before reporting, read the `id:`/`shortcode:` of the fichas
  already in `collections/<name>/*.md`. Report only items NOT in that set (`new_count`).
- **Resumable & partial-aware.** If you can't reach the full baseline in one pass (some lists load lazily),
  collect what you can and mark `state: DISCOVERED_PARTIAL` so the engine knows the pending count is a floor.
- **Text, not media.** The engine never watches videos or analyzes images — understanding comes from the
  item's title/caption/description/link (the `gist`) plus what you or your AI write into the ficha at
  catalog time. Video pins/reels are handled exactly like anything else.

## Available reference collectors
- [`instagram_reference.md`](instagram_reference.md) — Instagram saved collections.
- [`x_reference.md`](x_reference.md) — X (Twitter) bookmarks / likes.
- [`tiktok_reference.md`](tiktok_reference.md) — TikTok saved / favorited videos.
- [`pinterest_reference.md`](pinterest_reference.md) — Pinterest boards (image / video / idea pins).
- [`template_adapter.md`](template_adapter.md) — skeleton to add any other source (Reddit, Pocket, RSS, …).

You don't need code from us: any tool (a browser assistant, a small script in your own session, manual
copy) is fine as long as the output matches the contract.
