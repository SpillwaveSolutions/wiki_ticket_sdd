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

## Auto-merge flag

`features.auto_merge_on_green` in `.work/config.yml` (default **true**)
decides what happens when gates go green: true merges; false is advisory
mode — the script reports green, does NOT merge, and waits for a human to
run `gh pr merge <pr> --merge`. Overrides, strongest first: `--auto` /
`--advisory` as first argument to the script (one run only), then
`WORKLOG_AUTO_MERGE=1|0` in the environment, then the config value.
Red/pending/timeout behavior is identical in both modes.

Non-GitHub platforms: same rule, their CLI (`glab mr merge --when-pipeline-succeeds`,
`az repos pr update --auto-complete`) — prefer the platform's native
merge-when-green if it has one.
