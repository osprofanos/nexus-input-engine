## What this changes
A short description of the change and why.

## Type
- [ ] New source adapter (`collectors/…`)
- [ ] Engine fix / improvement
- [ ] Docs
- [ ] Other:

## Checklist
- [ ] The demo still runs end-to-end (`NEXUS_BASE=demo` → `build_index` … `candidates`).
- [ ] No personal data, handles, saved-list IDs, or credentials committed.
- [ ] `engine/` stays stdlib-only (no third-party deps).
- [ ] Hardening preserved (atomic write / read-back / heal-on-read) if `engine/` was touched.
- [ ] Config-driven — no hardcoded identity; user-specific values live in `config.json`.
- [ ] Updated the relevant docs (`README.md` / `docs/` / `collectors/`) if setup or behavior changed.

## Notes
Anything reviewers should know.
