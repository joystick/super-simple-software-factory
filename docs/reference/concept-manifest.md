---
title: Concept manifest
---

# Concept manifest

Every concept from the docs/reference concept inventory (see
`plans/2026-09-24-docs-reference-and-training.md`'s "Concept inventory"
section), mapped to its category, resolution (a link into the existing
skill-internal reference docs, or a real new page in this glossary), and the
source it is grounded in. Written first, before any page, so completeness is
checkable against a fixed list rather than trusted on faith.

"Link" rows point at `.claude/skills/sssf/references/{config,handoff,
observability}.md` in place — those files are not moved or copied (see
`README.md`). "Own page" rows are new files under this `reference/` tree.

Total: **80 concepts** (the plan's "~75" was an estimate; the full inventory
enumerates to 80). Split: **36 link**, **44 own-page** (both counts corrected
twice over — a fable review pass first found the original "51/29" summary
didn't match the table's own row count of 46/34, and separately found 9 of
those 46 "link" rows pointed at anchors that never actually discuss the
concept — a dead-end link, not a real answer. Those 9 are reclassified
"own-page (reclassified)" below, each with the review's finding and the real
source citation, and the split is now correct by direct count: **36 + 44 =
80**). Categories 5 (quality-gates-and-permissions) and 7 (the-queue) remain
~all own-page, per the plan's finding that `references/*.md` barely touches
them. Reclassified rows are stubbed, not yet fully authored, same as any
other unauthored own-page row.

## 1. Core execution model (12 concepts — all link)

| Concept | Category | Link-or-Own | Source citation |
|---|---|---|---|
| ADW | core-execution-model | link | `.claude/skills/sssf/references/handoff.md#session-directory-layout` |
| `adw_id` | core-execution-model | link | `.claude/skills/sssf/references/handoff.md#session-directory-layout` |
| Session / `ensure()` | core-execution-model | link | `.claude/skills/sssf/references/handoff.md#session-directory-layout` |
| Run | core-execution-model | link | `.claude/skills/sssf/references/handoff.md#envelope-schema` |
| Phase | core-execution-model | link | `.claude/skills/sssf/references/handoff.md#the-typed-output-rule` |
| PhaseParams | core-execution-model | link | `.claude/skills/sssf/references/handoff.md#envelope-schema` |
| Four-param rule | core-execution-model | own-page (reclassified) | dead-end link found by review: `handoff.md#variables` doesn't discuss it. Real source: `adw_modules/data_types.py:1` docstring. |
| AgentCall | core-execution-model | own-page (reclassified) | dead-end link found by review: `config.md#agents` covers roster config, not the `AgentCall` type. Real source: `adw_modules/data_types.py:286`. |
| `agents.execute()` | core-execution-model | link | `.claude/skills/sssf/references/config.md#coding-agents` |
| "Agent proposes / code disposes" | core-execution-model | link | `.claude/skills/sssf/references/handoff.md#two-output-channels-exactly` |
| Chains (`plan_build_test` vs `adw_simple_sdlc`) | core-execution-model | own-page (reclassified) | dead-end link found by review: `handoff.md#the-typed-output-rule` never mentions either chain. Real source: `templates/adws/adw_watch.py:5-9` docstring (names both). |
| `--skip-plan` | core-execution-model | own-page (reclassified) | dead-end link found by review: cited anchor doesn't discuss it. Real source: `adw_modules/utils.py:66`, `load_plan_from_file`. |

## 2. Handoff & typed output (9 concepts — all link)

| Concept | Category | Link-or-Own | Source citation |
|---|---|---|---|
| Envelope / EnvelopeBase | handoff-and-output | link | `.claude/skills/sssf/references/handoff.md#envelope-schema` |
| Two output channels | handoff-and-output | link | `.claude/skills/sssf/references/handoff.md#two-output-channels-exactly` |
| Typed-output rule | handoff-and-output | link | `.claude/skills/sssf/references/handoff.md#the-typed-output-rule` |
| `previous_envelope` | handoff-and-output | link | `.claude/skills/sssf/references/handoff.md#injecting-the-previous-envelope` |
| `context_handoff/` | handoff-and-output | link | `.claude/skills/sssf/references/handoff.md#context_handoff_dir` |
| Output types (PlanOutput, ReviewOutput, etc.) | handoff-and-output | link | `.claude/skills/sssf/references/handoff.md#envelope-schema` |
| ChangeSet / BaseRef | handoff-and-output | own-page (reclassified) | dead-end link found by review: `handoff.md#report` doesn't cover these types. Real source: `adw_modules/changes.py:1`. |
| `agent_map.json` | handoff-and-output | link | `.claude/skills/sssf/references/handoff.md#agent_mapjson-and-resuming` |
| Session directory layout | handoff-and-output | own-page | `.claude/skills/sssf/references/handoff.md#session-directory-layout` (worked "link, don't duplicate" example — see `handoff-and-output/Session-layout.md`) |

## 3. Agent configuration (16 concepts — mostly link, 2 own-page)

| Concept | Category | Link-or-Own | Source citation |
|---|---|---|---|
| Roster | agent-configuration | link | `.claude/skills/sssf/references/config.md#shape` |
| `defaults` merging | agent-configuration | link | `.claude/skills/sssf/references/config.md#defaults-merging` (worked example — see `agent-configuration/Defaults-merging.md`) |
| `coding_agent` | agent-configuration | link | `.claude/skills/sssf/references/config.md#coding-agents` |
| `model` | agent-configuration | link | `.claude/skills/sssf/references/config.md#model-resolution` |
| `thinking` | agent-configuration | link | `.claude/skills/sssf/references/config.md#thinking-levels` |
| `tools` | agent-configuration | link | `.claude/skills/sssf/references/config.md#tools` |
| `writes` | agent-configuration | own-page | `.claude/skills/sssf/templates/adws/adw_modules/permissions.py:127-135` (enforcement lives outside config.md's scope; see `quality-gates-and-permissions/Permissions-and-writes.md`) |
| `protected_files` | agent-configuration | own-page | `.claude/skills/sssf/templates/adws/adw_modules/permissions.py:110-124,127-135` (see `quality-gates-and-permissions/Permissions-and-writes.md`) |
| `purpose` / `color` | agent-configuration | link | `.claude/skills/sssf/references/config.md#fields` |
| `prompt_engineering` | agent-configuration | link | `.claude/skills/sssf/references/config.md#skill-engineering` |
| `harness_engineering` | agent-configuration | link | `.claude/skills/sssf/references/config.md#harness-engineering` |
| `skill_engineering` | agent-configuration | link | `.claude/skills/sssf/references/config.md#skill-engineering` |
| `data_dir` | agent-configuration | link | `.claude/skills/sssf/references/config.md#fields` |
| Observability config | agent-configuration | link | `.claude/skills/sssf/references/config.md#observability` |
| `ignored_field_warnings` | agent-configuration | own-page (reclassified) | not a real link target: `sssf.config.yaml` is config source with inline comments, not a doc with headings to anchor into. Found by the test script's own link-checker (it requires a `file.md#anchor` citation shape, which this never had). Real source: `adw_modules/agents.py:95`. |
| `validate()` | agent-configuration | link | `.claude/skills/sssf/references/config.md#defaults-merging` |

## 4. Coding-agent drivers (8 concepts — all link)

| Concept | Category | Link-or-Own | Source citation |
|---|---|---|---|
| `agent_pi` | coding-agent-drivers | link | `.claude/skills/sssf/references/config.md#pi` |
| `agent_cc` | coding-agent-drivers | link | `.claude/skills/sssf/references/config.md#claude_code-headless-claude--p` |
| `agent_agy` | coding-agent-drivers | link | `.claude/skills/sssf/references/config.md#agy-antigravity-cli` |
| `agent_opencode` | coding-agent-drivers | link | `.claude/skills/sssf/references/config.md#opencode-a-gateway-like-agy-one-cli-in-front-of-many-providers` |
| PiRequest / PiResult | coding-agent-drivers | own-page (reclassified) | dead-end link found by review: `config.md#coding-agents` covers `coding_agent:`/`model:` config, never mentions `PiRequest`. Real source: `adw_modules/data_types.py:392`. |
| ToolCallTracker | coding-agent-drivers | own-page (reclassified) | dead-end link found by review: same anchor, same gap. Real source: `adw_modules/agent_cc.py:219` (and each `agent_*.py`). |
| UsageBreakdown | coding-agent-drivers | own-page (reclassified) | dead-end link found by review: `observability.md#tables` describes the tracer's DB tables, not this dataclass. Real source: `adw_modules/data_types.py:407`. |
| `operator_env` | coding-agent-drivers | link | `.claude/skills/sssf/references/config.md#claude_code-headless-claude--p` |

## 5. Quality gates & permissions (15 concepts — all own-page, NET-NEW)

| Concept | Category | Link-or-Own | Source citation |
|---|---|---|---|
| Gate | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/gates.py:1-9` |
| GateReport | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/data_types.py:264-279` |
| GateCheck | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/data_types.py:252-261` |
| `artifacts_exist` | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/gates.py:27-33` |
| `files_non_empty` | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/gates.py:36-44` |
| `json_parses` | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/gates.py:47-58` |
| `diff_matches_claims` | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/gates.py:61-68` |
| `verdict_consistent` | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/gates.py:71-95` |
| `tests_pass` (gate factory) | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/gates.py:98-108` |
| Quality blocks | quality-gates-and-permissions | own-page | `docs/playbook-adopting-sssf.md` (Rule Zero section) + `adws/adw_modules/quality.py` (per-repo, stamped) |
| Rule zero | quality-gates-and-permissions | own-page | `docs/playbook-adopting-sssf.md:33-48` |
| `snapshot()` | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/permissions.py:50-68` |
| `enforce()` | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/permissions.py:163-185` |
| PermissionBreach | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/permissions.py:41-42` |
| `always_writable` | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/permissions.py:110-124` |

Full page: `quality-gates-and-permissions/Gate.md`. `writes`/`protected_files`
enforcement and permission concepts: `quality-gates-and-permissions/Permissions-and-writes.md`.

## 6. Observability (6 concepts — mostly link, 1 own-page)

| Concept | Category | Link-or-Own | Source citation |
|---|---|---|---|
| Tracer | observability | link | `.claude/skills/sssf/references/observability.md#two-stores-one-truth` |
| EventRecord | observability | link | `.claude/skills/sssf/references/observability.md#event-schema` |
| Prompt audit copy | observability | link | `.claude/skills/sssf/references/observability.md#tables` |
| `adw_skills.py` / `audit_skills` | observability | own-page (reclassified) | dead-end link found by review: `observability.md#tables` doesn't discuss it. Real source: `templates/adws/adw_skills.py`, `adw_modules/agents.py:144`. |
| Console | quality-gates-and-permissions | own-page | `.claude/skills/sssf/templates/adws/adw_modules/console.py` — listed here under category 6's section for discovery continuity (a reader scanning "observability" will look for it here), but its Category column and its actual file both correctly say category 5, matching `quality-gates-and-permissions/Console.md`'s real location. Fixed a genuine column/reality drift a fable review pass caught (column previously said "observability"). |
| Visualizer | observability | own-page | `.claude/skills/sssf/apps/visualizer/` (an app, not an `adw_modules/` class) + `.claude/skills/sssf/references/observability.md` + `.claude/skills/sssf/templates/justfile` (`obs` recipe); see `observability/Visualizer.md` |

## 7. The queue / dark factory (14 concepts — all own-page, NET-NEW)

| Concept | Category | Link-or-Own | Source citation |
|---|---|---|---|
| Dark factory | the-queue | own-page | `docs/playbook-adopting-sssf.md` (Part D) |
| The four jobs | the-queue | own-page | `docs/playbook-adopting-sssf.md` (Part A5, "The four jobs" — corrected 2026-09-24, two independent authoring passes found this row wrongly said Part D) |
| Two layers | the-queue | own-page | `docs/playbook-adopting-sssf.md` ("two layers" framing) |
| Five vendored skills | the-queue | own-page | `.claude/skills/sssf/templates/justfile` + `docs/playbook-adopting-sssf.md` |
| The chain named once | the-queue | own-page | `.claude/skills/sssf/templates/adws/adw_watch.py:1-9` |
| Triage states | the-queue | own-page | `.claude/skills/sssf/templates/prompt_engineering/planner/system.md` + `adw_watch.py:22-24` |
| Agent brief | the-queue | own-page | `.claude/skills/sssf/templates/prompt_engineering/planner/system.md` |
| Issue tracker | the-queue | own-page | `.claude/skills/sssf/templates/adws/adw_watch.py:321-332` (`detect_tracker`) |
| Ticket file | the-queue | own-page | `.claude/skills/sssf/templates/adws/adw_watch.py:106-112` (`Issue` dataclass) |
| Frontier | the-queue | own-page | `.claude/skills/sssf/templates/adws/adw_watch.py:228-237` (`frontier()`) |
| Claim / resolve | the-queue | own-page | `.claude/skills/sssf/templates/adws/adw_watch.py:100-103,278-318` |
| Scan-claim-dispatch-resolve cycle | the-queue | own-page | `.claude/skills/sssf/templates/adws/adw_watch.py:335-356` (`run_once()`) |
| Mandatory checkpoints | the-queue | own-page | `.claude/skills/sssf/templates/justfile` + `docs/playbook-adopting-sssf.md` (Part D) |
| Bootstrap vocabulary | the-queue | own-page | `docs/playbook-adopting-sssf.md` (bootstrap/AFK split, Part C) |

Full pages: `the-queue/Frontier.md`, `the-queue/The-queue-watcher.md`,
`the-queue/Dark-factory.md`, `the-queue/The-four-jobs.md`,
`the-queue/Bootstrap-vocabulary.md`.

## Totals

- **80 concepts** across 7 categories.
- **36 link** rows (resolve via a relative link into `references/config.md`,
  `references/handoff.md`, or `references/observability.md`).
- **44 own-page** rows (categories 5 and 7 in full, plus `Console` moved out
  of category 6, plus `Visualizer`, plus 10 rows a fable review pass and this
  workspace's own link-checker script found had dead-end or non-doc link
  citations and reclassified — see each row's own note above — plus the
  session-directory-layout and defaults-merging worked link examples, which
  get a short own-page that mostly redirects).
- **23 of the 44 own-page rows have a dedicated page on disk**; the other 21
  are answered inside a sibling page's prose (e.g. `Gate.md` alone answers 9
  rows: `Gate`, `GateReport`, `GateCheck`, and all six built-in gate
  functions; `Permissions-and-writes.md` answers 6:
  `writes`/`protected_files`/`snapshot()`/`enforce()`/`PermissionBreach`/
  `always_writable`; `Dark-factory.md` answers 9 more) — verified row by row,
  not assumed. See `README.md`'s "What this pass built" for the authored-page
  list. No row is a dead end.
