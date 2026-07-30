# Phase 0: add item_links() graph helper

`01KYABYEQP3YCB9AVHRPCTCMRS` · task/feature · **done**

Add `item_links(iid, graph)` to `bin/ia_graph.py` — one shared
parent/children/PR/release adjacency lookup, reusing the fwd/back pattern
already in `render_traceability`, so ticket/PR/release renderers don't
each reimplement graph traversal.

## Hierarchy

- epic: [[Ticket-01KYABYEQP8ANXGYPBCV2T20D8]] Extend IA to tickets, PRs, and releases (artifact pages) — Give every ticket, PR, and release its own generated wiki page reusing the IA content model's wiki_key/truth_state/traceability-graph machinery already built for docs — so a reader sees hierarchy, related artifacts, and traceability in one place instead of hunting indexes/logs.

## Linked PRs

- [[PR-cab8952]]

## Related tickets

- [github #124](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/124)
