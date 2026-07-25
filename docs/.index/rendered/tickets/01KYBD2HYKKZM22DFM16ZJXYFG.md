# Create hooks/commit-msg requiring a ULID or ticket reference

`01KYBD2HYKKZM22DFM16ZJXYFG` · task/feature · **done**

New hook: exempt merge commits via MERGE_HEAD, otherwise require a
26-char Crockford ULID or #123 ticket reference in the message, reusing
the bin/ulid.py alphabet.

## Hierarchy

- epic: [[Ticket-01KYBD2HYJVNHX698WR1JD96YC]] Branch-discipline hooks: never commit on main, always reference work — New git hooks (shipped in the plugin) that block authored commits directly on main/master and require every commit message to reference a worklog item or ticket -- prevents the local/origin main-drift incident that broke a release PR merge this session.

## Subtasks

- [[Ticket-01KYBD2HYK1AT1YCN3GW8Q3QQW]] Mirror to plugin/scripts/commit-msg (byte-identical canon copy) — Mirror to plugin/scripts/commit-msg (byte-identical canon copy) (done)

Progress: 1/1 done

## Related tickets

- [github #153](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/153)
