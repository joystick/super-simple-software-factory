#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///
"""/vendor-skill — copy a Pocock-style skill file into a target repo's
adws/adw_data/skill_engineering/, stamped with provenance so drift from the
source is detectable later. A deliberate, reviewable act that produces a
diff — never an auto-update. See docs/prd-skill-engineering.md.

This copies ONE file. A skill whose substance spans sibling files, or that
assumes an interactive user, needs the sssf-skill-vendoring procedure
(.claude/skills/sssf-skill-vendoring/SKILL.md), which uses this tool for
the stamping step and records the merge in an sssf:flattened manifest.

Usage:
    uv run <skill>/scripts/vendor_skill.py <source> [--as NAME]
        [--dest-dir adws/adw_data/skill_engineering]
    uv run <skill>/scripts/vendor_skill.py --check <vendored-file>
    uv run <skill>/scripts/vendor_skill.py --hash <sibling-file>
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
# A hand-flattened composite's manifest, directly under the header: which
# sibling files were merged in (with their hash, so --check can see them
# drift) and which were left out. Paths are relative to the vendored
# source's own directory. Must stay in step with skill_engineering.py's
# FLATTEN_MANIFEST_RE — test_vendor_skill.py checks that they agree.
FLATTEN_RE = re.compile(
    r"\A<!--\s*sssf:flattened\n"
    r"(?:(?:kept|dropped): .*\n)+"
    r"-->\s*",
)
KEPT_RE = re.compile(r"^kept: (?P<path>\S+) sha256:(?P<hash>[0-9a-f]{64})\s*$", re.MULTILINE)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_hash(path: str | Path) -> str:
    """The hash vendor() and check_drift() use, for writing a manifest's
    `kept:` lines. Not `shasum`: read_text() normalizes line endings first."""
    return _hash(Path(path).read_text())


def _flatten_manifest(vendored_text: str) -> str | None:
    """The manifest block of a flattened file, or None for a plain vendor."""
    header = HEADER_RE.match(vendored_text)
    if header is None:
        return None
    manifest = FLATTEN_RE.match(vendored_text[header.end():])
    return manifest.group(0) if manifest else None


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


class FlattenedFileError(ValueError):
    """The destination is a hand-flattened composite (SKILL.md plus merged
    sibling files) and its SKILL.md changed upstream. A plain re-vendor
    would replace the whole composite with bare SKILL.md, silently dropping
    every merged sibling — refuse, and point at the procedure that rebuilds
    it properly."""


class UnsafeNameError(ValueError):
    """--as (or a default derived from a hostile source path) contains a
    path separator or traversal component. Path(dest_dir) / name joins
    literally: a name of "../../../etc/passwd" escapes dest_dir entirely,
    and an absolute name like "/etc/passwd" discards dest_dir outright —
    that is how Python's Path "/" operator resolves an absolute right-hand
    side. Reject anything that is not a bare filename stem."""


def _validate_name(name: str) -> None:
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        raise UnsafeNameError(
            f"{name!r} is not a valid vendored filename stem — no '/', no "
            "'\\', not empty, not '.' or '..'. --as must name a bare file, "
            "not a path.")


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
    name = name or _default_name(source)
    _validate_name(name)
    dest = Path(dest_dir) / f"{name}.md"

    if dest.is_file():
        existing_text = dest.read_text()
        existing = HEADER_RE.match(existing_text)
        if existing is None:
            raise HandAuthoredFileError(
                f"{dest} already exists and has no provenance header — refusing to "
                "overwrite a file this tool did not vendor. Remove it, or vendor "
                "under a different --as name, if you meant to replace it.")
        if existing.group("hash") == source_hash:
            return VendorResult(dest=dest, source_hash=source_hash, changed=False)
        if _flatten_manifest(existing_text) is not None:
            raise FlattenedFileError(
                f"{dest} is a flattened composite (it has an sssf:flattened manifest) "
                "and its SKILL.md changed upstream. Re-vendoring would replace it with "
                "bare SKILL.md and drop every merged sibling. Rebuild it with the "
                "sssf-skill-vendoring procedure instead, or delete it first if you "
                "really want the plain file.")

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
    text = vendored_path.read_text()
    match = HEADER_RE.match(text)
    if not match:
        return DriftResult(drifted=False,
                           message=f"{vendored_path}: no provenance header (hand-authored, not vendored)")

    source = Path(match.group("source")).expanduser()
    if not source.is_file():
        return DriftResult(drifted=True, message=f"source gone: {source}")

    problems = []
    if _hash(source.read_text()) != match.group("hash"):
        problems.append(f"source changed since vendoring: {source}")

    # A flattened composite also tracks every sibling it merged in; dropped
    # siblings were a deliberate exclusion and are not checked.
    manifest = _flatten_manifest(text)
    for kept in KEPT_RE.finditer(manifest or ""):
        sibling = source.parent / kept.group("path")
        if not sibling.is_file():
            problems.append(f"merged sibling gone: {sibling}")
        elif _hash(sibling.read_text()) != kept.group("hash"):
            problems.append(f"merged sibling changed since flattening: {sibling}")

    if problems:
        return DriftResult(drifted=True, message="; ".join(problems))
    siblings = f" (+ {len(KEPT_RE.findall(manifest))} merged sibling(s))" if manifest else ""
    return DriftResult(drifted=False, message=f"{vendored_path}: matches {source}{siblings}")


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
    parser.add_argument("--hash", action="store_true",
                        help="print the content hash of a sibling file, for a flatten "
                             "manifest's `kept:` line")
    args = parser.parse_args()

    if args.hash:
        print(file_hash(args.path))
        return 0

    if args.check:
        drift = check_drift(args.path)
        print(("DRIFT: " if drift.drifted else "ok: ") + drift.message)
        return 1 if drift.drifted else 0

    try:
        result = vendor(args.path, args.dest_dir, name=args.name)
    except (HandAuthoredFileError, FlattenedFileError, UnsafeNameError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if result.changed:
        print(f"vendored: {result.dest}")
    else:
        print(f"unchanged: {result.dest} (source hash matches — no-op)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
