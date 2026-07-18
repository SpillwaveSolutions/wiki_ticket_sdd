---
name: uninstall
description: Remove worklog scaffolding from the current repo (keeps all .work/ data, plans, status reports, and the roadmap)
---

Uninstall worklog tooling from the current repo. This is destructive to the tooling, so:

1. FIRST confirm with the user that they really want to remove the worklog scaffolding (bin/ scripts, git hooks, .gitattributes lines, CI workflow, CLAUDE.md policy block). Tell them their data — `.work/`, `docs/plans/`, `docs/status/`, `docs/roadmap.md` — will be preserved. Do NOT run the script until they confirm.

2. After confirmation, from the repo root run:

   ```
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/uninstall.sh"
   ```

3. Show the user the output, including the list of what was preserved and why.

4. Run `git status`, review the removals, and commit them in one commit (e.g. `worklog: remove tooling (data preserved)`).
