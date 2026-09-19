# Archive-aware duplicate ownership check and untracked-archive guard

`01M2XCWMVD7KJ01FCNEV1X8233` · subtask/bug · **done**

Merge-check folds the archive so an archived owner still blocks a duplicate link, with the archive path inferred so callers do not change.

## Hierarchy

- task: [[Ticket-01M2XCWMVD7KJ01FCNEV1X822V]] Retention: stop re-snapshotting archived items into done.jsonl — done_state folds done and archive together, refreshed ids are pruned from the archive, and archive appends dedupe by item with the newest snapshot winning.
- epic: [[Ticket-01M2XCWMV0QYM4ZRBWN1V1327B]] Fix the v0.24.10 review findings and close #412 and #413 — The v0.24.10 change review found a P0 in retention (archived items ping-pong back into done.jsonl), a merge gate that trusts commit statuses from any actor, and seven releases without regenerated design docs.

## Linked PRs

- [[PR-434]]

## Related tickets

- [github #419](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/419)
