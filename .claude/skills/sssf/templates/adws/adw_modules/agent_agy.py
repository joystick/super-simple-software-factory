"""Antigravity (`agy`) interface — a third coding agent for the factory.

Same contract as `agent_pi.run` and `agent_cc.run`: `PiRequest` in, `PiResult`
out, the same on_event / on_spawn / on_exit callbacks, the same JSONL raw stream
on disk. `agents.execute()` picks a module and stops caring which.

`agy` is a gateway: one CLI in front of Gemini, Claude and GPT-OSS models, so
`agy models` is the catalog and the provider half of a roster entry is always
`agy`.

FOUR DIFFERENCES FROM `claude` THAT SHAPE THIS FILE
---------------------------------------------------

1. **The prompt is a flag VALUE, not a positional argument.** `agy -p "text"`
   silently takes `-p` to mean the next token; it must be `-p=text`. The CLI
   diagnoses this well, but only after wasting a call.

2. **There is no `--system-prompt`.** An SSSF agent *is* its rendered system
   prompt, so the prompt is prepended to the user turn behind a labelled
   delimiter. Weaker than a real system channel and it costs those tokens on
   every turn — see `_compose` for what that buys and what it does not.

3. **`--add-dir` is REQUIRED, and its absence fails strangely.** Without it the
   file tools are not rooted at cwd: a probe asking for a file sitting in cwd
   went looking through `~/Downloads`, then `find /Users/... -name note.txt`
   across the whole home directory, burned 120k tokens over 41 tool calls, and
   timed out having written nothing. With `--add-dir` the same task took one
   turn and 2.3 seconds.

4. **Conversation ids are ASSIGNED, not minted.** `claude` accepts a
   `--session-id` you choose; `agy` returns a `conversation_id` from the first
   call which later turns pass to `--conversation`. So the id is captured and
   stored rather than derived — see `_conversation_file`.

NO COST DATA. `usage` reports tokens but never dollars, so `PiResult.cost`
stays 0.0 for this interface and the trace's cost column is silent rather than
guessed. Tokens are real; money would be a made-up number from a price table
nobody is maintaining.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from functools import lru_cache
from pathlib import Path
from typing import Callable, Optional

from .data_types import PiRequest, PiResult
from .utils import now_iso, operator_env

AGY_PATH = os.environ.get("AGY_PATH", "agy")

# Stripped from the child's environment so agy always runs on the logged-in
# OAuth session and never silently switches to a metered API path.
#
# Verified on this machine: agy authenticates with an OAuth refresh_token in
# ~/.gemini/oauth_creds.json and calls daily-cloudcode-pa.googleapis.com — the
# Code Assist backend — not generativelanguage.googleapis.com (AI Studio) or
# Vertex. There is no API key in play today.
#
# The guard is for tomorrow. The justfile does `set dotenv-load` and
# operator_env() copies os.environ wholesale into every agent subprocess, so a
# GEMINI_API_KEY added to .env for some unrelated tool would be inherited by
# every agy agent. If that flipped the CLI onto the Gemini API it would be the
# same failure agent_cc.API_AUTH_VARS exists to prevent: identical output,
# identical trace, a different meter.
#
# Note the honest limit of this guard. Unlike the Anthropic case — where the
# effect of ANTHROPIC_API_KEY on `claude` was confirmed — I have NOT verified
# that any of these would actually redirect agy. They are stripped because
# they plausibly could and cost nothing to remove, not because a test proved
# each one dangerous.
API_AUTH_VARS = (
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENAI_API_KEY",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_QUOTA_PROJECT",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_GENAI_USE_VERTEXAI",
    "VERTEXAI_PROJECT",
    "VERTEXAI_LOCATION",
)

RESULT_SNIPPET_CHARS = 20_000
ARG_VALUE_CHARS = 20_000
LABEL_CHARS = 80

PRIMARY_ARGS = ("CommandLine", "command", "path", "file_path", "AbsolutePath",
                "pattern", "query", "url", "prompt")

# NOTE: the roster's `thinking` field is IGNORED under coding_agent: agy.
#
# agy encodes reasoning effort in the MODEL ID — gemini-3.7-flash-high,
# -medium, -low — so a separate `--effort` flag contradicts it. Passing both is
# a hard error, discovered on the first real run:
#
#   invalid model selection (--model "gemini-3.7-flash-medium"
#   --effort "high"): --model gemini-3.7-flash-medium conflicts with
#   --effort=high
#
# Rather than pass --effort only for the few ids that lack a suffix — a rule
# that would silently rot as the catalog changes — effort is left entirely to
# the model id. Choose it there: agy/gemini-3.7-flash-high, not thinking: high.
# This mirrors how harness_engineering is inert under claude_code.

# agy exposes no context-window figure, so these are the published ceilings for
# the model families it serves. Wrong-but-close beats a bar that reads 0.
CONTEXT_WINDOWS = {
    "gemini": 1_000_000,
    "claude-opus": 1_000_000,
    "claude-sonnet": 1_000_000,
    "gpt-oss": 128_000,
}
DEFAULT_CONTEXT_WINDOW = 128_000

# Long timeout: a build phase legitimately runs for minutes. The default is 5m,
# which a real feature will exceed.
PRINT_TIMEOUT = os.environ.get("AGY_PRINT_TIMEOUT", "900s")


@lru_cache(maxsize=1)
def _catalog() -> list[str]:
    """Model ids `agy models` reports. The same role pi's catalog plays."""
    try:
        result = subprocess.run([AGY_PATH, "models"], capture_output=True,
                                text=True, timeout=60, env=operator_env(),
                                check=False)
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    ids = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].strip():
            ids.append(parts[0].strip())
    return ids


def resolve_model(pattern: str) -> tuple[str, str]:
    """Resolve `agy/<model-id>` against the live catalog.

    Validating here means a typo fails at `agents.validate()` — before anything
    spawns — rather than partway through a billed run.
    """
    if "/" not in pattern:
        raise ValueError(
            f"model pattern {pattern!r} is not provider-qualified — write it as "
            "agy/<model-id>, e.g. agy/gemini-3.7-flash-medium")
    provider, model_id = pattern.split("/", 1)
    if provider != "agy":
        raise ValueError(
            f"model pattern {pattern!r} names provider {provider!r}, but "
            "coding_agent 'agy' only runs models from `agy models` — use "
            "agy/<model-id>, or switch the agent to another coding_agent")
    catalog = _catalog()
    if catalog and model_id not in catalog:
        raise ValueError(
            f"model {model_id!r} is not in `agy models` — available: "
            f"{', '.join(catalog[:6])}…")
    return provider, model_id


def context_window(provider: str, model_id: str) -> int:
    for prefix, window in CONTEXT_WINDOWS.items():
        if model_id.startswith(prefix):
            return window
    return DEFAULT_CONTEXT_WINDOW


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _label(tool: str, args: dict) -> str:
    value = next((args[k] for k in PRIMARY_ARGS
                  if isinstance(args.get(k), str) and args[k].strip()), "")
    if not value:
        value = next((v for v in args.values() if isinstance(v, str) and v.strip()), "")
    value = " ".join(str(value).split())
    return f"{tool}: {_clip(value, LABEL_CHARS)}" if value else tool


def _compose(system_prompt: str, prompt: str) -> str:
    """Fold the system prompt into the user turn, because agy has no other channel.

    Stated as a labelled block rather than glued on, so the model can tell the
    standing instructions from this turn's request. This is genuinely weaker
    than `claude --system-prompt`: it is advice inside the conversation rather
    than a separate channel, it can be argued with, and it is re-sent every turn.
    """
    if not system_prompt.strip():
        return prompt
    return (
        "=== STANDING INSTRUCTIONS (apply to every turn of this conversation) ===\n"
        f"{system_prompt.strip()}\n"
        "=== END STANDING INSTRUCTIONS ===\n\n"
        f"{prompt}"
    )


def _conversation_file(request: PiRequest) -> Path:
    """Where the assigned conversation id is remembered between turns.

    `claude` lets you mint a session id, so agent_cc derives one deterministically.
    agy assigns one, so it has to be captured from the first result and stored.
    """
    return Path(request.session_dir) / f"{request.session_id}.conversation"


def build_command(request: PiRequest, conversation: str | None) -> list[str]:
    """The exact invocation. Split out so it can be asserted without spending."""
    _provider, model_id = resolve_model(request.model)
    cmd = [
        AGY_PATH,
        "--model", model_id,
        "--output-format", "stream-json",
        # Required. Without it the file tools are not rooted at cwd — see the
        # module docstring for what that failure actually looks like.
        "--add-dir", str(Path(request.cwd).resolve()),
        # A headless run cannot answer a permission prompt; it would hang until
        # the timeout. The roster's `writes` and permissions.py are the real
        # boundary, exactly as with the other interfaces.
        "--dangerously-skip-permissions",
        "--print-timeout", PRINT_TIMEOUT,
    ]
    if conversation:
        cmd += ["--conversation", conversation]
    # THE PROMPT IS A FLAG VALUE. `-p "text"` is silently wrong.
    cmd.append(f"-p={_compose(request.system_prompt, request.prompt)}")
    return cmd


class ToolCallTracker:
    """Folds agy's step stream into ONE record per completed tool call.

    agy emits `step_update` events keyed by `step_index`: an ACTIVE one when a
    tool starts and a DONE one when it returns, with the output attached. Only
    the DONE carries a result, so that is where a record is emitted — the same
    one-record-per-real-call contract the other two trackers provide, so
    `agents._event_forwarder` consumes any of them without knowing the
    difference.
    """

    def __init__(self) -> None:
        self._open: dict[str, dict] = {}

    def observe(self, event: dict) -> Optional[dict]:
        if event.get("event") != "step_update":
            return None
        step = event.get("step_update") or {}
        if step.get("step_type") != "tool":
            return None

        key = str(step.get("step_index"))
        info = step.get("tool_info") or {}
        tool = str(step.get("tool_name") or info.get("name") or "tool")
        args = info.get("parameters") or {}

        if step.get("state") == "ACTIVE":
            known = self._open.get(key, {})
            self._open[key] = {
                "tool": tool or known.get("tool", ""),
                "args": args or known.get("args", {}),
                "started_at": known.get("started_at") or now_iso(),
                "clock": known.get("clock") or time.monotonic(),
            }
            return None

        if step.get("state") not in ("DONE", "ERROR"):
            return None

        opened = self._open.pop(key, {})
        args = args or opened.get("args", {})
        record = {
            "tool": tool or opened.get("tool") or "tool",
            "tool_call_id": key,
            "args": {k: _clip(v, ARG_VALUE_CHARS) if isinstance(v, str) else v
                     for k, v in args.items()},
            "ok": step.get("state") != "ERROR",
            "label": _label(tool, args),
        }
        output = info.get("output")
        if isinstance(output, str) and output:
            record["result_snippet"] = _clip(output, RESULT_SNIPPET_CHARS)
        record["ended_at"] = now_iso()
        if opened.get("clock"):
            record["duration_ms"] = int((time.monotonic() - opened["clock"]) * 1000)
        elif step.get("duration_seconds"):
            record["duration_ms"] = int(float(step["duration_seconds"]) * 1000)
        if opened.get("started_at"):
            record["started_at"] = opened["started_at"]
        return record


def _occupancy(usage: dict) -> int:
    """How full the window was for one model call."""
    return int(sum(usage.get(part) or 0 for part in
                   ("input_tokens", "output_tokens", "cache_read_tokens")))


def run(request: PiRequest, on_event: Optional[Callable[[dict], None]] = None,
        on_spawn: Optional[Callable[[int], None]] = None,
        on_exit: Optional[Callable[[int], None]] = None) -> PiResult:
    """Run one non-interactive agy turn. Contract-identical to agent_cc.run."""
    _provider, model_id = resolve_model(request.model)

    Path(request.session_dir).mkdir(parents=True, exist_ok=True)
    conv_file = _conversation_file(request)
    conversation = conv_file.read_text().strip() if conv_file.is_file() else None

    raw_path = Path(request.raw_output_path)
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    result = PiResult(session_id=request.session_id,
                      context_window=context_window(_provider, model_id))

    env = operator_env()
    for name in API_AUTH_VARS:
        env.pop(name, None)

    process = subprocess.Popen(build_command(request, conversation),
                               stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, bufsize=1, cwd=request.cwd, env=env)
    if on_spawn:
        on_spawn(process.pid)

    assigned: str | None = None
    error: str = ""

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

            name = event.get("event")
            if name == "init":
                assigned = (event.get("conversation_id")
                            or (event.get("init") or {}).get("conversation_id"))
            elif name == "step_update":
                # Per-step usage is the honest source for window occupancy: the
                # result event's usage is CUMULATIVE over the whole agentic loop,
                # and reading that as occupancy is the bug agent_cc had to fix.
                step = event.get("step_update") or {}
                occupancy = _occupancy(step.get("usage") or {})
                if occupancy:
                    result.context_tokens = occupancy
            elif name == "result":
                payload = event.get("result") or {}
                assigned = payload.get("conversation_id") or assigned
                if payload.get("response"):
                    result.text = str(payload["response"]).strip()
                if payload.get("status") != "SUCCESS":
                    error = str(payload.get("error") or payload.get("status") or "")
                usage = payload.get("usage") or {}
                total = int(usage.get("total_tokens") or 0)
                result.tokens += total
                # Mapped onto the pi shape so UsageBreakdown folds it the same
                # way. `cost` stays absent: agy reports no dollars, and a
                # fabricated figure is worse than a blank column.
                result.usage.add_turn({
                    "input": usage.get("input_tokens") or 0,
                    "output": usage.get("output_tokens") or 0,
                    "cacheRead": usage.get("cache_read_tokens") or 0,
                    "cacheWrite": 0,
                    "reasoning": usage.get("thinking_tokens") or 0,
                    "totalTokens": total,
                    "cost": {},
                }, total)

            if on_event:
                on_event(event)

    stderr = process.stderr.read() if process.stderr else ""
    result.returncode = process.wait()
    if on_exit:
        on_exit(process.pid)

    if assigned:
        conv_file.write_text(assigned)

    # agy exits 0 even when the result event reports ERROR — a timeout comes
    # back as a successful process with a failed payload. Without this the
    # factory would treat a stalled turn as a completed one.
    if error and not result.text:
        raise RuntimeError(f"agy reported {error!r} (exit {result.returncode})"
                           f"{': ' + stderr.strip()[-400:] if stderr.strip() else ''}")
    if result.returncode != 0 and not result.text:
        raise RuntimeError(f"agy exited {result.returncode}: {stderr.strip()[-800:]}")
    return result
