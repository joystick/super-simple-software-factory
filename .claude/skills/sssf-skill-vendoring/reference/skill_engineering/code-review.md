<!-- sssf:vendored
source: ~/Projects/training/super-simple-software-factory/downloads/skills/skills/engineering/code-review/SKILL.md
date: 2026-09-14
sha256: 47f4e52c21694def9c7c11cbfbf891ca35eac7a93e395797515be3c8a409ae50
-->
<!-- sssf:flattened
dropped: agents/openai.yaml -- harness display metadata, no prompt content
dropped: description "Runs both reviews in parallel sub-agents" -- the reviewer has no sub-agent/Task tool; now "Runs the two axes one after the other, keeping their findings separate"
dropped: intro "a fixed point the user supplies" and "Both axes run as parallel sub-agents" -- the fixed point is HEAD and the change is the uncommitted working tree (the build commit lands after an approved review in adw_simple_sdlc/adw_build_review); axes run in sequence with separate notes
dropped: intro issue-tracker line (docs/agents/issue-tracker.md, /setup-matt-pocock-skills) -- the spec comes from plan.md or prompt, not a tracker
dropped: step 1 "ask for it", git diff <fixed-point>...HEAD, git log commit list, git rev-parse check -- HEAD...HEAD is empty while the change is uncommitted; replaced with git diff HEAD + git status --porcelain cross-checked against previous_envelope.changed_files; an empty diff is reported as a finding
dropped: step 2 four-item spec lookup (commit-message issue refs, user argument, file search, ask the user) -- replaced with the reviewer's rule: <context_handoff_dir>/plan.md if it exists, else prompt verbatim
dropped: step 4 "Spawn both sub-agents in parallel" prompt-contents framing, commit list, "the sub-agent has no other access", per-sub-agent "Under 400 words" -- no Task tool; the reviewer runs Standards then Spec itself, each brief kept as that axis's checklist
dropped: step 5 "verbatim or lightly cleaned" -- there are no sub-agent reports to clean; sections now named as part of <context_handoff_dir>/review.md
-->

---
name: code-review
description: "Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/spec asked for?). Runs the two axes one after the other, keeping their findings separate, and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to \"review since X\"."
---

Two-axis review of the uncommitted changes in the working tree, measured against `HEAD`:

- **Standards**: does the code conform to this repo's documented coding standards?
- **Spec**: does the code faithfully implement the originating issue / spec?

The two axes run **one after the other, each with its own notes**, so neither pollutes the other's judgement; then this skill aggregates their findings.

## Process

### 1. Pin the fixed point

The fixed point is `HEAD`. The change under review is what the builder left uncommitted in the working tree.

Capture the diff command once: `git diff HEAD` (staged and unstaged changes together). Also list the working tree with `git status --porcelain`: new untracked files (`??`) don't appear in `git diff HEAD`, so read them directly. Cross-check both against `previous_envelope.changed_files`; a file one side names and the other doesn't is worth a note.

Before going further, confirm the change is non-empty. If `git diff HEAD` and `git status --porcelain` both show nothing, report that as a finding: there is no change to review. An empty change should surface here, not halfway through two axes.

### 2. Identify the spec source

The spec is `<context_handoff_dir>/plan.md` when that file exists. Otherwise it is the request text (`prompt`), verbatim. If there is no spec, the **Spec** axis skips and reports "no spec available".

### 3. Identify the standards sources

Anything in the repo that documents how code should be written, such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`.

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation. Like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

### 4. Run both axes, one after the other

Run the Standards axis first, then the Spec axis, both against the change from step 1. Write down the Standards findings before starting the Spec pass, and don't let one axis's findings shape the other's (see _Why two axes_).

**Standards axis.** Check the change against the standards-source files from step 3 **and the smell baseline from step 3**. Report, per file/hunk where relevant, (a) every place the diff violates a documented standard: cite the standard (file + the rule); and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls: documented-standard breaches can be hard, but baseline smells are always judgement calls, and a documented repo standard overrides the baseline. Skip anything tooling enforces.

**Spec axis.** Check the change against the spec from step 2. Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding.

If the spec is missing, skip the Spec axis and note this in the final report.

### 5. Aggregate

Write the two axes' findings into `<context_handoff_dir>/review.md`, the one review report, under `## Standards` and `## Spec` headings. Do **not** merge or rerank findings, because the two axes are deliberately separate (see _Why two axes_).

End with a one-line summary: total findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes: that's the reranking the separation exists to prevent.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.
