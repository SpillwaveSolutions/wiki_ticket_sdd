# Add WORKLOG_SKIP_BRANCH_GUARD to the three bare pre-commit call sites

`01KYBD2HYK196RQN7JNCMV6PDS` · task/feature · **done**

plugin/scripts/doctor.sh's own invocation, plugin/scripts/init.sh's CI
backstop step, and tests/test_integration.py's two "CI would pass"
assertions -- these run hooks/pre-commit with no real commit in flight
and would otherwise false-positive on main.

## Hierarchy

- epic: [[Ticket-01KYBD2HYJVNHX698WR1JD96YC]] Branch-discipline hooks: never commit on main, always reference work — New git hooks (shipped in the plugin) that block authored commits directly on main/master and require every commit message to reference a worklog item or ticket -- prevents the local/origin main-drift incident that broke a release PR merge this session.

## Linked PRs

- [[PR-155]]

## Related tickets

- [github #145](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/145)
