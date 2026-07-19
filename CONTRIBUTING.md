# Contributing to Nexus Input Engine

Thanks for wanting to build on this. The most valuable contributions are **new source adapters** and
small, well-scoped improvements. This project favors the smallest safe change over cleverness.

## Principles

- **Stdlib-only engine.** No third-party dependencies in `engine/`. Keep it portable and auditable.
- **Config-driven, zero hardcoded identity.** Anything user-specific (handles, saved-list IDs, project
  names) belongs in `config.json` (seeded by onboarding), never in code.
- **Your data stays yours.** No telemetry, no network calls in the engine. Collectors run in the
  contributor's own session; never commit credentials or personal data.
- **Preserve the hardening.** `build_index.py` / `refresh_dashboard.py` use atomic writes, read-back
  verification, and heal-on-read against cloud-sync corruption. Don't remove those guards.
- **Human-in-the-loop by design.** No automatic adoption; the weekly cap (`WEEK_CAP` in `adopt.py`) is
  intentional anti-dispersion.

## Dev setup

You need **Python 3.11+**. There is nothing to install.

```bash
git clone https://github.com/osprofanos/nexus-input-engine.git
cd nexus-input-engine

# run the whole pipeline on the bundled fake demo:
# PowerShell:  $env:NEXUS_BASE="$PWD\demo"
# bash:        export NEXUS_BASE="$PWD/demo"
python engine/build_index.py
python engine/engine_status.py
python engine/promotion_queue.py
python engine/candidates.py
python engine/adopt.py --list-week
```

The `demo/` folder is fake data safe to experiment with. Regenerated outputs (`index.csv`,
`BACKLOG.md`, etc.) are git-ignored — leave `demo/` with only its inputs when you're done.

## Adding a source adapter (the main contribution path)

You do **not** change the engine to support a new platform. You emit **discovery reports** in the
contract format and the engine consumes them identically.

1. Read [`docs/DISCOVERY_CONTRACT.md`](docs/DISCOVERY_CONTRACT.md) and
   [`collectors/template_adapter.md`](collectors/template_adapter.md).
2. Write `collectors/<platform>_reference.md` documenting how to collect from that platform **in the
   contributor's own authenticated session** (like `collectors/instagram_reference.md`).
3. If you include a helper script, keep it stdlib-only where possible, and make clear it runs locally
   in the user's session. Never bundle credentials or bypass a platform's protections.
4. Add a demo discovery report under `demo/_system/discovery/` if it helps others test.

## Pull requests

- Keep commits small and scoped; describe what changed and why.
- Confirm the demo still runs end-to-end (see Dev setup).
- No personal data, no credentials, no third-party deps in `engine/`.
- Update the relevant doc (`docs/`, `collectors/`, or `README.md`) when behavior or setup changes.

## Reporting issues

Use the issue templates (bug report / new source adapter). The more concretely you can describe the
saved list, the discovery report, and what the engine did, the faster it gets resolved.

## Code of conduct

Be kind and constructive. This is a small tool meant to help people turn what they save into what they
build — keep that spirit.
