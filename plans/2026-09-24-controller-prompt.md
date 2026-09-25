---
title: Controller-agent prompt — verify Phase 1 of the learning-content consolidation
created: 2026-09-24
status: planned
---

# Controller-agent prompt

Not yet fired. Hand this prompt to a fresh `fable`-model agent (general-purpose,
read-mostly with permission to run `just`/`npm`/`git` commands for verification)
**after** Phase 1 of `plans/2026-09-24-consolidate-learning-content.md` has actually
been executed — not before, and not in place of executing it. This agent's job is
adversarial verification: assume the executor made a mistake somewhere and go find
it, rather than confirming what the plan says should be true.

## The prompt to send

```
Read ~/Projects/training (a sibling working directory)/super-simple-software-factory/plans/2026-09-24-consolidate-learning-content.md
in full first — it is the plan for a migration someone just executed. Your job is
to verify, adversarially, that the migration actually did what the plan says, not
to re-plan or re-critique the plan itself. Assume something was missed; go find it.
Read-only except for the verification commands the checklist below asks you to run
(build/test/audio commands, hash comparisons, git log/status) — do not edit,
move, or delete anything yourself.

Work through every item below. For each, report PASS, FAIL (with the exact
evidence), or NOT-APPLICABLE-BECAUSE (with the reason) — no vague "looks fine".

## A. Nothing was silently dropped

1. Diff the file list under docs/handbook/site-starlight/ against a fresh clone (or
   the last-known-good commit ff8d696) of the standalone course repo's own GitHub repo —
   every tracked file from the source (excluding node_modules/, dist/, .astro/,
   public/audio/, .env.production) must exist at the destination. List anything
   present in source and absent in destination.
2. For every file that the plan says should be byte-identical (i.e. NOT one of the
   deliberately-edited config files — astro.config.mjs, package.json — or the
   deliberately-dropped ones — CLAUDE.md, .nojekyll), actually hash-compare it
   against the GitHub source at ff8d696. Report any unexpected difference.
3. Confirm NOTHING under 484 MB of previously-git-ignored build output
   (node_modules/, dist/, .astro/, public/audio/, .env.production) got committed
   into the fork. `git log --stat` on the migration commit(s) and check total
   size/file count for anything suspiciously large.
4. Confirm the fork's .gitignore actually has all 5 new rules, correctly anchored
   to docs/handbook/site-starlight/ (not bare/unanchored, which could over- or
   under-match elsewhere in the fork).

## B. The site actually works from its new home

5. Run `just handbook-install` then `just handbook-build` from the fork root —
   must succeed with exit 0. Report the actual command output if it fails.
6. Run `just handbook-test` — must be green (both audio-module unit test files).
7. Run `just handbook-audio-image` then `just handbook-audio` on ONE lesson route
   (pick any lesson under 01-sssf-fundamentals/lessons/) — confirm it actually
   produces audio output files, not just a zero exit code with no output.
8. Run `just handbook-serve` briefly and confirm the dev server actually starts
   and the homepage responds (curl localhost:4321 or equivalent) — then stop it.

## C. Nothing was left stale

9. grep -r "the standalone course repo" docs/handbook/ — for every hit, confirm it was a DELIBERATE
   choice (either updated to the new identity, or left as historical prose
   describing how the course was originally built) rather than an untouched
   leftover nobody looked at. The plan names 21 files that should have been walked;
   confirm all 21 were actually touched or explicitly left as-is on purpose (check
   git diff / git log for evidence of a deliberate decision, not just silence).
10. grep for "just audio", "just build", "just serve", "just test" (the OLD,
    unprefixed recipe names) inside docs/handbook/site-starlight/src/content/docs/
    — any hit is a stale command reference that will teach a reader something that
    no longer works. List every hit.
11. Confirm .vscode/launch.json's fate matches what the plan's Open Question 5
    resolution says was decided (either present and gitignore-excepted, or
    confirmed absent on purpose) — not silently whatever the pre-existing
    .gitignore rule happened to do.

## D. Nothing outside Phase 1's scope was touched

12. Confirm ~/Projects/training (a sibling working directory)/super-simple-software-factory/training/
    is COMPLETELY UNCHANGED — same file count, same content, same git history as
    before this migration. Phase 1 explicitly does not touch it; any change here
    is a scope violation.
13. Confirm learn/ is actually gone (not just partially removed), AND that its
    removal is backed by the plan's Open Question 1 resolution (re-verify, don't
    just trust the plan's claim: spot-check that at least one of the 3
    learn/reference/*.html pages really was a byte-for-byte prose duplicate of its
    the standalone course repo Ch1 counterpart before trusting the deletion was safe).

## E. Nothing was lost irrecoverably

14. Confirm the standalone course repo's own GitHub repo still exists on GitHub and its
    main branch is at (or ahead of) commit ff8d696 — this is the safety net the
    plan relies on before the local clone gets removed. If the local clone at
    the standalone course repo is already gone, confirm this check
    BEFORE treating that as fine — if the GitHub repo is missing or behind
    ff8d696, this is a FAIL regardless of what else passed.
15. Confirm the fork's commits for this migration are a small, coherent set (the
    plan's definition of done says "not one giant commit mixing the move, the
    config edits, and the cleanup") — report the actual commit list and whether it
    reads as one coherent story or an undifferentiated dump.

## Final verdict

State PASS or FAIL for the migration as a whole. If FAIL, list every failing item
by number, each with the specific fix needed — not a general "needs more work".
If PASS, explicitly confirm all of A-E passed, not just B (the part most likely to
get tested and treated as sufficient on its own).
```

## Notes for whoever fires this

- This agent needs real tool access: Bash (for `just`, `npm`, `git`, `curl`,
  `sha256sum`/hash comparison), Read, Grep. It does not need write access to
  anything — every verification step is either read-only or a build/test/serve
  command that doesn't mutate committed state.
- Launch with `model: "fable"`, `subagent_type` general-purpose (fresh, zero prior
  context — the prompt above is self-contained on purpose).
- If this agent reports FAIL, do not re-run it blindly after a fix — read what it
  found, fix specifically that, then re-run only the failing checks (cheaper, and
  confirms the fix rather than re-deriving the whole verification from scratch).

## Version history

| Version | Date | Changes |
|---|---|---|
| 0.1 | 2026-09-24 | Initial controller prompt, written after the fable critique pass on the migration plan (v0.2) but before Phase 1 execution. Not yet fired. |
</content>
