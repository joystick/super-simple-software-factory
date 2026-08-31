# Attach a Skill

Vendor a Pocock-style workflow protocol (`tdd`, `codebase-design`, a grilling protocol, a house convention you wrote yourself) and attach it to an agent, end to end.

## Vendor it in

```bash
uv run <skill>/scripts/vendor_skill.py ~/.claude/skills/tdd/SKILL.md
```

Copies the file's body into `adws/adw_data/skill_engineering/tdd.md`, stamped with a provenance header — source path, date, a content hash. Every real Pocock skill file is literally named `SKILL.md`; the destination name comes from the **parent directory** (`tdd`), not the file's own stem, so vendoring several skills never collides them into the same destination.

Name it explicitly if you want something other than the source directory's name:

```bash
uv run <skill>/scripts/vendor_skill.py ./my-house-rules.md --as house-rules
```

**Re-running the same command is a no-op.** The vendored file's date stamp only moves when the source content actually changed — a re-vendor loop or a CI check never produces a spurious diff.

**It refuses to overwrite a hand-authored file.** If `adws/adw_data/skill_engineering/tdd.md` already exists and has no provenance header, `vendor_skill.py` exits with an error and touches nothing. Either that file was never meant to be a vendoring target (rename it, or vendor under `--as` something else), or you genuinely want to replace it — do that by hand.

## Attach it to an agent

```yaml
agents:
  - name: builder
    skill_engineering:
      - adws/adw_data/skill_engineering/tdd.md
```

**Only takes effect under `coding_agent: claude_code`.** Skills ride in `--system-prompt`, a `claude_code`-specific delivery mechanism — `pi` and `agy` ignore the field, and `agents.validate()` warns you about it (never fails the run) if you attach one to either anyway.

**Composition order is the list order, never sorted**, and the agent's own `system.md` always comes first — its identity and output contract outrank any borrowed protocol. Attach several:

```yaml
agents:
  - name: builder
    skill_engineering:
      - adws/adw_data/skill_engineering/tdd.md
      - adws/adw_data/skill_engineering/house-rules.md
```

Attach a house-wide default instead of repeating it per agent:

```yaml
defaults:
  skill_engineering:
    - adws/adw_data/skill_engineering/tdd.md

agents:
  - name: builder          # inherits the default
  - name: scout
    skill_engineering: []  # explicit override: no skills for scout, even with a default set
```

**A per-agent list replaces the default — it never appends.** An agent that omits the key inherits `defaults.skill_engineering`; an agent that sets its own (even `[]`) uses exactly that instead.

## Check the cost before you run it

```bash
uv run adws/adw_prompt.py --agent builder "any cheap prompt"
```

The console prints the skill names and an **est.** token cost (a `chars/4` heuristic, never a real tokenizer count) right after the agent starts:

```
▸ builder anthropic/claude-sonnet-4-6  session sssf-...
  skill_engineering: tdd (est. 891 tokens/turn)
```

That cost is re-sent on **every internal turn** of the phase, on top of Claude Code's own ~15.5k-token base prompt. Set a soft budget to get a warning (never a hard failure) when a composed prompt gets big:

```yaml
defaults:
  skill_token_budget: 2000   # or per-agent, same override rule as skill_engineering
```

## Audit what's vendored and who's using it

```bash
just skills
```

```
vendored (adws/adw_data/skill_engineering/):
  adws/adw_data/skill_engineering/codebase-design.md  ->  (unused)
  adws/adw_data/skill_engineering/tdd.md  ->  builder, fixer
```

An unused vendored file is not wrong — you may be about to attach it — but it's worth noticing before it goes stale.

## Check for drift

```bash
uv run <skill>/scripts/vendor_skill.py --check adws/adw_data/skill_engineering/tdd.md
```

Reports whether the original source has changed (or moved, or been deleted) since vendoring. **Never resolves the drift automatically** — re-run the plain vendor command yourself when you actually want the update. Exits non-zero on drift, so it's safe to wire into a pre-commit check if you want one.

## The claim this doesn't make

None of this proves `tdd.md` actually changed how the builder worked. Enforcement here stops at outcome gates — the suite, the linter, the typechecker — never a gate that claims to verify a *process* was followed. If you want to know whether attaching a skill is worth its cost, run the same request twice from an identical baseline, once with the skill and once without, and read both diffs and both traces yourself.

Full spec: `references/config.md`, "Skill engineering" section.
