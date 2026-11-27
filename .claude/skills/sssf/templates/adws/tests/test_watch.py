"""adw_watch.py -- `just watch`: the headless half of the dark-factory queue.

Only ever claims issues already carrying Status: ready-for-agent. The
feasibility/compatibility/compliance/security judgment that gets an issue
there is explicitly not this module's job -- see its own docstring and the
adoption playbook's Part D.
"""

from __future__ import annotations

from pathlib import Path

import pytest

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

# test_main_returns_2_for_a_non_local_tracker was deleted with issue #20.
# It asserted "GitHub tracker -> exit 2, not implemented yet", which is the
# behaviour #20 deliberately replaced. It was also environment-dependent: it
# ran no mocks, so on a machine with `gh` authenticated it only still passed
# because tmp_path isn't a git repo. The property worth keeping -- an
# unreachable tracker exits 2 and never reports a falsely-empty queue -- is
# covered by test_main_exits_2_when_the_tracker_cli_is_unavailable, with the
# CLI mocked.


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


# ══════════════════════════════════════════════════════════════════════════
# Tracker adapters (issue #20). Every CLI call is faked -- no network, no
# `gh`/`glab` binary needed to run this suite.
# ══════════════════════════════════════════════════════════════════════════

def fake_runner(script):
    """Returns (runner, calls). `script` maps a command prefix to
    (exit_code, stdout); anything unmatched succeeds with empty output."""
    calls = []

    def run(argv):
        calls.append(argv)
        for prefix, result in script.items():
            if argv[:len(prefix)] == list(prefix):
                return result
        return 0, ""

    return run, calls


GH_AUTH_OK = {("gh", "auth", "status"): (0, "Logged in")}


def gh_list(rows):
    import json as _json
    return {("gh", "issue", "list"): (0, _json.dumps(rows))}


# ── fail-closed: the property the old hard refusal got right ──────────────

def test_github_preflight_raises_when_the_cli_is_missing():
    run, _ = fake_runner({("gh", "auth", "status"): (127, "gh: command not found")})
    with pytest.raises(adw_watch.TrackerUnavailable):
        adw_watch.GitHubTracker(run).preflight()


def test_main_exits_2_when_the_tracker_cli_is_unavailable(tmp_path, monkeypatch):
    # Replaces the old test_main_returns_2_for_a_non_local_tracker, which
    # pinned "GitHub -> not implemented". GitHub IS implemented now; what must
    # survive is the fail-closed property -- an unreachable tracker exits 2 and
    # never reports a falsely-empty queue, which an operator reads as "no work".
    doc = tmp_path / "docs" / "agents"
    doc.mkdir(parents=True)
    (doc / "issue-tracker.md").write_text("# Issue tracker: GitHub\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(adw_watch, "_run_cli",
                        lambda argv: (127, "gh: command not found"))

    assert adw_watch.main(".scratch", "cfg.yaml", once=True, interval=1) == 2


def test_make_tracker_refuses_an_unknown_tracker():
    with pytest.raises(adw_watch.TrackerUnavailable):
        adw_watch.make_tracker("unknown", Path(".scratch"))


# ── discovery: labels carry status, "#N" bodies carry blockers ────────────

def test_github_discover_reads_status_from_labels_and_blockers_from_the_body():
    run, _ = fake_runner({**GH_AUTH_OK, **gh_list([
        {"number": 7, "title": "Do it", "body": "Blocked by: #3, #4\n",
         "labels": [{"name": "ready-for-agent"}]},
    ])})
    issues = adw_watch.GitHubTracker(run).discover()

    assert len(issues) == 1
    assert issues[0].status == adw_watch.READY
    assert issues[0].number == "7"
    assert issues[0].blocked_by == ["3", "4"]   # the "#" is stripped
    assert issues[0].path is None
    assert str(issues[0]) == "#7"


def test_github_claimed_label_wins_so_a_second_watcher_cannot_reclaim():
    run, _ = fake_runner({**GH_AUTH_OK, **gh_list([
        {"number": 7, "title": "t", "body": "",
         "labels": [{"name": "ready-for-agent"}, {"name": "claimed"}]},
    ])})
    assert adw_watch.GitHubTracker(run).discover()[0].status == adw_watch.CLAIMED


def test_github_unlabelled_issue_is_not_ready():
    run, _ = fake_runner({**GH_AUTH_OK, **gh_list([
        {"number": 7, "title": "t", "body": "", "labels": []},
    ])})
    assert adw_watch.GitHubTracker(run).discover()[0].status != adw_watch.READY


# ── the semantics that INVERT between tracker families ───────────────────

def test_remote_treats_a_missing_blocker_as_resolved_because_it_closed():
    # gh is queried for OPEN issues only, so #3's absence IS the evidence it
    # closed. Treating absence as blocking would deadlock the queue the moment
    # a blocker was legitimately closed.
    run, _ = fake_runner({**GH_AUTH_OK, **gh_list([
        {"number": 7, "title": "t", "body": "Blocked by: #3\n",
         "labels": [{"name": "ready-for-agent"}]},
    ])})
    tracker = adw_watch.GitHubTracker(run)
    picked = adw_watch.frontier(tracker.discover(), tracker.missing_means_resolved)

    assert picked is not None and picked.number == "7"


def test_local_treats_a_missing_blocker_as_still_blocking(tmp_path):
    # Opposite default: local discovery sees every ticket regardless of status,
    # so an unfindable blocker is a typo/dangling ref -- never silently unblock.
    issues_dir = tmp_path / "feature" / "issues"
    make_issue(issues_dir, "02-b", "ready-for-agent", blocked_by=["99"])

    assert adw_watch.frontier(adw_watch.discover_issues(tmp_path)) is None


def test_remote_still_blocks_on_an_open_blocker():
    run, _ = fake_runner({**GH_AUTH_OK, **gh_list([
        {"number": 7, "title": "t", "body": "Blocked by: #3\n",
         "labels": [{"name": "ready-for-agent"}]},
        {"number": 3, "title": "blocker", "body": "",
         "labels": [{"name": "ready-for-agent"}]},
    ])})
    tracker = adw_watch.GitHubTracker(run)
    picked = adw_watch.frontier(tracker.discover(), tracker.missing_means_resolved)

    assert picked.number == "3"   # the blocker itself, never #7


# ── status writes map onto labels / close ────────────────────────────────

def test_github_claim_swaps_the_ready_label_for_claimed():
    run, calls = fake_runner(GH_AUTH_OK)
    issue = adw_watch.Issue(path=None, number="7", feature="", status="ready-for-agent",
                            blocked_by=[])
    adw_watch.GitHubTracker(run).set_status(issue, adw_watch.CLAIMED)

    assert calls == [["gh", "issue", "edit", "7",
                      "--add-label", "claimed", "--remove-label", "ready-for-agent"]]


def test_github_resolve_closes_the_issue_rather_than_labelling_it():
    # "resolved" is the issue being closed. A `resolved` label would be a
    # second source of truth that can disagree with the issue's own state.
    run, calls = fake_runner(GH_AUTH_OK)
    issue = adw_watch.Issue(path=None, number="7", feature="", status="claimed",
                            blocked_by=[])
    adw_watch.GitHubTracker(run).set_status(issue, adw_watch.RESOLVED)

    assert ["gh", "issue", "close", "7", "--reason", "completed"] in calls


def test_github_failure_flips_to_ready_for_human_without_closing():
    run, calls = fake_runner(GH_AUTH_OK)
    issue = adw_watch.Issue(path=None, number="7", feature="", status="claimed",
                            blocked_by=[])
    adw_watch.GitHubTracker(run).set_status(issue, adw_watch.FAILED_STATE)

    assert ["gh", "issue", "edit", "7", "--remove-label", "claimed",
            "--add-label", "ready-for-human"] in calls
    assert not any("close" in c for c in calls)


def test_remote_commit_state_is_a_noop_and_needs_no_git_repo(monkeypatch):
    # A label change is already durable server-side. This is also what frees
    # the remote trackers from the old unconditional "must be a git repo"
    # assumption (HANDOFF item 3's other half) -- so it must not touch git
    # even to ask.
    def explode():
        raise AssertionError("remote tracker must not consult git at all")

    monkeypatch.setattr(adw_watch.git_helper, "is_dirty", explode)
    monkeypatch.setattr(adw_watch.git_helper, "is_repo", explode)

    adw_watch.GitHubTracker(lambda a: (0, "")).commit_state("anything")


def test_remote_dispatch_does_not_refuse_on_a_dirty_tree(monkeypatch):
    # The dirty-tree guard exists because local claiming commits. Remote
    # claiming commits nothing, so the guard must not apply -- it would block
    # the queue for a reason that cannot affect it.
    run, _ = fake_runner({**GH_AUTH_OK, **gh_list([
        {"number": 7, "title": "t", "body": "", "labels": [{"name": "ready-for-agent"}]},
    ])})
    monkeypatch.setattr(adw_watch.git_helper, "is_repo", lambda: True)
    monkeypatch.setattr(adw_watch.git_helper, "is_dirty", lambda: True)
    monkeypatch.setattr(adw_watch.adw_simple_sdlc, "main", lambda *a, **kw: 0)

    assert adw_watch.run_once(Path(".scratch"), "cfg.yaml",
                              adw_watch.GitHubTracker(run)) is True


def test_remote_prompt_is_built_from_the_issue_title_and_body():
    issue = adw_watch.Issue(path=None, number="7", feature="", status="ready-for-agent",
                            blocked_by=[], title="Add the thing", body="Do it well.")
    prompt = adw_watch.GitHubTracker(lambda a: (0, "")).prompt_for(issue)

    assert "Add the thing" in prompt and "Do it well." in prompt


# ── ordering ─────────────────────────────────────────────────────────────

def test_frontier_orders_remote_numbers_numerically_not_lexically():
    # "#10" must sort AFTER "#9". A plain string sort puts "10" first; local
    # tickets are zero-padded "01".."09" and so never exposed this.
    run, _ = fake_runner({**GH_AUTH_OK, **gh_list([
        {"number": 10, "title": "ten", "body": "", "labels": [{"name": "ready-for-agent"}]},
        {"number": 9, "title": "nine", "body": "", "labels": [{"name": "ready-for-agent"}]},
    ])})
    tracker = adw_watch.GitHubTracker(run)
    picked = adw_watch.frontier(tracker.discover(), tracker.missing_means_resolved)

    assert picked.number == "9"


# ── the older one-file-per-feature local shape (HANDOFF item 3) ───────────

def test_local_discovers_the_single_issue_md_shape(tmp_path):
    # .scratch/<feature>/issue.md with no issues/ dir and no NN- prefix.
    # Previously found by nothing and reported as an empty queue.
    feature = tmp_path / "legacy-feature"
    feature.mkdir()
    (feature / "issue.md").write_text("# Legacy\n\nStatus: ready-for-agent\n")

    found = adw_watch.discover_issues(tmp_path)

    assert len(found) == 1
    assert found[0].feature == "legacy-feature"
    assert found[0].number == "01"
    assert adw_watch.frontier(found).path == feature / "issue.md"


def test_local_prefers_the_issues_dir_when_both_shapes_exist(tmp_path):
    feature = tmp_path / "feature"
    make_issue(feature / "issues", "01-real", "ready-for-agent")
    (feature / "issue.md").write_text("# Stale\n\nStatus: ready-for-agent\n")

    found = adw_watch.discover_issues(tmp_path)

    assert [i.path.name for i in found] == ["01-real.md"]


def test_local_ignores_a_stray_file_in_the_scratch_root(tmp_path):
    (tmp_path / "notes.md").write_text("# not a feature dir\n\nStatus: ready-for-agent\n")
    assert adw_watch.discover_issues(tmp_path) == []


# ── git-free repo on the LOCAL tracker (#24) ─────────────────────────────

def test_commit_watcher_state_skips_entirely_when_not_a_git_repo(monkeypatch, capsys):
    # The whole point: never invoke git. is_dirty/commit_all must not even be
    # consulted, because in a non-repo they are what raises.
    def explode(*a, **kw):
        raise AssertionError("must not touch git when is_repo() is False")

    monkeypatch.setattr(adw_watch, "_warned_not_a_repo", False)
    monkeypatch.setattr(adw_watch.git_helper, "is_repo", lambda: False)
    monkeypatch.setattr(adw_watch.git_helper, "is_dirty", explode)
    monkeypatch.setattr(adw_watch.git_helper, "commit_all", explode)

    adw_watch.commit_watcher_state("claim something")

    assert "not a git repo" in capsys.readouterr().out


def test_commit_watcher_state_says_it_once_not_per_call(monkeypatch, capsys):
    # dispatch() calls this up to three times per issue; a repeated line would
    # train the operator to ignore it.
    monkeypatch.setattr(adw_watch, "_warned_not_a_repo", False)
    monkeypatch.setattr(adw_watch.git_helper, "is_repo", lambda: False)

    for _ in range(3):
        adw_watch.commit_watcher_state("x")

    assert capsys.readouterr().out.count("not a git repo") == 1


def test_dispatch_completes_in_a_git_free_repo(tmp_path, monkeypatch):
    # End to end: the local tracker must still claim, dispatch and resolve
    # when there is no git at all. Previously this errored on the first claim.
    issues_dir = tmp_path / "feature" / "issues"
    path = make_issue(issues_dir, "01-a", "ready-for-agent")
    issue = adw_watch.discover_issues(tmp_path)[0]
    monkeypatch.setattr(adw_watch, "_warned_not_a_repo", False)
    monkeypatch.setattr(adw_watch.git_helper, "is_repo", lambda: False)
    monkeypatch.setattr(adw_watch.adw_simple_sdlc, "main", lambda *a, **kw: 0)

    ok, adw_id = adw_watch.dispatch(issue, "cfg.yaml")

    assert ok is True
    assert "Status: resolved" in path.read_text()


# ══════════════════════════════════════════════════════════════════════════
# Filtered comment inclusion in the remote dispatch prompt (#21).
# Body-only meant a requirement appended as a comment never reached the
# planner, the run went green, and the issue closed with the delta
# unexecuted. The LOCAL tracker never had this problem (resolve_prompt reads
# the whole file, `## Comments` included), so this was a divergence remote
# dispatch introduced.
# ══════════════════════════════════════════════════════════════════════════

def gh_comments(*bodies_by_author):
    import json as _json
    rows = [{"author": {"login": a}, "body": b} for a, b in bodies_by_author]
    return {("gh", "issue", "view"): (0, _json.dumps({"comments": rows}))}


def issue7(**kw):
    base = dict(path=None, number="7", feature="", status="ready-for-agent",
                blocked_by=[], title="Add the thing", body="Do it well.")
    base.update(kw)
    return adw_watch.Issue(**base)


def test_a_human_comment_reaches_the_prompt():
    run, _ = fake_runner({**GH_AUTH_OK,
                          **gh_comments(("alice", "Also handle the empty case."))})
    prompt = adw_watch.GitHubTracker(run).prompt_for(issue7())

    assert "Do it well." in prompt                 # body still there
    assert "Also handle the empty case." in prompt  # and the delta
    assert "@alice" in prompt


def test_the_prompt_states_that_the_body_is_the_contract():
    # Without a precedence rule the planner is left guessing which wins when
    # a comment contradicts the body.
    run, _ = fake_runner({**GH_AUTH_OK, **gh_comments(("alice", "Changed my mind."))})
    prompt = adw_watch.GitHubTracker(run).prompt_for(issue7())

    assert "CONTRACT" in prompt
    assert "LATER statement" in prompt


def test_the_watchers_own_status_notes_are_filtered_out():
    # The important one. Without this, a failed run's "flipped to
    # ready-for-human" note becomes input to the next attempt at the ticket.
    run, _ = fake_runner({**GH_AUTH_OK, **gh_comments(
        ("joystick", "> *just watch: session abc1234 failed (exit 1). Flipped to ready-for-human.*"),
        ("alice", "Keep this one."),
    )})
    prompt = adw_watch.GitHubTracker(run).prompt_for(issue7())

    assert "ready-for-human" not in prompt
    assert "Keep this one." in prompt


def test_ai_generated_triage_notes_are_filtered_out():
    # The `triage` skill mandates this disclaimer. Such notes are commentary
    # ABOUT the ticket, routinely longer than the ticket itself.
    run, _ = fake_runner({**GH_AUTH_OK, **gh_comments(
        ("joystick", "> *This was generated by AI during triage.*\n\nLots of analysis."),
    )})
    prompt = adw_watch.GitHubTracker(run).prompt_for(issue7())

    assert "Lots of analysis." not in prompt


def test_bot_comments_are_filtered_out():
    run, _ = fake_runner({**GH_AUTH_OK, **gh_comments(
        ("dependabot[bot]", "Bumped a dependency."),
        ("github-actions", "CI run finished."),
        ("alice", "Real requirement."),
    )})
    prompt = adw_watch.GitHubTracker(run).prompt_for(issue7())

    assert "Bumped a dependency." not in prompt
    assert "CI run finished." not in prompt
    assert "Real requirement." in prompt


def test_no_comments_section_when_nothing_survives_the_filter():
    run, _ = fake_runner({**GH_AUTH_OK, **gh_comments(
        ("joystick", "> *just watch: resolved by session abc1234.*"),
    )})
    prompt = adw_watch.GitHubTracker(run).prompt_for(issue7())

    assert "Comments on this issue" not in prompt


def test_prompt_is_body_only_when_there_are_no_comments():
    run, _ = fake_runner({**GH_AUTH_OK, **{("gh", "issue", "view"): (0, '{"comments":[]}')}})
    prompt = adw_watch.GitHubTracker(run).prompt_for(issue7())

    assert prompt.strip() == "# Add the thing\n\nDo it well."


def test_comment_read_failure_never_breaks_the_dispatch(capsys):
    # The body is the contract and is already in hand -- failing the whole
    # dispatch because comments were unreadable would be a worse outcome.
    run, _ = fake_runner({**GH_AUTH_OK,
                          **{("gh", "issue", "view"): (1, "API rate limit exceeded")}})
    prompt = adw_watch.GitHubTracker(run).prompt_for(issue7())

    assert "Do it well." in prompt
    assert "could not read comments" in capsys.readouterr().err


def test_malformed_comment_json_degrades_to_body_only():
    run, _ = fake_runner({**GH_AUTH_OK,
                          **{("gh", "issue", "view"): (0, "not json at all")}})
    prompt = adw_watch.GitHubTracker(run).prompt_for(issue7())

    assert "Do it well." in prompt


def test_include_comment_rejects_an_empty_body():
    assert adw_watch.GitHubTracker.include_comment("alice", "   \n") is False


def test_comments_ride_through_a_real_dispatch(monkeypatch):
    # The end-to-end point of #21: what the SDLC chain is actually handed.
    run, _ = fake_runner({**GH_AUTH_OK,
                          **gh_comments(("alice", "Also handle the empty case."))})
    seen = {}
    monkeypatch.setattr(adw_watch.adw_simple_sdlc, "main",
                        lambda prompt, **kw: seen.setdefault("prompt", prompt) and 0 or 0)

    adw_watch.dispatch(issue7(), "cfg.yaml", adw_watch.GitHubTracker(run))

    assert "Also handle the empty case." in seen["prompt"]
