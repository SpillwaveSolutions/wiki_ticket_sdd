# Extend IA to tickets, PRs, and releases (artifact pages)

`01KYABYEQP8ANXGYPBCV2T20D8` · epic/feature · **open**

Give every ticket, PR, and release its own generated wiki page reusing the IA content model's wiki_key/truth_state/traceability-graph machinery already built for docs — so a reader sees hierarchy, related artifacts, and traceability in one place instead of hunting indexes/logs.

## Children

- [[Ticket-01KYABYEQP3YCB9AVHRPCTCMRS]] Phase 0: add item_links() graph helper — Add `item_links(iid, graph)` to `bin/ia_graph.py` — one shared
parent/children/PR/release adjacency lookup, reusing the fwd/back pattern
already in `render_traceability`, so ticket/PR/release renderers don't
each reimplement graph traversal. (done)
- [[Ticket-01KYABYEQPDS2VFQKQ7B6YXZVR]] Phase 4: regenerate all pages and confirm coverage gate holds — Run `worklog ia-render`, verify CI diff-clean, confirm bin/ia*.py stays
at or above the 80%/95% coverage target. (open)
- [[Ticket-01KYABYEQPF8N2K26ENRKREE0W]] Phase 3: file PR live-metadata follow-up item — After Phases 0-2 land, file a separate kind:feature child item for
`worklog pr-sync` (gh pr view integration) — not implemented in this epic. (open)
- [[Ticket-01KYABYEQPK6PV87WNZXEYRB12]] Phase 1: render ticket pages for all four levels — Add `render_item_page()` to `bin/ia_render.py`, reusing `ticket_body()` for
the description/traceability base and branching by level (subtask/task vs
story/feature/epic) for upward/downward hierarchy sections, wired into
`render_all()`. (done)
- [[Ticket-01KYABYEQPNK7HHH5CMAR2V1JG]] Phase 4: extend tests/test_ia.py for the new page shapes — Add page-shape tests per ticket level, a PR-page test, a release-page
test, and a manifest-growth assertion to the existing test fixture
classes — do not fork a new test file. (open)
- [[Ticket-01KYABYEQPP82DJEN19F43YRAE]] Phase 2: render release pages with graph-derived Change Log — Add `render_release_page()` — Change Log section built from milestone-
tagged closed items and their linked PRs (not a CHANGELOG.md parser),
plus Release Tree, Related PRs, Related Tickets, Dependencies sections. (done)
- [[Ticket-01KYABYEQPW8Q2RGGTNP71W88E]] Phase 2: render PR pages — Add `render_pr_page()` — title/status, linked tickets via reverse
lands-in edges, related release via targets; files-changed/test-review
status render as "not tracked" pending the Phase 3 follow-up. (done)
- [[Ticket-01KYABYEQPXZAAY0VWF6Z8TQ27]] Phase 0: add item/release page-name helpers and extend build_manifest() — Add `item_page_name(iid, it)` and `release_page_name(tag)` to
`bin/ia_render.py` next to `page_name()`, and extend `build_manifest()` to
loop work items and release tags in addition to doc records, so every
item/PR/release gets a manifest slot. (done)

Progress: 5/8 done

## Related tickets

- [github #125](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/125)
