"""adw_simple_sdlc.classify_build_landing -- what commit_build does when the
working tree is clean (issue #19).

The planner correctly discovering that the requested work is already done,
and instructing the builder to change nothing, is a FEATURE. Before #19 the
only outcome in that case was git_helper.commit_all() raising "nothing to
commit" -- a hard crash on a run where the tests passed and the reviewer
approved.
"""

from __future__ import annotations

import adw_simple_sdlc as sdlc


def test_dirty_tree_commits():
    assert sdlc.classify_build_landing(True, ["src/a.py"]) == sdlc.COMMIT


def test_dirty_tree_commits_even_with_no_claims():
    # The builder under-reporting is not this function's problem; something
    # changed, so it must be committed rather than silently dropped.
    assert sdlc.classify_build_landing(True, []) == sdlc.COMMIT


def test_clean_tree_with_no_claims_is_a_legitimate_no_op():
    # The already-done case. Previously a crash.
    assert sdlc.classify_build_landing(False, []) == sdlc.SKIP_NO_CHANGES


def test_clean_tree_with_claims_is_a_failure_not_an_empty_build():
    # A builder reporting work it did not do. gates.diff_matches_claims does
    # NOT catch this: it only asserts each claimed path EXISTS, so naming an
    # untouched file that happens to exist passes the gate. Before #19 the
    # generic "nothing to commit" error masked this as the same thing as a
    # legitimate no-op.
    assert sdlc.classify_build_landing(False, ["src/untouched.py"]) == sdlc.CLAIMS_MISMATCH


def test_none_claims_is_treated_as_no_claims():
    # getattr(build, "changed_files", []) can legitimately yield None from a
    # partially-populated envelope; it must not be mistaken for a claim.
    assert sdlc.classify_build_landing(False, list([] or [])) == sdlc.SKIP_NO_CHANGES


def test_the_three_outcomes_are_distinct_constants():
    # Guards against a careless refactor collapsing two of them into one
    # string, which would silently turn a mismatch into a skip.
    assert len({sdlc.COMMIT, sdlc.SKIP_NO_CHANGES, sdlc.CLAIMS_MISMATCH}) == 3
