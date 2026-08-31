"""tracer.agent_session_row() records skill_engineering — Phase 3, "a trace
from a run with skills can be read back and answers 'which protocols was
this agent given'." Real sqlite (tmp_path), not a mock — this IS the seam.
"""

from __future__ import annotations

import json

from adw_modules.data_types import AgentConfig, PromptEngineering
from adw_modules.tracer import Tracer


def _tracer(tmp_path) -> Tracer:
    return Tracer(db_path=tmp_path / "sssf.db", events_jsonl=tmp_path / "events.jsonl")


def _agent(**overrides) -> AgentConfig:
    return AgentConfig(
        name="builder",
        prompt_engineering=PromptEngineering(system="s.md", user="u.md"),
        **overrides,
    )


def test_agent_session_row_records_skill_engineering_and_its_token_estimate(tmp_path):
    tracer = _tracer(tmp_path)
    agent = _agent(skill_engineering=["adws/adw_data/skill_engineering/tdd.md"])

    tracer.agent_session_row("adw1", agent, "session-1", skill_tokens_estimate=1234)

    row = tracer.conn.execute(
        "SELECT skill_engineering_json, skill_tokens_estimate FROM agent_sessions"
        " WHERE adw_id=? AND agent=?", ("adw1", "builder")).fetchone()
    assert json.loads(row[0]) == ["adws/adw_data/skill_engineering/tdd.md"]
    assert row[1] == 1234


def test_agent_with_no_skills_records_an_empty_list_and_zero(tmp_path):
    tracer = _tracer(tmp_path)
    agent = _agent()   # skill_engineering defaults to []

    tracer.agent_session_row("adw1", agent, "session-1")

    row = tracer.conn.execute(
        "SELECT skill_engineering_json, skill_tokens_estimate FROM agent_sessions"
        " WHERE adw_id=? AND agent=?", ("adw1", "builder")).fetchone()
    assert json.loads(row[0]) == []
    assert row[1] == 0


def test_a_second_call_for_the_same_agent_overwrites_not_appends(tmp_path):
    # Matches the existing behaviour for model/session_id/context_tokens —
    # one row per (adw_id, agent), latest wins.
    tracer = _tracer(tmp_path)
    first_agent = _agent(skill_engineering=["adws/adw_data/skill_engineering/tdd.md"])
    tracer.agent_session_row("adw1", first_agent, "session-1", skill_tokens_estimate=100)

    second_agent = _agent(skill_engineering=["adws/adw_data/skill_engineering/grill-me.md"])
    tracer.agent_session_row("adw1", second_agent, "session-2", skill_tokens_estimate=200)

    rows = tracer.conn.execute(
        "SELECT skill_engineering_json, skill_tokens_estimate FROM agent_sessions"
        " WHERE adw_id=? AND agent=?", ("adw1", "builder")).fetchall()
    assert len(rows) == 1
    assert json.loads(rows[0][0]) == ["adws/adw_data/skill_engineering/grill-me.md"]
    assert rows[0][1] == 200


def test_an_explicit_skill_engineering_override_is_recorded_instead_of_the_configs(tmp_path):
    # Found by adversarial review: agent_session_row previously always
    # derived skill_engineering_json from agent.skill_engineering directly,
    # even for a pi/agy agent where agents.execute() (correctly, after the
    # same review) never actually composed or applied those skills. That
    # meant the trace recorded skill paths as "given to this agent" when
    # they were configured but explicitly NOT applied — the same
    # field-configured-but-not-applied problem this whole phase exists to
    # eliminate, just showing up one layer down in the trace.
    tracer = _tracer(tmp_path)
    agent = _agent(coding_agent="pi",
                   skill_engineering=["adws/adw_data/skill_engineering/tdd.md"])

    tracer.agent_session_row("adw1", agent, "session-1", skill_engineering=[])

    row = tracer.conn.execute(
        "SELECT skill_engineering_json FROM agent_sessions"
        " WHERE adw_id=? AND agent=?", ("adw1", "builder")).fetchone()
    assert json.loads(row[0]) == []


def test_omitting_the_override_still_defaults_to_the_agents_own_list(tmp_path):
    # Backward compatible: existing callers that don't pass the new param
    # keep the old behaviour (record agent.skill_engineering as-is).
    tracer = _tracer(tmp_path)
    agent = _agent(skill_engineering=["adws/adw_data/skill_engineering/tdd.md"])

    tracer.agent_session_row("adw1", agent, "session-1")

    row = tracer.conn.execute(
        "SELECT skill_engineering_json FROM agent_sessions"
        " WHERE adw_id=? AND agent=?", ("adw1", "builder")).fetchone()
    assert json.loads(row[0]) == ["adws/adw_data/skill_engineering/tdd.md"]
