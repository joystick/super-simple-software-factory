"""agents.py's skill_engineering seam: validate() and the AgentConfig schema.

Phase 1 scope: one agent, one skill (or none). No defaults merging yet — that
is Phase 2, tracked separately in the plan.
"""

from __future__ import annotations

from adw_modules import agents
from adw_modules.data_types import AgentConfig, PromptEngineering, SSSFConfig


def _config(**agent_overrides) -> SSSFConfig:
    # coding_agent="claude_code" deliberately: its resolve_model() is a pure
    # pattern check (see agent_cc.py) with no subprocess call, unlike "pi"'s
    # (which shells out to `pi --list-models`) — this seam's tests must not
    # depend on a real pi installation being present.
    agent = AgentConfig(
        name="builder",
        coding_agent="claude_code",
        model="anthropic/claude-sonnet-4",
        prompt_engineering=PromptEngineering(system="system.md", user="user.md"),
        **agent_overrides,
    )
    return SSSFConfig(agents=[agent])


def test_agent_config_defaults_to_no_skills():
    agent = AgentConfig(
        name="builder",
        prompt_engineering=PromptEngineering(system="system.md", user="user.md"),
    )
    assert agent.skill_engineering == []


def test_validate_fails_on_missing_skill_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "system.md").write_text("system")
    (tmp_path / "user.md").write_text("user")
    cfg = _config(skill_engineering=["adws/adw_data/skill_engineering/tdd.md"])

    try:
        agents.validate(cfg, ["builder"])
        assert False, "expected SystemExit"
    except SystemExit as e:
        assert "builder" in str(e)
        assert "adws/adw_data/skill_engineering/tdd.md" in str(e)


def test_validate_fails_on_empty_skill_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "system.md").write_text("system")
    (tmp_path / "user.md").write_text("user")
    skill_dir = tmp_path / "adws" / "adw_data" / "skill_engineering"
    skill_dir.mkdir(parents=True)
    (skill_dir / "tdd.md").write_text("")
    cfg = _config(skill_engineering=["adws/adw_data/skill_engineering/tdd.md"])

    try:
        agents.validate(cfg, ["builder"])
        assert False, "expected SystemExit"
    except SystemExit as e:
        assert "builder" in str(e)
        assert "tdd.md" in str(e)


def test_validate_passes_with_a_real_skill_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "system.md").write_text("system")
    (tmp_path / "user.md").write_text("user")
    skill_dir = tmp_path / "adws" / "adw_data" / "skill_engineering"
    skill_dir.mkdir(parents=True)
    (skill_dir / "tdd.md").write_text("# TDD\n\nRed, green, refactor.\n")
    cfg = _config(skill_engineering=["adws/adw_data/skill_engineering/tdd.md"])

    agents.validate(cfg, ["builder"])  # must not raise


def test_validate_passes_for_an_agent_with_no_skill_engineering(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "system.md").write_text("system")
    (tmp_path / "user.md").write_text("user")
    cfg = _config()

    agents.validate(cfg, ["builder"])  # must not raise — user story 24


def test_validate_warns_but_does_not_raise_for_a_non_claude_code_agent_with_skill_engineering(
        tmp_path, monkeypatch, capsys):
    # coding_agent="agy" deliberately, same reason as _config()'s own choice
    # of "claude_code" elsewhere in this file: resolve_model() must be pure
    # (no `pi --list-models` subprocess) for this test to be about the
    # warning, not about whether pi happens to be installed on this machine.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "system.md").write_text("system")
    (tmp_path / "user.md").write_text("user")
    skill_dir = tmp_path / "adws" / "adw_data" / "skill_engineering"
    skill_dir.mkdir(parents=True)
    (skill_dir / "tdd.md").write_text("# TDD\n\nRed, green, refactor.\n")
    cfg = SSSFConfig(agents=[AgentConfig(
        name="builder", coding_agent="agy", model="agy/gemini-3.7-flash-medium",
        prompt_engineering=PromptEngineering(system="system.md", user="user.md"),
        skill_engineering=["adws/adw_data/skill_engineering/tdd.md"])])

    agents.validate(cfg, ["builder"])  # must not raise
    captured = capsys.readouterr()
    assert "warning" in captured.err
    assert "skill_engineering" in captured.err
    assert "builder" in captured.err
