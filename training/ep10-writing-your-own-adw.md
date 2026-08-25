---
title: "Episode 10 — Writing your own ADW"
version: 1.0
updated: 2026-08-25
episode: 10
duration_target: "12 minutes"
prerequisites: [1, 2, 3, 4, 5, 6, 7, 8, 9]
---

# Episode 10 — Writing your own ADW

## Learning objectives

By the end of this episode you can:

- Write a new `adw_*.py` script from scratch, following the canonical skeleton: config, validate, session, then a chain of `run.phase(PhaseParams(...))` blocks.
- Apply the four-param rule to decide when a new helper needs a Pydantic type instead of loose arguments.
- Add a new agent output type by extending `EnvelopeBase`, and write a gate that checks it.
- Decide, for any new phase, whether it belongs to an agent or to `adw_modules/` code — and explain why there is no tester agent.
- Wire a finished ADW into the justfile so it runs with `just <name> "<prompt>"`.

## Cold open (≤45s)

**[CAST: terminal, empty prompt]**

Every ADW you have run so far — `adw_prompt`, `adw_plan_build`, `adw_simple_sdlc` — was already written for you. You picked agents off a roster and watched phases go green. That's the ceiling of "using" the factory. Today is the floor of "operating" it: you are going to write one from nothing. Not a toy — a real workflow that runs the reviewer agent against whatever is currently in your working tree and leaves a `review.md` behind. By the end you'll have the file, you'll have run it, and you'll know exactly which nine lines are yours to write on every future ADW, because the rest is always the same nine lines in a different order.

## Script

| Time | Visual | Narration |
|---|---|---|
| 0:00–0:45 | Cold open per above | (as written above) |
| 0:45–1:45 | Editor: `adws/adw_prompt.py` full file on screen | Start from the smallest real ADW in this repo, `adws/adw_prompt.py`. Six lines of substance: load the config, validate the one agent it needs, get a session, run an engineer phase to record the ask, run one agent phase, return the exit code. Every ADW you will ever write is this shape with more phases in the middle. |
| 1:45–3:00 | Editor: `.claude/skills/sssf/cookbooks/create_adw.md` lines 52–104, the canonical skeleton | This is documented as the canonical skeleton, and it's worth reading once end to end. Four things happen before any phase opens. `agents.load_config` points at the roster YAML. `agents.validate(cfg, REQUIRED_AGENTS)` fails fast if an agent your script names isn't in that roster — nothing spawns on a half-valid config. `session.ensure` mints or joins the run, giving you the `Run` object everything else hangs off. Then, and only then, `with run.phase(...) as ph:` blocks, one per unit of work. |
| 3:00–4:15 | Editor: `adws/adw_modules/data_types.py:22–53`, `PhaseParams` | Every phase you open is described by one object, `PhaseParams` — `adws/adw_modules/data_types.py:22`. Five fields: `name`, unique within the run, it's the key the UI hangs the swim-lane block on. `kind`, one of `engineer`, `agent`, or `code` — it picks which lane renders and what `owner` is allowed to mean. `owner`: for `kind="agent"` it must be a name from the roster; for `kind="code"` it's a short actor label like `"git"` or `"quality"`; for `kind="engineer"` it's always `run.engineer`. `description`, required, one sentence on what and why. And `retries`, extra gate-correction rounds for an agent phase. Look at line 31 — there's a validator that rejects a blank description AND one that just echoes the phase name back. `commit_plan: "Commit the plan"` fails construction. That's deliberate: a description that doesn't earn its place is worse than none, because it's the only line of intent the trace and the UI ever show. |
| 4:15–4:45 | Editor: `create_adw.md:106–113`, non-negotiables list | This is the four-param rule, and it isn't just about `PhaseParams` and `AgentCall` — it's skill-wide. Any function you write in `adw_modules/` that would need a fifth positional argument gets those arguments turned into a small `BaseModel` instead. `update_modules.md` line 34 shows the pattern: a `ReviewParams` class with defaults, passed as one object. The reason is boring and correct: named fields with defaults don't drift out of order the way five positional strings do. |
| 4:45–6:00 | Editor: `adws/adw_modules/runner.py:36–39`, `PhaseHandle.call` | Inside an agent phase you call `ph.call(AgentCall(...))`. `AgentCall` — `data_types.py:286` — has four fields: `output_type`, the Pydantic model the agent's JSON must parse into; `prompt`, the text this call is answering; `previous`, the upstream envelope, which lands in the next agent's `user.md` as `{{previous_envelope}}` — that's how a chain hands context forward without you writing any plumbing; and `gates`, a list of callables run against the parsed envelope. `ph.call` only works inside a `kind="agent"` phase — line 37 raises otherwise, so you can't accidentally call an agent from a code phase. |
| 6:00–6:45 | Split: `update_modules.md:1–34` highlighted | Here's the rule that matters most for keeping this maintainable: all low-level logic lives in `adw_modules/`. An `adw_*.py` file declares agents, sequences phases, returns an exit code — full stop. Subprocess handling, git plumbing, retry mechanics, reusable predicates: none of that belongs in the script. Look at `adw_simple_sdlc.py` — even its two local helpers, `commit()` and `record()`, are four-line wrappers over calls into `git_helper` and don't touch a subprocess directly. If you catch yourself writing `subprocess.run` inside an `adw_*.py` file, stop — that's a module waiting to happen. |
| 6:45–7:45 | Editor: `data_types.py:107–120`, `ReviewOutput`; `update_modules.md:46–62` | Defining a typed output is one class. `ReviewOutput` extends `EnvelopeBase` — every envelope already carries `status`, `summary`, `artifacts`, `notes_for_next_agent` — and adds only what that call actually needs: `approved: bool`, a list of `findings`, a list of `blocking`. The cookbook calls this a synced triad: the type in `data_types.py`, the agent's `user.md` Report section showing exactly that JSON, and every call site passing `output_type=`. Change one, change all three, or the agent produces JSON the parser rejects and every call burns a correction round-trip. |
| 7:45–8:45 | Editor: `adws/adw_modules/gates.py:71–95`, `verdict_consistent` | A gate is one function: `gate(envelope, run) -> GateReport`. Read `verdict_consistent` at line 71 — it doesn't judge the code at all, it checks the envelope against itself: an approval that still lists blocking items is a contradiction the harness can catch without reading a line of diff. Notice the shape — one `report.check(item, ok, note)` call per thing looked at, and it keeps checking even after one fails, because the agent fixes more per correction round when it sees every problem at once. |
| 8:45–9:15 | Terminal: `grep -n "no tester agent" adws/adw_sssf_config/sssf.config.yaml` | Look at the roster — `adws/adw_sssf_config/sssf.config.yaml:110`. There's a comment where a tester agent would sit: "No tester agent: running the suite is a known command." That's the deciding rule for any phase you're about to write: if you can write the command down, it's code, not a model call. `bun test`, `pytest`, `git diff` — none of those need judgement, so none of those get an agent. Agent phases are reserved for the two questions code can't answer: "what should this plan be," and "is this what was asked for." |
| 9:15–9:45 | Editor: `update_config.md:87–95`, "Add a new agent" | If a phase genuinely needs a new *kind* of agent — not one already on the roster — three files change together: `prompt_engineering/{name}/system.md` and `user.md` (copy an existing pair as the shape), a config entry in `sssf.config.yaml`, and an output type. Skip any one and `agents.validate()` stops the run before anything spawns. Our worked example today reuses the reviewer that's already on the roster, so we won't need this step — but you'll need it the day you add a security-scanner or a triage agent. |
| 9:45–11:30 | Editor: new file, full script typed/pasted in | Now the worked example: a `review` ADW. One phase to capture whatever's currently different from `main` — that's code, `changes.py` already does exactly this. One phase to hand that diff to the reviewer and get a `ReviewOutput` back. One phase to write `review.md` from the envelope. No builder, no revise loop — this workflow only reports, it doesn't fix. [Full file below.] |
| 11:30–12:00 | Terminal: `just --list` showing new recipe; then `just review "ping"` running | Last step, wire it into the justfile the same way every recipe in this file is one `uv run` line: `review *ARGS: uv run adws/adw_review.py --config {{config}} "$@"`. `[CAST: terminal running `just review "describe the current diff"` end to end, showing phase-by-phase console output and the final exit code]` |

## The worked example — a `review` ADW

Design decisions, stated up front, the same way `create_adw.md` asks you to answer them before writing code:

1. **Agents, in order.** Just `reviewer` — already on the roster (`sssf.config.yaml:113`), already has `prompt_engineering/reviewer/{system,user}.md`. No new agent needed.
2. **Where code acts.** Capturing "what changed" is two git commands and a subtraction — `changes.py` already exists for exactly this (`adws/adw_modules/changes.py:52`, `capture(run, ChangeCapture(...))`). That's a `kind="code"` phase, not something the reviewer agent should rediscover with its own `git diff` calls.
3. **Does anything loop?** No. This workflow answers one question — "what does the reviewer say about the current diff" — and reports it. It does not try to fix findings; that's `adw_build_review.py`'s job, not this one's.
4. **What must each call prove?** The reviewer's envelope needs `gates.artifacts_exist` (did it actually write something) and `gates.verdict_consistent` (does its approved/blocking claim agree with its own findings) — the same pair `adw_build_review.py` uses at line 53.

This is a real, complete file. It is **not** written into `adws/` — copy it there yourself if you want to run it, since running it spends real reviewer-agent cost.

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic", "python-dotenv", "pyyaml", "rich"]
# ///
"""ADW Review — run the reviewer against the current diff, write review.md.

Usage:
    uv run adws/adw_review.py "<what to check against>" [--base main]
        [--config adws/adw_sssf_config/sssf.config.yaml] [--adw-id a1b2c3d4]

Phases: engineer(request) -> code(changes) -> reviewer -> code(write_review)

This workflow only reports. It does not revise — that loop already exists in
adw_build_review.py, and bolting a fix cycle onto a read-only report muddies
what each script is for. If the reviewer finds blocking issues, they land in
review.md and the run exits 1; a human or a separate build-review run decides
what happens next.
"""

import argparse
import sys
from pathlib import Path

from adw_modules import agents, changes, gates, session, utils
from adw_modules.data_types import AgentCall, ChangeCapture, PhaseParams, ReviewOutput

REQUIRED_AGENTS = ["reviewer"]


def render_review_md(review: ReviewOutput, changeset_summary: str) -> str:
    """Turn a ReviewOutput into the markdown file this ADW promises to write.

    Small enough to stay a free function rather than a adw_modules addition —
    if it grows a second responsibility, move it to adw_modules/reports.py.
    """
    lines = [
        "# Review",
        "",
        f"**Verdict:** {'approved' if review.approved else 'changes requested'}",
        "",
        f"_{changeset_summary}_",
        "",
        "## Findings",
        "",
    ]
    for f in review.findings:
        mark = "x" if f.met else " "
        lines.append(f"- [{mark}] {f.requirement}")
        if f.evidence:
            lines.append(f"  - {f.evidence}")
    if review.blocking:
        lines += ["", "## Blocking", ""]
        lines += [f"- {item}" for item in review.blocking]
    return "\n".join(lines) + "\n"


def main(prompt: str, base: str = "main",
         config: str = "adws/adw_sssf_config/sssf.config.yaml",
         adw_id: str | None = None) -> int:
    cfg = agents.load_config(config)
    agents.validate(cfg, REQUIRED_AGENTS)
    run = session.ensure(cfg, adw_id)

    with run.phase(PhaseParams(name="request", kind="engineer", owner=run.engineer,
                               description="Capture what the review should judge the diff against")) as ph:
        ph.log(input=prompt, base=base)

    with run.phase(PhaseParams(name="changes", kind="code", owner="git",
                               description="Diff the working tree against base — two git "
                                           "commands, not a judgement call")) as ph:
        changeset = changes.capture(run, ChangeCapture(base=base))
        ph.log(base=f"{changeset.base.label} @ {changeset.base.commit[:7]}",
               reason=changeset.base.reason,
               files=len(changeset.files) + len(changeset.untracked),
               lines=f"+{changeset.insertions} -{changeset.deletions}")
        if changeset.empty:
            raise RuntimeError(
                f"nothing changed since {changeset.base.label} "
                f"({changeset.base.reason}) — there is nothing to review.")

    with run.phase(PhaseParams(name="review", kind="agent", owner="reviewer",
                               description="Rule on every requirement in the prompt, against "
                                           "the diff just captured")) as ph:
        review = ph.call(AgentCall(output_type=ReviewOutput, prompt=prompt,
                                   previous=changes.as_envelope(
                                       changeset, "Judge this diff against the request."),
                                   gates=[gates.artifacts_exist, gates.verdict_consistent]))

    with run.phase(PhaseParams(name="write_review", kind="code", owner="git",
                               description="Persist the verdict as a plain file next to the "
                                           "code it judges")) as ph:
        review_path = Path(run.repo_root) / "review.md"
        review_path.write_text(render_review_md(review, review.summary))
        ph.log(wrote=str(review_path), approved=review.approved)

    return run.finish(accepted=review.approved,
                      reason="the reviewer did not approve the current diff")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", help="inline text or a path to a prompt file — what to judge the diff against")
    parser.add_argument("--base", default="main", help="ref to diff against")
    parser.add_argument("--config", default="adws/adw_sssf_config/sssf.config.yaml")
    parser.add_argument("--adw-id", default=None, help="join or pin an existing session")
    args = parser.parse_args()
    sys.exit(main(utils.resolve_prompt(args.prompt), args.base, args.config, args.adw_id))
```

And the justfile recipe, in the same style as every other recipe in `justfile`:

```just
# reviewer only, no revise loop, writes review.md: just review "add a /health endpoint"
review *ARGS:
    uv run adws/adw_review.py --config {{config}} "$@"
```

## Commands demonstrated

| Command | What you should see | Costs money? |
|---|---|---|
| `cat adws/adw_prompt.py` | The six-line skeleton this whole episode builds on | No |
| `sqlite3 adws/adw_data/sssf.db "select seq,name,kind,owner,status from phases where adw_id='<id>' order by seq;"` | The trace of the four phases in `adw_review.py`, in order, all `success` | No — reads the trace db |
| `just review "the diff should only touch app/pricing.py and its test"` | Four phases print in order; `review.md` appears in the repo root; exit code 0 if approved, 1 if not | Yes — one reviewer agent call. `[CAST: record the actual dollar figure from `just sessions` after this run — do not guess it]` |
| `cat review.md` | The rendered findings and verdict from the run above | No |
| `just --list` | `review` now appears alongside `demo`, `sdlc`, `simple-sdlc` | No |

## Recording notes

- **[CAST: terminal]** `cat -n adws/adw_prompt.py` scrolled slowly, pausing on the four numbered setup lines and the two `with run.phase` blocks.
- **[CAST: editor]** `data_types.py` open to `PhaseParams` (line 22) with the description validator (line 31) visible and highlighted.
- **[CAST: editor]** `gates.py` open to `verdict_consistent` (line 71), scrolled so all three `report.check` calls are visible at once.
- **[CAST: terminal]** A full `just review "<a small real request against this repo>"` run, unedited, showing every phase's console line and the final exit code. Follow immediately with `cat review.md` and `just sessions` so the real cost for this run is on screen, not narrated from memory.
- **[CAST: terminal]** `sqlite3 adws/adw_data/sssf.db` phase trace for that same `adw_id`, to show the four phases lining up with the four `run.phase` blocks in the file.

## Common mistakes

- **Writing `subprocess.run` inside the `adw_*.py` file.** Symptom: the script works, but the next ADW you write duplicates the same subprocess call with slightly different flags. The fix is always to push it into `adw_modules/` first, even for a one-off — `changes.py` exists because "diff the tree" needed exactly one home.
- **A phase description that echoes its name.** Symptom: `PhaseParams` raises a `ValueError` at construction, before the run even starts — `data_types.py:49` rejects `commit_plan: "Commit the plan"` outright. Read the actual message; it names the phase and tells you why.
- **Adding an agent phase for something a shell command already answers.** Symptom: a "tester" phase that costs money and produces a report a `pytest` exit code could have given you for free. Ask the deciding question from this episode: can you write the command down? If yes, it's `kind="code"`.
- **Forgetting the `changes.empty` guard.** Symptom: the reviewer gets handed an empty diff and either stalls or invents findings about nothing. `adw_review.py` raises before that happens — copy that guard into any workflow that hands an agent a captured diff.

## Check for understanding

1. **Why does `agents.validate()` run before any phase opens, instead of failing when the first invalid agent is actually called?**
   Answer: so a half-valid config fails fast, before any session directory, agent map, or trace record is created — nothing spawns on a broken roster.

2. **What decides whether a piece of logic belongs in the `adw_*.py` file or in `adw_modules/`?**
   Answer: if it's sequencing phases or declaring agents, it stays in the script; anything else — subprocess calls, parsing, retry mechanics, reusable predicates — belongs in a module. The rule from `update_modules.md` is explicit: "ALL low-level logic lives in `adw_modules/`; ADW scripts stay thin."

3. **The `review` ADW built in this episode has no revise loop, unlike `adw_build_review.py`. Why is that the right design, not a missing feature?**
   Answer: this workflow's job is to answer one question — what does the reviewer say about the current diff — and report it, not to drive a fix cycle. A revise loop already exists in `adw_build_review.py`; adding a second one here would duplicate that responsibility rather than compose with it.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-25 | Initial draft: capstone episode, worked `adw_review.py` example built end to end from `create_adw.md` and `update_modules.md`. |
