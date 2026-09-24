---
title: PRD — Audio-narrated lectures for sssf-learn
created: 2026-08-28
status: planned
version: 1.0
updated: 2026-08-28
---

# PRD — Audio-narrated lectures

## Problem Statement

The sssf-learn book is text + interactive quizzes. A learner who wants to absorb a lesson
away from the screen (commuting, walking, resting their eyes) has no way to *listen* to it,
and no way to follow along with where the narration is in the page.

## Solution

Each lesson gets a narrated audio track and an audio player (like a podcast transport bar:
play/pause, previous/next, scrubber, elapsed/total time, volume). As the narration plays, the
matching entry in the existing "On this page" panel highlights, and previous/next jump between
those entries — so the panel doubles as a chapter list and a live progress indicator.

Audio is generated with macOS `say` (the user's own TTS) at build time and committed, so the
deployed site plays without any server.

## User Stories

1. As a learner, I want a play button on a lesson, so that I can listen instead of read.
2. As a learner, I want the "On this page" entry for the section being narrated to highlight, so that I always know where the audio is.
3. As a learner, I want previous/next controls that jump between sections, so that I can skip to the part I care about.
4. As a learner, I want a scrubber with elapsed and total time, so that I can seek freely.
5. As a learner, I want a volume control, so that I can set a comfortable level.
6. As a learner, I want clicking an "On this page" entry to seek the audio to that section, so that the panel is a table of contents for the audio too.
7. As a learner, I want code blocks skipped in narration, so that I am not read raw punctuation and symbols.
8. As a learner, I want the win/why/trap callouts narrated, so that I do not miss the key framings.
9. As a learner, I want the player to remember nothing surprising — pausing keeps my place — so that control feels predictable.
10. As a learner on a phone, I want the transport bar to be usable at small widths, so that listening works on mobile.
11. As a learner who prefers reduced motion, I want no auto-scroll surprises, so that highlighting alone tracks progress (auto-scroll is opt-in/gentle).
12. As the author, I want one command to (re)generate all audio, so that regeneration after edits is trivial.
13. As the author, I want the narration text derived from the rendered lesson, so that what is spoken matches what ships.
14. As the author, I want the player to appear automatically on lessons that have audio, and be absent where there is none, so that no per-page wiring is needed.
15. As the author, I want the build to be deterministic and the section→timestamp map exact, so that highlight sync is never off.

## Implementation Decisions

- **One audio file per lesson + a cue map.** Internally each section (an "On this page" entry
  = a rendered `h2`/`h3` with an id) is rendered to its own clip so its exact duration is
  measured; the clips are concatenated into one per-lesson `.m4a`, and the cumulative offsets
  become the cue map. No timestamp estimation.
- **Deep module: `extractSections(html) -> Section[]`.** Pure function over a lesson's rendered
  HTML: walk the main content, split at heading ids, collect narration text (paragraphs, list
  items, table caption note, callout label+body), skip `pre`/`code`, return
  `{ id, title, text }[]`. Testable in isolation from any audio tooling.
- **Deep module: `buildCueMap(durations) -> Cue[]`.** Pure function: `[{id, title, dur}]` →
  `[{id, title, start, dur}]` with cumulative starts. Trivially testable.
- **Build script** (Node, run on the Mac): for each doc page, read its built HTML → `extractSections`
  → `say -v <voice> -o clip.aiff` per section → measure with `afinfo` → concat via `ffmpeg` →
  `public/audio/<slug>.m4a` + `public/audio/<slug>.json` manifest `{ src, cues }`.
- **Voice**: detect the best installed premium en_US/en_GB voice; fall back to Samantha.
- **`AudioLecture.astro`** component rendered once per doc page (via a Starlight override) that
  fetches `/audio/<slug>.json`; if absent, renders nothing. Owns the transport UI and the sync:
  on `timeupdate` it finds the current cue and toggles an `aria-current` class on the matching
  `starlight-toc a[href="#id"]`; prev/next seek to cue boundaries; clicking a TOC entry seeks.
- **data-testid** hooks: `audio-lecture`, `audio-play`, `audio-prev`, `audio-next`, `audio-seek`,
  `audio-volume`, `audio-time`, plus reuse of `nav-link` for TOC entries.

## Testing Decisions

- Good tests assert **external behavior**: given lesson HTML, `extractSections` returns the
  right ordered sections with code stripped and callouts included; given section durations,
  `buildCueMap` returns correct cumulative starts. No assertions on private helpers.
- Unit-tested modules: `extractSections`, `buildCueMap` (Node's built-in `node:test`, no new
  dependency — the site currently has no test runner).
- Player sync + transport verified with **Playwright** (integration): play highlights the right
  TOC entry, next/prev move the highlight and the audio position, seek via TOC works, both
  themes, mobile width. Prior art: the existing Playwright QA pass on this repo.

## Out of Scope

- Word-level karaoke highlighting (we sync at section granularity).
- Cloud/neural TTS; we use the user's local macOS voices only.
- Narrating quizzes (interactive), the homepage, or code blocks.
- A global persistent player across page navigations (per-lesson player for now).
- Playback-rate control and captions (possible later).

## Further Notes

macOS `say`, `afconvert`, and `ffmpeg` confirmed present. Audio is committed under
`site-starlight/public/audio/`. Regeneration is one command (a `just` recipe). If the
per-lesson-file decision proves awkward in the Playwright usability pass, the fallback is
per-section files as separate tracks — the manifest shape already isolates that choice.

## Version history
| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-28 | Initial PRD from the /write-a-prd interview. |
