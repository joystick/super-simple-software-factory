---
title: Quality blocks
---

# Quality blocks

A **quality block** is an operator-authored, deterministic check — `test`,
`lint`, `typecheck`, `build` — that an ADW chain runs *between* agent phases
as plain code, not as an agent. Each block is one function in the per-repo,
stamped file `adws/adw_modules/quality.py` that wraps a single `argv` list in
a `QualityCheckSpec` and hands it to `_run()`, which executes it as a
subprocess in the operator's own environment and records the exit code
(template source: `.claude/skills/sssf/templates/adws/adw_modules/quality.py`,
blocks at lines 138–174, runner at 62–132). `run_quality()` (lines 214–240)
runs every block in the list and collects *all* failures in one pass;
`run_tests()` (177–190) runs the test block alone as the chain's
deterministic test phase.

## Why it exists

The file's own docstring states the principle: "A known command is not a
judgement call. Anything whose invocation you can write down belongs here as
code — it runs in milliseconds, costs nothing, and returns the same answer
every time. Agents are for the parts that need reading and deciding"
(`quality.py:3-6`). `run_tests()` is explicitly "what replaces a `tester`
agent once the command is written down" (`quality.py:180`) — an agent
rediscovering the test runner every run is pure cost.

Two design points follow from that:

- **Failures flow back through the same door as agent output.** A
  `QualityResult` is adapted by `as_envelope()` (`quality.py:193-211`) into a
  `VerifyOutput` envelope, so a failing lint or test reaches the builder
  exactly as an agent's report would; the ADW script is the only thing that
  knows the difference. Each failure carries the command, its exit code, and
  the last `TAIL_CHARS` (4,000) of verbatim output — "trust it over any
  summary" (`quality.py:206-208`).
- **A failing block does not fail the phase.** `run_quality()`'s ordering
  contract: "The runner did its job; the CODE is what failed. Hand this
  result to the builder and let the bounded repair loop decide the run's
  fate" (`quality.py:217-219`).

## The PLACEHOLDER trap

A freshly stamped repo ships **every block as an `echo` that exits 0** and
announces it is fake (`_placeholder()`, `quality.py:49-52`; banner at
`quality.py:8-28`). This is deliberate — a stamped repo cannot guess your test
runner, and a wrong-but-plausible command that silently passes is worse than
one that says so out loud. But `run_quality()` reports an `echo` block as
*passed*, so an unwired factory produces green traces that prove nothing.
That is what `quality-gates-and-permissions/Rule-zero.md` exists to prevent:
run `just quality "baseline"`, and if the output says `PLACEHOLDER`, wire the
blocks before any agent writes a line — then break one thing and confirm
exactly one block goes red (`docs/playbook-adopting-sssf.md`, "Rule zero"
section). Delete blocks you do not have rather than leaving an `echo` in
place: "a `build` block running `echo` is a phantom check" (playbook, A2).

Rules for the real command (`quality.py:22-27`; playbook, Rule zero closing
paragraph): `argv` is a **list**, never a shell string; call binaries by
**bare name** so they resolve via `utils.operator_env()`; put scope and
strictness in config files (`pyproject.toml`, `package.json`), not the argv.

## How it differs from a Gate and from Permissions

| Mechanism | Who authors it | What it checks |
|---|---|---|
| Quality block | the operator, per repo, in `quality.py` | the code externally — does it lint, typecheck, build, test |
| `Gate` | built-in, mechanical | an agent's *envelope claims* against what is on disk |
| Permissions / `writes` | built-in, config-driven | that the agent touched only what it was allowed to |

All three answer "how do we know an agent's work is real" from a different
angle; a quality block is the only one that knows anything about *your*
project's toolchain, which is why it is the one that ships blank.

## See also

- `quality-gates-and-permissions/Rule-zero.md` — the adoption step that
  wires the blocks and proves each one can fail.
- `quality-gates-and-permissions/Gate.md` — the mechanical check on
  envelope claims.
- `quality-gates-and-permissions/Permissions-and-writes.md` — write-boundary
  enforcement.
- `docs/playbook-adopting-sssf.md` — "Rule zero" and "A2. Wire the gates".
- `../../training/site-starlight/src/content/docs/02-gates-deep-dive/lessons/0001-three-gates-you-have-watched-fail.mdx`
  — the hands-on lesson on watching each check fail.
