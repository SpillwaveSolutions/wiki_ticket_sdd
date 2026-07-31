# Record the decision that clearing a dead ticket link stays manual

`01KYTJGK2X7FFZC5BCYF2BPSSF` · task/feature · **done**

Write the architecture decision record explaining why automation is unsafe: the gone
signal is a substring match that cannot separate a deleted ticket from one you lack
permission to read, and clearing a link leaves the remote marker in place so a later
pull can re-attribute the old ticket.

## Hierarchy

- epic: [[Ticket-01KYTJGK2WMX6PNMYQDFFFPGTP]] Close both P1 epics, settle the merge-strategy and GONE questions — Follow-on session after the 2026-07-30 bug sweep cleared every defect in the tracker.

## Related tickets

- [github #258](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/258)
