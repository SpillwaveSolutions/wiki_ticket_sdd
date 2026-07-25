# Integration: GSD

## When to use

You're using GSD (Get Shit Done — the `gsd:*` skill family: roadmapping,
phase planning, execute-phase, verify-work) alongside `wiki_ticket_sdd`,
and want to know which tool owns which part of the work.

## One-command setup

Nothing to install on the `wiki_ticket_sdd` side — GSD is a separate
Claude Code plugin/skill set. If `gsd:*` commands already appear in your
skill list, nothing further is needed here; otherwise follow GSD's own
setup, not this repo's.

## Adapter configuration

Not applicable. GSD has no ticketing/wiki adapter concept, so there's
nothing to configure in `.work/config.yml`.

## Recommended workflow

GSD structures a milestone into phases with its own `PLAN.md`/roadmap
concepts (`.planning/`); `wiki_ticket_sdd` structures work into tracked
items with its own roadmap (`docs/roadmap.md`). Running both at once means
picking one as the system of record for what actually gets tracked and
published — recommended split:

1. Let GSD do `new-project`/`new-milestone`/`plan-phase` for the
   goal-backward planning and verification loop it's built for.
2. When a GSD phase plan is ready to execute, capture its task breakdown
   into `wiki_ticket_sdd` via `plan-capture` so it becomes real work items
   (ULIDs, roadmap entries, tickets) — GSD's own `.planning/` files are not
   visible to this repo's roadmap or wiki until captured this way.
3. Use GSD's `execute-phase`/`gsd-executor` for the actual implementation
   loop; close out items in `wiki_ticket_sdd` (`update`/`close`) as GSD's
   phases complete, then `roadmap-render` and sync/publish as usual.

Don't run GSD's roadmap and this repo's roadmap as two independent sources
of truth for the same milestone — pick `wiki_ticket_sdd`'s as canonical
once a phase is captured, since that's what ships to the wiki and the
ticket tracker.

## Mapping events

A captured GSD phase's tasks become ordinary `create` events in
`.work/todo.jsonl`, one per task/subtask, exactly like any other
`plan-capture` output. There's no GSD-specific event type.

## Pulling changes

Not applicable — GSD's `.planning/` state isn't an external system
`ticket-sync` pulls from. If a GSD phase plan changes after capture,
that's a new plan (per this repo's supersedes rule), not an edit pulled
back in.

## Rendering support

Identical to any other captured plan: rendered ticket pages per work item,
frozen plan doc published to the wiki. No GSD-specific rendering exists.

## Gotchas & troubleshooting

- Two roadmaps drifting apart is the main risk — decide up front which one
  a stakeholder actually reads, and treat the other as internal planning
  scratch space.
- GSD's phase verification (`gsd-verifier`) and this repo's
  `worklog verify`/status reporting are separate concepts that happen to
  sound similar; don't conflate them.

## Last updated

2026-07-25 — [edit this page](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki/Integration-GSD/_edit)
