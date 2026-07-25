# Mirror to plugin/scripts/commit-msg (byte-identical canon copy)

`01KYBD2HYK1AT1YCN3GW8Q3QQW` · subtask/feature · **done**

Mirror to plugin/scripts/commit-msg (byte-identical canon copy)

## Hierarchy

- task: [[Ticket-01KYBD2HYKKZM22DFM16ZJXYFG]] Create hooks/commit-msg requiring a ULID or ticket reference — New hook: exempt merge commits via MERGE_HEAD, otherwise require a
26-char Crockford ULID or #123 ticket reference in the message, reusing
the bin/ulid.py alphabet.
- epic: [[Ticket-01KYBD2HYJVNHX698WR1JD96YC]] Branch-discipline hooks: never commit on main, always reference work — New git hooks (shipped in the plugin) that block authored commits directly on main/master and require every commit message to reference a worklog item or ticket -- prevents the local/origin main-drift incident that broke a release PR merge this session.

## Related tickets

- [github #146](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/146)
