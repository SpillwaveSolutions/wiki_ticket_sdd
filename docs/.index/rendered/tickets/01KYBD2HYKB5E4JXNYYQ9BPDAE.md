# Full test suite green + manual verification

`01KYBD2HYKB5E4JXNYYQ9BPDAE` · task/feature · **open**

Run the full suite, confirm TestCanonSync passes, and manually exercise
the incident scenario (branch -> commit -> merge onto main) plus
worklog doctor's health report on main.

## Hierarchy

- epic: [[Ticket-01KYBD2HYJVNHX698WR1JD96YC]] Branch-discipline hooks: never commit on main, always reference work — New git hooks (shipped in the plugin) that block authored commits directly on main/master and require every commit message to reference a worklog item or ticket -- prevents the local/origin main-drift incident that broke a release PR merge this session.

## Related tickets

- [github #148](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/148)
