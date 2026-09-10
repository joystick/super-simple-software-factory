"""agents.execute() must template `context_handoff_dir` as an absolute path.

Found live, 2026-09-10: a reviewer ran `cd searoute-rs && cargo test -p
searoute-rs` (unnecessary -- the workspace root already supports `-p`), and
Claude Code's Bash tool keeps a persistent shell across turns in one session,
so that `cd` stuck for the rest of the run. The reviewer's later `Write` to
its declared `<context_handoff_dir>/review.md` -- a RELATIVE path, because
`context_handoff_dir` was templated from `cfg.defaults.data_dir` ("adws/adw_data")
without resolving it -- landed one directory off, at
`searoute-rs/adws/adw_data/sessions/.../review.md`. The gate correctly failed
the run (declared artifact does not exist) but the fix is to make the
templated path itself immune to any cwd drift a tool call causes, not to rely
on agents never `cd`-ing.
"""

from __future__ import annotations

import subprocess

import pytest
from adw_modules import agent_agy, agent_cc, agent_opencode, agent_pi, agents
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


@pytest.fixture
def captured_request(monkeypatch):
    captured = {}

    def fake_run(request, on_event, on_spawn, on_exit):
        captured["request"] = request
        return PiResult(text='{"status": "success", "summary": "ok"}')

    for module in (agent_cc, agent_pi, agent_agy, agent_opencode):
        monkeypatch.setattr(module, "run", fake_run)
    return captured


def test_context_handoff_dir_is_templated_as_an_absolute_path(repo, captured_request):
    (repo / "system.md").write_text("Write your review to {{context_handoff_dir}}/review.md")
    (repo / "user.md").write_text("{{prompt}}")
    cfg = SSSFConfig(
        defaults=ConfigDefaults(),  # data_dir defaults to a relative "adws/adw_data"
        agents=[AgentConfig(
            name="reviewer", coding_agent="claude_code", model="anthropic/claude-opus-4-6",
            prompt_engineering=PromptEngineering(system="system.md", user="user.md"))],
    )
    tracer = Tracer(db_path=repo / "sssf.db", events_jsonl=repo / "events.jsonl")
    run = Run(cfg=cfg, adw_id="test-adw", tracer=tracer, engineer="test")
    phase = Phase(phase_id="test-adw_01_review", adw_id="test-adw", seq=1,
                 params=PhaseParams(name="review", kind="agent", owner="reviewer",
                                   description="test phase"),
                 status="running")

    agents.execute(run, phase, AgentCall(output_type=GenericOutput, prompt="review it"))

    system_prompt = captured_request["request"].system_prompt
    # Find the templated path the way an agent would see it, then confirm
    # it's absolute -- a relative one is exactly what broke live, since it
    # only survives a session where no tool call ever changes cwd.
    templated_dir = system_prompt.split("Write your review to ")[1].split("/review.md")[0]
    assert templated_dir.startswith("/"), (
        f"context_handoff_dir must be absolute, got {templated_dir!r} -- a "
        "relative path breaks the moment any Bash tool call in the session "
        "changes cwd (Claude Code's Bash tool is a persistent shell)")
