---
title: Rule zero
---

# Rule zero

**Wire the gates and watch each one fail, before any agent writes a line.**
Source: `docs/playbook-adopting-sssf.md`, "Rule zero: wire the gates before
an agent writes a line" section.

## Why it exists

A freshly stamped factory ships every quality block as an `echo` that exits
0. Run a workflow against that and you get a green trace that proves
nothing — the agent's claim went unchecked, and the run *reported success*.
The playbook is explicit that this is worse than having no factory at all,
"because it manufactures confidence."

So the first action in any newly adopted repo, before any agent writes
anything, is:

```bash
just quality "baseline"        # zero agents — look at what it claims
```

If the output says `PLACEHOLDER`, the gates are fake. The playbook's
prescribed fix is to wire them in `adws/adw_modules/quality.py`, then
**prove each one can fail** — deliberately break something the gate should
catch and confirm it does, before trusting a green result on real work.

## Where it sits in the adoption order

The playbook orders adoption as: install + recon → wire the gates (rule
zero) → set boundaries → interrogate → work. Rule zero is deliberately early
in both the existing-codebase and new-project paths, not at the end — gates
are wired before any agent writes a line, not audited after the fact once
agents have already been producing (unverified) work.

## Relationship to Gate and Permissions

Rule zero is about the **quality blocks** an ADW chain runs between phases —
the operator-authored checks in `adw_modules/quality.py`, typically wired to
project-specific commands (lint, typecheck, test suite). This is distinct
from, but complementary to, the built-in mechanical `Gate`s
(`quality-gates-and-permissions/Gate.md`) that check envelope claims against
disk, and from write-permission enforcement
(`quality-gates-and-permissions/Permissions-and-writes.md`). All three answer
"how do we know an agent's work is real" from a different angle: quality
blocks check the code externally (does it lint/build/test), gates check the
agent's own claims about its artifacts, permissions check the agent didn't
touch what it wasn't supposed to.

## See also

- `quality-gates-and-permissions/Gate.md`
- `quality-gates-and-permissions/Permissions-and-writes.md`
- `docs/playbook-adopting-sssf.md` — full Rule Zero walkthrough with the
  Mermaid diagram showing it as the first step after install+recon.
