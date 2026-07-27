# Regression tests for id-prefix resolution

`01KYJYG4PY8S8RZNB9AYP3G8GW` · task/bug · **open**

Cover the cases that were broken: closing by short id updates the real item
and creates no phantom, updating a closed item by short id is refused, an
unknown id fails loudly, and an ambiguous short id names the candidates.

## Hierarchy

- epic: [[Ticket-01KYJYG4PX7NVTS1CZQ8MPES7T]] Clear post-v0.17.0 drift and fix the prefix-ULID log corruption — After v0.17.0 shipped, a sweep of the work log against the actual repo found four items that no longer match reality — a closed-out release still marked open, a finished epic still open and therefore invisible on the roadmap, a session health check that cries wolf on every start, and two abandoned worktrees.
