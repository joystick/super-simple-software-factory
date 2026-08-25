---
title: "PRD — Skill Engineering: Pocock-style workflow protocols as SSSF node behaviour"
version: 1.0
updated: 2026-08-25
status: proposed
source_research: raw/research.md
---

# PRD — Skill Engineering

## Problem Statement

SSSF decides *where and when* an agent runs. It says almost nothing about *how
rigorously* the agent works once it is running.

Today a phase hands its agent two things: a system prompt from
`prompt_engineering`, and a user prompt. Those prompts describe the agent's
*role* ("implement the plan exactly") but not its *method*. The builder is free
to write code first and tests after, to skip a reproduction step when fixing a
bug, or to start generating before it has understood the request. Nothing in the
factory objects, because the gates only look at the end state.

Meanwhile a body of well-tested engineering protocols already exists as
`SKILL.md` files — `tdd`, `codebase-design`, `diagnosing-bugs`, `grill-me`.
They are exactly the missing "how". Nine of them are already installed on this
machine under `~/.claude/skills/`.

Three things stop an engineer from simply using them inside SSSF today:

1. **They are invisible to SSSF agents.** SSSF runs `claude -p` with
   `--setting-sources ''` so agents are hermetic and cheap. Verified by direct
   probe: under that flag an agent sees only built-in skills. Under
   `--setting-sources user` it sees `tdd` and `codebase-design`. The
   hermeticity that makes runs predictable is precisely what hides the skills.

2. **Machine-dependent behaviour is not reproducible.** If an agent's method
   comes from whatever the operator happens to have in `~/.claude/skills/`, then
   the same commit produces different work on a colleague's laptop or in CI, and
   the trace cannot explain why. That defeats the point of a factory.

3. **There is no place in the roster to say it.** `sssf.config.yaml` can express
   who an agent is, what it may touch, and which model it uses. It cannot
   express which engineering discipline it follows.

## Solution

Add **skill engineering** as a first-class roster concern, alongside the
existing prompt engineering and harness engineering.

An engineer vendors the skills they want into the repo, then names them per
agent:

```yaml
- name: builder
  prompt_engineering:
    system: adws/adw_data/prompt_engineering/builder/system.md
    user:   adws/adw_data/prompt_engineering/builder/user.md
  skill_engineering:
    - adws/adw_data/skill_engineering/tdd.md
    - adws/adw_data/skill_engineering/codebase-design.md
```

At call time SSSF composes the agent's system prompt from its own `system.md`
plus every named skill, and passes the result to `claude -p --system-prompt`.
The agent is still hermetic — `--setting-sources ''` is unchanged — because the
protocol arrives as *text in the prompt* rather than as a tool it must discover.

Three consequences that matter more than the mechanism:

- **Reproducible.** The skill text is a file in the repo, reviewed in a diff and
  pinned by a commit. The same commit behaves the same way on any machine.
- **Explicable.** The trace records which skills were injected into which agent,
  so "why did it work that way" has an answer.
- **Composable with what exists.** `writes:` still bounds what it may change,
  gates still check the result, the fix loop still repairs. The skill changes
  behaviour inside the box; the box is unchanged.

Enforcement stays where SSSF already puts it: **outcome gates only**. We do not
try to prove the agent wrote its test first. `tdd.md` shapes how it works; the
suite, the linter and the typechecker judge what came out. A gate that claims to
verify process but can be satisfied by a well-worded envelope is worse than no
gate — it is the placeholder problem in a new costume.

## User Stories

1. As an engineer, I want to name a skill on an agent in the roster, so that the
   agent follows that discipline on every run without me re-typing it into a
   prompt.
2. As an engineer, I want skills vendored into my repo, so that a run is
   reproducible on a colleague's machine and in CI.
3. As an engineer, I want to vendor a skill with one command, so that copying it
   by hand does not become the reason I skip it.
4. As an engineer, I want the vendored file to record where it came from and
   when, so that I can tell how stale it is.
5. As an engineer, I want `defaults.skill_engineering` to apply to every agent,
   so that a house-wide discipline is stated once.
6. As an engineer, I want a per-agent list to override the default, so that the
   scout is not carrying the builder's TDD protocol for no reason.
7. As an engineer, I want a run to fail before spawning anything if a named
   skill file is missing, so that I learn about the typo in a second rather than
   after paying for a planning phase.
8. As an engineer, I want the composed system prompt written to the session
   directory, so that I can read exactly what the agent was told.
9. As an engineer, I want the trace to record which skills each agent received,
   so that the visualizer and the database can explain a behaviour change.
10. As an engineer, I want to see the token cost of the skills I attached, so
    that discipline is a decision I make with a number in front of me.
11. As an engineer, I want a warning when an agent's composed prompt exceeds a
    configured budget, so that I do not silently double my per-turn cost.
12. As an engineer, I want the builder to follow `tdd`, so that a feature
    arrives with tests that were written to fail first.
13. As an engineer, I want the planner to follow a grilling protocol, so that
    ambiguity is resolved before the expensive build phase starts.
14. As an engineer, I want the reviewer to follow `codebase-design`, so that it
    judges module depth and interface quality rather than only correctness.
15. As an engineer, I want the fix-loop builder to follow `diagnosing-bugs`, so
    that a red gate produces a diagnosis rather than a guess.
16. As an engineer, I want skills to compose in a stated order, so that two
    skills with overlapping advice resolve predictably.
17. As an engineer, I want the agent's own `system.md` to come first, so that
    its identity outranks any borrowed protocol.
18. As an engineer, I want skill injection to work unchanged with the fix loop
    and gate corrections, so that a resumed session does not lose its protocol.
19. As an engineer, I want to attach a skill I wrote myself, so that house
    conventions travel the same road as third-party protocols.
20. As an engineer, I want `just` to tell me which skills are vendored and which
    agents use them, so that I can audit the roster without reading YAML.
21. As an engineer, I want a vendored skill to be a plain Markdown file, so that
    I can edit it for my codebase without forking anything.
22. As an engineer running `pi` agents, I want a clear statement that skill
    engineering is Claude-Code-only, so that I do not silently get nothing.
23. As a reviewer of a pull request, I want a skill change to show up as a diff,
    so that a change to how agents work is reviewable like any other change.
24. As an engineer, I want existing rosters with no `skill_engineering` key to
    behave exactly as before, so that upgrading costs me nothing.
25. As an engineer, I want the composed prompt to be deterministic, so that
    prompt caching still works and cost does not regress.

## Implementation Decisions

**A new deep module: skill composition.**
A module in `adw_modules/` owns the whole concern behind one narrow function:
given an agent's configuration and the already-rendered system text, return the
final system prompt string. Everything else — resolving paths, reading files,
ordering, separators, provenance stripping, size accounting — lives behind that
interface. It takes no `Run`, spawns no process, and touches no network, which
is what makes it testable in isolation.

The interface is deliberately narrow so it can absorb change: skill ordering
rules, a future budget policy, or a different separator convention are all
internal. Callers only ever ask for the composed text and the token accounting.

**Config schema.** `skill_engineering: list[str]` is added to `defaults` and to
`agents[]`, merged by the same key-by-key rule every other field uses — a
per-agent list replaces the default rather than appending to it, consistent with
`tools` and `harness_engineering`. Absent key means empty list, so every
existing roster is unaffected.

**Validation before spawn.** `agents.validate()` gains a check that every named
skill file exists and is non-empty, alongside the existing check for the two
prompt files. A missing skill is a config error, surfaced with the agent name
and the path, before any process starts. This mirrors how a missing
`system.md` behaves today.

**Composition order.** The agent's own system prompt first, then skills in the
order listed, each separated by a stable delimiter that names the skill. Order
is the engineer's, not alphabetical — it is meaningful, and sorting it would
silently change behaviour. Determinism matters beyond tidiness: an unstable
prompt breaks prompt caching and would show up as a cost regression.

**Delivery.** The composed text goes to `claude -p --system-prompt`.
`--setting-sources ''` and `--strict-mcp-config` are unchanged; agents stay
hermetic. This is the whole reason vendoring was chosen over re-enabling native
skill discovery.

**Persistence and trace.** The composed prompt is written to the agent's session
directory next to the existing `prompts/system.md`, so what the agent was told
is recoverable after the fact. The `agent_start` event and the agent-session row
carry the list of skills injected and their token cost.

**Cost visibility.** Skills ride in the system prompt, so they are re-sent on
every internal turn and land in the cached prefix. The composition module
reports an estimated token count; the console surfaces it at agent start, and a
configurable soft budget produces a warning — never a hard failure, since the
engineer may have decided the discipline is worth it.

**Vendoring.** A script in the skill's `scripts/` copies a named skill from a
source directory into `adws/adw_data/skill_engineering/<name>.md`, prepending a
provenance header (source path, date, and a content hash so drift is
detectable). Vendoring is a deliberate, reviewable act that produces a diff.

**Claude Code only.** `pi` agents ignore `skill_engineering`, exactly as
`claude_code` agents ignore `harness_engineering`. Both directions are stated in
`references/config.md` and warned about in validation, because a silently
ignored config field is the failure mode this repo has already been bitten by.

**Roster wiring.** The starter roster gains no skills by default — adding
unrequested cost to every install would be wrong. The documentation shows the
recommended pairings (builder + `tdd`, reviewer + `codebase-design`, planner +
a grilling protocol) and the engineer opts in.

## Testing Decisions

A good test here asserts **external behaviour** — what text comes out for a
given config — and never reaches into how composition is implemented. It must
not spawn an agent, must not call the network, and must not cost money. Prior
art is `tests/test_pricing.py`: pure functions, real inputs, exact expected
outputs, one behaviour per test, and names that state the rule being protected.

**The composition module is the one that gets thorough tests.** It is pure and
deep, which is exactly the shape that repays testing:

- an agent with no skills produces its system prompt byte-identical to today
  (the no-regression guarantee behind user story 24)
- one skill is appended after the system prompt, never before it
- multiple skills appear in the order listed, not sorted
- the same config always composes the same string (determinism, protecting the
  prompt cache)
- a missing file, an empty file, and a directory-instead-of-file each raise with
  the agent name and path in the message
- provenance headers are stripped from the injected text so they do not become
  instructions to the model
- token accounting is reported and is monotonic in the number of skills

**Validation gets tests** at the level `agents.validate()` is already exercised:
a roster naming a missing skill fails before spawn, and the error names the
agent and the path.

**Config merging gets tests**: default applies when the agent is silent; a
per-agent list replaces rather than appends; absent everywhere means empty.

**Not tested by unit tests:** that a skill actually changes model behaviour.
That is not a property code can assert. It is verified once, by hand, by running
a build phase with and without `tdd.md` attached and reading the resulting diff
and trace — and it belongs in the plan as a manual acceptance step, not as a
test that would either be flaky or vacuous.

## Out of Scope

- **Process gates.** No gate will attempt to prove a protocol was followed —
  no inspecting intermediate commits for a failing test, no requiring the
  envelope to cite a test written first. Outcome gates only.
- **Native skill loading.** No per-agent escape hatch to `--setting-sources
  user`. It was considered and rejected: it re-admits the operator's hooks,
  plugins and MCP servers, and makes runs machine-dependent.
- **New skill-shaped ADWs.** No grill-first planning workflow, no
  diagnose-first fix loop as separate scripts. Existing ADWs gain skills through
  the roster; new chains are a later question.
- **Cost routing per skill**, `/caveman`-style output compression, and
  `/handoff` context preservation between phases — all present in the research
  but unvalidated here.
- **`pi` support.** `pi` has `harness_engineering` for this purpose.
- **Automatic skill updates.** Vendored files drift by design; detecting drift
  is a reporting feature, not a sync mechanism, and shipping a silent auto-update
  would undo reproducibility.
- **Shipping vendored third-party skills in the SSSF skill itself.** Licensing
  and attribution are the engineer's call; the tool copies from a path they name.

## Further Notes

**The finding that shaped this PRD.** `--setting-sources ''` was added to make
agents hermetic, measured at 22,478 → 17,932 prompt tokens per turn. That flag
is exactly what hides user skills. This design does not undo it — it routes the
protocol in as prompt text instead, keeping the cost win and gaining
reproducibility. Had this been discovered during implementation rather than
before, the obvious fix would have been to drop the flag, and the factory would
have quietly become machine-dependent.

**Cost is the honest objection.** Skills are re-sent on every internal turn, on
top of the ~15.5k-token Claude Code base prompt that no flag removes. A 3k-token
`tdd.md` on a nine-turn build phase is real money. This is why the token count is
surfaced at agent start rather than buried: the engineer should see the price of
the discipline they are buying.

**Why the agent's own prompt comes first.** A skill is borrowed advice; the
agent's `system.md` is its identity and its output contract. When `tdd.md` and
`builder/system.md` disagree about output format, the envelope contract must
win, or the phase fails to parse and the fix is a JSON retry loop that costs
money to discover.

**Relationship to the research.** `raw/research.md` frames SSSF as the control
plane and skills as node protocols. This PRD implements exactly that seam and
nothing else. The research's broader claims — cost routing, compression,
handoff — are deliberately left for later, because each needs its own
measurement before it earns a place in the factory.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-25 | Initial PRD. Scope set to the skill layer only; vendored-injection delivery and outcome-only enforcement chosen after probing that `--setting-sources ''` hides user skills. |
