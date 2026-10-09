---
title: "Skill engineering primer — reference implementation"
version: 1.1
updated: 2026-10-09
status: active
---

# Skill engineering primer: reference implementation

A complete, working skill-engineering setup produced by the `sssf-skill-vendoring` procedure (`../SKILL.md`), taken from the downstream adopter `weather-report` (a Rust/Axum service). All 9 files went through the procedure: an opus architect built each one and a fable expert approved it. Six of them were loaded live in run `f0333196` (10/10 phases). `code-review`, `writing-for-agents` and `pr` were processed after that run and haven't been loaded live in their final form.

| Path | What it is |
|---|---|
| `sssf.config.yaml` | The roster that loads these files. Its model ids are account-specific (opencode `muse-spark`, `anthropic/claude-*`), so swap in your own. |
| `skill_engineering/*.md` | The 9 vendored files. Copy them to `adws/adw_data/skill_engineering/`. |
| `prompt_engineering/{planner,builder,reviewer,documenter}/` | The role prompts with the overrides these files depend on. Merge them into yours; don't overwrite blindly. |

## Upstream pins

Every vendored header points at a clone under SSSF's own `downloads/`, which is gitignored. Recreate the clones to make `vendor_skill.py --check` work:

```bash
cd /path/to/super-simple-software-factory/downloads
git clone https://github.com/mattpocock/skills.git skills && git -C skills checkout 6fd9479
git clone https://github.com/trailofbits/skills trailofbits-skills && git -C trailofbits-skills checkout 82fe822
```

On another machine, the header's `source:` is `~/`-relative, so clone into the same path under your home directory or re-vendor.

## The nine files

| File | Upstream skill | Role(s) | Status | Merged siblings | Notable in-body edits | ~tokens |
|---|---|---|---|---|---|---|
| `codebase-design.md` | Pocock `codebase-design` | planner, builder, scout | **processed** | DEEPENING | DESIGN-IT-TWICE dropped (sub-agent procedure) | 2.1k |
| `tdd.md` | Pocock `tdd` | planner, builder | **processed** | tests, mocking | `GLOSSARY.md`→`CONTEXT.md`; Skill-tool dispatch struck | 1.8k |
| `sharp-edges-planner.md` | ToB `sharp-edges` | planner | **processed** | config-patterns, lang-rust | `## Agent` struck; Phase 4 = plan, not code | 6.8k |
| `sharp-edges.md` | ToB `sharp-edges` | reviewer | **processed** | crypto-apis, config-patterns, auth-patterns, case-studies, lang-rust | `## Agent` struck | 11.9k |
| `differential-review.md` | ToB `differential-review` | reviewer | **processed** | methodology, adversarial, reporting, patterns | adversarial-modeler dispatch struck; one report at `<context_handoff_dir>/review.md`; `git checkout` → read-only `git show`/`git diff`; issue-writer hand-offs removed | 8.1k |
| `property-based-testing.md` | ToB `property-based-testing` | builder | **processed** | generating, refactoring, reviewing, interpreting-failures, libraries | links → section names | 5.3k |
| `code-review.md` | Pocock `code-review` | reviewer | **processed** | — | fixed point is `HEAD` + the uncommitted working tree (the build isn't committed yet at review time); spec = `plan.md` else the prompt; the two axes run in sequence by the reviewer, no sub-agents | 1.6k |
| `writing-for-agents.md` | Pocock `writing-for-agents` | documenter | **processed** | — | `SKILL-MECHANICS.md` and both pointers to it dropped (skill packaging only) | 2.7k |
| `pr.md` | Pocock `pr` | documenter | **processed** | — | "PR body" reframed as the change write-up; `GLOSSARY.md`→`CONTEXT.md`; `CREDITS.md` dropped (frontmatter credits remain) | 1.0k |

**Processed** means the file was built by the procedure: it has an `sssf:flattened` manifest recording every kept and dropped file and edit, an opus architect built it, and a fable expert approved it.

## Role overrides these files depend on

The composites don't carry headless behavior themselves. The role's `system.md` does (step 4 of the procedure), so copy these paragraphs along with the files:

| Role | Override | Covers |
|---|---|---|
| planner | name the Seams list yourself; single-phase rule; already-implemented backstop (`user.md` fail branch) | `tdd` "confirm seams with the user" |
| planner | findings are tests at named seams, never code | `sharp-edges` Phase 4 |
| builder | seams come from `plan.md` | `tdd` |
| builder | decide the dev-dependency yourself; refactor only when the plan asks; no inverse the ticket didn't ask for; no "ask the maintainer" | `property-based-testing` |
| reviewer | sharp-edges/differential-review findings are in scope; one `review.md`; `audit-context-building` is not available | `sharp-edges`, `differential-review` |
| reviewer | smell-baseline findings never block | `code-review` |
| documenter | structure the write-up as Summary / Evidence / Merge Danger | `pr` |

## Adopting it

1. Install SSSF and the `sssf-skill-vendoring` skill (repo README, install step 1). Check the skill's Preconditions: `skill_engineering.py` must strip the manifest, and opencode roles need the auto-discovery fix.
2. Copy `skill_engineering/*.md` and merge the role overrides above.
3. **Adapt to your stack.** Both sharp-edges files keep only `lang-rust.md`. For another language, rebuild them with the procedure from step 4, keeping your language's reference instead.
4. Wire `skill_engineering:` per `sssf.config.yaml`, with your own models. Then run `just skills` and `agents.validate()`, run `vendor_skill.py --check` on every file, and do one live run.
5. **Watch the cost.** The reviewer composes about 21.7k skill tokens per turn and the builder about 9.2k. The reviewer's crypto-apis and case-studies (about 4k) are low-value for most services and are the first candidates to trim.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.1 | 2026-10-09 | `code-review`, `writing-for-agents` and `pr` processed (all 9 files now processed); reviewer smell override and documenter `pr` mapping added; documenter prompt included. |
| 1.0 | 2026-10-09 | Initial reference implementation: 9 vendored files, 4 role prompts and the roster from weather-report after live run `f0333196`. Six files processed by `sssf-skill-vendoring`; `code-review`, `writing-for-agents` and `pr` are plain vendors, with their failing checks listed. |
