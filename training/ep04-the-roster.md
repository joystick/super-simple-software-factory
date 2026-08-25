---
title: "Episode 4 — The roster: configuring your agents"
version: 1.0
updated: 2026-08-25
episode: 4
duration_target: "10 minutes"
prerequisites: [1, 2, 3]
---

# Episode 4 — The roster: configuring your agents

## Learning objectives

- Read `sssf.config.yaml` and explain how `defaults` merges into each agent entry.
- Explain every field on an agent: name, purpose, model, thinking, color, prompt_engineering, tools, writes, harness_engineering.
- State the difference between `tools` (capability) and `writes` (boundary), and why one cannot substitute for the other.
- Explain why `adws/adw_modules/` is in `protected_files` and what "the builder cannot edit its own grader" means concretely.
- Choose a model per agent as a cost lever, and know what one measured planner-model swap actually showed.

## Cold open (≤45s)

The builder agent has `bash` in its tools list, because it needs to run commands while it works. `bash` can also run `git checkout adws/adw_modules/quality.py`. Nothing about the tool "bash" stops that. If the builder ever did that — by mistake, by a bad prompt, by a model doing something a model does — it would be quietly disarming the exact gate that is supposed to catch its own mistakes. This episode is about the roster file that decides what each agent *can do*, and the separate, after-the-fact check that decides what it *is allowed to have done*.

## Script

| Time | Visual | Narration |
|---|---|---|
| 0:00–0:45 | Terminal, `adws/adw_sssf_config/sssf.config.yaml` open, cold open framing on screen | "The builder agent has bash. Bash can run `git checkout` on the file that grades it. That's not a hypothetical — it's why this config file has two separate ideas of permission, and today we learn both." |
| 0:45–1:30 | `sssf.config.yaml:1-9` | "One file: `adws/adw_sssf_config/sssf.config.yaml`. Two top-level blocks that matter: `defaults`, and `agents`, a list of five. `defaults` sets `coding_agent`, `model`, `thinking`, `tools`, `harness_engineering`, `protected_files`, `data_dir` — anything an agent doesn't specify for itself, it inherits from here." |
| 1:30–2:15 | `adws/adw_modules/agents.py:48-56`, `load_config` | "The merge isn't magic, it's eleven lines of Python. `load_config` reads the YAML, and for every agent entry, for each of `coding_agent`, `model`, `thinking`, `color`, `tools`, `writes` — if defaults has it and the agent doesn't, `agent.setdefault` fills it in. `harness_engineering` gets the same treatment on its own line. Whatever the agent already set, wins. That's the whole merge." |
| 2:15–3:00 | `sssf.config.yaml:42-66`, planner block | "Look at the planner. `name: planner` — the identifier every ADW script uses; ADWs name agents, never models, so swapping the model later doesn't touch the calling code. `model: anthropic/claude-sonnet-4-6`, `thinking: high` — more reasoning budget for a planner than a builder needs. `color` is just a hex string for its lane in the visualizer, purely cosmetic." |
| 3:00–3:45 | `sssf.config.yaml:47-49`, `prompt_engineering` | "`prompt_engineering.system` and `.user` point at markdown files on disk — the planner's entire identity and task template live there, not in this config. `purpose` is one sentence that should match what that system prompt says. This config wires an agent together; it doesn't define its personality inline." |
| 3:45–5:00 | `sssf.config.yaml:14-30` and `56-66` side by side | "Now the field beginners mix up: `tools` versus `writes`. `tools` is a capability list — what the agent's harness will let it invoke at all. The planner's tools: read, grep, find, ls, bash, write, plus four subagent tools. No `edit` — 'the planner never touches repo files' is a comment right there in the YAML. `writes`, on the planner, is `[specs/]` — that's a completely different kind of rule. It doesn't say what the agent can call. It says what paths in the repo it's allowed to have changed, checked after the fact." |
| 5:00–6:00 | `adws/adw_modules/permissions.py:1-30` (docstring) | "Why two systems? Because `bash` and `write` are general-purpose. `bash` runs anything, including `git checkout`. `write` reaches any path, not just the one report file you meant. The module's own docstring says it: one builder actually did run `git checkout adws/` and discarded uncommitted work. A tool allowlist can't stop that — a tool allowlist only says what's callable, not what's acceptable to have resulted." |
| 6:00–7:00 | `adws/adw_modules/permissions.py:50-75`, `snapshot`/`changed_paths`, then `enforce` at 163 | "So `permissions.py` doesn't watch calls, it watches the repo. `snapshot()` fingerprints every changed path before the agent runs. `enforce()` fingerprints again after and diffs. A path that was dirty and is now clean counts as changed too — that's specifically how it catches a `git checkout` revert. Anything outside the agent's `writes` gets rolled back, and the phase fails naming every path. This runs after every call the agent makes, including fix-loop retries." |
| 7:00–7:45 | `sssf.config.yaml:22-34`, `protected_files` | "`protected_files` is the roster-wide floor: `adws/adw_modules/`, `adws/adw_sssf_config/`, `adws/adw_*.py`. No agent touches these unless it names that exact path in its own `writes` — the builder has no `writes` key, meaning unrestricted, but the comment on line 74-75 spells it out: 'it still cannot touch defaults.protected_files.' That's `adw_modules/quality.py`, the gate that grades the builder's own work. The builder cannot edit its own grader — that's not a policy, it's enforced code." |
| 7:45–8:15 | `sssf.config.yaml:96-97, 121-122`, scout and reviewer `writes: []` | "Scout and reviewer both have `writes: []`. That does not mean silent. `writes: []` means read-only with respect to the repo — but every agent can always write its own report under `data_dir`, because that's session runtime, not the repo. Scout's findings land in `context_handoff/`. A read-only agent still talks; it just can't touch your code." |
| 8:15–9:15 | `[CAST: two terminal recordings — same prompt, opus planner vs sonnet planner, showing final cost line]` | "Model choice is a cost lever, and here's one real comparison, same prompt, same baseline, only the planner's model changed. Opus planner: $0.8265 for the planner call alone, 216 seconds, and the whole run cost $1.1438. Sonnet planner: $0.3768, 180 seconds, whole run $0.6139. In this one run, the cheaper plan also produced the better design — an explicit `coupon_code` keyword argument instead of a `**kwargs` catch-all. That's a single sample, not a rule — don't walk away thinking cheaper always wins, walk away knowing the planner's model is worth measuring, not assuming." |
| 9:15–9:45 | `.claude/skills/sssf/references/config.md`, `coding_agent` and `harness_engineering` sections | "Last field: `coding_agent`, `claude_code` or `pi`, mixable per agent in the same roster. `harness_engineering` lists pi extension files — and under `coding_agent: claude_code`, that field is silently ignored. Not deferred, not warned about. If your roster depends on a pi extension, that agent has to run on `coding_agent: pi`." |
| 9:45–10:00 | Config file, full agents list scrolled | "Five agents, one file, two permission systems. Next episode: wiring these into an actual ADW graph." |

## Commands demonstrated

- `cat adws/adw_sssf_config/sssf.config.yaml` — view the roster. Free, no agents run.
- `just sdlc` (or equivalent small-feature run) with `model: anthropic/claude-opus-4-6` on the planner, then again with `anthropic/claude-sonnet-4-6` — reproduces the cost comparison. Costs real money each run (~$0.61–$1.14 per the brief's measured range).
- `python -c "import yaml; from adws.adw_modules import agents; print(agents.load_config().agents)"` (or equivalent) to show the merged config in the REPL — free, no agents run.

## Recording notes

- `[CAST: full terminal scroll of sssf.config.yaml, syntax highlighted, paused on the planner and builder blocks]`
- `[CAST: two side-by-side or sequential recordings of a small `just sdlc`-style run, one with opus planner and one with sonnet planner, each showing the final per-phase cost line from the tracer/visualizer]` — needed because the brief's cost numbers must be shown as real terminal output, not asserted.
- `[CAST: a deliberately triggered permission breach — an agent with writes: [] or a narrow writes list touching a path outside it — showing the rollback message and phase failure from permissions.py:enforce]`

## Common mistakes

- **Thinking `tools: [...]` is the safety boundary.** It's a capability list; an agent with `bash` and `write` can technically touch anything until `permissions.py` checks afterward. The boundary is `writes` + `protected_files`, not `tools`.
- **Reading `writes: []` as "this agent produces nothing."** It means no repo writes. The agent still writes its report — scout's findings, the reviewer's review — under `data_dir`, which is always writable.
- **Adding a `harness_engineering` extension and expecting it to run under `claude_code`.** It's silently ignored — no error, no warning. If the extension matters, that agent needs `coding_agent: pi`.
- **Giving an extension's registered tool to an agent via `harness_engineering` alone.** `--tools` filters extension tools exactly like builtins — the tool name must also appear in the agent's own `tools` list or it's silently unavailable.

## Check for understanding

1. **Q: An agent has `tools: [read, bash, write]` and no `writes` key. Can it edit `adws/adw_modules/quality.py`?**
   A: No. `writes` unset means unrestricted *except* `protected_files`, and `adw_modules/` is in the roster's `protected_files` list — no agent can touch it without naming that exact path in its own `writes`.

2. **Q: The reviewer has `writes: []`. Where does its review.md actually get written?**
   A: Under `data_dir` (session runtime, e.g. `adws/adw_data/sessions/{adw_id}/reviewer/`), not into the repo proper — `writes: []` only bars repo changes; the session runtime is always writable.

3. **Q: You swap the planner's model from opus to sonnet on one measured run. What happened to cost, time, and design quality?**
   A: Cost and time both dropped (planner $0.8265/216s → $0.3768/180s; whole run $1.1438 → $0.6139), and in that one run the sonnet plan was also the better design (explicit `coupon_code` keyword vs `**kwargs`). It's one sample — worth remeasuring, not a guarantee that cheaper always wins.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-25 | Initial draft. |
