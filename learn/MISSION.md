# Mission

Operate SSSF for real — not demo it.

## Why

This repo already contains a working factory: eleven ADW workflows, a five-agent roster,
a real target app, three wired gates, and a dozen recorded runs. The machinery exists.
The open question is whether the operator can tell a factory that is **checking** from one
that is merely **reporting**.

That distinction is not decoration. Everything SSSF offers rests on one guarantee — that
an agent's *claims* are replaced by a *deterministic verdict* before work proceeds. The
guarantee's entire strength is the gates. A factory is exactly as trustworthy as its
weakest gate, and a gate's trustworthiness cannot be read, only demonstrated.

## Objectives

### 1. Gates — ✅ DONE (lessons 0001, 0002)

Know what a gate is, why a green result carries almost no information, and how to verify
one by mutation. Assessed by dialogue rather than assertion; see learning record 0001.

Then both families: **quality blocks** judge the code, **envelope gates** judge the
agent's claims about its own work. Wiring one, writing the other. See learning record
0002. Outstanding: the hands-on task in lesson 2 — write `no_placeholder_blocks`, a gate
that fails a run whose quality blocks are still placeholders.

### 2. Read a trace and know what it does not say

The trace records what ran and what it cost. It cannot record whether the checks meant
anything. Learn to read `sssf.db` for the questions it can answer, and to notice the ones
it cannot.

### 3. Bound an agent

`writes`, `protected_files`, and the reason the builder must not be able to edit its own
grader. What each mechanism does and does not prevent.

### 4. Run the factory on work that matters

A real feature on a real repo, reviewed properly — diff read, cost checked, gates trusted
because they were verified.

## Constraint

Nothing is taken on my word. Every claim in these lessons was executed on this machine
before it was written, and where a claim turned out wrong it is corrected in place with
the correction visible.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-25 | Initial mission. Objective 1 complete. |
