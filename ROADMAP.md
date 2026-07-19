# Roadmap

Nexus Input Engine is intentionally small. This is where it's going, and where help is welcome.

## Shipped (v0.1.0)
- Stdlib-only, config-driven engine: `build_index → engine_status → promotion_queue → candidates → adopt`.
- Priority by axis (Engines / Content / Personal) and a weekly adoption cap.
- Onboarding interview (`docs/SETUP.md`) → generates your `config.json`.
- Runnable fake `demo/`, end-to-end.
- Reference collectors: **Instagram, X, TikTok, Pinterest** + an adapter template.

## Next
- **More source adapters** — Reddit, Pocket, YouTube "Watch later" / playlists, RSS/read-later. Each is
  just a discovery-report emitter (see `collectors/template_adapter.md`).
- **Generated dashboard RANK** — today the dashboard's `RANK` block is hand-curated; generate it from
  `candidates.json` so the priority board updates itself.
- **Optional media enrichment** — for video/idea items, an opt-in step that summarizes a linked
  transcript/article at catalog time (still no media analysis in the engine itself).
- **A real walkthrough** — a short GIF/screencast of the flow in the README.
- **Light tests** — a smoke test over `demo/` runnable in CI.

## Non-goals
- No scraping that bypasses a platform's protections. Collectors run in *your* authenticated session on
  *your own* saved content.
- No telemetry, no network calls in the engine.
- The engine stays stdlib-only and file-based — easy to read, audit, and fork.

## Want to help?
Open a **"New source adapter"** issue (there's a template) with the platform, how items are saved, the
stable per-item id, and a small sample discovery report. Adapters are the highest-leverage contribution.
