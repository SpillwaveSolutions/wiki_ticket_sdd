# Phase 0: add item/release page-name helpers and extend build_manifest()

`01KYABYEQPXZAAY0VWF6Z8TQ27` · task/feature · **done**

Add `item_page_name(iid, it)` and `release_page_name(tag)` to
`bin/ia_render.py` next to `page_name()`, and extend `build_manifest()` to
loop work items and release tags in addition to doc records, so every
item/PR/release gets a manifest slot.

## Hierarchy

- epic: [[Ticket-01KYABYEQP8ANXGYPBCV2T20D8]] Extend IA to tickets, PRs, and releases (artifact pages) — Give every ticket, PR, and release its own generated wiki page reusing the IA content model's wiki_key/truth_state/traceability-graph machinery already built for docs — so a reader sees hierarchy, related artifacts, and traceability in one place instead of hunting indexes/logs.

## Related tickets

- [github #135](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/135)
