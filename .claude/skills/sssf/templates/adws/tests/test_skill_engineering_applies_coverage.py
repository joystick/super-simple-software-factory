"""Structural regression guard, added after round 5 of an adversarial
review of skill_engineering: every place in this package that reads
`agent.skill_engineering` must either be gated by
`skill_engineering_applies()` or be on the small, explicit, reasoned
allowlist below. New reads that are neither will fail this test — that is
the point. Eight instances of "gated in one place, forgotten in a sibling"
were found and fixed across this feature's build; this test exists so a
ninth has to be a conscious decision, not an accident.

This is intentionally a blunt text scan, not real static analysis — it
enumerates every source line matching `agent.skill_engineering` across the
package and requires each one to be accounted for. Cheap, and it catches
exactly the failure mode that kept recurring.
"""

from __future__ import annotations

import re
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]   # .../adws
FILES_TO_SCAN = [
    PACKAGE_ROOT / "adw_modules" / "agents.py",
    PACKAGE_ROOT / "adw_modules" / "console.py",
    PACKAGE_ROOT / "adw_modules" / "tracer.py",
    PACKAGE_ROOT / "adw_modules" / "skill_engineering.py",
    PACKAGE_ROOT / "adw_skills.py",
]

PATTERN = re.compile(r"agent\.skill_engineering\b")

# (file name, 1-indexed line number, why this one doesn't need a nearby
# skill_engineering_applies() call). Every other match must have
# "skill_engineering_applies" somewhere in the 3 lines before it (covers
# `if skill_engineering_applies(agent):` blocks and inline ternaries).
ALLOWED_UNGATED = {
    ("agents.py", 95): "ignored_field_warnings() IS the applies check — this line defines it",
    ("agents.py", 142): "audit_skills()'s own loop branches applies-vs-ignored per agent right here",
    ("agents.py", 194): "validate()'s file-existence check runs for every agent on purpose — "
                        "a typo should be caught even on a pi/agy agent, in case the roster "
                        "later switches that agent to claude_code",
    ("agents.py", 257): "agent_start event payload is deliberately AS-DECLARED, not as-applied "
                        "(see the comment at that call site) — matches harness_engineering's "
                        "own always-declared behaviour one line above it",
    ("tracer.py", 276): "the documented fallback when a caller omits the explicit override — "
                        "agents.py's one production caller always passes the gated value",
    ("tracer.py", 270): "docstring prose describing the fallback above — not a code read",
}


def _nearby_lines_contain_applies_check(lines: list[str], zero_indexed_lineno: int) -> bool:
    # +/- 3 lines: covers both `if skill_engineering_applies(agent):` blocks
    # (check precedes the read) and inline ternaries that wrap onto the
    # following line (check follows the read), e.g.
    #   skill_engineering=(agent.skill_engineering
    #                       if skill_engineering_applies(agent) else [])
    window = lines[max(0, zero_indexed_lineno - 3):zero_indexed_lineno + 4]
    return any("skill_engineering_applies" in line for line in window)


def test_every_read_of_agent_skill_engineering_is_gated_or_explicitly_allowed():
    unaccounted = []
    for path in FILES_TO_SCAN:
        lines = path.read_text().splitlines()
        for i, line in enumerate(lines):
            if not PATTERN.search(line):
                continue
            lineno = i + 1
            key = (path.name, lineno)
            if key in ALLOWED_UNGATED:
                continue
            if _nearby_lines_contain_applies_check(lines, i):
                continue
            unaccounted.append(f"{path.name}:{lineno}: {line.strip()}")

    assert not unaccounted, (
        "Found a read of agent.skill_engineering with no nearby "
        "skill_engineering_applies() check and not on the ALLOWED_UNGATED "
        "list in this test file:\n  " + "\n  ".join(unaccounted) +
        "\n\nEither gate it, or add it to ALLOWED_UNGATED with a reason — "
        "this is exactly the pattern that produced 8 real bugs across this "
        "feature's build.")


def test_allowlist_itself_stays_accurate_no_stale_entries():
    """If a line moves or its content changes, the allowlist entry is
    stale — this catches that before it silently stops covering anything."""
    for (filename, lineno), _reason in ALLOWED_UNGATED.items():
        path = next(p for p in FILES_TO_SCAN if p.name == filename)
        lines = path.read_text().splitlines()
        assert 1 <= lineno <= len(lines), f"{filename}:{lineno} is out of range"
        assert PATTERN.search(lines[lineno - 1]), (
            f"{filename}:{lineno} no longer contains 'agent.skill_engineering' — "
            "the allowlist entry is stale, update its line number")
