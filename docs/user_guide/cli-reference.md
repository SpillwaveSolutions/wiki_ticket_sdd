# WikiTicket SDD — CLI Reference

Complete reference for `bin/worklog`. For concepts and workflows, start with
the [User Guide](user-guide.md); for the Claude Code plugin, see the
[Plugin Guide](plugin-guide.md).

## Global flags

| Flag | Meaning |
|---|---|
| `--actor <name>` | Who caused the event (defaults to `$USER`). Recorded on every event; goes **before** the subcommand: `bin/worklog --actor alice update …` |
| `--version` | Print the CLI version and exit |

## Subcommands

### add

Create a work item. Prints the new item's ULID.

```bash
bin/worklog add "Extract auth middleware" --type task --priority P1 \
    --parent 01J8WZZ100 --labels backend,auth
```

| Flag | Values | Default |
|---|---|---|
| `<title>` | positional, required | — |
| `--type` | `epic` `story` `task` `subtask` `bug` | `task` |
| `--priority` | `P0` `P1` `P2` `P3` | `P2` |
| `--parent <ulid>` | parent item | none |
| `--plan <path>` | plan doc that produced it | none |
| `--labels a,b` | comma-separated | none |
| `--unplanned` | flag; requires `--discovered-during` | — |
| `--discovered-during <ulid>` | what the unplanned work interrupted | — |

### update

Change status, priority, title, or labels on an open item.

```bash
bin/worklog update 01J8X0M2QQ --status in_progress --add-label urgent
```

| Flag | Values |
|---|---|
| `<item>` | positional ULID, required |
| `--status` | `todo` `in_progress` `blocked` |
| `--priority` | `P0`–`P3` |
| `--title` | new title |
| `--add-label a,b` / `--del-label a,b` | comma-separated |

At least one change flag is required.

### close

Close an item as done or cancelled.

```bash
bin/worklog close 01J8X0M2QQ --status done --resolution "merged in PR #7"
```

`--status` is `done` (default) or `cancelled`; `--resolution` is optional
free text. Closing is just an event — nothing moves files at runtime.

### list

List open items, sorted by priority. `--all` includes closed ones.

```bash
bin/worklog list --all
```

Output: short id, priority, status, external key (or `-`), title. Prints a
warning to stderr if any items carry unresolved sync conflicts.

### show

Print one item's full folded state as JSON. Accepts a unique id prefix.

```bash
bin/worklog show 01J8X0M2
```

### fold

Print the full folded state of every item (open and closed) as JSON. The
read-only building block other tooling (like the plan-next skill) consumes.

```bash
bin/worklog fold
```

### plan-capture

Turn an approved plan into a frozen plan doc plus tracked items: one epic,
one item per `- [ ]` task under a `## Tasks` heading (indented checkboxes
become subtasks; a `(P0)`–`(P3)` token sets priority). Writes
`docs/plans/<YYYY-MM-DD>-<slug>.md` and prints the path and the epic ULID.

```bash
bin/worklog plan-capture --slug auth-refactor --title "Auth refactor" --file plan.md
```

| Flag | Meaning |
|---|---|
| `--slug` | required; kebab-case, becomes the filename |
| `--title` | required; the epic's title |
| `--file` | plan markdown (reads stdin if omitted) |
| `--priority` | epic priority, default `P1` |

Refuses to overwrite an existing plan file — plans are never rewritten; pick
a new slug to supersede.

### roadmap-render

Regenerate `docs/roadmap.md` from the log. Run it after any item change and
commit the roadmap together with the log.

```bash
bin/worklog roadmap-render
```

### roadmap-snapshot

Freeze the current roadmap as a dated snapshot:
copies `docs/roadmap.md` to `docs/roadmap/<YYYY-MM-DD>_<name>.md`.

```bash
bin/worklog roadmap-snapshot --name v0.2-roadmap
```

Snapshots are frozen — the command refuses to overwrite an existing snapshot
file. `docs/roadmap.md` stays the live, regenerated view; snapshots are the
"what did the roadmap say at release time" record.

### Planned (not yet implemented)

`sync`, `status`, and `compact` exist as stubs and exit with a "not
implemented yet" message. They are planned: tracker sync, generated status
reports (daily/weekly/timecard), and CI-only log compaction.

## Git hooks

Installed via `git config core.hooksPath hooks` (done for you by
`/worklog:init`). Both hooks run the same checks:

- **`hooks/pre-commit`** — on every commit:
  1. Every `.work/*.jsonl` file ends with a trailing newline (the invariant
     that keeps union merge safe).
  2. Every log line parses as JSON and carries the required event fields
     (`ev`, `ts`, `actor`, `op`, and `item` except on `compact` events).
  3. `docs/roadmap.md` is fresh: the hook regenerates it and diffs — a stale
     or hand-edited roadmap blocks the commit
     (`Run: worklog roadmap-render`).
  4. The fold test suite passes (only in repos that carry `tests/`).
- **`hooks/pre-merge-commit`** — the same script. Git does *not* run
  `pre-commit` for merge auto-commits, so without this a merge could
  silently land a stale roadmap or a smuggled corrupt line. If it blocks
  your merge: `bin/worklog roadmap-render && git add -A && git commit
  --no-edit`.

CI runs the same script on every push and PR, so bypassing the local hook
with `--no-verify` only defers the failure.

## Invariants worth knowing

- **Never hand-edit `.work/*.jsonl`** — no editors, no `echo >>`. The CLI's
  `append()` is the only writer; it does a single atomic newline-terminated
  write and self-heals a missing trailing newline left by a hand edit.
- **Never hand-edit `docs/roadmap.md`.** It's generated; change the work
  items and re-render.
- **Every `.jsonl` write is newline-terminated.** A missing final newline is
  how two events fuse into one corrupt, unparseable line.
- **Item bodies are capped at 2 KB** in the log (keeps appends atomic under
  `PIPE_BUF`). Longer prose belongs in the plan doc.
- **`sync`, `status`, `compact` are stubs** — planned, not implemented.
  Don't script against them yet.
