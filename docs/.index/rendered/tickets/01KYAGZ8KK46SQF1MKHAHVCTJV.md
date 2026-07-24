# worklog sync --pull can never bootstrap: cursor-less pull calls the adapter with no --since, which it requires

`01KYAGZ8KK46SQF1MKHAHVCTJV` · task/bug · **open**

sync_dispatch.py's pull step calls the adapter with no --since/--keys when .work/sync-state.json has no 'cursors' entry yet for a repo -- but the adapter's own contract requires one of --since <iso> or --keys, so the very first pull always fails (exit 1: 'pull requires --since <iso> or --keys').

## Related tickets

- [github #141](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/141)
