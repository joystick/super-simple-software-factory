"""agents.skill_engineering_applies() — the single source of truth for
whether skill_engineering takes effect for a given agent.

This exists because of a real bug found by an adversarial review: Phase 1-5
shipped ignored_field_warnings() correctly SAYING skill_engineering is
ignored under pi/agy, while agents.execute() unconditionally called
compose() regardless of coding_agent — so pi and agy agents actually HAD
skills injected and billed, contradicting the tool's own warning. The two
call sites (the warning, and whether to compose) must derive from one
function, or they can silently diverge again exactly like this.

The function was originally hardcoded to `claude_code` only, on the belief
that `--system-prompt` (the delivery channel) was claude_code-specific.
Checked live and that belief was wrong: `pi` has always had the identical
`--system-prompt` flag as `claude_code` (agent_pi.py / agent_cc.py), and
agy/opencode fold the composed system text into the user turn via their own
_compose() — a different but working channel. All four coding agents were
confirmed to actually receive the composed skill text, so all four apply.
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


def test_applies_under_pi():
    assert skill_engineering_applies(_agent("pi")) is True


def test_applies_under_agy():
    assert skill_engineering_applies(_agent("agy")) is True


def test_applies_under_opencode():
    assert skill_engineering_applies(_agent("opencode")) is True
