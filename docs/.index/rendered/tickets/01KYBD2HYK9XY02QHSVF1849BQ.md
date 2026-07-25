# Wire commit-msg into install/uninstall/doctor/CANON

`01KYBD2HYK9XY02QHSVF1849BQ` · task/feature · **open**

plugin/scripts/init.sh's hook-copy loop and CI template,
plugin/scripts/uninstall.sh's removal loop, plugin/scripts/doctor.sh's
existence check, tests/test_plugin.py's CANON list.

## Hierarchy

- epic: [[Ticket-01KYBD2HYJVNHX698WR1JD96YC]] Branch-discipline hooks: never commit on main, always reference work — New git hooks (shipped in the plugin) that block authored commits directly on main/master and require every commit message to reference a worklog item or ticket -- prevents the local/origin main-drift incident that broke a release PR merge this session.

## Related tickets

- [github #147](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/147)
