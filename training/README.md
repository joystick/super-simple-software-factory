---
title: SSSF Training Series — index and producer notes
version: 1.0
updated: 2026-08-25
status: draft
---

# SSSF Training Series

Ten screencast scripts taking someone from "I have used an AI coding assistant"
to "I can write my own ADW". Each episode assumes the ones before it and nothing
else.

| # | Episode | Target | Prereqs |
|---|---|---|---|
| 1 | [Why a software factory?](ep01-why-a-software-factory.md) | 8 min | — |
| 2 | [Installing the factory](ep02-installing-the-factory.md) | 7 min | 1 |
| 3 | [Your first run](ep03-your-first-run.md) | 8 min | 1–2 |
| 4 | [The roster: configuring your agents](ep04-the-roster.md) | 10 min | 1–3 |
| 5 | [Gates: making the factory actually check things](ep05-gates.md) | 10 min | 1–4 |
| 6 | [The SDLC chain: plan, build, test, commit](ep06-the-sdlc-chain.md) | 11 min | 1–5 |
| 7 | [The fix loop: when the gate goes red](ep07-the-fix-loop.md) | 9 min | 1–6 |
| 8 | [Observability: reading what happened](ep08-observability.md) | 8 min | 1–3 |
| 9 | [Coding agents, cost, and control](ep09-coding-agents-and-cost.md) | 10 min | 1–4 |
| 10 | [Writing your own ADW](ep10-writing-your-own-adw.md) | 12 min | all |

[`BRIEF.md`](BRIEF.md) is the writer's brief: the ground truth, the required
script format, and the rule that no terminal output may be invented.

## READ THIS BEFORE RECORDING — where the numbers come from

**These scripts were authored against a companion playground repository, not
against this one.** That repo is a real SSSF install with a real target
application (a cart pricing engine), a wired test/lint/typecheck gate, and a
`sssf.db` containing a dozen real runs.

Everything concrete in the scripts comes from there:

- run ids such as `991c1339`, `6dbd32b4`, `b16c5c29`, `9759e4ab`
- commit shas such as `4745bbf`, `106712c`, `16917b8`, `2f49eb0`
- costs, token counts and timings queried out of that `sssf.db`
- source citations of the form `app/pricing.py:177` or
  `adws/adw_modules/quality.py:138`

**None of those resolve in this repository.** This repo is the skill itself —
there is no `adws/`, no `app/`, no database, and a different commit history.
The scripts are still correct about *how SSSF works*; they are simply narrated
over a worked example that lives elsewhere.

To record them faithfully you need a playground of your own:

```bash
mkdir sssf-play && cd sssf-play && git init
uv run /path/to/this/repo/.claude/skills/sssf/scripts/install.py
# then give it something to build, wire the gates, and make some runs
```

Your ids, shas and costs will differ. **Re-derive them; do not read the ones in
these scripts aloud as if they were yours.** The teaching points survive the
substitution — the numbers are illustrations, not constants.

## Casts

`casts/*.cast` are [asciinema](https://asciinema.org) recordings of real
commands, captured on the playground repo. Play one with:

```bash
asciinema play casts/01-just-list.cast
```

| Cast | Shows | Cost to re-record |
|---|---|---|
| `01-just-list.cast` | the operating surface | free |
| `02-install.cast` | a fresh install into an empty repo | free |
| `03-install-guard.cast` | `--force` preserving engineer-owned files | free |
| `04-sessions.cast` | the last runs | free |
| `05-phases.cast` | phase status for one run | free |
| `06-trace-queries.cast` | reading cost and tokens out of the trace | free |
| `07-gate-mutation.cast` | each gate failing on its own defect class | free |
| `08-quality-gate.cast` | `just quality` — every gate, zero agents | free |

`casts/demo-gate-mutation.sh` produces cast 07. **It edits `app/pricing.py`**,
so it only runs inside a playground that has one. It backs the file up, mutates
it three times, and restores it on exit via a trap — but read it before running
it, and do not run it against a tree you have uncommitted work in.

No cast is included for the billed workflows (`just demo`, `just sdlc`). Record
those yourself if you want them on screen, and note the real prices: `just demo`
was about $0.11, and `just sdlc` on a small feature ran $0.48–$0.76 with a
sonnet planner.

## Production notes

- Scripts are written for the ear. Read them aloud once before recording; any
  sentence you stumble on should be shortened, not re-punctuated.
- `[CAST: ...]` markers in a script mean "a terminal recording goes here". Those
  not already in `casts/` still need capturing.
- Costs and model names age. Check them against your own run before recording,
  and prefer saying "about fifty cents" over a figure to four decimal places.
- The scripts deliberately keep the sharp edges in — cost, the base-prompt tax,
  placeholder gates, the `--force` hazard. Do not cut them for time. A viewer
  who hits an unwarned sharp edge stops trusting the rest of the series.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-25 | Initial index, provenance warning, and cast inventory. |
