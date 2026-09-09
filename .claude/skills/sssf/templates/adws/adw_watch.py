#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic", "python-dotenv", "pyyaml", "rich"]
# ///
"""ADW Watch -- `just sssf`: scan the issue tracker for ready-for-agent work,
claim the frontier, and dispatch it through the full SDLC chain.

Usage:
    uv run adws/adw_watch.py --once
    uv run adws/adw_watch.py [--interval 300] [--config adws/adw_sssf_config/sssf.config.yaml]
        [--scratch-dir .scratch]

Local-markdown tracker only (docs/agents/issue-tracker.md). A GitHub or
GitLab tracker is detected and refused with a clear error rather than
silently finding nothing -- that path needs `gh`/`glab` wiring this script
does not have yet.

This is the headless half of the dark-factory queue (see the adoption
playbook's Part D). The judgment call -- is this issue feasible, compatible
with what's already live, compliant, secure -- is NOT this script's job. It
only ever claims issues already carrying `Status: ready-for-agent`, a state
that should only be reached by an interactive triage session (the `triage`
skill, if installed) posting a durable agent brief. This script trusts that
gate; it does not re-check it.

Two status vocabularies meet here, on purpose: `triage`'s five canonical
states (needs-triage / needs-info / ready-for-agent / ready-for-human /
wontfix) get an issue TO ready-for-agent; this script then reuses wayfinder's
own claimed/resolved vocabulary to track its OWN work on top of that state,
same convention as `.scratch/<effort>/issues/NN-<slug>.md` ticket files
wayfinder already uses. A failed run flips back to `ready-for-human` (a
triage state) rather than sitting `claimed` forever, so a person sees it.

--once runs a single scan-claim-dispatch-resolve cycle then exits: 0 if work
was found and dispatched (regardless of outcome -- check the issue's new
Status to know which), 1 if the queue was empty, 2 if the tracker isn't
local-markdown. That's the right mode for cron/launchd. Without --once, loops
on --interval seconds.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import adw_plan_build_test
from adw_modules import utils

STATUS_RE = re.compile(r"^Status:\s*(\S+)", re.MULTILINE)
BLOCKED_BY_RE = re.compile(r"^Blocked by:\s*(.+)$", re.MULTILINE)

READY = "ready-for-agent"
CLAIMED = "claimed"
RESOLVED = "resolved"
FAILED_STATE = "ready-for-human"


@dataclass
class Issue:
    path: Path
    number: str      # "01" from "01-slug.md" -- unique only WITHIN a feature dir
    feature: str      # the .scratch/<feature-slug>/ this belongs to
    status: str
    blocked_by: list[str]


def read_status(text: str) -> str | None:
    m = STATUS_RE.search(text)
    return m.group(1) if m else None


def read_blocked_by(text: str) -> list[str]:
    m = BLOCKED_BY_RE.search(text)
    if not m:
        return []
    return [b.strip() for b in m.group(1).split(",") if b.strip()]


def discover_issues(scratch_dir: Path) -> list[Issue]:
    """Every `.scratch/<feature>/issues/*.md` file that carries a Status: line.
    A file with no Status: is not a tracked issue -- skip it rather than guess.
    """
    issues: list[Issue] = []
    if not scratch_dir.is_dir():
        return issues
    for feature_dir in sorted(scratch_dir.iterdir()):
        issues_dir = feature_dir / "issues"
        if not issues_dir.is_dir():
            continue
        for f in sorted(issues_dir.glob("*.md")):
            text = f.read_text()
            status = read_status(text)
            if status is None:
                continue
            number = f.stem.split("-", 1)[0]
            issues.append(Issue(path=f, number=number, feature=feature_dir.name,
                                status=status, blocked_by=read_blocked_by(text)))
    return issues


def group_by_feature(issues: list[Issue]) -> dict[str, dict[str, Issue]]:
    """Blocked-by numbers are only unique within one feature dir -- group
    before resolving them so a "01" in one feature never blocks against
    another feature's "01"."""
    groups: dict[str, dict[str, Issue]] = {}
    for i in issues:
        groups.setdefault(i.feature, {})[i.number] = i
    return groups


def is_unblocked(issue: Issue, siblings: dict[str, Issue]) -> bool:
    for b in issue.blocked_by:
        blocker = siblings.get(b)
        if blocker is None or blocker.status != RESOLVED:
            return False
    return True


def frontier(issues: list[Issue]) -> Issue | None:
    """The next issue to claim: ready-for-agent, every blocker resolved,
    lowest (feature, number) first -- same "first by number wins" rule
    wayfinder uses for its own frontier."""
    groups = group_by_feature(issues)
    candidates = [i for i in issues if i.status == READY and is_unblocked(i, groups[i.feature])]
    if not candidates:
        return None
    candidates.sort(key=lambda i: (i.feature, i.number))
    return candidates[0]


def set_status(path: Path, new_status: str) -> None:
    text = path.read_text()
    if STATUS_RE.search(text):
        text = STATUS_RE.sub(f"Status: {new_status}", text, count=1)
    else:
        text = f"Status: {new_status}\n\n" + text
    path.write_text(text)


def append_comment(path: Path, note: str) -> None:
    text = path.read_text().rstrip("\n")
    if "## Comments" not in text:
        text += "\n\n## Comments"
    path.write_text(text + f"\n\n{note}\n")


def dispatch(issue: Issue, config: str) -> tuple[bool, str]:
    """Claim, run the full SDLC chain with this issue's own body as the
    prompt, then resolve or flip to ready-for-human. Returns (succeeded, adw_id).
    """
    set_status(issue.path, CLAIMED)
    adw_id = utils.new_id()
    prompt = utils.resolve_prompt(str(issue.path))
    try:
        exit_code = adw_plan_build_test.main(prompt, config=config, adw_id=adw_id)
    except Exception as exc:  # a crash here is a failed run, not a watcher crash
        set_status(issue.path, FAILED_STATE)
        append_comment(issue.path, f"> *just sssf: session `{adw_id}` crashed: {exc}*")
        return False, adw_id

    if exit_code == 0:
        set_status(issue.path, RESOLVED)
        append_comment(issue.path, f"> *just sssf: resolved by session `{adw_id}`.*")
        return True, adw_id

    set_status(issue.path, FAILED_STATE)
    append_comment(
        issue.path,
        f"> *just sssf: session `{adw_id}` failed (exit {exit_code}). "
        f"Flipped to ready-for-human -- see `just phases {adw_id}` for what broke.*",
    )
    return False, adw_id


def detect_tracker(root: Path) -> str:
    doc = root / "docs" / "agents" / "issue-tracker.md"
    if doc.is_file():
        text = doc.read_text()
        first_line = text.splitlines()[0] if text.strip() else ""
        if "GitHub" in first_line:
            return "github"
        if "GitLab" in first_line:
            return "gitlab"
        if "Local Markdown" in first_line:
            return "local"
    return "local" if (root / ".scratch").is_dir() else "unknown"


def run_once(scratch_dir: Path, config: str) -> bool:
    """One scan-claim-dispatch-resolve cycle. Returns True if work was found
    and dispatched (regardless of outcome), False if the queue was empty."""
    issues = discover_issues(scratch_dir)
    next_issue = frontier(issues)
    if next_issue is None:
        print("just sssf: queue empty -- nothing ready-for-agent and unblocked")
        return False
    print(f"just sssf: claiming {next_issue.path}")
    ok, adw_id = dispatch(next_issue, config)
    print(f"just sssf: session {adw_id} {'succeeded' if ok else 'FAILED'} -- {next_issue.path}")
    return True


def main(scratch_dir: str, config: str, once: bool, interval: int) -> int:
    root = Path.cwd()
    tracker = detect_tracker(root)
    if tracker != "local":
        print(
            f"just sssf: {tracker} issue tracker detected -- not implemented yet. "
            "This watcher only supports the local-markdown tracker "
            "(docs/agents/issue-tracker.md). See Part D of the adoption playbook.",
            file=sys.stderr,
        )
        return 2

    path = Path(scratch_dir)
    if once:
        return 0 if run_once(path, config) else 1
    while True:
        run_once(path, config)
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="adws/adw_sssf_config/sssf.config.yaml")
    parser.add_argument("--scratch-dir", default=".scratch")
    parser.add_argument("--once", action="store_true",
                        help="one scan-claim-dispatch-resolve cycle, then exit "
                             "(0 dispatched, 1 empty queue, 2 unsupported tracker) -- "
                             "the right mode for cron/launchd")
    parser.add_argument("--interval", type=int, default=300,
                        help="seconds between scans when not --once (default 300)")
    args = parser.parse_args()
    sys.exit(main(args.scratch_dir, args.config, args.once, args.interval))
