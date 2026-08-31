# Config Reference

The full `sssf.config.yaml` spec: every field, how defaults merge, and how model / thinking / tools / extensions map onto the coding agent.

It lives at **`adws/adw_sssf_config/sssf.config.yaml`** — the default path every `adw_*.py` and the justfile resolve, and where `install.py` / `make_config.py` stamp it. Pass `--config <path>` to any ADW (or set `SSSF_CONFIG` for the justfile) to run against a different roster.

## Shape

```yaml
defaults:
  coding_agent: claude_code
  model: anthropic/claude-sonnet-4-6    # ALWAYS provider/model-id
  thinking: medium
  harness_engineering: []
  tools: [read, bash, edit, write, grep, find, ls]
  data_dir: adws/adw_data

observability:
  db: adws/adw_data/sssf.db
  poll_ms: 500

agents:
  - name: planner
    coding_agent: claude_code
    model: anthropic/claude-opus-4-6      # ALWAYS provider/model-id
    thinking: high
    color: "#a78bfa"
    purpose: Turn a request into a plan the builder can implement without asking questions.
    prompt_engineering:
      system: adws/adw_data/prompt_engineering/planner/system.md
      user: adws/adw_data/prompt_engineering/planner/user.md
    harness_engineering:
      - json-enforcer
    tools:
      - read
      - bash
```

## Fields

### `defaults`

| Field | Type | Meaning |
|---|---|---|
| `coding_agent` | `pi` \| `claude_code` \| `agy` | Which interface runs the agent. All three are implemented (`agent_pi.py`, `agent_cc.py`, `agent_agy.py`) and may be mixed per agent. Default `claude_code`. |
| `model` | string | Model id, always `provider/id`. `claude_code`: `anthropic/<id>`. `pi`: anything `pi --list-models` lists. Default `anthropic/claude-sonnet-4-6`. |
| `thinking` | enum | Reasoning effort — see below. Default `medium`. |
| `color` | hex string | Lane color for every agent that does not set its own. Default empty — the visualizer falls back to its own palette. |
| `harness_engineering` | list[string] | Pi extension paths, passed as `pi -e <path>`. **Ignored under `claude_code`/`agy`** — not deferred, not partially honoured — but `agents.validate()` now warns when a non-`pi` agent has this set, rather than staying silent about it. See "Harness engineering" below. |
| `skill_engineering` | list[string] | Vendored Pocock-protocol skill file paths, composed onto the agent's system prompt. **Ignored under `pi`/`agy`** — `agents.validate()` warns the same way. See "Skill engineering" below. |
| `skill_token_budget` | int \| null | Soft ceiling on one agent's estimated `skill_engineering` token cost. `null` (default) = no budget, no warning, ever. Exceeding it only warns — never fails the run. Per-agent overridable, same merge rule as everything else here. |
| `tools` | list[string] | Roster-wide tool allowlist. Every agent that omits its own `tools` inherits this. Unset = all tools usable. |
| `protected_files` | list[string] | Paths **no** agent may modify unless it names them in its own `writes`. Default: `adws/adw_modules/`, `adws/adw_sssf_config/`, `adws/adw_*.py` — an agent must not be able to edit the machinery that decides whether its work passed. |
| `data_dir` | path | Runtime home. Sessions land at `{data_dir}/sessions/{adw_id}/{agent_name}/`. Default `adws/adw_data`. |

### `observability`

| Field | Type | Meaning |
|---|---|---|
| `db` | path | SQLite trace db. `tracer.py` writes it directly; the visualizer polls it. Default `adws/adw_data/sssf.db`. |
| `poll_ms` | int | Visualizer live-poll cadence in ms. History uses the same queries, lazy-paged. Default `500`. |

### `agents[]`

| Field | Required | Meaning |
|---|---|---|
| `name` | yes | The identifier ADW scripts use. **ADWs name agents, never models.** |
| `purpose` | yes | One sentence: what this agent is for. Should match its `system.md` Purpose. |
| `prompt_engineering.system` | yes | Path to the system prompt — who the agent is, its single purpose, its output contract. |
| `prompt_engineering.user` | yes | Path to the default user prompt — the task template with `{{prompt}}`, `{{previous_envelope}}`, `{{context_handoff_dir}}`. |
| `color` | no | Hex swatch (`"#a78bfa"`) for this agent's lane in the visualizer. Travels config → `agent_sessions.color` → `/api/sessions/:adw_id`, and rides the `agent_start` event so a lane is colored while the agent is still running. Unset = the UI's fallback palette. |
| `coding_agent`, `model`, `thinking`, `color`, `harness_engineering`, `skill_engineering`, `skill_token_budget` | no | Override the corresponding `defaults` key. A per-agent list **replaces** the default's list entirely — it never appends. |
| `tools` | no | Allowlist. **Omitting the key means all tools usable.** A capability list, not a boundary — see `writes`. |
| `writes` | no | What this agent may modify **in the repo**, enforced after every call. Omitted = unrestricted (still barred from `protected_files`). `[]` = no repo writes at all. A list = only those paths: a trailing `/` is a directory prefix, `*` matches within one path segment, `**` crosses segments, anything else is an exact path. Naming a `protected_files` path here is what unlocks it. **The session runtime under `data_dir` is always writable** — `writes: []` means read-only with respect to the repo, not unable to write its own report. |

Output types are deliberately absent: config defines who an agent *is*; the ADW call site defines how it's *used*. One agent serves many calls — same system prompt, different user prompt + output type per call.

## Defaults merging

`agents.py` merges each entry **over** `defaults`, key by key. An entry states only what differs; anything unset inherits. `agents.validate(cfg, REQUIRED_AGENTS)` then confirms every name an ADW declares exists, resolves to a usable coding agent + model, and has both prompt files present on disk. Any miss fails the run immediately — **no agent is ever spawned against a half-valid config.**

## Thinking levels

Pi's reasoning-effort ladder, lowest to highest:

```
off | minimal | low | medium | high | xhigh | max
```

Mapped to Pi's reasoning effort control and honored when the model is registered with `reasoning: true` in `~/.pi/agent/models.json`. On a non-reasoning model the setting is inert — no error, no effect. Rough guidance: `high`/`xhigh` for planners and reviewers, `medium` for builders, `low` for mechanical read-and-report agents. Under `claude_code` the same field maps to a thinking-token budget, exported as `MAX_THINKING_TOKENS` (the CLI has no flag for it).

## Coding agents

`coding_agent` picks the module that runs a phase. All three implement the same
surface — `run(request, on_event, on_spawn, on_exit) -> PiResult`,
`resolve_model()`, `ToolCallTracker` — so `agents.execute()` selects one and
stops caring. The field is per-agent, so a roster can mix them: cheap read-only
agents on one, planner and builder on the other.

### `claude_code` — headless `claude -p`

One turn is one non-interactive CLI invocation:

```
claude -p --output-format stream-json --verbose \
  --model <id> --system-prompt <the agent's rendered system prompt> \
  --session-id <uuid>  |  --resume <uuid> \
  --setting-sources '' --strict-mcp-config \
  --allowedTools <mapped from the agent's tools> \
  --permission-mode bypassPermissions \
  <the prompt>
```

What each part is doing, and why:

- **`-p` with `stream-json`** — headless, one JSON event per line, read as it
  arrives so tool calls reach the tracer live rather than after the turn.
- **`--model`** — the roster's model with the `anthropic/` prefix stripped.
- **`--system-prompt`** — *replaces* Claude Code's default prompt, not
  `--append-`. An SSSF agent is defined by its own `prompt_engineering`; letting
  the default prompt survive underneath would mean two sets of instructions.
- **History** — turn one mints `--session-id`, every later turn in the phase
  (JSON retries, gate corrections, fix loops) uses `--resume`. That is what
  keeps a correction inside the context window the agent already built. SSSF
  session ids are not UUIDs, so they fold into a stable UUIDv5; the mapping is
  deterministic, which is what lets a rejoined run find its session.
- **`--setting-sources '' --strict-mcp-config`** — the agent runs hermetic. It
  does not inherit the engineer's hooks, plugins, custom agents or MCP servers.
  Measured cost of *not* doing this: 22,478 vs 17,932 prompt tokens per turn.
  The point is not the 20% — it is that `prompt_engineering` and `tools` are
  supposed to be the whole of what an agent sees.
- **`--permission-mode bypassPermissions`** — prompting for approval in a
  headless run would hang forever. The roster's `tools` is the allowlist and
  `permissions.py` is the enforcement.

**No Anthropic API calls.** Agents run on the engineer's logged-in Claude Code
session. `agent_cc.API_AUTH_VARS` is stripped from the child's environment
(`ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL`,
`ANTHROPIC_CUSTOM_HEADERS`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`)
so a key that reaches the ADW cannot quietly reroute agents onto metered
billing. That is a live path, not a hypothetical: the justfile does
`set dotenv-load`, `operator_env()` copies `os.environ` wholesale, and
`env.sample` invites provider keys — one `ANTHROPIC_API_KEY=` line in `.env`
would otherwise change the invoice with no change to the output or the trace.
A settings `apiKeyHelper` is the fourth route in, and `--setting-sources ''`
closes it.

Context windows are a hardcoded table in `agent_cc.CONTEXT_WINDOWS` (default
200k) because the CLI exposes no catalog to read them from.

### `pi`

Runs the Pi harness, needs a provider key per model, and is the only interface
that honours `harness_engineering`. See "Model resolution" and
"Harness engineering" below.

### `agy` — Antigravity CLI

A gateway: one CLI in front of Gemini, Claude and GPT-OSS models, so `agy models`
is the catalog and a roster entry is always `agy/<model-id>`.

    agy -p=<prompt> --model <id> --output-format stream-json
        --add-dir <repo> --dangerously-skip-permissions --print-timeout 900s
        [--conversation <id>]

Four things differ from `claude_code`, each of which shaped the adapter:

- **The prompt is a flag VALUE.** `agy -p "text"` is silently mis-parsed; it must
  be `-p=text`.
- **There is no `--system-prompt`.** An SSSF agent *is* its system prompt, so the
  adapter folds it into every user turn behind a labelled delimiter. That is
  advice inside the conversation rather than a separate channel — weaker, and
  re-sent every turn. Consider it when a system prompt carries a strict output
  contract.
- **`--add-dir` is required.** Without it the file tools are not rooted at cwd,
  and the failure is bizarre rather than obvious: a probe for a file sitting in
  cwd searched `~/Downloads`, then ran `find` across the whole home directory,
  burning 120k tokens over 41 tool calls before timing out having written
  nothing.
- **`thinking` is IGNORED.** Effort is encoded in the model id
  (`-high` / `-medium` / `-low`), and passing `--effort` as well is a hard error.
  Ask for more effort by choosing `agy/gemini-3.7-flash-high`.

Also: `agy` exits **0** when its result payload reports `ERROR`, so a timeout
arrives as a successful process with a failed body. The adapter raises on that
explicitly — otherwise the factory would treat a stalled turn as a completed one.

**No cost data.** `agy` reports tokens but never dollars, so `PiResult.cost` stays
0.00 for this interface. A `$0.00` in the trace means *unknown*, not *free*.
Authentication is OAuth against the Code Assist backend, not an API key.

## Model resolution

**Always write `model` as `provider/model-id`.** `agents.py` hands the string to whichever interface the agent's `coding_agent` selects, and each resolves it its own way.

Under **`claude_code`**, the provider half must be `anthropic`; anything else raises at `validate()` rather than on the first billed call, because Claude Code talks to Anthropic only. The id is passed straight through as `claude --model <id>`, so it must be a name the CLI accepts — a full id like `claude-sonnet-4-6`, or one of the aliases `sonnet` / `opus` / `haiku`. There is no catalog command to check against; an unknown id fails when the agent runs.

Under **`pi`**, the rest of this section applies. It resolves against pi's merged catalog — `~/.pi/agent/models.json` plus pi's built-in providers. The same model is usually carried by more than one provider (`gemini-3.6-flash` lives under `google` *and* under `openrouter` as `google/gemini-3.6-flash`), and a bare id that matches several **raises at resolution**:

```
agent 'scout': model pattern 'gemini-3.6-flash' is ambiguous:
  [('google', 'gemini-3.6-flash'), ('openrouter', 'google/gemini-3.6-flash'), ...]
```

That is `agents.validate()` doing its job — it fails before anything spawns rather than silently billing the wrong provider — but it means every agent in the roster inheriting that default is grounded until the pattern is qualified. Qualifying is the whole fix: `google/gemini-3.6-flash`, `openai/gpt-5.6-terra`, `fireworks/accounts/fireworks/models/kimi-k3`. The leading segment is matched against the provider list first, so the rest of the string can contain slashes.

Other consequences worth knowing:

- A model must be in the catalog before any agent can name it. An unknown id fails at resolution, before spawn. `pi --list-models` is the catalog the resolver actually reads.
- **Ambiguity can appear without you touching the config.** Registering a new provider that carries a model you already use turns a formerly-fine bare pattern ambiguous. If a roster stops validating and nobody edited it, that is why.
- Provider credentials come from the environment, not the config — the key that matches the provider you named (`GEMINI_API_KEY` for `google/...`, `OPENROUTER_API_KEY` for `openrouter/...`).
- The resolved model is recorded per session in `agent_map.json` and mirrored into the `agent_sessions` table. **Changing an agent's model invalidates its session**: a joined run starts that agent fresh instead of resuming a context window built by a different model.

## Tools

`tools` maps to `pi --tools`. Pi's seven builtin tool names:

| Tool | Purpose | Pi's own default |
|---|---|---|
| `read` | read file contents | on |
| `bash` | execute bash commands | on |
| `edit` | find/replace edits | on |
| `write` | create/overwrite files | on |
| `grep` | search file contents | **off** |
| `find` | find files by glob | **off** |
| `ls` | list directory contents | **off** |

`grep`, `find`, and `ls` are off in bare Pi, so an agent that does not name them will shell out through `bash` to do the same work. The starter roster therefore sets `defaults.tools` to all seven and lets each agent narrow from there.

**Resolution order:** an agent's own `tools` list wins; an agent that omits the key inherits `defaults.tools`; if neither is set, `tools` stays `None` and all tools are usable. An empty list is not "all tools" — it is a tool-less agent, and it will stall.

## Write permissions — `writes` and `protected_files`

`tools` cannot express a safety boundary, because two of the tools are general
purpose. `bash` runs anything, including `git checkout`, which discards an
engineer's uncommitted work; `write` reaches any path, not only the one report
file an agent was granted it for. So "this agent changes nothing" is a claim a
tool list can state but never keep.

`adw_modules/permissions.py` keeps it, the same way every other claim in this
system is kept — after the fact, against the repo. Before an agent's first
prompt the working tree's change-set is fingerprinted; after its last send
(including JSON retries and gate corrections) it is fingerprinted again. Any
path that appeared, vanished, or changed is attributed to that agent.

Comparing change-sets rather than watching writes is deliberate: a path that was
modified before the agent ran and is clean afterwards has been **reverted**, and
a reversion is a modification. That is what catches `git checkout`.

A breach is not a gate violation. Gates are for work an agent can be asked to
redo; a write has already happened, so re-prompting fixes nothing. Instead:

1. every unauthorized change the agent **introduced** is rolled back — tracked
   files with `git checkout --`, untracked files by deletion;
2. a path that was **already dirty** before the agent ran is left untouched. The
   operator had uncommitted work there, and discarding it to tidy up would be
   the same harm this module exists to prevent;
3. the phase fails and names every path with what happened to it.

```yaml
defaults:
  protected_files: [adws/adw_modules/, adws/adw_sssf_config/, "adws/adw_*.py"]

agents:
  - name: builder      # no `writes` key -> unrestricted, minus protected_files
  - name: scout
    writes: []         # no repo writes; its findings still land in context_handoff/
  - name: planner
    writes: [specs/]
  - name: documenter
    writes: [app_docs/, docs/, "**/*.md", "*.md"]
```

**The session runtime under `data_dir` is always writable, for every agent.**
`context_handoff/` is how agents hand work to each other, and each agent's
prompts, `raw_output.jsonl`, and `envelope.json` sit beside it. That grant comes
from `data_dir` rather than from `.gitignore`: the runtime is normally ignored,
so it never even appears in a snapshot, but an agent's ability to record its own
work must not depend on a gitignore line someone can delete.

Narrow by role, not by reflex. Anything that must produce a `context_handoff/` artifact needs `write`, or it will resort to a `bash` heredoc. Withhold `edit`/`write` only where the restriction *is* the guarantee — a reviewer that cannot edit cannot quietly fix what it was asked to report.

### Extension tools must be named explicitly

`pi --tools` is an allowlist over **built-in, extension, and custom tools alike** — not just builtins. So the moment an agent has a `tools` list at all (its own, or one inherited from `defaults`), any tool registered by its `harness_engineering` extensions is **excluded unless it appears in that list by name**.

This fails quietly. The extension still loads, the run still succeeds, and the tool the extension exists to provide is simply never offered to the model — you find out by noticing the agent never called it.

```yaml
  - name: reviewer
    harness_engineering:
      - .pi/extensions/ast_query.ts     # registers tool: ast_query
    tools:
      - read
      - grep
      - find
      - ls
      - bash
      - ast_query                       # REQUIRED — the extension's tool, named or lost
```

Rule: **every entry in `harness_engineering` that registers a tool must have that tool name added to the agent's `tools` list.** Adding an extension is therefore a two-line change, never one. The alternative is dropping the `tools` key *and* leaving `defaults.tools` unset so the agent resolves to `None` (all tools) — but with a roster-wide `defaults.tools` in place, that escape hatch is closed; naming the tool is the only path.

## Harness engineering

`harness_engineering` entries are pi extension **file paths**, passed through as `pi -e <path>`, one flag per entry, scoped to that agent only. This is where per-agent harness changes live — e.g. an output-tightening extension for an agent that keeps wrapping its envelope in prose.

**Under `coding_agent: claude_code`/`agy` the field is ignored.** Not deferred, not partially honoured — `agent_cc.build_command` never reads it. `agents.validate()` prints a warning naming the agent (to stderr, before anything spawns) — see `ignored_field_warnings()` — but the run still proceeds; this is a warning, never a failure. An agent that declares `subagents.ts` and lists `subagent_create` in its `tools` still gets subagents under `claude_code`, because `_map_tools` aliases every `subagent_*` name onto Claude Code's own `Task` tool; it just is not the extension the config names. Anything else an extension would have done — new tools, output shaping, extra flags — does not happen. If a roster depends on a pi extension, that agent belongs on `coding_agent: pi`.

The reason it is ignored rather than translated: pi extensions are TypeScript loaded into pi's own harness. Claude Code's equivalent surfaces are MCP servers and hooks, which are a different shape and arrive through `--mcp-config` and settings, not `-e`. A faithful translation is not a mapping exercise, so the field stays pi-only until someone writes that path deliberately.

**If the extension registers a tool, name that tool in the agent's `tools` list too** — `--tools` filters extension tools exactly like builtins, so an unnamed extension tool is silently unavailable no matter that the extension loaded fine. See [Extension tools must be named explicitly](#extension-tools-must-be-named-explicitly) above. Extensions that only shape output or add flags (no tool registration) need no `tools` change.

## Skill engineering

`skill_engineering` names Pocock-style workflow-protocol files (`tdd`, `codebase-design`, `diagnosing-bugs`, a grilling protocol — anything shaped like a `SKILL.md`) that get composed onto an agent's system prompt at call time. See `docs/prd-skill-engineering.md` for the full design; this section is the field reference.

**Why this exists.** SSSF governs *where and when* an agent runs — phases, gates, the envelope. It says nothing about *how rigorously* the agent works once running. A body of proven engineering-discipline skills already exists as `SKILL.md` files, but SSSF agents run with `--setting-sources ''` for hermeticity, which hides every user-installed skill (measured: 22,478 → 17,932 prompt tokens/turn). `skill_engineering` routes the protocol in as **vendored, committed text** instead — reproducible across machines, reviewable in a diff, and it costs nothing extra in hermeticity.

```yaml
agents:
  - name: builder
    skill_engineering:
      - adws/adw_data/skill_engineering/tdd.md
```

**Composition order: the agent's own `system.md` first, then skills in the order listed — never sorted.** The agent's identity and output contract outrank any borrowed protocol; if `tdd.md` and `builder/system.md` disagree about output shape, the envelope contract wins, or the phase fails to parse and the "fix" is a JSON retry loop that costs money to discover. Order is also what keeps the composed prompt — and therefore the prompt cache — stable across runs; an unstable order is a cost regression waiting to be noticed.

**Under `coding_agent: pi`/`agy` the field is ignored** — the same way, and warned about the same way, as `harness_engineering` under `claude_code` above. Skills ride in `--system-prompt`, which is a `claude_code`-specific delivery mechanism.

**Cost is real and re-sent every turn.** A skill's text lands in the system prompt, so it is billed on every internal turn of a phase, on top of the ~15.5k-token Claude Code base prompt no flag removes. Set `skill_token_budget` (roster-wide via `defaults`, or per-agent) to get a warning — never a hard failure — when a composed prompt's estimated cost exceeds it. The estimate is a `chars/4` heuristic, reported as "est." everywhere it's shown, never presented as a real tokenizer count.

**Enforcement stays at outcome gates only.** No gate ever attempts to prove a protocol was followed — no inspecting intermediate commits for a failing test, no requiring the envelope to cite a test written first. `tdd.md` shapes how the builder works; the suite, the linter, and the typechecker judge what came out. A gate that claims to verify process but can be satisfied by a well-worded envelope is worse than no gate.

**Vendoring** — `uv run <skill>/scripts/vendor_skill.py <source>` — copies a skill file into `adws/adw_data/skill_engineering/`, stamped with a provenance header (source path, date, content hash) that's stripped before the text ever reaches a model. Re-vendoring unchanged content is a no-op. `vendor_skill.py --check <vendored-file>` reports drift against the source without touching anything. Nothing auto-updates, ever — see the [attach-a-skill cookbook](../cookbooks/attach_a_skill.md) for the full walkthrough.

**Audit what's vendored and who uses it** — `just skills` (backed by `adws/adw_skills.py`, free: no agents, no trace) lists every vendored file and the agent names that reference it, plus anything an agent names outside the vendored directory.

**Recommended pairings — documented, not enabled by default.** Adding unrequested per-turn cost to every fresh install would be wrong, so the starter roster ships with no `skill_engineering` set anywhere:

| Agent | Skill | Why |
|---|---|---|
| `builder` | `tdd` | A feature arrives with tests that were written to fail first. |
| `reviewer` | `codebase-design` | Judges module depth and interface quality, not just correctness. |
| `planner` | a grilling protocol | Resolves ambiguity before the expensive build phase starts. Verify this one before trusting it in a headless run — the skill assumes a human is present to answer questions, and a planner with nobody to grill could stall or invent answers. |
| fix-loop builder | `diagnosing-bugs` | A red gate produces a diagnosis, not a guess. |

Opt in per roster, and read the diff and the trace after the first run either way — a skill changing behaviour is a claim, and this repo does not take claims on their word.
