---
title: "Head-to-head: agy vs claude as an SSSF coding agent"
version: 1.0
updated: 2026-08-27
status: active
---

# agy vs claude — one task, two runners

Both runs used the **same baseline commit** (`b82f3a1`), the **same prompt**, the same
workflow (`just sdlc` → `adw_plan_build_test`), and the same verified gates. The only
variable was `coding_agent` and the model behind it.

**The task**

> Add an `itemCount` property to Receipt: the total number of units across all lines,
> which is the sum of every line item quantity, and 0 for an empty cart. Add tests
> covering an empty cart, a single line, and one SKU split across two separate lines.
> Do not modify or delete any existing test.

## Result

| | **agy** / gemini-3.7-flash-medium | **claude** / claude-sonnet-4-6 |
|---|---|---|
| phases | 5/5 ✓ | 5/5 ✓ |
| wall clock | **2m 02s** | 2m 45s |
| plan phase | **53.4s** | 104.7s |
| build phase | 62.1s | **57.8s** |
| tokens | **211,630** | 470,855 |
| cost reported | **none — see below** | **$0.5104** |
| gates after | test/lint/check all PASS, 77 tests | test/lint/check all PASS, 77 tests |
| existing tests deleted | 0 | 0 |

**agy was 26% faster and used 55% fewer tokens.** Its planner in particular was half the
time of claude's.

## The implementation was byte-identical

Both produced exactly the same four lines:

```ts
readonly itemCount: number;
const itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);

  itemCount,
```

On a task of this size there is nothing to choose between them on the code itself.

## The tests differed, and claude's were better placed

Both wrote three tests covering the three requested cases. Both suites, put through the
same mutation (`itemCount` → `cart.items.length`), caught it: **75 passed, 2 failed** in
each. So both are real tests, not decoration.

The difference is judgement, not correctness:

| | agy | claude |
|---|---|---|
| file | appended to `tests/price-cart.test.ts` | **new `tests/receipt-item-count.test.ts`** |
| header | a `// ── item count ──` section rule | a docstring stating what the file specifies |
| fixtures | reused the file's existing `widget()` / `cartOf()` helpers | constructed `new LineItem(...)` explicitly |

agy's is more economical and fits the host file's idiom. claude's is more discoverable —
a reader looking for the itemCount spec finds a file named after it — at the cost of not
reusing helpers that already existed.

Reasonable people differ here. Neither is wrong.

## The honest caveats

- **One task, one sample each.** This is a small, well-specified feature with strong local
  conventions to imitate. It does not predict behaviour on ambiguous or architectural work.
- **Cost is not comparable.** `agy` reports tokens but never dollars, so the adapter leaves
  `cost` at 0.00 rather than inventing a figure. The `$0.00` in agy's trace means *unknown*,
  not *free* — those 211,630 tokens were billed to a Google Workspace account. Comparing
  price properly needs a price table nobody here is maintaining.
- **The `thinking` field is inert under agy.** Effort is encoded in the model id
  (`-high` / `-medium` / `-low`), so the roster's `thinking` is ignored. Choosing
  `agy/gemini-3.7-flash-high` is how you ask for more.

## What this cost to find out

Three defects in my own adapter, each surfaced by running rather than reading:

1. `agy -p "text"` silently mis-parses — the prompt must be `-p=text`.
2. **`--add-dir` is required.** Without it the file tools are not rooted at cwd. A probe
   for a file sitting *in* cwd instead searched `~/Downloads`, then ran
   `find /Users/alexei -name note.txt`, burned 120k tokens over 41 tool calls, and timed
   out having written nothing. With `--add-dir`: one turn, 2.3 seconds.
3. **`--effort` conflicts with the model id.** Caught on the first real run:
   `--model gemini-3.7-flash-medium conflicts with --effort=high`.

Also worth noting: `agy` exits **0** when its result payload reports `ERROR` — a timeout
comes back as a successful process with a failed body. The adapter raises on that
explicitly, or the factory would treat a stalled turn as a completed one.

## Which meter is agy actually on?

Worth pinning down, because an AI Studio console reading **"Free tier"** looks like it
governs this and does not.

Verified on the machine:

| | Finding |
|---|---|
| credential | OAuth `refresh_token` in `~/.gemini/oauth_creds.json` — **no API key**, none in the environment either |
| endpoint | `daily-cloudcode-pa.googleapis.com`, with 270 log mentions of `CodeAssist` |
| not | `generativelanguage.googleapis.com` (AI Studio) or Vertex |
| throttling during these runs | **none** — zero real 429s, zero `RESOURCE_EXHAUSTED` |

So agy runs on the **Gemini Code Assist** entitlement attached to the Workspace identity,
not on a project-bound API key. Published Gemini API rate tables and per-token prices
describe a meter these runs never touched, which is also why the CLI reports tokens and
never dollars.

The backend does know the real figure — agy calls `retrieveUserQuotaSummary` — but reading
it authenticated was not attempted, so **the actual quota remains unknown** rather than
guessed.

> A caution learned the hard way while checking this: grepping logs for `429` matches
> microsecond timestamps like `15:36:53.429825`. The first pass appeared to show 21
> throttling events; there were none.

## Recommendation

`agy` is a viable SSSF coding agent, and on work of this shape it is faster and leaner.
Two things should decide whether you adopt it:

- **The missing system prompt.** SSSF agents *are* their system prompt. agy has no
  `--system-prompt`, so the adapter folds it into every user turn behind a delimiter.
  That is advice inside the conversation rather than a separate channel — weaker, and
  re-sent every turn. On this task it did not matter. On a roster where the system prompt
  carries a strict output contract, it might.
- **The missing cost data.** If you care about per-run spend in the trace, claude reports
  it and agy does not.

The interesting option is neither/both: `coding_agent` is per-agent, so a roster can put
cheap read-only agents on agy and keep planner or builder on claude.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-27 | First head-to-head. One task, same baseline, both green. |
