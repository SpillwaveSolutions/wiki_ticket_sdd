# Integration: SpecKit

## When to use

You're using SpecKit (a spec-driven-development toolkit that generates
`spec.md`/`plan.md`/`tasks.md` artifacts from a feature description)
alongside `wiki_ticket_sdd`, and want its specs to show up as tracked
work instead of living only as loose files in a `specs/` directory.

## One-command setup

Nothing to install on the `wiki_ticket_sdd` side. SpecKit is installed and
initialized per its own instructions, independent of this repo — verify
its own CLI/install docs directly rather than relying on this page for
that step.

## Adapter configuration

Not applicable. SpecKit produces spec artifacts, not tickets or wiki
pages — there's no `.work/config.yml` knob for it.

## Recommended workflow

SpecKit's `tasks.md` output is the natural input to `plan-capture`: it's
already a checklist of discrete, describable tasks, which is exactly the
`- [ ] (P#) Title` shape `plan-capture` expects.

1. Run SpecKit's spec → plan → tasks flow as normal to get `tasks.md`.
2. Reformat (or directly feed, if the checkbox shape already matches)
   `tasks.md` into `plan-capture --slug <slug> --title <title> --file
   <tasks.md>` so each task becomes a real work item with a ULID.
3. Treat the SpecKit `spec.md`/`plan.md` as the design rationale — same
   role as this repo's own `docs/plans/*.md`, so it's reasonable to link
   the SpecKit spec from the plan's body rather than duplicating its
   content.
4. Execute and close out items through `wiki_ticket_sdd` as usual.

## Mapping events

Each `tasks.md` checkbox becomes one `create` event in `.work/todo.jsonl`
once captured — no SpecKit-specific event shape exists.

## Pulling changes

Not applicable. SpecKit's spec files aren't an external system this repo
pulls from; if the spec changes after capture, write a new plan that
supersedes the old one, per this repo's plan-immutability rule.

## Rendering support

Once captured, SpecKit-originated tasks render identically to any other
work item (ticket pages, roadmap entries) and the plan doc publishes to
the wiki like any other frozen plan.

## Gotchas & troubleshooting

- SpecKit's own task IDs (if it assigns any) are not the same as this
  repo's ULIDs — don't try to cross-reference them; the plan doc is the
  link between the two.
- If `tasks.md`'s checkbox format doesn't line up exactly with
  `- [ ] (P#) Title` plus a description line, `plan-capture` will reject
  or mis-parse it — reformat by hand rather than fighting the parser.

## Last updated

2026-07-25 — [edit this page](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki/Integration-SpecKit/_edit)
