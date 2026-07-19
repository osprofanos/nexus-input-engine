# Dashboard

A single self-contained HTML file that shows your engine at a glance: a small summary and a **priority
board** with three columns — **Engines**, **Content**, **Personal** — listing your top candidates per axis.

Open it in any browser; no server, no dependencies.

## Two generated blocks

The dashboard has two data blocks that the engine fills in; everything else is preserved byte-for-byte.

| Block | Filled by | Source |
|---|---|---|
| `const DATA = {…}` | `engine/refresh_dashboard.py` | `_system/index.csv` + `_system/manifest.json` (totals, per-axis counts) |
| `const RANK = […]` | `engine/dashboard_rank.py` | `_system/candidates.json` (`groups`: top per-axis) |

The **RANK is generated**, not hand-curated — re-run `dashboard_rank.py` and the board reflects your
current candidates. The two scripts are independent (separate anchors) and don't interfere.

## Refresh sequence

```bash
# NEXUS_BASE points at your data root (or the bundled demo/)
python engine/build_index.py          # index.csv + manifest.json
python engine/refresh_dashboard.py     # -> const DATA
python engine/candidates.py            # -> candidates.json (with groups)
python engine/dashboard_rank.py        # -> const RANK
# then open your dashboard HTML
```

Both HTML-writing steps support `--verify` (read-only; exit 1 on drift) and `--dry DIR` (write a copy
without touching the real file). Each keeps the same hardening as the rest of the engine: heal-on-read
against cloud-sync NUL corruption, atomic write + read-back verify, an `.md5` sidecar, and a dated backup.

## For contributors / custom dashboards

`dashboard_rank.py` swaps only the text between the literal anchors `const RANK = ` and `;` followed by
`/* END RANK */`. If you build your own dashboard HTML, keep those two markers around a JSON array and the
generator will fill it. `refresh_dashboard.py` uses `const DATA = ` … `;\nconst RANK` for the DATA block.
Each RANK item is `{group, id, title, collection, projects, url}`.
