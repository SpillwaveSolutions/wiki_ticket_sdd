# `ia-ticket <ULID>` preview subcommand on `bin/worklog`

`01KYABYEQPAFJM7WC3XZV6YY76` · subtask/feature · **done**

`ia-ticket <ULID>` preview subcommand on `bin/worklog`

## Hierarchy

- task: [[Ticket-01KYABYEQPK6PV87WNZXEYRB12]] Phase 1: render ticket pages for all four levels — Add `render_item_page()` to `bin/ia_render.py`, reusing `ticket_body()` for
the description/traceability base and branching by level (subtask/task vs
story/feature/epic) for upward/downward hierarchy sections, wired into
`render_all()`.
- epic: [[Ticket-01KYABYEQP8ANXGYPBCV2T20D8]] Extend IA to tickets, PRs, and releases (artifact pages) — Give every ticket, PR, and release its own generated wiki page reusing the IA content model's wiki_key/truth_state/traceability-graph machinery already built for docs — so a reader sees hierarchy, related artifacts, and traceability in one place instead of hunting indexes/logs.

## Linked PRs

- [[PR-dd6da53]]

## Related tickets

- [github #127](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/127)
