---
title: docs/reference — the SSSF concept glossary
---

# docs/reference

This is the complete, standing glossary of SSSF concepts. Every core
component — ADW, Gate, Envelope, Phase, Roster, `coding_agent`, the queue's
Frontier, and everything else in `concept-manifest.md` — has a real answer to
"what is X in SSSF" reachable from here. Start at `concept-manifest.md` for
the full 80-row index; the seven subdirectories below mirror its categories.

1. `core-execution-model/` — ADW, Session, Phase, chains, the four-param rule.
2. `handoff-and-output/` — Envelope, typed-output rule, session layout.
3. `agent-configuration/` — Roster, `defaults` merging, `coding_agent`, tools.
4. `coding-agent-drivers/` — the four driver modules (`agent_pi`, `agent_cc`,
   `agent_agy`, `agent_opencode`) and their shared surface.
5. `quality-gates-and-permissions/` — Gate, GateReport, Rule zero, `writes`,
   `protected_files`, `snapshot()`/`enforce()`, PermissionBreach.
6. `observability/` — Tracer, EventRecord, the Visualizer app.
7. `the-queue/` — dark factory, `just watch`, Frontier, triage states.

## The link-vs-own-page rule

Three files already document parts of this system well:
`.claude/skills/sssf/references/config.md`, `handoff.md`, and
`observability.md`. They are **skill-internal specs**, cited by name from
`SKILL.md` itself, and they stay exactly where they are — moving them would
break `SKILL.md`'s citations, and copying them would create two divergent
answers to the same question, which is the exact problem this glossary exists
to prevent.

So this `docs/reference/` tree does two things, and the manifest marks every
row with which one applies:

- **Link.** For a concept those three files already explain well (most of
  categories 1–4 and 6), the glossary entry is a link straight into the
  relevant section of `config.md`, `handoff.md`, or `observability.md`, with
  just enough local framing to say why the concept matters and where it sits
  relative to its neighbors. `agent-configuration/Defaults-merging.md` and
  `handoff-and-output/Session-layout.md` are worked examples of this — short
  pages that mostly say "see references/config.md's Defaults merging
  section," proving the link reads as a real answer, not a dead end.
- **Own page.** For a concept those three files don't cover — confirmed by a
  fable critique pass that found near-zero hits for `always_writable`,
  `PermissionBreach`, `Rule zero`, `Console`, or `Frontier` anywhere in
  `references/*.md` — this glossary carries a real, newly written page,
  cited directly against the source module. Categories 5
  (`quality-gates-and-permissions/`) and 7 (`the-queue/`) are almost entirely
  own-page for this reason: gates/permissions and the dark-factory queue are
  net-new documentation, not a reorganization of something that already
  existed.

A reader should never hit a dead end: every row in `concept-manifest.md`
resolves to either a working relative link or a real page.

## Fork glossary vs. course-internal reference

`sssf-learn`'s own `01-sssf-fundamentals/reference/` and
`02-gates-deep-dive/reference/` pages (Verifying a Gate, Gate Cookbook, Deno
Gates, Types and Contracts, etc.) are lab-specific how-to material — they stay
inside `docs/training/site-starlight/` unchanged, and they are **not**
glossary entries.

**Rule: this `docs/reference/` tree is the canonical "what is X" answer.**
The course's own reference pages should link IN here for term definitions
("a Gate, defined in `docs/reference/quality-gates-and-permissions/Gate.md`")
rather than ever redefining a term independently. If you are writing a lesson
or a lab page and find yourself explaining what a concept *is* rather than
how to *use* it in that lab's context, that explanation belongs here, not
there — link to it instead.

## What this pass built

Per the governing plan's scoping decision, this pass fully authors a
representative sample of the 44 own-page rows (36 link / 44 own-page,
corrected by a fable review pass and this workspace's own link-checker
script — see `concept-manifest.md`'s "Totals" section for why), not all of
them:

- `quality-gates-and-permissions/Gate.md`
- `quality-gates-and-permissions/Permissions-and-writes.md`
- `quality-gates-and-permissions/Rule-zero.md`
- `quality-gates-and-permissions/Console.md`
- `the-queue/Frontier.md`
- `the-queue/The-queue-watcher.md`
- `the-queue/Dark-factory.md`
- `observability/Visualizer.md`
- `agent-configuration/Defaults-merging.md` (worked link-example)
- `handoff-and-output/Session-layout.md` (worked link-example)

Every other own-page row in the manifest is tracked as follow-up work, not
claimed done by this pass. The manifest itself (`concept-manifest.md`) is
complete for all 80 concepts regardless — resolution status (link vs.
own-page) is recorded for every row even where the own-page isn't written
yet.
