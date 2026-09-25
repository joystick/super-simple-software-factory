---
title: docs/reference (full SSSF concept glossary) + docs/training (playbook + full learning arc)
created: 2026-09-24
status: done
---

# docs/reference + docs/training — supersedes the earlier handbook/reference split

## Supersession note

This replaces `plans/2026-09-24-consolidate-learning-content.md`'s target layout.
That plan's *mechanics* (ignore-aware copy of `site-starlight/`, `.gitignore`
porting, hash verification before delete, phased execution) are still correct and
reusable — but its target directory name (`docs/handbook/`) and its reference scope
("point at the site, no fork-level reference content") are both superseded by this
plan:

- `docs/handbook/` → **`docs/training/`** (renamed, and now explicitly two things,
  not one — see below).
- `docs/reference/` → no longer a thin pointer page. It must be a **complete
  glossary of every SSSF concept and component** — "what is X in SSSF" must always
  have an answer.

The prior plan's Phase 1 mechanics (site move, `.gitignore`, hash verification, the
21-file grep checklist) still apply unchanged to relocating `sssf-learn`'s Astro
site; only the destination path and surrounding scope changed. Do not re-derive
those mechanics — reference them.

## Why (restated for this plan's actual scope)

Two deliverables, not one:

1. **`docs/reference/`** — a complete, standing glossary. Every core SSSF
   concept/component (ADW, Gate, Envelope, Phase, Roster, `coding_agent`, the
   queue's Frontier, etc.) gets a real reference page. Grounded in a concept
   inventory already extracted from the actual codebase (see Concept inventory
   below) — not invented, not copied from memory.
2. **`docs/training/`** — two sub-parts:
   - a) **The playbook**, in md + pdf, as the on-screen step-by-step guide for
     newbies. This already exists (`docs/playbook-adopting-sssf.md` +
     `.pdf`) — this plan relocates/frames it, does not rewrite it.
   - b) **The guide**, in Astro/Starlight format, navigating an agentic engineer
     from a basic prompt all the way to running an unattended dark-factory queue.
     This is `sssf-learn`'s site, relocated (per the superseded plan's mechanics)
     **and substantially expanded** — its current two chapters only reach "gates
     deep-dive," not "dark factory." A gap analysis (below) found ~20 net-new
     lessons needed across 5 new chapters.

## Concept inventory (docs/reference/'s content backbone)

Extracted 2026-09-24 by a fable research pass reading `adw_modules/*.py`
docstrings, `sssf.config.yaml`'s inline comments, `references/{config,handoff,
observability}.md`, and the playbook. Revised 2026-09-24 after a fable critique
pass (`a9afe766faa44234c`) spot-checked 30 of the ~75 concepts against real
source — 27/30 confirmed accurate, 3 corrections folded in below. ~75 concepts
across **7** categories (the original header said 6; the list below always had 7
— a labeling error, not a scope error):

1. **Core execution model** — ADW, adw_id, Session/`ensure()`, Run, Phase,
   PhaseParams, four-param rule, AgentCall, `agents.execute()`, "agent proposes /
   code disposes", chains (`plan_build_test` vs `adw_simple_sdlc`), `--skip-plan`.
2. **Handoff & typed output** — Envelope/EnvelopeBase, two output channels,
   typed-output rule, `previous_envelope`, `context_handoff/`, output types
   (PlanOutput, ReviewOutput, etc.), ChangeSet/BaseRef, `agent_map.json`, session
   directory layout.
3. **Agent configuration** — Roster, `defaults` merging, `coding_agent`, `model`,
   `thinking`, `tools`, `writes`, `protected_files`, `purpose`/`color`,
   `prompt_engineering`, `harness_engineering`, `skill_engineering`, `data_dir`,
   observability config, `ignored_field_warnings`, `validate()`. Grounded in
   `.claude/skills/sssf/templates/sssf.config.yaml` (corrected path — this file is
   NOT at fork root, it's the template `/sssf install` stamps into target repos).
4. **Coding-agent drivers** — agent_pi, agent_cc, agent_agy, agent_opencode,
   PiRequest/PiResult, ToolCallTracker, UsageBreakdown, `operator_env`.
5. **Quality gates & permissions** — Gate/GateReport/GateCheck, built-in gates,
   quality blocks, Rule zero, `snapshot()`/`enforce()`/PermissionBreach,
   `always_writable`. **NET-NEW, not "reorganize existing"** — the critique
   confirmed zero hits for `always_writable`, `PermissionBreach`, `Rule zero`, and
   `Console` anywhere in `references/*.md`. These need pages written from
   `adw_modules/permissions.py` and the playbook's Rule Zero section directly.
6. **Observability** — Tracer, EventRecord, prompt audit copy,
   `adw_skills.py`/`audit_skills`. **Correction**: "Console" moved to category 5
   (it's `adw_modules/console.py`, unrelated to observability's tracer/UI
   concerns — a miscategorization in the original pass). **Correction**:
   "Visualizer" is not a module symbol — it's the app at
   `.claude/skills/sssf/apps/visualizer/`, documented in `observability.md` and
   the root `justfile`'s `obs` recipe. Its glossary entry should describe it as
   an app, cite those sources, not imply an `adw_modules/` class.
7. **The queue / dark factory** — dark factory, the four jobs, two layers, five
   vendored skills, the chain named once, triage states, agent brief, issue
   tracker, ticket file, frontier, claim/resolve, scan-claim-dispatch-resolve
   cycle, mandatory checkpoints, bootstrap vocabulary. **NET-NEW, not
   "reorganize"** — the critique found only 1 hit ("frontier") across all of
   `references/*.md`; this category's real sources are
   `.claude/skills/sssf/templates/adws/adw_watch.py`,
   `.claude/skills/sssf/templates/justfile`,
   `.claude/skills/sssf/templates/prompt_engineering/planner/system.md`, and the
   playbook — add these explicitly as the grounding sources, not
   `references/*.md`, which barely touches this category.

**Existing reference files — LINK, do not move.** `references/config.md`,
`handoff.md`, and `observability.md` (confirmed present at
`.claude/skills/sssf/references/`, 391/161/158 lines) are **skill-internal specs**
cited by name from `SKILL.md` itself (`SKILL.md:28,59`). The original "absorb and
reorganize as backbone" plan was wrong: moving them breaks `SKILL.md`'s citations;
copying them creates two divergent sources of truth for the same content — exactly
the "no cross-linking, no single answer" problem this whole project exists to fix.
**Decision**: `docs/reference/` stays a genuinely separate, fork-level glossary
that **links to** these three files in place (relative links into
`.claude/skills/sssf/references/`) for the material they already cover well
(config shape, defaults merging, envelopes, tracer tables), and only gets its own
new pages for what they don't cover — categories 5 and 7 above, plus any concept
from 1-4/6 not already well-explained there. `docs/reference/README.md`'s index
makes this link-vs-own-page split explicit per category so a reader always knows
whether "what is X" resolves locally or via a link, never a dead end.

**Fork glossary vs. course-internal reference — the other duplication risk.**
`sssf-learn`'s own `01-sssf-fundamentals/reference/` and
`02-gates-deep-dive/reference/` MDX pages (Verifying a Gate, Gate Cookbook, Deno
Gates, Types and Contracts, etc.) are lab-specific how-to material, not glossary
entries — they stay inside `docs/training/site-starlight/` unchanged. Rule: the
fork's `docs/reference/` is the canonical "what is X" answer; the course's own
`reference/` pages cross-link INTO the fork glossary for term definitions (e.g. "a
Gate, defined in docs/reference/...") rather than ever redefining a term
independently. This rule must be written into `docs/reference/README.md` and
`docs/training/README.md` both, not left implicit.

## Gap analysis (docs/training/'s content backbone)

Extracted 2026-09-24 by a fable research pass reading `sssf-learn`'s 17 existing
lessons' titles/gists, the playbook's section headings, and `training/`'s 10
episode scripts' learning objectives.

**Already covered** (17 lessons, keep as-is):
- **Chapter 1 — SSSF Fundamentals** (12 lessons): agent-proposes/code-disposes,
  gate verification, wiring vs writing gates, envelope, phases, fix loop, roster/
  writes, `skill_engineering` (half — see gap), reading the trace, composing a
  chain (partial — see gap), install+stamp+full SDLC, whole-machine synthesis.
- **Chapter 2 — Gates, Deep Dive** (5 lessons): a Deno/TS build-the-gates lab.
  Deepens Rule Zero; doesn't extend the operating arc.

**Confirmed gaps** (checked directly, not inferred):
- `harness_engineering` — **zero mentions** in sssf-learn (grep-confirmed). Only
  the playbook's "two layers" framing covers it.
- Bootstrap/AFK split (Part C) — **zero mentions** of bootstrap, AFK, grill,
  or the headless-interview problem.
- Queue/triage/`just watch` (Part D) — **zero mentions** of `just watch`,
  `ready-for-agent`, triage, or wayfinder.
- Writing an ADW from scratch (training ep10) — **partial**: existing lesson 0009
  teaches copy-closest-and-edit; missing the from-scratch skeleton, the
  four-param rule → Pydantic, extending `EnvelopeBase` + its gate, the
  agent-vs-code phase decision.
- Coding agents & cost (training ep09) — **overstated in the original pass, corrected
  by the fable critique**: lesson 0008 already teaches reading `total_tokens`/
  `total_cost` from `sessions`, and 0007 already teaches `coding_agent` vs
  `skill_engineering_applies()`. Ch4's real gap is narrower — the driver contract
  (`agent_cc`/`agent_pi`) and `--resume`/hermetic-flag mechanics — not "cost
  reading" from scratch, which is only ~1.5 lessons' worth of genuinely new
  material, not 3.
- Part A (existing-codebase adoption) and Part B (new-project bootstrap) —
  **not taught** as lessons; only in playbook prose.

**Proposed complete arc** (chapters 1–2 exist; 3–7 are net-new, ~20 lessons):

| Chapter | Status | Lessons |
|---|---|---|
| 1. SSSF Fundamentals | **Exists** | 12 (keep) |
| 2. Gates, Deep Dive | **Exists** | 5 (keep) |
| 3. Adopting a Factory | **Net-new** | 5 (recon-before-spending; interrogate-before-plan; the four jobs; new-project walking-skeleton+install; tuning the roster) |
| 4. Coding Agents and Cost | **Net-new** | 3 (the driver contract; sessions/resume/hermetic flags; reading real cost) |
| 5. Owning Your Workflow | **Extends 0009** | 2 (composing a chain — exists; from-scratch skeleton + new envelope type + its gate — new) |
| 6. Going Dark | **Net-new** | 4 (two layers; bootstrap vocabulary; the two headless problems; definition of done, extended) |
| 7. The Queue | **Net-new** | 5 (the chain named once; triage as sole promoter; filing checkpoints; `just watch` concretely; capstone — run a queue end to end) |

## Scoping decision for THIS pass (flagged for fable critique to challenge)

~20 new pedagogical lessons and ~75 reference articles is not something to
hand-author in one pass and honestly call "publish-ready" — that's a large body of
original writing, not a mechanical move. Proposed scope for the isolated test
implementation (next step):

- **Full structure**: every chapter, every lesson file, every reference page as a
  real file in the sidebar, correctly linked, correctly ordered — nothing missing
  from the navigation.
- **Fully authored, as a representative sample proving depth is achievable** (both
  picks revised per the fable critique — the original "easy" pick, Ch4 "reading
  real cost," turned out to mostly duplicate existing lesson 0008, proving nothing
  about the harder prose→lesson conversion the sample exists to test):
  - 1 complete new lesson from Chapter 7, "The Queue, `just watch` concretely" —
    the most novel content, closest to "dark factory," genuinely new prose-to-
    lesson conversion from `adw_watch.py` + the playbook's Part D.
  - 1 complete new lesson from Chapter 6, "Bootstrap vocabulary" (`grill-with-docs`,
    `CONTEXT.md`/ADRs, the interview-relocation problem) — purely playbook-derived,
    zero existing-lesson overlap, exercises the same prose→lesson mechanism as the
    Chapter 7 pick from a different source shape (narrative "why" prose vs.
    procedural code-comment prose).
  - ~10 reference pages: at minimum one from category 5 and one from category 7
    (both confirmed net-new, no existing source to lean on), plus a worked example
    of the link-vs-own-page split for a category-1/3 concept that IS already
    covered by `references/config.md` — proving the "link, don't duplicate"
    decision actually works in practice, not just in the plan's prose.
  - A written 75-row concept→page manifest (concept name, target category, link vs.
    own-page, source citation) BEFORE any page is built — the critique's finding
    that "every concept has a real page" is unverifiable without a fixed checklist
    to check against. This manifest itself is a required artifact of this step, not
    an afterthought.
  - The playbook's md+pdf relocated and verified rendering correctly under
    `docs/training/`
- **Stubbed, honestly labeled**: every other lesson/reference page gets a real
  file with frontmatter, a one-paragraph summary (from the inventory/gap-analysis
  data already gathered — not invented), and an explicit
  `<!-- TODO: full lesson content, see plans/2026-09-24-docs-reference-and-training.md -->`
  marker. Starlight renders these as real, findable, honest-about-incompleteness
  pages — not broken links, not silently absent from the sidebar.

This makes the *isolated test implementation* deliverable "structure is complete
and provably sound; a representative depth sample proves the content style and
mechanism work" — not "every page is finished." Full authoring of the remaining
~85 stubbed pages is follow-up work, tracked as its own item in this plan's
definition of done, explicitly NOT claimed done by this pass.

## Isolated test implementation — workspace

**Not `/private/tmp/...`.** The fable critique flagged a real risk: macOS
periodically reaps untouched `/private/tmp` entries after ~3 days, and this pass
involves an `npm install` (Astro 7 + Starlight 0.41, several minutes) plus
hand-authored content that must survive across however many turns this takes.
Use `/Users/alexei/Projects/training/_scratch/docs-training-test/` instead —
outside both real repos (so nothing here is mistaken for the real thing or
accidentally committed to either), but on durable local disk. `git init` it
immediately after scaffolding so in-progress edits have real history and nothing
is lost to an interrupted session; this scratch repo is never pushed anywhere and
gets deleted once Phase's content is copied into the real fork.

```
docs-training-test/
├── reference/                  # mirrors the target docs/reference/ layout
│   ├── README.md               # index: the 7-category structure, AND the
│   │                            #   explicit link-vs-own-page rule (which
│   │                            #   categories/concepts resolve via a link into
│   │                            #   .claude/skills/sssf/references/*.md, which
│   │                            #   get their own new page)
│   ├── concept-manifest.md     # the 75-row concept -> category -> link/own-page
│   │                            #   -> source-citation table, written FIRST
│   ├── core-execution-model/
│   ├── handoff-and-output/
│   ├── agent-configuration/    # mostly LINKS into references/config.md per the
│   │                            #   manifest, own pages only for gaps
│   ├── coding-agent-drivers/
│   ├── quality-gates-and-permissions/   # mostly OWN PAGES — confirmed net-new
│   ├── observability/          # mostly LINKS into references/observability.md
│   └── the-queue/              # mostly OWN PAGES — confirmed net-new
└── training/
    ├── playbook-adopting-sssf.md   # copied verbatim, path-adjusted links checked
    ├── playbook-adopting-sssf.pdf  # copied verbatim
    └── site-starlight/             # sssf-learn moved here per the superseded
                                     #   plan's Phase 1 mechanics, PLUS chapters
                                     #   3-7 scaffolded (full + stub per the
                                     #   scoping decision above)
```

## Process from here (as requested)

1. ~~Plan~~ — this document.
2. **Critique** — fable agent, adversarial, same discipline as the prior
   consolidation-plan critique: verify the concept inventory and gap analysis
   against the actual source files (not just trust the two research passes),
   check the scoping decision is defensible, look for anything this plan missed.
3. **Isolated test implementation** — build the workspace above, applying the
   superseded plan's Phase 1 mechanics for the site move, plus the new
   reference/ glossary and training/ chapters 3-7 scaffold, per the scoping
   decision.
4. **Fable review** of the test implementation — does it actually read well, is
   the navigation sound, does the sample content meet the bar a full lesson
   should hit.
5. **Critique** — fold review findings back in, fix what's wrong.
6. **Test the learning materials with test scripts** — `npm run build` must
   succeed with zero broken links/zero Astro errors; a link-checker pass over
   every internal cross-reference; confirm the reference glossary's every
   concept from the inventory has a real page (no silent drops); confirm the
   playbook PDF opens and its cross-references into the reference glossary (if
   any get added) resolve.
7. **Publish-ready delivery** — once 3-6 pass, apply the SAME changes for real
   to `super-simple-software-factory` (not the throwaway workspace) and to
   `sssf-learn` (deleted, per the original consolidation plan, only after the
   real fork copy is verified working).

## Definition of done

### This pass (plan + critique + isolated test implementation)
- [x] Plan critiqued by fable (`a9afe766faa44234c`), findings folded in (v0.2)
- [x] Isolated test implementation built at
      `/Users/alexei/Projects/training/_scratch/docs-training-test/`
      (git-init'd, not `/private/tmp`), not touching the real fork or `sssf-learn`
- [x] `docs/reference/concept-manifest.md` written: 80 concepts, each marked
      link-vs-own-page with a source citation (37 link / 43 own-page after
      review-driven reclassification)
- [x] `docs/reference/`: every manifest row resolved — either a working relative
      link into `.claude/skills/sssf/references/*.md` (left in place, not moved)
      or a real own-page for what those 3 files don't cover
- [x] `docs/training/playbook-adopting-sssf.md`+`.pdf` present, hash-verified
      against the fork originals
- [x] `docs/training/site-starlight/`: chapters 1-2 unchanged (byte-diff clean
      against `sssf-learn`), chapters 3-7 scaffolded (2 full new lessons + 16
      honest stubs, all with the TODO marker) + 10 full reference pages
- [x] `npm run build` succeeds on the test workspace's Astro site, zero errors
      (58 pages) — verified twice: once as the site-move baseline, once again
      after chapters 3-7 landed
- [x] Fable review of the test implementation completed (`a6173d4265a575410`),
      findings folded in: fixed stale `adw_watch.py` line-number citations
      across 3 reference pages, a manifest total-count error (46/34, not
      51/29), 9 dead-end "link" rows reclassified to "own-page", Console's
      Category-column drift, 2 broken scratch-workspace-only relative links,
      a stale bold-`Status:` claim in the bootstrap lesson that directly
      contradicted this session's own earlier fix, an unrendered mermaid
      fence, and a misattributed quote in the queue lesson. One review
      finding (the "none (explanation)" Blocked-by example) was independently
      re-verified and found to be CORRECT as originally written, not a bug —
      see the fix commit's message for the trace. `npm run build` re-verified
      clean (58 pages, 0 errors) after all fixes.
- [x] Test scripts run: `scripts/docs-check/{check_reference_manifest,
      check_markdown_links}.py`, wired to `just docs-check`. Both pass:
      36/36 link rows, and (as of the citation-cleanup pass) 73 real
      markdown links checked, up from 2.

### Follow-up discovered during this pass — fixed 2026-09-24 (commit `aae7aa8`)
- [x] **Real bug in `adw_watch.py`'s `read_blocked_by()`**: a `Blocked by:`
      value shaped like `(none — reason, with an internal comma)` failed
      to resolve to "no blocker" — the value got split on commas BEFORE the
      parenthetical-stripping regex ran, so a comma inside the explanation
      broke the parenthetical into two unmatched fragments before either could
      be recognized as `none`. Fix: strip the parenthetical from the whole
      matched value first, then split on commas. Two regression tests added
      (`test_watch.py`); full suite (49 tests) passes via
      `uv run --with pytest pytest .claude/skills/sssf/templates/adws/tests/test_watch.py`.

### Step 7 — real-fork application (done, 2026-09-24)
- [x] Test scripts written for real: `scripts/docs-check/{check_reference_manifest,
      check_markdown_links}.py`, wired to `just docs-check`. Both genuinely pass
      against the isolated workspace, verified by running them (not inspection) --
      caught and fixed a real regex bug (false "authored" matches), a real citation
      bug (`ignored_field_warnings` pointed at config source, not a doc), and 4 real
      anchor typos (double-hyphen slugs) along the way.
- [x] `docs/reference/` and `docs/training/` applied to the real fork (commits
      `db87e15`, `4cac036`), root `justfile` added (`training-*` recipes +
      `docs-check`), `.gitignore` updated, `learn/` removed
      (confirmed disposable, see `docs/training/retirement-notes.md`)
- [x] `just training-install` + `just training-build` run for real from the fork:
      58 pages, 0 errors
- [x] `just docs-check` run for real from the fork after commit: both checks pass
- [x] Pushed to `origin/main` (`4cac036`)
- [x] `sssf-learn`'s local clone removed -- GitHub (`ff8d696`) re-confirmed reachable
      and matching local before deletion; GitHub repo itself untouched
- [x] Isolated test workspace (`_scratch/docs-training-test/`) removed, its job done

### Step 8 — full content authoring + citation cleanup (done, 2026-09-25)
- [x] All 18 net-new lesson files authored in full (2 were already done as
      the v1.0 sample; the true count was 18, not the "17" v1.0 claimed --
      corrected during this pass). 9 parallel fable agents, each grounded
      in real source before writing.
- [x] Re-audited the "34 unauthored own-page rows" claim first: most were
      already covered *inside* one of the 10 sample pages (e.g.
      `Permissions-and-writes.md` alone answers 6 rows, `Gate.md` 9,
      `Dark-factory.md` 9). Only 13 rows had no real answer anywhere --
      those 13 authored by 4 parallel fable agents. All 44 own-page rows
      now resolve to a real answer (23 as dedicated pages, 21 bundled).
- [x] Opus adversarial review of all new content: 6 real findings (2 stale
      claims left over from bug fixes made earlier in the session, 1 dead
      link, 1 code-comment gap, 3 false cross-driver claims in
      `ToolCallTracker.md`), all fixed and verified against source directly
      before merging, not trusted on the reviewer's word alone.
- [x] Citation cleanup pass: ~150 file:line citations across all 23
      `docs/reference/` pages + `concept-manifest.md` verified against
      real current source; 16 had drifted and are fixed. Stale
      `gate() -> list[str]` signature in `SKILL.md:66` fixed to `GateReport`.
      ~40 backticked cross-reference paths converted to real
      `[text](path)` markdown links (`check_markdown_links.py`: 2 -> 73
      real links found).
- [x] `npm run build` clean (58 pages, 0 errors) and both `docs-check`
      scripts passing after every commit in this step.
- [x] Merged to `origin/main` across 2 commits (`f7ce5ec`, `a272ec8`),
      each on its own branch, reviewed and spot-verified before merging.

### Explicitly NOT done (genuinely remaining, unrelated to content completeness)
- [ ] `training/`'s screencast scripts -> `03-screencasts` conversion (Phase 2 of
      the site-move mechanics, Open Question 2 -- deliberately deferred, `training/`
      is untouched)
- [ ] The `docs/training/`-internal course pages (11 files: MISSION/NOTES/
      CONTRIBUTING/README/justfile/plans/site's own mission-notes-index) that still
      say "sssf-learn" in historical prose -- left as-is per the plan's own
      "leave as historical narrative" allowance, not a functional break

## Version history

| Version | Date | Changes |
|---|---|---|
| 2.0 | 2026-09-25 | Status: done. Step 8: all 18 net-new lessons and all 13 genuinely-missing reference pages authored (9 parallel fable agents), opus-reviewed (6 findings fixed), citation-cleaned (16 drifted citations fixed, SKILL.md's stale gate signature fixed, ~40 cross-references turned into real clickable links). Corrected the lesson-count arithmetic again (18, not 17) and the reference-gap arithmetic (13 genuine gaps, not 34 -- most "unauthored" rows were already covered inside a sibling page). Only genuinely remaining items: the deferred `training/`-screencast conversion and 11 files with historical "sssf-learn" prose, both explicitly out of scope by design, not oversights. |
| 1.1 | 2026-09-24 | Fixed the `read_blocked_by()` comma-inside-parenthetical bug tracked as an open follow-up in v1.0 (commit `aae7aa8`): stripped the parenthetical from the whole matched value before splitting on commas, added 2 regression tests, full 49-test suite passes. |
| 1.0 | 2026-09-24 | Step 7 (real-fork application) done: wrote and ran the standing test scripts for real (`scripts/docs-check/`, wired to `just docs-check`), found and fixed a fresh batch of real bugs running them (a regex over-match, a genuine citation-shape error, 4 anchor typos); applied `docs/reference/` and `docs/training/` to the real fork in two coherent commits, added the root `justfile` (`training-*` recipes) and `.gitignore` rules, removed `learn/`; `npm install`/`npm run build` run for real from the fork (58 pages, 0 errors); pushed to `origin/main`; removed `sssf-learn`'s local clone only after re-confirming GitHub still has the full history; removed the now-done isolated test workspace. Marked `in-progress` rather than `done` -- the explicit follow-ups (remaining lesson/reference authoring, the `read_blocked_by()` bug, the screencast conversion) are real, tracked, and none of them were silently claimed complete. |
| 0.3 | 2026-09-24 | Isolated test implementation built (3 builder passes: site move + baseline build, reference glossary, chapters 3-7 scaffold) and reviewed by a fable pass (`a6173d4265a575410`), which found several real issues — most notably a stale claim in the bootstrap lesson directly contradicting this session's own earlier `adw_watch.py` fix, and a genuinely new follow-up bug in `read_blocked_by()` discovered while verifying one of the review's findings (a comma inside a "none (explanation)" parenthetical still breaks resolution). All findings fixed except the new bug, which is tracked as an explicit follow-up. `npm run build` clean (58 pages) after fixes. Not yet: automated test scripts (link-checker, concept-completeness check) as standing scripts, and step 7 (real-fork application + `sssf-learn` deletion) — both still open, pending go-ahead. |
| 0.2 | 2026-09-24 | Revised per fable critique (`a9afe766faa44234c`): fixed 2 citation errors (sssf.config.yaml's real path; Visualizer is an app, not a module class) and a category-count label error (7, not 6); marked categories 5 (gates/permissions) and 7 (the queue) as NET-NEW rather than "reorganize existing" (confirmed near-zero coverage in references/*.md); resolved the references/*.md fate as LINK-not-move (moving breaks SKILL.md's citations, copying creates divergence — the exact problem this project exists to fix); added an explicit fork-glossary-vs-course-reference rule to prevent a second duplication; swapped the Ch4 "reading real cost" sample lesson (found to mostly duplicate existing lesson 0008) for a Ch6 "bootstrap vocabulary" pick that exercises the prose->lesson conversion for real; added the 75-row concept-manifest as a required pre-build artifact so "every concept has a page" is actually checkable; moved the isolated workspace off /private/tmp (macOS periodic cleanup risk) to a git-init'd _scratch/ directory. |
| 0.1 | 2026-09-24 | Initial plan, superseding `2026-09-24-consolidate-learning-content.md`'s target layout (docs/handbook -> docs/training, thin-pointer reference -> full concept glossary). Grounded in two fable research passes: a ~75-concept inventory and a gap analysis finding ~20 net-new lessons needed across 5 new chapters. Not yet critiqued or executed. |
</content>
