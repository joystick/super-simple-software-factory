---
title: Audit skills
---

# Audit skills

`adw_skills.py` is the zero-cost roster audit that answers "which
`skill_engineering` files are vendored, and which agents actually receive
them." It is the entrypoint at
`.claude/skills/sssf/templates/adws/adw_skills.py` (60 lines), reachable as
`just skills` (`.claude/skills/sssf/templates/justfile:68-69`), and it is a
thin printer over `agents.audit_skills(cfg)` in
`.claude/skills/sssf/templates/adws/adw_modules/agents.py:144-176`. It spawns
no agent, writes no trace, and costs nothing — its own docstring says so
(`adw_skills.py:5-8`): "there is no run to record."

## Why it exists

Skill files are text composed onto an agent's system prompt, so they are
billed on every internal turn of every phase
(`.claude/skills/sssf/references/config.md:363`). A roster can name them in
`defaults` or per agent, and the vendored copies live under
`adws/adw_data/skill_engineering/`. Over time three questions become hard to
answer by reading YAML by hand — and `audit_skills()`'s docstring
(`agents.py:146-150`) frames the audit as exactly that, "without reading YAML
by hand":

1. **Which vendored files are unused?** Every `*.md` under the vendored dir is
   listed whether or not any agent names it (`agents.py:166-170`); an
   unreferenced one prints as `(unused)` (`adw_skills.py:38`).
2. **Which named paths are not vendored?** A `skill_engineering` path that
   resolves outside the vendored dir is reported separately as
   `outside_vendor_dir` (`agents.py:172-175`) — "hand-authored, or check for a
   typo" (`adw_skills.py:48`). The audit has no opinion on which; it only
   refuses to count it as a vendoring gap.
3. **Which agents *think* they use a skill but never receive it?** This is
   the operator-lied-to case. `VendoredSkillUsage` splits `agents` (actually
   receive it) from `ignored_by` (named it, but `skill_engineering_applies()`
   is `False` for their `coding_agent`) — `agents.py:121-130`. The field
   comment records that without the split, "a pi/agy agent showed up as an
   'active user' of a skill that `execute()` correctly never gives it." The
   printer surfaces these as `[ignored by: ... — not claude_code]`
   (`adw_skills.py:40-44`), never silently dropped — the same reasoning as
   the ignored-field warning in `validate()`.

Two implementation details keep the report honest:

- **Paths are keyed by `Path(...).resolve()`** (`agents.py:152-164`), so
  `adws/x/tdd.md` and `./adws/x/tdd.md` match the same file; a config
  author's spelling choice must not read as a typo. The raw as-written string
  is kept alongside purely for display, and `outside_vendor_dir` is keyed by
  it, not by an absolute path — the same portability/privacy reasoning as
  `vendor_skill.py`'s provenance headers (`agents.py:137-141`).
- **The `ignored_by` bucket is presently always empty.**
  `skill_engineering_applies()` covers all four known coding agents
  (`agents.py:92`), so the `[ignored by: ...]` line is a dead case today.
  It is kept, per `config.md:371`, "for a future fifth coding agent that
  doesn't (yet) earn a place in that allowlist."

A note on the shebang deps (`adw_skills.py:11-15`): the script declares the
full `pydantic, python-dotenv, pyyaml, rich` set even though it only needs
two of them, because `adw_modules.agents` unconditionally imports the driver
modules at load. A leaner list "looked reasonable and failed the moment this
actually ran."

## Running it

```bash
just skills
# or
uv run adws/adw_skills.py [--config adws/adw_sssf_config/sssf.config.yaml]
```

Output shape (`adw_skills.py:31-50`):

```
vendored (adws/adw_data/skill_engineering/):
  adws/adw_data/skill_engineering/tdd.md  ->  planner, builder
  adws/adw_data/skill_engineering/review.md  ->  (unused)

named by an agent but NOT under the vendored dir (hand-authored, or check for a typo):
  adws/skills/local.md  ->  builder
```

Exit code is always `0`; the audit informs, it does not gate.

## Categorization note

This sits under `observability/` because it is a read-only view of roster
state, alongside the trace-reading tools — but unlike `Tracer` and the
Visualizer it reads *config*, not the trace database. An earlier manifest
pass pointed it at `observability.md#tables`; that section does not discuss
it, which is why this is an own page.

## See also

- `Visualizer.md` — the other read-only observability surface, over trace
  data rather than roster data.
- `../agent-configuration/Ignored-field-warnings.md` — the validate-time
  warning that uses the same `skill_engineering_applies()` predicate to flag
  a `skill_engineering` field the agent will never receive.
- `../agent-configuration/Defaults-merging.md` — how a skill named once in
  `defaults` becomes every agent's `skill_engineering`, and so shows up
  against every agent in this audit.
- `.claude/skills/sssf/references/config.md#skill-engineering` — vendoring,
  token budgets, and the cost model the audit exists to keep visible.
