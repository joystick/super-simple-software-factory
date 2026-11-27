#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic", "python-dotenv", "pyyaml", "rich"]
# ///
"""ADW Simple SDLC — plan, build, test, review, document, committing as it goes.

Usage:
    uv run adws/adw_simple_sdlc.py "<prompt or path/to/prompt.md>" [--config adws/adw_sssf_config/sssf.config.yaml] [--adw-id a1b2c3d4]

Phases: engineer(request) -> planner -> git(commit_plan)
        -> builder -> code(test) [-> builder(fix) -> code(test) ... bounded]
        -> reviewer [-> builder(revise) -> reviewer ... bounded]
        -> code(retest, only if a revision changed code)
        -> git(commit_build) -> code(changes) -> documenter -> git(commit_docs)

Three commits, three work products, three authors. The plan, the code, and the
write-up each land in their own commit, and each commit message is the words of
the agent that produced it — `commit_message` on PlanOutput describes the spec,
on BuildOutput the code, on DocumentOutput the write-up. No agent's sentence is
ever reused for another agent's diff.

Testing is CODE, not an agent. `bun test` is a command, not a judgement call:
an agent rediscovering it every run costs a million tokens to learn what a
subprocess already knows. Failures travel back to the builder as an envelope,
so the repair loop is unchanged — only the runner became free and repeatable.

Two different questions still get asked, in order. The suite asks "does it
run"; the reviewer asks "is this what was asked for", against `plan.md` — and
neither can answer the other's. A revision that closes a review finding
re-enters the suite, so the tree that gets committed is the tree that was both
tested and approved.

The code commit lands after verification, not straight after the build: fixes
and revisions are part of the same work product, and red code has no business
on the branch. A run that fails verification therefore leaves the plan
committed and the working tree dirty — the spec is a real artifact either way,
and the unfinished code stays where the engineer can see it.

The documenter measures against the commit this run STARTED from, not against
`main`, because by then the run has moved `main` itself. That baseline is
pinned before the first commit phase and printed in the request phase.
"""

import argparse
import sys

from adw_modules import agents, changes, gates, git_helper, quality, session, utils
from adw_modules.data_types import (AgentCall, BuildOutput, ChangeCapture,
                                    DocumentOutput, PhaseParams, PlanOutput,
                                    ReviewOutput)

REQUIRED_AGENTS = ["planner", "builder", "reviewer", "documenter"]
MAX_FIX_LOOPS = 3
MAX_REVISION_LOOPS = 2

DOCUMENT_NOTES = ("Read diff_path in full before writing. Document only what the "
                  "diff shows, then copy the write-up into app_docs/ as your task "
                  "describes.")


COMMIT = "commit"
SKIP_NO_CHANGES = "skip-no-changes"
CLAIMS_MISMATCH = "claims-mismatch"


def classify_build_landing(tree_is_dirty: bool, claimed_files: list[str]) -> str:
    """What should commit_build do? Pure, so it can be tested without a run.

    Three outcomes, and the third is the reason this is not just
    `if is_dirty()`:

    * COMMIT -- the builder changed files. Normal path.
    * SKIP_NO_CHANGES -- clean tree AND the builder claimed nothing. The
      planner correctly finding the work already done is a FEATURE: its own
      system prompt tells it to scope to the delta and not re-touch what
      exists. The reviewer can still approve ("6/6 requirements already met
      by existing code"). Previously the only outcome here was
      git_helper.commit_all() raising "nothing to commit" -- a hard crash on
      a successful run (#19).
    * CLAIMS_MISMATCH -- clean tree but the builder claimed files it changed.
      That is a builder reporting work it did not do, and it must stay a
      failure. `gates.diff_matches_claims` does NOT catch it: that gate only
      asserts each claimed file EXISTS, so naming an untouched file that
      happens to exist passes it. Before this split, the generic "nothing to
      commit" error masked this case as the same thing as a legitimate no-op.
    """
    if tree_is_dirty:
        return COMMIT
    return CLAIMS_MISMATCH if claimed_files else SKIP_NO_CHANGES


def main(prompt: str, config: str = "adws/adw_sssf_config/sssf.config.yaml", adw_id: str | None = None) -> int:
    cfg = agents.load_config(config)
    agents.validate(cfg, REQUIRED_AGENTS)
    run = session.ensure(cfg, adw_id)
    baseline = git_helper.rev("HEAD")     # pinned before this run commits anything

    def commit(ph, envelope) -> None:
        """Commit what the preceding phase produced, in that agent's own words."""
        message = envelope.commit_message or f"sssf({run.adw_id}): {envelope.summary}"
        ph.log(sha=git_helper.commit_all(message), message=message)

    def record(ph, result) -> None:
        """Log a deterministic block's verdict — the same shape every ADW uses."""
        passed = sum(1 for check in result.checks if check.passed)
        ph.log(passed=result.passed, checks=f"{passed}/{len(result.checks)}",
               artifacts=", ".join(result.artifacts))

    with run.phase(PhaseParams(name="request", kind="engineer", owner=run.engineer,
                               description="Capture the incoming ask")) as ph:
        ph.log(input=prompt, baseline=git_helper.short_sha(baseline))

    with run.phase(PhaseParams(name="plan", kind="agent", owner="planner",
                               description="Turn the request into an implementable plan")) as ph:
        plan = ph.call(AgentCall(output_type=PlanOutput, prompt=prompt,
                                 gates=[gates.artifacts_exist, gates.files_non_empty]))

    with run.phase(PhaseParams(name="commit_plan", kind="code", owner="git",
                               description="Put the spec on record before any code exists to blur it")) as ph:
        commit(ph, plan)

    with run.phase(PhaseParams(name="build", kind="agent", owner="builder",
                               description="Implement the plan exactly")) as ph:
        build = ph.call(AgentCall(output_type=BuildOutput, prompt=prompt, previous=plan,
                                  gates=[gates.diff_matches_claims]))

    test = None
    for i in range(1, MAX_FIX_LOOPS + 1):
        with run.phase(PhaseParams(name=f"test_{i}", kind="code", owner="quality",
                                   description="Run the suite — a known command, so code runs "
                                               "it and no agent has to rediscover it")) as ph:
            test = quality.run_tests(run)
            record(ph, test)

        if test.passed:
            break

        with run.phase(PhaseParams(name=f"fix_{i}", kind="agent", owner="builder", retries=1,
                                   description="Repair what the suite reported, from its "
                                               "verbatim output")) as ph:
            build = ph.call(AgentCall(output_type=BuildOutput, prompt=prompt,
                                      previous=quality.as_envelope(test, "tests"),
                                      gates=[gates.diff_matches_claims]))

    review = None
    revised = False
    for i in range(1, MAX_REVISION_LOOPS + 1):
        with run.phase(PhaseParams(name=f"review_{i}", kind="agent", owner="reviewer",
                                   description="Confirm the build matches the plan")) as ph:
            review = ph.call(AgentCall(output_type=ReviewOutput, prompt=prompt, previous=build,
                                       gates=[gates.artifacts_exist, gates.verdict_consistent]))

        if review.approved or i == MAX_REVISION_LOOPS:
            break

        with run.phase(PhaseParams(name=f"revise_{i}", kind="agent", owner="builder", retries=1,
                                   description="Close the reviewer's blocking findings")) as ph:
            build = ph.call(AgentCall(output_type=BuildOutput, prompt=prompt, previous=review,
                                      gates=[gates.diff_matches_claims]))
            revised = True

    # A revision edited code after the suite last ran, so the green light is
    # stale. Re-run it rather than commit on a result that predates the change.
    if revised and review is not None and review.approved:
        with run.phase(PhaseParams(name="retest", kind="code", owner="quality",
                                   description="Re-run the suite — the revision changed code "
                                               "after the last green result")) as ph:
            test = quality.run_tests(run)
            record(ph, test)

    # Red tests or a rejected review stop the chain here: the code stays
    # uncommitted and nothing is documented, because there is nothing worth
    # describing yet. The plan commit stands — it is a record of what was asked.
    verified = (test is not None and test.passed
                and review is not None and review.approved)
    landed = False
    if verified:
        with run.phase(PhaseParams(name="commit_build", kind="code", owner="git",
                                   description="Land the code only now: green suite, approved review")) as ph:
            # In a non-repo, fall through to commit_all()'s own clear
            # "not a git repository" error rather than asking is_dirty()
            # first, which would raise something far less useful.
            dirty = (not git_helper.is_repo()) or git_helper.is_dirty()
            claimed = list(getattr(build, "changed_files", []) or [])
            decision = classify_build_landing(dirty, claimed)
            if decision == COMMIT:
                commit(ph, build)
                landed = True
            elif decision == CLAIMS_MISMATCH:
                raise RuntimeError(
                    "the builder reported changed files but the working tree is "
                    f"clean: {', '.join(claimed)}. gates.diff_matches_claims only "
                    "checks those paths EXIST, so naming an untouched file passes "
                    "it. Treat this as a failed build, not an empty one.")
            else:
                ph.log(skipped="nothing to commit",
                       reason="the builder correctly changed nothing — the "
                              "requested work was already done (#19)")

    # Everything below describes a change. On a legitimate no-op there is
    # nothing to diff and nothing to write up, so the whole documentation
    # branch is skipped rather than fed an empty changeset. This is also why
    # the `changes` phase can keep RAISING on an empty diff: reaching it now
    # means a commit really did land and produced no diff, which is a genuine
    # inconsistency, not the already-done case (#19).
    if verified and landed:
        with run.phase(PhaseParams(name="changes", kind="code", owner="git",
                                   description="Diff the whole run against its pinned baseline, for the documenter")) as ph:
            changeset = changes.capture(run, ChangeCapture(base=baseline))
            ph.log(base=f"{changeset.base.label} @ {changeset.base.commit[:7]}",
                   reason=changeset.base.reason,
                   files=len(changeset.files) + len(changeset.untracked),
                   lines=f"+{changeset.insertions} -{changeset.deletions}",
                   diff=changeset.diff_path)
            if changeset.empty:
                raise RuntimeError(
                    f"nothing changed since {changeset.base.label} "
                    f"({changeset.base.reason}) — there is nothing to document.")

        with run.phase(PhaseParams(name="document", kind="agent", owner="documenter", retries=1,
                                   description="Write up the completed change")) as ph:
            document = ph.call(AgentCall(output_type=DocumentOutput, prompt=prompt,
                                         previous=changes.as_envelope(changeset, DOCUMENT_NOTES),
                                         gates=[gates.artifacts_exist, gates.files_non_empty]))

        with run.phase(PhaseParams(name="commit_docs", kind="code", owner="git",
                                   description="Ship the write-up in its own commit, beside the code it describes")) as ph:
            commit(ph, document)

    return run.finish(accepted=verified,
                      reason="the suite or the review never came back clean")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", help="inline text or a path to a prompt file")
    parser.add_argument("--config", default="adws/adw_sssf_config/sssf.config.yaml")
    parser.add_argument("--adw-id", default=None, help="join or pin an existing session")
    args = parser.parse_args()
    sys.exit(main(utils.resolve_prompt(args.prompt), args.config, args.adw_id))
