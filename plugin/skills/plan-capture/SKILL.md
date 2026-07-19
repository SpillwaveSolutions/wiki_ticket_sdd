---
name: plan-capture
description: Capture an approved plan as tracked work items. Use when exiting plan mode, when the user approves a plan, or says "capture this plan". Writes docs/plans/<date>-<slug>.md and appends the plan's tasks to .work/todo.jsonl via bin/worklog.
version: 0.6.0
---

# Plan capture

1. Write the approved plan as markdown. It MUST contain a `## Tasks` section:

       ## Tasks

       - [ ] (P1) Task title
         - [ ] Subtask of the task above

   Priority token `(P0)`–`(P3)` optional, default P2. Prose (the *why*) goes
   in other sections and is preserved verbatim in the plan doc.

   Captured items are `kind:feature` by design — a plan's tasks deliver
   planned value. If a captured task is really a defect, retag it after
   capture: `bin/worklog update <ulid> --kind bug`.

2. Save it to a temp file and run:

       bin/worklog plan-capture --slug <kebab-slug> --title "<plan title>" --file <tempfile>

3. Run `bin/worklog roadmap-render`, then commit `docs/plans/`,
   `docs/roadmap.md`, and `.work/todo.jsonl` together.

4. Publish in the background: spawn ONE background subagent (Agent tool with
   `run_in_background`) whose prompt is: run the ticket-sync skill flow for
   the newly created items, then the wiki-publish flow for the new plan doc
   (its key is `plan/<slug>`), and report counts. Continue implementing
   immediately — do NOT wait for the subagent; fold its result in when the
   notification arrives. If background agents are unavailable in the harness,
   run the two publishes inline after the first implementation commit
   instead — visibility may lag but never blocks.

Never append to `.work/*.jsonl` directly (invariant 15.4). Never overwrite an
existing plan (invariant 15.8) — a changed design gets a NEW plan that
supersedes the old one.
