---
title: SSSF Training Series — Writer's Brief
version: 1.0
updated: 2026-08-25
status: in-progress
---

# Writer's brief — SSSF training series

You are writing **one episode script** for a screencast series teaching the
Super Simple Software Factory (SSSF). Read this whole brief, then read the code
you are describing. **Never describe a command you have not read the source of.**

## The repo you are documenting

`/Users/alexei/Projects/training/sssf-play` — a real, working SSSF install with
a real target app. Everything in the series must be demonstrable here.

- `.claude/skills/sssf/` — the skill itself (installer, templates, cookbooks)
- `adws/` — the stamped factory: `adw_*.py` workflows, `adw_modules/` internals
- `adws/adw_sssf_config/sssf.config.yaml` — the agent roster
- `app/pricing.py`, `tests/test_pricing.py` — the target: a cart pricing engine
- `justfile` — the operating surface (`just --list`)
- `adws/adw_data/sssf.db` — SQLite trace of every run that has happened here

## Ground truth you must not contradict

These were established by running the thing, not by reading about it:

- **Two coding agents.** `claude_code` (default) drives headless `claude -p`
  on the logged-in session — no API key. `pi` drives the Pi harness and needs a
  provider key per model. Selectable per agent in the roster.
- **Deterministic code owns the graph.** Agents are bounded nodes. A phase of
  `kind="code"` (tests, git, quality) runs a known command; a phase of
  `kind="agent"` calls a model. "Agent proposes, code disposes."
- **Gates are real.** `quality.py` runs pytest / ruff / mypy. Each was verified
  to fail on its own defect class. A gate that always passes is worse than none.
- **The fix loop.** If the test phase goes red, a `fix_N` phase re-enters the
  **same** agent session with the suite's verbatim output; then it re-tests.
  Real numbers from run `6dbd32b4`: fix cost $0.08 and 24.5s.
- **Permissions.** `writes:` bounds what an agent may change in the repo;
  `protected_files` is off-limits to all. The builder cannot edit its own grader.
- **Real costs measured here.** `just demo` ≈ $0.11. `just sdlc` on a small
  feature ≈ $0.48–$0.76 with a sonnet planner, $1.14 with an opus planner.
  `just quality` is $0.00 (zero agents). ~15.5k tokens of Claude Code base
  prompt are re-read on every internal turn — that is the tax for using
  `claude` as the runner.

## Audience and tone

Episode 1 assumes someone who has used an AI coding assistant and has **never**
orchestrated one. By the last episode they are writing their own ADW. Each
episode assumes only the ones before it.

- Explain *why* before *how*. The reason SSSF exists is that a single "build me
  an app" prompt drifts; every mechanism is a response to a specific failure.
- Show real output. Numbers, costs, exit codes. Never invent terminal output —
  if you need output you have not seen, mark it `[CAST: <what to record>]` and
  the producer will record it.
- No hype. Do not call it magic, revolutionary, or a game-changer. It is a
  Python program that calls a CLI in a loop and checks the result.
- Admit the sharp edges. Cost, the base-prompt tax, placeholder gates, the
  `--force` hazard. A viewer who hits one unwarned will not trust the rest.

## Required output format

Write to the exact path you are given. Start with frontmatter:

```markdown
---
title: "Episode N — <title>"
version: 1.0
updated: 2026-08-25
episode: N
duration_target: "<n> minutes"
prerequisites: [<episode numbers>]
---
```

Then these sections, in order:

1. **Learning objectives** — 3–5 bullets, each a thing the viewer can *do*.
2. **Cold open** (≤45s) — the problem this episode solves, stated concretely.
3. **Script** — a table with columns `Time | Visual | Narration`. Narration is
   the exact words to speak, written for the ear: short sentences, no
   subordinate-clause pileups. Visual says what is on screen, and cites the
   file and line when showing code (`adws/adw_modules/quality.py:138`).
4. **Commands demonstrated** — every command, copy-pasteable, with a one-line
   note on what the viewer should see and whether it costs money.
5. **Recording notes** — `[CAST: ...]` markers listing each terminal recording
   the producer must capture, and what must be visible in each.
6. **Common mistakes** — 2–4 things a learner gets wrong here, and the symptom.
7. **Check for understanding** — 3 questions with answers.

End with a `## Version history` table (`Version | Date | Changes`, newest
first), per the project documentation standard.

## Hard rules

- Read the actual source before describing behaviour. Cite `file:line`.
- Never state a cost, token count, or timing that is not in this brief or that
  you did not read out of `adws/adw_data/sssf.db`.
- If something is genuinely unclear, write the uncertainty into the script as a
  note to the producer rather than guessing.
- Keep to the duration target. A 9-minute script is roughly 1,300 spoken words.
