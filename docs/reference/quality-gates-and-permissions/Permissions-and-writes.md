---
title: Permissions and writes
---

# Permissions and writes

`writes` and `protected_files` are the config-level policy for what an agent
may change; `snapshot()`/`enforce()`/`PermissionBreach` in
`adw_modules/permissions.py` are the code that actually holds that policy to
account, after the fact, against the real git tree.

## Why it exists (verified, not trusted)

`tools:` on a roster entry is a capability list, not a sandbox, and
`permissions.py`'s own module docstring names the two holes plainly:

- `bash` runs anything. A builder handed bash to run a test suite can also
  run `git checkout adws/` — not hypothetical, per the docstring: one did,
  discarding uncommitted changes to the very quality check it was about to
  be judged by.
- `write` reaches any path, not just the one report file an agent was
  configured for. A reviewer with no `edit` tool "so it cannot quietly fix"
  could still rewrite the code it was reviewing through `write`.

So SSSF doesn't try to sandbox tool calls in real time. It verifies the
outcome the same way every other claim in the system is verified — after the
fact, against the repo itself. Source:
`.claude/skills/sssf/templates/adws/adw_modules/permissions.py:1-30`.

## The two config keys

Both live in `sssf.config.yaml`:

- `defaults.protected_files` — paths **no** agent may touch unless it names
  them itself in its own `writes` list.
- `agents[].writes` — `None` = unrestricted, `[]` = read-only, a list = only
  those paths (naming a path here is what unlocks an otherwise-protected
  one).

(`permissions.py:27-29`)

## `snapshot()` and `enforce()`

`snapshot(run)` fingerprints every path the working tree currently differs
on **before** an agent runs — numstat counts for tracked files (so an edit to
an already-dirty file still registers), plain names for untracked files.
Gitignored paths never appear at all, which is why the session runtime under
`data_dir` needs no special case. (`permissions.py:50-68`)

`enforce(run, phase, agent, before)` re-snapshots afterward, diffs the two,
and checks every changed path against `permitted()`. Anything not permitted
is a breach. (`permissions.py:163-186`)

Comparing change-**sets**, rather than watching writes happen live, is what
catches the `git checkout` case from the module docstring: a path that was
dirty before the agent ran and is clean afterward has been *reverted* — and a
reversion counts as a modification just like any other change.

## `always_writable`

`always_writable(cfg)` returns `[data_dir + "/"]` — the session runtime every
agent must be able to write regardless of its `writes` list, because that's
where `context_handoff/`, prompts, `raw_output.jsonl`, and `envelope.json`
land. A read-only agent is read-only **with respect to the repo**, never with
respect to its own report. (`permissions.py:110-124`)

`permitted(path, agent, cfg)` checks in order: always-writable first, then
the agent's own `writes` list, then `protected_files`, then falls back to
`agent.writes is None` (unrestricted). (`permissions.py:127-135`)

## `PermissionBreach`

`PermissionBreach(RuntimeError)` — raised by `enforce()`, never caught and
retried. This is the key difference from a Gate
(`quality-gates-and-permissions/Gate.md`): a gate failure is a claim that
didn't check out, recoverable by re-prompting the same session. A breach
already happened on disk — the write occurred — so re-prompting can't undo
it. `enforce()` rolls back what it can (`_roll_back`, `permissions.py:138-160`)
and aborts the phase, naming every offending path in the exception message.
(`permissions.py:41-42, 163-186`)

One subtlety worth internalizing: `_roll_back` only touches paths the agent
itself introduced. A path that was already dirty before the agent ran and
gets reverted by the agent is reported as
`REVERTED-BY-AGENT (uncommitted work lost, cannot restore)` rather than
silently "fixed" — discarding an operator's pre-existing uncommitted work to
tidy up would be the exact harm this module exists to prevent, just
committed by the cleanup step instead of the agent. (`permissions.py:138-151`)

## See also

- `quality-gates-and-permissions/Gate.md` — the companion mechanism for
  verifying *what an agent claims it did*, as opposed to *what it touched*.
- `quality-gates-and-permissions/Console.md`
- `.claude/skills/sssf/references/config.md#write-permissions--writes-and-protected_files` —
  the config-shape side of `writes`/`protected_files` (field syntax,
  defaults merging); this page covers the enforcement code that reads them.
