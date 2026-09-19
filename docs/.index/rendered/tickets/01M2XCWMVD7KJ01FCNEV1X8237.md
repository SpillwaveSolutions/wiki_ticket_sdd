# #412: consult the remote marker map before creating a ticket

`01M2XCWMVD7KJ01FCNEV1X8237` · task/bug · **open**

observe_remote already fetches every remote ticket.

## Hierarchy

- epic: [[Ticket-01M2XCWMV0QYM4ZRBWN1V1327B]] Fix the v0.24.10 review findings and close #412 and #413 — The v0.24.10 change review found a P0 in retention (archived items ping-pong back into done.jsonl), a merge gate that trusts commit statuses from any actor, and seven releases without regenerated design docs.

## Subtasks

- [[Ticket-01M2XCWMVEH3XFP2VPS9JBD6X7]] Probe guard when the listing fails and the clone has no push memory — A transient listing failure on a fresh clone is the #412 scenario. (open)
- [[Ticket-01M2XCWMVEH3XFP2VPS9JBD6X9]] sync --explain and report hints — Print which key source answered for one item without mutating anything, forward the flag through cmd_sync, report probe hits in a new relinked count, and suggest dedupe --dry-run when the sync created tickets. (open)
- [[Ticket-01M2XCWMVEH3XFP2VPS9JBD6XB]] adapter check says when the clone has no push memory — A fresh clone must not see output that claims it has push memory. (open)

Progress: 0/3 done

## Related tickets

- [github #421](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/421)
