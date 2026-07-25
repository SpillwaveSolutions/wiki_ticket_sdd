# Integration: OpenSpec

## When to use

You're using OpenSpec (spec-driven changes tracked as proposals under a
`changes/` or `openspec/` directory, each with its own tasks) alongside
`wiki_ticket_sdd`, and want those proposals to become tracked, published
work rather than staying local-only.

## One-command setup

Nothing to install on the `wiki_ticket_sdd` side — OpenSpec is set up
independently, per its own instructions.

## Adapter configuration

Not applicable. OpenSpec has no ticketing/wiki adapter concept; nothing
to configure in `.work/config.yml`.

## Recommended workflow

Treat an OpenSpec change proposal the same way as a SpecKit spec or a
hand-written design doc — it's the *why*, and `wiki_ticket_sdd`'s
`plan-capture` is what turns its task list into tracked, published work:

1. Draft and approve the OpenSpec change proposal as normal.
2. Feed its task breakdown into `plan-capture` (reformat to
   `- [ ] (P#) Title` plus a one-to-three-sentence description per task if
   OpenSpec's own format differs).
3. Keep the OpenSpec proposal document itself as the permanent design
   record — same role this repo gives its own `docs/plans/`, so avoid
   re-deriving the rationale inside the `wiki_ticket_sdd` plan body; a
   short pointer back to the OpenSpec proposal is enough.
4. Execute and close out through `wiki_ticket_sdd` as usual.

## Mapping events

Each captured task becomes an ordinary `create` event in
`.work/todo.jsonl` — no OpenSpec-specific event shape.

## Pulling changes

Not applicable — nothing external to pull. If the OpenSpec proposal
changes after capture, write a new plan that supersedes it rather than
editing the captured one.

## Rendering support

Identical to any other captured plan — ticket pages per work item, the
frozen plan doc published to the wiki.

## Gotchas & troubleshooting

- OpenSpec's own "archived" state for a completed proposal and this repo's
  `done`/`cancelled` item statuses are two independent lifecycles — closing
  work items here doesn't archive the OpenSpec proposal, and vice versa.
- As with SpecKit, don't try to keep two live task lists (OpenSpec's and
  `.work/todo.jsonl`'s) in sync by hand after capture — capture once, then
  `wiki_ticket_sdd`'s log is the one that's tracked and published.

## Last updated

2026-07-25 — [edit this page](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki/Integration-OpenSpec/_edit)
