---
name: init
description: Scaffold or upgrade the current repo as a worklog repo (bin/, git hooks, .work/, CI workflow, CLAUDE.md policy block)
---

Install (or upgrade) worklog in the current repo:

1. From the repo root, run:

   ```
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/init.sh"
   ```

2. Show the user the script's output (version installed, what was written vs skipped, upgraded-from if applicable).

3. Run `git status`, review the scaffolding it added or updated, and commit it all in ONE commit (e.g. `worklog: scaffold repo (plugin v0.1.0)`). The copies are committed deliberately so git hooks and CI work for teammates who do not have the plugin.

The script is idempotent: re-running on an installed repo is the upgrade path. It never touches existing `.work/*.jsonl` logs.
