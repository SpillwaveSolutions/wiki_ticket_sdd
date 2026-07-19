---
name: viz
description: Regenerate the roadmap with ALL Mermaid diagrams (dependency graph, hierarchy, event-dated gantt) and republish it — runs in a background subagent, never blocks the main session.
---

Regenerate the visual roadmap without blocking the current work:

1. Spawn ONE background subagent (run in background — the same non-blocking
   pattern plan-capture uses for ticket/wiki publishing) with this task:

   - From the repo root, run:

     ```
     bin/worklog roadmap-render --viz=all
     ```

   - If `docs/roadmap.md` (or the `.work/*.jsonl` log alongside it) changed,
     commit the log and roadmap together.
   - Republish the roadmap via the wiki-publish flow so the wiki copy matches.

2. Continue the main session immediately — never wait on the subagent.

3. When its completion notification arrives, fold the result in: tell the
   user which diagrams rendered and where (`docs/roadmap.md`, wiki page if
   republished).
