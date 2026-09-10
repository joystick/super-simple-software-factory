"""agents.ignored_field_warnings() — Phase 5.

skill_engineering takes effect under any coding_agent covered by
skill_engineering_applies() (currently all four known coding agents);
harness_engineering only takes effect under coding_agent: pi. Naming the
other agent's field is not an error (the config is still usable), but it's
exactly the kind of silently-ignored setting this repo has been bitten by
before — so it warns, in a pure function validate() can call and print,
never failing the run.
"""

from __future__ import annotations

from adw_modules.agents import ignored_field_warnings
from adw_modules.data_types import AgentConfig, PromptEngineering


def _agent(**overrides) -> AgentConfig:
    return AgentConfig(
        name="builder",
        prompt_engineering=PromptEngineering(system="s.md", user="u.md"),
        **overrides,
    )


def test_pi_agent_with_harness_engineering_and_skill_engineering_warns_about_neither():
    # Both fields are honoured under pi now: harness_engineering always has
    # been, and skill_engineering_applies() covers pi too.
    agent = _agent(coding_agent="pi",
                   harness_engineering=["adws/adw_data/harness_engineering/subagents.ts"],
                   skill_engineering=["adws/adw_data/skill_engineering/tdd.md"])
    assert ignored_field_warnings(agent) == []


def test_claude_code_agent_with_harness_engineering_warns():
    agent = _agent(coding_agent="claude_code",
                   harness_engineering=["adws/adw_data/harness_engineering/subagents.ts"])
    warnings = ignored_field_warnings(agent)
    assert len(warnings) == 1
    assert "builder" in warnings[0]
    assert "harness_engineering" in warnings[0]
    assert "claude_code" in warnings[0]


def test_agy_agent_with_skill_engineering_does_not_warn():
    # skill_engineering_applies() covers agy — this is now the normal case,
    # not a silently-ignored one.
    agent = _agent(coding_agent="agy", skill_engineering=["adws/adw_data/skill_engineering/tdd.md"])
    assert ignored_field_warnings(agent) == []


def test_pi_agent_with_harness_engineering_does_not_warn():
    # harness_engineering IS honoured under pi — this is the normal case.
    agent = _agent(coding_agent="pi",
                   harness_engineering=["adws/adw_data/harness_engineering/subagents.ts"])
    assert ignored_field_warnings(agent) == []


def test_claude_code_agent_with_skill_engineering_does_not_warn():
    # skill_engineering IS honoured under claude_code — the normal case.
    agent = _agent(coding_agent="claude_code",
                   skill_engineering=["adws/adw_data/skill_engineering/tdd.md"])
    assert ignored_field_warnings(agent) == []


def test_agent_with_neither_field_set_warns_about_nothing():
    agent = _agent(coding_agent="pi")
    assert ignored_field_warnings(agent) == []


def test_claude_code_agent_with_harness_engineering_and_skill_engineering_warns_about_only_the_relevant_one():
    agent = _agent(coding_agent="claude_code",
                   harness_engineering=["adws/adw_data/harness_engineering/subagents.ts"],
                   skill_engineering=["adws/adw_data/skill_engineering/tdd.md"])
    warnings = ignored_field_warnings(agent)
    assert len(warnings) == 1  # not two — skill_engineering is fine under claude_code
    assert "harness_engineering" in warnings[0]
