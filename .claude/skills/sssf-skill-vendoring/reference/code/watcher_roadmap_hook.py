# From weather-report adws/adw_watch.py. Replace commit_watcher_state() in your
# adw_watch.py with this (add `import subprocess`), so every claim/resolve commit
# also regenerates .okf/roadmap/ via scripts/sync_okf_roadmap.py.

ROADMAP_SYNC = Path("scripts/sync_okf_roadmap.py")


def commit_watcher_state(message: str) -> None:
    """Commit the watcher's own claim/resolve writes to the issue file.

    The ADW's own commit phase (inside adw_simple_sdlc.main) fires mid-run,
    before dispatch() writes the final Status: -- so without this, that final
    write sits uncommitted after every run, needing a manual follow-up commit.
    is_dirty() guards against there being nothing to commit (e.g. a crash
    before set_status ran).

    If the repo has a roadmap generator, regenerate first so the commit that
    flips a ticket's Status: also carries it into .okf/roadmap/. The documenter
    runs before resolve, so it only ever sees the ticket as `claimed`. A failing
    generator never blocks the watcher; the bundle validator catches drift."""
    if ROADMAP_SYNC.is_file():
        subprocess.run(["uv", "run", str(ROADMAP_SYNC)], capture_output=True, text=True)
    if git_helper.is_dirty():
        sha = git_helper.commit_all(message)
        print(f"just watch: committed watcher state ({sha}): {message}")
