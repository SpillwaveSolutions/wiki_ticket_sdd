# Update test fixtures for the new hooks

`01KYBD2HYKG0DW7QJX7XG561A8` · task/feature · **done**

tests/test_integration.py (~23 commit_all calls) and
tests/test_plugin.py (3 raw git commit calls) mostly commit on main with
no-reference messages -- give pure setup commits no_verify=True or move
them onto a branch via Sandbox.branch(), following the file's existing
precedent; leave the four pre-commit-content-testing call sites alone.

## Hierarchy

- epic: [[Ticket-01KYBD2HYJVNHX698WR1JD96YC]] Branch-discipline hooks: never commit on main, always reference work — New git hooks (shipped in the plugin) that block authored commits directly on main/master and require every commit message to reference a worklog item or ticket -- prevents the local/origin main-drift incident that broke a release PR merge this session.

## Related tickets

- [github #150](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/150)
