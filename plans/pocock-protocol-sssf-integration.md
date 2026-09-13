# Pocock protocol × SSSF — integration plan

**Date:** 2026-09-12
**Inputs:** fresh clone of mattpocock/skills (`downloads/skills/`, CHANGELOG
through 1.2.3), locally installed set (`~/.claude/skills/`), SSSF playbook
v4.5 (`docs/playbook-adopting-sssf.md`), the bootstrap/AFK audit
(`downloads/bootstrap-afk-audit.md`, treated as ground truth on SSSF's actual
behavior), the vendoring mechanism
(`.claude/skills/sssf/scripts/vendor_skill.py`,
`.claude/skills/sssf/cookbooks/attach_a_skill.md`), a real downstream repo
(`/Users/alexei/Projects/training/opencode-expo`), and the Medium article
"Matt Pocock's 5 Claude Code skills made me rewrite how I work with AI
agents" (fetched successfully 2026-09-12).
**Companion knowledge base:** `.okf/pocock-skills/` in this repo — the full
skill matrix, the two-snapshot comparison, and per-skill deep dives. This
plan cites it rather than restating it.

---

## 0. The one-paragraph verdict

The two systems are already halves of one machine: Pocock's skills own the
human-interactive front end (interview → spec → tickets → triage judgment)
and SSSF owns everything after `ready-for-agent` (queue, planner → builder →
reviewer → documenter). The seam works today in one real repo. The main
threat is not architectural — it is **vocabulary drift**: SSSF's playbook,
planner prompt, and vendored files are written against a skill generation
(`write-a-prd`, `prd-to-plan`) that no longer exists upstream, and the
upstream renames (`to-spec`, `to-tickets`) are not cosmetic — they changed
the skills' interaction contract in a way that would actually *simplify*
SSSF's headless overrides if adopted deliberately, and quietly break them if
adopted by accident.

---

## 1. Where they complement each other

SSSF is a headless execution engine with almost no opinion about how
requirements form; Pocock's collection is almost entirely about forming
them, plus a few headless-safe disciplines. The pairings that already work
in this fork:

| Pocock side | SSSF side | Status |
|---|---|---|
| `/grill-with-docs` (grilling + domain-modeling) writes `CONTEXT.md` + `docs/adr/` | Planner treats committed `CONTEXT.md`/ADRs as binding vocabulary (Part C "going dark") | **Working today** — verified by the prior audit (Diagram A); commit step manual |
| `tdd`, `code-review` protocol text | Vendored via `vendor_skill.py` into `adws/adw_data/skill_engineering/`, appended to the planner's system prompt | **Working today** — provenance headers dated 2026-09-09 in opencode-expo |
| `/triage`'s `ready-for-agent` terminal state + durable agent brief | `adw_watch.py` (`just watch`) only ever claims already-`ready-for-agent` tickets, then writes its own `claimed`/`resolved` | **Working today** — the contract state between the systems |
| `wayfinder`'s map/child/frontier/claim/resolve mechanics | Part D reuses them *as* the queue instead of inventing one | **Working today** (design reuse, per playbook v4.0 history) |
| `setup-matt-pocock-skills`' local-tracker template (`.scratch/<f>/spec.md` + `issues/NN-slug.md`, `Status:` lines) | The exact shape `adw_watch.py`'s frontier scan reads | **Working today** — opencode-expo's `docs/agents/issue-tracker.md` was re-synced to the canonical template on 2026-09-09, then extended with queue states |

The Medium article independently confirms the philosophical fit: its loop
(grill → spec → slice → ship → refactor, with each ticket classified HITL
or AFK and AFK tickets feeding "Ralph loops" — agents autonomously pulling
from the backlog) *is* SSSF's Part C + Part D described from the
interactive side. The article's five skills are `/grill-me`, `/to-prd`,
`/to-issues`, `/tdd`, `/improve-codebase-architecture`. Notably its stage 5
(architecture cleanup feeding lessons back to stage 1) has no SSSF
counterpart today — a genuine open pairing opportunity (the documenter
stage updates knowledge, but nothing schedules deepening work).

## 2. Where they overlap or duplicate

**2.1 The tracker doc — same file, two authors.** Pocock's
`setup-matt-pocock-skills` writes `docs/agents/issue-tracker.md` from its
bundled templates; SSSF needs that same file to carry queue extensions
(`claimed`/`resolved` states written by `adw_watch.py`, `Type:` lines,
per-feature-scoped `Blocked by:`). In opencode-expo these were merged by
hand: the file is the canonical template *plus* an SSSF-extended
"Wayfinding operations" section. They are the same thing under one name —
but only because a human reconciled them once. A re-run of
`/setup-matt-pocock-skills` (the skill offers "restart from scratch")
would regenerate the template and silently drop the SSSF extensions;
nothing marks them as foreign matter. The base convention itself has NOT
diverged: both snapshots and the downstream file agree on the
`.scratch/<feature-slug>/` shape.

**2.2 Two vendoring philosophies, three copies of one protocol.** Pocock's
`skills.sh` path copies editable SKILL.md files into your project ("hack on
them, own them"; `npx skills update` pulls upstream on demand, no
provenance). SSSF's `vendor_skill.py` copies a skill's *body* into
`adws/adw_data/skill_engineering/<name>.md` with a provenance header
(source path, date, sha256) so drift is detectable, and attaches it to one
headless agent's system prompt. These answer different questions — "install
for interactive use" vs. "attach a protocol to an unattended agent" — and
can coexist. But run both on one repo and a protocol exists three times
(plugin/skills.sh copy, `~/.claude/skills/` copy, vendored copy) with no
cross-check between them; the upstream README already warns that
plugin + skills.sh together gives "every skill twice." `vendor_skill.py`'s
refusal to overwrite header-less files is the right safety valve here (it
protected `prd-to-plan.md` from being clobbered), and its no-op-on-re-run
property makes a CI drift check feasible — Pocock's side has no equivalent.

**2.3 Duplicate skills inside the local install.** `~/.claude/skills/` is
a transitional snapshot holding three generations at once: `write-a-prd`
AND `to-prd` (both "write a PRD" triggers), `prd-to-issues` AND `to-issues`,
`review` AND `code-review`. Which one fires on a natural-language request is
model's choice. Pure duplication, no benefit.

**2.4 One artifact, several names.** The prior audit's 3.4.3 finding
("one artifact, four names" [LOW]) extends across the boundary: Pocock
gen-1 says PRD, gen-3 says spec; SSSF says plan/spec (`specs/<adw_id>_*.md`,
`prd-to-plan` writing `./plans/`); the tracker template says
`.scratch/<f>/spec.md`. Upstream has already converged on "spec" — SSSF
prose hasn't.

## 3. Concrete friction points

**F1 — The naming drift is load-bearing, not cosmetic. [HIGH]**
Verified mapping (full evidence in `.okf/pocock-skills/naming-drift.md`):

- `write-a-prd` → `to-prd` → **`to-spec`** (and the interview was removed:
  to-spec is "no interview, just synthesis")
- `prd-to-issues` → `to-issues` → **`to-tickets`** (one file per ticket,
  native blocking edges)
- `review` → **`code-review`**; `decision-mapping` → **`wayfinder`** (1.1.0)
- **`prd-to-plan` exists in neither snapshot.** In opencode-expo it is the
  only `skill_engineering/` file with *no* provenance header — hand-authored
  or carried from a pre-vendoring era. Its intent (slice a PRD into phases,
  one local file in `./plans/`) is covered upstream by `to-tickets` +
  `implement`, with a different output contract (tracker tickets with
  `Blocked by:` edges — exactly the queue-pickable shape playbook Part D
  says `prd-to-plan` phases lack).

Where the old names bind: `docs/playbook-adopting-sssf.md` (the
`/grill-with-docs → /write-a-prd → /prd-to-plan` chain appears at ~10 sites
including both mermaid diagrams and the Part C problem statements) and
`.claude/skills/sssf/templates/prompt_engineering/planner/system.md:32-51`
("On the skills composed below (wayfinder, write-a-prd, prd-to-plan, tdd)"
with per-skill never-prompt overrides keyed to those names). A new adopter
following the playbook against the current upstream cannot find two of the
three skills it tells them to vendor. Extra wrinkle: the four provenance
headers point at `~/.agents/skills/…` — a third on-disk snapshot this plan
did not audit file-by-file.

The flip side, worth stating as an opportunity: two of SSSF's three
headless patches exist because gen-1 skills interview.
`to-spec` never prompts *by design*, so migrating shrinks the planner
override section rather than growing it.

**F2 — grill → triage handoff is still manual, in both snapshots. [MEDIUM]**
Already proven by the prior audit (finding 3.1.3): `grill-with-docs` is a
one-line composition that ends when the interview ends; filing the ticket is
a separate human act. Checked against the fresh clone: nothing closes the
gap. `loop-me` is another *interview entry* (grilling about workflow specs),
not a bridge; `to-spec`/`to-tickets` still require the human to type them;
`ask-matt` routes but is itself user-invoked. The gap is upstream-canonical:
their own flow is grill, *then* type `/to-spec`, *then* type `/to-tickets`,
then triage. Any bridge is ours to build.

**F3 — `triage` itself drifted, and the local copy is the stale one. [MEDIUM]**
Fresh `triage` adds `disable-model-invocation: true` (human-only entry),
extends the state machine to external PRs ("a PR is an issue with attached
code"), and reroutes its grilling dependency from `grill-with-docs` to
`grilling` + `domain-modeling`. SSSF's Part D leans on `/triage` as the
interactive gate that posts the agent brief; the version the user actually
runs is the older, issue-only, model-invokable one. Not currently breaking
anything, but the two copies will keep diverging, and the PR-surface
feature is one SSSF's queue could genuinely use (external PRs as a request
surface feeding `ready-for-agent`).

**F4 — Tracker-doc regeneration can eat SSSF's queue states. [MEDIUM]**
Per 2.1: `docs/agents/issue-tracker.md` in a downstream repo is
Pocock-template + SSSF-extension merged by hand, and `adw_watch.py` reads
*only* the extended shape (opencode-expo's own doc records that the
pre-sync shape "was never picked up by adw_watch.py's frontier scan").
Re-running the setup skill, or re-syncing to a future upstream template,
regenerates the base and drops the extension unless someone remembers.
Neither side owns the merge.

**F5 — The article's workflow (and upstream's) assumes hand-run sequencing;
SSSF's watcher changes the failure modes. [LOW-MEDIUM]** Three concrete
mismatches once `just watch` is standing:
(a) the article's "AFK: an agent picks up, implements, **and merges**
without your involvement" overstates what SSSF does — the reviewer stage
reviews, a human merges;
(b) mid-sequence dispatch is *mostly* interlocked by design — `/to-spec`
files at `needs-triage` and the watcher only claims `ready-for-agent`, so a
half-finished human sequence is invisible to the queue. The interlock's weak
point is the dirty-tree rule: the watcher refuses dirty trees, so an
in-progress grill session with uncommitted `.scratch/` edits stalls the
whole queue rather than one ticket;
(c) the article's `/to-prd` "lands as a GitHub issue" — SSSF's proven
deployment is the local-markdown tracker; a GitHub-tracker adopter is
running a path where `adw_watch.py`'s frontier scan (which reads `.scratch/`
files) has never been shown to work. Playbook doesn't currently say this.

**F6 — Local install heterogeneity. [LOW]** Duplicate-generation skills
(2.3) create ambiguous triggers, and local `wayfinder` (byte-identical to
fresh) references `research` and `prototype`, which are not installed
locally — a composition that silently no-ops. Cosmetic until a session
depends on it.

## 4. Recommendations

Priorities follow the prior audit's convention. Each item names the file to
change or create. Constraint respected: nothing under `.claude/skills/sssf/`
or `adws/` is modified by *this* task — items touching them are proposed
changes for a follow-up commit.

**R1 [HIGH] — Publish the name mapping and pin the vendored names.**
Add a short "Skill-name compatibility" subsection to
`docs/playbook-adopting-sssf.md` (Part C, near the first
`/write-a-prd` mention) carrying the verified mapping table: `write-a-prd →
to-spec`, `prd-to-issues/to-issues → to-tickets`, `prd-to-plan → (SSSF-local,
no upstream equivalent; nearest: to-tickets + implement)`, plus one sentence:
*vendored filenames in `adws/adw_data/skill_engineering/` are pinned to the
names the planner prompt keys on; re-vendoring from the current upstream
must either use `vendor_skill.py --as write-a-prd` etc., or update
`prompt_engineering/planner/system.md`'s "On the skills composed below"
section in the same commit.* This is documentation-only and removes the
playbook's broken instruction for new adopters.

**R2 [HIGH] — Migrate the planner composition to gen-3 skills, deliberately.
DONE (2026-09-13, `6bc5940` fork / `f6e292e`+`fdd1809` opencode-expo).**
Re-vendored `to-spec` and `to-tickets` from `downloads/skills/skills/
engineering/…` pinned at commit `3cca18b`; retired `write-a-prd.md` and
`prd-to-plan.md`; rewrote the planner template's composed-skills section
for the new names in both the fork's generic template and opencode-expo's
live copy. Payoff landed as predicted: `to-spec`'s non-interactive design
removed a whole "never prompt" override rather than adding one, and
`to-tickets`' native per-phase ticket files retired the hand-maintained
`prd-to-plan` gap entirely.

Two headless-safety gaps surfaced during the rewrite that this plan's
research pass had not caught (now recorded in `.okf/pocock-skills/skills/
to-spec.md` and `to-tickets.md`): both skills apply `ready-for-agent`
themselves by default (their own "quiz/check with the user" step standing
in for a triage gate in their model) — overridden to file at
`needs-triage` instead, since SSSF's `/triage` judges a materially fuller
set of concerns; and `to-tickets`' own local-ticket-template uses bold
`**Status:**`/`**Blocked by:**` lines, which `adw_watch.py`'s frontier scan
would never match — overridden to require plain lines. opencode-expo's
full suite (102 tests) and `just skills`' roster audit both green after
the migration.

**R3 [MEDIUM] — Make `setup-matt-pocock-skills` the single source of the
tracker doc, with a fenced SSSF extension. DONE (2026-09-13, fork commit
pending push / opencode-expo `6aaf9fd`).** Documented the contract in
`.claude/skills/sssf/references/config.md` (new paragraph after Vendoring)
and the playbook (new "Two owners of one file" subsection in Filing, v4.7).
Applied the actual markers to opencode-expo's real `docs/agents/
issue-tracker.md`: the base template turned out to be interleaved with
SSSF's additions, not cleanly appended at the bottom, so the fence is four
separate `<!-- sssf:queue-extension -->` regions (the re-sync history note,
the `Type:` line, the heavily-rewritten "Wayfinding operations" section
with a visible "on re-sync, keep this version" callout above it, and the
two `/handoff`-integration sections that don't exist in the base template
at all) rather than one contiguous block — the plan's original single-block
framing didn't survive contact with the real file.

Scoped down from the original ask: did **not** teach `install.py` to
(re)inject the block — `install.py` doesn't own this file at all (it's
written by `/setup-matt-pocock-skills`, a Pocock skill this project doesn't
control), so there's no SSSF-side hook to attach automatic reinjection to.
The markers are a diff aid for whoever re-syncs the base by hand, not
automatic reinjection — documented as such rather than overclaiming a
mechanism that doesn't exist. Full suite still green (102 passed); this
file isn't machine-parsed.

**R4 [MEDIUM] — Close (or formally accept) the grill → triage gap. DONE
(2026-09-13, playbook v4.8).** Decision: **accept-as-manual**, not
bridge — the user opted against building the `grill-and-file` wrapper
skill, on the reasoning that a skill to maintain for one reminder isn't
worth it when a checklist line covers the same ground. Added a new Part C
subsection ("The grill → triage handoff is manual, on purpose") recording
the decision and citing the prior audit's 3.1.3, plus a new Definition-of-
done checklist item ("if this bootstrap session ran because of a fresh
grilling, its outcome is filed — run `/triage` before leaving the
session"). Re-checked F2 against current upstream while there: still
unbridged in the fresh clone too, so this isn't a gap SSSF could have
inherited a fix for.

**R5 [MEDIUM] — Adopt the fresh `triage` (and note the PR surface). DONE
(2026-09-13, playbook v4.9).** Updated the local install — turns out
`~/.claude/skills/triage` is a symlink to `~/.agents/skills/triage`, the
real location (and, per F1's evidence, the same directory the vendored
provenance headers already point at). Backed up the prior version to
`~/.agents/skills/.triage-backup-2026-09-13/` before overwriting; the fresh
copy now matches the upstream clone byte-for-byte (`diff -rq` clean).

The playbook sentence turned out to need a correction the plan didn't
anticipate: the original framing ("the queue can gate external PRs the
same way once the tracker config flips the flag") is wrong. A PR only
exists on a GitHub/GitLab tracker, and `adw_watch.py` explicitly refuses
those (exit code 2 — its own module docstring already names GitHub/GitLab
support as unbuilt). So triage adopting PR support does not extend to
`just watch` at all yet; caught and fixed before it shipped as a second
stale claim in the same playbook this whole effort exists to de-stale.

**R6 [LOW, mostly cosmetic] — Local-install hygiene. DONE (2026-09-13).**
R1/R2 had already landed, so the precondition was met — confirmed no
remaining vendored `skill_engineering/` file's provenance header pointed at
any of the five before deleting. Backed up
`write-a-prd`/`to-prd`/`prd-to-issues`/`to-issues`/`review` to
`~/.agents/skills/.superseded-backup-2026-09-13/`, then removed both the
`~/.claude/skills/` symlinks and their `~/.agents/skills/` backing
directories. Installed `research` and `prototype` from the pinned fresh
clone the same way (copy into `~/.agents/skills/`, symlink from
`~/.claude/skills/`, matching the existing convention) — both now register
as available skills, and `wayfinder`'s `research`/`prototype` ticket types
stop no-op'ing. Local install: 20 skills, no duplicate generations. No
repo file changed by this item; nothing to push.

**R7 [LOW] — Terminology pass to "spec". DONE (2026-09-13, playbook
v4.10).** All 5 remaining "PRD" mentions converted to "spec". Widened
slightly beyond pure word-swap: Problem 1's title and body still named the
retired `write-a-prd`/`prd-to-plan` skills throughout (R1 had deliberately
left prose like this alone), and renaming "PRD" right next to unrenamed
skill names would have read incoherently, so that one section's skill
references were updated too (`write-a-prd` → `to-spec`, `prd-to-plan`'s
"ask the user to paste it" → `to-tickets`'s "quiz the user"). Also
corrected the section's title, which claimed "the interview `to-spec`
wants" — no longer true now that `to-spec` doesn't interview by design;
reframed around `wayfinder`'s own fallback instead, which is where the
interview-with-no-audience problem actually still lives. Scoped to
Problem 1 and one Filing-section mention only — the ~15 remaining
`/write-a-prd`/`/prd-to-plan` references elsewhere (diagrams, Parts A/B
walkthroughs) stay as-is per R1's original decision, not swept in this
pass.

## 5. What I could NOT verify

- **`~/.agents/skills/` contents** — the actual vendoring source named in
  all four provenance headers. Inferred ≈ current upstream from the vendored
  bodies' descriptions matching fresh-clone text, but not diffed
  file-by-file.
- **Live behavior of any skill or of `adw_watch.py`** — this is a static
  analysis of skill texts, prompts, code, and one downstream repo's
  artifacts; no skill was executed and no queue run observed (consistent
  with the prior audit, whose full-chain dispatch had also never run).
- **The Medium article's screenshots/images** — text fetched and read in
  full (all sections, including the five-skill list and the closing loop);
  images ("Press enter or click to view image") were not retrievable.
  The article carries no publication date in the fetched text.
- **`weather-report` repo** — cited by playbook v4.5 history as evidence for
  `/triage` filing behavior; not on disk (already flagged by the prior
  audit; unchanged).
- **Every one of the 37 fresh SKILL.md bodies in prose** — all 37 were
  parsed programmatically (frontmatter, cross-references, bundled files) and
  the load-bearing ten read closely; the `misc/` and `writing-*` bodies were
  skimmed at digest level only.

## 6. Independent re-audit (2026-09-13) and follow-up fixes (F1–F6)

An independent fable-agent re-audit of R1–R7, `downloads/pocock-sssf-reaudit.md`,
verified every claim above directly on disk (not on trust) and found R1–R7
substantially landed correctly — every artifact exists, both R2 safety
overrides are present and still accurate against current upstream (which
had not moved), and opencode-expo's suite genuinely passes (102, re-run
fresh). It also found new issues the original R1–R7 pass didn't and
couldn't have caught, prioritized below as F1–F6, continuing the numbering.

**F1 [HIGH] — Document the interactive `ready-for-agent` triage bypass.
DONE (2026-09-13, playbook v4.11, `11a3cc2`).** R2's needs-triage/plain-line
overrides only ever applied to the headless planner prompt. The Filing
section's own guidance recommends running `/to-spec` interactively, and
both `/to-spec`/`/to-tickets` self-apply `ready-for-agent` by default —
running either by hand bypasses `/triage` entirely, undocumented until now.
Added a "sharp edge" paragraph: `/to-tickets`' bold template makes an
interactive ticket invisible to the queue (silent stall); plain lines
instead produce an untriaged `ready-for-agent` ticket the watcher builds
unjudged. Instructs running `/triage` on interactive output, or hand-fixing
the status line and format, first.

**F2 [MEDIUM] — Fix a third instance of the self-inflicted-error pattern.
DONE (2026-09-13, playbook v4.12, `e56901c`).** Part D's "judgment call
stays interactive" section claimed "`to-spec`'s interview had no one to
answer it headless" — false, `to-spec` never interviews; introduced by
v4.9's mechanical rename, missed by v4.10's own cleanup pass which fixed
the identical disease elsewhere. Reworded to point at `wayfinder`'s
fallback instead (the thing Problem 1 actually still describes). Also
fixed two wording nits: the compatibility table's "renamed two of the
three" (only one skill was renamed) and Problem 1's garbled parenthetical.

**F3 [MEDIUM] — Extend `issue-tracker.md` fencing to full coverage. DONE
(2026-09-13, opencode-expo `f66afd9`).** The four R3 fences were real but
incomplete against a direct diff of the actual base template: the
`Blocked by:` Conventions bullet, the whole Directory Structure section,
the reworded publish-to-the-tracker guidance, and the trailing
Rule-of-thumb line all sat outside every fence. Diffed line-by-line against
the base template and fenced every genuinely SSSF-added-or-reworded piece
— 8 balanced regions now (was 4). Also fixed two more stale "PRD" mentions
surfaced during the close read. Full suite still green (102 passed).

**F4 [MEDIUM] — Teach both R2 safety overrides in Problem 1's AFK bullet
list. DONE (2026-09-13, playbook v4.13, `962a537`).** Problem 1's list only
covered the interview-related overrides (wayfinder no-fog, to-spec
never-prompts, to-tickets quiz-skip) — it never mentioned the two
triage-bypass overrides R2 actually shipped (force `needs-triage`, force
plain lines). An adopter hand-writing their own `system.md` from this list
alone would get a queue-bypassing, queue-invisible configuration even
though the shipped template is correct. Added both.

**F5 [LOW] — Back-port a real heuristic fix, document a manual drift check.
DONE (2026-09-13, fork `2f48f59`).** Diffed the fork's shipped planner
template against opencode-expo's live copy: the fork's ticket-detection
heuristic keyed on `to-tickets`' own local-ticket-template shape, while
opencode's correctly keys on what `/triage` actually posts (`## Agent
Brief`/`Current behavior`/`Desired behavior`) — opencode's version matches
reality, the fork's didn't. Backported it plus a missing "do not attempt to
prompt" safety clause. Re-diffed after: only formatting differences remain.
Added a `config.md` paragraph documenting why this file has no automatic
drift check (it isn't provenance-headered — downstream customization is
expected) and a manual `diff` command with guidance on what's worth
noticing (a safety override present on one side, not the other) versus
what to ignore (wrapping, phrasing).

**Fourth-pass correction (B2, `downloads/pocock-sssf-sync-plan-v2.md`):**
"only formatting differences remain" understated the real diff — a
normalized word-level comparison found genuine (if benign) wording deltas
in both directions beyond wrapping (a fork-only clarifying parenthetical;
an opencode-only closing sentence about one-phase-at-a-time). No safety
override differs on either side, which is the test that actually matters
per `config.md`'s own drift-check guidance — so the substantive conclusion
still holds. But "formatting differences" was the wrong description, and a
future drift-checker trusting that phrase at face value would misread a
real delta as noise. See B3 for the follow-up decision on these two
sentences.

**F6 [LOW] — Unify provenance-source convention, refresh stale tracking.
DONE (2026-09-13, opencode-expo `89b36b1`).** `to-spec`/`to-tickets`'
provenance headers pointed at the gitignored, disposable `downloads/`
clone while `code-review`/`tdd`/`wayfinder` pointed at the durable
`~/.agents/skills/`. Installed `to-spec`/`to-tickets` into
`~/.agents/skills/` (matching R6's `research`/`prototype` convention) and
re-vendored both from there — same content, same sha256, only the recorded
source changed; all five vendored files now share one convention. Also
found and fixed real staleness the audit flagged: local `tdd` and
`grill-with-docs` were both tracking pre-upstream-wording-pass copies
(cosmetic em-dash→colon changes, plus a real invocation-mechanism note in
`grill-with-docs`: "run a `/grilling` session" → "call the Skill tool
twice"). Backed up both before refreshing from the fresh clone, then
re-vendored `tdd` (not `grill-with-docs`, which stays deliberately
unvendored per its `disable-model-invocation: true`). `--check` clean on
all five vendored files; full suite still green (102 passed).

All six follow-up findings from the independent re-audit (F1–F6) are now
addressed.
