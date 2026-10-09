<!-- sssf:vendored
source: ~/Projects/training/super-simple-software-factory/downloads/okf-skills/skills/okf/SKILL.md
date: 2026-10-09
sha256: ad4a2d130643816d579f9c394ee1bffa8881a42ed6dc17e4ff75fa3cb0ff272a
-->
<!-- sssf:flattened
kept: templates/concept.md sha256:0d70e0f313b2019c8c1a6deb591d3929b60690fa41c345145fb18de8eaf82c4d
kept: templates/index.md sha256:fca29f13b7ac2b3c455cdce19edf518392bb5fed15b1b903e05c8a715c772880
kept: templates/log.md sha256:f5e352d5c2d017ebe135d92684334905cf4797f82bb91765605552596cc81c55
dropped: reference/SPEC.md -- OKF v0.2 spec, 1016 lines (~12k tokens/turn), Apache-2.0; the body already summarizes the hard rule, conventions and v0.2 families, and the deterministic validator decides conformance
dropped: reference/APACHE-2.0.txt -- license of the dropped SPEC.md; nothing vendored is under it
dropped: scripts/okf_init.py -- tool runner, not prompt content; the repo's .okf/ bundle already exists
dropped: SKILL.md "Always read the canonical spec ... [reference/SPEC.md]" paragraph -- spec not vendored; rewritten to say the rules summarize the spec, the validator decides conformance, and the §N labels match the validator's messages
dropped: SKILL.md "Templates to copy" links -- templates merged below; line rewritten to point at "Templates"
dropped: SKILL.md produce "init fast-path" paragraph and okf_init.py code block -- tool not vendored; bundle already exists
dropped: SKILL.md produce step 1 "Read [reference/SPEC.md]" -- rewritten to re-read the hard rule, conventions and v0.2 families above
dropped: SKILL.md produce step 4 [templates/concept.md] link -- rewritten to "the concept template (see Templates)"
dropped: SKILL.md Validation "/okf:validate" skill call and ${CLAUDE_SKILL_DIR} path -- no Skill tool or skill dir here; replaced with `uv run scripts/okf_validate.py .okf` from the repo root (repo copy of the validator)
dropped: SKILL.md Validation --strict guidance -- run without --strict: every ERROR must be resolved, warnings are soft (the bundle carries legacy v0.1 ones), clear them in concepts you touched
dropped: SKILL.md maintain step 2 "Facing a whole v0.1 bundle ... run the validator's `--migrate` once." sentence -- contradicts documenter system.md ("never run --migrate over the whole bundle"); the bundle's 80 legacy warnings would trigger it, and skill text composes after system.md so it would win
dropped: templates/*.md as files -- merged under "## Templates", one ### heading each, content verbatim in a markdown code fence (no heading demotion: the templates' headings and comment are content to copy)
-->

---
name: okf
description: >-
  Author, maintain, and consume Open Knowledge Format (OKF) knowledge bundles —
  portable markdown + YAML frontmatter that both humans and agents read. Use when
  capturing project knowledge (services, APIs, schemas, metrics, runbooks,
  decisions) into an OKF bundle, when updating one after code or docs change, or
  when a repository contains an `.okf/` (or other OKF) bundle that should inform
  the task. Triggers on: "document this in OKF", "update the knowledge bundle",
  "capture this as a concept", or any work in a repo that has an OKF bundle.
user-invocable: true
argument-hint: "[produce|maintain|consume] [path]"
allowed-tools: Read Write Edit Grep Glob Bash
---

# Open Knowledge Format (OKF) skill

OKF represents knowledge as a directory of markdown files with YAML frontmatter.
It is minimal by design: no schema registry, no runtime, no SDK. Your job is to
produce, maintain, and consume OKF bundles **conformant with the spec**, not your
memory of it.

The rules below summarize the canonical OKF v0.2 specification. Where they
leave a case open, the deterministic validator (see *Validation*) decides what
conforms. The `§N` labels name sections of that spec, and the validator's
messages cite the same labels.

## The one hard rule

A bundle is conformant (§11) iff: every non-reserved `.md` file has a parseable
YAML frontmatter block, and every such block has a **non-empty `type`** field.
Everything else is soft guidance. Consumers MUST tolerate missing optional
fields, unknown types, and broken links — never reject a bundle over them.

## Conventions to apply

- **One concept = one file.** The file path (minus `.md`) is the concept ID.
- **Frontmatter:** `type` is required. Add `title`, `description`, `tags` when
  they aid consumption; add `resource` (a canonical URI) only for concepts bound
  to a real asset — omit it for abstract concepts.
- **Body:** prefer structural markdown (headings, tables, lists, fenced code).
  Conventional headings: `# Schema`, `# Examples`, `# Computation`.
- **Cross-links:** standard markdown links; prefer absolute bundle-relative
  form (`/services/auth-api.md`). A link asserts a relationship; its *kind* lives
  in the surrounding prose, not the link.
- **Reserved files:** `index.md` (directory listing, no frontmatter, except the
  bundle-root index, which may carry `okf_version` and this plugin's
  `upkeep: enforced` opt-in flag) and `log.md` (ISO-dated history, newest
  first). Never use these names for concepts.
- **What goes in `log.md`:** lifecycle events only, written in the bundle-root
  `log.md`: a bundle **created**, a concept **deprecated** or retired, one
  concept **superseding** another, concepts **regenerated** after their source
  changed, a **verification** pass. Routine edits to a concept do not get an
  entry: its `generated` and git already record them. A log is append-only, so
  never rewrite or drop an existing entry.

## The v0.2 families (all optional, all worth filling)

- **Trust (§5.2):** `generated: { by, at }` — who produced the current content
  and when. `verified: [{ by, at }]` — who confirmed it since (a bare mapping is
  one entry). Write `by` in the **actor convention** (§7): `<producer>/<version>`
  for an agent, `human:<id>` for a person, `process:<id>` for an automated job.
  Use `human:` whenever a person authored or signed off — consumers key trust
  tiers off that prefix.
- **Lifecycle (§5.4–5.5):** `status: draft|stable|deprecated` (absent means
  stable) and `stale_after`, an absolute ISO 8601 datetime (a bare date is
  tolerated), not a TTL.
- **Provenance (§5.1):** `sources: [{ id, resource, title, author,
  usage_count, last_modified }]` plus a `usage_window: { from, to }` sibling of
  `sources` framing every `usage_count` (an entry may carry its own to override
  it); a `usage_count` without a window warns. `resource` is required per entry
  and may be a URL, a bundle path, or a scope descriptor. Attribute a specific
  claim with a markdown footnote whose label is the source's `id`:
  `…sharded daily.[^ga4-schema]` plus a `[^ga4-schema]: …` definition. The label
  is the join key, it must match a `sources[].id`.
- **Attestation (§10):** a sanctioned computation is its own concept,
  `type: Attested Computation`, carrying `runtime` (required), `parameters`,
  `executor`, `attester`, and the computation itself under `# Computation` (or a
  `computation:` path). Concepts that need the value link to it. Never inline a
  number's SQL into the concept that narrates it.

**Reading a v0.1 bundle?** Two constructs were superseded (§13.1): `timestamp`
is now `generated.at`, and a body `# Citations` list is now `sources`. Read both,
write v0.2 — and when you touch a legacy concept in **maintain** mode, migrate
its frontmatter as part of the edit. The validator warns on both.

Templates to copy for a concept, an `index.md`, and a `log.md` are under
*Templates* at the end of this skill.

## Default bundle location

Use `.okf/` at the repository root unless the project already uses another
location. Commit it alongside the code it describes — knowledge as code.

## Modes

### produce — create or extend a bundle

1. Re-read *The one hard rule*, *Conventions to apply*, and *The v0.2
   families* above. They are your working copy of the spec.
2. Pick the source(s): **code** (derive concepts from source, READMEs,
   docstrings, config), **docs/wiki** (distill pages into concepts, record the
   originals in `sources`), **manual** (decisions, playbooks, metrics).
3. Choose a directory layout by domain (e.g. `services/`, `datasets/`,
   `decisions/`). One concept per file.
4. Write each concept from the concept template (see *Templates*): set a
   descriptive `type`, fill recommended fields, record `generated` and the
   `sources` you actually read, cross-link related concepts.
5. Add/refresh `index.md` per directory (and `okf_version: "0.2"` in the root
   index). A new bundle gets a dated **Creation** entry in `log.md`. Extending
   an existing one does not.
6. Validate (see below). Fix every error before finishing.

### maintain — keep a bundle in sync with reality
1. Identify which concepts the change affects (search by `resource`, path, or
   topic). This bookkeeping is exactly what agents are good at — touch every
   affected file in one pass.
2. Update the body and `generated.at` (with your own actor in `generated.by`);
   fix or add cross-links; create new concepts for new assets; mark removed
   assets `status: deprecated` and note the deprecation in `log.md` rather than
   silently deleting context.
3. Update the relevant `index.md` files. Append a dated `log.md` entry only if
   the change is a lifecycle event (see *What goes in `log.md`*).
4. Validate.

### consume — use a bundle as context
1. Read the bundle-root `index.md` first for progressive disclosure, then follow
   links only into the concepts relevant to the task.
2. Weigh what you read: `status: draft`/`deprecated`, a `stale_after` already
   past, or no `verified` entry all mean "check before relying on this". Treat
   broken links as not-yet-written knowledge, not errors.
3. Need a number an `Attested Computation` covers? Run *its* computation with
   values bound to the declared `parameters` — never write your own query.
4. If you learn something durable while working, switch to **maintain** and
   write it back.

## Validation (do this before declaring done)

Never eyeball conformance — run the deterministic checker from the repository
root:

```bash
uv run scripts/okf_validate.py .okf
```

Resolve every `ERROR` (hard §11 failures); any one of them fails the run
(exit 1). Warnings do not fail the run, and concepts you did not touch may
still carry legacy ones. Clear the warnings in every concept you touched.

## Templates

### Concept template

```markdown
---
type: <Concept type, e.g. Service, BigQuery Table, Metric, Playbook, Decision>
title: <Human-readable display name>
description: <Single sentence summarizing the concept.>
resource: <Canonical URI of the underlying asset — omit for abstract concepts>
tags: [<tag>, <tag>]
status: stable                    # draft | stable | deprecated; absent means stable
generated: { by: <actor>, at: <ISO 8601, e.g. 2026-06-14T10:00:00Z> }
verified: { by: human:<id>, at: <ISO 8601> }   # omit until someone confirms it
stale_after: <YYYY-MM-DDTHH:MM:SSZ>   # omit when the content does not expire
sources:                          # what this was derived from; omit if nothing
  - id: <short-key>
    resource: <URL, bundle path, or scope descriptor>
    title: <Human-readable label>
    author: <actor>               # optional credibility signal
    last_modified: <YYYY-MM-DDTHH:MM:SSZ>   # when the source itself last changed
---

<!--
  Actors (§7): `<producer>/<version>` for an agent, `human:<id>` for a person,
  `process:<id>` for an automated job. Use `human:` whenever a person authored
  or signed off — consumers key trust tiers off that prefix.
-->

# Overview

<What this concept is and why it matters. Attribute a sourced claim with a
footnote whose label is a `sources[].id`.[^short-key]>

# Schema

<Use for assets with fields/columns; otherwise replace with relevant sections.>

| Field | Type | Description |
|-------|------|-------------|
|       |      |             |

[^short-key]: <Human-readable label of the source>
```

### `index.md` template

```markdown
# <Directory / Group Heading>

* [<Title>](<relative-url>) - <short description from the concept's frontmatter>
* [<Title>](<relative-url>) - <short description>

# <Another Group>

* [<Subdirectory>](<subdir>/) - <short description of the subdirectory>
```

### `log.md` template

```markdown
# Update Log

## <YYYY-MM-DD>
* **Creation**: <what was created> — [<concept>](<bundle-relative-path>).
* **Deprecation**: <what was retired, and what replaces it> — [<concept>](<bundle-relative-path>).
* **Supersession**: [<new concept>](<bundle-relative-path>) supersedes [<old concept>](<bundle-relative-path>). Affirmed by <actor>.
* **Regeneration**: <which concepts, after what source change> — [<concept>](<bundle-relative-path>).
* **Verification**: <what was verified, by whom> — [<concept>](<bundle-relative-path>).
```
