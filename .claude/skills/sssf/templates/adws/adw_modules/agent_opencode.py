"""`opencode` interface — a fourth coding agent for the factory.

Same contract as `agent_pi.run` / `agent_cc.run` / `agent_agy.run`: `PiRequest`
in, `PiResult` out, the same on_event / on_spawn / on_exit callbacks, the same
JSONL raw stream on disk. `agents.execute()` picks a module and stops caring
which.

`opencode` is a gateway like `agy` — one CLI in front of many providers
(`opencode models` lists ~427 across OpenRouter, Anthropic, its own "opencode"
gateway, and more) — but unlike `agy`'s bare model ids, its models are already
`provider/model-id` shaped (e.g. `openrouter/nvidia/nemotron-3-super-120b-a12b:free`).
So a roster entry's `model:` is `opencode/<that whole string>` — the `opencode/`
prefix is this module's own namespacing (same reason `agy/<id>` exists), and
everything after the first `/` is passed to `opencode run --model` verbatim.

THINGS THAT SHAPE THIS FILE, FOUND BY ACTUALLY RUNNING IT
-----------------------------------------------------------

1. **No `--system-prompt` flag, same as agy.** The system prompt is folded
   into the user turn behind a labelled delimiter — see `_compose`, reused
   verbatim from `agent_agy`.

2. **`--format json` gives ONE complete event per part, not deltas.** Each
   line is a whole JSON object with a `type` (`step_start`, `tool_use`,
   `text`, `step_finish`, ...) and a `sessionID` present on every event.
   `tool_use` events already carry `state.status: "completed"` with both
   `input` and `output` together — no ACTIVE/DONE pairing to track, unlike
   `agy`'s two-phase `step_update` stream. Confirmed via a live test call,
   not the docs (opencode's CLI docs don't cover this shape).

3. **Session ids are ASSIGNED, not minted — same as agy.** `opencode run`
   creates a `ses_...` id on its own; continuing means passing `--session
   <that id>` on the next call. So the id is captured from the first
   response and stored, same `_conversation_file`-shaped pattern as agy.

4. **No `--tools` allowlist flag.** Unlike `pi --tools` or an explicit
   per-agent tool restriction, opencode exposes its own fixed built-in
   toolset on every call — the roster's `tools:` field has nothing to bind
   to here. This is not a security gap: `permissions.py`'s post-hoc
   `writes:`/`protected_files` tree-diff enforcement still applies
   regardless of what tool surface an agent had, the same way it backstops
   every other coding agent. But `tools:` in a roster entry with
   `coding_agent: opencode` is currently decorative — flagged here so it
   doesn't read as broken enforcement.

5. **`--auto` is required for headless runs**, same reasoning as agy's
   `--dangerously-skip-permissions`: a headless run cannot answer a
   permission prompt; it would hang until timeout.

6. **Real cost data**, unlike agy. Each `step_finish` event carries a numeric
   `cost` (0.0 for a free-tier model, a real dollar figure otherwise) — this
   module sums it across steps rather than leaving `PiResult.cost` at 0.0.

NO CONTEXT-WINDOW FIGURE from the CLI. Same posture as agy: published
ceilings per model family, wrong-but-close beats a bar that reads 0.
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
from .utils import operator_env

OPENCODE_PATH = os.environ.get("OPENCODE_PATH", "opencode")

RESULT_SNIPPET_CHARS = 20_000
ARG_VALUE_CHARS = 20_000

# Published ceilings per model family prefix (matched against the part of
# model_id after the provider, e.g. "nvidia/nemotron-3-super..."). Same
# rationale as agent_agy.CONTEXT_WINDOWS: opencode exposes no per-call figure.
CONTEXT_WINDOWS = {
    "nvidia/nemotron-3-super": 262_144,
    "nvidia/nemotron-3-nano": 256_000,
    "nvidia/nemotron-nano": 128_000,
    "nvidia/llama-3.1-nemotron": 131_072,
    "nvidia/llama-3.3-nemotron": 131_072,
    "google/gemini": 1_000_000,
    "anthropic/claude": 200_000,
    "openai/gpt": 128_000,
}
DEFAULT_CONTEXT_WINDOW = 128_000

# Long timeout: a build phase legitimately runs for minutes.
PRINT_TIMEOUT_S = int(os.environ.get("OPENCODE_TIMEOUT_S", "900"))


@lru_cache(maxsize=1)
def _catalog() -> list[str]:
    """Every `provider/model-id` `opencode models` reports, ~427 entries.
    Same role agy's `_catalog()`/pi's `--list-models` play."""
    try:
        result = subprocess.run([OPENCODE_PATH, "models"], capture_output=True,
                                text=True, timeout=60, env=operator_env(),
                                check=False)
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def resolve_model(pattern: str) -> tuple[str, str]:
    """Resolve `opencode/<provider>/<model-id>` against the live catalog.

    Validating here means a typo fails at `agents.validate()` — before
    anything spawns — rather than partway through a run.
    """
    if "/" not in pattern:
        raise ValueError(
            f"model pattern {pattern!r} is not provider-qualified — write it as "
            "opencode/<provider>/<model-id>, e.g. "
            "opencode/openrouter/nvidia/nemotron-3-super-120b-a12b:free")
    provider, model_id = pattern.split("/", 1)
    if provider != "opencode":
        raise ValueError(
            f"model pattern {pattern!r} names provider {provider!r}, but "
            "coding_agent 'opencode' only runs models from `opencode models` — "
            "use opencode/<provider>/<model-id>, or switch the agent to "
            "another coding_agent")
    catalog = _catalog()
    if catalog and model_id not in catalog:
        raise ValueError(
            f"model {model_id!r} is not in `opencode models` — check "
            "`opencode models <provider>` for the real current id")
    return provider, model_id


def context_window(_provider: str, model_id: str) -> int:
    for prefix, window in CONTEXT_WINDOWS.items():
        if model_id.startswith(prefix):
            return window
    return DEFAULT_CONTEXT_WINDOW


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _compose(system_prompt: str, prompt: str) -> str:
    """Fold the system prompt into the user turn, because opencode has no
    other channel. Same shape as agent_agy._compose — same real weakness:
    advice inside the conversation, not a separate channel, resent every turn.
    """
    if not system_prompt.strip():
        return prompt
    return (
        "=== STANDING INSTRUCTIONS (apply to every turn of this conversation) ===\n"
        f"{system_prompt.strip()}\n"
        "=== END STANDING INSTRUCTIONS ===\n\n"
        f"{prompt}"
    )


def _session_file(request: PiRequest) -> Path:
    """Where the assigned session id is remembered between turns — opencode
    assigns one, so it's captured from the first result and stored, same
    reasoning as agent_agy._conversation_file."""
    return Path(request.session_dir) / f"{request.session_id}.opencode_session"


def build_command(request: PiRequest, session: str | None) -> list[str]:
    """The exact invocation. Split out so it can be asserted without spending."""
    _provider, model_id = resolve_model(request.model)
    cmd = [
        OPENCODE_PATH, "run",
        "--model", model_id,
        "--format", "json",
        "--dir", str(Path(request.cwd).resolve()),
        # A headless run cannot answer a permission prompt; it would hang
        # until the timeout. The roster's `writes` and permissions.py are
        # the real boundary, exactly as with the other interfaces.
        "--auto",
    ]
    if session:
        cmd += ["--session", session]
    cmd.append(_compose(request.system_prompt, request.prompt))
    return cmd


class ToolCallTracker:
    """One record per `tool_use` event.

    Unlike agy's ACTIVE/DONE pairing, opencode emits a single event per
    completed tool call — `state.status == "completed"` with both `input`
    and `output` already attached — so there's nothing to open and close.
    """

    def observe(self, event: dict) -> Optional[dict]:
        if event.get("type") != "tool_use":
            return None
        part = event.get("part") or {}
        if (part.get("state") or {}).get("status") != "completed":
            return None

        tool = str(part.get("tool") or "tool")
        state = part.get("state") or {}
        args = state.get("input") or {}
        output = state.get("output")
        timing = state.get("time") or {}

        record = {
            "tool": tool,
            "tool_call_id": str(part.get("callID") or ""),
            "args": {k: _clip(v, ARG_VALUE_CHARS) if isinstance(v, str) else v
                     for k, v in args.items()},
            "ok": True,
            "label": tool,
        }
        if isinstance(output, str) and output:
            record["result_snippet"] = _clip(output, RESULT_SNIPPET_CHARS)
        start = timing.get("start")
        end = timing.get("end")
        if start:
            record["started_at"] = str(start)
        if start and end:
            record["duration_ms"] = int(end) - int(start)
        return record


def run(request: PiRequest, on_event: Optional[Callable[[dict], None]] = None,
        on_spawn: Optional[Callable[[int], None]] = None,
        on_exit: Optional[Callable[[int], None]] = None) -> PiResult:
    """Run one non-interactive opencode turn. Contract-identical to agent_cc.run."""
    provider, model_id = resolve_model(request.model)

    Path(request.session_dir).mkdir(parents=True, exist_ok=True)
    sess_file = _session_file(request)
    session = sess_file.read_text().strip() if sess_file.is_file() else None

    raw_path = Path(request.raw_output_path)
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    result = PiResult(session_id=request.session_id,
                      context_window=context_window(provider, model_id))

    process = subprocess.Popen(build_command(request, session),
                               stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, bufsize=1, cwd=request.cwd,
                               env=operator_env())
    if on_spawn:
        on_spawn(process.pid)

    assigned: str | None = None
    text_parts: list[str] = []
    total_cost = 0.0

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

            assigned = event.get("sessionID") or assigned
            etype = event.get("type")
            part = event.get("part") or {}

            if etype == "text":
                t = part.get("text")
                if isinstance(t, str) and t:
                    text_parts.append(t)
            elif etype == "step_finish":
                tokens = part.get("tokens") or {}
                total = int(tokens.get("total") or 0)
                result.tokens += total
                total_cost += float(part.get("cost") or 0.0)
                cache = tokens.get("cache") or {}
                result.usage.add_turn({
                    "input": tokens.get("input") or 0,
                    "output": tokens.get("output") or 0,
                    "cacheRead": cache.get("read") or 0,
                    "cacheWrite": cache.get("write") or 0,
                    "reasoning": tokens.get("reasoning") or 0,
                    "totalTokens": total,
                    "cost": {"total": part.get("cost") or 0.0},
                }, total)
                occupancy = int(sum(tokens.get(k) or 0 for k in
                                    ("input", "output")) + (cache.get("read") or 0))
                if occupancy:
                    result.context_tokens = occupancy

            if on_event:
                on_event(event)

    stderr = process.stderr.read() if process.stderr else ""
    result.returncode = process.wait()
    if on_exit:
        on_exit(process.pid)

    if assigned:
        sess_file.write_text(assigned)
    result.text = "\n".join(text_parts).strip()
    result.cost = total_cost

    if result.returncode != 0 and not result.text:
        raise RuntimeError(f"opencode exited {result.returncode}: "
                           f"{stderr.strip()[-800:]}")
    return result
