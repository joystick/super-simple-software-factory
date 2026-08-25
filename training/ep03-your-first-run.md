---
title: "Episode 3 — Your first run"
version: 1.1
updated: 2026-08-25
episode: 3
duration_target: "8 minutes"
prerequisites: [1, 2]
---

# Episode 3 — Your first run

## Learning objectives

- Operate SSSF through the `justfile` and understand what each recipe does
- Run `just quality` to verify the machinery works without spending money
- Run `just demo` to see the two read-only workflows in action
- Interpret the run banner: adw_id, phases, cost, tokens, and database path
- Understand where a run's artifacts land in the filesystem

## Cold open

You have installed SSSF into a working repo. You haven't run anything yet. You want to know: What does the thing actually do? How do you operate it? Is it worth running, or is something broken? This episode answers those questions.

## Script

| Time | Visual | Narration |
|------|--------|-----------|
| 0:00 | Terminal at repo root | You operate SSSF through recipes — small, composable just scripts that invoke Python workflows. They are all in the justfile, the single source of truth for what your factory can do. |
| 0:10 | Run `just --list` | Let's start here. Type `just --list` to see every recipe. |
| 0:15 | `just --list` output | The justfile groups them into three categories. The first group, "first run", is two read-only recipes that prove everything works end to end. Then, "run a workflow" — seven recipes for different phases or combinations of phases. Finally, "watch it" — commands to inspect a running run or fetch results. |
| 0:35 | Show the justfile, lines 43-65 (adws/adw_quality.py:1-45) | Before we spend any money, let's verify the machinery works. That's what `just quality` does. Quality is read-only — it runs pytest, ruff, and mypy, and reports pass or fail. Zero agents. Zero cost. Free. |
| 0:45 | Show adws/adw_quality.py:5-11 and lines 19-20 | Quality is a two-phase workflow. Phase one captures the request — your reason for checking. Phase two runs the three quality blocks: tests, linter, typecheck. It says REQUIRED_AGENTS equals an empty list — no agents to pay for. |
| 1:00 | Show adws/adw_quality.py:31-36 | The quality phase collects all three checks — how many passed, how many total, and where the output logs landed. |
| 1:10 | Terminal, type `just quality "proof of concept"` | Let's run it. |
| 1:15 | [CAST: Run just quality] | The output fills the terminal in real time. First, the "request" phase captures your reason. Then the "quality" phase runs each check — tests, linter, typecheck — and logs the exit code and timing. |
| 1:40 | [CAST: Final banner] | When it is done, you see a banner with the run summary. Here is what each line means. Status shows pass or fail. Phases tells you how many of the workflow's phases succeeded. Tokens is zero because no agent ran. Cost is zero dollars. The **adw_id** is a session ID — a unique hex string that identifies this exact run forever. The database is where the trace lives. Next tells you the command to inspect the run in detail. |
| 2:00 | Show adws/adw_quality.py:16-18 (engineer, kind="engineer") and lines 27-29 | Now, what is an adw_id? When you run a workflow, the first thing the factory does is create a session in the database and mint an adw_id. Every phase, every event, every artifact from that run is tagged with that ID. That ID is how you reference the run forever. |
| 2:20 | Terminal, show `just sessions` | You can list the last 10 runs with `just sessions`. Each row is an adw_id, its status, the request, token count, and cost. |
| 2:30 | [CAST: Session list output] | Real runs from this factory. Here is one with zero cost — a quality run. Here is one with 0.48 dollars — a planner plus builder plus test cycle on a feature. The database keeps every run. |
| 2:45 | Terminal, type `just demo` | Now let's run `just demo` to see two read-only agents working end to end. This costs about a dime total and takes about a minute. Both workflows are read-only. They prove the agent harness works before you touch anything. |
| 2:55 | [CAST: Run just demo, part 1] | First, adw_prompt — one agent, one prompt. The banner appears. The engine sends a request to the agent. The agent replies with an envelope — structured output. The factory parses it, checks gates, records the envelope in the database. |
| 3:30 | [CAST: Run just demo, part 2] | Second, adw_scout — the read-only recon agent. Same structure: request, agent, envelope, gates. But scout is specialized for reading and finding — change nothing. |
| 4:00 | [CAST: Final banner from demo] | When both are done, the cost is roughly 11 cents. The tokens are split between the two agents. The database now has two new envelopes — the agent outputs captured in full. |
| 4:15 | Terminal, type `just phases <adw_id>` | You can inspect a run's phases in sequence. Each row shows the phase name, whether it is engineer, code, or agent, who ran it, and its status. If a phase fails, the attempt and retry counts tell you how many times the factory tried to fix it. |
| 4:30 | [CAST: Phase list output] | Here is a real run, `6dbd32b4`. Seven phases: request, plan, build, test_1, fix_1, test_2, commit — one fix phase, because the suite only needed one correction before it went green. Each phase has a start time. |
| 4:50 | Show `/Users/alexei/Projects/training/sssf-play/adws/adw_data/sessions/` | Artifacts land here. Each run gets its own directory named after the adw_id. |
| 5:00 | Show directory structure with `ls` | Inside, events.jsonl is the structured event log. context_handoff/ holds handoff data between phases. For agent runs, there are agent directories — one for each agent that ran. |
| 5:15 | Show /adws/adw_data/sessions/<adw_id>/context_handoff/ | The context_handoff directory is where the factory stashes structured data for the next phase to consume. Quality runs put test/lint/typecheck logs here. Agent runs put the parsed envelope and the phase's decision log here. |
| 5:40 | Terminal, show the database schema | All of this is queryable. The database has tables for sessions, phases, events, envelopes (agent output), and processes. Every run is a row. Every phase is a row. Every agent call is an envelope. |
| 6:00 | Show adws/adw_prompt.py:5-10 | Let's look at the simplest agent workflow — adw_prompt. It has two phases. Request captures the ask. Prompt sends it straight to an agent and parses the envelope. |
| 6:20 | Show adws/adw_scout.py:5-10 | And here is adw_scout. Same structure, but the scout agent has a gate: artifacts_exist. It checks that the agent actually returned an artifacts list. |
| 6:40 | Show adws/adw_quality.py:5-11 | Finally, quality again. Two phases. No agent. Just deterministic checks. This is the template for any workflow that is too simple or too risky for an agent. |
| 7:00 | Terminal | So: justfile gives you the recipes. Quality is free and proves it works. Demo is cheap and real. Every run gets an adw_id. Phases are queryable. Artifacts live in the session directory. The database is your audit trail. |
| 7:15 | Show justfile lines 51-65 | From here, you have seven more recipes to explore. Plan only. Plan plus build. Build plus test. Full SDLC. Each is a chain of phases. Read the ADW source if you want to know the exact sequence. |
| 7:30 | Terminal | Next episode: we read the quality suite itself and see how the gates work. You will understand why quality fails, what artifacts matter, and how the fix loop re-enters the same agent session when a test goes red. |
| 7:45 | | Fin. |

## Commands demonstrated

```bash
# List every recipe
just --list

# Run quality checks (free — zero cost, zero agents)
just quality "proof of concept"

# Run two demo agents (about $0.11, ~65 seconds)
just demo

# List the last 10 runs
just sessions

# Inspect a run's phases in order
just phases 592290a5

# Watch live events from a run
just tail 592290a5

# See what processes are alive on a run
just procs 592290a5

# Open the trace UI (needs bun — not installed on this machine, so this will not run here)
just obs
```

### What to watch for

- `just quality` should finish in a few seconds — a real run in this repo took about 2 seconds end to end. It reads pytest, ruff, mypy output and always reports exactly what each tool said. Pytest tells you which test failed. Ruff tells you linting errors. Mypy tells you type errors.
- `just demo` shows two banners. The first is the adw_prompt agent run. The second is the adw_scout agent run. Each banner shows an adw_id and a cost.
- The cost in the banner is real — what you were charged by the model provider. Tokens are the input+output tokens the agent consumed.
- The adw_id is always an 8-digit hex string. You use it to look up the run later.

## Recording notes

- [CAST: Run just quality] — Show the full run of `just quality "proof of concept"`. Should take a few seconds — a real run here finished in about 2 seconds. Capture the progress lines for each phase, and the final banner.
- [CAST: Final banner] — A clean screenshot of just the final banner with status, phases, tokens, cost, adw_id, db, and next.
- [CAST: Session list output] — Output of `just sessions`. Should show at least 5 past runs with varying costs (some zero, some $0.48+, some $0.11).
- [CAST: Run just demo, part 1] — Run `just demo`. Capture up to the point where adw_prompt finishes. Should show the "1/2" message, the progress lines, and the first banner.
- [CAST: Run just demo, part 2] — Continue, capturing the "2/2" message and adw_scout finishing.
- [CAST: Final banner from demo] — The final summary banner after both agents finish. Should show higher token count and ~$0.11 cost split.
- [CAST: Phase list output] — Run `just phases 6dbd32b4` or another multi-phase run. Show the full sequence with seq, name, kind, owner, status.

## Common mistakes

- **Thinking `just quality` costs money.** It doesn't. Quality is pure code — pytest, ruff, mypy. Run it as many times as you want for free.
- **Confusing adw_id with a build number or git commit.** The adw_id is a session ID for a single run, not a version. If you run the same request twice, you get two different adw_ids. They are queryable but not human-memorable — paste them into `just phases <id>` or the UI.
- **Missing the "next" hint in the banner.** Every run tells you exactly what to run next to inspect it. It says `just phases <adw_id>`. Use that. It saves you from copying the ID by hand.
- **Running `just demo` in the background or piping it.** The demo is interactive and shows real-time progress. Run it in the foreground so you see the banners and the final summary.

## Check for understanding

1. **Q: Can you run `just quality` as many times as you want?**
   A: Yes. Quality is zero agents, zero cost. Run it to verify the machinery works before spending money on agents.

2. **Q: What is an adw_id and how do you use it?**
   A: An adw_id is an 8-digit hex session ID minted when you run a workflow. Every phase, event, and artifact is tagged with it. You use it to look up the run in the database with `just phases <adw_id>`, `just tail <adw_id>`, or the UI.

3. **Q: Where do a run's artifacts land in the filesystem, and what are the main subdirectories?**
   A: `adws/adw_data/sessions/<adw_id>/`. It contains events.jsonl (the event log), context_handoff/ (handoff data between phases), and agent directories for each agent that ran.

## Version history

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2026-08-25 | Fact-check: run `6dbd32b4` has one fix phase (`fix_1`), not three — corrected the phase-list description. Noted `just obs` needs `bun`, which is not installed on this machine, so it cannot be demonstrated live here. Corrected the "run a workflow" recipe count from eight to seven (verified against `just --list`). Softened the `just quality` timing claim from "~10-15 seconds" to match a real measured run (~2 seconds), matching Episode 5's captured 2.9s figure instead of contradicting it. |
| 1.0 | 2026-08-25 | Initial episode. Covers justfile, quality, demo, run banners, adw_id, artifact filesystem structure, and database queries. |
