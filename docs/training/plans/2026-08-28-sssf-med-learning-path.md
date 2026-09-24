---
title: SSSF — Minimum Effective Learning Path for the whole ADW
created: 2026-08-28
status: done
version: 1.2
updated: 2026-08-28
---

# SSSF — a MED path through the whole ADW

**Subject.** SSSF = disler's (IndyDevDan) **Super Simple Software Factory**
(`github.com/disler/super-simple-software-factory`). One idea underneath all of it:
**code owns sequencing, retries, and acceptance; the agent owns only the work inside one
bounded phase.** *Agent proposes, code disposes.* Everything the course calls a "gate",
"envelope", "trace", "roster", or "fix loop" is a load-bearing primitive of that idea —
not incidental jargon.

This path is the **minimum effective dose**: the fewest modules that still cover *every*
moving part of the ADW, each delivering philosophy → implementation → a hands-on rep.
"Watched failing" is not a module — it is the **verification ritual repeated in every
module**: never trust a mechanism you have not watched fail.

---

## Part 1 — Do "envelope", "quality script", "watched failing" deserve their own deep dives?

| Concept | Verdict | Why |
|---|---|---|
| **Envelope** | **Yes — a full standalone deep dive. It is a missing pillar.** | The envelope is the *only* way context crosses a phase seam: "context transfers in code, not in conversation." An agent's two output channels are files in `context_handoff/` and one valid-JSON response, persisted as `envelope.json` and injected into the next agent's prompt. It is a distinct primitive from gates and is currently taught only in passing. |
| **Quality script (`quality.py`)** | **Yes — but scoped as "the two-layer gate system," completing what Ch1 L2 / Ch2 obj1 started.** | There are *two* different things both called "gate": `quality.py` holds the deterministic command **blocks** (lint/typecheck/build/test — "until you wire this, your test phase is theater"), while `gates.py` holds **claim-verifying functions** `gate(envelope, run) -> GateReport`. The course teaches wiring blocks; it has not yet cleanly separated blocks-vs-claim-gates. Worth one focused deep dive. |
| **Watched failing** | **Not its own module — it is the spine.** Your intuition ("yes") is right that it is essential; the refinement is that it is a *method*, not a component. | It is mutation testing applied to gates. Ch1 L1 already teaches it. Rather than a separate chapter, it recurs as the closing rep of every module below: mutate the thing, watch it go red, restore. |

**Bottom line:** envelope = yes (new). quality/gates split = yes (finish it). watched-failing
= keep it as the recurring ritual, not a silo.

---

## Part 2 — The MED path (8 modules)

Legend: **[DONE]** already in the course · **[OPEN]** already a course objective, not yet written · **[NEW]** gap this research surfaced.

### M0 — The one idea (philosophy only, ~20 min) **[NEW, short]**
Why handing a model your whole SDLC fails: no phase boundary (can't say which step failed),
no nameable acceptance ("done" = "the agent stopped talking"), a retry is a cold start.
The fix is structural, not a better prompt.
- **Source:** SSSF README "Why this exists" + the YouTube walkthrough.
- **Rep:** none — this is the lens the rest is seen through.

### M1 — Gates & watched-failing (the cornerstone) **[DONE]**
Two families: **quality blocks** judge the code, **claim gates** judge the envelope's own
declarations (`artifacts_exist`, `files_non_empty`, `diff_matches_claims`, `tests_pass`).
A green gate must say *what* it verified. Verify every gate by mutation before trusting it.
- **Already covered:** Ch1 L1–L2, Ch2 obj1.
- **Rep (outstanding):** write `no_placeholder_blocks`; mutate a real gate and watch it fail.

### M2 — The envelope (the seam) **[DONE — Ch1 L3]**
`envelope.json`, `context_handoff/`, one typed JSON output per phase, injected into the next
prompt. Context in code, never in conversation. `data_types.py` envelope types; `changes.py`
turns a git diff into a `ChangeSet` the gates check against.
- **Rep:** read a real `envelope.json` from a run; add a field to an envelope type and watch
  it flow into the next phase's prompt and into a claim gate.

### M3 — Phases & the run object (the spine) **[DONE — Ch1 L4]**
Three swim lanes: **engineer** (human), **agent** (`ph.call()`: prompt in → typed envelope
out → gates verified), **code** (a deterministic step that stands alone, never buried inside
an agent phase). `runner.py`: `run.phase(...).call(...)`.
- **Rep:** run the smallest ADW (`adw_scout` / `adw_prompt`) and read its phases.

### M4 — The fix loop (correction, not restart) **[DONE — Ch1 L5]**
On a bad JSON or gate violation **nothing restarts** — the harness re-prompts the *same*
session naming exactly what was wrong; the context window stays intact (`--session-id` is
create-or-continue). A correction costs one message; a restart throws away what the agent
learned. Ties back to Ch1's "a dead gate disables the repair machinery."
- **Rep:** force a gate violation and watch the correction fire; contrast with a dead gate
  where the loop never fires.

### M5 — The roster & bounding (config + permissions) **[DONE — Ch1 L6]**
`adws/adw_sssf_config/sssf.config.yaml`: models (`provider/model-id`), thinking levels,
tools, and **what each agent may write**. `protected_files`; why the builder must not be
able to edit its own grader.
- **Rep:** set `writes`/`protected_files`, have an agent attempt an out-of-bounds write, and
  watch it get blocked.

### M6 — The trace (observability) **[DONE — Ch1 L7]**
`sssf.db`, seven tables (`sessions`, `phases`, `events`, `envelopes`, `gate_results`,
`agent_sessions`, `processes`), WAL so reads never block a run. One tool call = one
`tool_call` row. Read what ran and what it cost — and notice what it *cannot* say (whether
any of it meant anything).
- **Rep:** `just phases <adw_id>`, `just tail <adw_id>`; query `gate_results`; write down one
  question the trace answers and one it can't.

### M7 — ADW chains & composing (implementation) **[DONE — Ch1 L8]**
The chain table (`adw_prompt` … `adw_simple_sdlc`), scripts are thin (40–180 lines) because
`adw_modules/` holds the logic. `MAX_FIX_LOOPS`. Copy the closest chain, edit the phase list.
- **Rep:** author a custom chain by editing an existing `adw_*.py`'s phase list; run it.

### M8 — Stamp & run on real work (capstone) **[DONE — Ch1 L9]**
Get the skill into a repo, **stamp** the factory (`install.py`), wire `quality.py` with real
commands, run `adw_simple_sdlc` on a genuine feature, review the diff + cost + trace, trust
the gates *because they were watched failing*.
- **Rep:** the unspent demonstration in NOTES — run a real `just sdlc` with a deliberately
  dead test gate and watch the factory commit a bug and certify it 5/5 (~$0.60–£1).

---

## Part 3 — What maps to the current two chapters

- **Ch1 (fundamentals)** already delivers M0–M1 and defines M5/M6/M8 as open objectives.
- **Ch2 (gates deep dive)** hardens M1 in a second toolchain (done).
- **Genuinely new deep dives this path adds:** M2 (envelope), M3 (phases/run), M4 (fix loop),
  M7 (chains) — plus finishing M5/M6/M8.
- **A candidate Chapter 3** ("SSSF on an existing Next.js + Expo Turborepo", already parked in
  NOTES) is the natural home for M5 + M8 against a real monorepo.

## Sequencing rule
Take them in order; each depends on the prior. Every module ends with its **watched-failing
rep** — the mechanism is not "learned" until it has been seen to go red on purpose and green
again.

## Version history
| Version | Date | Changes |
|---|---|---|
| 1.2 | 2026-08-28 | M5–M8 shipped (Ch1 L6 Bounding an Agent, L7 Reading the Trace, L8 Composing a Chain, L9 Stamp and Run for Real). All implementation modules M1–M8 now done; status → done. |
| 1.1 | 2026-08-28 | M2 (Ch1 L3 The Envelope), M3 (Ch1 L4 Phases and the Run), and M4 (Ch1 L5 The Fix Loop) written and shipped; status → in-progress. |
| 1.0 | 2026-08-28 | Initial MED path drafted from the SSSF README (disler/super-simple-software-factory, `example` branch) and the course's own MISSION/NOTES. |
