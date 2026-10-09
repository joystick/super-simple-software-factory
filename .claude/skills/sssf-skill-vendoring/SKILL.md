---
name: sssf-skill-vendoring
description: Vendor any third-party or house skill (tdd, codebase-design, a Trail of Bits skill, a grilling protocol) into an SSSF repo's adws/adw_data/skill_engineering/ so the agent that loads it can actually use it headless. Inventories the whole skill directory, checks it against the consuming role's real config and prompts, flattens sibling files, records the merge, wires and validates it, and runs an architect/expert review. Use instead of a bare vendor_skill.py call whenever a skill has more than one file, asks the user anything, dispatches other skills, or is going onto a role it wasn't written for — or when the user says "vendor this skill", "skill architect", or "skill expert".
version: 1.0
updated: 2026-10-09
---

# SSSF skill vendoring

`.claude/skills/sssf/scripts/vendor_skill.py` copies one file and stamps a hash. It knows nothing about the things that decide whether a vendored skill works:

- A skill is a **directory**. `SKILL.md` often points at siblings (`DEEPENING.md`, `references/*.md`). `compose()` ships exactly one file per `skill_engineering:` entry and never follows a link, so every sibling link becomes a dead pointer.
- The skill runs in a **headless role**. It may ask the user something, call the Skill tool, spawn a `Workflow`, or write files, none of which the role can do or is allowed to do.
- **The role is specific.** Its `writes:`, `tools:`, `coding_agent`, existing skill list, and `system.md` output contract all constrain what the skill can do.
- **The repo has conventions.** For example, `CONTEXT.md` vs `GLOSSARY.md`.

This procedure covers all four. It still uses `vendor_skill.py` for the stamping, so `--check` keeps tracking drift.

## The bar

**USABLE** is the minimum. Don't ship anything below it.

- No dead links. Every sibling a link points at is either merged in or the link is removed.
- No unreachable dispatch: no Skill-tool, `Workflow`, `Task`, or slash-command calls the role can't make.
- Every interactive fallback ("ask the user", "confirm with the user") is either provably unreachable in this role's flow or overridden in the role's `system.md`.
- The skill asks for no writes outside the role's `writes:`. Output it produces lands where the role's `user.md` Report says.
- `just skills` and `agents.validate()` are clean, and `vendor_skill.py --check` reports no drift.

**FLAWLESS** is the target. It's USABLE plus:

- Each consuming role gets only what it uses. Per-language or per-stack references are trimmed to this repo's stack.
- An `sssf:flattened` manifest records every kept sibling (with its hash) and every dropped one (with the reason).
- Terminology matches the repo (`CONTEXT.md`/`GLOSSARY.md`, ADR paths, issue-tracker states).
- Rewritten links read naturally as part of the skill, not as patch notes.
- The skill expert has approved it. The token cost is checked against `skill_token_budget`.
- One live run of the role has loaded it.

## Preconditions (check once per repo)

```bash
# the composition module must strip the flatten manifest, or the manifest reaches the model
grep -q FLATTEN_MANIFEST_RE adws/adw_modules/skill_engineering.py && echo ok
# vendor_skill.py must know about manifests (FlattenedFileError, --hash)
grep -q FlattenedFileError .claude/skills/sssf/scripts/vendor_skill.py && echo ok
```

If the first check fails, port `FLATTEN_MANIFEST_RE` and the two-step `_strip_provenance` from this skill's sibling `sssf/templates/adws/adw_modules/skill_engineering.py` by hand. **Don't** use `install.py --force`: it overwrites your config and prompts too. If any consuming role runs `coding_agent: opencode`, also confirm `adws/adw_modules/agent_opencode.py` sets `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`. Without it, opencode auto-loads skills from `.claude/skills/` underneath your `skill_engineering:` list, and a skill you deliberately left out stays reachable.

## Procedure

### 1. Inventory the skill directory

List every file and classify each one:

| Kind | Example | Default |
|---|---|---|
| body | `SKILL.md` | always vendored |
| prose sibling: reference text the body links to | `DEEPENING.md`, `references/config-patterns.md`, `tests.md` | merge if the role uses it |
| procedure sibling: a workflow with its own steps | `DESIGN-IT-TWICE.md` (spawns sub-agents, presents designs to the user) | usually drop. It runs a process, it isn't reference material |
| per-stack sibling | `references/lang-go.md` … `lang-rust.md` | keep only this repo's stack |
| tool runner | `scripts/*.py`, semgrep/codeql invocations | never vendor. It's a known command, so it belongs in a `kind="code"` phase (`quality.py`) |
| harness metadata | `agents/openai.yaml`, plugin manifests | drop. It has no prompt content |

Then grep the body and each candidate sibling for risk signals: markdown links, `Skill tool`, `ask the user`, `AskUserQuestion`, `confirm`, `Task`, `Workflow`, `/slash-commands`, `allowed-tools:`, file names the skill writes, `CONTEXT.md`/`GLOSSARY.md`, and the license (Trail of Bits skills are CC-BY-SA-4.0, Pocock's are MIT).

### 2. Read every consuming role

For each role that will list this skill, read:

- **`sssf.config.yaml` entry.** `coding_agent` decides how the text arrives: `claude_code`/`pi` get a real `--system-prompt`, while `agy`/`opencode` fold it into the user turn, which is a weaker channel resent every turn. Also read `tools`, `writes`, `harness_engineering`, and the existing `skill_engineering` list and its order.
- **`system.md` and `user.md`.** Note the output contract, any existing "On the skills composed below" overrides, and the "not your job" lines.
- **Where the role sits in the ADW.** Is the decision this skill helps make still open when the role runs, or did a human or an earlier role already make it?

### 3. Run the seven checks per (skill, role)

| # | Check | Fails when |
|---|---|---|
| 1 | Dispatch dependency | it calls a sibling skill or tool not also vendored and reachable here |
| 2 | Interactive fallback | it asks the user, and that step isn't provably unreachable headless |
| 3 | Output shape | it assumes a tracker, file, or report this repo doesn't use |
| 4 | Writes/permissions | it writes somewhere `writes:`/`protected_files` would roll back |
| 5 | Composition order | its assumptions about what comes before or after it don't match the list order (compose() never sorts) |
| 6 | Terminology drift | it names a file or convention that doesn't match this repo's |
| 7 | Sibling-file dependency | its substance lives in files compose() won't ship |

The full rationale and real failure cases are in `super-simple-software-factory/docs/reference/agent-configuration/Skill-compatibility-checklist.md`.

### 4. Decide the composition

For each sibling, write down **kept** or **dropped** and the reason. Prefer **one composite shared by all consuming roles**, because two near-copies of the same text drift apart. Split into a role variant (`<name>-<role>.md`) only when a role genuinely needs different *content*, not just a different intro.

Where a check fails, fix it in the right layer:

- **Behavioral overrides belong in the role's `system.md`,** under "On the skills composed below". Examples: "name the seams yourself instead of confirming with the user", "decide the dev-dependency yourself". Don't rewrite the skill's own rules to change role behavior.
- **Mechanical flatten fixes belong in the composite.** That covers rewriting or removing sibling links, and striking a dispatch line that composition order already satisfies. Record each in-body edit as a `dropped:` line.

### 5. Build

```bash
SKILL_SRC=~/.claude/skills/codebase-design            # the real upstream dir, never a temp copy
# 1. stamp SKILL.md from its real path, so --check can track it
uv run .claude/skills/sssf/scripts/vendor_skill.py "$SKILL_SRC/SKILL.md" --as codebase-design
# 2. hash each sibling you're keeping
uv run .claude/skills/sssf/scripts/vendor_skill.py --hash "$SKILL_SRC/DEEPENING.md"
```

Then edit the vendored file in place:

1. Directly under the `sssf:vendored` header, add the manifest. It contains only `kept:` and `dropped:` lines. `kept:` paths are relative to the skill dir. `dropped:` text is free.
   ```
   <!-- sssf:flattened
   kept: DEEPENING.md sha256:<hash from --hash>
   dropped: DESIGN-IT-TWICE.md -- <reason>
   dropped: agents/openai.yaml -- harness metadata, no prompt content
   -->
   ```
2. Rewrite each sibling link. A link to a **kept** sibling becomes a pointer to the merged section ("below", "in the Glossary above"). A link to a **dropped** sibling is removed, or replaced with a plain statement if the reader would otherwise miss something.
3. Append each kept sibling's content after the body. Drop the sibling's own H1, and fix any link inside it that pointed back at `SKILL.md` too.
4. For a Trail of Bits or other copyleft source, add the license attribution as plain text inside the skill body, not in a second comment.

Never vendor from a temporary staging copy. If the header's `source:` points at a deleted path, `--check` will report "source gone" forever.

### 6. Wire and validate

- Add the file to each role's `skill_engineering:` in the decided order, and add any `system.md` overrides from step 4.
- `just skills`: the file appears under the right roles, and nothing that should be in use shows `(unused)`.
- `agents.validate()` passes. The `just` recipes run it, or call `agents.load_config` + `agents.validate` directly.
- `uv run .claude/skills/sssf/scripts/vendor_skill.py --check <file>` reports no drift, and the message counts the merged siblings.
- Check the estimated token cost in the console line when the role starts (`skill_engineering: … (est. N tokens/turn)`), and set `skill_token_budget` if it's large.

### 7. Review: skill architect + skill expert

This step is required for FLAWLESS, and for any composite with merged siblings or in-body edits. A plain single-file vendor that passes every check on its own can skip it.

| Role | Model | Does | Never does |
|---|---|---|---|
| Orchestrator (you) | current | steps 1–4, both briefs, relays the verdict, ports, commits | ships an unreviewed composite |
| Skill architect | strongest available (e.g. opus) | steps 5's edits, wording judgment | git, other files |
| Skill expert | a **different** model (e.g. fable) | verifies the file against the source and the role | edits, or trusting the architect's report |

Use a different model for each, so the reviewer doesn't share the author's blind spots. Both are fresh agents rather than forks, so brief them fully. If either could reach a git remote, restate the user's never-act-on-a-repo-you-don't-own rule in its brief.

**Architect brief:** give it the file path, what the composite is, and the role(s) and their constraints from step 2. Include the step 4 decisions (kept, dropped, and why) and any suggested wording as a starting point, not a mandate. Its job:

1. Read the whole file and the source dir.
2. Apply step 5's edits.
3. Make every changed line read naturally in context. No markup that only helps rendered HTML, since this is plain text in a prompt.
4. Change nothing outside the decided scope.

It reports the exact before/after of each edit, its reasons, and anything else it found.

**Expert brief:** give it the same context, plus the architect's report as *claims to check*. Its job is to read the file itself and confirm:

- every merged sibling is complete and unparaphrased against the source;
- no dead link remains anywhere in the file;
- every referent ("above", "below", a named heading) exists and is unambiguous;
- the manifest parses, its hashes match `--hash`, and every drop has a reason;
- the role can actually do everything the composite asks.

It should keep real defects separate from stylistic preference, and give a verdict of **APPROVE**, **REJECT**, or **APPROVE with non-blocking follow-up**, citing file content, in under 300 words. It doesn't edit.

On **REJECT**, send the findings to the *same* architect (SendMessage, so it keeps its context) and then run a fresh expert. After two rejections, stop and show the user both positions.

### 8. Port and commit

To put the same composite in another repo, `diff` first. A byte-identical copy apart from the reviewed change needs no new review. Anything else gets its own pass through this procedure. Commit only in repos the user owns, one commit per repo, and never from inside an agent.

## Re-vendoring and drift

Run `vendor_skill.py --check` on a schedule or in pre-commit. When it reports drift:

- **SKILL.md changed:** a plain re-vendor of a flattened file raises `FlattenedFileError` rather than overwriting the merge. Re-run this procedure from step 1 instead, because the upstream change may move links, siblings, or fallbacks.
- **A merged sibling changed or is gone:** re-run from step 4 for that sibling.

## Known traps

- **Hand-flattened files that have no manifest** (made before this procedure existed) are invisible to `--check` for sibling drift, and a plain re-vendor overwrites them. Give each one a manifest, built from its real upstream path, the next time you touch it.
- **Comments in the composite reach the model.** Only the `sssf:vendored` header and the `sssf:flattened` manifest are stripped. Any other "this file was edited because…" note costs tokens on every turn. Put it in the manifest's `dropped:` lines or in a commit message.
- **Skill text comes after `system.md`.** A later, more specific line in the skill can outweigh an earlier override. If an override doesn't hold in a real run, strike the conflicting line in the composite and record the edit in the manifest.
- **A stale claim in the docs:** `cookbooks/attach_a_skill.md` used to say skill_engineering only applies under `claude_code`. It applies to all four coding agents (see `agents.skill_engineering_applies()`).

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-09 | Initial version. Supersedes the user-level `~/.claude/skills/skill-architect-review/SKILL.md` (final version 1.0, same date), which became step 7 here. Adds the full vendoring procedure around it, plus the `sssf:flattened` manifest, which is now stripped by `skill_engineering.py` and drift-checked and overwrite-guarded by `vendor_skill.py`. |
