---
title: "Skill engineering primer — reference implementation"
version: 1.3
updated: 2026-10-11
status: active
---

# Skill engineering primer: reference implementation

A complete, working skill-engineering setup produced by the `sssf-skill-vendoring` procedure (`../SKILL.md`), taken from the downstream adopter `weather-report` (a Rust/Axum service). All 10 files went through the procedure: an opus architect built each one and a fable expert approved it.

All 10 have been loaded in live `just watch` runs:
- The first six: run `f0333196`.
- `code-review`, `writing-for-agents` and `pr`: run `a101fda9`.
- `okf`: run `2b07fef7`, where the documenter updated the OKF bundle and the `okf_maintained` gate passed on the first attempt.
- The generated roadmap: run `32ad6429`. The documenter ran `just okf-roadmap`, wrote narrative only, and the gate's drift check passed. The watcher's resolve commit then carried the ticket into the roadmap as `resolved`.

| Path | What it is |
|---|---|
| `sssf.config.yaml` | The roster that loads these files. Its model ids are account-specific (opencode `muse-spark`, `anthropic/claude-*`), so swap in your own. |
| `skill_engineering/*.md` | The 10 vendored files. Copy them to `adws/adw_data/skill_engineering/`. |
| `prompt_engineering/{planner,builder,reviewer,documenter}/` | The role prompts with the overrides these files depend on. Merge them into yours; don't overwrite blindly. |
| `code/` | The adopter-side code the OKF overrides rely on: `sync_okf_roadmap.py` (goes in `scripts/`), and the `okf_maintained` gate and watcher hook as snippets to paste into `gates.py` and `adw_watch.py`. |

## Upstream pins

Every vendored header points at a clone under SSSF's own `downloads/`, which is gitignored. Recreate the clones to make `vendor_skill.py --check` work:

```bash
cd /path/to/super-simple-software-factory/downloads
git clone https://github.com/mattpocock/skills.git skills && git -C skills checkout 6fd9479
git clone https://github.com/trailofbits/skills trailofbits-skills && git -C trailofbits-skills checkout 82fe822
git clone https://github.com/scaccogatto/okf-skills okf-skills && git -C okf-skills checkout 8e31878
```

On another machine, the header's `source:` is `~/`-relative, so clone into the same path under your home directory or re-vendor.

## The ten files

| File | Upstream skill | Role(s) | Merged siblings | Notable in-body edits | ~tokens |
|---|---|---|---|---|---|
| `codebase-design.md` | Pocock `codebase-design` | planner, builder, scout | DEEPENING | DESIGN-IT-TWICE dropped (sub-agent procedure) | 2.1k |
| `tdd.md` | Pocock `tdd` | planner, builder | tests, mocking | `GLOSSARY.md`→`CONTEXT.md`; Skill-tool dispatch struck | 1.8k |
| `sharp-edges-planner.md` | ToB `sharp-edges` | planner | config-patterns, lang-rust | `## Agent` struck; Phase 4 = plan, not code | 6.8k |
| `sharp-edges.md` | ToB `sharp-edges` | reviewer | crypto-apis, config-patterns, auth-patterns, case-studies, lang-rust | `## Agent` struck | 11.9k |
| `differential-review.md` | ToB `differential-review` | reviewer | methodology, adversarial, reporting, patterns | adversarial-modeler dispatch struck; one report at `<context_handoff_dir>/review.md`; `git checkout` → read-only `git show`/`git diff`; issue-writer hand-offs removed | 8.1k |
| `property-based-testing.md` | ToB `property-based-testing` | builder | generating, refactoring, reviewing, interpreting-failures, libraries | links → section names | 5.3k |
| `code-review.md` | Pocock `code-review` | reviewer | — | fixed point is `HEAD` + the uncommitted working tree (the build isn't committed yet at review time); spec = `plan.md` else the prompt; the two axes run in sequence, no sub-agents | 1.6k |
| `writing-for-agents.md` | Pocock `writing-for-agents` | documenter | — | `SKILL-MECHANICS.md` and both pointers to it dropped (skill packaging only) | 2.7k |
| `okf.md` | scaccogatto `okf` (0.10.0, OKF v0.2) | documenter | templates: concept, index, log | `SPEC.md` dropped (Apache-2.0, ~12k tokens; the validator decides conformance); `okf_init.py` and whole-bundle `--migrate` dropped; `/okf:validate` → `uv run scripts/okf_validate.py .okf` | 2.6k |
| `pr.md` | Pocock `pr` | documenter | — | "PR body" reframed as the change write-up; `GLOSSARY.md`→`CONTEXT.md`; `CREDITS.md` dropped (frontmatter credits remain) | 1.0k |

Each file has an `sssf:flattened` manifest recording every kept and dropped file and every in-body edit.

## Role overrides these files depend on

The composites don't carry headless behavior themselves. The role prompts do (step 4 of the procedure), so copy these paragraphs along with the files:

| Role | Override | Covers |
|---|---|---|
| planner | name the Seams list yourself; single-phase rule; already-implemented backstop (`user.md` fail branch) | `tdd` "confirm seams with the user" |
| planner | findings are tests at named seams, never code | `sharp-edges` Phase 4 |
| planner | read `.okf/index.md`, then `.okf/roadmap/`, then relevant concepts; code is ground truth | the bundle the documenter keeps |
| builder | seams come from `plan.md` | `tdd` |
| builder | decide the dev-dependency yourself; refactor only when the plan asks; no inverse the ticket didn't ask for; no "ask the maintainer" | `property-based-testing` |
| reviewer | sharp-edges/differential-review findings are in scope; one `review.md`; `audit-context-building` is not available | `sharp-edges`, `differential-review` |
| reviewer | smell-baseline findings never block | `code-review` |
| reviewer, documenter | the Report JSON is the reply, never a file; no scratch files in the repo, even ones deleted again | any skill that writes a report file |
| documenter | structure the write-up as Summary / Evidence / Merge Danger | `pr` |
| documenter | maintain `.okf/` in maintain mode, validator 0 errors, never a whole-bundle `--migrate`; the `user.md` task steps 4–6 make it explicit | `okf`, `writing-for-agents` |
| documenter | roadmap: run `just okf-roadmap`, write narrative only, never hand-edit ticket rows | `okf` |

**The OKF upkeep needs `user.md` as well as a gate.** In the first live run with `okf.md` composed and the duties only in `system.md`, the documenter touched nothing under `.okf/`, because its `user.md` task list defines the job. So `weather-report` added two things:
- **Task steps:** explicit `user.md` steps for the bundle.
- **A gate:** `okf_maintained` (`code/okf_maintained_gate.py`), wired into `adw_simple_sdlc.py` and `adw_document.py`. It requires:
  - an existing `.okf/*.md` path in `artifacts`, including a `.okf/roadmap/<feature>.md`;
  - `scripts/okf_validate.py` to exit 0;
  - when the repo has the roadmap generator, `sync_okf_roadmap.py --check` to pass.

  A miss comes back to the documenter as a correction. The roadmap requirement was added after run `9c166220`: the gate passed on the builder's `.okf` files alone while the roadmap was never touched.

**Ticket status is generated, never transcribed.** In run `9c166220` the documenter (haiku) listed a resolved ticket as `needs-triage`. Status is a fact the issue files already hold, so `code/sync_okf_roadmap.py` (`just okf-roadmap`) copies it:
- one `.okf/roadmap/<feature>.md` per `.scratch/<feature>/`;
- only the block between the `okf-roadmap:tickets` markers is generated (number, status, delivering session); narrative outside it survives;
- the index is rebuilt; output is deterministic, and `--check` changes nothing.

`code/watcher_roadmap_hook.py` runs it in `commit_watcher_state`, so the commit that flips a ticket's `Status:` also updates its roadmap entry. The documenter runs before resolve and only ever sees its own ticket as `claimed`.

The gate, the generator and the hook are adopter-side code, not SSSF core: OKF-specific code in the factory would hard-wire one third-party skill into a skill-agnostic factory.

## Adopting it

1. Install SSSF and the `sssf-skill-vendoring` skill (repo README, install step 1). Check the skill's Preconditions: `skill_engineering.py` must strip the manifest, and opencode roles need the auto-discovery fix.
2. Copy `skill_engineering/*.md` and merge the role overrides above.
3. **For the OKF parts:**
   - Copy `okf-skills/skills/validate/scripts/okf_validate.py` to your repo's `scripts/`.
   - Copy `code/sync_okf_roadmap.py` to `scripts/`, and add `okf-roadmap` / `okf-roadmap-check` recipes (`uv run scripts/sync_okf_roadmap.py [--check]`).
   - Paste `code/okf_maintained_gate.py` into `gates.py` and add `gates.okf_maintained()` to your documenter phases.
   - Replace `commit_watcher_state` in `adw_watch.py` with `code/watcher_roadmap_hook.py`. If your tests run from the repo root, point `ROADMAP_SYNC` elsewhere in them, so a test never regenerates your real bundle.
   - Make sure a `.okf/` bundle exists. For a repo with history and no bundle, build the first one with scaccogatto's interactive `backfill` skill; that's a bootstrap-phase job, not an AFK one.
4. **Adapt to your stack.** Both sharp-edges files keep only `lang-rust.md`. For another language, rebuild them with the procedure from step 4, keeping your language's reference instead.
5. Wire `skill_engineering:` per `sssf.config.yaml`, with your own models. Then run `just skills` and `agents.validate()`, run `vendor_skill.py --check` on every file, and do one live run.
6. **Watch the cost.** The reviewer composes about 21.7k skill tokens per turn, the builder about 9.2k and the documenter about 6.3k. The reviewer's crypto-apis and case-studies (about 4k) are low-value for most services and are the first candidates to trim.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.3 | 2026-10-11 | Synced weather-report `e1d9ce8` and `b52e3e1`: reviewer and documenter prompts (the Report is the reply, never a file; roadmap via `just okf-roadmap`, narrative only); the stricter `okf_maintained` gate (roadmap concept required, generator drift check); the roadmap generator and watcher hook, now shipped under `code/`. Live-tested in run `32ad6429`. |
| 1.2 | 2026-10-09 | Added `okf.md` (scaccogatto okf-skills @ 8e31878) for the documenter, the OKF role overrides (documenter maintain + roadmap, planner consume), the documenter `user.md`, and the note on why the upkeep needed task steps plus an adopter-side `okf_maintained` gate. All 10 files are now live-tested. |
| 1.1 | 2026-10-09 | `code-review`, `writing-for-agents` and `pr` processed (all 9 files now processed); reviewer smell override and documenter `pr` mapping added; documenter prompt included. |
| 1.0 | 2026-10-09 | Initial reference implementation: 9 vendored files, 4 role prompts and the roster from weather-report after live run `f0333196`. Six files processed by `sssf-skill-vendoring`; `code-review`, `writing-for-agents` and `pr` are plain vendors, with their failing checks listed. |
