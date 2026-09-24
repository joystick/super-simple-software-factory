---
title: ChangeSet and BaseRef
---

# ChangeSet and BaseRef

`ChangeSet` is the record of what changed in the repo since a base commit —
"pure git facts, no judgement" — and `BaseRef` is the part of it that says
*which* commit that was and *why* it was chosen. Both are produced by code
(`adw_modules/changes.py`), never by an agent; an agent only ever receives
the result, adapted into a `ChangesOutput` envelope. The module docstring
states the principle:

> "What changed since main" is not a judgement call — it is two git commands
> and a subtraction. So it is code, and an agent is only handed the result.

Source: `.claude/skills/sssf/templates/adws/adw_modules/changes.py:1-14`.

## Why it exists

The documenter in `adw_simple_sdlc.py` has to write up "the work that was
just done." Asking an agent to figure out what that is would cost a context
window and produce a claim; running `git diff` costs nothing and produces a
fact. But a diff is only meaningful relative to a base, and that base is not
obvious — is it `main`? the working tree? the last commit? — so the harness
resolves it explicitly and **records the reasoning** in `BaseRef.reason`,
"so the trace never leaves you guessing what a diff was measured against"
(`changes.py:8-13`). `BaseRef`'s own docstring: "A diff is only as
trustworthy as the thing it was taken against, so the ADW records that
choice instead of leaving the reader to infer it." (`data_types.py:186-190`)

## The types

All in `.claude/skills/sssf/templates/adws/adw_modules/data_types.py`:

| Type | Lines | Role |
|---|---|---|
| `ChangeCapture` | 177-182 | the *input* — `base` (default `"main"`), `max_diff_lines` (2000), `include_untracked` (True); one object per the four-param rule |
| `BaseRef` | 185-202 | `ref` (what was asked for), `commit` (what was actually diffed against), `reason`; `.label` shortens a raw sha to 7 chars |
| `ChangeSet` | 205-219 | `base: BaseRef`, `files`, `untracked`, `insertions`, `deletions`, `stat`, `diff_path`, `truncated`; `.empty` = no files and no untracked |
| `ChangesOutput` | 222-234 | `EnvelopeBase` subclass — the same facts flattened into envelope fields so an agent can consume them |

## How the base is resolved

`resolve_base(ref)` (`changes.py:24-49`) starts from `merge_base(ref, HEAD)`
and then picks one of four cases, each writing its own `reason`:

| Situation | `commit` used | `reason` |
|---|---|---|
| HEAD is ahead of the base | the merge-base | "HEAD is ahead of `<base>` — diffing every commit since, plus the working tree" |
| On the base, dirty tree | the merge-base | "HEAD is on `<base>` — diffing the uncommitted working tree" |
| On the base, clean tree | `HEAD~1` | "HEAD is on `<base>` with a clean tree — falling back to the last commit" |
| On the base, clean, no parent | the merge-base | "... with a clean tree and no parent commit" |

The third row is the one that makes the documenter work at all: by the time
it runs, the chain has already committed the code, so a naive "diff the
working tree" would find nothing. Missing base refs and non-repos raise
immediately with an actionable message rather than diffing against nothing
(`changes.py:26-33`).

## What `capture()` writes

`capture(run, params: ChangeCapture) -> ChangeSet` (`changes.py:52-84`) runs
the git commands and persists the evidence to
`context_handoff/changes.diff` with a header naming the base, the reason,
and the counts, then `## stat`, `## untracked files`, and the `## diff`
(truncated at `max_diff_lines`, with a note saying how to get the rest).
Untracked files are listed by name explicitly because "Untracked files are
absent from `git diff` by construction, so they are named here rather than
silently missing from the record" (`changes.py:68-70`).

`as_envelope(changes, notes)` (`changes.py:87-103`) then wraps the `ChangeSet`
as a `ChangesOutput` whose `artifacts` is the diff path and whose `base`
string is `"<label> @ <sha> — <reason>"` — the one door every handoff uses.

## In the chain

`adw_simple_sdlc.py` pins `baseline = git_helper.rev("HEAD")` before its
first commit (`:65`), because the run itself moves `main`
(`:39-41`). After `commit_build` it captures against that pinned sha, logs
`base`/`reason`/`files`/`lines`/`diff` to the trace, and raises if
`changeset.empty` — "there is nothing to document" (`:150-161`). The
documenter's `previous=` is then `changes.as_envelope(changeset,
DOCUMENT_NOTES)` (`:165-167`).

## See also

- `core-execution-model/AgentCall.md` — how a `ChangesOutput` reaches the
  documenter through `previous=`.
- `core-execution-model/Four-param-rule.md` — why `capture()` takes a single
  `ChangeCapture` object.
- `handoff-and-output/Session-layout.md` — where `context_handoff/changes.diff`
  lands inside the session directory.
