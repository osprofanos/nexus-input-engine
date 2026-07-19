# Architecture

Two layers, deliberately decoupled:

## 1. Engine (portable, ships here)
Pure stdlib Python over files. Never talks to any platform. Reads:
- `collections/<name>/*.md`  (fichas)
- `_system/index.csv`, `_system/manifest.json`  (derived source of truth)
- `_system/discovery/*.md`   (collector output)
- `_system/adoption_log.csv` (the ledger)
Writes derived artifacts only (BACKLOG, PROMOTION_QUEUE, candidates, and — on your explicit call —
one adoption_log row). Idempotent, atomic writes, heal-on-read against cloud-sync NUL corruption.

## 2. Collector (a contract, per-source, NOT shipped as a turnkey script)
Collection requires *your* authenticated session on the platform, so it cannot be a
"run and forget" binary. Instead this repo specifies the **Discovery Report Contract**
(`docs/DISCOVERY_CONTRACT.md`). Any collector — the Instagram reference, or your own for X/TikTok/
Reddit — just has to emit reports in that format. The engine consumes them identically.

## Priority model
`candidates.py` groups routable, not-yet-adopted fichas by destination axis:
- **Engines**  (system_project) — tools/automation that compound.
- **Content**  (content_channel) — blog/newsletter/video/social.
- **Personal** — everything else.
Ranked per-ficha by leverage (number of target projects). You adopt up to the weekly cap.

## Personalization
`manifest.json.destination_axes` maps *your* projects to axes. It is seeded by onboarding
(`docs/SETUP.md`), never hardcoded in the engine.
