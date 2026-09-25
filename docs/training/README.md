# SSSF Training

The `/teach` course on operating SSSF, originally consolidated from two source repos
(as "the standalone course repo") into one place, and moved here 2026-09-24 — see
`plans/2026-09-24-docs-reference-and-training.md` in the fork root for why. See
[`MISSION.md`](MISSION.md) for objectives and [`NOTES.md`](NOTES.md) for how this
learner learns.

## Reading it as a book

This directory is an [Astro Starlight](https://starlight.astro.build) site in `site-starlight/`:
a global left-hand sidebar over the whole book (chapters → lessons, reference, learning
records) with a right-hand "On this page" table of contents. Lessons are MDX with an
interactive quiz island; nothing is served via iframe.

```bash
just install   # one-time: install site deps
just serve     # dev server with hot reload at http://localhost:4321
just build     # production build into site-starlight/dist
```

## Layout

```
the standalone course repo/
├── MISSION.md              merged mission — both chapters, in one sequence
├── NOTES.md                merged teaching notes — general + per-chapter
├── justfile                install / serve / build / preview recipes
└── site-starlight/         the Astro Starlight book
    ├── astro.config.mjs     site config + chapter sidebar
    └── src/
        ├── components/      Quiz.astro (interactive island), Callout.astro
        └── content/docs/
            ├── index.mdx    homepage
            ├── mission.md, notes.md
            ├── 01-sssf-fundamentals/   operating SSSF in general (Python, the Python playground repo)
            │   ├── lessons/  reference/  learning-records/
            └── 02-gates-deep-dive/      gates as the cornerstone, taken deep (TypeScript, the TypeScript rebuild repo)
                ├── lessons/  reference/  learning-records/
                └── resources.md         external sources specific to this chapter (Deno/TS)
```

## Why two chapters, not two courses

Gates are the cornerstone of the whole factory — everything else rests on the guarantee
that a claim was checked, not merely reported. Chapter 1 introduces that guarantee and
its two gate families in the playground's native language (Python). Chapter 2 does not
introduce a new topic; it re-proves the same guarantee in a second language end to end —
domain modelling, porting, TDD — so the lesson is shown to survive a change of toolchain
rather than being an artifact of one.

Read them in order. Chapter 2 assumes Chapter 1's vocabulary (gate, envelope,
`quality.py`, "watched failing") without re-explaining it.

## Where the code these lessons are about actually lives

This directory holds course material only — no application code. The lessons reference
and were built against:

- the Python playground repo — the Python playground: skill source, stamped
  factory, and the cart-pricing target app the fundamentals chapter uses.
- the TypeScript rebuild repo — the Deno/TypeScript rebuild of the same pricing
  engine, with its own stamped factory, used by the gates-deep-dive chapter.

Both remain independent, runnable repos. Nothing here duplicates their code — only the
teaching material that was previously split between `the Python playground repo/learn/` and
`the TypeScript rebuild repo/{lessons,reference,learning-records}/` has moved here.

## Related: video screencast scripts (`training/` at the fork root)

There is a second, separate body of SSSF training material at the fork root, `training/`
(not under `docs/`) — ten timed screencast scripts (`ep01`–`ep10`) plus `asciinema`
terminal recordings, meant for producing narrated video content, not for reading as
lessons. **This is deliberately not folded into this Astro course**, resolving an open
question from the site-move plan (`plans/2026-09-24-docs-reference-and-training.md`):
a check of the episode scripts against this course found heavy topical overlap — e.g.
Episode 9 ("Coding agents, cost, and control") covers almost exactly the same three
things as this course's own `04-coding-agents-and-cost/` chapter, citing many of the
same source lines. Converting the episodes into a duplicate `03-screencasts` MDX
chapter would violate the same "link, don't duplicate" principle this glossary and
course apply everywhere else (see `docs/reference/README.md`'s link-vs-own-page rule).

`training/README.md` carries the full episode index and its own cross-reference back to
this course's chapters. The two stay independent artifacts on purpose — this course
teaches by reading and doing; `training/`'s scripts teach by watching, and are written
for a narrator's voice, not a reader's pace.

## Version history

| Version | Date | Changes |
|---|---|---|
| 2.1 | 2026-09-25 | Added the "Related: video screencast scripts" section, resolving the site-move plan's deferred "Open Question 2" (whether `training/`'s screencast scripts should become MDX lessons here): they stay a separate artifact, per the real topical-overlap check documented there. |
| 2.0 | 2026-08-28 | Rebuilt as an Astro Starlight site in `site-starlight/`: global left sidebar over the whole book, right-hand TOC, MDX lessons with an interactive quiz island — replacing the iframe-based Docsify book. Removed the Docsify shell, `_sidebar.md`, `assets/`, `tools/gen-docsify.py`, and the standalone `chapters/**/*.html` (content ported into `src/content/docs/`). |
| 1.1 | 2026-08-27 | Reformatted as a Docsify book — CHM-style left TOC drawer over the existing lesson/reference HTML, served as-is via iframe wrapper pages. `_sidebar.md` and the wrappers are generated by `tools/gen-docsify.py`. |
| 1.0 | 2026-08-27 | Course extracted from `the Python playground repo/learn/` and `the TypeScript rebuild repo/{lessons,reference,learning-records}/` into this single sibling directory, organized as two chapters. |
