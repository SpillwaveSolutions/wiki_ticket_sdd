---
name: work-track
description: Track work items — use when creating, updating, closing, or listing work items, or when discovering unplanned work mid-flight ("we also need to…", a bug found while doing something else).
version: 0.1.0
---

# Work tracking

All state changes go through `bin/worklog`. Never edit `.work/*.jsonl` by
hand or with shell redirects (invariant 15.4) — the CLI's `append()` is the
only writer.

## Add an item

    bin/worklog add "<title>" [--type epic|story|task|subtask|bug] \
        [--priority P0-P3] [--parent <ulid>] [--labels a,b]

## Unplanned discoveries

Work discovered mid-flight ("we also need to…", a bug found while doing
something else) MUST be recorded BEFORE doing the work:

    bin/worklog add "<title>" --unplanned --discovered-during <current-item-ulid>

`--unplanned` requires `--discovered-during` (spec 5.4).

## Update / close

    bin/worklog update <ulid> [--status todo|in_progress|blocked] \
        [--priority P0-P3] [--add-label a] [--del-label b]
    bin/worklog close <ulid> --status done|cancelled [--resolution "..."]

## Inspect

    bin/worklog list          # open items
    bin/worklog list --all    # includes closed
    bin/worklog show <id-prefix>

## After any change

Run `bin/worklog roadmap-render` and commit the log and roadmap together
(`.work/todo.jsonl` + `docs/roadmap.md`) — the pre-commit hook rejects a
stale roadmap.

## After merging branches

The logs union-merge without conflict, but `docs/roadmap.md` may conflict or
go stale (both sides regenerated it). Recovery is always the same: run
`bin/worklog roadmap-render`, `git add -A`, and finish the merge commit. The
pre-merge-commit hook blocks any merge that would land a stale roadmap.
