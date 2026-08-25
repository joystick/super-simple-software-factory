#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///
"""/install — stamp the SSSF factory from the skill into the cwd. Idempotent.

Usage:
    uv run <skill>/scripts/install.py [--force]

Stamps: adws/ (modules + starter ADWs), adws/adw_data/prompt_engineering/
(4 starter agents), adws/adw_sssf_config/sssf.config.yaml, .env.sample,
.gitignore entries.
Existing files are skipped unless --force.
"""

import argparse
import shutil
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"

GITIGNORE_ENTRIES = [
    "adws/adw_data/sessions/",
    "adws/adw_data/sssf.db*",
    ".env",
    # The ADWs are Python, so importing adw_modules writes bytecode next to it.
    # Chains that end in a commit phase call `git add -A`, so without this a
    # stamped repo commits its own .pyc files — 15 of them showed up in the
    # first repo that was ever installed into from scratch.
    "__pycache__/",
    "*.pyc",
]


# Stamped once, then owned by the engineer. `--force` alone will NOT overwrite
# these; `--reset-owned` is required on top, and says out loud what it does.
#
# Both files are templates only on the day they land. `quality.py` ships every
# gate as an `echo` placeholder that exits 0, and wiring them to the repo's real
# commands is the first thing an engineer does; `sssf.config.yaml` is the roster.
# Restoring either from the template is not a lost edit you would notice — it is
# a factory that still runs, still reports every phase green, and no longer
# checks anything. That failure is silent by construction, so it gets a second
# flag rather than riding along with `--force`.
OWNED_AFTER_STAMP = frozenset({
    "adws/adw_modules/quality.py",
    "adws/adw_sssf_config/sssf.config.yaml",
})


def stamp(src: Path, dest: Path, force: bool, stamped: list, skipped: list,
          root: Path, reset_owned: bool, preserved: list) -> None:
    if src.is_dir():
        for child in sorted(src.iterdir()):
            if child.name == "__pycache__":
                continue
            stamp(child, dest / child.name, force, stamped, skipped,
                  root, reset_owned, preserved)
        return
    if dest.exists():
        try:
            relative = dest.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:                       # dest outside root; treat as normal
            relative = ""
        if relative in OWNED_AFTER_STAMP and not reset_owned:
            preserved.append(relative)
            return
        if not force:
            skipped.append(str(dest))
            return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    stamped.append(str(dest))


def ensure_gitignore(root: Path, stamped: list) -> None:
    gitignore = root / ".gitignore"
    existing = gitignore.read_text().splitlines() if gitignore.exists() else []
    missing = [e for e in GITIGNORE_ENTRIES if e not in existing]
    if missing:
        with gitignore.open("a") as f:
            f.write("\n# sssf runtime\n" + "\n".join(missing) + "\n")
        stamped.append(f"{gitignore} (+{len(missing)} entries)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="overwrite existing files")
    parser.add_argument("--reset-owned", action="store_true",
                        help="also overwrite engineer-owned files "
                             f"({', '.join(sorted(OWNED_AFTER_STAMP))}). "
                             "Restores the placeholder gates — every quality "
                             "check will pass unconditionally until rewired.")
    args = parser.parse_args()

    root = Path.cwd()
    stamped, skipped, preserved = [], [], []

    def put(src: Path, dest: Path) -> None:
        stamp(src, dest, args.force, stamped, skipped, root, args.reset_owned, preserved)

    put(TEMPLATES / "adws", root / "adws")
    put(TEMPLATES / "prompt_engineering",
        root / "adws" / "adw_data" / "prompt_engineering")
    put(TEMPLATES / "harness_engineering",
        root / "adws" / "adw_data" / "harness_engineering")
    put(TEMPLATES / "sssf.config.yaml",
        root / "adws" / "adw_sssf_config" / "sssf.config.yaml")
    put(TEMPLATES / "env.sample", root / ".env.sample")
    # The recipes are part of the operating experience, and several cookbooks
    # plus the run banner tell you to use them, so a stamped repo has to have
    # them. Skipped like any other file if the repo already has a justfile.
    put(TEMPLATES / "justfile", root / "justfile")
    ensure_gitignore(root, stamped)

    print(f"sssf installed into {root}")
    print(f"  stamped: {len(stamped)} file(s)")
    for s in stamped:
        print(f"    + {s}")
    if skipped:
        print(f"  skipped (already exist, use --force to overwrite): {len(skipped)}")
    if preserved:
        print(f"  preserved (yours, --force does not touch these): {len(preserved)}")
        for p in preserved:
            print(f"    = {p}")
        print("    these hold your wired gate commands and your roster;")
        print("    --reset-owned restores the template placeholders, which pass unconditionally")
    print("\nnext steps:")
    print("  1. cp .env.sample .env   # then set the key(s) your roster needs")
    print("  2. just demo             # two cheap read-only runs, end to end")
    print("  3. just sessions         # what just happened")
    print("  4. just obs              # the trace UI, needs bun")
    print("\n  no just? the raw form of step 2 is:")
    print("     uv run adws/adw_prompt.py \"say hello\" --agent scout")
    return 0


if __name__ == "__main__":
    sys.exit(main())
