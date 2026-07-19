---
name: status-report
description: Generate a status report. Use when asked for a status report, a standup summary, "what changed this week", or "what did we ship". Writes docs/status/<date>-<kind>.md, commits, and publishes — never paste an unrecorded status into chat.
version: 0.8.0
---

# Status report

1. Pick the kind from the ask: `daily` (the standup — terse, item-level),
   `weekly` (the stakeholder rollup — epic-level), or `timecard` (the billing
   narrative — a sentence or two per day; §17 Q4 is closed: no hours).

2. Run `bin/worklog status --kind <kind> --emit-facts` and read the JSON.
   For a timecard, add `--since YYYY-MM-DD --until YYYY-MM-DD` when the ask
   names a window (default: the last 7 days). Every claim in the report comes
   from these facts — not from memory of the session.

3. Write the prose per §13.3's shapes:
   - **daily** — terse bullets, fits on a screen: Shipped / In flight (with
     ages — a 9-day-old "in progress" is the whole story) / Blocked (and by
     what) / Unplanned / Needs attention (conflicts, deferred syncs).
   - **weekly** — prose plus tables grouped by epic: what shipped, slippage
     (still open despite being in flight at the window start), the unplanned
     rollup with the percentage of closed items that were unplanned, and
     what's next.
   - **timecard** — ONE SHORT PARAGRAPH PER DAY: a sentence or two saying
     what the day consisted of, in plain language, under a day heading like
     `## Monday, 14 July`. No tables, no ticket IDs in the reading path, no
     status columns. Days without activity are omitted, not padded.

   THE UNPLANNED SECTION IS THE POINT — always include it (in a timecard, as
   prose in the day's paragraph, never as a percentage).

4. Pipe the prose to `bin/worklog status --kind <kind> --write` (timecard:
   repeat the same `--since`/`--until`; the file lands at
   `docs/status/<until>-timecard.md`). Commit the report file, together with
   the log/roadmap if they were touched.

5. Publish via the wiki-publish skill flow, key `status/<date>-<kind>`
   (timecard: `status/<until-date>-timecard`). Status reports are frozen —
   publish once, never re-publish.

Never regenerate an existing report (invariant 15.9). If a report was wrong,
the correction goes in the next report, not into the old one.
