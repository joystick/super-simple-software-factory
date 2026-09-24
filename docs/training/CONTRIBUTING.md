# Contributing to sssf-learn

## Golden rule: preserve training material verbatim

Every piece of authored teaching content is valuable and must be preserved in
its **original form** through any migration, reformatting, or refactor. This
covers **all** of it, not just the body prose:

- lesson/reference prose, byte-for-byte
- tables, code samples, and command transcripts
- quiz questions, choices, and feedback text
- **lesson subtitles / taglines** — the one-line summary under each title
- callouts ("the win", "why", "trap", etc.)

Nothing may be dropped, summarized, paraphrased, or demoted to invisible
metadata. A subtitle that only lives in frontmatter and no longer renders on the
page counts as a **loss**, even though the text technically still exists.

### How to verify after any content change

1. Diff page **bodies** against the previous version — expect zero content
   differences (only frontmatter/imports may change for framework reasons).
2. Load each changed page and confirm every visible element still **renders**:
   title, subtitle, callouts, tables, and a working quiz.
3. If a framework forces a field into frontmatter (e.g. Starlight's
   `description`), also surface it **visibly**. In this project the lesson
   subtitle is re-rendered on-page by the `PageTitle.astro` component override
   in `site-starlight/src/components/` — do not remove it.

## Running the book

The book is an [Astro Starlight](https://starlight.astro.build) site in
`site-starlight/`. From the repo root:

```bash
just install   # one-time: install site deps
just serve     # dev server with hot reload at http://localhost:4321
just build     # production build
```

Content lives in `site-starlight/src/content/docs/`, grouped by chapter. The
sidebar is configured in `site-starlight/astro.config.mjs`.
