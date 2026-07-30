# Run the log merge guard in continuous integration

`01KYTJGK2XJD516RXMZ52PDZP1` · task/feature · **open**

The guard added for the resurrection bug is gated on a merge being in progress, which
is never true in a continuous-integration checkout, so it protects only developer
machines today.

## Hierarchy

- epic: [[Ticket-01KYTJGK2WMX6PNMYQDFFFPGTP]] Close both P1 epics, settle the merge-strategy and GONE questions — Follow-on session after the 2026-07-30 bug sweep cleared every defect in the tracker.

## Related tickets

- [github #262](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/262)
