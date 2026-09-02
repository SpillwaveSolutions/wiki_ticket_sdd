---
name: merge-green
metadata:
  version: "0.24.10"
description: Merge PRs only when all quality gates pass. Use whenever asked to merge a PR, complete a merge, or land a branch — arms GitHub auto-merge and falls back to polling instead of merging blind or bypassing.
---

# Merge when green

The default, always: **a PR merges only when every check is green.** Pending
means wait; failing means fix. There is no third option.

1. GitHub: run `plugin/scripts/merge-when-green.sh <pr> [interval] [max]`
   (defaults: 60 s × 120). The script arms `gh pr merge --auto --merge` up
   front so GitHub merges server-side the moment required checks pass; the
   poll loop is the fallback reporter, not the merge mechanism. Run it in
   the background so work continues. In this repo the script lives at
   `plugin/scripts/`; in plugin-installed sessions use
   `"${CLAUDE_PLUGIN_ROOT}/scripts/merge-when-green.sh"`.
2. Other platforms: same rule via their CLI; prefer native merge-when-green
   (`glab mr merge --when-pipeline-succeeds`, ADO auto-complete).
3. After a merge: pull the base branch, delete the merged local branch.
   Roadmap/index regeneration and `worklog sync --report` run in CI on main
   (`worklog-post-merge`); do not wait on them locally. Ticket-sync on
   closed items can still run locally if the post-merge report is not enough.
4. On red gates: report which checks failed and fix them. Never merge with
   `--admin`, never skip a gate, never retry-until-flaky-passes without
   understanding the failure, never squash (ADR-0008).
5. Auto-merge flag: `features.auto_merge_on_green` in `.work/config.yml`
   (default **true**). False = advisory mode: the script polls, reports
   green, does NOT merge — a human runs `gh pr merge <pr> --merge`.
   Overrides, strongest first: `--auto`/`--advisory` as the script's first
   argument (one run), then `WORKLOG_AUTO_MERGE=1|0`, then the config.
   Red/pending/timeout behavior is unchanged either way.
6. For `--auto` to actually queue, the host repo must allow auto-merge and
   require status checks on the base branch (ADR-0010). Without those,
   GitHub rejects the arm and the poll loop merges once green.
