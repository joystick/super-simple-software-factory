---
title: "Cheat sheet — stamping the factory into a brand-new monorepo"
version: 1.1
updated: 2026-10-08
status: active
---

# Stamp the factory: step-by-step

Grounded in the exact steps used to bring up `weather-report`'s extended
Pocock+Trail of Bits roster. Every command below is real, not illustrative.
See `docs/playbook-adopting-sssf.md` for the full rationale; this is the
condensed, print-ready checklist.

## Phase 0 — Prereqs

- `uv`, `sqlite3`, `git` (base factory)
- `opencode` CLI on PATH, logged into whichever gateway resolves your
  chosen model string (the `muse-spark-1.3-contributor-free` id used here
  is account-specific — substitute your own `opencode models` entry)
- `claude` CLI logged in (reviewer/scout/documenter run on `claude_code`
  in this roster, not opencode)
- API keys for whatever `sssf.config.yaml` actually names

## Phase 1 — Stamp the base factory

```bash
cd /path/to/new-monorepo
git init && git commit --allow-empty -m init
mkdir -p .claude/skills
cp -r /path/to/super-simple-software-factory/.claude/skills/sssf .claude/skills/
uv run .claude/skills/sssf/scripts/install.py
cp .env.sample .env   # set your API keys
just demo && just sessions && just obs
```

Green smoke test = config validated, session minted, envelope parsed,
events landed in `sssf.db`.

## Phase 2 — Apply the missing upstream patch

```bash
grep -n "OPENCODE_DISABLE" .claude/skills/sssf/templates/adws/adw_modules/agent_opencode.py
```

Comes up empty — SSSF's shipped template lacks this fix. If any role runs
`coding_agent: opencode`, add `_opencode_env()` to
`adws/adw_modules/agent_opencode.py`, setting
`OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` and
`OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1` on the subprocess env `run()`
uses, in place of bare `operator_env()`. Without it, opencode
auto-discovers skills from `~/.claude/skills/` and injects your global
`CLAUDE.md` into every prompt — underneath whatever `skill_engineering:`
actually says. Live-confirmed bug, not theoretical: see
`weather-report/.scratch/sssf-ops/issues/01-opencode-config-leaks.md`.

## Phase 3 — Vendor the Pocock bootstrap skillset

Run `/setup-matt-pocock-skills` inside Claude Code, pointed at the new
repo. Vendors `wayfinder`/`grill-with-docs`/`to-spec`/`to-tickets`/
`triage`/`domain-modeling`/`grilling`/`improve-codebase-architecture` —
the **interactive bootstrap** skills, run by hand, never composed onto a
headless role in this roster.

Confirm the label mapping matches the five canonical triage roles
(`needs-triage`/`needs-info`/`ready-for-agent`/`ready-for-human`/
`wontfix`) — `weather-report/docs/agents/issue-tracker.md` has a working
example.

## Phase 4 — Vendor the `skill_engineering` roster's 8 source skills

```bash
# Trail of Bits — clone read-only if you don't have it
git clone https://github.com/trailofbits/skills /tmp/trailofbits-skills
```

Straight Pocock vendors (single file, no flattening):

```bash
cd /path/to/new-monorepo
uv run /path/to/super-simple-software-factory/.claude/skills/sssf/scripts/vendor_skill.py \
  /path/to/super-simple-software-factory/downloads/skills/skills/engineering/codebase-design/SKILL.md \
  --dest-dir adws/adw_data/skill_engineering --as codebase-design
# repeat for: tdd, code-review, writing-for-agents, pr
```

ToB skills need hand-flattening first (compatibility check #7 —
`compose()` ships one file, ToB splits across `references/*.md`):

```bash
mkdir -p .scratch/_tob-vendor-staging/flattened
# concatenate SKILL.md + only the reference files your stack needs
# (weather-report kept lang-rust.md, dropped the other 10 — use yours)
# add a CC-BY-SA-4.0 attribution header naming the exact upstream commit
uv run .../vendor_skill.py .scratch/_tob-vendor-staging/flattened/sharp-edges.md \
  --dest-dir adws/adw_data/skill_engineering --as sharp-edges
# repeat for: differential-review, property-based-testing
rm -rf .scratch/_tob-vendor-staging
```

## Phase 5 — Build the planner-specific trimmed variants

Three files no other role needs — copy directly from `weather-report`,
repo-specific trims, not upstream vendors:

```bash
cp /path/to/weather-report/adws/adw_data/skill_engineering/{codebase-design-planner,tdd-planner,sharp-edges-planner}.md \
   adws/adw_data/skill_engineering/
```

Non-Rust stack? Re-check `sharp-edges-planner.md`'s trim — swap
`lang-rust.md` for your own language file and re-flatten.

## Phase 6 — Copy the prompt amendments

```bash
cp /path/to/weather-report/adws/adw_data/prompt_engineering/planner/{system,user}.md \
   adws/adw_data/prompt_engineering/planner/
cp /path/to/weather-report/adws/adw_data/prompt_engineering/builder/system.md \
   adws/adw_data/prompt_engineering/builder/
cp /path/to/weather-report/adws/adw_data/prompt_engineering/reviewer/system.md \
   adws/adw_data/prompt_engineering/reviewer/
```

Carries: the already-implemented backstop, the single-phase rule, the
seam-naming override, the sharp-edges Phase-4 rewrite, the style-opinions
carve-out. Re-read once — some reference `weather-report`-specific
conventions (`CONTEXT.md`, `docs/adr/`); verify against your own repo.

## Phase 7 — Drop in the roster wiring

Copy `weather-report/adws/adw_sssf_config/sssf.config.yaml`'s `agents:`
block wholesale. Adjust only:

- `model:` strings to your own `opencode models`/`claude` catalog
- `writes:`/`protected_files:` paths if your repo layout differs

## Phase 8 — Validate before running anything real

```bash
just skills      # every skill_engineering file resolves; flags (unused) ones
just quality      # wire to your repo's real test/lint commands first (Rule Zero)
```

## Phase 9 — Bootstrap vocabulary once, interactively

```bash
# /grill-with-docs (or /wayfinder), inside Claude Code
# writes CONTEXT.md / docs/adr/ -- planner's system.md expects these
```

## Phase 10 — First real ticket, end to end

```bash
/to-spec        # or let grill-with-docs write it inline
/to-tickets
/triage         # flips Status: to ready-for-agent -- the one human gate
just watch --once   # claims it, runs the full chain, resolves it
```

`just watch --once` is the one worth watching closely the first time —
the real queue path, not the `just simple-sdlc "<text>"` CLI shortcut,
and the one that proves bootstrap→AFK actually works end to end in the
new repo.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.1 | 2026-10-08 | Renamed from `cheat-sheet-plant-the-factory.md` (final version 1.0) — "stamp" is this project's own term (README: "stamped into any repo", "The skill is the product... stamping config, adws, and prompt_engineering into three different target repos"); "plant" was never used elsewhere in this codebase. Title and heading updated to match; no content/structure change. |
| 1.0 | 2026-10-08 | Initial cheat sheet, derived from the live `weather-report` setup (Pocock+ToB extended roster, re-armed planner, opencode harness patch). |
