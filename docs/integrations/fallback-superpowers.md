# Integration: Superpowers

## When to use

You're using Superpowers (the `superpowers:*` skill family — brainstorming,
systematic-debugging, test-driven-development, executing-plans, and
friends) alongside `wiki_ticket_sdd` for work tracking, and want to know
how the two fit together.

## One-command setup

Nothing to install on the `wiki_ticket_sdd` side — Superpowers is a
separate Claude Code plugin/skill set with its own install path. If it's
already showing up in your skills list, you're set; if not, follow
Superpowers' own install instructions, not this repo's.

## Adapter configuration

Not applicable. Superpowers has no ticketing or wiki adapter concept —
there is nothing to set in `.work/config.yml` for it. This page is purely
about workflow composition, not sync configuration.

## Recommended workflow

Superpowers owns *how you think through and execute* a change
(brainstorming → plan → TDD → execute → review). `wiki_ticket_sdd` owns
*the record of that work* (work items, plans, tickets, wiki pages). They
compose in sequence, not in parallel:

1. Use `superpowers:brainstorming` and `superpowers:writing-plans` to shape
   the approach.
2. Once a plan is approved, capture it with this repo's `plan-capture`
   skill — that's what turns the design into tracked work items
   (`docs/plans/<date>-<slug>.md` + `.work/todo.jsonl` entries), not
   Superpowers' own plan-writing output.
3. Execute with `superpowers:test-driven-development` /
   `superpowers:executing-plans` as normal.
4. Close out with this repo's usual `worklog` flow (`update`/`close`,
   `roadmap-render`, `ticket-sync`, `wiki-publish`).

In short: let Superpowers drive engineering discipline, let
`wiki_ticket_sdd` be the system of record. Don't let both try to own the
plan document — `plan-capture`'s output is the one that gets tracked and
published.

## Mapping events

There's no ticket/issue system underneath Superpowers to map events to.
The only "event" that matters is plan approval, which is captured exactly
once via `plan-capture` regardless of which planning skill produced the
draft.

## Pulling changes

Not applicable — nothing external to pull from. Superpowers doesn't hold
its own state that could drift from `.work/todo.jsonl`.

## Rendering support

Once a Superpowers-originated plan is captured, it renders like any other
plan: `docs/.index/rendered/tickets/<ULID>.md` for its work items, and the
frozen plan doc itself publishes to the wiki via the normal
`wiki-publish` flow. No special rendering exists for Superpowers content.

## Gotchas & troubleshooting

- Don't run `superpowers:writing-plans` and `plan-capture` as if they're
  the same step — writing-plans produces the design, `plan-capture` is
  what makes it a tracked work item. Skipping the second step means the
  plan exists but nothing shows up on the roadmap.
- If Superpowers isn't in your skill list at all, that's a Superpowers
  installation problem, not a `wiki_ticket_sdd` one — this repo has no
  dependency on it being present.

## Last updated

2026-07-25 — [edit this page](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki/Integration-Superpowers/_edit)
