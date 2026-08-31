"""load_config()'s skill_engineering merge rule — Phase 2.

Mirrors the existing merge behaviour for harness_engineering/tools/etc:
a per-agent list REPLACES the default, never appends; an agent that omits
the key entirely inherits defaults.skill_engineering; absent everywhere
means no skills.
"""

from __future__ import annotations

import textwrap

from adw_modules import agents


def _write_config(tmp_path, body: str):
    path = tmp_path / "sssf.config.yaml"
    path.write_text(textwrap.dedent(body))
    return path


def test_agent_with_no_skill_engineering_inherits_the_default(tmp_path):
    cfg = agents.load_config(str(_write_config(tmp_path, """\
        defaults:
          skill_engineering:
            - adws/adw_data/skill_engineering/tdd.md
        agents:
          - name: builder
            prompt_engineering:
              system: system.md
              user: user.md
        """)))
    assert cfg.agents[0].skill_engineering == ["adws/adw_data/skill_engineering/tdd.md"]


def test_agent_with_its_own_skill_engineering_replaces_the_default_not_appends(tmp_path):
    cfg = agents.load_config(str(_write_config(tmp_path, """\
        defaults:
          skill_engineering:
            - adws/adw_data/skill_engineering/tdd.md
        agents:
          - name: reviewer
            skill_engineering:
              - adws/adw_data/skill_engineering/codebase-design.md
            prompt_engineering:
              system: system.md
              user: user.md
        """)))
    assert cfg.agents[0].skill_engineering == ["adws/adw_data/skill_engineering/codebase-design.md"]


def test_agent_with_explicit_empty_list_gets_no_skills_even_with_a_default(tmp_path):
    cfg = agents.load_config(str(_write_config(tmp_path, """\
        defaults:
          skill_engineering:
            - adws/adw_data/skill_engineering/tdd.md
        agents:
          - name: scout
            skill_engineering: []
            prompt_engineering:
              system: system.md
              user: user.md
        """)))
    assert cfg.agents[0].skill_engineering == []


def test_absent_everywhere_means_no_skills(tmp_path):
    cfg = agents.load_config(str(_write_config(tmp_path, """\
        agents:
          - name: builder
            prompt_engineering:
              system: system.md
              user: user.md
        """)))
    assert cfg.agents[0].skill_engineering == []


# ── skill_token_budget — per-agent overridable, same merge rule as
#    skill_engineering itself: an agent naming more/fewer skills than the
#    roster norm needs a budget that tracks ITS list. ─────────────────────

def test_agent_with_no_skill_token_budget_inherits_the_default(tmp_path):
    cfg = agents.load_config(str(_write_config(tmp_path, """\
        defaults:
          skill_token_budget: 2000
        agents:
          - name: builder
            prompt_engineering:
              system: system.md
              user: user.md
        """)))
    assert cfg.agents[0].skill_token_budget == 2000


def test_agent_with_its_own_skill_token_budget_overrides_the_default(tmp_path):
    cfg = agents.load_config(str(_write_config(tmp_path, """\
        defaults:
          skill_token_budget: 2000
        agents:
          - name: reviewer
            skill_token_budget: 8000
            prompt_engineering:
              system: system.md
              user: user.md
        """)))
    assert cfg.agents[0].skill_token_budget == 8000


def test_absent_everywhere_means_no_budget(tmp_path):
    cfg = agents.load_config(str(_write_config(tmp_path, """\
        agents:
          - name: builder
            prompt_engineering:
              system: system.md
              user: user.md
        """)))
    assert cfg.agents[0].skill_token_budget is None
