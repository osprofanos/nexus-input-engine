---
name: New source adapter
about: Propose or request support for collecting from a new platform
title: "[adapter] "
labels: adapter
assignees: ''
---

## Platform
Which platform / source? (e.g. X, TikTok, Reddit, Pocket, RSS, …)

## How items are saved there
How does a user save/bookmark items, and how is a "list" identified (URL, id, feed)?

## Stable item id
What is the stable per-item id you'd put in the `code` column of a discovery report?
(The engine dedupes on this — see `docs/DISCOVERY_CONTRACT.md`.)

## Sample discovery report
If you can, paste a small example following the contract
(`_system/discovery/<date>_<name>.md`), even with 1–2 rows:

```
---
type: discovery-report
collection: <name>
collection_url: <url>
account: <handle-or-id>
detected_at: <YYYY-MM-DD>
baseline_count: 0
loaded_count: 2
new_count: 2
state: DISCOVERED
---

# | code | tipo | autor | url | gist
---|---|---|---|---|---
1 | <id> | <type> | <author> | <url> | <short gist>
2 | ...
```

## Are you offering to build it?
- [ ] Yes, I can open a PR with `collectors/<platform>_reference.md`
- [ ] No, this is a request

## Notes
Collectors must run in the user's own authenticated session — no bundled credentials, no bypassing
platform protections.
