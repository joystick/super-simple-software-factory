---
title: Session directory layout
---

# Session directory layout

Full definition: see
[`.claude/skills/sssf/references/handoff.md`'s "Session directory layout" section](../../../.claude/skills/sssf/references/handoff.md#session-directory-layout).
(This page lives at `docs/reference/handoff-and-output/`, so `../../../` reaches
the fork root — fixed by a fable review pass, which caught the link pointing at
a scratch-workspace-only path that would 404 once this tree moves into the
real fork.)

## Local framing

Every ADW run gets one `adw_id` and one directory under `data_dir`
(configured in `sssf.config.yaml` — see
`.claude/skills/sssf/references/config.md#fields`) holding everything that
run produced: prompts sent to each agent, `raw_output.jsonl` per phase,
`envelope.json` per phase, and the `context_handoff/` directory the phases
use to pass typed output to each other (see
`.claude/skills/sssf/references/handoff.md#the-typed-output-rule`).

This is the layout that makes `always_writable`
([Permissions and writes](../quality-gates-and-permissions/Permissions-and-writes.md)) meaningful — a
read-only agent still needs to write *somewhere*, and this session directory
under `data_dir` is that somewhere, granted unconditionally regardless of
the agent's own `writes` list. If you're trying to find where a specific
run's artifacts landed on disk, `handoff.md`'s section is the exact map;
this page just orients you to why the layout exists before you go read it.

## See also

- `.claude/skills/sssf/references/handoff.md#agent_mapjson-and-resuming` —
  how a later run resumes against files this layout produced.
- [Permissions and writes](../quality-gates-and-permissions/Permissions-and-writes.md) — why this
  directory is always writable regardless of an agent's `writes` config.
