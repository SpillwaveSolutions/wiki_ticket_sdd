# Phase 1: render ticket pages for all four levels

`01KYABYEQPK6PV87WNZXEYRB12` · task/feature · **done**

Add `render_item_page()` to `bin/ia_render.py`, reusing `ticket_body()` for
the description/traceability base and branching by level (subtask/task vs
story/feature/epic) for upward/downward hierarchy sections, wired into
`render_all()`.

## Hierarchy

- epic: [[Ticket-01KYABYEQP8ANXGYPBCV2T20D8]] Extend IA to tickets, PRs, and releases (artifact pages) — Give every ticket, PR, and release its own generated wiki page reusing the IA content model's wiki_key/truth_state/traceability-graph machinery already built for docs — so a reader sees hierarchy, related artifacts, and traceability in one place instead of hunting indexes/logs.

## Subtasks

- [[Ticket-01KYABYEQP9FDY8THDV79F324G]] One-line summary derivation from body's first sentence (no cache) — One-line summary derivation from body's first sentence (no cache) (done)
- [[Ticket-01KYABYEQPAFJM7WC3XZV6YY76]] `ia-ticket <ULID>` preview subcommand on `bin/worklog` — `ia-ticket <ULID>` preview subcommand on `bin/worklog` (done)
- [[Ticket-01KYABYEQPRM8308SYFPR8X437]] Aggregate progress rollup for Story/Feature/Epic pages — Aggregate progress rollup for Story/Feature/Epic pages (done)

Progress: 3/3 done

## Related tickets

- [github #130](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/130)
