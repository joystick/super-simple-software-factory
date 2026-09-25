---
title: Retirement notes
---

# Retirement notes

Records what happened to prior learning-content locations during the
`docs/reference` + `docs/training` consolidation (see
`plans/2026-09-24-docs-reference-and-training.md` in the fork root for the
full plan, critique, and review history). Kept here so `git log`'s trail on
the removed directories stays discoverable from `docs/` — a reader who
notices `learn/` no longer exists shouldn't have to go spelunking through
`git log --all` to find out why.

## `learn/` — removed, 2026-09-24

A one-off, orphaned interactive HTML course on gates (2 lessons, 3 reference
pages, 2 learning-records, its own CSS/JS quiz engine), parked after lesson 1
of 4 objectives, single commit (2026-08-27) — never merged into anything.

**Confirmed fully disposable before removal**, not assumed: a fable review
pass ran a normalized-text diff of all 3 `learn/reference/*.html` pages
against the standalone course repo's (now `docs/training/site-starlight`'s)
`01-sssf-fundamentals/reference/000{1,2,3}-*.mdx` counterparts. Body prose,
examples, and code blocks were identical; the only differences were HTML-only
chrome (nav links, `<title>`, one tagline/subtitle per page) and MDX-only
frontmatter. `learn/learning-records/*.md` were likewise identical modulo
Starlight frontmatter. No unique content was lost.

## The standalone course repo — moved into `docs/training/site-starlight/`, 2026-09-24

Was its own separate GitHub repo (name withheld from this doc on purpose — this
fork's documentation does not name or path to other repos) — a live,
actively-maintained Astro Starlight course (24 commits, quizzes, a Piper TTS
narration pipeline) consolidating the Python playground repo's `learn/`
(Chapter 1) and the TypeScript rebuild repo's contents (Chapter 2).
Relocated wholesale — kept fully functional, not flattened to plain markdown
(an earlier direction for this consolidation, reversed before any execution) —
via an ignore-aware copy (excluding `node_modules/`, `dist/`, `.astro/`,
`public/audio/`, `.env.production`), byte-hash-verified against the source
before any path/config edit touched the copy.

**Expanded, not just moved**: the site's original two chapters only reached
"gates deep-dive." A gap analysis found ~20 net-new lessons needed across 5
new chapters (`03-adopting-a-factory` through `07-the-queue`) to reach the
full "basic prompt → dark factory" arc this consolidation set out to cover.
This pass scaffolded all 5 new chapters (real files, real navigation) and
fully authored 2 sample lessons proving the mechanism works — the rest are
honest stubs (a real page, a one-paragraph summary drawn from the gap
analysis, and a `<!-- TODO -->` marker), tracked as explicit follow-up work,
not silently claimed complete.

The GitHub repo itself was **not** deleted — only the local clone was
removed, after its last commit
(`ff8d696`) was confirmed pushed. Deleting the GitHub repo is a separate,
more irreversible decision, out of scope for this consolidation.

## `training/` (repo root, screencast scripts) — untouched, not yet retired

10 screencast-production scripts + 8 asciinema recordings, frozen since
2026-08-25. **Deliberately not touched by this pass** — converting these into
the new `03-screencasts`-shaped content (or deciding they should stay as
producer material referenced from, not absorbed into, the course) was scoped
out as its own follow-up, not mixed into the mechanical site-move. See the
governing plan's "Open Question 2" for the undecided part.
