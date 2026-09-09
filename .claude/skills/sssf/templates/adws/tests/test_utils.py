"""adw_modules/utils.py — small shared helpers.

load_plan_from_file backs --skip-plan: build a PlanOutput from an
already-written, already-reviewed plan instead of re-invoking the planner.
"""

from __future__ import annotations

import pytest
from adw_modules import utils
from adw_modules.data_types import PlanOutput


def test_load_plan_from_file_returns_a_plan_output(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("# Add a /health endpoint\n\nReturn 200 with an empty body.\n")

    result = utils.load_plan_from_file(str(plan))

    assert isinstance(result, PlanOutput)
    assert result.status == "success"
    assert result.artifacts == [str(plan)]


def test_load_plan_from_file_summary_uses_the_first_non_blank_line(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("\n\n# Add a /health endpoint\n\nReturn 200 with an empty body.\n")

    result = utils.load_plan_from_file(str(plan))

    assert "Add a /health endpoint" in result.summary
    # the leading "# " markdown heading marker must not leak into the summary
    assert "#" not in result.summary


def test_load_plan_from_file_notes_it_was_loaded_not_generated(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("# A plan\n")

    result = utils.load_plan_from_file(str(plan))

    assert "--skip-plan" in result.notes_for_next_agent
    assert "not freshly generated" in result.notes_for_next_agent


def test_load_plan_from_file_raises_file_not_found_error_for_a_missing_path(tmp_path):
    missing = tmp_path / "nope.md"

    with pytest.raises(FileNotFoundError) as excinfo:
        utils.load_plan_from_file(str(missing))
    assert str(missing) in str(excinfo.value)


def test_load_plan_from_file_raises_value_error_for_an_empty_file(tmp_path):
    empty = tmp_path / "empty.md"
    empty.write_text("")

    with pytest.raises(ValueError) as excinfo:
        utils.load_plan_from_file(str(empty))
    assert str(empty) in str(excinfo.value)


def test_load_plan_from_file_raises_value_error_for_a_whitespace_only_file(tmp_path):
    blank = tmp_path / "blank.md"
    blank.write_text("   \n\n   \n")

    with pytest.raises(ValueError):
        utils.load_plan_from_file(str(blank))


def test_load_plan_from_file_handles_a_line_that_is_only_hash_marks(tmp_path):
    # "###" strips to "" via .strip("# ") — the summary must still be a
    # usable non-empty string ("Loaded existing plan: ") rather than raising
    plan = tmp_path / "plan.md"
    plan.write_text("###\n")

    result = utils.load_plan_from_file(str(plan))

    assert result.summary.startswith("Loaded existing plan:")
