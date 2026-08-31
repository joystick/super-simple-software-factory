"""agents.skill_engineering_applies() — the single source of truth for
whether skill_engineering takes effect for a given agent.

This exists because of a real bug found by an adversarial review: Phase 1-5
shipped ignored_field_warnings() correctly SAYING skill_engineering is
ignored under pi/agy, while agents.execute() unconditionally called
compose() regardless of coding_agent — so pi and agy agents actually HAD
skills injected and billed, contradicting the tool's own warning. The two
call sites (the warning, and whether to compose) must derive from one
function, or they can silently diverge again exactly like this.
"""

from __future__ import annotations

from adw_modules.agents import skill_engineering_applies
from adw_modules.data_types import AgentConfig, PromptEngineering


def _agent(coding_agent: str) -> AgentConfig:
    return AgentConfig(
        name="builder", coding_agent=coding_agent,
        prompt_engineering=PromptEngineering(system="s.md", user="u.md"),
    )


def test_applies_under_claude_code():
    assert skill_engineering_applies(_agent("claude_code")) is True


def test_does_not_apply_under_pi():
    assert skill_engineering_applies(_agent("pi")) is False


def test_does_not_apply_under_agy():
    assert skill_engineering_applies(_agent("agy")) is False
