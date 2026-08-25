---
title: "Episode 6 — The SDLC chain: plan, build, test, commit"
version: 1.0
updated: 2026-08-25
episode: 6
duration_target: "11 minutes"
prerequisites: [1, 2, 3, 4, 5]
---

# Episode 6 — The SDLC chain: plan, build, test, commit

## Learning objectives

- Trace the exact phase sequence `just sdlc` runs, by the names the code uses:
  `request`, `plan`, `build`, `test_N`, `fix_N`, `commit`.
- Explain why the commit phase is `kind="code"` owned by `"git"`, not an agent
  decision.
- Read a `PlanOutput` → `BuildOutput` handoff and say what a bounded JSON-retry
  loop does when an agent's response doesn't parse.
- Find `context_handoff/plan.md` for a real run and explain what it's for.
- State, and demonstrate, the commit-only-after-green rule — and the
  `commit_all` hazard that trips people up first.

## Cold open (≤45s)

**Visual:** terminal, `just sdlc "add a /health endpoint"` mid-run, phases
scrolling by.

You've seen a planner write a spec, and a builder write code from it. Neither
one, alone, gets you shippable work. A plan nobody implements is a document. A
build with no plan is a guess with commit access. And code that isn't tested
before it lands is a liability with a timestamp.

`just sdlc` is what happens when you chain them: plan, build, test, and only
then, commit. Five phases, in order, in one file:
`adws/adw_plan_build_test.py`. This episode reads that file line by line, and
then we watch a real run that shipped a real feature for $0.61.

## Script

| Time | Visual | Narration |
|---|---|---|
| 0:00–0:45 | Cold open per above | (as written above) |
| 0:45–1:30 | `adws/adw_plan_build_test.py:10` docstring: `Phases: engineer(request) -> planner -> builder -> code(test) [-> builder(fix) -> code(test) ... bounded] -> git(commit)` | This one line is the whole episode. Five phase *kinds*, six phase *names* once you count the loop. Let's open the file and match every phase call to this line. |
| 1:30–2:30 | `adws/adw_plan_build_test.py:37-39`, the `request` phase | First phase: `request`. `kind="engineer"`, owner is `run.engineer` — that's you, the human who typed the prompt. It doesn't call an agent. It just logs what you asked for, so the trace has a first line that says "here is the ask" before any model touches it. |
| 2:30–3:30 | `adws/adw_plan_build_test.py:41-44`, the `plan` phase, alongside `adws/adw_modules/data_types.py:85-90` (`PlanOutput`) | Second phase: `plan`. `kind="agent"`, owner `"planner"`. It calls the planner with two gates: `artifacts_exist`, `files_non_empty`. The planner's job isn't to write code — it's to produce a `PlanOutput` envelope: a summary, a list of artifact paths, and a `commit_message` field it won't get to use in this chain. |
| 3:30–4:30 | `adws/adw_modules/gates.py:27-44`, `artifacts_exist` and `files_non_empty` | Here's what those two gates actually check, and it's disappointingly literal: `artifacts_exist` opens every path the planner *claimed* to write and asks `Path.exists()`. `files_non_empty` then checks the size is not zero. That's it. The planner can say anything in its summary — these gates only believe the filesystem. |
| 4:30–5:45 | `adws/adw_modules/agents.py:291-311`, `_parse_with_retries`, `JSON_FIX_ATTEMPTS = 2` at line 24 | Now the part that's easy to miss: how the plan reaches the builder. Not as text — as a typed JSON object, validated against `PlanOutput`. If the model's final response isn't valid JSON for that shape, the code doesn't fail the run immediately. It calls `send()` again, in the **same session**, telling the model exactly which fields it needs and to drop the prose. `JSON_FIX_ATTEMPTS = 2` means it gets two corrections before the phase gives up. That's the bound — not infinite retries, and not a fresh context each time. |
| 5:45–6:45 | `adws/adw_plan_build_test.py:46-49`, the `build` phase | Third phase: `build`. `kind="agent"`, owner `"builder"`. `ph.call` passes `previous=plan` — the whole `PlanOutput` envelope becomes the builder's context. The builder never re-reads the planner's chat history; it reads the envelope. Gate here is `artifacts_exist` again, checked against whatever `BuildOutput.artifacts` the builder claims. |
| 6:45–8:00 | `adws/adw_plan_build_test.py:51-67`, the `test_i` / `fix_i` loop, `MAX_FIX_LOOPS = 3` at line 24 | Fourth: the test loop. `test_1` is `kind="code"`, owner `"quality"` — it calls `quality.run_tests(run)`, a subprocess, not a model. If it passes, the loop breaks. If it fails, `fix_1` re-enters the builder, `kind="agent"`, with `previous=quality.as_envelope(test, "tests")` — the suite's own failure output, verbatim, as the envelope. Then it loops back to `test_2`. Bounded at 3 attempts total. |
| 8:00–8:45 | `adws/adw_plan_build_test.py:69-74`, the `commit` phase | Fifth: `commit`. `kind="code"`, owner `"git"`. Look at the guard one line up: `if test is not None and test.passed:`. The whole phase is inside that `if`. There is no code path where `commit` runs against a red suite — it's not a policy an agent could override, it's a Python `if` statement wrapping a `with run.phase(...)` block. |
| 8:45–9:30 | `adws/adw_modules/git_helper.py:43-53`, `commit_all` | **Sharp edge, said plainly.** `commit_all` runs `git add -A`, then `git commit`. Not "add the builder's files" — the *entire working tree*. If you've got an unrelated half-edited file sitting there when you run `just sdlc`, it rides along into this commit. Keep your tree clean before a run, same as episode 3 told you to check `git status` before `just demo`. |
| 9:30–10:15 | `ls adws/adw_data/sessions/991c1339/context_handoff/`, then open `plan.md` | These envelopes aren't just in-memory Python objects — the plan phase also writes `context_handoff/plan.md` to disk, per run, under `adws/adw_data/sessions/<adw_id>/`. That's the durable artifact: if you want to know what the planner actually decided for run `991c1339`, this file is the ground truth, independent of the trace or the db. |
| 10:15–11:00 | `sqlite3 adws/adw_data/sssf.db` query on run `991c1339`; then `git show 106712c --stat` | Real run, real numbers. `991c1339`: `adw_plan_build_test`, sonnet planner and builder, request "Add coupon code support to the pricing engine." Five phases, all green: `request` (instant), `plan` (179.5s), `build` (84.3s), `test_1` (0.5s, first try, no `fix` needed), `commit` (0.2s). Total: $0.6139, 552,648 tokens. The commit landed as `106712c`: a `CouponDiscount` dataclass in `app/pricing.py`, its spec in `specs/`, and new tests — 232 lines across 3 files, one commit, one message the builder wrote itself. |

## Commands demonstrated

- `just sdlc "add a /health endpoint"` — runs the full plan→build→test→commit
  chain. Costs money: a sonnet planner + builder run is roughly $0.48–$0.76 per
  the brief; budget similarly here. Watch the phase names in the console match
  this episode's table exactly.
- `git status` — run *before* `just sdlc`, to confirm the tree is clean.
  Free. If this shows unrelated changes, `commit_all` will absorb them.
- `sqlite3 adws/adw_data/sssf.db "select seq, phase_id, status from phases where adw_id='991c1339' order by seq;"` — inspect the real run's phase ledger. Free, read-only.
- `sqlite3 adws/adw_data/sssf.db "select adw_name, request, total_tokens, total_cost from sessions where adw_id='991c1339';"` — the session summary: $0.6139, 552,648 tokens. Free.
- `cat adws/adw_data/sessions/991c1339/context_handoff/plan.md` — read the durable plan artifact for the worked example. Free.
- `git show 106712c --stat` then `git show 106712c -- app/pricing.py` — inspect the actual commit this chain produced. Free.

## Recording notes

- `[CAST: full terminal capture of `just sdlc "add a small, real feature"` from invocation to the final "session finished" banner, showing all five phase names scrolling in order — request, plan, build, test_1, commit — with no fix_N triggered]`
- `[CAST: sqlite3 query output for run 991c1339's phases table, formatted with -header -column, showing the five rows and their durations]`
- `[CAST: git show 106712c --stat output, then the app/pricing.py diff hunk adding CouponDiscount]`
- `[CAST: a deliberately dirty working tree — one unrelated modified file — followed by `just sdlc`, then `git show --stat` on the resulting commit, to make the commit_all hazard visible rather than described]`

## Common mistakes

- **Running `just sdlc` with a dirty tree.** `commit_all` stages everything,
  so an unrelated edit sitting in the working directory becomes part of the
  builder's commit with no warning. Symptom: `git show --stat` on the new
  commit lists a file you never asked to touch. Fix: `git status` first,
  every time.
- **Reading "5/5 phases" as "no problems happened."** A phase can be
  `status="success"` while the *run* still fails — see `run.finish()` in
  `adw_modules/runner.py:114-142`. If `test.passed` is `False` after all fix
  loops, every phase up to that point still shows green, but the exit code is
  1 and there is no `commit` phase at all. Check the run's acceptance, not
  just phase count.
- **Assuming a `fix_N` phase gets a fresh look at the problem.** It re-enters
  the *same* builder session with the suite's raw output appended — it is not
  a new agent starting cold. If the builder misunderstood the plan the first
  time, the same misunderstanding often survives into the fix.
- **Expecting infinite JSON-retry patience.** `JSON_FIX_ATTEMPTS = 2` in
  `adw_modules/agents.py:24`. Three malformed responses in a row (the original
  plus two corrections) and the phase raises, not retries again.

## Check for understanding

1. **Q:** Why is the `commit` phase `kind="code"` with owner `"git"`, instead
   of an agent phase that decides whether to commit?
   **A:** Because whether to commit is a fact the test suite already
   established, not a judgment call — `adw_plan_build_test.py:70` gates the
   whole phase behind `if test is not None and test.passed`. Making it code
   means there's no prompt an agent could be talked out of honoring.

2. **Q:** The planner claims it wrote `specs/991c1339_coupon-discount-rule.md`
   in its `PlanOutput.artifacts`. What actually checks that this is true, and
   what does it check?
   **A:** The `artifacts_exist` gate (`adw_modules/gates.py:27-33`) opens that
   exact path with `Path.exists()`. It doesn't read the content or judge
   quality — `files_non_empty` (line 36-44) separately checks the file isn't
   zero bytes. Together they catch a planner that names a file it never wrote.

3. **Q:** A builder's final response comes back as prose with a JSON block
   buried in the middle, and it fails to parse on the first attempt. What
   happens next, mechanically?
   **A:** `_parse_with_retries` (`adw_modules/agents.py:291`) sends a
   correction message back into the *same* session asking for only a JSON
   object with the required fields — up to `JSON_FIX_ATTEMPTS = 2` times. Only
   after three total failures does the phase raise `RuntimeError` and fail.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-25 | Initial draft, using real run `991c1339` (CouponDiscount, $0.6139, 5/5 phases) and commit `106712c` as the worked example. |
