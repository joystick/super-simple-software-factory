---
title: "Handoff — where this work stands and how to pick it up"
version: 1.10
updated: 2026-11-27
status: active
---

# Handoff

The durable copy of the session state. A parallel copy lives in Claude Code's memory
directory (`~/.claude/projects/<path-slug>/`) which is auto-loaded into a fresh session —
but that directory is outside git, machine-local, and its name encodes this repo's
**absolute path**, so it is lost on a rename or a move. **This file is the one that
survives.** If the two disagree, trust this one and refresh the other.

## The three places

| Where | What it is |
|---|---|
| the Python playground repo | Python playground. Holds the **skill source** at `.claude/skills/sssf/`, a stamped factory in `adws/`, the cart-pricing target app, docs, and the `learn/` course. |
| the TypeScript rebuild repo | Deno/TypeScript rebuild of the same pricing engine, with its **own** stamped factory and its own five-lesson course. |
| [`joystick/super-simple-software-factory`](https://github.com/joystick/super-simple-software-factory) | Fork of `disler/super-simple-software-factory`. **Skill-only** — no `adws/`, no app. |

the Python playground repo was a bare `git init`; it shares no history with upstream. Porting to the fork
is a deliberate file copy, never a rebase.

**Direction of travel.** Skill changes are made in `the Python playground repo/.claude/skills/sssf/` and
copied to the fork. Stamped-factory changes (`adws/adw_modules/*.py`) live per-repo and are
copied between repos by hand — they drift unless synced. `quality.py` is the one module
*designed* to differ per repo: its gate commands are repo-specific and the template keeps
`echo` placeholders deliberately.

## State

```
the Python playground repo   main 5f107b6   51 tests · lint · typecheck   tag: experiment/opus-planner
the TypeScript rebuild repo  main bb18859   77 tests · lint · typecheck   tag: experiment/agy-vs-claude-claude-side
fork        main   up to date with origin (skill_engineering merged, --skip-plan ported)
```

All clean, all committed, single branch each.

## Fork skill fixes (2026-08-30, committed 2026-09-08) — made while dogfooding the skill in a real project

Both surfaced while running `just obs` from a downstream Expo project (`a downstream project`)
that installs this skill. Sat uncommitted for over a week; reviewed and committed 2026-09-08:

- **`.claude/skills/sssf/scripts/install.py`** — `install` did not vendor the visualizer app, so
  `just obs` in a target repo had no server to run. Added `SKILL_ROOT` + a `SKIP_NAMES` set
  (`__pycache__`, `node_modules`, `dist`, `.turbo`) and now copy `apps/visualizer` into the target
  plus the matching `.gitignore` entries.
- **`.claude/skills/sssf/apps/visualizer/server/db.ts`** — opened `sssf.db` `{ readonly: true }`,
  which throws `CANTOPEN` on a **WAL** database (WAL needs to touch `-wal`/`-shm`). Changed to
  `{ readwrite: true, create: false }` — opens the existing WAL db without creating a new one.

`just obs` (Vue/bun visualizer at `.claude/skills/sssf/apps/visualizer`) works after these.

## What exists now that did not before

- **Three coding agents.** `pi`, `claude_code`, `agy` — all in the skill template, mixable
  per agent. `agent_cc.py` and `agent_agy.py` were both written from scratch.
- **Gates wired and verified** in both repos, each watched failing through the ADW.
- **Two `/teach` courses**: `learn/` here (operating SSSF; objective 1 done, objective 2
  next) and `the TypeScript rebuild repo/` (TypeScript; all four objectives done).
- **A head-to-head** between `agy` and `claude` — `docs/head-to-head-agy-vs-claude.md`.
- **`skill_engineering` — built.** Landed upstream in the fork (6 phases + 4 rounds of
  adversarial review, `skill_engineering.py`/`vendor_skill.py`/`adw_skills.py`), pulled into
  this repo 2026-09-08. Reviewed post-pull — two low-severity findings, both fixed
  2026-09-08 (see below): missing test coverage on `load_plan_from_file`, and an
  unvalidated `--as` path-traversal case in `vendor_skill.py`.
- **Fixed the two review findings above.** `vendor_skill.vendor()` now rejects any `--as`
  name containing a path separator or resolving to `.`/`..`/empty (`UnsafeNameError`) —
  `Path(dest_dir) / name` joins literally, so an unchecked name could escape `dest_dir` or
  (if absolute) discard it outright. Added `test_vendor_skill.py` coverage for the guard,
  plus a new `test_utils.py` covering `load_plan_from_file`'s summary extraction and both
  its error paths. Full suite green (99 passed) after the changes.
- **Two more fixes ported back from a downstream adoption** (a downstream project, which went
  through its own ADR-governed git-init cutover 2026-09-09 — the first real target repo to
  actually exercise `adw_watch.py`'s git-dependent code against a live history):
  - `git_helper.py`'s `_git()` did a full `.strip()` on subprocess output — silently ate
    the leading space off only the *first* line of multi-line porcelain output (git's
    status codes are leading-whitespace-significant: `" M path"` vs a corrupted `"M path"`
    shifted `changed_files()`'s fixed `line[3:]` slice into the filename itself). Never
    reachable before a target repo had real git history to run these functions against.
    Fixed to `.rstrip()` — trailing-only, never eats meaningful leading whitespace.
  - `just sssf` renamed to `just watch`, matching its script (`adw_watch.py`) — 6 of 8
    recipes in this justfile mirror their script name directly; this one didn't need to be
    the second deliberate exception `sdlc` already legitimately is. Every prescriptive
    reference in the playbook's Part D updated; the two changelog rows describing what was
    literally built and named at the time (4.0/4.1) were deliberately left saying `just
    sssf` — accurate history, not something to retroactively rewrite.
  Both verified: full suite green (124 passed) after porting.

## Publishing hygiene — real adopter names (issue #23)

This repo is **public**, and `.claude/skills/sssf-skill-vendoring/` is a
**shipped** skill: a name written there propagates into every adopter repo that
installs it, not merely to people browsing GitHub.

Tracked files are now clean of real adopter project names, and
`.claude/skills/sssf/tests/test_no_private_identifiers.py` fails on a denylist
of them so it cannot silently regress. The convention is a neutral label that
keeps the engineering detail — "a downstream adopter", "the Rust adopter",
"that adopter" — because the value of those passages is the *failure*, never
the repo it happened in. `route-builder` and `cart-pricing` are the deliberate
non-existent stand-ins used in docs, lessons and fixtures.

**The scrub does not reach history, and no attempt was made to.** `git log -S`
finds the old names in ~20 commits going back to 2026-09-08; the repo is public
and long since pushed, so the names remain retrievable from history exactly as a
pushed secret would. What was fixed is that nothing *new* ships them. If those
names are ever judged genuinely sensitive rather than untidy, that is a separate
and much larger decision (history rewrite + force-push, or a fresh repo) and
should be taken deliberately, not inherited from this cleanup.

Out of scope by design: `downloads/` (gitignored) and `.claude/settings.local.json`
(untracked) still contain real names. Neither is published, and testing them
would produce permanent false failures.

## Open

**Nothing is blocked.** Three things remain deliberately left (item 3 closed
2026-11-27, issue #20 — kept in place, marked CLOSED, rather than deleted, so the
two design questions it resolved stay readable):

1. **The dead-gate demo** (~£1). Break the TypeScript rebuild repo's test gate to an `echo`, plant a known
   bug, run a real `just sdlc` on an unrelated feature, watch the factory commit the bug and
   record `5/5 ✓ success`. The mechanism is traced and each link verified in isolation; what
   is missing is watching the whole chain do it. Buys conviction, not information. **Do it
   in a copy of the repo** — a commit containing a deliberate bug should not enter real
   history.
2. **`learn/` objective 2** — reading a trace, and what `sssf.db` structurally cannot tell
   you.
3. **`adw_watch.py` doesn't work in every target repo — found trying to point it at
   a downstream project.** Two independent problems, both real:
   - **Assumes a git repo unconditionally.** `commit_watcher_state()` (added `032b25f`,
     2026-09-09 — the "commits its own claim/resolve/fail writes" fix) shells out to
     `git status`/`git commit` after every claim/resolve/fail with no guard. a downstream project
     is deliberately **not** a git repo (its own ADR 0003) — running the watcher there as-is
     would error on the first claim. `run_once`'s own dirty-tree refusal
     (`git_helper.is_repo() and git_helper.is_dirty()`) already shows the right pattern
     (`is_repo()` gates it) — `commit_watcher_state` needs the same gate, and the
     non-git case needs a defined behavior (skip committing entirely? refuse to run at all,
     same as the GitHub/GitLab-tracker refusal in `detect_tracker`?) — a real design
     decision, not just a missing `if`.
   - **Tracker-shape mismatch.** `discover_issues()`'s frontier scan expects
     `.scratch/<feature>/issues/NN-slug.md` (a numbered-file subdirectory — the shape Part D's
     "Filing" section, `2513c46`, documents). a downstream project's own
     `docs/agents/issue-tracker.md` (predates Part D) uses one file per feature,
     `.scratch/<feature>/issue.md` — no `issues/` subdir, no `NN-` numbering, no
     `Blocked by:` convention. The watcher would silently find nothing there, not error —
     worse than the git problem, because it looks like an empty queue instead of a
     shape mismatch.
   **CLOSED 2026-11-27 (issue #20).** Both halves are fixed, after the same
   failure recurred in a second adopter — one whose tracker had since migrated to
   GitHub Issues, where `just watch` could not be used at all and every ticket had
   to be dispatched manually (`adw_simple_sdlc.py` per issue), exactly as the first
   adopter did. Recurrence in a different shape was the argument for a seam rather
   than another special case.

   `adw_watch.py` now selects a **tracker adapter** from the `detect_tracker()`
   value it already computed — `LocalTracker` / `GitHubTracker` / `GitLabTracker`,
   one protocol (`discover` / `set_status` / `append_comment` / `commit_state` /
   `prompt_for` / `preflight`). Resolutions to the two open design questions:

   - **(a) non-git behaviour.** Remote trackers make `commit_state` a **no-op** and
     never consult git at all: a label change is already durable server-side, so
     there is nothing local to commit. The dirty-tree refusal is likewise scoped to
     local trackers — it exists because local claiming commits, which cannot apply
     to a tracker that commits nothing. A git-free repo on a remote tracker now
     works, and **as of 2026-11-27 so does one on the local tracker** (#24):
     `commit_watcher_state` returns early when `is_repo()` is false, printing one
     line per run rather than failing or going silent. Item 3(a) is therefore
     fully resolved. Skip-and-say-so was chosen over refuse-to-run: in a git-free
     repo the working tree *is* the storage model, so the status writes are already
     as durable as every other file there, and denying the whole queue over a
     version-control preference would be disproportionate. What is given up is the
     audit trail of status transitions, which is the only reason committing them
     exists.
   - **(b) single-`issue.md`.** `discover_issues()` **does** now recognize it
     (`.scratch/<feature>/issue.md`, numbered `01`, `issues/` preferred when both
     exist). It was the cheaper half of the answer and removes a silent-empty-queue
     failure from every older adopter repo, rather than pushing a migration onto
     each of them.

   The fail-closed property the old hard refusal got right is preserved and now
   tested: a missing or unauthenticated CLI — at preflight **or** mid-run — exits 2
   with a clear message, never a falsely-empty queue. Two semantics genuinely invert
   between the families and are pinned by tests rather than left to inference: a
   blocker that cannot be found is **still blocking** locally (a dangling ref) but
   **resolved** remotely (`gh` lists open issues only, so absence is the evidence it
   closed), and "resolved" means the literal string locally but a **closed issue**
   remotely. Suite: 143 passed, with every CLI call faked — no network, no `gh`/`glab`
   binary needed.
4. **Not every vendored skill belongs on a headless agent via `skill_engineering:` — the
   `code-review` skill is a concrete counter-example, found live in a downstream project.**
   Vendored alongside `wayfinder`/`write-a-prd`/`prd-to-plan`/`tdd` (all four wired to
   `planner`, 2026-09-09), `code-review` was deliberately left unwired after assessment
   (independent research agent, a downstream project's own `adws/`): wiring it to the `reviewer`
   agent would conflict on three fronts, not just need the same "ask the user" override the
   planner skills got —
   - **Assumes interactivity the override pattern can't fully absorb.** Beyond "ask for the
     fixed point" / "ask the user where the spec is" (the planner-style fix), it also
     requires **parallel sub-agents** it has no tool access to under `reviewer`'s
     `tools:` list (no Task/Agent tool) — unexecutable, not just interactively awkward.
   - **Contradicts the target agent's own charter.** `reviewer/system.md` already says
     "not your job: running tests, style opinions, refactors" — `code-review`'s Standards
     axis is exactly that. Letting style findings count toward `blocking` would spend
     `adw_simple_sdlc.py`'s bounded `MAX_REVISION_LOOPS` on style, not spec conformance.
   - **Output-shape mismatch.** The skill wants to produce a human-readable two-section
     report ("don't pick a single winner across axes"); the reviewer's actual contract
     (`ReviewOutput`: `approved: bool` + `blocking: [...]`) is consumed *programmatically*
     to gate commit-vs-revise — `reviewer/user.md` demands "ONLY valid JSON, no prose."
   Planner's wiring worked because stripping "ask the user" left transferable content
   behind (PRD structure, TDD discipline). Here, stripping the interactive bits *and* the
   unsupported orchestration *and* the incompatible output format leaves only a smell
   checklist that actively fights the reviewer's own no-style-opinions rule. **Left
   unwired** (`code-review.md` sits in `adws/adw_data/skill_engineering/`, `just skills`
   correctly reports it `(unused)`) — kept instead as a candidate for the engineer's own
   *interactive* pre-merge use, same bootstrap-phase category as `/grill-with-docs`.
   Possible follow-up if standards-checking is wanted headlessly: route it through the
   deterministic `ast-grep scan` gate `reviewer/system.md` already names, not through
   `skill_engineering:`. Worth folding this "does the target agent's contract survive
   composition" check into the adoption playbook's "Where the two layers sit" section as
   general guidance, not just an a downstream project-local note — not done yet.

## Things that will bite if forgotten

- **`just sdlc` gates on tests only** (`run_tests`, 1 of 3). Lint and typecheck are wired
  and verified but do not run in that chain. Run `just quality` afterwards — it is free.
- **`commit_all` stages the entire working tree.** Clean tree, throwaway branch, every time.
- **A green banner means the gates you verified found nothing.** Nothing more. This is the
  whole subject of `learn/`.

## The one idea underneath all of it

A gate has two states that are **identical from outside**: it checked and found nothing
wrong, or it is incapable of finding anything. Green does not distinguish them; neither does
reading the command. Only a deliberate defect does.

Four separate bugs this session were the same failure — a claim nobody executed. The clamp
test that passed with the clamp deleted. The percentages that were all binary-representable.
The guard invisible through the public entry point. The gate table that was simply wrong.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-27 | Initial handoff. |
| 1.1 | 2026-08-30 | Recorded two uncommitted fork skill fixes (`install.py` visualizer-vendoring, `db.ts` WAL read-write) found while dogfooding `just obs` downstream. |
| 1.2 | 2026-09-08 | Committed and pushed the two fork skill fixes. Pulled 21 upstream commits, including `skill_engineering` (now built) and the adoption-playbook rework; reviewed, findings filed. |
| 1.3 | 2026-09-08 | Fixed both review findings from 1.2: `vendor_skill.py`'s `--as` path-traversal case, and missing test coverage on `load_plan_from_file`. |
| 1.4 | 2026-09-09 | Filed a new Open item: `adw_watch.py` (`just sssf`, built today) doesn't work against every target repo — found trying to point it at a downstream project. Assumes a git repo unconditionally (breaks against a deliberately git-free target, ADR 0003 there) and its frontier scan's `issues/NN-slug.md` shape doesn't match that repo's older single-`issue.md` tracker convention. Not fixed; a downstream project's next ticket dispatched manually instead. |
| 1.5 | 2026-09-09 | Filed a new Open item: the vendored `code-review` skill (a downstream project) was deliberately left unwired from `reviewer` after assessment — it assumes interactivity + sub-agent orchestration `reviewer`'s tools can't support, contradicts `reviewer`'s own "not your job: style opinions" charter, and its human-readable report format mismatches the `ReviewOutput`/JSON contract `adw_simple_sdlc.py`'s revision loop consumes programmatically. `wayfinder`/`write-a-prd`/`prd-to-plan`/`tdd` remain wired to `planner`, unaffected. Flags a possible playbook follow-up (does the target agent's contract survive composition, not just "ask the user") — not written yet. |
| 1.6 | 2026-09-09 | Ported two fixes back from a downstream project after it became the first target repo to actually run `adw_watch.py`'s git-dependent code against a real, live git history: a real bug in `git_helper.py`'s `_git()` (a full `.strip()` corrupted the first path in multi-line porcelain output — fixed to `.rstrip()`), and `just sssf` renamed to `just watch` to match its script name. Playbook bumped to 4.3 with a new changelog row; historical 4.0/4.1 rows deliberately left saying `just sssf`, matching what was actually named at the time. Full suite green (124 passed). |
| 1.7 | 2026-09-10 | Ported another real fix back from a downstream project, found after its first two live `just watch` dispatches (a PIN-authentication access gate, a biometric-unlock follow-up) both landed with zero review: `adw_watch.py` always called `adw_plan_build_test.main()` (planner → builder → test → commit, no reviewer/revision-loop/documenter), not the fuller `adw_simple_sdlc.py` chain the playbook's own prose implied. An unattended queue dispatch has nothing else checking it besides the test gate — worse than a manual `just sdlc` run a human reads afterward. Switched the dispatch target (identical 3-arg signature, confirmed before switching); the roster already had `reviewer`/`documenter` configured. Playbook bumped to 4.4; "What this playbook does not claim" corrected — `just watch` genuinely has shipped two real issues now, but not yet through this corrected full-chain path. Full suite green (124 passed). |
| 1.8 | 2026-09-10 | Self-correction: the "126 passed" test count reported in this file's 1.6/1.7 rows and in commits `8b80fdc`/`6a3a981`'s messages was wrong — the fork's suite has always been 124 tests, identical to a downstream project's count, confirmed by rerunning both directly. Fixed both rows here to say 124. The two already-pushed commit messages still say 126 and are left as-is rather than rewriting pushed history; treat this row as the correction of record. |
| 1.9 | 2026-11-27 | Closed Open item 3 (issue #20): `adw_watch.py`'s frontier scan is now **tracker-agnostic**. One adapter protocol selected from the `detect_tracker()` value that already existed — `LocalTracker` / `GitHubTracker` / `GitLabTracker`. Triggered by the same failure recurring in a second adopter, one whose tracker had migrated to GitHub Issues: `just watch` could not be used at all there and every ticket was dispatched manually (`adw_simple_sdlc.py` per issue), exactly as row 1.4's adopter did. Both of item 3's open design questions resolved: remote trackers make `commit_state` a no-op and never consult git (a label change is already durable), and the dirty-tree refusal is scoped to local trackers since it exists only because local claiming commits; `discover_issues()` additionally recognizes the older single-`issue.md`-per-feature shape rather than pushing a migration onto every older adopter. Fail-closed preserved and now tested at preflight **and** mid-run: a missing/unauthenticated CLI exits 2, never a falsely-empty queue — "looks like an empty queue" was the original bug and is strictly worse than an error. Two semantics genuinely invert between families and are pinned by tests, not inferred: an unfindable blocker still blocks locally (dangling ref) but is resolved remotely (`gh` lists open issues only, so absence IS the evidence it closed), and "resolved" is the literal string locally but a closed issue remotely. Also fixed a robustness gap found by the existing suite during the refactor — `TrackerUnavailable` raised from `discover()` escaped `run_once` as a traceback instead of exit 2. One test retired deliberately: `test_main_returns_2_for_a_non_local_tracker` pinned the "not implemented yet" refusal this replaces, and was environment-dependent (unmocked, so it only still passed because `tmp_path` isn't a git repo); its surviving property is covered by `test_main_exits_2_when_the_tracker_cli_is_unavailable` with the CLI mocked. Suite: **143 passed** (was 124; +19 adapter tests, all CLI calls faked — no network, no `gh`/`glab` needed). Separately noted for a downstream port: that adopter's vendored `adw_watch.py` is **stale against this template** in `read_blocked_by` — it splits on commas before stripping parentheticals, so `Blocked by: None (Phase 10 complete, merged into X)` made an explicitly unblocked ticket permanently blocked; 18 ticket files were affected. The template has been correct since 2026-09-24; vendored `adws/` copies drift silently with nothing detecting it. |
| 1.10 | 2026-11-27 | Brought the fork's own tracker to zero open issues, and closed the four that mattered with code rather than triage. **#19** `commit_build` crashed on a correct zero-change build (the planner finding work already done is a feature); split the clean-tree case into commit / skip / claims-mismatch, the third being a builder reporting work it did not do, which `gates.diff_matches_claims` never caught because it only asserts claimed paths EXIST. Fixing only `commit_build` would have moved the crash one phase later into `changes`, so the whole documentation branch is now gated on a commit having landed. **#21** remote dispatch prompts were title+body only, so a requirement appended as a comment reached no agent while the run still went green; comments are now included **filtered** (the watcher's own status notes, AI-triage notes and bots dropped — feeding a prior run's "flipped to ready-for-human" into the next attempt is worse than omitting it) with body-is-the-contract precedence stated in the prompt. This was a divergence #20 introduced, not an omission: local always included comments because `resolve_prompt` reads the whole ticket file. **#24** (split out of #20) `commit_watcher_state` assumed a git repo; now skips and says so once per run, closing HANDOFF item 3(a) in full. **#23** real adopter project names were in 11 tracked files of this PUBLIC repo, six of them inside the shipped `sssf-skill-vendoring` skill; scrubbed to neutral labels, with a denylist test so it cannot regress, and the cheat sheet's `cp /path/to/<private-repo>/...` commands repointed at the `reference/` dir that actually ships here — they had been instructing readers to copy from a repo they could not have. **#18** closed as answered: `--skip-plan` and `adw_build.py` are not redundant. Suite **124 → 163**. | 
