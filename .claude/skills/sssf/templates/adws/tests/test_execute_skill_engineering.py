"""agents.execute() end to end: does the REQUEST a coding-agent module
actually receives carry the composed skill, or not, per coding_agent?

This is the seam a prior adversarial review found broken: every earlier
test exercised skill_engineering.compose() directly (a pure function) or
agents.validate()'s warning text, but nothing crossed the agents.execute()
boundary where the real bug lived — compose() was called unconditionally
regardless of coding_agent, so a pi/agy agent had skills injected and
billed while ignored_field_warnings() told the operator they were not.
This test spawns nothing real (the coding-agent module's run() is
monkeypatched to a fake that just captures the request), but it goes
through the REAL execute(), the REAL Run, and the REAL skill_engineering
module — the only thing faked is the subprocess boundary itself.
"""

from __future__ import annotations

import json
import subprocess

import pytest
from adw_modules import agent_agy, agent_cc, agent_pi, agents
from adw_modules.data_types import (AgentCall, AgentConfig, ConfigDefaults,
                                    GenericOutput, Phase, PhaseParams,
                                    PiResult, PromptEngineering, SSSFConfig)
from adw_modules.runner import Run
from adw_modules.tracer import Tracer


@pytest.fixture
def repo(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _run(cfg: SSSFConfig, tmp_path) -> Run:
    tracer = Tracer(db_path=tmp_path / "sssf.db", events_jsonl=tmp_path / "events.jsonl")
    return Run(cfg=cfg, adw_id="test-adw", tracer=tracer, engineer="test")


def _phase() -> Phase:
    return Phase(phase_id="test-adw_01_build", adw_id="test-adw", seq=1,
                params=PhaseParams(name="build", kind="agent", owner="builder",
                                  description="test phase"),
                status="running")


def _call() -> AgentCall:
    return AgentCall(output_type=GenericOutput, prompt="do the thing")


@pytest.fixture
def captured_request(monkeypatch):
    """Patch every coding-agent module's run() to capture the PiRequest it
    was actually given, and return a minimal successful PiResult — no
    subprocess, no cost, no network."""
    captured = {}

    def fake_run(request, on_event, on_spawn, on_exit):
        captured["request"] = request
        return PiResult(text='{"status": "success", "summary": "ok"}')

    for module in (agent_cc, agent_pi, agent_agy):
        monkeypatch.setattr(module, "run", fake_run)
    return captured


def _skill_dir(tmp_path) -> None:
    (tmp_path / "system.md").write_text("You are the builder.")
    (tmp_path / "user.md").write_text("{{prompt}}")
    skill_dir = tmp_path / "adws" / "adw_data" / "skill_engineering"
    skill_dir.mkdir(parents=True)
    (skill_dir / "tdd.md").write_text("# TDD\n\nRed, green, refactor.\n")


@pytest.mark.parametrize("coding_agent,model", [
    ("claude_code", "anthropic/claude-sonnet-4"),
    ("pi", "google/gemini-3.6-flash"),
    ("agy", "agy/gemini-3.7-flash-medium"),
])
def test_skill_engineering_applies_or_not_per_coding_agent(
        repo, captured_request, coding_agent, model):
    _skill_dir(repo)
    cfg = SSSFConfig(
        defaults=ConfigDefaults(),
        agents=[AgentConfig(
            name="builder", coding_agent=coding_agent, model=model,
            prompt_engineering=PromptEngineering(system="system.md", user="user.md"),
            skill_engineering=["adws/adw_data/skill_engineering/tdd.md"])],
    )
    run = _run(cfg, repo)

    agents.execute(run, _phase(), _call())

    system_prompt = captured_request["request"].system_prompt
    contains_skill = "Red, green, refactor." in system_prompt
    if coding_agent == "claude_code":
        assert contains_skill, "claude_code must receive the composed skill text"
    else:
        assert not contains_skill, (
            f"{coding_agent} must NOT receive skill text — skill_engineering "
            "only applies under claude_code, and this is exactly the bug an "
            "adversarial review found: it was being injected anyway")

    # The trace must agree with the actual request, not just echo the
    # config — a second review pass found agent_session_row recording
    # agent.skill_engineering unconditionally, so a pi/agy agent's row
    # claimed a skill was "given" even when execute() correctly never
    # applied it.
    row = run.tracer.conn.execute(
        "SELECT skill_engineering_json FROM agent_sessions WHERE adw_id=? AND agent=?",
        (run.adw_id, "builder")).fetchone()
    recorded_skills = json.loads(row[0])
    if coding_agent == "claude_code":
        assert recorded_skills == ["adws/adw_data/skill_engineering/tdd.md"]
    else:
        assert recorded_skills == [], (
            f"{coding_agent}'s trace row must not claim tdd.md was given when "
            "it was never applied")
