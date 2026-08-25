---
title: "Episode 2 — Installing the factory"
version: 1.1
updated: 2026-08-25
episode: 2
duration_target: "7 minutes"
prerequisites: [1]
---

# Episode 2 — Installing the factory

## Learning objectives

After this episode, you can:
- Run the installer and describe exactly what lands in your repo
- Locate the workflow files, config, and prompts that you'll wire up
- Understand why some files ignore `--force` and what `--reset-owned` means
- Recognize why the default roster needs no `.env` configuration
- Know what the justfile does and how to run a workflow from the command line

## Cold open (45s)

You've installed Claude Code and logged in. Now the question is: how do I *use* it to run agents on my own codebase?

The factory gives you the answer. It's a Python application that orchestrates agents. A single install command stamps 44 files into your repo — workflows, templates, configuration, and an operating surface. You won't write these files yourself. You'll customize them.

In this episode, we run the installer and take a tour of what appeared.

## Script

| Time | Visual | Narration |
|------|--------|-----------|
| 0:00–0:10 | Terminal, fresh directory | Let's install into a clean temp directory so we can see the full output. |
| 0:10–0:25 | Run: `cd /tmp/sssf-demo && mkdir -p sssf-demo && cd sssf-demo` | First, a fresh working directory. |
| 0:25–0:35 | Run: `uv run /Users/alexei/Projects/training/sssf-play/.claude/skills/sssf/scripts/install.py` | Now we run the installer. This is the one-liner that stamps the entire factory into the current directory. |
| 0:35–1:20 | [CAST: capture full installer output] | The installer reports: stamped 44 files. Let me describe what just landed. |
| 1:20–2:00 | Show directory structure: `ls -la adws/` and tree view | First, there's the `adws/` directory. This is where the factory lives. Inside: four starter workflow files — `adw_prompt.py`, `adw_scout.py`, `adw_plan.py`, and `adw_quality.py`. The underscore prefix means these are special. We'll use these with the `just` command to run different chains. |
| 2:00–2:30 | Show: `ls -la adws/adw_modules/` | Inside `adw_modules/` are sixteen Python files. These are the guts: the agent runners, the permission checker, the tracer that writes to the database, the quality gates. You won't edit these. They come from the skill and stay read-only. |
| 2:30–3:00 | Show: `ls -la adws/adw_data/` and mention subdirs | The `adws/adw_data/` directory holds runtime data: sessions, the trace database, and configuration. One subdirectory matters on day one: `prompt_engineering/`. |
| 3:00–3:45 | Show: `ls -la adws/adw_data/prompt_engineering/` and list agent directories | Inside `prompt_engineering/` are five folders: planner, builder, scout, reviewer, documenter. One folder per agent. Each folder holds two files: `system.md` and `user.md`. These are the prompts that define what each agent does. You customize these to fit your codebase. |
| 3:45–4:15 | Show: `cat adws/adw_sssf_config/sssf.config.yaml` (first 30 lines) | Here's the roster: `sssf.config.yaml`. This YAML file lists every agent, their model, their permissions, and which prompts they use. It also defines the protected files — the machinery that no agent is allowed to edit. You edit this file when you swap agents or add new ones. |
| 4:15–4:45 | Show: `cat justfile` (first 40 lines) | The justfile is your command palette. Recipes like `just demo`, `just prompt`, `just scout`, and `just sdlc` invoke the workflows. You can see what each recipe does by running `just --list`. |
| 4:45–5:15 | Show: `cat .env.sample` | The `.env.sample` file shows all possible environment variables. The default roster runs on `coding_agent: claude_code`, which means it uses your logged-in Claude Code session. No API key needed. No configuration needed. Just `claude --version` and you're ready to go. |
| 5:15–5:50 | Explain idempotence and `--force` | If you run the installer again on the same repo, existing files are skipped. This is idempotence — it's safe to run twice. If you want to overwrite a file, use `--force`. But two files get special treatment: `quality.py` and `sssf.config.yaml`. These are marked as engineer-owned on first stamp. Restoring them from the template would give you a factory that still runs and still reports every phase green — but it no longer checks anything. That silent failure is dangerous, so `--force` alone won't touch them. You must add `--reset-owned` to restore the template, and the flag name says out loud what it does. |
| 5:50–6:30 | Show files in repo root | Your repo root now has `.gitignore` entries and `.env.sample`. The `.env.sample` warns you in a comment: "DO NOT SET ANTHROPIC_API_KEY." Here's why: the default roster runs on your logged-in Claude Code session. If you copy an API key into `.env`, the factory would move all your agents from your personal subscription to per-token billing — same output, same trace, different invoice. The protection is built into the agent runners: they strip any Anthropic key before spawning an agent. So the warning is real. |
| 6:30–6:50 | Show: `just --list` output | Now that the factory is installed, you can see every recipe by running `just --list`. Each recipe passes through the configuration, so you can swap the roster with `SSSF_CONFIG=other.yaml just sdlc "..."`. |
| 6:50–7:00 | Terminal ready for next steps | The factory is installed. Next episode: running your first workflow. |

## Commands demonstrated

```bash
# Install the factory into the current directory
uv run /Users/alexei/Projects/training/sssf-play/.claude/skills/sssf/scripts/install.py

# Show the workflow files
ls -la adws/

# Show the internal modules
ls -la adws/adw_modules/

# Show the prompt engineering folder structure
ls -la adws/adw_data/prompt_engineering/

# Show the agent roster
cat adws/adw_sssf_config/sssf.config.yaml

# Show the operating surface
cat justfile

# Show the environment template
cat .env.sample

# List all available recipes
just --list

# Reinstall with overwrite (preserves quality.py and config)
uv run /path/to/install.py --force

# Reinstall and restore owned files to defaults (dangerous)
uv run /path/to/install.py --force --reset-owned
```

**Note:** The first six commands produce no costs. The `just --list` command lists recipes without running them. The install script itself makes no API calls — it only copies files.

## Recording notes

- `[CAST: full installer output]` — Run the install into a fresh directory and capture the complete output. The viewer needs to see "stamped: 44 file(s)" and the list of what was created.
- `[CAST: ls and tree output]` — Show the directory structures with `ls -la` and `tree` so the viewer can see the nesting.
- `[CAST: .env.sample with DO NOT SET warning]` — The warning about ANTHROPIC_API_KEY is the critical point here; make sure it's visible.

## Common mistakes

1. **Running the installer in the project root.** The user runs `uv run .claude/skills/sssf/scripts/install.py` from the `sssf-play` repo root. This overwrites the factory that's already there with the template, which resets the configuration and quality gates. Always install into a *new* directory to see what lands. If you're upgrading, use `--force --reset-owned` intentionally.

2. **Trying to set ANTHROPIC_API_KEY in .env.** The user copies a key into `.env` thinking the factory needs it. But the agent runners strip it before spawning. The factory still works, but now bills against the key instead of the logged-in session — a silent billing surprise.

3. **Using `--force` and expecting quality.py to update.** The user runs `install.py --force` thinking it will restore quality.py if they've lost it. It doesn't. They need `--reset-owned` on top. The two-flag requirement is intentional because restoring quality.py wires it back to echo placeholders that always pass.

4. **Not realizing the roster defines permissions.** The user edits `sssf.config.yaml` to add a new agent, but forgets to add it to the `tools:` list. That agent then runs with no tools at all. The config is not validated at startup; the failure shows up when that agent runs.

## Check for understanding

**Q1: What does the install script stamp into your repo?**

A: Forty-four files. The adws/ directory with starter workflows and the internal modules (adw_modules/), the config file (sssf.config.yaml), per-agent prompts in prompt_engineering/, a justfile with recipes, an .env.sample file, and five new lines appended to .gitignore.

**Q2: Why does `--force` alone not overwrite quality.py and sssf.config.yaml?**

A: Both files are marked as engineer-owned after the first stamp. Restoring quality.py from the template gives you echo placeholders that pass unconditionally, silently disabling all quality checks. Restoring the config resets your agent roster. The danger is silent, so a second flag `--reset-owned` makes it explicit.

**Q3: What does "the default roster needs NOTHING in .env" mean?**

A: It means you do not need to set any API keys. The default coding agent is `claude_code`, which runs headless `claude -p` on your logged-in Claude Code session. No key, no configuration — just login and you're ready. Other agents can use the `pi` harness and different models, and those require API keys per provider in .env — but not the default.

## Version history

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2026-08-25 | Fact-check: `adw_modules/` ships sixteen Python files, not seventeen (verified by running the installer into a clean directory). |
| 1.0 | 2026-08-25 | Initial draft. Covers installation, tour of what appears, idempotence, owned files guard, .env story. |
