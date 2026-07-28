# Resolve work-item id prefixes in close and update

`01KYJYG4PYDA4H10JXXRDRCXPZ` · task/feature · **done**

Closing or updating an item by the short 8-character id that the tool itself
prints creates a brand-new phantom item instead of touching the real one,
silently corrupting the work log.

## Hierarchy

- epic: [[Ticket-01KYJYG4PX7NVTS1CZQ8MPES7T]] Clear post-v0.17.0 drift and fix the prefix-ULID log corruption — After v0.17.0 shipped, a sweep of the work log against the actual repo found four items that no longer match reality — a closed-out release still marked open, a finished epic still open and therefore invisible on the roadmap, a session health check that cries wolf on every start, and two abandoned worktrees.

## Release

- [[Release-v0.17.1]]
