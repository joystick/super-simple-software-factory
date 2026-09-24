#!/usr/bin/env python3
"""Walk every .md file under reference/, find real Markdown links
(`[text](path#anchor)`), and confirm each target file exists and each anchor
resolves to a real heading. Distinct from check_reference_manifest.py, which
checks the manifest TABLE's own citations -- this checks actual clickable
links in prose, which is a different surface (a page's "See also" section, a
"Full definition: see [...]" line) that could drift independently of the
manifest.

Skips http(s):// links (external, not this script's job) and links with no
file extension (assumed same-page anchors like [text](#section), not checked
here since Starlight/GitHub both resolve those natively).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)


def slugify(heading: str) -> str:
    heading = re.sub(r"`([^`]*)`", r"\1", heading)
    heading = heading.lower()
    heading = re.sub(r"[^\w\s-]", "", heading)
    heading = re.sub(r"\s+", "-", heading.strip())
    return heading


def check_file(md_file: Path, root: Path, fork_root: Path) -> list[str]:
    """A relative link that climbs out of `root` (e.g. `../../../.claude/...`,
    reaching for the fork root) is resolved against `fork_root` instead --
    those links are written to work once this tree lands inside the real
    fork, not against the isolated test workspace, which has no `.claude/`
    of its own."""
    errors = []
    text = md_file.read_text()
    for link_text, target in MD_LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        path_part, _, anchor = target.partition("#")
        if not path_part:
            continue  # same-page anchor only, e.g. [x](#foo) -- not checked here
        if "." not in Path(path_part).name:
            continue  # no extension, likely not a file link
        in_workspace = (md_file.parent / path_part).resolve()
        in_fork = (fork_root / Path(*Path(path_part).parts[3:])).resolve() if path_part.startswith("../../../") else in_workspace
        resolved = in_workspace if in_workspace.is_file() else in_fork
        if not resolved.is_file():
            errors.append(f"{md_file.relative_to(root)}: [{link_text}]({target}) -> "
                         f"neither {in_workspace} nor {in_fork} exists")
            continue
        if anchor:
            heading_text = resolved.read_text()
            slugs = {slugify(h) for h in HEADING_RE.findall(heading_text)}
            if anchor not in slugs:
                errors.append(f"{md_file.relative_to(root)}: [{link_text}]({target}) -> "
                             f"anchor #{anchor} not found in {resolved}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--fork-root", type=Path, default=None,
                        help="see check_reference_manifest.py's --fork-root for why")
    args = parser.parse_args()
    root = args.root.resolve()
    fork_root = (args.fork_root or args.root).resolve()

    md_files = sorted((root / "reference").rglob("*.md"))
    all_errors = []
    checked_links = 0
    for f in md_files:
        text = f.read_text()
        checked_links += len(MD_LINK_RE.findall(text))
        all_errors.extend(check_file(f, root, fork_root))

    print(f"Scanned {len(md_files)} files, found {checked_links} markdown links total.")
    if all_errors:
        print(f"\n{len(all_errors)} broken link(s):")
        for e in all_errors:
            print(f"  FAIL: {e}")
        print("\nFAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
