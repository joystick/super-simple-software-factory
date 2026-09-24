#!/usr/bin/env python3
"""Verify docs/reference/concept-manifest.md against reality.

Two independent checks, matching what the plan's Definition of done actually
claims -- not a generic "is everything perfect" scan:

1. Every "link" row's citation must resolve: the target file must exist, and
   if the citation names a `#anchor`, that file must contain a heading whose
   GitHub-style slug matches it. A link row with a non-resolving anchor is
   exactly the "dead-end link" class of bug a fable review pass already found
   and fixed 9 instances of -- this script exists so the next one doesn't
   need a human to notice by hand.

2. Every "own-page" row explicitly listed in reference/README.md's "What this
   pass built" list must have a real file on disk. Own-page rows NOT in that
   list are expected to be unauthored stubs per the plan's scoping decision --
   reported, never failed, so this script stays honest about what "done"
   actually means for this pass instead of demanding 100% authorship a single
   pass never claimed to deliver.

Usage: run from the reference/ directory's parent (the workspace root), or
pass --root explicitly.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROW_RE = re.compile(
    r"^\|\s*(?P<concept>.+?)\s*\|\s*(?P<category>[\w-]+)\s*\|\s*(?P<resolution>[^|]+?)\s*\|\s*(?P<citation>.+?)\s*\|\s*$"
)
LINK_TARGET_RE = re.compile(r"`([^`]+\.md)(#[\w-]+)?`")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)


def slugify(heading: str) -> str:
    """GitHub-style heading slug: lowercase, spaces -> hyphens, strip
    everything that isn't a word char, hyphen, or existing hyphen. Good
    enough for our own house-style headings (no duplicate-heading disambiguation
    needed here -- every reference page's headings are unique per file)."""
    heading = re.sub(r"`([^`]*)`", r"\1", heading)  # drop backticks, keep contents
    heading = heading.lower()
    heading = re.sub(r"[^\w\s-]", "", heading)
    heading = re.sub(r"\s+", "-", heading.strip())
    return heading


def parse_manifest_rows(manifest_path: Path) -> list[dict]:
    rows = []
    for line in manifest_path.read_text().splitlines():
        if not line.startswith("|") or "Concept" in line or set(line.strip()) <= {"|", "-", " "}:
            continue
        m = ROW_RE.match(line)
        if m:
            rows.append(m.groupdict())
    return rows


def check_link_row(row: dict, fork_root: Path) -> str | None:
    """Returns an error string, or None if the link resolves. Citations are
    paths like `.claude/skills/sssf/references/config.md#anchor` -- relative
    to the FORK root (where they'll actually resolve once this tree lands in
    docs/reference/), not the isolated test workspace, which has no .claude/
    of its own. Passing the wrong root here produced 37 false failures the
    first time this script ran."""
    m = LINK_TARGET_RE.search(row["citation"])
    if not m:
        return f"no parseable `file.md#anchor` citation in: {row['citation']!r}"
    rel_path, anchor = m.group(1), m.group(2)
    target = fork_root / rel_path
    if not target.is_file():
        return f"cited file does not exist: {rel_path}"
    if anchor:
        slug = anchor.lstrip("#")
        text = target.read_text()
        slugs = {slugify(h) for h in HEADING_RE.findall(text)}
        if slug not in slugs:
            return f"anchor #{slug} not found as a heading in {rel_path} (found: {sorted(slugs)[:5]}...)"
    return None


def own_page_authored_list(readme_path: Path) -> set[str]:
    """Parse reference/README.md's 'What this pass built' bullet list of
    fully-authored page paths (backtick-quoted, one per line). Scoped
    strictly to that one section -- a naive whole-file regex also matches
    every other backtick-quoted .md mention in the file's prose (SKILL.md,
    config.md, the link-vs-own-page rule's own examples), which is not what
    this function means to answer. Found live running this script the first
    time: 6 false "authored" entries from exactly that over-matching."""
    text = readme_path.read_text()
    m = re.search(r"^## What this pass built\n(.*?)(?=\n## |\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        return set()
    section = m.group(1)
    return {line.strip().lstrip("- ").split()[0].strip("`")
           for line in section.splitlines() if line.strip().startswith("- `")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."),
                        help="workspace root (contains reference/)")
    parser.add_argument("--fork-root", type=Path, default=None,
                        help="where .claude/skills/sssf/references/*.md actually "
                             "live -- defaults to --root (correct once this tree "
                             "is applied inside the real fork; pass the real fork "
                             "path explicitly when testing from an isolated "
                             "workspace that has no .claude/ of its own)")
    args = parser.parse_args()

    root = args.root.resolve()
    fork_root = (args.fork_root or args.root).resolve()
    manifest_path = root / "reference" / "concept-manifest.md"
    readme_path = root / "reference" / "README.md"
    if not manifest_path.is_file():
        print(f"FAIL: manifest not found at {manifest_path}", file=sys.stderr)
        return 2

    rows = parse_manifest_rows(manifest_path)
    print(f"Parsed {len(rows)} manifest rows.")

    link_failures = []
    own_page_authored = 0
    own_page_stubbed = 0
    own_page_missing_but_claimed = []

    authored = own_page_authored_list(readme_path)

    for row in rows:
        resolution = row["resolution"].lower()
        if resolution.startswith("link"):
            err = check_link_row(row, fork_root)
            if err:
                link_failures.append((row["concept"], err))
        elif resolution.startswith("own-page"):
            # Own-page rows have no fixed filename convention to derive
            # automatically -- existence is checked in bulk below, against
            # README.md's explicit "fully authored" list, not per-row here.
            pass
        else:
            link_failures.append((row["concept"], f"unrecognized resolution: {row['resolution']!r}"))

    # Cross-check: every file README.md claims as fully-authored must exist.
    for rel in sorted(authored):
        p = root / "reference" / rel
        if p.is_file():
            own_page_authored += 1
        else:
            own_page_missing_but_claimed.append(rel)
    own_page_stubbed = sum(1 for r in rows if r["resolution"].lower().startswith("own-page")) - own_page_authored

    print(f"\n=== Link rows ===")
    print(f"{len(rows) - sum(1 for r in rows if r['resolution'].lower().startswith('own-page'))} link rows checked, {len(link_failures)} failed.")
    for concept, err in link_failures:
        print(f"  FAIL: {concept}: {err}")

    print(f"\n=== Own-page rows ===")
    print(f"{own_page_authored} confirmed authored (per README.md's list, file exists).")
    print(f"{own_page_stubbed} not yet authored (expected per the plan's scoping decision -- informational, not a failure).")
    if own_page_missing_but_claimed:
        print(f"  FAIL: README.md claims these are authored, but the file is missing:")
        for rel in own_page_missing_but_claimed:
            print(f"    {rel}")

    ok = not link_failures and not own_page_missing_but_claimed
    print(f"\n{'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
