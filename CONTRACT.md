# Input Lifecycle Contract

Lifecycle of an input:
DISCOVERED -> PROCESSED -> TRIAGED -> CANDIDATE
  -> (READY | GATED | WATCH | BLOCKED | HELD) -> ADOPTED -> (VALIDATED | REJECTED | DEFERRED)

Four truths (do not conflate):
- Inventory Truth  — does it exist? catalogued? where from?
- Interpretation Truth — what does it mean? themes/projects it touches?
- Adoption Truth   — did it become action? ready/gated/blocked/adopted?
- Impact Truth     — did it produce improvement/content/code/decision/learning?

Governance rules:
- An input does not become an action; it becomes a candidate.
- A candidate passes a promotion gate and must point to an EXISTING project.
- The target project must have capacity to absorb it.
- Max N adoptable inputs per ISO week (default 3) — anti-dispersion.
- No automatic adoption; no sub-agent executes; no paid API without approval.

Configure N and the sensitive-content boundary during onboarding (docs/SETUP.md).
