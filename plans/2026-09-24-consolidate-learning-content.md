---
title: Consolidate training/, learn/, and the standalone course repo into docs/handbook + docs/reference
created: 2026-09-24
status: superseded
---

> **SUPERSEDED** by `plans/2026-09-24-docs-reference-and-training.md`. This plan's
> *mechanics* for moving the standalone course repo's Astro site (ignore-aware copy, `.gitignore`
> porting, hash-before-edit verification, the 21-file grep checklist) are still
> correct and are reused by the new plan. Its *target layout* is not: `docs/handbook/`
> is renamed `docs/training/`, and `docs/reference/` is no longer a thin pointer page
> — it's now a full glossary of every SSSF concept. Read the new plan first.

# Consolidate three learning-content locations into one

## Why

Three independently-grown bodies of SSSF learning/reference content exist with no
cross-linking and, in two cases, no active maintenance:

| Location | What it is | Status (as of 2026-09-24) |
|---|---|---|
| `super-simple-software-factory/training/` | 10-episode screencast **scripts** (narration timing, `[CAST:]` markers) + 8 asciinema `.cast` recordings | Frozen, single commit (2026-08-25). Depends on the separate the Python playground repo playground repo for real ids/costs. |
| `super-simple-software-factory/learn/` | Orphaned one-off interactive HTML course on gates (2 lessons, 3 reference pages, 2 learning-records, raw CSS/JS) | Parked after lesson 1 of 4 objectives, single commit (2026-08-27). Notes say its assets were "copied from the TypeScript rebuild repo's workspace" but it was never actually merged into anything. |
| `the standalone course repo/` (its own separate repo) | Real, actively-maintained Astro/Starlight course consolidating `the Python playground repo/learn/` (Ch1) + `the TypeScript rebuild repo/*` (Ch2) — quizzes, audio (Piper TTS) narration pipeline, 24 commits, latest 2026-09-07 | Alive, but sits in its own repo disconnected from the fork it teaches. |

Decision (superseding an earlier "flatten everything to plain markdown" direction):
**keep the standalone course repo's Astro/Starlight site and its TTS pipeline fully functional** —
relocate it wholesale into the fork rather than flattening it. `training/` and
`learn/` fold in as supporting/superseded content.

## BEFORE layout (current state, exact)

```
super-simple-software-factory/
├── training/                          # 21 files, 1 commit (2026-08-25), frozen
│   ├── README.md, BRIEF.md
│   ├── ep01..ep10-*.md                # 10 screencast scripts
│   └── casts/                         # 8 .cast recordings + demo-gate-mutation.sh
├── learn/                             # 11 files + MISSION/NOTES, 1 commit (2026-08-27), parked
│   ├── MISSION.md, NOTES.md
│   ├── learning-records/              # 2 .md (0001-green-does-not-mean-wired,
│   │                                  #        0002-two-families-of-gate)
│   ├── lessons/                       # 2 .html (gate-fail, wiring-and-writing-gates)
│   ├── reference/                     # 3 .html (verifying-a-gate, gate-cookbook,
│   │                                  #           prompting-an-adw)
│   └── assets/                        # lesson.css, quiz.js
└── docs/                              # existing, unrelated fork docs — untouched
    ├── playbook-adopting-sssf.md(+pdf), manual-skill-engineering.md(+pdf),
    │   prd-skill-engineering.md, research-local-video-generation.md,
    │   head-to-head-agy-vs-claude.md

the standalone course repo/                            # OWN REPO, its own separate repo
├── README.md, MISSION.md, NOTES.md, CONTRIBUTING.md, justfile, CLAUDE.md, .nojekyll
│                                     # CLAUDE.md is context-mode routing config
│                                     #   IDENTICAL in shape to the fork's own — do
│                                     #   NOT copy it into docs/handbook/, the fork's
│                                     #   own root CLAUDE.md already covers this tree.
│                                     # .nojekyll is a relic of an earlier Docsify/
│                                     #   GitHub-Pages phase, sits at repo root (not
│                                     #   inside site-starlight/) — irrelevant post-move,
│                                     #   drop it, do not carry it.
├── plans/                             # 4 files (audio-lectures PRD+plan, OCP review,
│                                       #           MED learning path)
└── site-starlight/                    # Astro Starlight site, npm/node toolchain
    ├── astro.config.mjs               # sidebar: Mission, Notes, Ch1, Ch2
    ├── package.json                   # name is still the scaffold default
    │                                  #   "@example/starlight-basics" — fix on move
    ├── package-lock.json              # 255 KB, commit as-is (fork .gitignore allows it)
    ├── tsconfig.json
    ├── README.md, MIGRATION_NOTES.md  # site-starlight's OWN docs, distinct from the
    │                                  #   repo-root README.md above
    ├── .vscode/{extensions,launch}.json
    │                                  # fork's own .gitignore has a .vscode/* rule
    │                                  #   with !extensions.json/!settings.json —
    │                                  #   launch.json would be silently dropped;
    │                                  #   decide whether to keep it (add an
    │                                  #   !launch.json exception) or accept the drop
    ├── scripts/audio/                 # Piper TTS (Docker) narration pipeline:
    │                                  #   build-audio.mjs, cue-map.mjs,
    │                                  #   extract-sections.mjs, piper.Dockerfile,
    │                                  #   + 2 test files
    ├── node_modules/, dist/, .astro/, public/audio/, .env.production
    │                                  # GIT-IGNORED, ~484 MB total (node_modules
    │                                  #   241 MB, public/audio 137 MB, dist 106 MB).
    │                                  #   MUST NOT be copied wholesale — see
    │                                  #   Migration mechanics step 2a.
    └── src/content/docs/
        ├── index.mdx, mission.md, notes.md
        ├── 01-sssf-fundamentals/
        │   ├── lessons/               # 12 .mdx (0000..0011)
        │   ├── reference/             # 4 .mdx (verifying-a-gate, gate-cookbook,
        │   │                          #          prompting-an-adw, wiring-your-factory)
        │   └── learning-records/      # 2 .md
        └── 02-gates-deep-dive/
            ├── lessons/                # 5 .mdx
            ├── reference/              # 5 .mdx
            ├── learning-records/       # 6 .md
            └── resources.md
```

Cross-reference facts established (fable research, 2026-09-24):
- `training/` references neither `learn/` nor the standalone course repo; its only external
  dependency is the Python playground repo (for real ids/costs).
- `learn/` references neither `training/` nor the standalone course repo by name. Its only link is
  the "assets copied from the TypeScript rebuild repo's workspace" note in NOTES.md.
- the standalone course repo explicitly says its Ch1 was extracted from `the Python playground repo/learn/` — **a
  different source than `super-simple-software-factory/learn/`** — and its Ch2 from
  `the TypeScript rebuild repo/`. It never mentions `super-simple-software-factory/learn/` or
  `training/` at all.
- **Open Question 1 RESOLVED by the fable critique pass (2026-09-24):** normalized-text
  diff of all 3 `learn/reference/*.html` vs. the standalone course repo Ch1 `reference/000{1,2,3}-*.mdx`
  pairs confirms body prose, examples, and code blocks are identical. The only
  differences are HTML-only chrome (nav links, `<title>`, one tagline/subtitle per
  page — e.g. "Say it out loud before you trust a green build") and MDX-only
  frontmatter. `learn/learning-records/*.md` are likewise identical modulo Starlight
  frontmatter. **`learn/` is confirmed fully disposable** — no unique content to fold
  in. Optional, not required: carry the 3 taglines into the corresponding MDX pages'
  `description:` frontmatter field before deleting `learn/`, since they read as
  genuinely-considered subtitles, not filler.

## AFTER layout (proposed — Phase 1 scope; `03-screencasts` is Phase 2, not yet designed)

```
super-simple-software-factory/
├── justfile                           # NEW at fork root — handbook-* recipes
├── .gitignore                         # UPDATED — 5 new rules anchored to
│                                       #   docs/handbook/site-starlight/, see
│                                       #   Migration mechanics step 3
├── docs/
│   ├── handbook/
│   │   ├── README.md                  # NEW — the standalone course repo/README.md, moved (SIBLING
│   │   │                              #   to site-starlight/, not nested inside it)
│   │   ├── MISSION.md, NOTES.md, CONTRIBUTING.md, plans/
│   │   │                              # the standalone course repo's own top-level docs, moved
│   │   │                              #   alongside site-starlight/ below — this is
│   │   │                              #   the course's own governance doc, not
│   │   │                              #   merged into the fork's own MISSION/etc.
│   │   │                              #   (CLAUDE.md and .nojekyll NOT carried — see
│   │   │                              #   BEFORE layout notes)
│   │   ├── site-starlight/            # the standalone course repo's site-starlight/, copied via
│   │   │   │                          #   rsync --exclude (ignored dirs left behind),
│   │   │   │                          #   byte-hash-verified BEFORE any edit —
│   │   │   │                          #   see Migration mechanics steps 2 and 6
│   │   │   ├── astro.config.mjs       # EDITED: title, GitHub social href
│   │   │   ├── package.json           # EDITED: name (was scaffold default
│   │   │   │                          #   "@example/starlight-basics")
│   │   │   ├── package-lock.json, tsconfig.json, README.md, MIGRATION_NOTES.md
│   │   │   ├── .vscode/{extensions,launch}.json   # launch.json's fate DECIDED
│   │   │   │                                      #   explicitly, not silently dropped
│   │   │   ├── scripts/audio/         # UNCHANGED byte-for-byte — Piper TTS
│   │   │   │                          #   pipeline, no hardcoded absolute paths,
│   │   │   │                          #   confirmed location-independent
│   │   │   └── src/content/docs/      # UNCHANGED content:
│   │   │       ├── 01-sssf-fundamentals/...   # as-is (12 lessons, 4 reference,
│   │   │       │                              #   2 learning-records)
│   │   │       └── 02-gates-deep-dive/...     # as-is (5 lessons, 5 reference,
│   │   │                                      #   6 learning-records, resources.md)
│   │   │       # NOTE: no 03-screencasts/ yet — that's Phase 2, not designed here
│   │   └── training-and-learn-retirement-note.md   # NEW — records exactly what
│   │                                                #   learn/ used to be and that
│   │                                                #   it was confirmed duplicate
│   │                                                #   and deleted; training/ is
│   │                                                #   NOT yet retired (Phase 2)
│   └── reference/                          # NEW top-level fork reference dir —
│       │                                   #   SEPARATE from the site's own internal
│       │                                   #   "reference/" sections (those stay
│       │                                   #   inside site-starlight/src/content/docs/
│       │                                   #   as Astro pages, unchanged)
│       └── README.md                       # NEW — points at docs/handbook/site-starlight
│                                            #   as the canonical reference source;
│                                            #   this dir stays for FORK-level reference
│                                            #   docs (config.md-style material), not a
│                                            #   duplicate of the course's own reference
│                                            #   pages
└── learn/                             # DELETED — confirmed disposable, see Open
                                        #   Question 1 resolution above
                                        # training/ UNTOUCHED — stays put until
                                        #   Phase 2 (03-screencasts) is designed and
                                        #   executed as its own pass

the standalone course repo/  (its own separate repo)   # LOCAL CLONE removed after
                                                 #   verification (Migration mechanics
                                                 #   step 6). GitHub repo itself
                                                 #   untouched — already pushed
                                                 #   (ff8d696) as the durable backup;
                                                 #   deleting the GitHub repo is a
                                                 #   separate, more irreversible
                                                 #   decision, out of scope here.
```

## New justfile recipes (fork root)

Mirrors the standalone course repo's existing `justfile` one-for-one (confirmed exact match by the
fable critique pass, plus the `default`/`dev` conveniences it also has), paths
rewritten for the new location (`docs/handbook/site-starlight/` instead of
`site-starlight/`). `handbook-audio` now depends on `handbook-build` as a real `just`
dependency rather than a comment, since `build-audio.mjs` reads from `dist/`:

```just
# --- handbook (docs/handbook/site-starlight/, an Astro Starlight site) ---
handbook-install:
    cd docs/handbook/site-starlight && npm install
handbook-serve PORT="4321":
    cd docs/handbook/site-starlight && npm run dev -- --port {{PORT}}
handbook-dev PORT="4321": (handbook-serve PORT)
handbook-build:
    cd docs/handbook/site-starlight && npm run build
handbook-preview:
    cd docs/handbook/site-starlight && npm run preview
handbook-test:
    cd docs/handbook/site-starlight && node --test scripts/audio/extract-sections.test.mjs scripts/audio/cue-map.test.mjs
handbook-audio-image:
    cd docs/handbook/site-starlight && docker build -t piper-tts:local -f scripts/audio/piper.Dockerfile scripts/audio
# needs `just handbook-audio-image` once, and a fresh dist/ -- depends on
# handbook-build so `dist/` always exists before build-audio.mjs reads it
handbook-audio ROUTE="": handbook-build
    cd docs/handbook/site-starlight && node scripts/audio/build-audio.mjs {{ if ROUTE != "" { "--only " + ROUTE } else { "" } }}
```

Prefixed `handbook-` rather than bare `serve`/`build`/etc. — confirmed by the fable
critique pass that the fork has no root justfile today (only
`.claude/skills/sssf/templates/justfile`, the template `/sssf install` stamps into
*target* repos, an entirely different recipe set with no name collisions either way)
so the prefix is a style choice for future-proofing, not a fix for an existing clash.

## Migration mechanics (how, not just where)

This plan is now **two phases, two PRs**, per the critique's finding 12: the
site-starlight move (mechanical, low-risk, byte-identical) must land and be verified
working BEFORE the screencast conversion (the one genuinely creative, lossy-risk step)
even starts. Do not mix them in one commit.

### Phase 1 — move site-starlight wholesale (this is the phase to execute first)

1. ~~Diff first~~ — **done**, see Open Question 1 resolution above. `learn/` confirmed
   disposable.
2. **Ignore-aware copy, not `cp -r`.** Use `rsync -a --exclude=node_modules
   --exclude=dist --exclude=.astro --exclude=public/audio --exclude=.env.production
   the standalone course repo/site-starlight/ docs/handbook/site-starlight/` (or `git archive` from a
   clean the standalone course repo tree, equivalent effect) — a naive `cp -r` + `git add -A` would
   commit ~484 MB of build output (`node_modules/` 241 MB, `public/audio/` 137 MB,
   `dist/` 106 MB, `.astro/`) into the fork. Also copy the repo-root files listed in
   the BEFORE layout (`README.md`, `MISSION.md`, `NOTES.md`, `CONTRIBUTING.md`,
   `justfile`, `plans/`) into `docs/handbook/`, sibling to `site-starlight/` — but
   NOT `CLAUDE.md` (fork's own root `CLAUDE.md` already covers this tree) or
   `.nojekyll` (Docsify relic, irrelevant post-move).
3. **Port the missing `.gitignore` rules.** Add to the fork's `.gitignore`, anchored
   to the new path: `docs/handbook/site-starlight/node_modules/`,
   `docs/handbook/site-starlight/dist/`, `docs/handbook/site-starlight/.astro/`,
   `docs/handbook/site-starlight/public/audio/`,
   `docs/handbook/site-starlight/.env.production`. Check the fork's existing
   `.vscode/*` rule (`!extensions.json`/`!settings.json`) against
   `site-starlight/.vscode/launch.json` — it will be silently dropped by that rule
   as written; either add a `!launch.json` exception or explicitly accept the drop
   (note the decision in the retirement note either way, don't let it be silent).
4. **Path/config fixups**, driven by the grep the critique ran (finding 8: "the standalone course repo"
   appears in 21 tracked files, not just `astro.config.mjs`) — re-run
   `grep -rl "the standalone course repo" docs/handbook/` after the copy and walk every hit:
   - `astro.config.mjs`: `title: 'the standalone course repo'` and the GitHub social `href`.
   - `package.json`: `name` is still the scaffold default `@example/starlight-basics`
     — fix it (e.g. `sssf-handbook` or similar), no `repository` field to update.
   - README/MISSION/NOTES/CONTRIBUTING/plans/*.md and the 13 content pages that
     mention "the standalone course repo" by name (index.mdx, mission.md, notes.md, 5 Ch1
     lessons/refs, 3 Ch2 lessons, resources.md) — each needs a human judgment call
     (rename to the new location's identity, or leave as historical prose describing
     how the course was built — do not blanket-find-replace).
   - Every `just <recipe>` mention inside those same content pages (`just audio`,
     `just build`, `just serve`, etc.) — these go stale under the `handbook-`
     prefix and must be updated to match, or the course's own pages will teach a
     command that no longer exists.
5. **`handbook-audio` depends on `handbook-build`.** The original justfile's `audio`
   recipe silently assumes `dist/` already exists (it reads from there); the plan's
   recipe table dropped that comment. Either add
   `handbook-audio ROUTE="": handbook-build` as a real just dependency, or keep the
   comment explaining the manual ordering — don't drop the constraint silently.
6. **Verify before delete, correctly this time.** The critique caught a real bug in
   the original wording: hash-comparing source vs. destination must happen BEFORE
   step 4's path/config edits touch the destination, not after — otherwise the
   comparison is source-vs-edited-tree and will show spurious diffs on every renamed
   file. Concretely: after step 2's copy, immediately hash every non-ignored file in
   both `the standalone course repo/site-starlight/` and the fresh `docs/handbook/site-starlight/`
   copy and confirm byte-for-byte equality — THEN apply step 4's edits on top.
   Nothing under `learn/` or the standalone course repo's local clone is deleted until: (a) that
   pre-edit hash comparison passed, and (b) `just handbook-build` succeeds from the
   new location, and (c) `just handbook-test` is green, and (d)
   `just handbook-audio-image` + `just handbook-audio` produce output on at least one
   spot-checked lesson. **`training/` is untouched by Phase 1** — it is not deleted
   until Phase 2's conversion is designed, executed, and separately verified.
7. **GitHub repo**: only the local clone of the standalone course repo is removed by this plan.
   Deleting the GitHub repo itself is a separate, more irreversible decision, out of
   scope here — the pushed history at `ff8d696` stays as the durable backup regardless.

### Phase 2 — `training/`'s screencast scripts (separate PR, after Phase 1 ships)

`training/`'s 10 episode scripts (screencast-script format: Time | Visual |
Narration tables, `[CAST:]` markers, 62 markers total across all 10 files) convert
into a new `03-screencasts` Starlight chapter. **Not started in this plan pass** —
per the critique (finding 12), this is the largest, least-specified, genuinely
lossy-risk conversion in the whole migration (episodes cite the Python playground repo-specific
ids/costs the new site location can't reproduce; no existing spec for how the 62
`[CAST:]` markers map onto embedded/linked `.cast` playback). Needs its own
grilling/design pass before conversion starts — see Open Question 2.

## Open questions

1. ~~Is `learn/reference/*.html` a true content duplicate~~ — **RESOLVED**, see above:
   confirmed duplicate, `learn/` is disposable.
2. Should `training/`'s screencast scripts become real Starlight MDX lesson pages, or
   stay as a `resources.md`-style pointer to markdown kept in their original script
   format? **Deferred to Phase 2** — not required to resolve before Phase 1 executes,
   since Phase 1 does not touch `training/` at all.
3. Does anything in the standalone course repo's `plans/` reference paths that break once the site
   moves? **Not yet checked** — the fable critique pass reported the mentions found
   are prose-only (one mention of `site-starlight/public/audio/`) and nothing
   structurally breaks, but this should get a final look during Phase 1 step 4's
   grep pass, not assumed clean.
4. `.nojekyll` / CI deploy — **RESOLVED**: `.nojekyll` is a root-level Docsify relic,
   dropped, not carried. the standalone course repo has no deploy recipe or CI workflow today and
   this plan doesn't add one — if a deploy target is wanted later, that's a separate
   follow-up.
5. `.vscode/launch.json` — **NOT YET DECIDED**: the fork's `.gitignore` `.vscode/*`
   rule (with `!extensions.json`/`!settings.json` exceptions) will silently drop it
   unless an exception is added. Needs an explicit yes/no before Phase 1's `.gitignore`
   edit (step 3), not left to whichever way the existing rule happens to fall.

## Definition of done — Phase 1 only

- [x] Open Question 1 resolved (`learn/` confirmed disposable)
- [ ] Open Question 5 decided (`.vscode/launch.json` kept or explicitly dropped)
- [ ] `docs/handbook/site-starlight/` copied via ignore-aware `rsync`/`git archive`
      (not `cp -r`) — no `node_modules/`, `dist/`, `.astro/`, `public/audio/`,
      `.env.production` committed
- [ ] Fresh copy byte-hash-verified against the standalone course repo's source BEFORE any
      path/config edit touches it
- [ ] Fork `.gitignore` updated with the 5 rules anchored to
      `docs/handbook/site-starlight/`
- [ ] All 21 "the standalone course repo"-mentioning files walked (grep-driven, not blanket
      find-replace) — `astro.config.mjs`, `package.json` `name`, and every
      `just <recipe>` mention inside course content pages updated to match the
      `handbook-` prefix
- [ ] `docs/handbook/site-starlight/` builds and serves locally
      (`just handbook-build`, `just handbook-serve`) from the new location
- [ ] Audio pipeline still works from the new location (`just handbook-test` green;
      `just handbook-audio-image` + `just handbook-audio` produce output, at least
      spot-checked on one lesson)
- [ ] `docs/reference/README.md` and `docs/handbook/README.md` written
- [ ] `docs/handbook/training-and-learn-retirement-note.md` written, naming exactly
      what `learn/` used to be, confirming it as a verified duplicate, and noting
      that `training/` is intentionally NOT covered by this note yet (Phase 2)
- [ ] `learn/` deleted from the fork
- [ ] the standalone course repo's local clone removed (GitHub repo itself untouched, already
      pushed as of `ff8d696`)
- [ ] Everything committed to the fork in a small number of coherent commits (not
      one giant commit mixing the move, the config edits, and the cleanup)
- [ ] **`training/` is explicitly OUT of Phase 1's definition of done** — it is not
      touched, not deleted, not converted. Phase 2 gets its own plan document once
      Open Question 2 is resolved.

## Version history

| Version | Date | Changes |
|---|---|---|
| 0.2 | 2026-09-24 | Revised per fable critique pass (`af7fe21c8d6b21184`): added the 8 tracked files the BEFORE layout omitted (`CLAUDE.md`, `.nojekyll`, `MIGRATION_NOTES.md`, `.vscode/*`, `README.md`, `tsconfig.json`, `package.json`, `package-lock.json`); resolved Open Question 1 (`learn/` confirmed a true duplicate, safe to delete); added the ignore-aware-copy requirement (484 MB of git-ignored build output would otherwise get committed) and the 5 `.gitignore` rules it needs; added the 21-file "the standalone course repo"-mention grep checklist (was previously just `astro.config.mjs`); fixed the hash-verification step, which compared source against the EDITED destination in v0.1 (spurious diffs on every renamed file) — now compares against the pre-edit copy; split into two phases/PRs (Phase 1: move `site-starlight/`, mechanical and low-risk; Phase 2: `training/` → `03-screencasts` conversion, deferred, not designed) per the critique's finding that mixing them risked the larger lossy conversion blocking the smaller safe move. `training/` is no longer deleted by this plan's Phase 1 scope. |
| 0.1 | 2026-09-24 | Initial before/after layout plan, superseding an earlier same-day "flatten to plain markdown, delete the standalone course repo" direction that the user reversed before any execution happened. Not yet critiqued or executed. |
</content>
