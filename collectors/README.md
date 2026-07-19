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

## Reference collectors
- [`instagram_reference.md`](instagram_reference.md) — Instagram saved collections.
- [`template_adapter.md`](template_adapter.md) — skeleton to add any source (X, TikTok, Reddit, RSS, …).

You don't need code from us: any tool (a browser assistant, a small script in your own session, manual
copy) is fine as long as the output matches the contract.
