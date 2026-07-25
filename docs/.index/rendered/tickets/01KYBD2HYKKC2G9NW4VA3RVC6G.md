# Add the branch-guard block to hooks/pre-commit

`01KYBD2HYKKC2G9NW4VA3RVC6G` · task/feature · **done**

Insert the MERGE_HEAD-exempt, WORKLOG_SKIP_BRANCH_GUARD-overridable check
that fails when HEAD is main/master, right after fail() is defined.

## Hierarchy

- epic: [[Ticket-01KYBD2HYJVNHX698WR1JD96YC]] Branch-discipline hooks: never commit on main, always reference work — New git hooks (shipped in the plugin) that block authored commits directly on main/master and require every commit message to reference a worklog item or ticket -- prevents the local/origin main-drift incident that broke a release PR merge this session.

## Related tickets

- [github #152](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/152)
