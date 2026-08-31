"""skill_engineering.compose() — pure function, no subprocess, no network.

Phase 1 (tracer bullet) scope only: one skill or none, on the composition
function itself. Defaults merging, multiple skills, ordering across several
skills, and vendoring are later phases (see plans/2026-08-31... — Phase 2+).
"""

from __future__ import annotations

import pytest
from adw_modules import skill_engineering


def test_no_skills_returns_system_text_unchanged():
    # Phase 1 acceptance criterion / user story 24: an agent with no
    # skill_engineering key composes a byte-identical prompt to today.
    system_text = "You are the builder. Implement the plan exactly."
    assert skill_engineering.compose(system_text, []) == system_text


def test_one_skill_is_appended_after_the_system_prompt(tmp_path):
    skill_file = tmp_path / "tdd.md"
    skill_file.write_text("# TDD\n\nRed, green, refactor.\n")

    system_text = "You are the builder."
    composed = skill_engineering.compose(system_text, [str(skill_file)])

    assert composed.startswith(system_text)
    assert "Red, green, refactor." in composed
    # the skill's own name is named in the composed text, so a human reading
    # the persisted prompt can tell where one protocol starts
    assert "tdd" in composed.split(system_text, 1)[1]


def test_composition_is_deterministic(tmp_path):
    skill_file = tmp_path / "tdd.md"
    skill_file.write_text("# TDD\n\nRed, green, refactor.\n")

    system_text = "You are the builder."
    first = skill_engineering.compose(system_text, [str(skill_file)])
    second = skill_engineering.compose(system_text, [str(skill_file)])
    assert first == second


def test_missing_skill_file_raises_with_path(tmp_path):
    missing = tmp_path / "does-not-exist.md"
    with pytest.raises(skill_engineering.SkillFileError) as excinfo:
        skill_engineering.compose("system text", [str(missing)])
    assert str(missing) in str(excinfo.value)


def test_empty_skill_file_raises_with_path(tmp_path):
    empty = tmp_path / "empty.md"
    empty.write_text("")
    with pytest.raises(skill_engineering.SkillFileError) as excinfo:
        skill_engineering.compose("system text", [str(empty)])
    assert str(empty) in str(excinfo.value)


def test_directory_instead_of_file_raises_with_path(tmp_path):
    a_dir = tmp_path / "not-a-file"
    a_dir.mkdir()
    with pytest.raises(skill_engineering.SkillFileError) as excinfo:
        skill_engineering.compose("system text", [str(a_dir)])
    assert str(a_dir) in str(excinfo.value)


# ── check() — the fail-fast seam agents.validate() calls, standalone from
#    compose() so a future change to composition (e.g. something that reads
#    system_text) cannot silently diverge from what validate() checked. ────

def test_check_passes_silently_for_a_real_skill_file(tmp_path):
    skill_file = tmp_path / "tdd.md"
    skill_file.write_text("# TDD\n\nRed, green, refactor.\n")
    skill_engineering.check([str(skill_file)])  # must not raise


def test_check_passes_silently_for_no_skills():
    skill_engineering.check([])  # must not raise


def test_check_raises_the_same_error_compose_would(tmp_path):
    missing = tmp_path / "does-not-exist.md"
    with pytest.raises(skill_engineering.SkillFileError) as excinfo:
        skill_engineering.check([str(missing)])
    assert str(missing) in str(excinfo.value)
