---
title: "Episode 9 — Coding agents, cost, and control"
version: 1.0
updated: 2026-08-25
episode: 9
duration_target: "10 minutes"
prerequisites: [1, 2, 3, 4]
---

# Episode 9 — Coding agents, cost, and control

## Learning objectives

- Explain the interface contract `agent_cc.py` and `agent_pi.py` both implement, and why it makes coding agents swappable per roster entry.
- Read the exact headless `claude -p` invocation `build_command` produces and state what each flag buys.
- Explain history via `--session-id` / `--resume`, and why SSSF session ids fold through UUIDv5 to satisfy Claude's `--session-id`.
- Explain why agents run hermetic (`--setting-sources '' --strict-mcp-config`), with the measured token cost of not doing that.
- State what `API_AUTH_VARS` closes, and the concrete `.env` mistake that would silently move every agent onto metered billing.
- Read a run's real cost and token numbers from `sssf.db` and explain why "tokens" in the banner looks huge while cost stays near the round-trip actually paid for.

## Cold open (≤45s)

Two Python files, `agent_cc.py` and `agent_pi.py`, drive two completely different command-line tools — one headless Claude Code, one the Pi harness. Neither the ADW scripts nor `agents.execute()` know which one is running underneath a given phase. That's not an accident of naming; it's a contract. And the same roster that lets you swap coding agents per line is also the thing that can, with one `.env` line, quietly swap your subscription for a metered API key — same output, same trace, a different invoice. This episode is about the contract, the exact command it runs, and the cost dial under your hand.

## Script

| Time | Visual | Narration |
|---|---|---|
| 0:00–0:45 | `adws/adw_modules/agent_cc.py:1-25` and `agent_pi.py:1-7` docstrings, side by side | "Two files, two tools: `agent_cc.py` drives headless Claude Code, `agent_pi.py` drives the Pi harness. `agent_cc.py`'s own docstring says it plainly — it mirrors `agent_pi.run()` one-for-one, so `agents.execute()` doesn't care which one is behind a phase." |
| 0:45–1:45 | `agent_cc.py:333-335` and `agent_pi.py:211-213`, `run()` signatures | "The contract is the same function shape on both sides: `run(request, on_event, on_spawn, on_exit) -> PiResult`. Same `PiRequest` in, same `PiResult` out, same callbacks for tool events, process spawn, process exit. Plus `resolve_model()` to turn a roster string into a real model id, and a `ToolCallTracker` class that folds each tool's stream into one record. Three names, identical shape, two very different CLIs underneath — that's what `coding_agent: claude_code` versus `coding_agent: pi` in the roster is actually switching." |
| 1:45–2:45 | `agent_cc.py:293-330`, `build_command` | "Here's the exact headless invocation, quoted straight from `build_command`: `claude -p --output-format stream-json --verbose --model <id> --system-prompt <text>`, then `--session-id <uuid>` or `--resume <uuid>`, then `--setting-sources '' --strict-mcp-config`, `--allowedTools <mapped tools>`, `--permission-mode bypassPermissions`, and the prompt itself as the last argument." |
| 2:45–3:45 | `agent_cc.py:299-306` | "`-p` means headless — print and exit, no interactive session. `--output-format stream-json` with `--verbose` gives one JSON event per line, live, so the tracer sees a tool call the moment it happens instead of after the whole turn finishes. `--system-prompt` doesn't append to Claude Code's own default prompt — it *replaces* it. An SSSF agent is defined entirely by its `prompt_engineering` file; leaving the default prompt underneath would mean two competing sets of instructions running at once." |
| 3:45–4:45 | `agent_cc.py:307-310, 136-138`, `claude_session_id` | "History: `--session-id` mints a session on turn one; every later turn in that phase — a JSON retry, a fix-loop correction — uses `--resume` on the same id, which is what keeps a correction inside the context window the agent already built. But `--session-id` insists on a UUID, and SSSF's own session ids aren't UUIDs. So `claude_session_id()` folds the SSSF id through a fixed UUIDv5 namespace. Same SSSF id, always the same Claude session — deterministic, which is what lets a rejoined run find the conversation it left." |
| 4:45–6:00 | `agent_cc.py:312-320` comment block | "Now the hermetic flags: `--setting-sources '' --strict-mcp-config`. Without them, every turn inherits the *operator's* settings — your hooks, your plugins, your custom agents, your MCP servers — and pays for all their tool schemas in the prompt on every single send. This was measured on a trivial turn: 22,478 prompt tokens inherited, versus 17,932 hermetic. That's not really about the 20%. It's that an SSSF agent is supposed to see exactly two things — its own `prompt_engineering` and its own `tools` — not whatever the engineer happened to have installed that week." |
| 6:00–7:00 | `agent_cc.py:42-60`, `API_AUTH_VARS` | "No Anthropic API calls — that's a hard guarantee, not a preference. `API_AUTH_VARS` — `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_CUSTOM_HEADERS`, the Bedrock and Vertex switches — is stripped from every child process before it spawns. The comment right above it spells out why this isn't theoretical: the justfile does `set dotenv-load`, `operator_env()` copies `os.environ` wholesale into the child, and `env.sample` invites you to add provider keys. One `ANTHROPIC_API_KEY=` line left in your `.env` would silently move every agent from your logged-in subscription onto metered per-token billing — same output, same trace in the visualizer, a different bill. Stripping the six vars closes that door regardless of what's sitting in the environment." |
| 7:00–7:45 | `sssf.db` query on screen, `d18cfb17` and `9759e4ab` rows | "Here's a real number from this repo's own trace. Two identical `adw_prompt` runs — same one-line request, minutes apart — logged 298,698 tokens at $0.0996, and 162,149 tokens at $0.0511. Same prompt, same model, tokens roughly double, cost barely half a cent apart. That's the base-prompt tax: about 15.5k tokens of Claude Code's own prompt and tool schemas get re-read on every internal turn, and no flag removes it — it's not the hermetic settings, it's the runner itself. On a longer, multi-turn scout that overhead compounds; `pi` doesn't carry it. That's the honest cost of choosing `claude` as the runner." |
| 7:45–8:45 | `sssf.db` query, `b16c5c29` vs `991c1339` rows | "Model choice is the lever that actually moves the needle. Same coupon-code feature request, same graph, only the planner's model changed: opus planner, 521,040 tokens, $1.1438 total. Sonnet planner, 552,648 tokens, $0.6139 total. Nearly double the cost for the opus run despite fewer tokens — opus is billed at a higher rate per token. The config docs say it directly: mix coding agents per agent, cheap read-only agents on one, planner and builder on the other, and measure before assuming the expensive model is buying you anything." |
| 8:45–9:30 | Visualizer run banner, tokens field vs cost field | "This is why a run banner can show 400,000 or 600,000 tokens while the cost sits under a dollar, and it isn't a bug. `agent_cc.py`'s own comment on the `result` event says it: the token count is cumulative over *every* internal turn inside one `claude -p` call — thirteen model calls isn't unusual for a routine scout — and each of those turns re-reads the cached prompt prefix. A cache read is still counted as a token, but it's billed at a fraction of a fresh input token. Big token number, small invoice — read the cost field, not the token field, when you want to know what a run actually cost." |
| 9:30–10:00 | `sssf.config.yaml`, `coding_agent` field on two agents | "Two coding agents, one contract, one hermetic sandbox, one hard-closed billing door, and one honest tax for using `claude` as the runner. Next episode: [wiring these agents into a fix loop / whatever ep10 covers]." |

## Commands demonstrated

- `sqlite3 adws/adw_data/sssf.db "select adw_id, adw_name, total_tokens, total_cost from sessions order by started_at;"` — reads real per-run cost and token totals from this repo's trace. Free, no agents run.
- `sqlite3 adws/adw_data/sssf.db "select name, kind, owner, status, started_at, ended_at from phases where adw_id='6dbd32b4' order by seq;"` — shows the fix-loop phase (`fix_1`) re-entering the builder session after a red test. Free.
- `python -c "from adws.adw_modules.agent_cc import build_command; ..."` (or read the source directly) to print `build_command`'s output for a sample request — free, no agents run, and it's literally what the file says it's for: "split out so it can be asserted in tests without spawning anything or spending a cent."
- `just sdlc` with the planner's model swapped between `anthropic/claude-opus-4-6` and `anthropic/claude-sonnet-4-6` — reproduces the $1.14 vs $0.61 comparison. Costs real money, on the order of $0.6–$1.2 per run.

## Recording notes

- `[CAST: terminal running the two sqlite3 queries above against adws/adw_data/sssf.db, full output visible, including the d18cfb17/9759e4ab token-vs-cost pair and the b16c5c29/991c1339 opus-vs-sonnet pair]`
- `[CAST: agent_cc.py:293-330 (build_command) scrolled slowly in an editor, paused on the hermetic-flags comment block at 312-320]`
- `[CAST: agent_cc.py:42-60 (API_AUTH_VARS) with the .env / env.sample files shown alongside, to make the exposure concrete rather than abstract]`

## Common mistakes

- **Reading the run banner's token count as the cost.** It's cumulative across every internal turn of one `claude -p` call, including cheap cache reads. Look at `total_cost` in `sssf.db` or the visualizer's cost field, not `total_tokens`.
- **Assuming hermetic flags remove the base-prompt tax.** `--setting-sources '' --strict-mcp-config` only strips the *operator's* hooks/plugins/MCP servers (22,478 → 17,932 measured tokens). The ~15.5k-token Claude Code base prompt and tool schema still gets re-read on every turn regardless — there's no flag for that.
- **Adding `ANTHROPIC_API_KEY` to `.env` "just to test something."** `set dotenv-load` plus `operator_env()` means that key reaches every child process unless `API_AUTH_VARS` strips it — which it does for `claude_code`, but only because someone wrote that stripping code. It's worth knowing the mechanism, not just trusting the outcome.
- **Assuming the more expensive model always plans better.** In the one measured comparison here, sonnet was both cheaper ($0.61 vs $1.14) and produced the better design (episode 4's finding). One sample isn't proof cheap always wins — but it's proof "just use opus" isn't free confidence either.

## Check for understanding

1. **Q: What three names make up the contract that lets `agents.execute()` not care whether a phase runs on `claude_code` or `pi`?**
   A: `run(request, on_event, on_spawn, on_exit) -> PiResult`, `resolve_model()`, and the `ToolCallTracker` class — both `agent_cc.py` and `agent_pi.py` implement all three with the same shape.

2. **Q: You leave one `ANTHROPIC_API_KEY=sk-...` line in `.env`. What actually stops every `claude_code` agent from silently switching to metered API billing?**
   A: `agent_cc.API_AUTH_VARS` — a fixed tuple of six env vars (`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_CUSTOM_HEADERS`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`) — is popped out of the child's environment right before every spawn, even though `operator_env()` copied the whole environment, key included, moments earlier.

3. **Q: Two runs of the same one-line `adw_prompt` request logged 298,698 tokens at $0.0996 and 162,149 tokens at $0.0511. Why did the token count nearly double while the cost barely moved?**
   A: The token total sums every internal turn of the `claude -p` call, and most of that repeated volume is the cached prompt prefix (Claude Code's own ~15.5k-token base prompt plus tool schemas) being re-read turn after turn. Cache reads bill at a fraction of a fresh input token, so a much larger token count doesn't translate into a proportionally larger cost.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-25 | Initial draft. |
