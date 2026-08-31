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


def test_multiple_skills_compose_in_the_listed_order_not_sorted(tmp_path):
    # Names chosen so alphabetical order would reverse the listed order —
    # "zzz" would sort after "aaa", but the engineer listed it first.
    first = tmp_path / "zzz-grill-me.md"
    first.write_text("Grill the plan before it costs anything.")
    second = tmp_path / "aaa-tdd.md"
    second.write_text("Red, green, refactor.")

    composed = skill_engineering.compose("System.", [str(first), str(second)])

    grill_at = composed.index("Grill the plan")
    tdd_at = composed.index("Red, green, refactor.")
    assert grill_at < tdd_at, "skills must compose in listed order, not alphabetical"


def test_a_hand_authored_local_skill_composes_identically_to_a_vendored_one(tmp_path):
    # compose() has no concept of "vendored" vs. "local" — a plain Markdown
    # file the engineer wrote themselves must work exactly the same way as
    # one copied in by a vendoring script (that script doesn't exist until
    # Phase 4; this proves compose() never needed to know the difference).
    house_rule = tmp_path / "house-conventions.md"
    house_rule.write_text("Every PR description states the why, not the what.")

    composed = skill_engineering.compose("System.", [str(house_rule)])

    assert "Every PR description states the why" in composed
    assert "house-conventions" in composed.split("System.", 1)[1]


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


# ── estimate_tokens() — Phase 3: cost visibility. A heuristic, not exact —
#    good enough to warn on, never claimed as billed truth. ────────────────

def test_estimate_tokens_is_zero_for_no_skills():
    assert skill_engineering.estimate_tokens([]) == 0


def test_estimate_tokens_is_positive_for_a_real_skill(tmp_path):
    skill_file = tmp_path / "tdd.md"
    skill_file.write_text("# TDD\n\n" + ("Red, green, refactor. " * 50))
    assert skill_engineering.estimate_tokens([str(skill_file)]) > 0


def test_estimate_tokens_is_monotonic_in_the_number_of_skills(tmp_path):
    one = tmp_path / "one.md"
    one.write_text("Red, green, refactor. " * 20)
    two = tmp_path / "two.md"
    two.write_text("Judge module depth. " * 20)

    single = skill_engineering.estimate_tokens([str(one)])
    double = skill_engineering.estimate_tokens([str(one), str(two)])
    assert double > single
