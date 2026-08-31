#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///
"""/vendor-skill — copy a Pocock-style skill file into a target repo's
adws/adw_data/skill_engineering/, stamped with provenance so drift from the
source is detectable later. A deliberate, reviewable act that produces a
diff — never an auto-update. See docs/prd-skill-engineering.md.

Usage:
    uv run <skill>/scripts/vendor_skill.py <source> [--as NAME]
        [--dest-dir adws/adw_data/skill_engineering]
    uv run <skill>/scripts/vendor_skill.py --check <vendored-file>
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

DEFAULT_DEST_DIR = "adws/adw_data/skill_engineering"

HEADER_TEMPLATE = (
    "<!-- sssf:vendored\n"
    "source: {source}\n"
    "date: {today}\n"
    "sha256: {source_hash}\n"
    "-->\n\n"
)
HEADER_RE = re.compile(
    r"\A<!--\s*sssf:vendored\n"
    r"source:\s*(?P<source>.*)\n"
    r"date:\s*(?P<date>.*)\n"
    r"sha256:\s*(?P<hash>[0-9a-f]{64})\n"
    r"-->\s*",
    re.MULTILINE,
)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _display_source(source: Path) -> str:
    """The path stamped into the provenance header. Relative to $HOME
    (as "~/...") when the source is under it — the common case, since
    every real Pocock skill lives under ~/.claude/skills/ or similar — so
    the header stays portable to any machine that shares that convention
    instead of baking in one person's exact home directory. Found by
    adversarial review: the original always stored an absolute path,
    which meant a committed vendored file leaked one machine's username
    and reported permanent false drift on anyone else's."""
    resolved = source.resolve()
    home = Path.home().resolve()
    try:
        return f"~/{resolved.relative_to(home)}"
    except ValueError:
        return str(resolved)   # genuinely outside $HOME — no portable shorthand exists


class HandAuthoredFileError(ValueError):
    """The destination exists and was not vendored by this tool (no
    provenance header) — refuse rather than silently overwrite it."""


@dataclass
class VendorResult:
    dest: Path
    source_hash: str
    changed: bool


def _default_name(source: Path) -> str:
    """Every real Pocock skill file is literally SKILL.md — the identity
    lives in the parent directory, not the filename. Falling back to the
    file's own stem for a bare "SKILL.md" would vendor every skill in a
    roster to the same destination and silently clobber each other."""
    if source.stem.lower() == "skill":
        return source.parent.name
    return source.stem


def vendor(source: str | Path, dest_dir: str | Path, name: str | None = None,
          today: str | None = None) -> VendorResult:
    """Copy `source`'s body into `dest_dir`, stamped with provenance.

    Re-vendoring identical source content is a no-op: the destination file
    (including its date stamp) is left untouched and `changed` is False, so
    running this in a loop or a CI check never produces a spurious diff.

    Raises HandAuthoredFileError, and touches nothing, if the destination
    already exists but carries no provenance header — that means a human
    wrote it, and this tool does not get to decide their file was actually
    meant to be a vendoring target.
    """
    source = Path(source)
    body = source.read_text()
    source_hash = _hash(body)
    dest = Path(dest_dir) / f"{name or _default_name(source)}.md"

    if dest.is_file():
        existing = HEADER_RE.match(dest.read_text())
        if existing is None:
            raise HandAuthoredFileError(
                f"{dest} already exists and has no provenance header — refusing to "
                "overwrite a file this tool did not vendor. Remove it, or vendor "
                "under a different --as name, if you meant to replace it.")
        if existing.group("hash") == source_hash:
            return VendorResult(dest=dest, source_hash=source_hash, changed=False)

    dest.parent.mkdir(parents=True, exist_ok=True)
    header = HEADER_TEMPLATE.format(
        source=_display_source(source), today=today or date.today().isoformat(),
        source_hash=source_hash)
    dest.write_text(header + body)
    return VendorResult(dest=dest, source_hash=source_hash, changed=True)


@dataclass
class DriftResult:
    drifted: bool
    message: str


def check_drift(vendored_path: str | Path) -> DriftResult:
    """Has the source this file was vendored from changed (or gone) since?

    Reports; never resolves. Re-vendoring on purpose is how drift is fixed.
    """
    vendored_path = Path(vendored_path)
    match = HEADER_RE.match(vendored_path.read_text())
    if not match:
        return DriftResult(drifted=False,
                           message=f"{vendored_path}: no provenance header (hand-authored, not vendored)")

    source = Path(match.group("source")).expanduser()
    if not source.is_file():
        return DriftResult(drifted=True, message=f"source gone: {source}")

    current_hash = _hash(source.read_text())
    if current_hash != match.group("hash"):
        return DriftResult(drifted=True,
                           message=f"source changed since vendoring: {source}")
    return DriftResult(drifted=False, message=f"{vendored_path}: matches {source}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help="skill file to vendor, or (with --check) a vendored file")
    parser.add_argument("--as", dest="name", default=None,
                        help="vendored filename stem (default: the source's own stem, or "
                             "its parent directory's name for a bare SKILL.md)")
    parser.add_argument("--dest-dir", default=DEFAULT_DEST_DIR)
    parser.add_argument("--check", action="store_true",
                        help="report drift for an already-vendored file instead of vendoring")
    args = parser.parse_args()

    if args.check:
        drift = check_drift(args.path)
        print(("DRIFT: " if drift.drifted else "ok: ") + drift.message)
        return 1 if drift.drifted else 0

    try:
        result = vendor(args.path, args.dest_dir, name=args.name)
    except HandAuthoredFileError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if result.changed:
        print(f"vendored: {result.dest}")
    else:
        print(f"unchanged: {result.dest} (source hash matches — no-op)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
