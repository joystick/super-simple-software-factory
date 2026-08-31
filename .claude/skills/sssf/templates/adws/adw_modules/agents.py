"""Config loading/validation and agent execution.

Every ADW validates its agents before running (fail fast, nothing spawns
against a half-valid config). Every agent call parses against a concrete
output type; parse failures and gate violations re-prompt the SAME session
with a correction — context intact, bounded retries. Agent proposes, code
disposes.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from . import agent_agy, agent_cc, agent_pi, permissions, prompts, skill_engineering
from .data_types import (AgentCall, AgentConfig, EnvelopeBase, EventRecord,
                         GateCheck, GateReport, Phase, PiRequest, SSSFConfig,
                         UsageBreakdown)
from .utils import new_id

JSON_FIX_ATTEMPTS = 2      # continue-with-correction attempts for malformed JSON

# The two coding agents behind a phase. Both expose the same surface —
# run(request, on_event, on_spawn, on_exit) -> PiResult, resolve_model(pattern),
# ToolCallTracker — so everything below picks a module and stops caring which.
INTERFACES = {"pi": agent_pi, "claude_code": agent_cc, "agy": agent_agy}


def interface(agent: AgentConfig):
    """The coding-agent module that runs this agent."""
    try:
        return INTERFACES[agent.coding_agent]
    except KeyError:
        raise SystemExit(f"agent {agent.name!r}: unknown coding_agent "
                         f"{agent.coding_agent!r} (expected one of "
                         f"{', '.join(INTERFACES)})") from None


class GateFailure(RuntimeError):
    pass


# ── config ───────────────────────────────────────────────────────────────────

def load_config(path: str = "adws/adw_sssf_config/sssf.config.yaml") -> SSSFConfig:
    raw = yaml.safe_load(Path(path).read_text()) or {}
    defaults = raw.get("defaults", {}) or {}
    for agent in raw.get("agents", []) or []:
        for key in ("coding_agent", "model", "thinking", "color", "tools", "writes",
                    "skill_token_budget"):
            if key in defaults:
                agent.setdefault(key, defaults[key])
        agent.setdefault("harness_engineering", defaults.get("harness_engineering", []))
        agent.setdefault("skill_engineering", defaults.get("skill_engineering", []))
    return SSSFConfig(**raw)


def ignored_field_warnings(agent: AgentConfig) -> list[str]:
    """Configured but silently-ignored-by-design fields, named — never
    fatal, and never silent either. `harness_engineering` only takes effect
    under `coding_agent: pi`; `skill_engineering` only takes effect under
    `coding_agent: claude_code`. The other coding agent's own field is a
    valid combination (a roster naming both, meant to be flipped between
    agents later, say) so this warns rather than fails validate() — but it
    warns, because a config field that does nothing with no signal is
    exactly the failure mode this repo has already been bitten by.
    """
    warnings = []
    if agent.coding_agent != "pi" and agent.harness_engineering:
        warnings.append(
            f"agent {agent.name!r}: harness_engineering is set but coding_agent is "
            f"{agent.coding_agent!r} — harness_engineering only takes effect under "
            f"coding_agent: pi and will be ignored")
    if agent.coding_agent != "claude_code" and agent.skill_engineering:
        warnings.append(
            f"agent {agent.name!r}: skill_engineering is set but coding_agent is "
            f"{agent.coding_agent!r} — skill_engineering only takes effect under "
            f"coding_agent: claude_code and will be ignored")
    return warnings


@dataclass
class VendoredSkillUsage:
    path: str
    agents: list[str] = field(default_factory=list)   # empty = vendored but unused


@dataclass
class SkillAudit:
    vendored: list[VendoredSkillUsage]
    # skill paths named by some agent that are NOT under the vendored dir —
    # hand-authored files, or a typo pointing outside it. path -> agent names.
    outside_vendor_dir: dict[str, list[str]]


def audit_skills(cfg: SSSFConfig,
                 skill_dir: str = "adws/adw_data/skill_engineering") -> SkillAudit:
    """"Which skills are vendored, and which agents use them" — the Phase 5
    audit, without reading YAML by hand. Every *.md under skill_dir is
    listed (used or not); every skill_engineering path NOT under skill_dir
    is reported separately, since that's a hand-authored file this audit
    has no opinion about, not a vendoring gap.
    """
    # Keyed by resolved path so "adws/x/tdd.md" and "./adws/x/tdd.md" match
    # the same file — a config author's harmless spelling choice must not
    # read as a typo pointing outside the vendored directory.
    usage: dict[Path, list[str]] = {}
    for agent in cfg.agents:
        for path in agent.skill_engineering:
            usage.setdefault(Path(path).resolve(), []).append(agent.name)

    dir_path = Path(skill_dir)
    vendored_paths = sorted(dir_path.glob("*.md")) if dir_path.is_dir() else []
    vendored = [VendoredSkillUsage(path=str(p), agents=usage.get(p.resolve(), []))
               for p in vendored_paths]

    vendored_resolved = {p.resolve() for p in vendored_paths}
    outside = {str(path): names for path, names in usage.items()
              if path not in vendored_resolved}
    return SkillAudit(vendored=vendored, outside_vendor_dir=outside)


def resolve(cfg: SSSFConfig, name: str) -> AgentConfig:
    for agent in cfg.agents:
        if agent.name == name:
            return agent
    raise SystemExit(f"agent {name!r} is not defined in the config — "
                     f"available: {[a.name for a in cfg.agents]}")


def validate(cfg: SSSFConfig, required: list[str]) -> None:
    """Fail fast: every required name must resolve to a usable agent."""
    problems = []
    for name in required:
        try:
            agent = resolve(cfg, name)
        except SystemExit as e:
            problems.append(str(e))
            continue
        if agent.coding_agent not in INTERFACES:
            problems.append(f"agent {name!r}: unknown coding_agent "
                            f"{agent.coding_agent!r} (expected one of "
                            f"{', '.join(INTERFACES)})")
            continue
        for label, ref in (("system", agent.prompt_engineering.system),
                           ("user", agent.prompt_engineering.user)):
            if not Path(ref).is_file():
                problems.append(f"agent {name!r}: {label} prompt not found: {ref}")
        try:
            interface(agent).resolve_model(agent.model)
        except ValueError as e:
            problems.append(f"agent {name!r}: {e}")
        # Fail before spawn on a missing/empty skill file — a typo in a
        # roster is a config error, not something discovered mid-run.
        try:
            skill_engineering.check(agent.skill_engineering)
        except skill_engineering.SkillFileError as e:
            problems.append(f"agent {name!r}: {e}")
        # Warn, never fail: the OTHER coding agent's field is a valid
        # roster (someone may flip agents between pi/claude_code later),
        # just one where this field currently does nothing. Printed here,
        # not through run.console, because validate() runs before any Run
        # or trace exists — there is nothing yet for this to drift from.
        for warning in ignored_field_warnings(agent):
            print(f"warning: {warning}", file=sys.stderr)
    if problems:
        raise SystemExit("config validation failed:\n- " + "\n- ".join(problems))


# ── execution ────────────────────────────────────────────────────────────────

def execute(run, phase: Phase, call: AgentCall) -> EnvelopeBase:
    """One agent call: render prompts -> pi run -> typed parse -> gates -> envelope."""
    agent = resolve(run.cfg, phase.params.owner)
    coder = interface(agent)
    agent_dir = run.session_dir / agent.name
    agent_dir.mkdir(parents=True, exist_ok=True)

    variables = {
        "prompt": call.prompt,
        "previous_envelope": call.previous.model_dump_json(indent=2) if call.previous else "(none)",
        "context_handoff_dir": str(run.context_handoff_dir),
    }
    system_text = prompts.render(agent.prompt_engineering.system, variables)
    system_text = skill_engineering.compose(system_text, agent.skill_engineering)
    skill_tokens_estimate = skill_engineering.estimate_tokens(agent.skill_engineering)
    user_text = prompts.render(agent.prompt_engineering.user, variables)
    prompts.save(agent_dir / "prompts", "system.md", system_text)
    prompts.save(agent_dir / "prompts", "user.md", user_text)

    session_id = _agent_session_id(run, agent)
    run.tracer.event(EventRecord(adw_id=run.adw_id, phase_id=phase.phase_id,
                                 type="agent_start", name=agent.name,
                                 payload={"model": agent.model, "thinking": agent.thinking,
                                          "color": agent.color,
                                          "session_id": session_id,
                                          "coding_agent": agent.coding_agent,
                                          "purpose": agent.purpose,
                                          "tools": agent.tools,  # None = all tools
                                          "harness_engineering": agent.harness_engineering,
                                          "skill_engineering": agent.skill_engineering,
                                          "skill_tokens_estimate": skill_tokens_estimate}))
    run.console.agent_started(agent.name, agent.model, session_id)
    run.console.skill_engineering_report(agent.skill_engineering, skill_tokens_estimate,
                                         agent.skill_token_budget)

    # Parse retries and gate corrections re-enter the SAME pi session, so the
    # last send is the one whose context occupancy is current — while spend is
    # the opposite: every send costs, so usage accumulates across all of them.
    latest: agent_pi.PiResult | None = None
    spent = UsageBreakdown()

    def send(prompt_text: str) -> agent_pi.PiResult:
        nonlocal latest
        request = PiRequest(
            prompt=prompt_text,
            system_prompt=system_text,
            model=agent.model,
            thinking=agent.thinking,
            session_id=session_id,
            # absolute: these are read by the coding-agent subprocess, which
            # runs in repo_root
            session_dir=str((agent_dir / f"{agent.coding_agent}_sessions").resolve()),
            raw_output_path=str((agent_dir / "raw_output.jsonl").resolve()),
            tools=agent.tools,
            extensions=agent.harness_engineering,
            cwd=str(run.repo_root),
        )
        result = coder.run(
            request,
            on_event=_event_forwarder(run, phase, agent, coder),
            on_spawn=lambda pid: run.tracer.process_start(
                run.adw_id, "agent", agent.name, pid,
                f"{agent.coding_agent} {agent.name} {agent.model}"),
            on_exit=lambda pid: run.tracer.process_end(run.adw_id, pid))
        run.add_usage(result.tokens, result.cost)
        spent.merge(result.usage)
        latest = result
        return result

    # What the tree looked like before this agent got its hands on it. Every
    # send in this phase — first prompt, JSON retries, gate corrections — is
    # measured against this one baseline.
    tree_before = permissions.snapshot(run)

    result = send(user_text)
    envelope, attempt = _parse_with_retries(run, phase, call, result, send)

    # claim gates — violations flow back into the SAME session as corrections
    for gate_attempt in range(1, max(1, phase.params.retries + 1) + 1):
        violations = []
        for gate in call.gates:
            report = _as_report(gate(envelope, run))
            found = report.violations
            run.tracer.gate_row(phase, gate.__name__, report, gate_attempt)
            run.tracer.event(EventRecord(
                adw_id=run.adw_id, phase_id=phase.phase_id,
                type="gate_fail" if found else "gate_pass", name=gate.__name__,
                payload={"attempt": gate_attempt, "violations": found,
                         "checks": [c.model_dump() for c in report.checks]}))
            run.console.gate_result(gate.__name__, report)
            violations.extend(found)
        if not violations:
            break
        if gate_attempt > phase.params.retries:
            raise GateFailure(f"{agent.name} failed gates after {gate_attempt} attempt(s):\n- "
                              + "\n- ".join(violations))
        phase.attempt = gate_attempt
        run.console.retry(agent.name, gate_attempt, phase.params.retries,
                          f"{len(violations)} gate violation(s)")
        correction = ("Your previous response failed validation:\n- "
                      + "\n- ".join(violations)
                      + "\n\nFix these problems, then re-emit ONLY your Report JSON.")
        result = send(correction)
        envelope, attempt = _parse_with_retries(run, phase, call, result, send)

    # Permission is checked after every send is done, and before the envelope is
    # accepted: an agent does not get to report success on a phase in which it
    # wrote somewhere it was not allowed to.
    try:
        touched = permissions.enforce(run, phase, agent, tree_before)
    except permissions.PermissionBreach as breach:
        run.tracer.event(EventRecord(adw_id=run.adw_id, phase_id=phase.phase_id,
                                     type="error", name="permission_breach",
                                     payload={"agent": agent.name, "error": str(breach),
                                              "writes": agent.writes,
                                              "protected_files": run.cfg.defaults.protected_files}))
        raise
    if touched:
        run.tracer.event(EventRecord(adw_id=run.adw_id, phase_id=phase.phase_id,
                                     type="log", name="paths_touched",
                                     payload={"agent": agent.name, "paths": touched}))

    _persist_envelope(run, phase, agent.name, call, envelope, attempt, valid=True)
    run.console.envelope_summary(envelope)
    context = latest or result
    run.tracer.agent_session_row(run.adw_id, agent, session_id,
                                 context_tokens=context.context_tokens,
                                 context_window=context.context_window,
                                 skill_tokens_estimate=skill_tokens_estimate)
    run.save_agent_map(agent.name, {"session_id": session_id, "model": agent.model,
                                    "coding_agent": agent.coding_agent})
    run.tracer.event(EventRecord(adw_id=run.adw_id, phase_id=phase.phase_id,
                                 type="handoff", name=agent.name,
                                 payload={"artifacts": envelope.artifacts,
                                          "summary": envelope.summary}))
    run.tracer.event(EventRecord(adw_id=run.adw_id, phase_id=phase.phase_id,
                                 type="agent_end", name=agent.name,
                                 # Phase totals, not the last send's: a retried
                                 # phase paid for every attempt.
                                 tokens=spent.total_tokens,
                                 payload={"cost": spent.total_cost,
                                          "usage": spent.model_dump(),
                                          "context_tokens": context.context_tokens,
                                          "context_window": context.context_window}))
    run.console.agent_finished(agent.name, spent.total_tokens, spent.total_cost)
    if envelope.status != "success":
        raise RuntimeError(f"{agent.name} reported status={envelope.status!r}: {envelope.summary}")
    return envelope


# ── internals ────────────────────────────────────────────────────────────────

def _as_report(result) -> GateReport:
    """Accept a GateReport, or a legacy gate that returned a violations list."""
    if isinstance(result, GateReport):
        return result
    return GateReport(checks=[GateCheck(item=str(v), ok=False) for v in (result or [])])


def _agent_session_id(run, agent: AgentConfig) -> str:
    entry = run.agent_map.get(agent.name)
    if entry and entry.get("model") == agent.model:
        return entry["session_id"]           # rejoin the existing context window
    return f"sssf-{run.adw_id}-{agent.name}-{new_id(4)}"


def _event_forwarder(run, phase: Phase, agent: AgentConfig, coder):
    """One tool_call event per real tool call, with its exact args and result.

    The tracker comes from whichever coding agent is running — pi's and Claude
    Code's tool streams are shaped differently, but both trackers emit the same
    normalized record, so nothing downstream changes."""
    agent_name = agent.name
    tracker = coder.ToolCallTracker()

    def forward(event: dict) -> None:
        record = tracker.observe(event)
        if record is None:
            return
        # The call's span rides the columns; duration_ms stays in the payload as
        # pi's own authoritative number.
        run.tracer.event(EventRecord(adw_id=run.adw_id, phase_id=phase.phase_id,
                                     type="tool_call", name=record.pop("label"),
                                     started_at=record.pop("started_at", None),
                                     ended_at=record.pop("ended_at", None),
                                     payload={**record, "agent": agent_name}))
    return forward


def _extract_json(text: str) -> dict:
    candidate = text
    if "```" in text:
        for block in text.split("```")[1::2]:
            block = block.removeprefix("json").strip()
            if block.startswith("{"):
                candidate = block
                break
    start, end = candidate.find("{"), candidate.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in the response")
    return json.loads(candidate[start:end + 1])


def _parse_with_retries(run, phase: Phase, call: AgentCall, result, send):
    """Parse the final response against the declared output type; on failure,
    continue the SAME session with a correction (bounded)."""
    for attempt in range(1, JSON_FIX_ATTEMPTS + 2):
        try:
            payload = _extract_json(result.text)
            return call.output_type.model_validate(payload), attempt
        except Exception as error:
            _persist_envelope(run, phase, phase.params.owner, call, None, attempt,
                              valid=False, raw=result.text)
            if attempt > JSON_FIX_ATTEMPTS:
                raise RuntimeError(
                    f"{phase.params.owner} never produced valid "
                    f"{call.output_type.__name__} JSON: {error}") from error
            run.console.retry(phase.params.owner, attempt, JSON_FIX_ATTEMPTS,
                              f"invalid {call.output_type.__name__} JSON: {error}")
            fields = ", ".join(call.output_type.model_fields.keys())
            result = send(
                f"Your response was not valid JSON for the required structure "
                f"({error}). Respond again with ONLY a JSON object with these "
                f"fields: {fields}. No prose, no code fences.")


def _persist_envelope(run, phase: Phase, agent_name: str, call: AgentCall,
                      envelope: Optional[EnvelopeBase], attempt: int,
                      valid: bool, raw: str = "") -> None:
    payload_json = envelope.model_dump_json(indent=2) if envelope else json.dumps({"raw": raw[-2000:]})
    run.tracer.envelope_row(phase, agent_name, call.output_type.__name__,
                            payload_json, valid, attempt)
    if envelope:
        record = {"agent_name": agent_name, "purpose": resolve(run.cfg, agent_name).purpose,
                  "output_type": call.output_type.__name__, "attempt": attempt,
                  **envelope.model_dump()}
        (run.session_dir / agent_name / "envelope.json").write_text(json.dumps(record, indent=2))
