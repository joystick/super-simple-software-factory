---
title: Frontier
---

# Frontier

The frontier is the single next ticket `just watch` is allowed to claim: it
must be `Status: ready-for-agent`, every ticket it's blocked by must already
be `resolved`, and among everything qualifying, the lowest `(feature,
number)` pair wins. Source:
`.claude/skills/sssf/templates/adws/adw_watch.py:228-237`:

```python
def frontier(issues: list[Issue]) -> Issue | None:
    """The next issue to claim: ready-for-agent, every blocker resolved,
    lowest (feature, number) first -- same "first by number wins" rule
    wayfinder uses for its own frontier."""
    groups = group_by_feature(issues)
    candidates = [i for i in issues if i.status == READY and is_unblocked(i, groups[i.feature])]
    if not candidates:
        return None
    candidates.sort(key=lambda i: (i.feature, i.number))
    return candidates[0]
```

## Why it exists

An unattended watcher can't ask a human which ticket to do next, so the
selection rule has to be fully deterministic and safe on its own. "Frontier"
names that single deterministic choice: never "whatever looks interesting,"
always "the earliest unblocked ready thing, by a fixed tiebreak." The same
convention — first-by-number wins — is shared with `wayfinder`'s own
frontier concept, so an engineer who has worked with one recognizes the
other.

## Blocking is scoped per-feature

`Blocked by:` numbers (e.g. `Blocked by: 03`) are only unique **within one
feature directory** — `.scratch/<feature>/issues/NN-slug.md`. `frontier()`
groups issues by feature before resolving blockers
(`group_by_feature`, `adw_watch.py:210-217`) specifically so a `03` in one
feature never accidentally blocks against an unrelated feature's `03`.
`is_unblocked()` (`adw_watch.py:220-225`) then requires every named blocker
to already be `resolved` — a missing blocker (typo, wrong number) counts as
still-blocked rather than silently ignored, the safe default.

## What claiming the frontier does

Claiming is `dispatch()`'s job, not `frontier()`'s — `frontier()` only picks
the ticket. See `the-queue/The-queue-watcher.md` for the
claim/dispatch/resolve cycle that acts on whatever `frontier()` returns.

## See also

- [The queue watcher (just watch)](The-queue-watcher.md) — the full scan-claim-dispatch-resolve
  cycle `frontier()` is one step of.
- [Dark factory](Dark-factory.md) — where the frontier concept sits in the
  larger unattended-queue picture.
