---
title: PiRequest and PiResult
---

# PiRequest and PiResult

`PiRequest` is the one input every coding-agent driver takes and `PiResult`
is the one output every driver returns — the pair is the **shared surface**
that lets `agents.execute()` run a phase without caring whether `pi`, Claude
Code, agy, or opencode is behind it. `PiRequest`'s own docstring is the whole
contract in one line: "Everything one non-interactive pi run needs."
(`.claude/skills/sssf/templates/adws/adw_modules/data_types.py:392-393`)

## Why it exists

The four driver modules each wrap a different CLI with a different event
stream, a different session-id convention, and different cost reporting. The
harness above them must not know any of that. `agents.py` states the rule at
the point it picks a driver:

> All expose the same surface — `run(request, on_event, on_spawn, on_exit)
> -> PiResult`, `resolve_model(pattern)`, `ToolCallTracker` — so everything
> below picks a module and stops caring which.
> (`adw_modules/agents.py:29-33`)

The "Pi" in the names is historical — `agent_pi` was the first driver, and
the later ones were written to its shape rather than the other way round.
`agent_cc.py`'s header says so plainly: "Mirrors `agent_pi.run()` one-for-one
so `agents.execute()` does not care which coding agent is behind a phase:
same `PiRequest` in, same `PiResult` out" (`agent_cc.py:3-5`); `agent_agy.py:3`
and `agent_opencode.py:3-4` open with the same sentence. Every driver's `run`
carries the identical signature — `agent_pi.py:211-213`, `agent_cc.py:333-335`,
`agent_agy.py:306-308`, `agent_opencode.py:228-230`.

## `PiRequest`

Source: `adw_modules/data_types.py:392-404`.

| Field | Type | Meaning |
|---|---|---|
| `prompt` | `str` | the user-turn text for this send |
| `system_prompt` | `str` | the agent's system text (roster prompt + skill engineering) |
| `model` | `str` | a registry *pattern*, resolved by the driver's `resolve_model()` to provider + id |
| `thinking` | `str = "medium"` | reasoning effort, passed through to the CLI |
| `session_id` | `str` | "creates or continues" — the same id re-enters the same context window |
| `session_dir` | `str` | where the driver keeps its own session state |
| `raw_output_path` | `str` | the JSONL event stream lands here (`raw_output.jsonl`) |
| `tools` | `Optional[list[str]]` | the roster's `tools:` list, or `None` |
| `extensions` | `list[str]` | harness-engineering extensions to load |
| `cwd` | `str = "."` | "set from `run.repo_root` — the codebase root agents work in" |

`agents.execute()` builds exactly one of these per send (`agents.py:302-315`).
Two details are load-bearing there: `session_dir` and `raw_output_path` are
made **absolute** because "these are read by the coding-agent subprocess,
which runs in `repo_root`", and `session_id` is reused across every send in
the phase — first prompt, JSON-fix retries, gate corrections — so they all
land in one session (see `handoff-and-output/Session-layout.md` for where
the files end up).

## `PiResult`

Source: `adw_modules/data_types.py:455-466`.

```python
class PiResult(BaseModel):
    text: str = ""
    returncode: int = 0
    session_id: str = ""
    tokens: int = 0
    cost: float = 0.0
    usage: UsageBreakdown = Field(default_factory=UsageBreakdown)
    # Context occupancy after the LAST turn — not a sum. `tokens` bills every
    # turn; this is how full the window is right now, which is what the
    # visualizer's context bar measures against `context_window`.
    context_tokens: int = 0
    context_window: int = 0         # 0 when the registry declares no ceiling
```

The comment on `context_tokens` is the one thing to internalize: `tokens` and
`usage` are **sums** (every turn bills), while `context_tokens` is a
**snapshot** (how full the window is after the last turn). `agents.execute()`
treats the two differently on purpose — it keeps `latest` (the last
`PiResult`, for context occupancy) and `spent` (a running `UsageBreakdown`
merged over every send, for cost), because "Parse retries and gate corrections
re-enter the SAME pi session, so the last send is the one whose context
occupancy is current — while spend is the opposite: every send costs"
(`agents.py:294-298`, `321-325`).

Not every driver fills every field. agy's header declares "NO COST DATA … so
`PiResult.cost` stays 0.0 for this interface and the trace's cost column is
silent rather than guessed" (`agent_agy.py:35-38`), whereas opencode sums a
real per-step `cost` (`agent_opencode.py:50-52`). A `0.0` here is therefore
"unknown", not "free".

## See also

- [UsageBreakdown](UsageBreakdown.md) — the type behind
  `PiResult.usage`, and why `tokens`/`cost` are duplicated there per component.
- [ToolCallTracker](ToolCallTracker.md) — the third member of the shared
  driver surface; it consumes the events `run()` streams via `on_event`.
- [Session directory layout](../handoff-and-output/Session-layout.md) — where `session_dir` and
  `raw_output_path` land on disk.
- `.claude/skills/sssf/references/config.md#coding-agents` — the
  `coding_agent:`/`model:` roster keys that choose which driver receives the
  request.
