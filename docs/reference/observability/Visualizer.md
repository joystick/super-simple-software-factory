---
title: Visualizer
---

# Visualizer

The Visualizer is the swim-lane trace UI at
`.claude/skills/sssf/apps/visualizer/` — a small Bun/Vite web app (server +
frontend, see its `server/`, `src/`, `shared/` subdirectories) that reads the
same SQLite trace database the `Tracer` writes to and renders it as a
readable timeline, rather than a table of raw `EventRecord` rows.

## Categorization note

This is deliberately documented as an **app**, not an `adw_modules/` class.
An earlier pass of this glossary's concept inventory implied "Visualizer" was
a module symbol alongside `Tracer`/`EventRecord`; a fable critique corrected
that — there is no such class. It's a standalone process you boot
separately, pointed at a trace database.

## Booting it

```bash
just obs
```

Source: `.claude/skills/sssf/templates/justfile:97-105`. The recipe:

```
obs:
    cd .claude/skills/sssf/apps/visualizer && bun install && (SSSF_DB={{justfile_directory()}}/{{db}} bun run server/index.ts &) && bunx vite
```

`SSSF_DB` is passed explicitly because the server process runs from the app's
own directory (`apps/visualizer/`), so without it the server would look for a
trace database sitting next to itself rather than the real one at the
project's `db` path. The UI serves at `http://localhost:4601`, its API at
`:4600`.

## What it reads

The same two-store trace data described in
`.claude/skills/sssf/references/observability.md#two-stores-one-truth` and
`#event-schema` — every phase, log line, and process record an ADW run
writes. The swim-lane layout groups events by `adw_id`/phase the same way
`Console` (`quality-gates-and-permissions/Console.md`) narrates them to the
terminal — the Visualizer is the same story, viewed after the fact, in a
browser instead of scrollback.

## See also

- `.claude/skills/sssf/references/observability.md` — the schema and tables
  the Visualizer reads.
- `quality-gates-and-permissions/Console.md` — the terminal-side narrator of
  the same events, live.
