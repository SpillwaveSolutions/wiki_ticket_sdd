# Retention: stop re-snapshotting archived items into done.jsonl

`01M2XCWMVD7KJ01FCNEV1X822V` · task/bug · **done**

done_state folds done and archive together, refreshed ids are pruned from the archive, and archive appends dedupe by item with the newest snapshot winning.

## Hierarchy

- epic: [[Ticket-01M2XCWMV0QYM4ZRBWN1V1327B]] Fix the v0.24.10 review findings and close #412 and #413 — The v0.24.10 change review found a P0 in retention (archived items ping-pong back into done.jsonl), a merge gate that trusts commit statuses from any actor, and seven releases without regenerated design docs.

## Subtasks

- [[Ticket-01M2XCWMVD7KJ01FCNEV1X822X]] Cap counts only items present in done.jsonl and unparseable ts never occupies a cap slot — The FIFO cap currently counts archived items and evicts real ones once the archive exceeds the cap. (done)
- [[Ticket-01M2XCWMVD7KJ01FCNEV1X822Z]] Parent veto in eviction, live children only — A parent is never archived while a child remains in done or todo, and an already archived child does not hold its parent back. (done)
- [[Ticket-01M2XCWMVD7KJ01FCNEV1X8231]] Tolerate a corrupt archive line and warn on ignored retention config values — A garbage line in archive.jsonl must not crash the nightly job, even when no item is open. (done)
- [[Ticket-01M2XCWMVD7KJ01FCNEV1X8233]] Archive-aware duplicate ownership check and untracked-archive guard — Merge-check folds the archive so an archived owner still blocks a duplicate link, with the archive path inferred so callers do not change. (done)
- [[Ticket-01M2XCWMVD7KJ01FCNEV1X8235]] Retention tests and doc renumbering — Add the eight test classes listed in the plan, add test_retention and test_watermark to the explicit CI list, and fix the step order in the compact.py header, the spec, the CLI reference, and the README. (done)

Progress: 5/5 done

## Linked PRs

- [[PR-434]]

## Related tickets

- [github #415](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/415)
