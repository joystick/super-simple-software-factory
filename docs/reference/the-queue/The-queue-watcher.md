---
title: The queue watcher (just watch)
---

# The queue watcher — `just watch`

`just watch` runs `adw_watch.py`: the headless half of the dark-factory
queue. It scans the local-markdown issue tracker for ready work, claims the
frontier ticket, dispatches it through the **full SDLC chain**
(`adw_simple_sdlc.py` — planner → builder → reviewer → revision loop →
documenter → commit), and resolves or fails it. Source:
`.claude/skills/sssf/templates/adws/adw_watch.py:5-51` (module docstring).

## Why the full SDLC chain, not the lighter one

The module docstring is explicit about this choice: "an unattended queue
dispatch gets no other independent check besides the test gate, so it needs
the review/revision loop a supervised manual run could otherwise skip." A
human running `plan_build_test` interactively can eyeball the plan before it
ships; nothing eyeballs a `just watch` dispatch, so the queue always takes
the slower, more-checked chain. See
`the-queue/Dark-factory.md#the-chain-named-once` for how this is framed at
the playbook level.

## The scan-claim-dispatch-resolve cycle

`run_once()` (`adw_watch.py:328-351`):

1. **Refuse on a dirty tree.** Claiming commits (see below), so a dirty
   working tree would sweep unrelated in-progress work into that commit —
   `run_once` refuses outright rather than risk it.
2. **Scan** — `discover_issues()` reads every `.scratch/<feature>/issues/*.md`
   file carrying a canonical `Status:` line.
3. **Pick the frontier** — see `the-queue/Frontier.md`.
4. **Dispatch** — `dispatch()` (`adw_watch.py:271-313`):
   - `set_status(issue, CLAIMED)`, then commits that write immediately
     (`commit_watcher_state`) — the ADW's own commit phase fires mid-run,
     *before* dispatch's final status write, so without this immediate
     commit the last transition would sit uncommitted after every run.
   - Runs `adw_simple_sdlc.main(prompt, ...)` with the issue file's own body
     as the prompt.
   - On success: `set_status(issue, RESOLVED)`, comment, commit.
   - On a non-zero exit **or a crash** (`Exception` and `SystemExit` are
     both caught explicitly — `SystemExit` inherits `BaseException`, not
     `Exception`, and `agents.validate()` raises it on a bad config, a real
     bug found live 2026-09-10 that let a config error crash the whole
     watcher process and strand a ticket at `claimed` with no resolution
     commit): `set_status(issue, FAILED_STATE)` — flips back to
     `ready-for-human`, never left stuck at `claimed`. `KeyboardInterrupt`
     still propagates and stops the watcher, the behavior an operator hitting
     Ctrl+C actually wants.

## `--once` vs looping

`--once` runs a single cycle and exits with a meaningful code for
cron/launchd: `0` if work was dispatched (check the ticket's new `Status:` to
know the outcome), `1` if the queue was empty, `2` if the tracker isn't
local-markdown (GitHub/GitLab trackers are detected and explicitly refused,
not silently mishandled — `detect_tracker`, `adw_watch.py:314-327`). Without
`--once`, it loops on `--interval` seconds (default 300).
Source: `adw_watch.py:352-384` (`main()`).

## Status format tolerance, and its limit

The status/blocked-by parser tolerates two real forms found in the wild —
plain `Status: X` and `**Status:** X` (bold, matching `to-tickets`' own
template) — via `STATUS_RE`/`BLOCKED_BY_RE`
(`adw_watch.py:73-74`). It does **not** silently tolerate other markup
(underscores, missing colon, wrong casing); a near-miss line instead prints a
loud stderr warning that the ticket is invisible to the frontier scan, rather
than silently vanishing from the queue the way four real `to-tickets`-authored
tickets once did undetected. (`_check_format`, `adw_watch.py:157-176`)

## See also

- `the-queue/Frontier.md` — the selection rule step 3 uses.
- `the-queue/Dark-factory.md` — where the watcher sits in the larger
  unattended-operation picture.
- `.claude/skills/sssf/templates/justfile` — the `watch` recipe that runs
  this script.
