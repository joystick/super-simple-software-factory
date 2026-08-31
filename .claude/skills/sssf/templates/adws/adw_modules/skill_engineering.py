"""Skill composition — Pocock-style workflow protocols as SSSF node behaviour.

See docs/prd-skill-engineering.md for the why. This module owns exactly one
concern: given an agent's already-rendered system prompt and a list of skill
file paths, return the final system prompt string. Pure — no Run, no
subprocess, no network — which is what makes it testable in isolation and
safe to call from agents.execute() without changing anything about how an
agent is spawned.

Composition order is the engineer's, not alphabetical: the agent's own system
prompt always comes first (its identity and output contract outrank any
borrowed protocol), then skills in the order listed. Sorting them would
silently change behaviour, and an unstable order would break prompt caching.
"""

from __future__ import annotations

from pathlib import Path

DELIMITER = "\n\n# --- skill: {name} ---\n\n"


class SkillFileError(ValueError):
    """A named skill_engineering path is missing, empty, or not a file."""


def _read(raw_path: str) -> tuple[str, str]:
    """(stem, stripped body), or raise SkillFileError naming the path.

    Resolves relative to the process cwd — same convention as
    `AgentConfig.prompt_engineering`'s paths, which `agents.py` also reads
    with a bare `Path(ref).is_file()`. An ADW is always invoked from the
    repo root (every cookbook and template in this skill assumes it), so
    this is consistent with existing behaviour, not a new assumption.
    """
    path = Path(raw_path)
    if not path.is_file():
        raise SkillFileError(f"skill file not found: {raw_path}")
    body = path.read_text().strip()
    if not body:
        raise SkillFileError(f"skill file is empty: {raw_path}")
    return path.stem, body


def check(skill_paths: list[str]) -> None:
    """Raise SkillFileError, naming the path, if any entry is missing, empty,
    or a directory. Nothing else — no system prompt required, no text
    returned — so `agents.validate()` can fail fast on a roster typo before
    any process spawns without depending on `compose()` staying oblivious to
    a `system_text` it doesn't actually need for this check.
    """
    for raw_path in skill_paths:
        _read(raw_path)


def compose(system_text: str, skill_paths: list[str]) -> str:
    """The agent's system prompt, then each named skill's text in order.

    Raises SkillFileError, naming the path, if any entry is missing, empty,
    or a directory. This runs before any agent spawns (see agents.validate
    -> check(), which performs the identical check), so a typo in a roster
    is a config error, not a wasted turn.
    """
    if not skill_paths:
        return system_text

    parts = [system_text]
    for raw_path in skill_paths:
        name, body = _read(raw_path)
        parts.append(DELIMITER.format(name=name) + body)
    return "".join(parts)
