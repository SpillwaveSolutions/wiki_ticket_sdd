---
name: merge-green
description: Merge PRs only when all quality gates pass. Use whenever asked to merge a PR, complete a merge, or land a branch — polls checks every 5 minutes until green instead of merging blind or bypassing.
version: 0.8.0
---

# Merge when green

The default, always: **a PR merges only when every check is green.** Pending
means wait; failing means fix. There is no third option.

1. GitHub: run `plugin/scripts/merge-when-green.sh <pr> [interval] [max]`
   (defaults: 300 s × 24) — in the background, so work continues while it
   polls. In this repo the script lives at `plugin/scripts/`; in
   plugin-installed sessions use `"${CLAUDE_PLUGIN_ROOT}/scripts/merge-when-green.sh"`.
2. Other platforms: same rule via their CLI; prefer native merge-when-green
   (`glab mr merge --when-pipeline-succeeds`, ADO auto-complete).
3. After a merge: pull the base branch, delete the merged local branch, sync
   tickets if items closed, regenerate the roadmap if the log changed.
4. On red gates: report which checks failed and fix them. Never merge with
   `--admin`, never skip a gate, never retry-until-flaky-passes without
   understanding the failure.
