# Nexus Input Engine

Turn saved social content into a prioritized feed of reusable ideas, routed to *your* projects.

Nexus Input Engine is a small, file-based pipeline. You (or your AI) collect items you saved on a
platform (Instagram, X, …), it catalogs them into structured "fichas", reconciles a backlog,
and produces a **priority queue** and **adoption ledger** — so curiosity becomes capability, on a
budget (max N adoptions/week, no auto-adoption).

Created by **Adan (@adanviajante)**. Licensed under Apache-2.0.

## How it works (source-agnostic)

```
[collector]  ->  discovery/<date>_<source>.md   (what's new; a documented CONTRACT)
[you/AI]     ->  collections/<name>/*.md         (fichas: summary, themes, target projects)
engine/build_index.py      -> index.csv + manifest.json   (source of truth)
engine/engine_status.py    -> BACKLOG.md         (catalogued vs discovered-pending)
engine/promotion_queue.py  -> PROMOTION_QUEUE.md (what to catalog next, by value)
engine/candidates.py       -> candidates.md      (ideas by project axis: Engines / Content / Personal)
engine/adopt.py            -> adoption_log.csv   (record a decision; weekly cap enforced)
```

The **engine** is portable and knows nothing about any platform. The **collector** is a contract
(see `docs/DISCOVERY_CONTRACT.md`): it just has to emit discovery reports in the agreed format.
An Instagram reference collector ships in `collectors/`. Add your own source with `template_adapter.md`.

## Quickstart

1. Run the onboarding interview: open `docs/SETUP.md` with your AI and answer the questions.
   It seeds your `manifest.json` (your saved lists) and your project routing (`destination_axes`).
2. Collect: produce a `discovery/<date>_<source>.md` report (reference method in `collectors/`).
3. Catalog the new items into `collections/<name>/*.md` fichas.
4. Run the engine: `build_index -> engine_status -> promotion_queue -> candidates`.
5. Decide: adopt up to your weekly cap with `engine/adopt.py`.

See `demo/` for a runnable fake dataset and `CONTRACT.md` for the lifecycle rules.

## License & attribution
Apache-2.0. See `LICENSE` and `NOTICE`. Please keep the attribution to the original author.
