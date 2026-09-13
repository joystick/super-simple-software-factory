"""Catches the one failure class that's recurred five times across four
audit passes on this repo's Pocock-protocol integration: a fix in one
artifact (code, a template, a config file) leaves a stale or contradictory
claim in another, and nothing executes to notice. All three checks here are
pure text parsing — no agents, no network, free to run on every change.

Each assertion traces to a real, previously-shipped incident:
- Retired-name lint: the exact defect fixed by playbook v4.6/v4.8/v4.9/v4.14
  and the fourth-pass audit's N2/N3 findings (a rename landed in the
  template/vendored files but the playbook or config.md kept teaching the
  old names).
- Coding-agent parity: the fourth-pass audit's N1 finding (config.md
  claimed 3 coding agents; the code shipped 4; nothing caught the gap).
- Composed-skills parity: the class of defect R2's migration guarded
  against directly — the planner template's header names the skills it
  composes, and each named skill needs its own override bullet, or a
  future rename leaves an override for a skill nobody vendors anymore.
"""

from __future__ import annotations

import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
PLAYBOOK = SKILL_ROOT.parent.parent.parent / "docs" / "playbook-adopting-sssf.md"
CONFIG_MD = SKILL_ROOT / "references" / "config.md"
AGENTS_PY = SKILL_ROOT / "templates" / "adws" / "adw_modules" / "agents.py"
PLANNER_SYSTEM_MD = SKILL_ROOT / "templates" / "prompt_engineering" / "planner" / "system.md"

RETIRED_NAMES = ["write-a-prd", "prd-to-plan", "prd-to-issues", "to-prd", "to-issues"]

VERSION_HISTORY_HEADING = re.compile(r"^## Version history\s*$", re.MULTILINE)


def _text_above_version_history(path: Path) -> str:
    """The live, instructional part of a doc — everything before its
    Version History changelog, which is the one place retired names are
    allowed to appear (it's a historical record, not live instruction)."""
    text = path.read_text()
    match = VERSION_HISTORY_HEADING.search(text)
    return text[: match.start()] if match else text


def test_no_retired_skill_names_in_live_instructional_text():
    for path in (PLAYBOOK, CONFIG_MD):
        live_text = _text_above_version_history(path)
        for name in RETIRED_NAMES:
            assert name not in live_text, (
                f"{path.name} still names the retired skill {name!r} outside its "
                "Version History table. Either the rename is incomplete somewhere "
                "in the live system, or this reference needs to move into the "
                "changelog (history) or be removed (dead instruction).")


def _coding_agents_from_code() -> set[str]:
    """The authoritative list: skill_engineering_applies()'s own allowlist
    tuple in agents.py. This is the same function playbook/config.md both
    cite as the source of truth, so parsing it here (rather than the
    agent_*.py filenames, which don't string-match their coding_agent
    values 1:1 -- agent_cc.py implements "claude_code", not "cc") keeps
    this test anchored to the same ground truth the docs point readers at.
    """
    text = AGENTS_PY.read_text()
    match = re.search(
        r"def skill_engineering_applies.*?return agent\.coding_agent in \(([^)]+)\)",
        text, re.DOTALL)
    assert match, (
        "could not find skill_engineering_applies()'s return tuple in agents.py -- "
        "this test's parsing needs updating, the function may have moved or been "
        "rewritten")
    return {name.strip().strip('"').strip("'") for name in match.group(1).split(",")}


def test_coding_agent_parity_config_md():
    code_agents = _coding_agents_from_code()
    config_text = CONFIG_MD.read_text()
    for agent in code_agents:
        assert agent in config_text, (
            f"coding_agent {agent!r} is implemented in agents.py but never "
            f"mentioned in config.md — a new adopter configuring this agent "
            f"gets no documentation for it.")


def test_coding_agent_parity_playbook():
    code_agents = _coding_agents_from_code()
    playbook_text = _text_above_version_history(PLAYBOOK)
    for agent in code_agents:
        assert agent in playbook_text, (
            f"coding_agent {agent!r} is implemented in agents.py but never "
            f"mentioned in the playbook's live instructional text.")


def test_composed_skills_override_bullets_match_header():
    """The planner template's '## On the skills composed below (...)' header
    names every skill it's written against. Not every named skill needs its
    own override bullet below (a pure protocol with no "ask the user"
    behavior, like `tdd`, legitimately has nothing to override) — but every
    override bullet that DOES exist must name a skill still present in the
    header, or it's a leftover pointing at a skill the header no longer
    composes (the exact R2-class defect this whole effort has now caught
    three separate times: a rename lands in the header but a stale bullet
    for the retired name survives underneath it)."""
    text = PLANNER_SYSTEM_MD.read_text()
    header_match = re.search(
        r"^## On the skills composed below \(([^)]+)\)", text, re.MULTILINE)
    assert header_match, "planner system.md's composed-skills header not found"
    named_skills = {s.strip() for s in header_match.group(1).split(",")}

    # Only look inside the "On the skills composed below" section itself,
    # so a bullet in some unrelated part of the file (e.g. Subagents) isn't
    # mistaken for a per-skill override.
    section_match = re.search(
        r"^## On the skills composed below.*?(?=^## |\Z)", text,
        re.MULTILINE | re.DOTALL)
    section_text = section_match.group(0)
    bullet_skills = re.findall(r"^-\s+\*\*([^*]+)\*\*:", section_text, re.MULTILINE)
    assert bullet_skills, "no per-skill override bullets found in the composed-skills section"
    for skill in bullet_skills:
        assert skill in named_skills, (
            f"the composed-skills section has an override bullet for {skill!r}, "
            f"but the header no longer lists it among {sorted(named_skills)} — "
            "this is a stale override left behind by a rename.")
