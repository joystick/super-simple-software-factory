"""Claude Code interface — headless (`-p`) driver for the factory.

Mirrors `agent_pi.run()` one-for-one so `agents.execute()` does not care which
coding agent is behind a phase: same `PiRequest` in, same `PiResult` out, same
`on_event` / `on_spawn` / `on_exit` callbacks, same JSONL raw stream on disk.

The four things the caller needs from a headless turn, and how they are wired:

    -p --output-format stream-json   non-interactive; one JSON event per line,
                                     streamed, so the tracer sees tool calls as
                                     they happen instead of after the fact
    --model <id>                     the roster's model, provider prefix stripped
    --system-prompt <text>           the agent's rendered system prompt, REPLACING
                                     Claude Code's default (not appended) — an
                                     SSSF agent is defined by its own prompt
    --session-id / --resume          history: turn one mints the session, every
                                     later turn in the same phase (JSON retries,
                                     gate corrections) resumes it, so the agent
                                     keeps its context window

`--session-id` wants a UUID and SSSF session ids are not, so the SSSF id is
folded into a stable UUIDv5. The mapping is deterministic: the same SSSF session
id always yields the same Claude session, which is what makes a rejoined run
land in the context window it left.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Callable, Optional

from .data_types import PiRequest, PiResult
from .utils import now_iso, operator_env

CLAUDE_PATH = os.environ.get("CLAUDE_PATH", "claude")

# Stripped from the child's environment so agents always run on the logged-in
# Claude Code session and never on a metered API key.
#
# The exposure is real, not theoretical: the justfile does `set dotenv-load`,
# `operator_env()` copies os.environ wholesale, and env.sample invites the
# engineer to add provider keys. One ANTHROPIC_API_KEY line in .env would flip
# every agent from the subscription to per-token API billing, silently — same
# output, same trace, a different invoice. BASE_URL and the BEDROCK/VERTEX
# switches are here for the same reason: each one redirects the child to a
# billed backend. (An `apiKeyHelper` in settings is a fourth route, already
# closed by `--setting-sources ''` in build_command.)
API_AUTH_VARS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_CUSTOM_HEADERS",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
)

RESULT_SNIPPET_CHARS = 20_000
ARG_VALUE_CHARS = 20_000
LABEL_CHARS = 80

PRIMARY_ARGS = ("command", "path", "file_path", "pattern", "query", "url", "prompt")

# Stable namespace for SSSF -> Claude session id folding. Fixed forever: change
# it and every existing session becomes unreachable.
SESSION_NAMESPACE = uuid.UUID("6ba7b812-9dad-11d1-80b4-00c04fd430c8")

# Roster tool names are pi's. Claude Code's are capitalized and split differently.
TOOL_ALIASES = {
    "read": "Read",
    "bash": "Bash",
    "edit": "Edit",
    "write": "Write",
    "grep": "Grep",
    "find": "Glob",
    "ls": "Glob",            # Claude Code has no `ls` tool; Glob covers listing
    "subagent_create": "Task",
    "subagent_continue": "Task",
    "subagent_list": "Task",
    "subagent_remove": "Task",
}

# Context ceilings by model id. Claude Code does not expose a catalog command,
# so the windows live here rather than being discovered like pi's.
CONTEXT_WINDOWS = {
    "claude-opus-4-6": 1_000_000,
    "claude-opus-4-7": 1_000_000,
    "claude-sonnet-4-6": 1_000_000,
}
DEFAULT_CONTEXT_WINDOW = 200_000

# `thinking` maps to a token budget, the way pi maps it to a reasoning effort.
# Claude Code has no flag for this — it reads MAX_THINKING_TOKENS from the
# environment — so the budget is exported at spawn rather than passed in argv.
THINKING_BUDGETS = {
    "off": 0, "minimal": 1_024, "low": 4_000,
    "medium": 10_000, "high": 24_000, "xhigh": 32_000, "max": 64_000,
}


def resolve_model(pattern: str) -> tuple[str, str]:
    """Resolve a roster pattern to ``(provider, model_id)``.

    Claude Code talks to Anthropic only, so the provider half must be
    `anthropic` — a config pointing this coding agent at openai/ or google/ is a
    config error, and saying so here means it fails at validate() rather than
    on the first billed call.
    """
    if "/" in pattern:
        provider, model_id = pattern.split("/", 1)
        if provider != "anthropic":
            raise ValueError(
                f"model pattern {pattern!r} names provider {provider!r}, but "
                "coding_agent 'claude_code' can only run anthropic models — "
                "use anthropic/<model-id>, or switch the agent to coding_agent: pi")
        return provider, model_id
    # Bare aliases Claude Code resolves itself (`sonnet`, `opus`, `haiku`).
    if pattern in ("sonnet", "opus", "haiku", "sonnet[1m]", "opusplan"):
        return "anthropic", pattern
    raise ValueError(
        f"model pattern {pattern!r} is not provider-qualified — write it as "
        "anthropic/<model-id> (e.g. anthropic/claude-sonnet-4-6)")


def context_window(provider: str, model_id: str) -> int:
    for prefix, window in CONTEXT_WINDOWS.items():
        if model_id.startswith(prefix):
            return window
    return DEFAULT_CONTEXT_WINDOW


def claude_session_id(sssf_session_id: str) -> str:
    """Fold an SSSF session id into the UUID `--session-id` insists on."""
    return str(uuid.uuid5(SESSION_NAMESPACE, sssf_session_id))


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _label(tool: str, args: dict) -> str:
    value = next((args[key] for key in PRIMARY_ARGS
                  if isinstance(args.get(key), str) and args[key].strip()), "")
    if not value:
        value = next((v for v in args.values() if isinstance(v, str) and v.strip()), "")
    value = " ".join(str(value).split())
    return f"{tool}: {_clip(value, LABEL_CHARS)}" if value else tool


def _text_of(message: dict) -> str:
    """Join the text blocks of an Anthropic-shaped message."""
    return "".join(block.get("text", "") for block in message.get("content", []) or []
                   if isinstance(block, dict) and block.get("type") == "text")


def _result_text(content) -> str:
    """A tool_result's content is a string or a list of blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(block.get("text", "") for block in content
                       if isinstance(block, dict) and block.get("type") == "text")
    return ""


def _map_tools(tools: Optional[list[str]]) -> Optional[list[str]]:
    """Roster tool names -> Claude Code tool names, de-duplicated, order kept."""
    if not tools:
        return None
    mapped: list[str] = []
    for name in tools:
        claude_name = TOOL_ALIASES.get(name, name)
        if claude_name not in mapped:
            mapped.append(claude_name)
    return mapped


def _occupancy(usage: dict) -> int:
    """How full the context window was for one model call.

    Every component counts: cached prompt is still prompt, and the output just
    written is part of the window the next call inherits.
    """
    return int(sum(usage.get(part) or 0 for part in
                   ("input_tokens", "output_tokens",
                    "cache_read_input_tokens", "cache_creation_input_tokens")))


def _pi_shaped_usage(usage: dict, cost: float) -> tuple[dict, int]:
    """Translate Claude's usage block into the pi shape `UsageBreakdown` folds.

    Claude reports cache creation and cache reads as separate counters and does
    NOT include them in `input_tokens`, which is the same convention pi uses —
    so the parts add up the same way on both sides.
    """
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    cache_write = int(usage.get("cache_creation_input_tokens") or 0)
    cache_read = int(usage.get("cache_read_input_tokens") or 0)
    total = input_tokens + output_tokens + cache_write + cache_read
    shaped = {
        "input": input_tokens,
        "output": output_tokens,
        "cacheWrite": cache_write,
        "cacheRead": cache_read,
        "totalTokens": total,
        # Claude does not itemize cost per component in the CLI stream; the one
        # authoritative number is the turn total, so it rides on `total` alone
        # rather than being split into fabricated parts.
        "cost": {"total": cost},
    }
    return shaped, total


class ToolCallTracker:
    """Folds Claude Code's tool stream into ONE record per completed call.

    Claude announces a call as a `tool_use` block on an assistant message, then
    reports it as a `tool_result` block on the following user message. Only the
    result knows whether it worked, so that is where a record is emitted — the
    same one-event-per-real-call contract `agent_pi.ToolCallTracker` provides,
    so `agents._event_forwarder` consumes either without knowing the difference.
    """

    def __init__(self) -> None:
        self._open: dict[str, dict] = {}

    def observe(self, event: dict) -> Optional[dict]:
        etype = event.get("type", "")
        if etype == "assistant":
            for block in event.get("message", {}).get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    self._announce(block.get("id"), block.get("name"),
                                   block.get("input"))
            return None
        if etype != "user":
            return None
        for block in event.get("message", {}).get("content", []) or []:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                return self._close(block)
        return None

    def _close(self, block: dict) -> dict:
        call_id = str(block.get("tool_use_id") or "")
        opened = self._open.pop(call_id, {})
        tool = str(opened.get("tool") or "tool")
        args = opened.get("args") or {}
        record = {
            "tool": tool,
            "tool_call_id": call_id,
            "args": {key: _clip(value, ARG_VALUE_CHARS) if isinstance(value, str) else value
                     for key, value in args.items()},
            "ok": not block.get("is_error", False),
            "label": _label(tool, args),
        }
        result_text = _result_text(block.get("content"))
        if result_text:
            record["result_snippet"] = _clip(result_text, RESULT_SNIPPET_CHARS)
        record["ended_at"] = now_iso()
        if opened.get("clock"):
            record["duration_ms"] = int((time.monotonic() - opened["clock"]) * 1000)
        if opened.get("started_at"):
            record["started_at"] = opened["started_at"]
        return record

    def _announce(self, call_id, tool, args) -> None:
        if not call_id:
            return
        known = self._open.get(str(call_id), {})
        self._open[str(call_id)] = {
            "tool": tool or known.get("tool", ""),
            "args": args or known.get("args", {}),
            "started_at": known.get("started_at") or now_iso(),
            "clock": known.get("clock") or time.monotonic(),
        }


def _session_marker(request: PiRequest, session_uuid: str) -> Path:
    """Marker recording that this Claude session has been opened.

    `--session-id` mints a session; resuming one that does not exist yet fails,
    and minting one that already exists fails too. The marker is what tells the
    two apart across separate ADW processes — an in-memory flag would forget
    between runs, which is exactly when a rejoined session needs to resume.
    """
    return Path(request.session_dir) / f"{session_uuid}.opened"


def build_command(request: PiRequest, resume: bool) -> list[str]:
    """The exact headless invocation. Split out so it can be asserted in tests
    without spawning anything or spending a cent."""
    _provider, model_id = resolve_model(request.model)
    session_uuid = claude_session_id(request.session_id)

    cmd = [
        CLAUDE_PATH,
        "-p",                                   # headless: print and exit
        "--output-format", "stream-json",       # one JSON event per line, live
        "--verbose",                            # required for stream-json under -p
        "--model", model_id,
        "--system-prompt", request.system_prompt,
    ]
    # History. Turn one mints the id; every later turn resumes that same
    # conversation, which is what keeps retries and gate corrections inside the
    # context window the agent already built.
    cmd += ["--resume", session_uuid] if resume else ["--session-id", session_uuid]

    # Hermetic agents. Without these, every turn inherits the OPERATOR's
    # settings — their hooks, plugins, custom agents and MCP servers — and pays
    # for the tool schemas in the prompt. Measured on a trivial turn: 22,478
    # prompt tokens inherited vs 17,932 hermetic, so ~4.5k tokens (-20%) per
    # turn, on every send, for context an SSSF agent was never meant to have.
    # `--setting-sources ''` does the work; `--strict-mcp-config` closes the MCP
    # path that settings are not the only route into. (`-nc` was measured too
    # and saves nothing — CLAUDE.md is not in the cached prefix.)
    cmd += ["--setting-sources", "", "--strict-mcp-config"]

    tools = _map_tools(request.tools)
    if tools:
        cmd += ["--allowedTools", *tools]
    # The roster's `tools` list is the allowlist and permissions.py is the
    # enforcement; prompting for approval in a headless run would just hang.
    cmd += ["--permission-mode", "bypassPermissions"]

    cmd.append(request.prompt)
    return cmd


def run(request: PiRequest, on_event: Optional[Callable[[dict], None]] = None,
        on_spawn: Optional[Callable[[int], None]] = None,
        on_exit: Optional[Callable[[int], None]] = None) -> PiResult:
    """Run one non-interactive Claude Code turn. Contract-identical to
    `agent_pi.run`."""
    _provider, model_id = resolve_model(request.model)
    session_uuid = claude_session_id(request.session_id)

    Path(request.session_dir).mkdir(parents=True, exist_ok=True)
    marker = _session_marker(request, session_uuid)

    raw_path = Path(request.raw_output_path)
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    env = operator_env()
    # CLAUDE_CONFIG_DIR is deliberately NOT overridden. It is where Claude Code
    # keeps credentials as well as sessions, so pointing it at a per-agent
    # directory yields a child that cannot authenticate ("Not logged in").
    # Sessions do not need that isolation anyway: every session id is a UUID
    # derived from the SSSF id, so two agents can never collide in the shared
    # store. `request.session_dir` holds only SSSF's own marker files.
    for name in API_AUTH_VARS:
        env.pop(name, None)
    budget = THINKING_BUDGETS.get(request.thinking)
    if budget:
        env["MAX_THINKING_TOKENS"] = str(budget)

    def attempt(resume: bool) -> tuple[PiResult, str]:
        """One spawn. Returns the parsed result and whatever went to stderr."""
        result = PiResult(session_id=request.session_id,
                          context_window=context_window(_provider, model_id))
        # stdin is DEVNULL for the same reason it is in agent_pi: the prompt
        # travels in argv, and an inherited non-TTY stdin can leave the child
        # waiting on input that never arrives.
        process = subprocess.Popen(build_command(request, resume=resume),
                                   stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, bufsize=1, cwd=request.cwd, env=env)
        if on_spawn:
            on_spawn(process.pid)

        with raw_path.open("a") as raw:
            assert process.stdout is not None
            for line in process.stdout:
                raw.write(line)
                raw.flush()
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                etype = event.get("type")
                if etype == "assistant":
                    message = event.get("message", {}) or {}
                    text = _text_of(message)
                    if text:
                        result.text = text      # last assistant message wins
                    # Occupancy comes from HERE, not from the result event.
                    # One `claude -p` call runs a whole agentic loop, and each
                    # assistant message reports the window as it stood for that
                    # model call — which is what the context bar measures.
                    occupancy = _occupancy(message.get("usage") or {})
                    if occupancy:
                        result.context_tokens = occupancy
                elif etype == "result":
                    # The terminal event carries the authoritative final text
                    # and the run's billed usage — CUMULATIVE over every
                    # internal turn (13 model calls in a routine scout run), so
                    # it is spend, never occupancy. Reading it as occupancy
                    # reports 298k against a 200k window.
                    if event.get("result"):
                        result.text = str(event["result"])
                    cost = float(event.get("total_cost_usd") or 0.0)
                    usage, total = _pi_shaped_usage(event.get("usage") or {}, cost)
                    result.tokens += total
                    result.usage.add_turn(usage, total)
                    result.cost += cost
                if on_event:
                    on_event(event)

        stderr = process.stderr.read() if process.stderr else ""
        result.returncode = process.wait()
        if on_exit:
            on_exit(process.pid)
        return result, stderr

    resuming = marker.exists()
    result, stderr = attempt(resume=resuming)

    # A minted session exists on Claude's side the moment it is created, even if
    # that turn then failed — so a lost marker (crash, wiped session_dir, a run
    # rejoined from elsewhere) would otherwise strand the agent forever on
    # "Session ID ... is already in use". Take Claude's word for it and resume.
    if result.returncode != 0 and not resuming and "already in use" in stderr:
        marker.write_text(now_iso())
        result, stderr = attempt(resume=True)

    if result.returncode == 0:
        # Written whether or not this was the minting turn: the marker records
        # "this session exists", and re-writing it is harmless.
        marker.write_text(now_iso())
    elif not result.text:
        raise RuntimeError(f"claude exited {result.returncode}: {stderr.strip()[-800:]}")
    return result
