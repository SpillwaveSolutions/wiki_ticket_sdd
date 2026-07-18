---
name: merge
description: Merge a PR only when every quality gate is green — polls every 5 minutes until checks pass, refuses on any failure.
---

# /worklog:merge <pr-number>

Merging with red or pending gates is never an option; this command encodes
the house rule.

1. Confirm the PR number with the user if not given.
2. Run, in the background so the session stays free:

       bash "${CLAUDE_PLUGIN_ROOT}/scripts/merge-when-green.sh" <pr> 300 24

   (5-minute polls, up to 2 h.) Exit meanings: 0 merged · 1 failing checks,
   NOT merged · 2 no gh CLI · 3 PR not open · 4 timed out waiting.
3. On merge: pull the base branch, delete the local feature branch, run the
   ticket-sync skill if the PR closed work items, and `worklog roadmap-render`
   if the log changed.
4. On failure or timeout: report the failing checks; fixing them is the path
   to merging — never `--admin`, never bypass.

Non-GitHub platforms: same rule, their CLI (`glab mr merge --when-pipeline-succeeds`,
`az repos pr update --auto-complete`) — prefer the platform's native
merge-when-green if it has one.
