# Mission

This file used to carry the course's mission statement directly. It was found to be a
byte-for-byte copy of the Starlight site's own `mission.md` page that had already drifted
out of sync (this file still said "this course has two chapters" after the site page was
rewritten to cover all six) — the same duplicate-and-drift bug found in
`docs/training/playbook-adopting-sssf.md` (removed) and `docs/training/NOTES.md`.

**The mission statement now lives in exactly one place:**
[`site-starlight/src/content/docs/mission.md`](site-starlight/src/content/docs/mission.md)
(rendered at `/mission/` when the site is served).

## Version history

| Version | Date | Changes |
|---|---|---|
| 3.0 | 2026-09-25 | Replaced with this pointer. This file had drifted from the canonical `site-starlight/src/content/docs/mission.md` (still described a two-chapter course after the real page was rewritten for six) — found during an opus audit of `docs/` for duplication. |
| 2.0 | 2026-08-27 | Merged the Python playground repo's and the TypeScript rebuild repo's courses into this single course, as Chapter 1 (fundamentals) and Chapter 2 (gates deep dive). Superseded the Python playground repo's `learn/MISSION.md` (was v1.0) and the TypeScript rebuild repo's `MISSION.md` (was v1.2). |
