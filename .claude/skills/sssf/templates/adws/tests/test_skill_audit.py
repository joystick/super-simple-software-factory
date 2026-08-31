"""agents.audit_skills() — Phase 5: "which skills are vendored, and which
agents use them," without reading YAML by hand.
"""

from __future__ import annotations

from adw_modules.agents import audit_skills
from adw_modules.data_types import AgentConfig, PromptEngineering, SSSFConfig


def _agent(name: str, **overrides) -> AgentConfig:
    return AgentConfig(
        name=name, coding_agent="claude_code",
        prompt_engineering=PromptEngineering(system="s.md", user="u.md"),
        **overrides,
    )


def test_a_vendored_skill_used_by_one_agent(tmp_path):
    skill_dir = tmp_path / "skill_engineering"
    skill_dir.mkdir()
    (skill_dir / "tdd.md").write_text("# TDD")
    cfg = SSSFConfig(agents=[_agent("builder", skill_engineering=[str(skill_dir / "tdd.md")])])

    report = audit_skills(cfg, str(skill_dir))

    assert len(report.vendored) == 1
    assert report.vendored[0].path == str(skill_dir / "tdd.md")
    assert report.vendored[0].agents == ["builder"]


def test_a_vendored_skill_used_by_multiple_agents(tmp_path):
    skill_dir = tmp_path / "skill_engineering"
    skill_dir.mkdir()
    (skill_dir / "tdd.md").write_text("# TDD")
    path = str(skill_dir / "tdd.md")
    cfg = SSSFConfig(agents=[
        _agent("builder", skill_engineering=[path]),
        _agent("fixer", skill_engineering=[path]),
    ])

    report = audit_skills(cfg, str(skill_dir))

    assert len(report.vendored) == 1
    assert sorted(report.vendored[0].agents) == ["builder", "fixer"]


def test_a_vendored_skill_used_by_no_agent_is_reported_unused(tmp_path):
    skill_dir = tmp_path / "skill_engineering"
    skill_dir.mkdir()
    (skill_dir / "grill-me.md").write_text("# Grill me")
    cfg = SSSFConfig(agents=[_agent("builder")])   # doesn't use it

    report = audit_skills(cfg, str(skill_dir))

    assert len(report.vendored) == 1
    assert report.vendored[0].agents == []


def test_an_agent_naming_a_skill_outside_the_vendored_dir_is_reported_separately(tmp_path):
    skill_dir = tmp_path / "skill_engineering"
    skill_dir.mkdir()
    house_rule = tmp_path / "house.md"   # hand-authored, elsewhere
    house_rule.write_text("Every PR states the why.")
    cfg = SSSFConfig(agents=[_agent("builder", skill_engineering=[str(house_rule)])])

    report = audit_skills(cfg, str(skill_dir))

    assert report.vendored == []
    assert report.outside_vendor_dir == {str(house_rule): ["builder"]}


def test_an_equivalent_but_differently_written_path_is_still_matched(tmp_path):
    # A config author writing "./adws/.../tdd.md" instead of the exact string
    # Path.glob() returns must not be misclassified as "outside the vendor
    # dir" — that would read as a possible typo when it isn't one.
    skill_dir = tmp_path / "skill_engineering"
    skill_dir.mkdir()
    (skill_dir / "tdd.md").write_text("# TDD")
    differently_written = str(skill_dir) + "/./tdd.md"
    cfg = SSSFConfig(agents=[_agent("builder", skill_engineering=[differently_written])])

    report = audit_skills(cfg, str(skill_dir))

    assert len(report.vendored) == 1
    assert report.vendored[0].agents == ["builder"]
    assert report.outside_vendor_dir == {}


def test_no_vendored_skills_and_no_agent_usage_is_an_empty_report(tmp_path):
    skill_dir = tmp_path / "skill_engineering"   # never created — nothing vendored yet
    cfg = SSSFConfig(agents=[_agent("builder")])

    report = audit_skills(cfg, str(skill_dir))

    assert report.vendored == []
    assert report.outside_vendor_dir == {}
