---
title: Defaults merging
---

# Defaults merging

Full definition: see
[`.claude/skills/sssf/references/config.md`'s "Defaults merging" section](../../../.claude/skills/sssf/references/config.md#defaults-merging).
(This page lives at `docs/reference/agent-configuration/`, so `../../../` reaches
the fork root — fixed by a fable review pass, which caught the link pointing at
a scratch-workspace-only path that would 404 once this tree moves into the
real fork.)

## Local framing

`defaults` merging is *how* `sssf.config.yaml`'s roster stays terse: each
`agents[]` entry states only what differs from `defaults`, and everything it
leaves unset is inherited. If you're reading a roster entry and wondering
where its `model` or `tools` came from when the entry itself doesn't set
them, this is the mechanism — check `defaults` next, not the entry in
isolation.

It's also the validation boundary. `agents.validate(cfg, REQUIRED_AGENTS)`
runs after merging, confirming every agent name an ADW declares exists,
resolves to a usable coding agent + model, and has both prompt files present
on disk. A miss there fails the run immediately — no agent is ever spawned
against a half-valid config. That validation step is why a typo'd agent name
in a chain fails loudly at startup rather than mysteriously mid-run.

`config.md` already covers the mechanics (merge order, what `validate()`
checks, the exact fields involved) in full — this page exists only to point
you there with enough context to know it's the right page before you click
through.

## See also

- `.claude/skills/sssf/references/config.md#shape` — the roster's overall
  shape, of which `defaults` is one key.
- `.claude/skills/sssf/references/config.md#fields` — the individual fields
  `defaults` and each `agents[]` entry can set.
