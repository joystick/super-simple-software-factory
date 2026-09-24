---
title: UsageBreakdown
---

# UsageBreakdown

`UsageBreakdown` is the Pydantic model that holds "Tokens and the dollars they
cost, per component, summed over a call" — the itemized figure behind
`PiResult.usage`, and the source of the `total_tokens` / `total_cost` numbers
the trace and console report for every agent run.
(`.claude/skills/sssf/templates/adws/adw_modules/data_types.py:407-408`)

## Why it exists

A single `tokens` integer cannot reconcile with what a coding agent actually
billed, because input, output, cache reads, and cache writes each carry their
own price. The docstring fixes the shape to pi's own: it "Mirrors pi's `usage`
shape one-for-one so the numbers reconcile with what pi itself reports:
`input` EXCLUDES cache reads, which bill at their own (cheaper) rate — add
them to learn the size of the prompt that was sent."
(`data_types.py:410-412`)

Choosing pi's convention as the canonical one is what lets the other drivers
feed the same model. `agent_cc._pi_shaped_usage()` translates Claude Code's
usage block into that shape, noting that Claude "does NOT include [cache
counters] in `input_tokens`, which is the same convention pi uses — so the
parts add up the same way on both sides" (`agent_cc.py:193-199`); agy maps
its usage "onto the pi shape so `UsageBreakdown` folds it the same"
(`agent_agy.py:371`).

## Fields

Source: `data_types.py:414-428`.

| Field | Type | Meaning |
|---|---|---|
| `input_tokens` | `int` | prompt tokens billed at the input rate — cache reads excluded |
| `output_tokens` | `int` | completion tokens, thinking included |
| `cache_read_tokens` | `int` | prompt tokens served from cache |
| `cache_write_tokens` | `int` | prompt tokens written to cache |
| `reasoning_tokens` | `int` | the thinking **share** of `output_tokens` — see below |
| `total_tokens` | `int` | the CLI's own reported total when it has one, else the sum of the four billable components — see `add_turn()` below; empirically the two agree, but the field is not *defined* as the sum |
| `input_cost` / `output_cost` / `cache_read_cost` / `cache_write_cost` | `float` | dollars per component |
| `total_cost` | `float` | the CLI's own turn total, summed |

`reasoning_tokens` is deliberately **not** a fifth component. The inline
comment records the measurement behind that: "measured across every session
on disk, reasoning is always <= output and the four components above always
sum to totalTokens, so reasoning is the thinking SHARE of output, billed at
the output rate. Report it nested under output, never added to it."
(`data_types.py:418-421`)

## `add_turn()` and `merge()`

Two methods accumulate:

- `add_turn(usage, total_tokens)` folds in one pi `message_end` usage object,
  reading `input`/`output`/`cacheRead`/`cacheWrite`/`reasoning` and the nested
  `cost` dict. `total_tokens` is passed in rather than re-derived because "the
  caller already computes it pi's way (totalTokens, else the sum of the
  parts)". (`data_types.py:430-447`)
- `merge(other)` adds every field of another `UsageBreakdown` — "a phase that
  retries spends more than once". (`data_types.py:449-452`)

The two operate at different levels: a driver calls `add_turn()` per turn
inside one `run()` to build `PiResult.usage`; `agents.execute()` calls
`merge()` per **send** into a phase-level `spent = UsageBreakdown()`, so JSON
retries and gate corrections are all counted (`agents.py:298`, `324`). That
phase total — not the last send's — is what lands on the `agent_end` event as
`tokens=spent.total_tokens` and `payload={"cost": spent.total_cost, "usage":
spent.model_dump(), …}` and on the console's "agent finished" line
(`agents.py:396-405`).

## Reading a zero

Cost components are only as good as the CLI's reporting. Claude Code "does not
itemize cost per component in the CLI stream; the one authoritative number is
the turn total, so it rides on `total` alone rather than being split into
fabricated parts" (`agent_cc.py:211-214`) — so `input_cost` etc. are `0.0`
there while `total_cost` is real. agy reports no dollars at all
(`agent_agy.py:35-38`). A zero in any cost field means "not reported", never
"free". For the operator's-eye walkthrough of these numbers on a real run,
see the training lesson `04-coding-agents-and-cost/lessons/0002-reading-real-cost`
— this page is the type-level reference it points back to.

## See also

- `coding-agent-drivers/PiRequest-and-PiResult.md` — `PiResult.usage` is
  this type; that page explains why `tokens`/`cost` are sums while
  `context_tokens` is a snapshot.
- `observability/Visualizer.md` — where `agent_end`'s `usage` payload is
  rendered.
- `.claude/skills/sssf/references/observability.md` — the `events` table the
  `agent_end` row is written to.
