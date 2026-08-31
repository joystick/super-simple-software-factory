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

import re
from pathlib import Path

DELIMITER = "\n\n# --- skill: {name} ---\n\n"

# A vendored file (see vendor_skill.py) opens with exactly this HTML-comment
# block — invisible in a rendered Markdown viewer, and easy to strip before
# the text ever reaches a model. A hand-authored file has no such header, so
# this simply doesn't match and the file is used as-is: compose() still has
# no concept of "vendored" vs. "local", only "has a header" vs. "doesn't."
#
# Deliberately as strict as vendor_skill.py's own HEADER_RE (source/date/
# sha256 lines, a real 64-hex-char hash), not a loose "any HTML comment
# starting with sssf:vendored" match — a skill body that happens to
# document this very header format in prose must not be mistaken for one
# and stripped. The two regexes are defined independently (this module
# ships standalone into every stamped repo; vendor_skill.py stays in the
# skill source and is never stamped), so test_vendor_skill.py carries a
# parity test asserting they agree on the same fixtures — that test is
# the thing actually preventing silent divergence, not code sharing.
PROVENANCE_HEADER_RE = re.compile(
    r"\A<!--\s*sssf:vendored\n"
    r"source:.*\n"
    r"date:.*\n"
    r"sha256:\s*[0-9a-f]{64}\n"
    r"-->\s*",
    re.MULTILINE,
)


class SkillFileError(ValueError):
    """A named skill_engineering path is missing, empty, or not a file."""


def _strip_provenance(text: str) -> str:
    """Remove a leading vendoring header, if present. A comment about where
    a file came from is not an instruction to the model, and leaving it in
    the prompt is both noise and a small correctness risk."""
    return PROVENANCE_HEADER_RE.sub("", text, count=1)


def skill_name(path: Path) -> str:
    """The name used in the composition delimiter, in estimate_tokens()'s
    accounting, and in console.py's cost report — every place a skill needs
    a human-legible label. Public (no leading underscore) specifically so
    console.py can reuse it rather than deriving its own: an earlier version
    of this fix touched compose() and vendor_skill.py's naming but missed
    the console report, which used a bare Path(p).stem and printed
    "SKILL, SKILL" for two real, distinct skills. Adversarial review caught
    that as a third instance of the same bug in one review pass, which is
    exactly why this is now the one place the rule lives.

    Every real Pocock skill file is literally named SKILL.md — identity
    lives in the parent directory. Falling back to the bare file stem gives
    two distinct skills the identical label, making both the composed
    prompt and the console report unnavigable.
    """
    if path.stem.lower() == "skill":
        return path.parent.name
    return path.stem


def _read(raw_path: str) -> tuple[str, str]:
    """(skill name, stripped body), or raise SkillFileError naming the path.

    Resolves relative to the process cwd — same convention as
    `AgentConfig.prompt_engineering`'s paths, which `agents.py` also reads
    with a bare `Path(ref).is_file()`. An ADW is always invoked from the
    repo root (every cookbook and template in this skill assumes it), so
    this is consistent with existing behaviour, not a new assumption.
    """
    path = Path(raw_path)
    if not path.is_file():
        raise SkillFileError(f"skill file not found: {raw_path}")
    body = _strip_provenance(path.read_text()).strip()
    if not body:
        raise SkillFileError(f"skill file is empty: {raw_path}")
    return skill_name(path), body


def check(skill_paths: list[str]) -> None:
    """Raise SkillFileError, naming the path, if any entry is missing, empty,
    or a directory. Nothing else — no system prompt required, no text
    returned — so `agents.validate()` can fail fast on a roster typo before
    any process spawns without depending on `compose()` staying oblivious to
    a `system_text` it doesn't actually need for this check.
    """
    for raw_path in skill_paths:
        _read(raw_path)


CHARS_PER_TOKEN = 4   # rough, model-agnostic heuristic — good enough to warn
                      # on, never presented as a billed count. See PRD: "an
                      # estimated token count."


def estimate_tokens(skill_paths: list[str]) -> int:
    """Rough size of the composed skill text, in tokens. 0 for no skills.

    Same file-reading rules as compose()/check() — raises SkillFileError on
    a bad path. Called from agents.execute() only after agents.validate()
    has already confirmed every path is good, so in practice this never
    raises at that call site; it is exposed here (rather than folded into
    compose()) so a caller can get a cost estimate without needing a real
    system_text to compose against.
    """
    total_chars = sum(len(DELIMITER.format(name=name)) + len(body)
                      for name, body in (_read(p) for p in skill_paths))
    return total_chars // CHARS_PER_TOKEN


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
