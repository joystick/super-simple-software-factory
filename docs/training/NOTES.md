# Notes

Working notes on how this learner wants to be taught. Merged from both source courses;
observations are kept attributed to the chapter where they surfaced, since some are
chapter-specific (toolchain, workspace layout) and some are general.

## General preferences (both chapters)

- **Verify, do not assert.** The reaction to every claim was "prove it." Lessons must run
  their own examples before publishing; a claim that turns out wrong is corrected
  visibly, not quietly.
- **Sharp edges stay in.** Cost, traps, and known failure modes are wanted, not softened.
- **Recommendations, not menus.** When offered options, the recommended one is usually
  taken. Lead with a recommendation and say why.
- **Answers honestly when they do not know.** Said "i don't know, teach me the basics"
  rather than bluffing — the single most useful trait a learner can have, and it should be
  met with actual teaching, not reassurance.
- **Responds extremely well to demonstration.** Every concept that landed, landed when it
  was executed in front of them. Prefer running a thing over explaining it.
- **Overclaims slightly when summarising.** "The gate works" drifted into "the code
  works." Worth catching each time — it is the same drift that makes a green trace feel
  like evidence.

## Chapter 1 (SSSF fundamentals) observations

- **Label-matching under pressure.** Twice reached for a recently-taught label instead of
  reasoning from mechanism:
  - Applied the pipe/exit-code hazard, taught thirty seconds earlier, to an unrelated
    question about detection. *Recency capture.*
  - Picked the first row of a diagnosis table for a both-red result, which was actually a
    different row.
  Counter: ask "what is this tool's *job*" before asking what to conclude. Force the
  mechanism, not the label.
- **Constraint discovered mid-course: the learner is not a Python developer.** SSSF is
  written in Python but their own work is TypeScript. Consequence for every lesson here:
  **teach the gate thinking, supply the Python.** Quizzing on Python syntax (e.g.
  `node.returns` semantics) taught nothing about verification and cost time — steering
  them toward a line that does not exist (`ast.RetunType`) was a teaching error, not a
  learner error. The decisions worth their attention are the ones that survive a change of
  language: what to check, what a note must tell the agent, what a gate cannot promise.
  This is also the whole reason Chapter 2 exists — TypeScript is the learner's actual
  language, and gates deserved to be taught there directly, not just translated.
- Workspace lives in `chapters/01-sssf-fundamentals/` (originally `sssf-play/learn/`)
  rather than the target repo root, so the course does not scatter directories through a
  working project.
- Assessment before authoring: the dialogue set the zone of proximal development, and the
  lesson was written afterwards to fix what the questions exposed. Do this again.
- "Do I have to wire gates BEFORE prompting?" was asked unprompted — the sign an
  objective landed. Answer: wired *and watched failing*. Behind an unverified gate a good
  prompt only produces unchecked work faster.

## Chapter 2 (gates deep dive / TypeScript) observations

- **Toolchain: Deno**, therefore `deno fmt` / `deno lint`. No Biome, ESLint or Prettier —
  standing project rule.
- Workspace was deliberately a sibling repo (`pricing-ts`, now folded into this course as
  Chapter 2's source), not nested inside `sssf-play`: pointing a factory at a TS repo
  needs a separate repo, and nesting a Deno project inside a Python one would confuse both
  toolchains' gates. That reasoning still applies to why *this course* now lives in its
  own sibling directory (`sssf-learn/`) rather than inside either source repo.
- Specs are handed over as failing tests; the learner implements. The Python original
  (`sssf-play/app/pricing.py`) is reference to consult *after* an attempt, never before.
- Quiz answers are authored to equal length so formatting leaks no clues.
- The clamp bug and the binary-representable-percentage bug were handed over as specs
  (failing tests), not as anecdotes — matches the "run it, don't explain it" preference
  above.

## Open threads

- **Chapter 1, objective 2** (reading a trace) is the natural next lesson. The hook:
  `sssf.db` records cost, phases and tool calls faithfully, and cannot record whether any
  of it meant anything.
- **Unspent demonstration** (Chapter 1): running a real `just sdlc` with a deliberately
  dead test gate in a copy of `pricing-ts`, to watch the factory commit a bug and certify
  it 5/5. Costs roughly $0.60–£1. The most convincing artefact available for objective 1
  and was deliberately left unspent — offer it before objective 2.
- **Chapter 2** is fully done (all four objectives); nothing outstanding there beyond
  what its own lessons already close out.
- **Parked (2026-08-27): a possible Chapter 3** — a practical lesson on running SSSF
  against an existing Next.js + Expo Turborepo (a real monorepo, not a from-scratch
  target like Chapters 1–2). Not started. Open questions to resolve before writing it:
  where `quality.py`'s gate commands point in a multi-app/multi-package workspace, what
  `protected_files` should cover across a Turborepo's shared packages, and whether one
  `sssf.config.yaml` roster can sensibly cover both the Next.js web app and the Expo
  native app or whether it wants two.

## Version history

| Version | Date | Changes |
|---|---|---|
| 2.1 | 2026-08-27 | Parked a possible Chapter 3: SSSF on an existing Next.js + Expo Turborepo. |
| 2.0 | 2026-08-27 | Merged `sssf-play/learn/NOTES.md` and `pricing-ts/NOTES.md` into this file, split into general vs. chapter-specific observations. |
