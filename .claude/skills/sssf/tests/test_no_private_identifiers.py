"""No real adopter project names or private identifiers in tracked files.

This repo is PUBLIC, and some of its tracked files are a SHIPPED skill —
`.claude/skills/sssf-skill-vendoring/` is installed into adopter repos — so
a name here propagates outward, not merely to people browsing GitHub.

Filed and fixed as issue #23. This test exists because the scrub alone was a
one-off: nothing detected the names for the two months they sat there, and
nothing would detect the next one. The denylist is the point, not the
current green.

Scope note: only TRACKED files are checked. `downloads/` is gitignored and
`.claude/settings.local.json` is untracked; both legitimately contain real
names and neither is published. Checking them would produce permanent
false failures and train people to ignore this test.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]

# Real private project / host / domain names that must never appear in a
# tracked file. Add to this when a new adopter or host is worked on.
DENYLIST = [
    "weather-report",
    "portfinder",
    "opencode-expo",
    "rxdb-sqlite",
    "crewfile",
    "vesta02",
    "vesta03",
    "kipr24",
    "seaducate",
]

# Teaching the pattern needs *a* project name. These are deliberate,
# non-existent stand-ins used across the docs, lessons and test fixtures.
NEUTRAL_EXAMPLES = ["route-builder", "cart-pricing"]


# This file necessarily contains every forbidden name -- that is what a
# denylist is. Once it became tracked, `git grep` started finding them here
# and the guard failed on itself, every term at once. Excluding it is the
# honest fix: the alternative (assembling the names from fragments to dodge
# the grep) would make the list unreadable, which is worse than a one-line
# pathspec. Found by running the suite after committing, not before.
SELF = ":(exclude).claude/skills/sssf/tests/test_no_private_identifiers.py"


def tracked_hits(needle: str) -> list[str]:
    """Files git actually tracks that contain `needle`, case-insensitively.

    Excludes this file (see SELF) -- everything else is in scope.
    """
    r = subprocess.run(
        ["git", "grep", "-i", "-l", needle, "--", ".", SELF],
        cwd=REPO, capture_output=True, text=True,
    )
    # exit 1 == no matches, which is the passing case
    if r.returncode not in (0, 1):
        pytest.fail(f"git grep failed: {r.stderr.strip()}")
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


@pytest.mark.parametrize("needle", DENYLIST)
def test_no_private_identifier_in_tracked_files(needle):
    hits = tracked_hits(needle)
    assert not hits, (
        f"{needle!r} appears in {len(hits)} tracked file(s) of a PUBLIC repo:\n  "
        + "\n  ".join(hits)
        + "\n\nUse a neutral label instead — 'a downstream adopter', 'the Rust "
          "adopter', 'that adopter' — keeping the engineering detail, which is "
          "the part worth publishing. See issue #23."
    )


def test_the_guard_can_actually_fail():
    # A denylist test that can only ever pass is worthless. Prove the
    # mechanism detects a string that IS present in a tracked file.
    #
    # The sentinel is deliberately a string in ANOTHER file, not in this
    # one: the first version grepped for a token in this very file, which
    # silently passes nothing while the file is still untracked (as it is
    # the moment it is written). Caught by this test failing on its own
    # first run -- exactly the self-check it exists to provide.
    assert tracked_hits("adw_watch"), (
        "git grep found no tracked file containing 'adw_watch' -- the guard "
        "mechanism itself is broken, so every denylist pass above is "
        "meaningless")


@pytest.mark.parametrize("name", NEUTRAL_EXAMPLES)
def test_neutral_example_names_are_not_on_the_denylist(name):
    # Guards against someone later adding a teaching placeholder to the
    # denylist and making the docs unwritable.
    assert name not in DENYLIST
