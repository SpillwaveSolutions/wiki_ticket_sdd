# Remove the "direct-commit repos" mode from the release skill

`01KYBD2HYKET7WJARQFB2NVMFS` · task/feature · **done**

plugin/skills/release/SKILL.md section 3 currently documents committing
release stamps directly on the default branch -- dead once the branch
guard ships; describe branch+PR landing only.

## Hierarchy

- epic: [[Ticket-01KYBD2HYJVNHX698WR1JD96YC]] Branch-discipline hooks: never commit on main, always reference work — New git hooks (shipped in the plugin) that block authored commits directly on main/master and require every commit message to reference a worklog item or ticket -- prevents the local/origin main-drift incident that broke a release PR merge this session.

## Linked PRs

- [[PR-155]]

## Related tickets

- [github #149](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/149)
