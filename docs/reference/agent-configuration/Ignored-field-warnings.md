---
title: Ignored-field warnings
---

# Ignored-field warnings

An ignored-field warning is the stderr line SSSF prints at config-validation
time when a roster entry sets a field that its `coding_agent` will never read.
It is produced by `ignored_field_warnings(agent)` in
`.claude/skills/sssf/templates/adws/adw_modules/agents.py:95-118`, called once
per required agent from `validate()` (`agents.py:220-221`). It is **a warning,
never a failure**: the run still starts, the field is simply named as inert
so the operator knows it is doing nothing.

Two fields are checked today (`agents.py:108-117`):

- `harness_engineering` — pi extension paths, only honoured under
  `coding_agent: pi`. Set it on a `claude_code`/`agy`/`opencode` agent and you
  get: `agent 'X': harness_engineering is set but coding_agent is
  'claude_code' — harness_engineering only takes effect under coding_agent: pi
  and will be ignored`.
- `skill_engineering` — vendored skill files composed onto the system prompt.
  Warned when `skill_engineering_applies(agent)` is `False`, which today it
  never is (see below).

## Why it exists

The failure mode this guards against is *silent-ignore-with-billing*: a field
that looks configured, costs nothing to write, and does nothing at runtime —
or worse, does something the operator was told it does not. The docstring on
`skill_engineering_applies()` (`agents.py:65-92`) records the concrete
incident: an earlier version had `execute()` compose skills unconditionally
while the warning claimed pi/agy agents were unaffected, so "the warning was
actively false, and pi/agy agents had skills injected and billed with no
signal that it was happening." The fix was to make one predicate the single
source of truth, called both by `execute()` (`agents.py:255`, `:290`) to decide
whether to compose, and by `ignored_field_warnings()` to decide whether to
warn. Two independent checks cannot drift apart if there is only one check.

The `harness_engineering` case is the simpler one: pi extensions are
TypeScript loaded into pi's harness, and Claude Code's equivalents (MCP
servers, hooks) arrive through different flags, so the field is not
translated — it is ignored, and `agent_cc.build_command` never reads it. The
config reference is explicit that this is "not deferred, not partially
honoured" (`.claude/skills/sssf/references/config.md:340`).

Two design choices in the function itself are worth knowing:

- **Warn, do not fail.** The comment at `agents.py:215-219` explains: a roster
  with the other coding agent's field set is still a *valid* roster —
  someone may flip an agent between `pi` and `claude_code` later — so it is
  reported, not rejected. Contrast `validate()`'s hard failures (unknown
  `coding_agent`, missing prompt file, missing skill file) at
  `agents.py:196-214`.
- **Printed to stderr, not through `run.console`.** `validate()` runs before
  any `Run` or trace exists, so there is nothing yet for the warning to be
  recorded against (`agents.py:217-219`). Look for it in the terminal, not in
  the trace database.

The `skill_engineering` branch is currently dead code by design.
`skill_engineering_applies()` returns `True` for all four known coding agents
(`agents.py:92`), so the second warning can never fire today. The docstring
at `agents.py:100-105` keeps it anyway: the allowlist is deliberate rather
than `return True`, so a fifth `coding_agent` added without being confirmed
against its own interface module will trip this warning instead of silently
reintroducing the billing bug.

```python
def ignored_field_warnings(agent: AgentConfig) -> list[str]:
    warnings = []
    if agent.coding_agent != "pi" and agent.harness_engineering:
        warnings.append(...)   # harness_engineering only under pi
    if not skill_engineering_applies(agent) and agent.skill_engineering:
        warnings.append(...)   # presently unreachable — see docstring
    return warnings
```

(`agents.py:95-118`, abridged.)

## Why this is an own page, not a link

`sssf.config.yaml` documents its fields as inline comments in config source,
not as headed prose, so there is no anchor to link into. `config.md` does
mention the warning — at `config.md:49` (the `harness_engineering` field row)
and `config.md:340` (the "Harness engineering" section) — but only as a
pointer to `ignored_field_warnings()`, never as a definition of the
mechanism. This page is that definition.

## See also

- [Defaults merging](Defaults-merging.md) — the merge step that runs *before* validation;
  a field inherited from `defaults` triggers this warning exactly as a
  per-agent field does (`load_config`, `agents.py:52-62`).
- [Audit skills](../observability/Audit-skills.md) — `just skills` applies the same
  `skill_engineering_applies()` predicate to report agents that name a
  skill their `coding_agent` will never receive, as `[ignored by: ...]`.
- `.claude/skills/sssf/references/config.md#harness-engineering` and
  `#skill-engineering` — what the two fields do when they *are* honoured.
