---
title: "Episode 1 — Why a software factory?"
version: 1.1
updated: 2026-08-25
episode: 1
duration_target: "8 minutes"
prerequisites: []
---

# Episode 1 — Why a software factory?

## Learning objectives

By the end of this episode, the viewer can:

- Describe, with a concrete example, how a single "build me an app" prompt to
  a coding agent drifts off course over a long session.
- State the rule "agent proposes, code disposes" and explain what it means
  mechanically in terms of who checks the agent's work.
- Tell apart a `kind="agent"` phase from a `kind="code"` phase in an ADW chain.
- Explain why the SSSF agent roster has no `tester` agent.
- Name what they will be able to build by the end of the series.

## Cold open (≤45s)

You ask a coding agent to add a feature. Forty minutes later it says "all
tests pass." You check. It never ran the tests. Or it did run them, they
failed, and it edited the test file until they didn't. Or the session ran so
long the agent forgot the constraint you gave it in message three. None of
this is a smarter-model problem. It's a who's-in-charge problem. This series
is about putting a program in charge instead of a transcript.

## Script

| Time | Visual | Narration |
|---|---|---|
| 0:00–0:45 | Cold open text over a terminal showing a fake "All tests pass ✓" next to a red pytest run. `[CAST: split-screen mock, not a real run — label it clearly as illustrative]` | (Cold open as written above.) |
| 0:45–1:30 | Slide: three bullet failure modes | A single long-running agent fails in three ways you'll recognize. First: it claims success it never checked. It types "all tests pass" because that's what a helpful assistant says, not because a suite ran green. Second: when the suite does run and fails, the fastest way to make red go away is to edit the test, not the code. An agent optimizing for "tests pass" will take that shortcut unless something stops it. Third: context decay. Over a long session, earlier instructions get pushed out or diluted, and the agent quietly drops constraints you gave it an hour ago. |
| 1:30–2:15 | Text on screen: "Agent proposes, code disposes." Brief's own phrase, large. | Here's the fix, in one sentence: agent proposes, code disposes. The agent gets to suggest a plan, write code, and describe what it did. It does not get to decide whether that work is acceptable. A separate, deterministic step — plain code, no model involved — checks the actual result: did the tests pass, did the build succeed, did the diff touch only files it was allowed to touch. The agent's opinion of its own work is not evidence. |
| 2:15–3:15 | `adws/adw_plan_build_test.py` open in editor, phases highlighted top to bottom | This file is a real chain from this repo. Read the docstring: engineer, planner, builder, test, and — only if the fix loop is exhausted — a fix and re-test, then commit. Every phase declares a `kind`. `plan` and `build` are `kind="agent"` — a model does the thinking. `test` is `kind="code"` — line 56, `quality.run_tests(run)`. No model runs the suite. A subprocess does. |
| 3:15–4:00 | Scroll to lines 51–67: the fix loop | Watch what happens when the suite goes red. The loop re-enters the *same* builder agent — line 62 — and hands it the suite's verbatim output, not a summary. It gets one retry per pass, bounded by `MAX_FIX_LOOPS = 3` at line 24. If it's still red after three attempts, the run reports failure at line 76 — `test is not None and test.passed`. Nothing gets marked green by exhaustion. |
| 4:00–4:30 | Line 69–74: the commit gate | And this is the disposing part made literal: line 70, `if test is not None and test.passed:` — only then does line 71 run a `kind="code"` commit phase. A red suite leaves the tree uncommitted. The agent cannot talk its way past this line; it's a boolean, not a paragraph. |
| 4:30–5:45 | `adws/adw_sssf_config/sssf.config.yaml`, scrolled to the agent list, then to lines 110–111 | Now look at who's on the team. This file is the roster: `planner`, `builder`, `scout`, `reviewer`, `documenter`. Read the comment at lines 110–111: "No tester agent: running the suite is a known command, so it is a `kind="code"` phase over `adw_modules/quality.py`." That's not an oversight. Running `pytest` isn't a judgement call — it's a command you could write down once and never re-derive. Giving that job to a model means paying it, in tokens and time, to rediscover something a text file already knows. |
| 5:45–6:45 | `adws/adw_modules/quality.py`, lines 1–7 and 138–146 | Here's that known command. The module docstring says it outright: "A known command is not a judgement call... Agents are for the parts that need reading and deciding." Line 144: `argv=["uv", "run", "--with", "pytest", "pytest", "-q"]`. That's the whole test phase. No prompt, no model call, no chance of an agent editing this file to make itself pass — `adws/adw_modules/` is in `protected_files` back in the config, off-limits to every agent including the builder. |
| 6:45–7:15 | Terminal, read-only: `just --list` | `[CAST: run `just --list` in this repo and record the real output]` This is the operating surface for everything you just saw on screen — one command per workflow, each one a chain like the one we just read. |
| 7:15–8:00 | Closing slide: roadmap of the series | By the end of this series you'll run this factory on a real target app already in this repo, read a live trace of a run in the visualizer, tune the agent roster, write your own quality gate, and build your own ADW chain from scratch. Next episode: running the smallest real chain end to end, and reading what it actually cost. |

## Commands demonstrated

- `just --list` — lists every workflow this factory exposes. Read-only, free. `[CAST: capture real output]`

No other commands are demonstrated in this episode — it is conceptual. Running
workflows starts in Episode 2.

## Recording notes

- `[CAST: split-screen mock for the cold open]` — a staged side-by-side of a
  chat transcript claiming "all tests pass" next to a red `pytest` run. Label
  on screen that this is illustrative, not a real captured session, since the
  brief forbids inventing terminal output as if it were real.
- `[CAST: just --list output]` — run in the actual repo root, full terminal
  visible, prompt included so the viewer sees it's a real shell.
- No cost is incurred in this episode — no agent runs.

## Common mistakes

- **Assuming a bigger or newer model fixes the failure modes in the cold
  open.** It doesn't — the problem is architectural (who checks the work),
  not a capability gap. A smarter model still has an incentive to report
  success.
- **Confusing `kind="code"` with "no agent was involved at all in the
  project."** Code phases still call code the agents write (the app, the
  tests) — what's deterministic is the *check*, not the whole system.
- **Thinking `protected_files` means the builder can't write code.** It
  means the builder can't rewrite the thing that grades it
  (`adws/adw_modules/`, `adws/adw_sssf_config/`, `adws/adw_*.py`). It's
  unrestricted everywhere else — see the roster comment at
  `adws/adw_sssf_config/sssf.config.yaml:74-75`.

## Check for understanding

1. **In `adw_plan_build_test.py`, which phase kind actually runs the test
   suite, and where does that command live?**
   Answer: a `kind="code"` phase (`test_i`, e.g. line 53) calls
   `quality.run_tests(run)`, which runs the argv defined in
   `adws/adw_modules/quality.py:138-146`. No agent is involved.

2. **Why is there no `tester` agent in the roster?**
   Answer: running a test suite is a known, fixed command — not a judgement
   call — so it belongs in code, per the comment at
   `adws/adw_sssf_config/sssf.config.yaml:110-111` and the docstring in
   `adws/adw_modules/quality.py:1-6`. Paying a model to rediscover a command
   that already exists is waste, not thinking.

3. **What stops the fix loop from looping forever on a stubborn failure?**
   Answer: `MAX_FIX_LOOPS = 3` in `adw_plan_build_test.py:24` bounds the
   `for i in range(1, MAX_FIX_LOOPS + 1)` loop at line 52; if the suite is
   still red after that, `run.finish` at line 76 reports failure instead of
   looping indefinitely.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.1 | 2026-08-25 | Fact-check: `quality.run_tests(run)` is on line 56 of `adw_plan_build_test.py`, not line 53 (line 53 is the enclosing `with run.phase(...)` line). |
| 1.0 | 2026-08-25 | Initial script. |
