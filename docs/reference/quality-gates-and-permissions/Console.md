---
title: Console
---

# Console

`Console` (`.claude/skills/sssf/templates/adws/adw_modules/console.py:29-35`)
is the run's terminal reporter — "one narrative, two destinations." Every
line an ADW prints also lands in the database as a `log` event, so the
swim-lane observability UI reads the exact same story the terminal shows.
Both go through one internal `_emit`, so print output and the trace cannot
drift apart. Source: `console.py:1-7`.

## Categorization note

This concept is filed under quality-gates-and-permissions, not
observability, even though it emits into the same event store the Tracer
(`.claude/skills/sssf/references/observability.md#two-stores-one-truth`)
writes to. An earlier pass of this glossary's concept inventory grouped it
with observability by association; a fable critique pass corrected that —
`console.py` is genuinely about reporting/narrating a run to the operator at
the terminal, not about the tracer/UI machinery itself. It's grouped here
because the reporting discipline it embodies (deterministic, no
spinners/live displays) mirrors the same "verify after the fact, report
plainly" ethos as gates and permission enforcement, and because its bound
object (`run.console`) is reached from the same phase-execution code path
that gates and permission checks run in.

## Design: plain sequential lines, on purpose

`Console` deliberately avoids spinners or live-updating displays — "so a CI
log reads exactly like a terminal" (`console.py:6`). `KIND_COLOR` distinguishes
three kinds of narrator (`engineer`, `agent`, `code`) by color, and dynamic
text (summaries, violations, error messages) is clipped to `MAX_LINE = 160`
characters (`console.py:21-25`) so one runaway line can't swallow the log.

`Console` is bound to one run's tracer and reachable as `run.console`
everywhere in the ADW's execution — phases, gates, and permission checks all
narrate through the same object, which is why a failed gate or a
`PermissionBreach` shows up in the terminal and the trace in the same
words, not two independently-worded reports of the same event.

## See also

- [Gate](Gate.md) and
  [Permissions and writes](Permissions-and-writes.md) — the checks
  whose pass/fail narration flows through `Console`.
- `.claude/skills/sssf/references/observability.md#event-schema` — the
  `EventRecord` shape `Console`'s `log` events populate.
