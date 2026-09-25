---
type: Comparison
title: Pocock skill matrix
description: >-
  GoF-pattern-style catalog of every skill in the fresh upstream clone (37)
  plus the locally installed skills with no fresh-clone equivalent (10).
tags: [pocock, skills, catalog, comparison]
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
stale_after: 2026-12-12
sources:
  - id: fresh-clone
    resource: downloads/skills/skills/
    title: Fresh clone skill catalog (37 SKILL.md files, parsed 2026-09-12)
  - id: local-install
    resource: ~/.claude/skills/
    title: Locally installed skill set
---

# Pocock skill matrix

Method: every `SKILL.md` in both snapshots was parsed programmatically
(frontmatter `description` and `disable-model-invocation`, body
cross-references, bundled reference files); the load-bearing ones were also
read in prose. **Interactive/Headless** reports two things: the frontmatter
invocation policy (`user-invoked` = `disable-model-invocation: true`, only a
human can fire it; `model-invoked` = model or human), and a behavioral
judgment of whether the protocol *text* could run unattended if attached to
a headless agent's prompt (SSSF's vendoring strips invocation policy — it
copies body text into a system prompt, so the policy stops applying).

## Fresh clone — `engineering/` (18)

| Skill | Intent | Trigger | Mechanism | Collaborates with | Interactive/Headless | Notes |
|---|---|---|---|---|---|---|
| ask-matt | Route "which skill/flow fits my situation?" to the right skill | User asks for guidance | Read-only router over the whole catalog; main flow routes idea → `/to-spec` → `/to-tickets` → `/implement` | references nearly every skill | user-invoked; headless-safe (pure routing) | Bundles `PHASE-BOUNDARIES.md`; no local equivalent installed |
| code-review | Review changes since a fixed point on two axes (Standards, Spec) | "review this branch/PR/since X" | Spawns two parallel sub-agents; reads repo standards + originating issue/spec; reports side by side | setup-matt-pocock-skills (tracker config), sub-agents | model-invoked; headless-safe (read-only analysis) | Byte-identical to local copy; SSSF vendors it onto agents |
| codebase-design | Shared vocabulary for designing deep modules (Ousterhout) | Interface design, seams, testability discussions | Pure reference/vocabulary skill; no writes | consumed by tdd, improve-codebase-architecture, setup-ts-deep-modules | model-invoked; headless-safe | Bundles `DESIGN-IT-TWICE.md`, `DEEPENING.md`; not installed locally |
| diagnosing-bugs | Disciplined diagnosis loop for hard bugs/regressions | "diagnose/debug", something broken or slow | Hypothesis-driven loop with scripts; reads CONTEXT.md/domain docs | domain docs | model-invoked; headless-safe | Not installed locally |
| domain-modeling | Build/sharpen the project's domain model | Terminology discussions, writing CONTEXT.md or an ADR | Writes `CONTEXT.md` + `docs/adr/*` per bundled `CONTEXT-FORMAT.md`/`ADR-FORMAT.md` | composed by grill-with-docs, triage, wayfinder, improve-codebase-architecture | model-invoked; conversational but can run headless when input is settled | Byte-identical to local copy; produces SSSF's bootstrap artifacts |
| grill-with-docs | Relentless interview that also writes ADRs + glossary as it goes | Human types `/grill-with-docs` | One line: run `/grilling` using `/domain-modeling` — pure composition | grilling + domain-modeling | user-invoked; **interview needs a human** | 8 lines; identical to local. SSSF's bootstrap entry point; deliberately NOT vendored |
| implement | Execute a spec or ticket set | Human types `/implement` | Drives implementation off tickets; leans on tdd and code-review | tdd, code-review | user-invoked; protocol text is headless-plausible | New upstream; closest fresh equivalent to "now build it"; no local equivalent |
| improve-codebase-architecture | Find deepening opportunities, present visual report, grill through one | "improve architecture" | Sub-agent scan → HTML report → grilling session on the chosen item | codebase-design, domain-modeling, grilling | user-invoked; scan is headless-safe, grill phase is not | Byte-identical to local copy; the Medium article's "stage 5" |
| prototype | Throwaway prototype to answer a design question | Sanity-check a state model or UI feel | Builds on a `prototype/<name>` branch kept as runnable evidence (1.2.x change) | referenced by to-spec, to-tickets, wayfinder | model-invoked; headless-safe | Bundles `LOGIC.md`, `UI.md`; not installed locally |
| research | Investigate a question against primary sources, capture as repo markdown | "research this" | Read/fetch + write one findings file | referenced by wayfinder, implement-spec | model-invoked; headless-safe | Not installed locally |
| resolving-merge-conflicts | Resolve an in-progress merge/rebase | Conflict encountered | Procedural conflict-resolution protocol | — | model-invoked; headless-safe | Not installed locally |
| setup-matt-pocock-skills | One-time repo config: issue tracker, triage labels, domain-doc layout | Human runs it once per repo | Interview → writes `docs/agents/{issue-tracker,triage-labels,domain}.md` + `## Agent skills` section in CLAUDE.md/AGENTS.md | configures to-spec, to-tickets, triage, all domain-doc consumers | user-invoked; **interview needs a human** | The seam between Pocock-land and SSSF; local copy functionally identical (punctuation-only diff) |
| tdd | Red-green-refactor discipline | Build test-first, "integration tests" | Behavioral protocol; bundles `tests.md`, `mocking.md` | codebase-design, code-review | model-invoked; headless-safe | Byte-identical to local copy; SSSF vendors it onto the planner |
| to-spec | Turn the current conversation into a spec on the tracker — **no interview, just synthesis** | Human types `/to-spec` after grilling | Synthesizes conversation → publishes spec to configured tracker (`gh issue create` or `.scratch/<feature>/spec.md`), `needs-triage` state | setup-matt-pocock-skills, triage, prototype | user-invoked; **headless-safe by design** (explicitly non-interactive) | Successor of `write-a-prd`/`to-prd`; the interview moved out to grilling |
| to-tickets | Break plan/spec/conversation into tracer-bullet tickets with blocking edges | Human types `/to-tickets` | Writes one file per ticket (`.scratch/<f>/issues/NN-slug.md` locally) or native tracker issues with dependency edges | setup-matt-pocock-skills, triage, prototype | user-invoked; headless-plausible | Successor of `prd-to-issues`/`to-issues`; one-file-per-ticket rule is 1.2.x |
| triage | Move issues **and external PRs** through the triage state machine; write agent-ready briefs | "triage", "look at #42" | State machine over `needs-triage/needs-info/ready-for-agent/ready-for-human/wontfix`; grills when needed; writes durable agent briefs (`AGENT-BRIEF.md`) | setup-matt-pocock-skills (labels), grilling, domain-modeling | user-invoked (**new** — local copy is model-invoked); judgment steps want a human | Drifted from local: adds PR-as-request-surface, `disable-model-invocation: true` |
| wayfinder | Plan work too big for one session as a map of decision tickets on the tracker | Human types `/wayfinder` | Map + child decision tickets; frontier/claim/resolve mechanics; each ticket typed HITL or AFK | grilling, domain-modeling, prototype, research, setup-matt-pocock-skills | user-invoked; HITL tickets need a human, AFK tickets don't | Byte-identical to local copy; renamed from `decision-mapping` in 1.1.0; SSSF's queue reuses its map/claim/resolve mechanics |
| wizard | Generate a bash wizard walking a human through steps only they can do | Provisioning, credentials, dashboards | Writes an interactive script from `template.sh` | — | model-invoked; output is human-facing by definition | Not installed locally |

## Fresh clone — `in-progress/` (8, "beta channel, published on purpose")

| Skill | Intent | Trigger | Mechanism | Collaborates with | Interactive/Headless | Notes |
|---|---|---|---|---|---|---|
| claude-handoff | Hand the conversation to a fresh background agent that continues immediately | Human invokes | Compacts context via handoff, spawns background agent | handoff | user-invoked; the *successor* runs headless | |
| implement-spec | Implement a specification in code | Human invokes | Drives build from a spec; uses research + sub-agents; ends in code-review | code-review, research | user-invoked; headless-plausible | With `implement`, the closest fresh analog to SSSF's builder stage |
| loop-me | Grill about specs for workflows to build in this workspace | Human invokes | Grilling variant scoped to workflow-building | grilling | user-invoked; needs a human | Does NOT bridge grill→triage; it is another interview entry |
| retro | Retrospective on a coding session | Human invokes | Structured retro conversation | — | user-invoked; needs a human | |
| setup-ts-deep-modules | Enforce deep-module boundaries in a TS repo via dependency-cruiser | Human invokes | Writes dependency-cruiser config | codebase-design | user-invoked; setup is mechanical | |
| writing-beats | Assemble raw material into a journey of beats | Human invokes | Writing-process protocol | — | user-invoked; needs a human | |
| writing-fragments | Mine raw fragments, no structure yet | Human invokes | Writing-process protocol | grilling | user-invoked; needs a human | |
| writing-shape | Shape raw material into an article paragraph by paragraph | Human invokes | Writing-process protocol | grilling | user-invoked; needs a human | |

## Fresh clone — `misc/` (4) and `productivity/` (7)

| Skill | Intent | Trigger | Mechanism | Collaborates with | Interactive/Headless | Notes |
|---|---|---|---|---|---|---|
| git-guardrails-claude-code | Block dangerous git commands via hooks | "add git safety hooks" | Writes Claude Code PreToolUse hooks + scripts | — | model-invoked; setup is mechanical | |
| migrate-to-shoehorn | Replace `as` assertions in tests with shoehorn | Mentions shoehorn | Mechanical codemod protocol | — | model-invoked; headless-safe | |
| scaffold-exercises | Scaffold course exercise structures | Course authoring | Writes directory scaffolds | — | model-invoked; headless-safe | |
| setup-pre-commit | Husky + lint-staged setup | "add pre-commit hooks" | Writes hook config | — | model-invoked; mechanical | |
| grill-me | Relentless interview to sharpen a plan (no docs written) | Human types `/grill-me` | One line: run `/grilling` | grilling | user-invoked; **needs a human** | Identical to local; the Medium article's centerpiece |
| grilling | The actual grilling protocol | "grill me", stress-test my thinking | Question-tree interview engine; explores codebase instead of asking when it can | composed by grill-me, grill-with-docs, loop-me, triage, wayfinder, improve-codebase-architecture, writing-* | model-invoked; **needs a human to answer** | Identical to local; the collection's most-composed primitive |
| handoff | Compact conversation into a handoff doc for another agent | Human invokes | Writes one handoff document | claude-handoff | user-invoked; headless-safe output | Identical to local |
| teach | Teach the user a skill/concept in this workspace | Human invokes | Tutoring protocol with mission/glossary/learning-record formats | — | user-invoked; needs a human | Identical to local |
| to-questionnaire | Turn an unanswerable decision into a questionnaire for someone else | Human invokes | Writes a questionnaire document | — | user-invoked; headless-safe output | Not installed locally |
| wait-what | "That last message did not land — re-pitch it" | Human invokes | Re-explanation protocol | — | user-invoked; needs a human | Local copy near-identical (punctuation) |
| writing-for-agents | How to write documents for agents (skills, AGENTS.md) | Editing skills or agent docs | Reference + `SKILL-MECHANICS.md` | — | model-invoked; headless-safe | Not installed locally |

## Local-only skills (no fresh-clone equivalent)

The first five are **superseded Pocock generations** (see
[naming-drift](/pocock-skills/naming-drift.md)); the last five are **not
Pocock skills** — they ship from other sources and merely live in the same
`~/.claude/skills/` directory.

| Skill | Intent | Trigger | Mechanism | Collaborates with | Interactive/Headless | Notes |
|---|---|---|---|---|---|---|
| write-a-prd | Create a PRD through **user interview** + codebase exploration, submit as GitHub issue | "write a PRD" | Interview → PRD → `gh issue create` | — | model-invoked; **interview needs a human** | Oldest generation; GitHub-only; vendored into SSSF downstream repos |
| to-prd | Turn current conversation into a PRD, publish to the **configured** tracker | "create a PRD from this" | Synthesis (skips the interview if already grilled) → tracker publish | setup-matt-pocock-skills, triage, prototype | model-invoked; headless-plausible | Middle generation (tracker-agnostic); renamed upstream to `to-spec` with PRD language dropped |
| prd-to-issues | Break a PRD into grabbable **GitHub** issues, tracer-bullet slices | "PRD to issues" | Slices → `gh issue create` each | — | model-invoked; headless-plausible | Oldest generation; GitHub-only |
| to-issues | Break plan/spec/PRD into issues on the **configured** tracker | "convert plan to issues" | Slices → tracker publish with blocking edges | setup-matt-pocock-skills, triage, prototype | model-invoked; headless-plausible | Middle generation; renamed upstream to `to-tickets` |
| review | Two-axis review (Standards, Spec/PRD) | "review since X" | Parallel sub-agents, like code-review | setup-matt-pocock-skills, sub-agents | model-invoked; headless-safe | Older/parallel variant of `code-review` (which is also installed) — both live side by side locally |
| find-skills | Discover and install agent skills | "is there a skill for X" | Searches skill registries, installs | — | model-invoked; headless-safe | Not a Pocock engineering skill (skills.sh ecosystem helper) |
| okf | Author/maintain/consume OKF knowledge bundles | OKF work in a repo | Spec + templates + `okf_init.py` | validate, visualize | model-invoked; headless-safe | Not a Pocock skill; produced this bundle |
| validate | Deterministic OKF v0.2 conformance checker | "validate the bundle" | Runs `okf_validate.py` | okf | model-invoked; headless-safe | Not a Pocock skill |
| visualize | Render an OKF bundle as interactive HTML graph | "visualize the bundle" | Generates `viz.html` | okf | model-invoked; headless-safe | Not a Pocock skill |
| ubiquitous-language | Extract a DDD glossary from the conversation | "define domain terms" | Writes `UBIQUITOUS_LANGUAGE.md` | — | user-invoked; headless-plausible | Not a Pocock skill; overlaps conceptually with domain-modeling |

## Also relevant: `prd-to-plan` (exists in **neither** snapshot)

`prd-to-plan` — "turn a PRD into a multi-phase implementation plan saved in
`./plans/`" — appears only as a **hand-authored, header-less file** in SSSF
downstream repos' `adws/adw_data/skill_engineering/`. It is not in the fresh
clone, not in `~/.claude/skills/`, and carries no vendoring provenance
header. See [naming-drift](/pocock-skills/naming-drift.md).
