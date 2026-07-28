# Accept an absolute core.hooksPath in the doctor checks

`01KYJYG4PY6TE6ZTZMF8CV2VFT` · task/bug · **done**

The session-start health check compares the configured git hooks path
against the literal string "hooks", so a repo wired with the full absolute
path — the form that actually works inside a git worktree — is reported as
broken every session.

## Hierarchy

- epic: [[Ticket-01KYJYG4PX7NVTS1CZQ8MPES7T]] Clear post-v0.17.0 drift and fix the prefix-ULID log corruption — After v0.17.0 shipped, a sweep of the work log against the actual repo found four items that no longer match reality — a closed-out release still marked open, a finished epic still open and therefore invisible on the roadmap, a session health check that cries wolf on every start, and two abandoned worktrees.

## Release

- [[Release-v0.17.1]]

## Related tickets

- [github #209](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/209)
