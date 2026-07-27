# Clear post-v0.17.0 drift and fix the prefix-ULID log corruption

`01KYJYG4PX7NVTS1CZQ8MPES7T` · epic/feature · **open**

After v0.17.0 shipped, a sweep of the work log against the actual repo found four items that no longer match reality — a closed-out release still marked open, a finished epic still open and therefore invisible on the roadmap, a session health check that cries wolf on every start, and two abandoned worktrees.

## Children

- [[Ticket-01KYJYG4PY6TE6ZTZMF8CV2VFT]] Accept an absolute core.hooksPath in the doctor checks — The session-start health check compares the configured git hooks path
against the literal string "hooks", so a repo wired with the full absolute
path — the form that actually works inside a git worktree — is reported as
broken every session. (open)
- [[Ticket-01KYJYG4PY8S8RZNB9AYP3G8GW]] Regression tests for id-prefix resolution — Cover the cases that were broken: closing by short id updates the real item
and creates no phantom, updating a closed item by short id is refused, an
unknown id fails loudly, and an ambiguous short id names the candidates. (open)
- [[Ticket-01KYJYG4PYDA4H10JXXRDRCXPZ]] Resolve work-item id prefixes in close and update — Closing or updating an item by the short 8-character id that the tool itself
prints creates a brand-new phantom item instead of touching the real one,
silently corrupting the work log. (done)
- [[Ticket-01KYJYG4PYFFTK74AZ7RW90M7R]] Close out stale work-log bookkeeping — Two items no longer reflect reality: a release task for a version that
shipped three releases ago, and an epic whose every child is finished but
which is itself still open — and therefore invisible on the generated
roadmap. (open)
- [[Ticket-01KYJYG4PYJRAFEHJCP51XVCRA]] Remove two abandoned git worktrees — Two worktrees left over from earlier agent runs sit in the repo; both of
their branches are already merged. (open)

Progress: 1/5 done
