# Cap counts only items present in done.jsonl and unparseable ts never occupies a cap slot

`01M2XCWMVD7KJ01FCNEV1X822X` · subtask/bug · **open**

The FIFO cap currently counts archived items and evicts real ones once the archive exceeds the cap.

## Hierarchy

- task: [[Ticket-01M2XCWMVD7KJ01FCNEV1X822V]] Retention: stop re-snapshotting archived items into done.jsonl — done_state folds done and archive together, refreshed ids are pruned from the archive, and archive appends dedupe by item with the newest snapshot winning.
- epic: [[Ticket-01M2XCWMV0QYM4ZRBWN1V1327B]] Fix the v0.24.10 review findings and close #412 and #413 — The v0.24.10 change review found a P0 in retention (archived items ping-pong back into done.jsonl), a merge gate that trusts commit statuses from any actor, and seven releases without regenerated design docs.
