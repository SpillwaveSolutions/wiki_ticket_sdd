# #413: CI as the authoritative syncer behind ticketing.sync_owner: ci

`01M2XCWMVEH3XFP2VPS9JBD6XN` · task/feature · **done**

post-merge sets the adapter env, runs a push-only sync with the bot token before rendering, stages the log with the docs, and caches sync-state.

## Hierarchy

- epic: [[Ticket-01M2XCWMV0QYM4ZRBWN1V1327B]] Fix the v0.24.10 review findings and close #412 and #413 — The v0.24.10 change review found a P0 in retention (archived items ping-pong back into done.jsonl), a merge gate that trusts commit statuses from any actor, and seven releases without regenerated design docs.

## Related tickets

- [github #429](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/429)
