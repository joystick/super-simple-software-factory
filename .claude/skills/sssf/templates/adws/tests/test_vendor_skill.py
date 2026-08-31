"""vendor_skill.py — Phase 4: vendoring with provenance.

A deliberate, reviewable copy: source path + date + content hash stamped
into the vendored file, so drift from the original is detectable later.
No auto-update, ever — see the plan's own explicit acceptance criterion.
"""

from __future__ import annotations

import pytest
import vendor_skill


def test_vendor_copies_the_source_body_into_the_destination(tmp_path):
    source = tmp_path / "tdd.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"

    result = vendor_skill.vendor(source, dest_dir)

    assert result.dest.is_file()
    assert "Red, green, refactor." in result.dest.read_text()


def test_vendored_file_carries_source_path_date_and_hash(tmp_path):
    source = tmp_path / "tdd.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"

    result = vendor_skill.vendor(source, dest_dir, today="2026-08-31")

    text = result.dest.read_text()
    assert "2026-08-31" in text
    assert result.source_hash in text


def test_a_source_under_home_is_stored_relative_to_home_not_as_an_absolute_path(
        monkeypatch, tmp_path):
    # Found by adversarial review: a committed provenance header with an
    # absolute path bakes one machine's username into the repo, and
    # --check on any other machine reports "source gone" for a source that
    # is actually right there under THEIR home directory. Every real Pocock
    # skill lives under ~/.claude/skills/ or similar — store relative to
    # $HOME so the header is portable across machines that share that
    # convention, which is the entire premise of this feature existing.
    fake_home = tmp_path / "home" / "alexei"
    (fake_home / ".claude" / "skills" / "tdd").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(fake_home))
    source = fake_home / ".claude" / "skills" / "tdd" / "SKILL.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"

    result = vendor_skill.vendor(source, dest_dir)

    text = result.dest.read_text()
    assert str(fake_home) not in text
    assert "~/.claude/skills/tdd/SKILL.md" in text


def test_a_source_outside_home_still_stores_an_absolute_path(tmp_path):
    # No portable shorthand exists for a source outside $HOME — an absolute
    # path here is the honest answer, not a regression.
    source = tmp_path / "elsewhere" / "tdd.md"
    source.parent.mkdir()
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"

    result = vendor_skill.vendor(source, dest_dir)

    assert str(source.resolve()) in result.dest.read_text()


def test_vendored_name_defaults_to_the_source_stem(tmp_path):
    source = tmp_path / "tdd.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"

    result = vendor_skill.vendor(source, dest_dir)

    assert result.dest.name == "tdd.md"


def test_vendored_name_defaults_to_the_parent_directory_for_a_bare_skill_md(tmp_path):
    # Every real Pocock skill file is literally named SKILL.md — the actual
    # skill name lives in the parent directory (~/.claude/skills/tdd/SKILL.md).
    # Defaulting to the file's own stem ("SKILL") would vendor every skill
    # in a roster to the same destination filename and silently clobber each
    # other. Caught live, not by a test — every earlier fixture in this file
    # used a filename that happened to already be the skill's real name.
    skill_dir = tmp_path / "tdd"
    skill_dir.mkdir()
    source = skill_dir / "SKILL.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"

    result = vendor_skill.vendor(source, dest_dir)

    assert result.dest.name == "tdd.md"


def test_vendored_name_can_be_overridden(tmp_path):
    source = tmp_path / "SKILL.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"

    result = vendor_skill.vendor(source, dest_dir, name="tdd")

    assert result.dest.name == "tdd.md"


def test_revendoring_an_unchanged_skill_is_a_reported_no_change(tmp_path):
    source = tmp_path / "tdd.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"

    first = vendor_skill.vendor(source, dest_dir, today="2026-08-31")
    second = vendor_skill.vendor(source, dest_dir, today="2026-09-01")

    assert second.changed is False
    # re-vendoring unchanged content must not rewrite the file (and so must
    # not bump its date/timestamp) — the first vendoring's date is preserved
    assert "2026-08-31" in second.dest.read_text()
    assert first.dest.read_text() == second.dest.read_text()


def test_revendoring_changed_source_is_reported_as_a_real_change(tmp_path):
    source = tmp_path / "tdd.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"
    vendor_skill.vendor(source, dest_dir, today="2026-08-31")

    source.write_text("# TDD\n\nRed, green, refactor, always in that order.\n")
    result = vendor_skill.vendor(source, dest_dir, today="2026-09-01")

    assert result.changed is True
    assert "always in that order" in result.dest.read_text()
    assert "2026-09-01" in result.dest.read_text()


def test_check_drift_reports_none_when_source_matches_the_stamped_hash(tmp_path):
    source = tmp_path / "tdd.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"
    result = vendor_skill.vendor(source, dest_dir)

    drift = vendor_skill.check_drift(result.dest)
    assert drift.drifted is False


def test_check_drift_works_on_a_source_stored_relative_to_home(monkeypatch, tmp_path):
    fake_home = tmp_path / "home" / "alexei"
    (fake_home / ".claude" / "skills" / "tdd").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(fake_home))
    source = fake_home / ".claude" / "skills" / "tdd" / "SKILL.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"
    result = vendor_skill.vendor(source, dest_dir)

    drift = vendor_skill.check_drift(result.dest)
    assert drift.drifted is False


def test_check_drift_detects_a_changed_source(tmp_path):
    source = tmp_path / "tdd.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"
    result = vendor_skill.vendor(source, dest_dir)

    source.write_text("# TDD\n\nSomething else entirely.\n")
    drift = vendor_skill.check_drift(result.dest)
    assert drift.drifted is True
    assert str(source) in drift.message


def test_vendor_refuses_to_overwrite_a_hand_authored_file_with_the_same_name(tmp_path):
    dest_dir = tmp_path / "vendored"
    dest_dir.mkdir()
    hand_authored = dest_dir / "tdd.md"
    hand_authored.write_text("My own house rules for TDD, written by hand.")

    source = tmp_path / "tdd.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")

    with pytest.raises(vendor_skill.HandAuthoredFileError) as excinfo:
        vendor_skill.vendor(source, dest_dir)
    assert str(hand_authored) in str(excinfo.value)
    # the hand-authored content must survive the attempt untouched
    assert hand_authored.read_text() == "My own house rules for TDD, written by hand."


# ── Parity with skill_engineering.PROVENANCE_HEADER_RE ─────────────────────
# The two regexes are independently defined — this module lives only in the
# skill source (never stamped into a target repo), while
# adw_modules/skill_engineering.py IS stamped and must stay standalone. This
# test is what actually prevents silent divergence between them, not any
# shared import.

def test_a_real_vendored_header_is_recognized_by_both_regexes(tmp_path):
    from adw_modules import skill_engineering

    source = tmp_path / "tdd.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"
    result = vendor_skill.vendor(source, dest_dir, today="2026-08-31")

    raw = result.dest.read_text()
    assert vendor_skill.HEADER_RE.match(raw) is not None
    assert skill_engineering.PROVENANCE_HEADER_RE.match(raw) is not None
    # and both agree on WHERE the header ends: the body left after stripping
    # is identical either way
    vendor_tail = vendor_skill.HEADER_RE.sub("", raw, count=1)
    skill_eng_tail = skill_engineering.PROVENANCE_HEADER_RE.sub("", raw, count=1)
    assert vendor_tail == skill_eng_tail


def test_prose_about_the_header_format_is_not_mistaken_for_a_real_one(tmp_path):
    # A skill file that happens to DOCUMENT this feature (e.g. a skill about
    # skill_engineering itself) must not have that documentation stripped as
    # if it were a real, machine-written header.
    from adw_modules import skill_engineering

    tricky = tmp_path / "meta.md"
    tricky.write_text(
        "# About vendoring\n\n"
        "Vendored files start with a header like:\n\n"
        "<!-- sssf:vendored\n"
        "this is not a real hash -->\n\n"
        "Real content follows.\n"
    )
    composed = skill_engineering.compose("System.", [str(tricky)])
    assert "Vendored files start with a header like" in composed
    assert "Real content follows." in composed


def test_check_drift_reports_a_moved_or_deleted_source(tmp_path):
    source = tmp_path / "tdd.md"
    source.write_text("# TDD\n\nRed, green, refactor.\n")
    dest_dir = tmp_path / "vendored"
    result = vendor_skill.vendor(source, dest_dir)

    source.unlink()
    drift = vendor_skill.check_drift(result.dest)
    assert drift.drifted is True
    assert str(source) in drift.message
