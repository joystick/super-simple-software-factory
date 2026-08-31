---
title: SSSF Skill Engineering — Pocock protocols as node behaviour
created: 2026-08-25
status: in-progress
version: 1.4
updated: 2026-08-31
---

# Plan: SSSF Skill Engineering

> Source PRD: `docs/prd-skill-engineering.md` (v1.0)
> Source research: `raw/research.md`

## Architectural decisions

Durable across every phase. Settle these once; do not relitigate them per phase.

- **Delivery mechanism**: skills arrive as **text inside `--system-prompt`**, not
  as discoverable Skill tools. `--setting-sources ''` and `--strict-mcp-config`
  stay exactly as they are. This was chosen after probing that
  `--setting-sources ''` hides user skills while `--setting-sources user`
  exposes them along with the operator's hooks, plugins and MCP servers.
- **Config key**: `skill_engineering: list[str]` on `defaults` and on `agents[]`.
  Paths, not names — the same convention `prompt_engineering` already uses.
- **Merge rule**: a per-agent list **replaces** the default, never appends.
  Identical to `tools` and `harness_engineering`. Absent key = empty list.
- **Vendor location**: `adws/adw_data/skill_engineering/<name>.md`, committed to
  the repo. Runtime lives under `data_dir`; this is deliberately *not* runtime —
  it is reviewed source, and it belongs in diffs.
- **Composition order**: agent's own `system.md` first, then skills in the order
  the engineer listed them. Never sorted. Order is meaningful and stable
  composition is what keeps the prompt cache working.
- **Precedence**: the agent's identity and output contract outrank any injected
  protocol. Where `tdd.md` and `builder/system.md` disagree about output shape,
  the envelope contract wins.
- **Enforcement**: outcome gates only. No gate ever attempts to prove a protocol
  was followed.
- **Coding-agent scope**: `claude_code` only. `pi` ignores `skill_engineering`
  exactly as `claude_code` ignores `harness_engineering`, and both directions are
  warned about rather than left silent.
- **Backward compatibility**: a roster with no `skill_engineering` key must
  compose a byte-identical system prompt to today. This is a test, not an
  aspiration.

---

## Phase 1: Tracer bullet — one skill, one agent, end to end

**User stories**: 1, 7, 8, 17, 24, 25

### What to build

The thinnest complete path: an engineer puts one skill file path on one agent in
the roster, and that skill's text provably reaches the model.

Cuts through every layer — config parsing, pre-spawn validation, composition,
delivery to `claude -p`, and persistence of what was actually sent. Hard-code
nothing about *which* skill; a single hand-placed Markdown file under
`adws/adw_data/skill_engineering/` is enough to prove the path.

Deliberately excluded so the slice stays thin: defaults merging, multiple
skills, trace events, cost reporting, the vendoring script.

### Acceptance criteria

- [x] `skill_engineering` on a single agent is parsed and reaches the code that
      builds the system prompt
- [x] The composed prompt is the agent's `system.md`, then a stable delimiter
      naming the skill, then the skill body
- [x] The composed prompt is what `claude -p --system-prompt` receives
- [x] The exact composed text is written to the agent's session directory and is
      readable after the run
- [x] A roster naming a missing or empty skill file fails in `validate()`,
      before any process spawns, with the agent name and the path in the message
- [x] An agent with no `skill_engineering` key composes a byte-identical prompt
      to the current behaviour, proven by a test
- [x] Composition is deterministic: the same config yields the same string
- [x] Verified live on the real repo with one cheap agent call, and the injected
      text is confirmed present in the session directory

**Done 2026-08-31.** `adw_modules/skill_engineering.py` (new: `compose()`,
`check()`), wired into `agents.py`'s `validate()`/`execute()`, schema in
`data_types.py`. 14 unit tests (first-ever test suite for this repo's
`adw_modules`; `pyproject.toml`/`uv.lock` added to run them via
`uv run pytest`). Reviewed via `/code-review`; two findings both fixed —
`validate()`'s fail-fast check now calls a dedicated `skill_engineering.check()`
rather than reusing `compose()` with a throwaway argument, so the two paths
can't silently diverge. Verified live: `tdd.md` vendored by hand onto a
`scout` agent in a scratch install, one real `claude_code` call
(`adw_prompt.py`, $0.0567), composed `system.md` confirmed to contain the
skill's real body after the `# --- skill: tdd ---` delimiter.

---

## Phase 2: Defaults, multiples, and ordering

**User stories**: 5, 6, 16, 19, 21

### What to build

Widen the tracer bullet to the full config surface: a house-wide default that
every agent inherits, per-agent lists that replace it, and several skills on one
agent composed in the stated order.

Includes an engineer's own hand-written skill file, since a local convention
must travel the same road as a borrowed protocol — if that path differs, the
feature has two implementations and one of them will rot.

### Acceptance criteria

- [x] `defaults.skill_engineering` applies to every agent that omits its own
- [x] A per-agent list replaces the default rather than appending to it
- [x] Absent in both places means no skills and no behaviour change
- [x] Multiple skills appear in the listed order, never sorted
- [x] Each skill is separated by a delimiter that names it, so the model — and a
      human reading the persisted prompt — can tell where one protocol ends
- [x] A repo-local, hand-authored skill file works identically to a vendored one
- [x] Config-merge behaviour is covered by tests at the level `validate()` is
      already exercised

**Done 2026-08-31.** One line in `load_config()` (mirrors the existing
`harness_engineering` merge exactly) plus `ConfigDefaults.skill_engineering`.
6 new tests: the four merge-rule cases (inherit, replace, explicit-empty-stays-
empty, absent-everywhere) plus multi-skill ordering and a hand-authored-vs-
vendored equivalence check. `/code-review`: no findings. Verified live against
the real stamped config in a scratch install — `defaults.skill_engineering`
correctly reached all 5 roster agents via `load_config()`.

---

## Phase 3: Trace and cost visibility

**User stories**: 9, 10, 11

### What to build

Make skill injection visible in the two places an engineer looks: the terminal
while it runs, and the database afterwards.

Skills ride in the system prompt and are therefore re-sent on every internal
turn, on top of the ~15.5k-token Claude Code base prompt. That cost must be a
number the engineer sees at the moment they are paying it, not a surprise on an
invoice. A soft budget warns; it never fails a run, because the engineer may
have decided the discipline is worth the money.

### Acceptance criteria

- [x] The `agent_start` event carries the list of skills injected
- [x] The agent-session row records the same, so history explains behaviour
- [x] The console reports skills and their estimated token cost at agent start,
      through `run.console` and never a bare `print()`
- [x] A configurable soft budget emits a warning when the composed prompt
      exceeds it, and does not fail the run
- [x] Token accounting is monotonic in the number of skills attached
- [x] A trace from a run with skills can be read back and answers "which
      protocols was this agent given"

**Done 2026-08-31.** `skill_engineering.estimate_tokens()` (chars/4 heuristic,
explicitly labelled "est." wherever a human reads it — a `/code-review`
finding caught the first version presenting it as a bare number). Console
gained `skill_engineering_report()`: silent when no skills, else reports
names + estimate, warns (never raises) over budget. `agent_sessions` gained
`skill_engineering_json`/`skill_tokens_estimate` columns via the existing
additive-migration pattern. `skill_token_budget` is per-agent overridable
(defaults to inheriting `defaults.skill_token_budget`) — a second
`/code-review` finding caught the first version being defaults-only, which
would have judged an agent against a budget that didn't track its own
skill list. 13 new tests. Verified live: real `claude_code` call with a
deliberately tiny budget (50 tokens) — console printed both the skill
report and the over-budget warning, the run still succeeded, and both the
`agent_start` event and the `agent_sessions` row in the real sqlite db
were queried directly and confirmed correct (891-token estimate, `tdd.md`
named in both).

---

## Phase 4: Vendoring with provenance

**User stories**: 2, 3, 4

### What to build

One command that copies a named skill from a source directory into
`adws/adw_data/skill_engineering/`, stamping a provenance header: where it came
from, when, and a content hash so later drift is detectable.

Vendoring is a deliberate, reviewable act that produces a diff. There is no
auto-update and no sync: silently refreshing a vendored skill would undo the
reproducibility the whole design exists to buy.

The provenance header must be stripped before injection — a comment about where
a file came from is not an instruction to the model, and leaving it in the
prompt is both noise and a small correctness risk.

### Acceptance criteria

- [x] A single command vendors a named skill from a path the engineer supplies
- [x] The vendored file carries source path, date, and a content hash
- [x] Re-vendoring an unchanged skill is a no-op or a clearly reported no-change
- [x] Drift against the source is detectable and reported
- [x] The provenance header is stripped from the text that reaches the model,
      proven by a test
- [x] The vendored file is plain Markdown the engineer can edit in place
- [x] Nothing is auto-updated, ever

**Done 2026-08-31.** `scripts/vendor_skill.py` — `vendor()`/`check_drift()`
as a testable core behind a thin CLI, `--check` for drift, non-zero exit on
drift for scripting. `skill_engineering.py`'s `_read()` strips the header
automatically, so `compose()`/`check()`/`estimate_tokens()` all get it for
free. 14 new tests.

One real bug was caught only by live testing, not by the test suite, and is
fixed in this diff: every actual Pocock skill file is literally named
`SKILL.md` (identity lives in the parent directory —
`~/.claude/skills/tdd/SKILL.md`), but the original default-naming logic used
the source file's own stem, so it would have vendored every skill in a
roster to the same destination and silently clobbered each other. All the
hand-written test fixtures happened to use filenames that already matched
the real skill name, masking it. Fixed with a parent-directory fallback for
the literal `SKILL.md` case, plus a regression test using the real shape.

`/code-review` found three more real issues, all fixed: (1) `vendor()` would
silently overwrite a hand-authored file with no provenance header — now
raises `HandAuthoredFileError` and touches nothing; (2) the CLI let that
exception surface as a raw traceback instead of a clean message — now
caught in `main()`; (3) the two provenance-header regexes
(`vendor_skill.HEADER_RE` and `skill_engineering.PROVENANCE_HEADER_RE`) are
necessarily defined independently — `skill_engineering.py` ships stamped
into every target repo, `vendor_skill.py` stays in the skill source and
never is — so a parity test now asserts they agree on real fixtures, and
the header regex was tightened (exact source/date/sha256 shape, not a loose
match) so a skill file that merely *documents* this feature in prose can't
be mistaken for a real header and stripped.

**Not fixed, considered:** `_default_name()` only special-cases the literal
stem `"skill"`. Every real Pocock skill observed in this environment uses
that one convention; generalizing to hypothetical others (`INSTRUCTIONS.md`,
etc.) with no example to test against would be speculative.

Verified live throughout, not just in tests: vendored the real
`~/.claude/skills/tdd/SKILL.md`, confirmed re-vendor no-op, confirmed drift
detection on a mutated scratch source, confirmed the hand-authored refusal
leaves the original file byte-for-byte untouched, and ran one real
`claude_code` call with the vendored skill attached — the persisted
`system.md` had zero provenance-header matches and the real skill body
present.

---

## Phase 5: Documentation, guidance and audit

**User stories**: 12, 13, 14, 15, 20, 22, 23

### What to build

Make the feature discoverable and its limits explicit — the failure mode this
repo has already been bitten by is a config field that is silently ignored.

Recommended pairings are documented but **not** enabled in the starter roster:
adding unrequested per-turn cost to every fresh install would be wrong.

An audit recipe answers "which skills are vendored, and which agents use them"
without reading YAML.

### Acceptance criteria

- [ ] `references/config.md` documents `skill_engineering`, the merge rule,
      composition order, precedence, and the cost implication
- [ ] A cookbook covers vendoring and attaching a skill end to end
- [ ] `skill_engineering` under `pi` and `harness_engineering` under
      `claude_code` are both documented as ignored, and both warn at validation
- [ ] Recommended pairings are documented — builder + `tdd`, reviewer +
      `codebase-design`, planner + a grilling protocol, fix-loop builder +
      `diagnosing-bugs` — and none is enabled by default
- [ ] A `just` recipe lists vendored skills and the agents that use them
- [ ] The template roster and the skill's own templates stay consistent with the
      repo copy, so a fresh install does not reintroduce stale claims

---

## Phase 6: Manual acceptance — does it actually change the work?

**User stories**: 12, 14, 15

### What to build

Not code. The one claim this feature makes that no unit test can assert: that
attaching a protocol changes what the agent produces.

Run the same small feature request twice through a real build phase — once with
`tdd.md` attached to the builder, once without — from the same clean baseline,
changing only the skill list. Compare the resulting diffs, the test files, the
order of work visible in the trace, and the cost.

Record the result honestly in the plan, including the possibility that it makes
little difference. A negative result is worth knowing before rolling the pattern
across a roster, and this repo has already twice found that a change which
"obviously" worked did nothing measurable.

### Acceptance criteria

- [ ] Two runs from an identical baseline, differing only in `skill_engineering`
- [ ] Both diffs, both traces, and both costs captured
- [ ] A written comparison: what changed in the work, and what it cost per turn
- [ ] An explicit recommendation on whether the default roster should adopt any
      pairing, with the evidence behind it
- [ ] The repo is left clean; any scratch commits or branches are removed

---

## Risks and open questions

- **Cost may outweigh benefit.** A 3k-token protocol on a nine-turn build phase
  is real money, re-sent every turn. Phase 6 exists to answer this with numbers
  rather than intuition.
- **Skill text is written for interactive sessions.** Pocock's skills assume a
  human is present to answer questions. `grill-me` in particular may be actively
  wrong inside a headless run that has nobody to grill — the planner could stall
  or invent answers. Attach grilling protocols to the planner only after Phase 6
  has been run against one.
- **Prompt-contract collisions.** A skill instructing the model to output prose
  will fight the envelope's JSON contract, and the symptom will be a JSON retry
  loop that costs money to diagnose. Precedence is documented; Phase 1's
  ordering test is the guard.
- **Vendored skills drift** from upstream by design. Phase 4 reports drift; it
  never resolves it.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.4 | 2026-08-31 | Phase 4 done — see its acceptance criteria for what shipped and how it was verified. |
| 1.3 | 2026-08-31 | Phase 3 done — see its acceptance criteria for what shipped and how it was verified. |
| 1.2 | 2026-08-31 | Phase 2 done — see its acceptance criteria for what shipped and how it was verified. |
| 1.1 | 2026-08-31 | Phase 1 done — see its acceptance criteria for what shipped and how it was verified. |
| 1.0 | 2026-08-25 | Initial plan. Six vertical slices from PRD v1.0; scope limited to the skill layer. |
