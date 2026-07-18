---
name: plan-capture
description: Capture an approved plan as tracked work items. Use when exiting plan mode, when the user approves a plan, or says "capture this plan". Writes docs/plans/<date>-<slug>.md and appends the plan's tasks to .work/todo.jsonl via bin/worklog.
version: 0.3.0
---

# Plan capture

1. Write the approved plan as markdown. It MUST contain a `## Tasks` section:

       ## Tasks

       - [ ] (P1) Task title
         - [ ] Subtask of the task above

   Priority token `(P0)`–`(P3)` optional, default P2. Prose (the *why*) goes
   in other sections and is preserved verbatim in the plan doc.

2. Save it to a temp file and run:

       bin/worklog plan-capture --slug <kebab-slug> --title "<plan title>" --file <tempfile>

3. Run `bin/worklog roadmap-render`, then commit `docs/plans/`,
   `docs/roadmap.md`, and `.work/todo.jsonl` together.

Never append to `.work/*.jsonl` directly (invariant 15.4). Never overwrite an
existing plan (invariant 15.8) — a changed design gets a NEW plan that
supersedes the old one.
