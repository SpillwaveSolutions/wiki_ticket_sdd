# Add a CI step validating commit messages on PRs

`01KYBD2HYKYBBNGDMCQSW4VE2T` · task/feature · **done**

Walk git rev-list --no-merges base..HEAD through hooks/commit-msg in
.github/workflows/worklog.yml (template and this repo's installed
copy); needs fetch-depth 0.

## Hierarchy

- epic: [[Ticket-01KYBD2HYJVNHX698WR1JD96YC]] Branch-discipline hooks: never commit on main, always reference work — New git hooks (shipped in the plugin) that block authored commits directly on main/master and require every commit message to reference a worklog item or ticket -- prevents the local/origin main-drift incident that broke a release PR merge this session.

## Related tickets

- [github #154](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/154)
