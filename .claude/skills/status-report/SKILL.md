---
name: status-report
description: Generate a status report. Use when asked for a status report, a standup summary, "what changed this week", or "what did we ship". Writes docs/status/<date>-<kind>.md, commits, and publishes — never paste an unrecorded status into chat.
---

# Status report

1. Pick the kind from the ask: `daily` (the standup — terse, item-level) or
   `weekly` (the stakeholder rollup — epic-level). `timecard` is not yet
   available: spec §17 open question 4 (hours vs narrative) has to be decided
   first — say so if it's asked for.

2. Run `bin/worklog status --kind <kind> --emit-facts` and read the JSON.
   Every claim in the report comes from these facts — not from memory of the
   session.

3. Write the prose per §13.3's shapes:
   - **daily** — terse bullets, fits on a screen: Shipped / In flight (with
     ages — a 9-day-old "in progress" is the whole story) / Blocked (and by
     what) / Unplanned / Needs attention (conflicts, deferred syncs).
   - **weekly** — prose plus tables grouped by epic: what shipped, slippage
     (still open despite being in flight at the window start), the unplanned
     rollup with the percentage of closed items that were unplanned, and
     what's next.

   THE UNPLANNED SECTION IS THE POINT — always include it.

4. Pipe the prose to `bin/worklog status --kind <kind> --write`. Commit the
   report file, together with the log/roadmap if they were touched.

5. Publish via the wiki-publish skill flow, key `status/<date>-<kind>`.
   Status reports are frozen — publish once, never re-publish.

Never regenerate an existing report (invariant 15.9). If a report was wrong,
the correction goes in the next report, not into the old one.
