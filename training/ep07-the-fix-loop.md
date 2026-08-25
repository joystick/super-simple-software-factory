---
title: "Episode 7 — The fix loop: when the gate goes red"
version: 1.0
updated: 2026-08-25
episode: 7
duration_target: "9 minutes"
prerequisites: [1, 2, 3, 4, 5, 6]
---

## Learning objectives

- Explain how a failing command becomes an agent input, with no parser guessing what it means.
- Trace the fix loop in `adws/adw_plan_build_test.py`: `test_N` → `fix_N` → `test_N+1`, bounded by `MAX_FIX_LOOPS`.
- Explain why `fix_N` re-enters the same agent session instead of starting a fresh one, and why that makes repair cheap.
- Tell apart three different retry mechanisms in this codebase — gate corrections, JSON parse retries, and the fix loop — and say which module owns each.
- Read a real run (`6dbd32b4`) end to end: what failed, what it cost to fix, and what got left behind.

## Cold open (≤45s)

**Narration:** Every demo so far ended the same way: the agent finishes, the tests pass, you commit. That's the easy case. Anyone can run an agent once and get lucky. The real question is what happens the first time it isn't lucky — the suite comes back red. Does the factory panic? Does it loop forever? Does it quietly delete the test that caught it? Today we open one real run where the builder shipped a bug, the suite caught it, and we watch exactly what the factory did next — no guessing, straight from the database and the git log.

## Script

| Time | Visual | Narration |
|---|---|---|
| 0:00–0:45 | Cold open, terminal idle | (as above) |
| 0:45–1:30 | Editor: `adws/adw_plan_build_test.py:51-67` | This is the whole loop. A `for` loop from 1 to `MAX_FIX_LOOPS`. Each pass runs `test_N` — that's code, not an agent, calling `quality.run_tests`. If it passes, we break out. If it fails, we run `fix_N` — an agent phase, owner `builder` — and loop back to test again. |
| 1:30–2:15 | Editor: `adws/adw_modules/quality.py:138-146,173-186` | The test block is one line: `uv run pytest -q`. `run_tests` wraps it in a `QualityResult`. Look at line 182 — on failure it builds one failure string: the check name, the exact command, and the exit code, plus the output tail. Nothing here reads the pytest output and decides what broke. It just carries it. |
| 2:15–3:15 | Editor: `adws/adw_modules/quality.py:43-46,131,189-207` | `TAIL_CHARS = 4000` — line 46. Every quality check keeps the last 4000 characters of stdout plus stderr, line 131. That's `output_tail`. Then `as_envelope`, line 189, wraps a `QualityResult` into a `VerifyOutput` — the same typed envelope an agent hands another agent. Read the docstring: "a failing lint or test run flows back into the builder through exactly the same door an agent's report would." The builder never knows it's talking to a subprocess instead of a teammate. |
| 3:15–4:00 | Editor: `adw_plan_build_test.py:62-67` | Here's the handoff: `fix_N`'s `AgentCall` sets `previous=quality.as_envelope(test, "tests")`. The builder's next prompt includes that envelope verbatim — command, exit code, output tail. No summary written by a parser that guessed what the traceback meant. The builder reads the real pytest output the same way you would. |
| 4:00–5:00 | Editor: `adw_modules/agents.py:112,124-126,247-251` | Now the part beginners miss: `fix_N`'s owner is `builder` — the same agent as the `build` phase. Line 247, `_agent_session_id`: if this agent already has an entry in `run.agent_map` with a matching model, it returns the *same* session id — "rejoin the existing context window." The fix phase calls `--resume` under the hood, into the session the builder already had. It still remembers the plan, the file layout, why it wrote the code the way it did. That's why a fix is cheap: it isn't relearning the codebase, it's finishing a thought. |
| 5:00–5:30 | Editor: `adw_plan_build_test.py:24,76-77` | The loop is bounded: `MAX_FIX_LOOPS = 3`. Three chances, not infinity. If test never passes, the `for` loop exhausts, `test` stays failing, the run reports `accepted=False` with reason "the suite still failed after 3 fix attempt(s)." Nothing gets committed — look at line 70: commit only runs `if test is not None and test.passed`. A run that never goes green just... stops, uncommitted. |
| 5:30–6:30 | Editor: `adw_modules/agents.py:164-192,291-312` | Do not confuse three different retries. First, gate corrections — lines 166-192 — when a gate like `artifacts_exist` finds a violation, it re-sends a correction into the *same* send loop, bounded by `phase.params.retries`. Second, JSON parse retries — `_parse_with_retries`, line 291, bounded by `JSON_FIX_ATTEMPTS = 2` — when the agent's response isn't valid JSON for its output type, it gets told to re-emit. Third, the fix loop we've been tracing — a whole new *phase*, re-testing the whole suite, bounded by `MAX_FIX_LOOPS`. Gate corrections fix a malformed report. JSON retries fix a malformed envelope. The fix loop fixes broken code. Different failure, different mechanism, different bound. |
| 6:30–8:15 | Terminal: sqlite3 queries against `adws/adw_data/sssf.db`, then `git show 4745bbf` | [CAST: run the queries below against run `6dbd32b4` and show `git show 4745bbf` scrolling]. Seven phases, all `success`: request, plan, build, test_1, fix_1, test_2, commit. Total cost for the whole run: $0.4798. `test_1` failed — exit 1. `fix_1` ran for 24.5 seconds and cost $0.08. `test_2` passed. It landed as commit `4745bbf`. |
| 8:15–8:50 | Editor: `git show 4745bbf` diff of `app/pricing.py` | The planted bug was one word: `_percent_of` used `ROUND_DOWN` where the docstring says half cents round up. The builder's fix message: "Fix `_percent_of` to round half-up as documented, not truncate." It changed the rounding mode in the function — it did not touch the two tests that caught it. It had unrestricted writes in this repo; deleting those two assertions was the cheaper path to a green suite, and it did not take it. That's the result worth showing: cheap and gameable are not the same axis. |
| 8:50–9:00 | Editor: `git show 51f70e2` commit message, lines about `ROUND_DOWN` leftover | One honest loose end: the fix corrected the *usage* but left the now-unused `ROUND_DOWN` import sitting in the file. Nothing caught it that day — the lint gate was still a placeholder. Weeks later, wiring lint to real `ruff check` caught it immediately. Gates layer: a fast, narrow gate misses what a later, slower gate catches. That's not a flaw to hide — it's the reason you run more than one. |

## Commands demonstrated

```bash
# Read a completed run's phases — no cost, read-only
sqlite3 adws/adw_data/sssf.db \
  "select seq,name,kind,owner,status,started_at,ended_at from phases where adw_id='6dbd32b4' order by seq;"
# Shows all 7 phases of run 6dbd32b4 in order, including fix_1. Free — sqlite read.
```

```bash
# Read the run's total cost and token spend
sqlite3 adws/adw_data/sssf.db \
  "select adw_id,status,total_tokens,total_cost from sessions where adw_id='6dbd32b4';"
# Shows total_cost = 0.479819. Free — sqlite read.
```

```bash
# See exactly what the fix changed and what it didn't touch
git show 4745bbf
# Shows the ROUND_DOWN -> ROUND_HALF_UP diff; no test assertions were deleted. Free — git read.
```

```bash
# See the later gate catch the leftover import
git show 51f70e2 -- app/pricing.py
# Shows ROUND_DOWN import removed once lint was wired to real ruff. Free — git read.
```

```bash
# Run the loop yourself on a fresh bug (costs money — real agent calls)
just sdlc "your feature request"
# Runs plan -> build -> test -> (fix loop if needed) -> commit. ~$0.48-$0.76 with a sonnet planner.
```

## Recording notes

- [CAST: terminal, full width, run the four sqlite3/git commands above in sequence with a beat between each so the numbers are readable on screen]
- [CAST: editor, split view — `adw_plan_build_test.py:51-77` on the left, `adw_modules/quality.py:189-207` on the right, scrolled to `as_envelope`]
- [CAST: editor, `git show 4745bbf` diff view of `app/pricing.py`, scrolled slowly so both the `ROUND_DOWN` → `ROUND_HALF_UP` line and the untouched test file are visible]
- [CAST: terminal, `git log --oneline -- app/pricing.py` showing the three commits in order: `16917b8` (planted bug) → `4745bbf` (fix) → `51f70e2` (lint catches the leftover import) — this sequence is the spine of the episode, worth a full-screen beat]

## Common mistakes

- **Assuming the fix phase is a fresh agent call.** It isn't — it's `--resume` into the builder's own session (`agents.py:247-251`). If you architect your own ADW with a *different* agent name for the fix step, you lose this and pay full re-discovery cost every time.
- **Confusing the fix loop's bound with the gate retry bound.** `MAX_FIX_LOOPS` (3, in `adw_plan_build_test.py`), `phase.params.retries` (per-phase, gate corrections), and `JSON_FIX_ATTEMPTS` (2, fixed in `agents.py`) are three separate counters. Raising one to "make retries more generous" does nothing to the other two.
- **Expecting a bad run to leave a broken commit.** It won't — look at the guard on line 70 of `adw_plan_build_test.py`. An exhausted fix loop leaves the working tree dirty and uncommitted, not committed-and-broken. If you see a red run and a clean git log, that's correct behavior, not a bug.
- **Trusting a green run before the gates are wired.** `6dbd32b4` ran with a placeholder lint gate — see the sidebar in the script. A green run only proves what the wired gates check. An unwired gate that "passes" is not evidence of anything.

## Check for understanding

1. **Q: What exactly does the builder see when `test_1` fails — a summary of the error, or something else?**
   A: The verbatim command, its exit code, and the last `TAIL_CHARS` (4000) characters of combined stdout/stderr, wrapped in a `VerifyOutput` envelope by `as_envelope` (`quality.py:189`). No summarizing parser sits in between.

2. **Q: Why does `fix_1` cost only $0.08 and take 24.5 seconds, when the original `build` phase took over a minute?**
   A: `fix_1` re-enters the builder's existing agent session via the same `session_id` (`agents.py:247-251`, "rejoin the existing context window") instead of starting fresh. It's finishing a repair with context already loaded, not rediscovering the plan and the codebase from zero.

3. **Q: A gate keeps rejecting the planner's output for a malformed field. Is that the fix loop?**
   A: No. That's a gate correction — a bounded resend inside the same phase, governed by `phase.params.retries` (`agents.py:166-192`). The fix loop (`fix_N`/`test_N` in `adw_plan_build_test.py`) is a separate mechanism that only fires after the *test* phase fails, and it's a whole new phase, not a resend within one.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-25 | Initial script, grounded in run `6dbd32b4` and commits `16917b8`/`4745bbf`/`51f70e2`. |
