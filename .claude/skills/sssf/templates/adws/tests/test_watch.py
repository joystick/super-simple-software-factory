"""adw_watch.py -- `just watch`: the headless half of the dark-factory queue.

Only ever claims issues already carrying Status: ready-for-agent. The
feasibility/compatibility/compliance/security judgment that gets an issue
there is explicitly not this module's job -- see its own docstring and the
adoption playbook's Part D.
"""

from __future__ import annotations

import adw_watch


def make_issue(dir_, name, status, blocked_by=None, body="Do the thing.\n"):
    dir_.mkdir(parents=True, exist_ok=True)
    text = f"# {name}\n\nStatus: {status}\n"
    if blocked_by:
        text += f"Blocked by: {', '.join(blocked_by)}\n"
    text += f"\n{body}"
    (dir_ / f"{name}.md").write_text(text)
    return dir_ / f"{name}.md"


# ── discover_issues / read_status / read_blocked_by ────────────────────────

def test_discover_issues_finds_files_with_a_status_line(tmp_path):
    issues_dir = tmp_path / "route-builder" / "issues"
    make_issue(issues_dir, "01-first", "ready-for-agent")
    make_issue(issues_dir, "02-second", "needs-triage")

    found = adw_watch.discover_issues(tmp_path)

    assert {i.number for i in found} == {"01", "02"}
    assert all(i.feature == "route-builder" for i in found)


def test_discover_issues_skips_a_file_with_no_status_line(tmp_path):
    issues_dir = tmp_path / "route-builder" / "issues"
    issues_dir.mkdir(parents=True)
    (issues_dir / "00-notes.md").write_text("# Just some notes, not a tracked issue\n")

    found = adw_watch.discover_issues(tmp_path)

    assert found == []


def test_discover_issues_returns_empty_for_a_missing_scratch_dir(tmp_path):
    assert adw_watch.discover_issues(tmp_path / "does-not-exist") == []


def test_read_blocked_by_parses_a_comma_separated_list():
    text = "Status: ready-for-agent\nBlocked by: 01, 02\n"
    assert adw_watch.read_blocked_by(text) == ["01", "02"]


def test_read_blocked_by_returns_empty_list_when_absent():
    assert adw_watch.read_blocked_by("Status: ready-for-agent\n") == []


# ── bold-markup tolerance -- found live, 2026-09-14: to-tickets publishes
#    its own local-ticket-template with **Status:**/**Blocked by:**, which
#    the original plain-only regex never matched, so four real portfinder
#    tickets were silently invisible to the frontier scan with no error ──

def test_read_status_accepts_the_bold_form_to_tickets_actually_writes():
    assert adw_watch.read_status("**Status:** ready-for-agent\n") == "ready-for-agent"


def test_read_blocked_by_accepts_the_bold_form():
    assert adw_watch.read_blocked_by("**Blocked by:** 01, 02\n") == ["01", "02"]


def test_read_blocked_by_strips_a_trailing_parenthetical_annotation():
    # "05 (Directory tables + seed)" -> "05" -- found alongside the bold-markup
    # bug: without stripping, the whole string is one fragment that never
    # matches is_unblocked()'s bare-number sibling keys.
    text = "Blocked by: 05 (Directory tables + seed), 06 (Search route)\n"
    assert adw_watch.read_blocked_by(text) == ["05", "06"]


def test_read_blocked_by_strips_a_parenthetical_with_trailing_punctuation():
    # "09 (Directory fallback in endpoint resolution)." -- a period AFTER the
    # closing paren. Found live: the first fix's $-anchored strip only fired
    # when the parenthetical was the true end of the string, so this never
    # matched and "09 (...)." sat as one permanently-unresolvable fragment.
    text = "Blocked by: 09 (Directory fallback in endpoint resolution).\n"
    assert adw_watch.read_blocked_by(text) == ["09"]


def test_read_blocked_by_treats_bare_none_as_no_blockers():
    assert adw_watch.read_blocked_by("Blocked by: None\n") == []


def test_read_blocked_by_treats_none_with_explanatory_parenthetical_as_no_blockers():
    # Found live: "None (port_directory tables ship; this only reads them)."
    # was kept as one literal, permanently-unmatched token -- an explicitly
    # UNblocked ticket sat invisible to the frontier, the identical failure
    # shape as the original bug, just via a different value.
    text = "Blocked by: None (port_directory tables ship; this only reads them).\n"
    assert adw_watch.read_blocked_by(text) == []


def test_read_blocked_by_treats_none_with_a_comma_inside_the_parenthetical_as_no_blockers():
    # Found while writing the docs/training queue lesson, 2026-09-24: a comma
    # INSIDE the parenthetical ("(none -- API exists, see spec.md)") used to
    # get comma-split before the parenthetical was stripped, producing two
    # broken tokens ("none -- API exists" and "see spec.md)") instead of
    # recognizing the whole value as "no blocker".
    text = "Blocked by: none (API exists, see spec.md)\n"
    assert adw_watch.read_blocked_by(text) == []


def test_read_blocked_by_strips_a_parenthetical_containing_a_comma_before_a_real_ticket():
    text = "Blocked by: 09 (needs review, see spec.md)\n"
    assert adw_watch.read_blocked_by(text) == ["09"]


def test_read_blocked_by_warns_on_a_value_that_is_not_a_bare_ticket_number(tmp_path, capsys):
    path = tmp_path / "ticket.md"
    text = "Blocked by: the migration ticket\n"

    result = adw_watch.read_blocked_by(text, path)

    assert result == ["the migration ticket"]  # kept, not dropped -- safe default
    assert "WARNING" in capsys.readouterr().err


def test_read_blocked_by_no_warning_without_a_path(capsys):
    # discover_issues() always passes path; direct callers (e.g. tests) may
    # not care about the warning -- must not crash when path is omitted.
    assert adw_watch.read_blocked_by("Blocked by: garbage\n") == ["garbage"]
    assert capsys.readouterr().err == ""


def test_discover_issues_finds_bold_form_tickets(tmp_path):
    issues_dir = tmp_path / "portfinder" / "issues"
    issues_dir.mkdir(parents=True)
    (issues_dir / "05-seed.md").write_text(
        "# 05: Seed\n\n**What to build:** the thing.\n\n**Status:** ready-for-agent\n")

    found = adw_watch.discover_issues(tmp_path)

    assert len(found) == 1
    assert found[0].status == "ready-for-agent"


def test_set_status_preserves_bold_key_formatting_only_changing_the_value(tmp_path):
    # Only the VALUE changes -- the key's own formatting (bold, here) is not
    # this function's business to rewrite. A prior version replaced the
    # WHOLE matched span with a hardcoded plain "Status: X", silently
    # stripping bold formatting on every claim/resolve as an unrequested
    # side effect.
    path = tmp_path / "ticket.md"
    path.write_text("# Ticket\n\n**Status:** ready-for-agent\n")

    adw_watch.set_status(path, adw_watch.CLAIMED)

    text = path.read_text()
    assert "**Status:** claimed" in text
    assert "ready-for-agent" not in text


def test_set_status_preserves_plain_key_formatting(tmp_path):
    path = tmp_path / "ticket.md"
    path.write_text("# Ticket\n\nStatus: ready-for-agent\n")

    adw_watch.set_status(path, adw_watch.CLAIMED)

    text = path.read_text()
    assert "Status: claimed" in text
    assert "**" not in text


# ── _check_format: loud warning, never silent, never fatal, for a
#    Status:/Blocked by: line that looks intended but matches neither
#    canonical form ──

def test_check_format_warns_on_underscore_emphasis(capsys):
    # \b (word boundary) fails right after "Status_" because underscore IS
    # a word character in Python's re -- a \b-anchored near-miss detector
    # would silently let this straight through, the exact failure class
    # this detector exists to catch.
    adw_watch._check_format("_Status_: ready-for-agent\n", "fake.md")
    assert "WARNING" in capsys.readouterr().err


def test_check_format_warns_on_a_missing_colon(capsys):
    adw_watch._check_format("Status ready-for-agent\n", "fake.md")
    assert "WARNING" in capsys.readouterr().err


def test_check_format_warns_on_malformed_blocked_by(capsys):
    adw_watch._check_format("_Blocked by_: 01\n", "fake.md")
    assert "WARNING" in capsys.readouterr().err


def test_check_format_silent_on_plain(capsys):
    adw_watch._check_format("Status: ready-for-agent\n", "fake.md")
    assert capsys.readouterr().err == ""


def test_check_format_silent_on_bold(capsys):
    adw_watch._check_format("**Status:** ready-for-agent\n", "fake.md")
    assert capsys.readouterr().err == ""


def test_check_format_silent_on_unrelated_prose(capsys):
    # "status" appearing mid-sentence, not at true line start, must never
    # false-positive -- issues/*.md files carry plenty of free-form prose.
    adw_watch._check_format("The migration status changed recently.\n", "fake.md")
    assert capsys.readouterr().err == ""


def test_discover_issues_warns_on_a_near_miss_file_but_does_not_crash(tmp_path, capsys):
    issues_dir = tmp_path / "feature" / "issues"
    issues_dir.mkdir(parents=True)
    (issues_dir / "01-broken.md").write_text("# Broken\n\n_Status_: ready-for-agent\n")

    found = adw_watch.discover_issues(tmp_path)

    assert found == []  # still correctly not a tracked issue -- doesn't parse
    assert "WARNING" in capsys.readouterr().err  # but the operator is told why


# ── frontier ─────────────────────────────────────────────────────────────

def test_frontier_picks_the_only_ready_and_unblocked_issue(tmp_path):
    issues_dir = tmp_path / "feature" / "issues"
    make_issue(issues_dir, "01-a", "ready-for-agent")
    make_issue(issues_dir, "02-b", "needs-triage")

    picked = adw_watch.frontier(adw_watch.discover_issues(tmp_path))

    assert picked.number == "01"


def test_frontier_skips_a_blocked_issue_until_its_blocker_resolves(tmp_path):
    issues_dir = tmp_path / "feature" / "issues"
    make_issue(issues_dir, "01-a", "ready-for-agent")
    make_issue(issues_dir, "02-b", "ready-for-agent", blocked_by=["01"])

    picked = adw_watch.frontier(adw_watch.discover_issues(tmp_path))
    assert picked.number == "01"  # 02 is blocked, skip straight past it

    # resolve 01, then 02 becomes pickable
    adw_watch.set_status(issues_dir / "01-a.md", adw_watch.RESOLVED)
    picked = adw_watch.frontier(adw_watch.discover_issues(tmp_path))
    assert picked.number == "02"


def test_frontier_ignores_claimed_and_resolved_issues(tmp_path):
    issues_dir = tmp_path / "feature" / "issues"
    make_issue(issues_dir, "01-a", "claimed")
    make_issue(issues_dir, "02-b", "resolved")

    assert adw_watch.frontier(adw_watch.discover_issues(tmp_path)) is None


def test_frontier_returns_none_for_an_empty_queue(tmp_path):
    assert adw_watch.frontier([]) is None


def test_frontier_blocked_by_numbers_are_scoped_per_feature(tmp_path):
    # feature A's "01" must never satisfy feature B's "Blocked by: 01"
    a_dir = tmp_path / "feature-a" / "issues"
    b_dir = tmp_path / "feature-b" / "issues"
    make_issue(a_dir, "01-a", "ready-for-agent")  # unrelated, not resolved
    make_issue(b_dir, "01-b", "ready-for-agent")
    make_issue(b_dir, "02-c", "ready-for-agent", blocked_by=["01"])

    picked = adw_watch.frontier(adw_watch.discover_issues(tmp_path))

    # only 01-a (feature-a) and 01-b (feature-b) are unblocked; feature-a
    # sorts first alphabetically
    assert picked.feature == "feature-a"
    assert picked.number == "01"


def test_frontier_picks_lowest_feature_and_number_first(tmp_path):
    issues_dir_z = tmp_path / "zzz-feature" / "issues"
    issues_dir_a = tmp_path / "aaa-feature" / "issues"
    make_issue(issues_dir_z, "01-a", "ready-for-agent")
    make_issue(issues_dir_a, "02-b", "ready-for-agent")

    picked = adw_watch.frontier(adw_watch.discover_issues(tmp_path))

    assert picked.feature == "aaa-feature"


# ── set_status / append_comment ─────────────────────────────────────────

def test_set_status_rewrites_the_status_line_in_place(tmp_path):
    issues_dir = tmp_path / "feature" / "issues"
    path = make_issue(issues_dir, "01-a", "ready-for-agent", body="The body.\n")

    adw_watch.set_status(path, adw_watch.CLAIMED)

    text = path.read_text()
    assert "Status: claimed" in text
    assert "Status: ready-for-agent" not in text
    assert "The body." in text  # rest of the file survives untouched


def test_append_comment_adds_a_comments_section_once(tmp_path):
    issues_dir = tmp_path / "feature" / "issues"
    path = make_issue(issues_dir, "01-a", "ready-for-agent")

    adw_watch.append_comment(path, "> *first note*")
    adw_watch.append_comment(path, "> *second note*")

    text = path.read_text()
    assert text.count("## Comments") == 1
    assert "first note" in text
    assert "second note" in text


# ── dispatch (adw_simple_sdlc.main AND git_helper both mocked -- no ────
# real agent calls, and critically no real git commands: dispatch() now
# commits its own state, and these tests don't chdir into tmp_path, so an
# unmocked git_helper would run against whatever repo pytest itself is
# invoked from.

def mock_git(monkeypatch):
    """Fake git_helper: always "dirty" (so commit_watcher_state always
    attempts a commit) and commit_all just records calls instead of running
    real git. Returns the list of recorded commit messages."""
    commits = []
    monkeypatch.setattr(adw_watch.git_helper, "is_dirty", lambda: True)
    monkeypatch.setattr(adw_watch.git_helper, "is_repo", lambda: True)
    monkeypatch.setattr(adw_watch.git_helper, "commit_all",
                        lambda msg: commits.append(msg) or "abc1234")
    return commits


def test_dispatch_resolves_the_issue_on_success(tmp_path, monkeypatch):
    issues_dir = tmp_path / "feature" / "issues"
    path = make_issue(issues_dir, "01-a", "ready-for-agent")
    issue = adw_watch.discover_issues(tmp_path)[0]
    commits = mock_git(monkeypatch)

    monkeypatch.setattr(adw_watch.adw_simple_sdlc, "main", lambda *a, **kw: 0)

    ok, adw_id = adw_watch.dispatch(issue, "adws/adw_sssf_config/sssf.config.yaml")

    assert ok is True
    assert "Status: resolved" in path.read_text()
    assert adw_id in path.read_text()
    assert len(commits) == 2  # claim, then resolve
    assert "claim" in commits[0]
    assert "resolve" in commits[1]


def test_dispatch_flips_to_ready_for_human_on_a_nonzero_exit(tmp_path, monkeypatch):
    issues_dir = tmp_path / "feature" / "issues"
    path = make_issue(issues_dir, "01-a", "ready-for-agent")
    issue = adw_watch.discover_issues(tmp_path)[0]
    mock_git(monkeypatch)

    monkeypatch.setattr(adw_watch.adw_simple_sdlc, "main", lambda *a, **kw: 1)

    ok, adw_id = adw_watch.dispatch(issue, "adws/adw_sssf_config/sssf.config.yaml")

    assert ok is False
    text = path.read_text()
    assert "Status: ready-for-human" in text
    assert "failed" in text


def test_dispatch_flips_to_ready_for_human_on_a_crash_not_a_watcher_crash(tmp_path, monkeypatch):
    issues_dir = tmp_path / "feature" / "issues"
    path = make_issue(issues_dir, "01-a", "ready-for-agent")
    issue = adw_watch.discover_issues(tmp_path)[0]
    mock_git(monkeypatch)

    def boom(*a, **kw):
        raise RuntimeError("agent exploded")

    monkeypatch.setattr(adw_watch.adw_simple_sdlc, "main", boom)

    ok, adw_id = adw_watch.dispatch(issue, "adws/adw_sssf_config/sssf.config.yaml")

    assert ok is False
    assert "Status: ready-for-human" in path.read_text()
    assert "crashed" in path.read_text()


def test_dispatch_flips_to_ready_for_human_on_a_system_exit_not_a_watcher_crash(tmp_path, monkeypatch):
    # agents.validate() raises SystemExit on a config problem (bad model string,
    # missing prompt file, etc.) -- SystemExit inherits BaseException, not
    # Exception, so a bare `except Exception` never sees it. Found live: a
    # malformed roster model string crashed the whole watcher process instead of
    # flipping the issue to ready-for-human, leaving it stuck at Status: claimed
    # with no resolution commit.
    issues_dir = tmp_path / "feature" / "issues"
    path = make_issue(issues_dir, "01-a", "ready-for-agent")
    issue = adw_watch.discover_issues(tmp_path)[0]
    mock_git(monkeypatch)

    def config_error(*a, **kw):
        raise SystemExit("config validation failed:\n- agent 'planner': bad model")

    monkeypatch.setattr(adw_watch.adw_simple_sdlc, "main", config_error)

    ok, adw_id = adw_watch.dispatch(issue, "adws/adw_sssf_config/sssf.config.yaml")

    assert ok is False
    text = path.read_text()
    assert "Status: ready-for-human" in text
    assert "crashed" in text
    assert "bad model" in text


def test_dispatch_claims_before_running_so_a_crash_never_leaves_it_ready(tmp_path, monkeypatch):
    issues_dir = tmp_path / "feature" / "issues"
    path = make_issue(issues_dir, "01-a", "ready-for-agent")
    issue = adw_watch.discover_issues(tmp_path)[0]
    mock_git(monkeypatch)

    seen_status_at_call_time = {}

    def spy(*a, **kw):
        seen_status_at_call_time["status"] = path.read_text()
        return 0

    monkeypatch.setattr(adw_watch.adw_simple_sdlc, "main", spy)
    adw_watch.dispatch(issue, "adws/adw_sssf_config/sssf.config.yaml")

    assert "Status: claimed" in seen_status_at_call_time["status"]


def test_commit_watcher_state_skips_commit_when_nothing_changed(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(adw_watch.git_helper, "is_dirty", lambda: False)
    monkeypatch.setattr(adw_watch.git_helper, "commit_all", lambda msg: calls.append(msg))

    adw_watch.commit_watcher_state("should not fire")

    assert calls == []


# ── detect_tracker ───────────────────────────────────────────────────────

def test_detect_tracker_reads_local_markdown_from_the_doc(tmp_path):
    doc_dir = tmp_path / "docs" / "agents"
    doc_dir.mkdir(parents=True)
    (doc_dir / "issue-tracker.md").write_text("# Issue tracker: Local Markdown\n")

    assert adw_watch.detect_tracker(tmp_path) == "local"


def test_detect_tracker_reads_github_from_the_doc(tmp_path):
    doc_dir = tmp_path / "docs" / "agents"
    doc_dir.mkdir(parents=True)
    (doc_dir / "issue-tracker.md").write_text("# Issue tracker: GitHub\n")

    assert adw_watch.detect_tracker(tmp_path) == "github"


def test_detect_tracker_falls_back_to_scratch_dir_presence(tmp_path):
    (tmp_path / ".scratch").mkdir()
    assert adw_watch.detect_tracker(tmp_path) == "local"


def test_detect_tracker_returns_unknown_with_no_signal(tmp_path):
    assert adw_watch.detect_tracker(tmp_path) == "unknown"


# ── main() exit codes ───────────────────────────────────────────────────

def test_main_returns_2_for_a_non_local_tracker(tmp_path, monkeypatch):
    doc_dir = tmp_path / "docs" / "agents"
    doc_dir.mkdir(parents=True)
    (doc_dir / "issue-tracker.md").write_text("# Issue tracker: GitHub\n")
    monkeypatch.chdir(tmp_path)

    assert adw_watch.main(".scratch", "adws/adw_sssf_config/sssf.config.yaml", once=True, interval=1) == 2


def test_main_returns_1_for_an_empty_queue(tmp_path, monkeypatch):
    (tmp_path / ".scratch").mkdir()
    monkeypatch.chdir(tmp_path)

    assert adw_watch.main(".scratch", "adws/adw_sssf_config/sssf.config.yaml", once=True, interval=1) == 1


def test_main_returns_0_when_work_was_dispatched(tmp_path, monkeypatch):
    scratch = tmp_path / ".scratch"
    make_issue(scratch / "feature" / "issues", "01-a", "ready-for-agent")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(adw_watch.adw_simple_sdlc, "main", lambda *a, **kw: 0)

    # not a real repo -- dispatch()'s own commits must not hit real git.
    # is_dirty()'s first call is run_once's own scan-time guard (must see
    # clean, or it refuses to claim); every call after that is a
    # commit_watcher_state check post-write (must see dirty, or it skips).
    monkeypatch.setattr(adw_watch.git_helper, "is_repo", lambda: True)
    calls = {"n": 0}

    def is_dirty():
        calls["n"] += 1
        return calls["n"] > 1

    monkeypatch.setattr(adw_watch.git_helper, "is_dirty", is_dirty)
    monkeypatch.setattr(adw_watch.git_helper, "commit_all", lambda msg: "abc1234")

    assert adw_watch.main(".scratch", "adws/adw_sssf_config/sssf.config.yaml", once=True, interval=1) == 0


# ── dirty-tree guard ─────────────────────────────────────────────────────

def test_run_once_refuses_to_claim_against_a_dirty_tree(tmp_path, monkeypatch):
    scratch = tmp_path / ".scratch"
    make_issue(scratch / "feature" / "issues", "01-a", "ready-for-agent")
    monkeypatch.setattr(adw_watch.git_helper, "is_repo", lambda: True)
    monkeypatch.setattr(adw_watch.git_helper, "is_dirty", lambda: True)
    calls = []
    monkeypatch.setattr(adw_watch.adw_simple_sdlc, "main",
                        lambda *a, **kw: calls.append(1) or 0)

    found = adw_watch.run_once(scratch, "adws/adw_sssf_config/sssf.config.yaml")

    assert found is False
    assert calls == []  # never even reached dispatch
    assert "Status: ready-for-agent" in (scratch / "feature" / "issues" / "01-a.md").read_text()
