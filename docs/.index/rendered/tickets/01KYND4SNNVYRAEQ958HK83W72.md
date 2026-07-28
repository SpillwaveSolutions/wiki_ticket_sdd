# One local owner per remote ticket (#226)

`01KYND4SNNVYRAEQ958HK83W72` · epic/feature · **done**

Two local work items were allowed to point at the same ticket in the external tracker.

## Children

- [[Ticket-01KYND4SNNCPZ7R2NWFD7QXYTJ]] Add an external-key ownership map to the fold — One shared helper that answers "which items claim this remote ticket", so the
link command and the sync dispatcher enforce the same rule from the same place
instead of each growing its own copy. (done)
- [[Ticket-01KYND4SNP68XAJ30Q4PY4VV11]] Stop sync from pushing a ticket that two items claim — Skip every item in a contested set, print a prominent block naming all claimants
and the exact repair, and exit non-zero so the failure cannot be missed. (done)
- [[Ticket-01KYND4SNPBAW2A1H0GPHDGT0E]] Update the mirrored copies, the docs and the changelog — The command scripts ship in two places that must stay byte-identical. (done)
- [[Ticket-01KYND4SNPF2DYKSMDG4NJ39CF]] Refuse a duplicate external key when linking — Linking an item to a ticket another item already owns is the mistake that causes
the corruption. (done)
- [[Ticket-01KYND4SNPG1HFE8E0P7F7K7PF]] Keep sync's automatic linking from ever aborting a run — Sync records the ticket key right after creating the ticket. (done)
- [[Ticket-01KYND4SNPH307DFDEE9BJ0ZZ4]] Make undoing or moving a link actually re-push — The change detection only looks at an item's content, so unlinking or re-pointing
it is silently a no-op and the damaged ticket is never repaired. (done)
- [[Ticket-01KYND4SNPXVR1W4GQA453VB4G]] Add a command to undo a link — A mistaken link is currently impossible to undo through supported commands, which
is a sharp edge in a log designed so that mistakes are corrected by appending. (done)

Progress: 7/7 done

## Related tickets

- [github #226](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/226)
