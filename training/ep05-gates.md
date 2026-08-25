---
title: "Episode 5 — Gates: making the factory actually check things"
version: 1.0
updated: 2026-08-25
episode: 5
duration_target: "10 minutes"
prerequisites: [1, 2, 3, 4]
---

# Episode 5 — Gates: making the factory actually check things

## Learning objectives

By the end of this episode you can:

- Find and read the placeholder blocks in `quality.py` and explain why they ship as no-ops.
- Wire a real quality block: argv as a list, bare binary names, strictness parked in `pyproject.toml`.
- Name the three wired gates in this repo — pytest, ruff, mypy `--strict` — and what each one owns.
- Verify a gate by mutation: break the code on purpose and confirm the right gate, and only the right gate, goes red.
- Explain, using two real bugs from this repo, why a mutation that stays green means the test is the defect, not the tool.

## Cold open (≤45s)

Here's a fact that should worry you: a quality gate that always passes and a
missing quality gate produce the exact same trace entry — "quality: passed."
One of them checked something. The other is lying by omission. In this repo,
the freshly stamped factory ships with gates that are `echo` commands. They
exit 0. They print a message admitting they're fake. And if you never replace
them, every run of `just sdlc` reports a green test phase for a suite that
never ran. This episode is about closing that gap, and about a harder lesson
underneath it: even a gate that runs a real tool can stay green while the
thing it's testing is broken — because the test itself is wrong. We're going
to prove both problems by breaking things on purpose.

## Script

| Time | Visual | Narration |
|---|---|---|
| 0:00–0:45 | Cold open, terminal showing `just quality` output from a hypothetical unwired repo (see Recording Notes) | (as written above) |
| 0:45–1:30 | Editor: `adws/adw_modules/quality.py:1-29`, banner comment highlighted | "Open `quality.py`. The whole file starts with a banner in a box. It says: every block ships as an echo that exits 0, and that's on purpose. A freshly stamped repo has no way to guess your test runner. A wrong-but-plausible guess that silently passes is worse than a check that admits it's fake." |
| 1:30–2:15 | Editor: `quality.py:49-52`, `_placeholder()` function | "Here's the function. `_placeholder` returns `echo`, plus your block's name, plus a message telling you to go edit this file. Every one of `test`, `lint`, `typecheck` used to call this. In a fresh SSSF install, they still do — until you wire them." |
| 2:15–3:15 | Editor: `quality.py:138-167`, the three wired functions in this repo | "In this repo, they're already wired. `test` at line 138 runs pytest. `lint` at 149 runs ruff. `typecheck` at 160 runs mypy. Notice the shape: `argv=[\"uv\", \"run\", \"--with\", \"pytest\", \"pytest\", \"-q\"]`. That's a Python list, not a string you'd type in a shell." |
| 3:15–4:00 | Editor: `quality.py:62-67`, `_run()` calling `subprocess.run(spec.argv, ...)` and `shlex.join` only for the log | "Why a list? Line 76: `subprocess.run(spec.argv, ...)`. No shell in between. A list means no quoting bugs and no shell injection — whatever's in that list is exactly what runs, argument by argument. `shlex.join` only reconstructs a readable string for the log." |
| 4:00–4:45 | Editor: `quality.py:24-28` banner rule 2, then `pyproject.toml` open side by side | "Second rule: call binaries by bare name. `bun`, `uv`, `pytest` — never an absolute path like `/Users/you/.bun/bin/bun`. These blocks inherit your own shell environment, so the bare name resolves the same way it does in your terminal. And scope and strictness — which files, how strict — live here, in `pyproject.toml`, not in the argv." |
| 4:45–5:30 | `pyproject.toml`, `[tool.ruff]` and `[tool.mypy]` sections | "Look: ruff's `include` list and `select` list are here. Mypy's `strict = true` and `files` list are here. The comment above them says why: a gate whose strictness moves when the tool updates is a gate that fails on a day nobody touched the code. Keeping it in one file means the gate and you, running `ruff check` by hand, can never disagree about what counts as a violation." |
| 5:30–6:15 | Terminal: `just quality "verify gates for training episode"` running live | "Let's run it for real. `just quality` — zero agents, this costs nothing. [CAST: full terminal output]. Three checks, three passes: test, lint, typecheck, in 2.9 seconds." |
| 6:15–8:00 | Terminal: three mutation experiments in sequence, each followed by `just quality`, each restored | "Now the actual exercise. Break one thing, run the gate, watch exactly one check turn red, then put it back. First: add an unused import to `app/pricing.py`. Run quality. [CAST] Lint fails. Test and typecheck still pass — an unused import doesn't change behavior or types, only style. Second: strip the `percent: float` type annotation off `_percent_of`. Run quality. [CAST] Typecheck fails, alone. Third: in `_percent_of`, change `Decimal(str(percent))` to `Decimal(percent)`. Run quality. [CAST] Test fails, alone — one specific test, `test_fractional_percent_goes_through_the_exact_decimal_path`, catches it. Each time, restore the file and check `git status` is clean before moving on." |
| 8:00–9:15 | Editor: `tests/test_pricing.py:107-118` and commit `2f49eb0` in `git log` | "Here's where it gets uncomfortable. Commit `2f49eb0` in this repo's history. The test `test_discounts_never_exceed_the_subtotal` used two 100% discounts. Delete the `min()` clamp in `_clip_to` — the function that's supposed to stop a discount stack from paying the customer — and that test stayed green. Why? The first 100% discount alone already hits the ceiling; the loop's `if running >= ceiling: break` fires before `min()` is ever consulted. The clamp could vanish and nothing noticed. The fix wasn't touching the code — it was writing a test where the SECOND discount overflows only partly: 60% plus 60% of 1,000 cents is 1,200, so it must trim to the 400 left, not take all 600 or drop to 400. That's the case that actually exercises the clamp." |
| 9:15–9:50 | Editor: `tests/test_pricing.py:172-183`, the comment explaining the float boundary | "Second story, same shape. `_percent_of` uses `Decimal(str(percent))`. Every percentage the old suite used — 5, 12.5, 7.25, 7.0 — happens to be exactly representable in binary float. So `Decimal(str(percent))` and the wrong `Decimal(percent)` agree on all of them; the str() guard was never actually exercised. 8.7 is the case that differs: as a float it's a hair under 8.7, so 8.7% of 500 cents lands right on the 43.5-cent boundary — the exact path rounds up to 44, the float path truncates to 43. One cent taken off the customer, and nothing in the suite could see it until that exact case was added." |
| 9:50–10:00 | Editor: `gates.py:27-44`, `artifacts_exist` and `files_non_empty` | "One more gate family, quickly: these don't check code, they check an agent's claims. If an agent's envelope says it wrote a file, `artifacts_exist` checks the file is actually there. `files_non_empty` checks it isn't zero bytes. Same principle — verify, don't trust." |

## Commands demonstrated

- `just quality "verify gates for training episode"` — runs pytest, ruff, mypy in sequence. Free (zero agents). Expect three passes in a few seconds on a clean tree.
- `uv run --with pytest pytest -q` — the bare command the `test` block runs. Free. Run it directly to confirm it matches the gate exactly.
- `uv run --with ruff ruff check` — the bare command the `lint` block runs. Free.
- `uv run --with mypy mypy` — the bare command the `typecheck` block runs. Free.
- Mutation 1 (lint): add `import os` unused near the top of `app/pricing.py`, run `just quality`, confirm only lint fails, then remove the line.
- Mutation 2 (typecheck): remove the `: float` annotation from `_percent_of`'s `amount_cents` parameter in `app/pricing.py`, run `just quality`, confirm only typecheck fails, then restore it.
- Mutation 3 (test): in `_percent_of`, change `Decimal(str(percent))` to `Decimal(percent)`, run `just quality`, confirm only test fails, then restore it.
- `git status --short` — run after each restore. Must show no diff in `app/pricing.py` before moving to the next mutation.

## Recording notes

- `[CAST: adws/adw_modules/quality.py:1-29]` — the banner comment, full width, legible.
- `[CAST: just quality "verify gates for training episode" full output]` — captured live in this session: 3/3 checks passed, test 1.2s, lint 0.2s, typecheck 1.6s, total phase 2.9s, cost $0.0000.
- `[CAST: mutation 1 — unused import]` — captured live: lint failed (exit 1), test and typecheck passed.
- `[CAST: mutation 2 — stripped annotation]` — captured live: typecheck failed (exit 1), test and lint passed.
- `[CAST: mutation 3 — Decimal(percent)]` — captured live: test failed (exit 1), lint and typecheck passed. Show the pytest failure naming `test_fractional_percent_goes_through_the_exact_decimal_path` if it fits on screen.
- `[CAST: git log commit 2f49eb0 --stat and full message]` — show the commit message in full; it states the war story better than paraphrase.
- `[CAST: tests/test_pricing.py:107-118 and :172-183]` — the two comments explaining why each mutation needed a specific value to be caught.
- Producer note: for the cold open, either record an unwired stamped repo once and reuse the clip, or narrate over the static banner text in `quality.py:1-29` instead of a live unwired run — this repo's gates are already wired, so there's no live "echo passes" moment to capture here without a separate checkout.

## Common mistakes

- **Writing argv as a shell string.** `argv="pytest -q"` instead of `argv=["pytest", "-q"]` breaks `subprocess.run` (no shell to parse it) or, worse, invites exactly the injection/quoting bugs the list form exists to avoid. Symptom: `FileNotFoundError` naming the whole string as the binary.
- **Hard-coding an absolute binary path.** `argv=["/Users/you/.local/bin/uv", ...]` runs on your machine and fails everywhere else, including CI. Symptom: gate works locally, fails with exit 127 for a teammate.
- **Putting strictness in the argv instead of pyproject.toml.** `argv=["ruff", "check", "--select=E,F"]` means a developer running `ruff check` locally sees different violations than the gate does. Symptom: "it's clean on my machine" tickets.
- **Trusting a green mutation test.** If you break something and the gate stays green, the instinct is to shrug and move on. The two war stories in this episode are both cases where that shrug was wrong — the test was blind to exactly the case that mattered. Symptom: a gate that has "always passed" on a code path nobody has actually exercised.

## Check for understanding

1. **Q: Why does `argv` have to be a list rather than a shell string?**
   A: `subprocess.run` executes the list directly with no shell in between, so there's no quoting to get wrong and no shell-injection surface. A shell string would need a shell to parse it, reintroducing both risks.

2. **Q: You add an unused import to `app/pricing.py` and run `just quality`. Which check fails, and why do the other two still pass?**
   A: Only `lint` fails — ruff's pyflakes rule (`F`) flags unused imports. `test` and `typecheck` still pass because an unused import changes neither runtime behavior nor any type signature.

3. **Q: The `test_discounts_never_exceed_the_subtotal` test used two 100%-discounts and stayed green after the `min()` clamp in `_clip_to` was deleted. Why didn't it catch the regression, and what test did?**
   A: The first 100% discount alone already reached the subtotal ceiling, so the loop's `break` fired before `min()` was ever reached — the clamp was never exercised. The fix was `test_the_overflowing_discount_is_clipped_not_dropped`, using 60% + 60%, where the second discount overflows only partly and must be trimmed rather than taken whole or dropped.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-25 | Initial episode script. |
