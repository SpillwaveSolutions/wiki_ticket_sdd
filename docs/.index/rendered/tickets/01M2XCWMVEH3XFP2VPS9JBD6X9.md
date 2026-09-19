# sync --explain and report hints

`01M2XCWMVEH3XFP2VPS9JBD6X9` · subtask/bug · **open**

Print which key source answered for one item without mutating anything, forward the flag through cmd_sync, report probe hits in a new relinked count, and suggest dedupe --dry-run when the sync created tickets.

## Hierarchy

- task: [[Ticket-01M2XCWMVD7KJ01FCNEV1X8237]] #412: consult the remote marker map before creating a ticket — observe_remote already fetches every remote ticket.
- epic: [[Ticket-01M2XCWMV0QYM4ZRBWN1V1327B]] Fix the v0.24.10 review findings and close #412 and #413 — The v0.24.10 change review found a P0 in retention (archived items ping-pong back into done.jsonl), a merge gate that trusts commit statuses from any actor, and seven releases without regenerated design docs.
