# Add TestBranchGuard and TestCommitMsgReference test classes

`01KYBD2HYKJHS5M2PFZ78Y585C` · task/feature · **open**

New tests in tests/test_integration.py covering: commit on main
rejected, commit on branch succeeds, merge onto main allowed (the
incident scenario), message without reference rejected, message with
ULID/ticket passes, merge commit message exempt.

## Hierarchy

- epic: [[Ticket-01KYBD2HYJVNHX698WR1JD96YC]] Branch-discipline hooks: never commit on main, always reference work — New git hooks (shipped in the plugin) that block authored commits directly on main/master and require every commit message to reference a worklog item or ticket -- prevents the local/origin main-drift incident that broke a release PR merge this session.
