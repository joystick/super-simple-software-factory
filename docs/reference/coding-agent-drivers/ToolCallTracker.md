---
title: ToolCallTracker
---

# ToolCallTracker

A `ToolCallTracker` is the per-driver class that folds a coding agent's raw
event stream into **one normalized record per completed tool call**. Every
driver module ships its own — `agent_pi.py:144`, `agent_cc.py:219`,
`agent_agy.py:238`, `agent_opencode.py:188` — with the same two-method shape,
so `agents._event_forwarder` "consumes either without knowing the difference"
(`agent_cc.py:225-226`).

## Why it exists

No CLI emits "a tool call" as one event. `agent_pi.py`'s docstring describes
the problem for pi: it "announces a call as a `toolCall` content block, then
emits `tool_execution_start` / `_update` / `_end` for it. Only the end carries
the result, so that is where a record is emitted — one trace event per real
tool call, the moment it returns, instead of three shapeless ones."
(`agent_pi.py:145-150`)

That "one event per real call" contract is what the tracer and the Visualizer
rely on: `observability.md` defines the `tool_call` event type as "one event
per real call", carrying `{tool, tool_call_id, args, result_snippet, ok,
duration_ms, agent}` (`.claude/skills/sssf/references/observability.md:19`),
and it is "the one event that spans time", filling both `started_at` and
`ended_at` on the row so the UI can lay calls on a time axis "without parsing
every payload" (`observability.md:44`, `agent_pi.py:152-154`). The tracker is
the component that makes that promise true regardless of which CLI produced
the stream.

## Shape

```python
class ToolCallTracker:
    def __init__(self) -> None: ...
    def observe(self, event: dict) -> Optional[dict]:
        """Returns the record for a finished tool call, else None."""
```
(`agent_pi.py:157-161`)

`observe()` is called once per raw event. It returns `None` for everything
that is not a completed tool call and a record dict for the one event that is.
The record's key **names** are the same across all four drivers, but two of
them carry driver-specific meaning — this is not uniform normalization,
just a uniform shape:

| Key | Meaning |
|---|---|
| `tool` | tool name (`bash`, `read`, `edit`, …) |
| `tool_call_id` | the CLI's own id for the call |
| `args` | the call's arguments, string values clipped to `ARG_VALUE_CHARS` |
| `ok` | `agent_cc`/`agent_pi`/`agent_agy`: `False` only when the CLI reported an error (agy: `state == "ERROR"`, `agent_agy.py:284`). **`agent_opencode`: always `True`** — its tracker hardcodes `"ok": True` (`agent_opencode.py:214`) because opencode's event stream never surfaces a failed-tool-call signal this tracker can read; opencode can never report a failed tool call through this path. |
| `label` | `agent_cc`/`agent_pi`/`agent_agy`: a short human line built from tool + args, e.g. `bash: ls -la src`. **`agent_opencode`: just the bare tool name** (`record["label"] = tool`, `agent_opencode.py:215`) — no argument summary. |
| `result_snippet` | first `RESULT_SNIPPET_CHARS` of the result, if any |
| `started_at` / `ended_at` / `duration_ms` | the call's real span, when the CLI exposes it |

(`agent_pi.py:180-196`, `agent_cc.py:252-268`)

## How each driver pairs start and end

The trackers differ only in *which* raw events open and close a call:

| Driver | Opens on | Closes on | Lines |
|---|---|---|---|
| `agent_pi` | `toolCall` block in `message_end`, or `tool_execution_start` | `tool_execution_end` | 160-196 |
| `agent_cc` | `tool_use` block on an `assistant` message | `tool_result` block on the next `user` message — "Only the result knows whether it worked" | 232-268 |
| `agent_agy` | `step_update` with `step_type == "tool"` and status ACTIVE | the same `step_index` reported `DONE` **or** `ERROR` | 238-297 |
| `agent_opencode` | — | a single `tool_use` event with `state.status == "completed"`; "there's nothing to open and close" | 188-225 |

The three pairing trackers keep `self._open: dict[str, dict]` keyed by call
id, recording the tool, args, and a `time.monotonic()` clock at announce time
so `duration_ms` measures the harness's own wall-clock span
(`agent_cc.py:270-279`, `_announce()`). opencode's tracker has no `__init__`
at all because the CLI already delivers input, output, and timing in one
event.

## Where it is consumed

`agents._event_forwarder` is the only caller. It instantiates
`coder.ToolCallTracker()` for whichever driver is running, calls `observe()`
on every streamed event, and turns each non-`None` record into an
`EventRecord(type="tool_call")` — popping `label` out as the event `name` and
`started_at`/`ended_at` into the row's columns, with the rest of the record
(plus the agent's name) as the payload. (`agents.py:427-447`)

## See also

- [PiRequest and PiResult](PiRequest-and-PiResult.md) — the other two members
  of the shared driver surface (`run(request, …) -> PiResult`).
- [Visualizer](../observability/Visualizer.md) — the UI that lays `tool_call` events on a
  time axis from the columns this tracker fills.
- `.claude/skills/sssf/references/observability.md` — the `tool_call` event
  definition and the `events` table schema the record is written to.
