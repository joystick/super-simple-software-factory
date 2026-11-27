#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic", "python-dotenv", "pyyaml", "rich"]
# ///
"""ADW Watch -- `just watch`: scan the issue tracker for ready-for-agent work,
claim the frontier, and dispatch it through the full SDLC chain (planner ->
builder -> reviewer -> revision loop -> documenter -> commit --
adw_simple_sdlc.py, not the lighter plan_build_test chain -- an unattended
queue dispatch gets no other independent check besides the test gate, so it
needs the review/revision loop a supervised manual run could otherwise skip).

Usage:
    uv run adws/adw_watch.py --once
    uv run adws/adw_watch.py [--interval 300] [--config adws/adw_sssf_config/sssf.config.yaml]
        [--scratch-dir .scratch]

Tracker-agnostic as of 2026-11-27 (issue #20). `detect_tracker()` reads
docs/agents/issue-tracker.md and selects one of three adapters, all sharing
the same claim -> dispatch -> resolve protocol:

    local   .scratch/<feature>/issues/NN-slug.md, and the older
            .scratch/<feature>/issue.md single-file-per-feature shape
    github  `gh`   -- status is labels; a blocker is resolved when closed
    gitlab  `glab` -- same, with GitLab's own label/close vocabulary

Whichever is selected, a MISSING or UNAUTHENTICATED CLI exits 2 with a clear
message. It never falls through to an empty queue: "looks like an empty
queue" was the original bug here (HANDOFF item 3) and is strictly worse than
an error, because an operator reads it as "no work to do".

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

Every status write (claim, resolve, or fail) is committed immediately -- the
ADW's own commit phase fires mid-run, before this script's final write, so
without this the last status transition would sit uncommitted after every
run. Because claiming commits, `run_once` refuses to claim anything against
a dirty working tree: an unrelated in-progress change sitting there would get
swept into that commit, same `git add -A` gotcha every ADW commit phase
carries.

--once runs a single scan-claim-dispatch-resolve cycle then exits: 0 if work
was found and dispatched (regardless of outcome -- check the issue's new
Status to know which), 1 if the queue was empty, 2 if the tracker isn't
local-markdown. That's the right mode for cron/launchd. Without --once, loops
on --interval seconds.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import adw_simple_sdlc
from adw_modules import git_helper, utils

# \*{0,2} tolerates the two real forms seen in the wild: plain "Status: X"
# (this script's own set_status() writes) and "**Status:** X" (to-tickets'
# own local-ticket-template, per its SKILL.md, uses bold) -- found live,
# 2026-09-14, when to-tickets published four portfinder tickets entirely in
# bold and every one of them was silently invisible to the frontier scan.
# It does NOT tolerate arbitrary other markup (underscores, backticks,
# missing colon) on purpose -- see _check_format() below, which flags those
# loudly instead of silently accepting or silently ignoring them.
STATUS_RE = re.compile(r"^\*{0,2}Status:\*{0,2}[ \t]*(\S+)", re.MULTILINE)
BLOCKED_BY_RE = re.compile(r"^\*{0,2}Blocked by:\*{0,2}[ \t]*(.+)$", re.MULTILINE)

# A line that looks LIKE it's trying to declare Status:/Blocked by: (starts
# the line with the word, optionally markdown-wrapped) but isn't in one of
# the two forms STATUS_RE/BLOCKED_BY_RE actually accept -- underscore
# emphasis, a missing colon, wrong casing, or some other markup an agent
# reached for. [*_\s]{0,3} on purpose, not \W*: \W excludes underscore
# (it's a word character in Python's re), so a naive \W*-based near-miss
# detector silently passed "_Status_:" straight through undetected -- the
# exact silent-failure shape this detector exists to prevent, just one
# level up. No colon required either, so a missing-colon line ("Status
# ready-for-agent") is caught too. Scoped to issues/*.md files only (never
# spec.md/map.md/plan.md), where a line this specific is never incidental
# prose. No trailing \b either: \b needs a word/non-word transition, and
# underscore IS a word character, so "Status_: ..." (closing underscore
# emphasis right after the word) has no boundary there and would silently
# pass a \b-anchored version straight through -- caught testing this exact
# detector against itself.
# Known gap, not yet closed: a backtick-wrapped `Status:` matches neither
# STATUS_RE nor this near-miss detector ([*_\s]{0,3} doesn't include the
# backtick character), so that one specific markup choice is still a silent
# skip, not a loud warning -- found while writing docs/training's queue
# lessons, 2026-09-24. Author advice: use plain or **bold**, never backticks.
_STATUS_NEAR_MISS_RE = re.compile(r"^[*_\s]{0,3}status", re.MULTILINE | re.IGNORECASE)
_BLOCKED_BY_NEAR_MISS_RE = re.compile(r"^[*_\s]{0,3}blocked\s+by", re.MULTILINE | re.IGNORECASE)

READY = "ready-for-agent"
CLAIMED = "claimed"
RESOLVED = "resolved"
FAILED_STATE = "ready-for-human"


@dataclass
class Issue:
    path: Path | None  # the ticket file (local trackers); None for remote ones
    number: str      # "01" from "01-slug.md" -- unique only WITHIN a feature dir
    feature: str      # the .scratch/<feature-slug>/ this belongs to
    status: str
    blocked_by: list[str]
    # Remote trackers have no file and no feature dimension. `feature` is ""
    # for them, which group_by_feature() collapses into a single global
    # namespace -- matching how "#42" actually behaves on GitHub/GitLab.
    title: str = ""
    body: str = ""

    def __str__(self) -> str:
        """What the operator sees in every log line and commit message."""
        return str(self.path) if self.path is not None else f"#{self.number}"


def read_status(text: str) -> str | None:
    m = STATUS_RE.search(text)
    return m.group(1) if m else None


_NONE_RE = re.compile(r"^none\b|^n/a\b", re.IGNORECASE)
_TICKET_NUMBER_RE = re.compile(r"^\d+$")


def read_blocked_by(text: str, path: Path | None = None) -> list[str]:
    m = BLOCKED_BY_RE.search(text)
    if not m:
        return []
    # Strip parenthetical annotations BEFORE splitting on commas -- a comma
    # inside a parenthetical ("(none -- API exists, see spec.md)") used to
    # get comma-split first, producing two broken tokens ("none -- API
    # exists" and "see spec.md)") instead of one. Parens don't nest here, so
    # a single non-greedy sub over the whole value is safe and simpler than
    # re-deriving this per split token.
    value = re.sub(r"\s*\([^)]*\)", "", m.group(1))
    tokens = (b.strip() for b in value.split(","))
    result = []
    for raw in tokens:
        if not raw:
            continue
        cleaned = raw.rstrip(".;:,").strip()
        if not cleaned or _NONE_RE.match(cleaned):
            # "None" (with or without an explanatory parenthetical) means no
            # blocker, same as omitting the line -- found live: "None
            # (port_directory tables ship; this only reads them)." was being
            # kept as one literal unmatched-forever token, so an explicitly
            # UNblocked ticket sat permanently invisible to the frontier,
            # identical in effect to the bug this was meant to fix the first
            # time. The playbook's own "no real blocker -> omit the line
            # entirely" convention is still correct authoring advice; this
            # is defense for when that advice isn't followed.
            continue
        if not _TICKET_NUMBER_RE.match(cleaned) and path is not None:
            print(f"just watch: WARNING -- {path} has a Blocked by: value "
                  f"{cleaned!r} that doesn't look like a bare ticket number "
                  "after cleanup. It will be kept as a blocker (safe default:"
                  " never silently unblocks something that might genuinely "
                  "be blocked) but will never resolve, so this ticket is "
                  "stuck at ready-for-agent forever until the line is fixed.",
                  file=sys.stderr)
        result.append(cleaned)
    return result


def _check_format(text: str, path: Path) -> None:
    """Warn loudly -- never silently -- when a Status:/Blocked by: line
    looks intended but doesn't match either canonical form (plain or
    **bold**). Never raises: one malformed ticket must not take the whole
    queue down, but it must never again fail invisibly either -- that was
    the actual bug (four real tickets silently missing from the frontier
    scan, `just watch` reporting a clean "queue empty" with no error at
    all)."""
    if _STATUS_NEAR_MISS_RE.search(text) and not STATUS_RE.search(text):
        print(f"just watch: WARNING -- {path} has a Status:-like line that "
              "doesn't match the canonical 'Status: X' or '**Status:** X' "
              "form. This ticket is INVISIBLE to the frontier scan until "
              "fixed.", file=sys.stderr)
    if _BLOCKED_BY_NEAR_MISS_RE.search(text) and not BLOCKED_BY_RE.search(text):
        print(f"just watch: WARNING -- {path} has a Blocked by:-like line "
              "that doesn't match the canonical 'Blocked by: NN' or "
              "'**Blocked by:** NN' form. Blocking will not be honored for "
              "this ticket.", file=sys.stderr)


def discover_issues(scratch_dir: Path) -> list[Issue]:
    """Every `.scratch/<feature>/issues/*.md` file that carries a Status: line
    in either canonical form (plain or **bold**; see STATUS_RE). A file with
    neither is not a tracked issue -- skip it rather than guess -- but first
    check whether it merely LOOKS like one that's malformed (_check_format):
    that gets a loud warning instead of a silent skip.
    """
    issues: list[Issue] = []
    if not scratch_dir.is_dir():
        return issues
    for feature_dir in sorted(scratch_dir.iterdir()):
        if not feature_dir.is_dir():
            continue
        issues_dir = feature_dir / "issues"
        if issues_dir.is_dir():
            for f in sorted(issues_dir.glob("*.md")):
                text = f.read_text()
                _check_format(text, f)
                status = read_status(text)
                if status is None:
                    continue
                number = f.stem.split("-", 1)[0]
                issues.append(Issue(path=f, number=number, feature=feature_dir.name,
                                    status=status, blocked_by=read_blocked_by(text, f)))
            continue
        # Older one-file-per-feature shape: .scratch/<feature>/issue.md, with
        # no issues/ dir and no NN- prefix. Predates Part D's convention and
        # is still what some adopter repos have. Previously these were found
        # by nothing at all and reported as an empty queue -- HANDOFF item 3,
        # "worse than the git problem, because it looks like an empty queue".
        # Numbered "01" so it is a well-formed single-ticket feature; nothing
        # can be blocked on a sibling that cannot exist.
        single = feature_dir / "issue.md"
        if single.is_file():
            text = single.read_text()
            _check_format(text, single)
            status = read_status(text)
            if status is not None:
                issues.append(Issue(path=single, number="01",
                                    feature=feature_dir.name, status=status,
                                    blocked_by=read_blocked_by(text, single)))
    return issues


def group_by_feature(issues: list[Issue]) -> dict[str, dict[str, Issue]]:
    """Blocked-by numbers are only unique within one feature dir -- group
    before resolving them so a "01" in one feature never blocks against
    another feature's "01"."""
    groups: dict[str, dict[str, Issue]] = {}
    for i in issues:
        groups.setdefault(i.feature, {})[i.number] = i
    return groups


def is_unblocked(issue: Issue, siblings: dict[str, Issue],
                 missing_means_resolved: bool = False) -> bool:
    """Every blocker resolved?

    `missing_means_resolved` inverts the treatment of a blocker that isn't in
    the discovered set, and the two tracker families genuinely need opposite
    answers here:

    * **Local (False, the default).** Every ticket file is discovered
      regardless of status, so a blocker we cannot find is a typo or a
      dangling reference. Treat it as still blocking -- never silently
      unblock something that might genuinely be blocked.
    * **Remote (True).** `gh`/`glab` are queried for OPEN issues only, so a
      blocker's *absence* is precisely the evidence that it closed, i.e. that
      it is done. Treating absence as blocking there would deadlock the whole
      queue the moment a blocker was legitimately closed.

    Getting this backwards fails silently in both directions, which is why
    it's a parameter rather than something inferred inside the loop.
    """
    for b in issue.blocked_by:
        blocker = siblings.get(b)
        if blocker is None:
            if missing_means_resolved:
                continue
            return False
        if blocker.status != RESOLVED:
            return False
    return True


def _order_key(issue: Issue) -> tuple[str, int, str]:
    """Sort key for the frontier. Numeric when the number is all digits, so
    "#10" sorts after "#9" -- a plain string sort puts "10" first, which only
    shows up once a tracker passes double digits (local tickets are
    zero-padded "01".."09" and hid this)."""
    n = issue.number
    return (issue.feature, int(n) if n.isdigit() else 1 << 30, n)


def frontier(issues: list[Issue], missing_means_resolved: bool = False) -> Issue | None:
    """The next issue to claim: ready-for-agent, every blocker resolved,
    lowest (feature, number) first -- same "first by number wins" rule
    wayfinder uses for its own frontier."""
    groups = group_by_feature(issues)
    candidates = [i for i in issues
                  if i.status == READY
                  and is_unblocked(i, groups[i.feature], missing_means_resolved)]
    if not candidates:
        return None
    candidates.sort(key=_order_key)
    return candidates[0]


def set_status(path: Path, new_status: str) -> None:
    text = path.read_text()
    m = STATUS_RE.search(text)
    if m:
        # Splice in only the captured value (group 1) -- preserve the key's
        # own formatting (plain "Status:" or **bold**) exactly as written.
        # A prior version replaced the WHOLE match with a hardcoded plain
        # "Status: X", silently stripping bold formatting on every
        # claim/resolve -- an unrequested side effect, not a deliberate
        # normalization: a ticket authored **Status:** should read
        # **Status:** claimed after the watcher claims it, not have its
        # formatting rewritten out from under it.
        text = text[:m.start(1)] + new_status + text[m.end(1):]
    else:
        text = f"Status: {new_status}\n\n" + text
    path.write_text(text)


def append_comment(path: Path, note: str) -> None:
    text = path.read_text().rstrip("\n")
    if "## Comments" not in text:
        text += "\n\n## Comments"
    path.write_text(text + f"\n\n{note}\n")


def commit_watcher_state(message: str) -> None:
    """Commit the watcher's own claim/resolve writes to the issue file.

    The ADW's own commit phase (inside adw_simple_sdlc.main) fires mid-run,
    before dispatch() writes the final Status: -- so without this, that final
    write sits uncommitted after every run, needing a manual follow-up commit.
    is_dirty() guards against there being nothing to commit (e.g. a crash
    before set_status ran)."""
    if git_helper.is_dirty():
        sha = git_helper.commit_all(message)
        print(f"just watch: committed watcher state ({sha}): {message}")


def dispatch(issue: Issue, config: str, tracker=None) -> tuple[bool, str]:
    """Claim, run the full SDLC chain with this issue's own body as the
    prompt, then resolve or flip to ready-for-human. Returns (succeeded, adw_id).

    `tracker` defaults to a LocalTracker rooted at the issue's own file, so
    existing callers (and the tests that pin this protocol) keep working
    unchanged.
    """
    if tracker is None:
        tracker = LocalTracker(issue.path.parent if issue.path else Path(".scratch"))
    set_status = tracker.set_status
    append_comment = tracker.append_comment
    commit_watcher_state = tracker.commit_state

    set_status(issue, CLAIMED)
    commit_watcher_state(f"just watch: claim {issue}")

    adw_id = utils.new_id()
    prompt = tracker.prompt_for(issue)
    try:
        exit_code = adw_simple_sdlc.main(prompt, config=config, adw_id=adw_id)
    except (Exception, SystemExit) as exc:
        # A crash here is a failed run, not a watcher crash -- SystemExit must be
        # caught explicitly alongside Exception: agents.validate() raises SystemExit
        # on a config problem (bad model string, missing prompt file, etc.), and
        # SystemExit inherits BaseException, not Exception, so a bare `except
        # Exception` never sees it. That let a config error crash the whole watcher
        # process, skipping this handler entirely and leaving the issue stuck at
        # Status: claimed with no resolution commit -- found live, 2026-09-10,
        # against a real malformed model string. KeyboardInterrupt (also
        # BaseException, not caught here) still propagates and stops the watcher,
        # which is the behavior an operator hitting Ctrl+C actually wants.
        set_status(issue, FAILED_STATE)
        append_comment(issue, f"> *just watch: session `{adw_id}` crashed: {exc}*")
        commit_watcher_state(f"just watch: session {adw_id} crashed -- flipped to ready-for-human")
        return False, adw_id

    if exit_code == 0:
        set_status(issue, RESOLVED)
        append_comment(issue, f"> *just watch: resolved by session `{adw_id}`.*")
        commit_watcher_state(f"just watch: resolve {issue} (session {adw_id})")
        return True, adw_id

    set_status(issue, FAILED_STATE)
    append_comment(
        issue,
        f"> *just watch: session `{adw_id}` failed (exit {exit_code}). "
        f"Flipped to ready-for-human -- see `just phases {adw_id}` for what broke.*",
    )
    commit_watcher_state(f"just watch: session {adw_id} failed -- flipped to ready-for-human")
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


# ── tracker adapters ──────────────────────────────────────────────────────
#
# One protocol, three implementations. Everything below the adapters (the
# frontier, dispatch, run_once) is written against this interface and never
# against a file path or a `gh` invocation:
#
#     discover()                  -> list[Issue]
#     set_status(issue, status)   -> None
#     append_comment(issue, note) -> None
#     commit_state(message)       -> None
#     prompt_for(issue)           -> str   (what the SDLC chain is handed)
#     missing_means_resolved      -> bool  (see is_unblocked)
#
# `preflight()` is the fail-closed gate: it must raise TrackerUnavailable if
# the tracker cannot be reached, so main() can exit 2 instead of reporting a
# falsely-empty queue.


class TrackerUnavailable(RuntimeError):
    """The selected tracker cannot be reached (CLI missing, unauthenticated,
    wrong directory). Always exit 2 -- never a silent empty queue."""


class LocalTracker:
    """`.scratch/<feature>/issues/NN-slug.md`, plus the older one-file-per-
    feature `.scratch/<feature>/issue.md` shape that predates Part D."""

    kind = "local"
    missing_means_resolved = False

    def __init__(self, scratch_dir: Path):
        self.scratch_dir = Path(scratch_dir)

    def preflight(self) -> None:
        # A missing .scratch/ is a legitimately empty queue here, not an
        # unavailable tracker -- discover() returns [] and run_once says so.
        return None

    def discover(self) -> list[Issue]:
        return discover_issues(self.scratch_dir)

    def set_status(self, issue: Issue, status: str) -> None:
        set_status(issue.path, status)

    def append_comment(self, issue: Issue, note: str) -> None:
        append_comment(issue.path, note)

    def commit_state(self, message: str) -> None:
        commit_watcher_state(message)

    def prompt_for(self, issue: Issue) -> str:
        return utils.resolve_prompt(str(issue.path))


class _CliTracker:
    """Shared behaviour for the two remote trackers. Subclasses supply the
    CLI name and the four verbs; everything else is identical."""

    missing_means_resolved = True

    def __init__(self, runner=None):
        # Injectable so tests never shell out. Returns (exit_code, stdout).
        self._run = runner if runner is not None else _run_cli

    def commit_state(self, message: str) -> None:
        """No-op. A label change is already durable on the server, so there
        is nothing local to commit -- and this is also what frees the remote
        trackers from adw_watch's old unconditional "must be a git repo"
        assumption (HANDOFF item 3's other half)."""
        return None

    def prompt_for(self, issue: Issue) -> str:
        return f"# {issue.title}\n\n{issue.body}\n"

    def _parse(self, payload: str) -> list[Issue]:
        data = json.loads(payload or "[]")
        issues: list[Issue] = []
        for row in data:
            number = str(row.get("number"))
            body = row.get("body") or ""
            # "#42" in a body -> "42", so the keys match discovered numbers.
            blockers = [b.lstrip("#") for b in read_blocked_by(body)]
            issues.append(Issue(
                path=None, number=number, feature="",
                status=self._status_from(row), blocked_by=blockers,
                title=row.get("title") or "", body=body,
            ))
        return issues

    def _status_from(self, row: dict) -> str:
        """Labels carry status on a remote tracker. READY only when the
        ready label is present AND no claimed label is -- a claimed issue
        must never be re-claimed by a second watcher."""
        names = {(l.get("name") if isinstance(l, dict) else str(l))
                 for l in (row.get("labels") or [])}
        if CLAIMED in names:
            return CLAIMED
        if FAILED_STATE in names:
            return FAILED_STATE
        if READY in names:
            return READY
        return "needs-triage"


class GitHubTracker(_CliTracker):
    kind = "github"

    def preflight(self) -> None:
        code, out = self._run(["gh", "auth", "status"])
        if code != 0:
            raise TrackerUnavailable(
                "`gh` is missing or not authenticated -- cannot read the GitHub "
                "issue queue. Install it and run `gh auth login`. Refusing to "
                f"report an empty queue instead.\n{out.strip()}")

    def discover(self) -> list[Issue]:
        code, out = self._run([
            "gh", "issue", "list", "--state", "open", "--limit", "200",
            "--json", "number,title,body,labels",
        ])
        if code != 0:
            raise TrackerUnavailable(f"`gh issue list` failed:\n{out.strip()}")
        return self._parse(out)

    def set_status(self, issue: Issue, status: str) -> None:
        n = issue.number
        if status == CLAIMED:
            self._run(["gh", "issue", "edit", n,
                       "--add-label", CLAIMED, "--remove-label", READY])
        elif status == RESOLVED:
            # Closing IS "resolved" here. A `resolved` label would be a second
            # source of truth that can disagree with the issue's own state.
            self._run(["gh", "issue", "edit", n, "--remove-label", CLAIMED])
            self._run(["gh", "issue", "close", n, "--reason", "completed"])
        elif status == FAILED_STATE:
            self._run(["gh", "issue", "edit", n, "--remove-label", CLAIMED,
                       "--add-label", FAILED_STATE])

    def append_comment(self, issue: Issue, note: str) -> None:
        self._run(["gh", "issue", "comment", issue.number, "--body", note])


class GitLabTracker(_CliTracker):
    kind = "gitlab"

    def preflight(self) -> None:
        code, out = self._run(["glab", "auth", "status"])
        if code != 0:
            raise TrackerUnavailable(
                "`glab` is missing or not authenticated -- cannot read the GitLab "
                "issue queue. Install it and run `glab auth login`. Refusing to "
                f"report an empty queue instead.\n{out.strip()}")

    def discover(self) -> list[Issue]:
        code, out = self._run(["glab", "issue", "list", "--opened",
                               "--per-page", "200", "--output", "json"])
        if code != 0:
            raise TrackerUnavailable(f"`glab issue list` failed:\n{out.strip()}")
        return self._parse(out)

    def set_status(self, issue: Issue, status: str) -> None:
        n = issue.number
        if status == CLAIMED:
            self._run(["glab", "issue", "update", n,
                       "--label", CLAIMED, "--unlabel", READY])
        elif status == RESOLVED:
            self._run(["glab", "issue", "update", n, "--unlabel", CLAIMED])
            self._run(["glab", "issue", "close", n])
        elif status == FAILED_STATE:
            self._run(["glab", "issue", "update", n, "--unlabel", CLAIMED,
                       "--label", FAILED_STATE])

    def append_comment(self, issue: Issue, note: str) -> None:
        self._run(["glab", "issue", "note", issue.number, "--message", note])


def _run_cli(argv: list[str]) -> tuple[int, str]:
    """Run a tracker CLI, returning (exit_code, combined output). A missing
    binary is reported as a non-zero exit rather than raising, so preflight()
    turns it into the same TrackerUnavailable as an auth failure."""
    try:
        p = subprocess.run(argv, capture_output=True, text=True)
    except FileNotFoundError:
        return 127, f"{argv[0]}: command not found"
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def make_tracker(kind: str, scratch_dir: Path, runner=None):
    if kind == "local":
        return LocalTracker(scratch_dir)
    if kind == "github":
        return GitHubTracker(runner)
    if kind == "gitlab":
        return GitLabTracker(runner)
    raise TrackerUnavailable(
        f"cannot tell which issue tracker this repo uses (detected {kind!r}). "
        "Put a first line like '# Issue tracker: GitHub' in "
        "docs/agents/issue-tracker.md, or create .scratch/ for the "
        "local-markdown tracker.")


def run_once(scratch_dir: Path, config: str, tracker=None) -> bool:
    """One scan-claim-dispatch-resolve cycle. Returns True if work was found
    and dispatched (regardless of outcome), False if the queue was empty.

    `tracker` defaults to a LocalTracker over `scratch_dir`, so the original
    two-argument call still means exactly what it used to.
    """
    if tracker is None:
        tracker = LocalTracker(scratch_dir)

    # Claiming commits on a LOCAL tracker (see commit_watcher_state) -- a
    # dirty tree at scan time would get swept into that commit, same "git
    # add -A stages the entire working tree" gotcha every ADW commit phase
    # carries. Refuse rather than silently commit someone else's unrelated
    # in-progress work.
    #
    # Remote trackers are exempt: they commit nothing, so a dirty tree
    # cannot be swept anywhere, and refusing would block the queue for a
    # reason that does not apply to them.
    if getattr(tracker, "kind", "local") == "local":
        if git_helper.is_repo() and git_helper.is_dirty():
            print("just watch: working tree is dirty -- refusing to claim anything "
                  "until it's clean (claiming commits, and would sweep in whatever "
                  "else is sitting there)")
            return False

    issues = tracker.discover()
    next_issue = frontier(issues, tracker.missing_means_resolved)
    if next_issue is None:
        print("just watch: queue empty -- nothing ready-for-agent and unblocked")
        return False
    print(f"just watch: claiming {next_issue}")
    ok, adw_id = dispatch(next_issue, config, tracker)
    print(f"just watch: session {adw_id} {'succeeded' if ok else 'FAILED'} -- {next_issue}")
    return True


def main(scratch_dir: str, config: str, once: bool, interval: int) -> int:
    root = Path.cwd()
    kind = detect_tracker(root)
    try:
        tracker = make_tracker(kind, Path(scratch_dir))
        tracker.preflight()
    except TrackerUnavailable as exc:
        # Exit 2, never a falsely-empty queue: an operator reads "queue empty"
        # as "no work to do" and walks away. That was the original bug.
        print(f"just watch: {exc}", file=sys.stderr)
        return 2

    print(f"just watch: {kind} tracker")
    path = Path(scratch_dir)
    # A tracker can also become unavailable mid-run (token expires, network
    # drops, `gh` invoked outside a repo), and discover() raises then too.
    # That must still be exit 2, not a traceback -- and in loop mode it must
    # stop rather than spin uselessly every `interval` seconds.
    try:
        if once:
            return 0 if run_once(path, config, tracker) else 1
        while True:
            run_once(path, config, tracker)
            time.sleep(interval)
    except TrackerUnavailable as exc:
        print(f"just watch: {exc}", file=sys.stderr)
        return 2


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
