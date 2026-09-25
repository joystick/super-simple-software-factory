# Notes

This file used to carry the working notes directly. It was found to be a byte-for-byte
copy of the Starlight site's own `notes.md` page — the same duplicate-and-drift risk found
in `docs/training/playbook-adopting-sssf.md` (removed) and `docs/training/MISSION.md`
(already-drifted; also replaced with a pointer). This one hadn't drifted yet, but two
independent copies of the same content always eventually do — fixing the risk, not just
the current symptom.

**The working notes now live in exactly one place:**
[`site-starlight/src/content/docs/notes.md`](site-starlight/src/content/docs/notes.md)
(rendered at `/notes/` when the site is served).

## Version history

| Version | Date | Changes |
|---|---|---|
| 3.0 | 2026-09-25 | Replaced with this pointer. Was byte-identical to the canonical `site-starlight/src/content/docs/notes.md` — found during an opus audit of `docs/` for duplication; fixing the risk before it drifted, the same bug class as the playbook and MISSION.md copies. |
| 2.1 | 2026-08-27 | Parked a possible Chapter 3: SSSF on an existing Next.js + Expo Turborepo. |
| 2.0 | 2026-08-27 | Merged `the Python playground repo/learn/NOTES.md` and `the TypeScript rebuild repo/NOTES.md` into this file, split into general vs. chapter-specific observations. |
