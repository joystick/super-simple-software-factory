---
title: "Episode 8 — Observability: reading what happened"
version: 1.1
updated: 2026-08-25
episode: 8
duration_target: "8 minutes"
prerequisites: [1,2,3]
---

# Episode 8 — Observability: reading what happened

## Learning objectives

- Query the SQLite trace to understand what a run did, how much it cost, and why it failed
- Use the justfile's observability recipes to drill into a live or completed workflow
- Read session artifacts on disk to access raw agent output before parsing
- Write ad-hoc queries to measure cost, context occupancy, and tooling patterns
- Understand why the terminal output and the database stay in sync

## Cold open (45 seconds)

A workflow ran, and now you need to know: Did it succeed? What did it cost? Which agent made the mistake? Why did the test phase fail three times before succeeding? The database can answer all of this. SSSF writes every event—every tool call, every gate result, every token—into SQLite as it happens. The just recipes let you peek without waiting for the full UI.

---

## Script

| Time | Visual | Narration |
|------|--------|-----------|
| 0:00 | Terminal, just --list | "We've already seen how to run a workflow. Now: how to read what happened." |
| 0:05 | Terminal, just sessions | "just sessions shows the last 10 runs. Here: three successful runs, one failed, one still running." |
| 0:10 | SQLite result with columns: adw_id, status, request, total_tokens, total_cost | "Each row is a workflow. The adw_id is unique; you'll use it to drill down. The cost comes from the model's usage report, so it's only exact if the agent finished." |
| 0:20 | Show real output: 6dbd32b4\|success\|Add a savings_percent property to Receipt...\|635982\|0.4798 | "This run cost about 48 cents, used 636k tokens across all agents and gates. Status is success—that means all phases finished, all gates passed." |
| 0:40 | Terminal, `just phases 6dbd32b4` | "To see what phases ran inside it: just phases, the adw_id." |
| 0:45 | SQLite result: seq, name, kind, owner, status, attempt | "Sequence number tells you the order. kind is engineer, code, or agent. owner is who ran it—scout, planner, builder, or a quality gate. Status is success or fail. Attempt counts in-phase gate-correction retries." |
| 1:00 | Show one row: 2\|plan\|agent\|planner\|success\|0 | "Phase 2: the planner ran once, succeeded. Attempt stays at 0 — no gate correction needed." |
| 1:10 | Show one row: 5\|fix_1\|agent\|builder\|success\|0 | "Phase 5 is `fix_1` — the builder came back a second time after `test_1` failed. That's not a retried attempt on the same phase row; it's a whole new phase. In this repo's captured runs, `attempt` on the phases table stays 0 even here — the fix loop's bound is a separate phase count (`MAX_FIX_LOOPS`), not this column. `attempt` tracks in-phase gate-correction retries, which none of these runs needed." |
| 1:30 | Terminal, `just tail 6dbd32b4` | "To live-tail a workflow: just tail, adw_id. Polls the event log and shows the 25 most recent." |
| 1:40 | SQLite result: rowid, type, name, started_at | "rowid is the insertion order, so highest rowid = newest. type is tool_call, phase_start, agent_end, log—events as they happen. started_at is when it was recorded, precise to milliseconds." |
| 1:55 | Show tool_call events in output | "Each tool_call is one READ, EDIT, BASH, or WRITE. These are the atomic pieces—they're measured for time and cost." |
| 2:10 | Terminal, highlight two rows: tool_call\|Bash: test\|08:49:10 and tool_call\|Bash: test\|08:49:12 | "This Bash call started at 08:49:10 and finished at 08:49:12—2 seconds. Tool calls are the ONLY event type that span time. Everything else is a point in time." |
| 2:35 | Terminal, `just procs 6dbd32b4` | "To find a stuck workflow: just procs, adw_id. Shows what's running right now, with process ids." |
| 2:45 | SQLite result: kind, name, pid, command, started_at | "kind is adw—the workflow runner—or agent—a coding agent subprocess. pid is the operating-system process id you'd pass to kill if it hung. command is what that pid WAS, so if the OS recycled the pid, we don't signal the wrong thing." |
| 3:05 | Navigate to .claude/skills/sssf/references/observability.md:~line 40 | "The database tables are documented here. There are seven: sessions holds the top-level run. phases tracks each workflow stage. events is the event log—a river of everything that happened." |
| 3:30 | Show schema for events table: event_id, adw_id, phase_id, type, started_at, ended_at | "Every event knows its workflow and its phase. type is the event kind. started_at and ended_at—ended_at is NULL on events that don't span time, set only on tool_calls." |
| 3:50 | Show schema for agent_sessions: agent, context_tokens, context_window | "agent_sessions is the mirror of agent_map.json. context_tokens is how many tokens the agent was sitting in after its last turn. context_window is the model's limit. Dividing one by the other gives occupancy." |
| 4:10 | Show: scout\|298698\|200000 = 149% occupancy, then scout\|26562\|200000 = 13% occupancy | "Here's a trap in this repo's own history. Run `d18cfb17` shows 298,698 tokens against a 200,000 window — 149%, over the ceiling. That's not a real occupancy reading; it's a bug artifact. `_occupancy()` used to read from the cumulative `result` event, which sums every internal turn of the whole `claude -p` call, not the window as it stood after the last turn. That bug is fixed — occupancy is now read per assistant message (`agent_cc.py`'s `_occupancy`, called from the `assistant` event branch, not `result`). The very next comparable run, `9759e4ab`, shows the corrected number: 26,562 tokens, 13% — that's what a real scout occupancy looks like. If you see a number over 100% in old data, it's the bug, not a warning about that run." |
| 4:30 | Terminal, sqlite3 -header -column ad-hoc query | "Ad-hoc queries are free. No UI needed. For example: cost per agent. Select agent, sum cost from agent_sessions joined to sessions, group by agent." |
| 4:45 | Show result: planner\|$2.99\|4 runs, builder\|$2.99\|4 runs, scout\|$0.27\|4 runs | "The planner has been the most expensive agent: 3 dollars across 4 runs. The scout—read-only—costs a dime per run. Over time, this tells you which agent to optimize." |
| 5:10 | Terminal, just obs | "The full UI boots with just obs. It needs bun, which is not installed on this machine, so we won't run it here. But it pulls from the same database: http://localhost:4601. Events stream in live as the workflow runs." |
| 5:30 | adws/adw_modules/console.py:~line 30 | "Now, the rule: never print() directly. Modules report through run.console. Read console.py." |
| 5:45 | Show _emit() method: prints to terminal AND calls tracer.event() | "Every output method—phase_started, agent_finished, gate_result—calls _emit internally. _emit does two things: prints to the terminal and writes an event to the database. Same message, two paths." |
| 6:10 | Show tracer.py structure | "tracer.py writes both JSONL on disk and rows to SQLite, live, as events happen. Never batched. This is why tail works while the agent is still working." |
| 6:30 | Terminal, ls -la adws/adw_data/sessions/6dbd32b4/ | "Session artifacts are on disk in adws/adw_data/sessions/{adw_id}/. One folder per agent." |
| 6:45 | Show structure: planner/, builder/, events.jsonl, context_handoff/, agent_map.json | "events.jsonl is the raw event stream. agent_map.json is the roster and their models. context_handoff/ holds notes passed between agents. Inside each agent folder: raw_output.jsonl, prompts/, envelope.json." |
| 7:10 | Show builder/prompts/system.md and builder/prompts/user.md | "The prompts folder contains the exact system and user messages that were sent. This is how you debug why an agent chose something—read the prompt it received." |
| 7:30 | Show builder/envelope.json structure | "The envelope is the parsed structured output. Here: BuildOutput, status success, summary, changed_files, commit_message. If parsing failed, valid would be false, and no downstream phase would run." |
| 7:55 | Terminal prompt | "You now know four ways to read what happened: the SQLite tables, the justfile recipes, the session artifacts on disk, and ad-hoc queries. Use them to answer: Did it work, what did it cost, why did it fail, and which agent made the choice?" |

---

## Commands demonstrated

```bash
# The last 10 runs: status, token use, cost
just sessions

# All phases in one run, showing attempts and retries
just phases 6dbd32b4

# The 25 most recent events: what the agents did, when
just tail 6dbd32b4

# What's running now—if a workflow got stuck, find its pid to kill
just procs 6dbd32b4

# Cost per agent across all runs
sqlite3 adws/adw_data/sssf.db \
  "select agent, sum(s.total_cost) as total, count(s.adw_id) as runs \
   from agent_sessions a join sessions s on a.adw_id=s.adw_id \
   group by a.agent order by total desc;"

# Context occupancy: how full is each agent's window after its last turn?
sqlite3 adws/adw_data/sssf.db \
  "select agent, context_tokens, context_window, \
    round(100.0*context_tokens/context_window, 1) as pct \
   from agent_sessions where context_window > 0;"

# Which phases failed, and how many times?
sqlite3 adws/adw_data/sssf.db \
  "select name, status, count(*) from phases group by name, status;"

# How many tool calls per run?
sqlite3 adws/adw_data/sssf.db \
  "select s.adw_id, s.status, count(e.event_id) as tool_calls \
   from sessions s left join events e on s.adw_id=e.adw_id and e.type='tool_call' \
   group by s.adw_id order by s.started_at desc limit 5;"
```

---

## Recording notes

- [CAST: Terminal showing `just sessions` output—the user should see adw_id, status (running, success, fail), a snippet of the request, total_tokens, total_cost. Show at least one running, one success, one fail.]
- [CAST: Terminal showing `just phases 6dbd32b4`—all phases in sequence, showing seq, name, kind, owner, status, and attempt. No phase in this repo's trace has attempt > 0, so narrate that `fix_1` (a whole new phase) is how this run recovered from a red test, not an `attempt` bump on the same phase.]
- [CAST: Terminal showing `just tail 6dbd32b4`—events as rowid, type, name, started_at. Show both tool_calls and phase_start/phase_end.]
- [CAST: Terminal showing `just procs 6dbd32b4` on a live run. If no live runs are available, show output from a recent run and note ended_at is NULL for live ones.]
- [CAST: Text editor or terminal showing adws/adw_modules/console.py, lines 20–50, highlighting _emit() method.]
- [CAST: Terminal showing file structure: ls -la adws/adw_data/sessions/6dbd32b4/. Then ls -la adws/adw_data/sessions/6dbd32b4/builder/ to show prompts/, raw_output.jsonl, envelope.json.]
- [CAST: Text editor showing builder/prompts/system.md and builder/envelope.json content.]

---

## Common mistakes

1. **Confusing "running" with success.** A session can sit in the database with status="running" forever if a subprocess hung. Use `just procs` to check for orphaned pids, then kill the pid directly with the OS (`kill <pid>`) — this starter justfile has no `just kill` recipe; that's listed in the skill's example branch as a future recipe, not something stamped here. If `ended_at` is NULL on the process row, it's either live or crashed before cleanup.

2. **Reading `total_cost` before the workflow is done.** Cost is summed as events arrive; a running workflow shows partial cost. Check `status` first. Only `success` or `fail` means the number is final.

3. **Forgetting that tool_call is the only event with duration.** If you try to compute phase duration from log events, you'll get NULL for all but tool_calls. Use `ended_at − started_at` only on tool_calls. For phases, read the `phases` table directly—`ended_at − started_at` is already there.

4. **Printing directly instead of using run.console.** If an agent module calls print() instead of ph.log(), the message appears in the terminal but not in the database, and the UI shows nothing. Later viewers can't tell what the agent saw. Always use the console interface.

---

## Check for understanding

**Q1: You run `just sessions` and see a workflow with status='running' and total_cost=0.5. Why is the cost not the final cost?**

A: The workflow is still in progress. Costs are summed as agents complete; when the session ends, the total is final. Check `just procs <adw_id>` to see if it's truly stuck — the justfile in this repo has no `just kill` recipe, so a genuinely hung process has to be killed by pid directly (`kill <pid>`).

**Q2: A tool_call event has started_at='08:49:10' and ended_at='08:49:12'. Why does this event have an ended_at when most others don't?**

A: Tool calls are the only event type that spans time—they measure how long a tool actually took to run. Other events (phase_start, agent_end, log) are points in time, so ended_at is NULL. Use tool_call's started_at and ended_at to lay out a timeline.

**Q3: You look at builder/prompts/system.md and it's different from what you expected the builder to see. What should you check next?**

A: Check builder/envelope.json to see if the previous agent's output (enveloped to this agent) was parsed correctly. If `valid` is false, the builder got a fallback prompt instead of the real one. Or check context_handoff/ to see if context was too full and a reset happened.

---

## Version history

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2026-08-25 | Fact-check: replaced a fabricated session/phase example (`6dbd32b4` was shown with an invented request, token, and cost that didn't match `sssf.db`; phase rows showed `attempt` values that don't occur anywhere in this repo's trace) with real data. Removed two references to a non-existent `just kill` recipe — this justfile has no such command. Corrected the 149%-occupancy example: that number (`d18cfb17`) is a fixed bug artifact from `_occupancy()` once reading the cumulative `result` event instead of per-turn assistant-message usage, not a normal "over window" warning — added the corrected `9759e4ab` (~13%) comparison and said so explicitly. |
| 1.0 | 2026-08-25 | Initial version. Teaches SQLite tables (sessions, phases, events, agent_sessions, envelopes, gate_results, processes), justfile recipes (just sessions, just phases, just tail, just procs, just obs), ad-hoc queries (cost per agent, context occupancy, tool calls per run), the tool_call event's time span, the never-print() rule and console.py, session artifacts on disk. All examples grounded in real database data. |
