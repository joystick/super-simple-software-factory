# Notes

## How this learner learns

Observed across the objective-1 dialogue:

- **Answers honestly when they do not know.** Said "i don't know, teach me the basics"
  rather than bluffing. That is the single most useful trait a learner can have and it
  should be met with actual teaching, not reassurance.
- **Label-matching under pressure.** Twice reached for a recently-taught label instead of
  reasoning from mechanism:
  - Q6 — applied the pipe/exit-code hazard, taught thirty seconds earlier, to a question
    about detection. *Recency capture.*
  - Q9 — picked the first row of the diagnosis table ("gate doesn't reach") for a
    both-red result, which is a different row.
  Counter: ask "what is this tool's *job*" before asking what to conclude. Force the
  mechanism, not the label.
- **Overclaims slightly when summarising.** "The gate works" drifted into "the code
  works". Worth catching each time; it is the same drift that makes a green trace feel
  like evidence.
- **Responds extremely well to demonstration.** Every concept that landed, landed when it
  was executed in front of them. The placeholder install and the dead-lint-gate demo did
  more than any paragraph. Prefer running a thing over explaining it.

## Constraint discovered mid-course

**The learner is not a Python developer.** Stated plainly during lesson 2's exercise, and
it recontextualises everything: SSSF is written in Python, but their work is TypeScript.

Consequence for every future lesson here: **teach the gate thinking, supply the Python.**
Asking them to reason about `node.returns` being `None` for unannotated functions taught
nothing about verification and cost them time — that was my error, and it produced a line
(`ast.RetunType`) that does not exist because I steered them at it.

The decisions worth their attention are the ones that survive a change of language:
what to check, what a note must tell the agent, and what the gate cannot promise. The
syntax is incidental and I should hand it over rather than quiz on it.

## Teaching decisions

- Workspace lives in `learn/` rather than the repo root, so the course does not scatter
  five directories through a working project.
- Assets copied from the pricing-ts workspace so both courses look like one body of work.
- Assessment before authoring: the dialogue set the zone of proximal development, and the
  lesson was written afterwards to fix what the questions exposed. Do this again.

## Answered along the way

- "Do I have to wire gates BEFORE prompting?" — asked unprompted, which is the sign the
  objective landed. Answer: wired *and watched failing*. Behind an unverified gate a good
  prompt only produces unchecked work faster.

## Open threads

- Objective 2 (reading a trace) is the natural next lesson. The hook: `sssf.db` records
  cost, phases and tool calls faithfully, and cannot record whether any of it meant
  anything.
- Unspent demonstration: running a real `just sdlc` with a deliberately dead test gate,
  to watch the factory commit a bug and certify it 5/5. Costs roughly $0.60. It is the
  most convincing artefact available for objective 1 and was deliberately left unspent —
  offer it before objective 2.
