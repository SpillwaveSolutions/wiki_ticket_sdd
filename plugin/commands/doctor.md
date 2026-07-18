---
name: doctor
description: Report worklog health for the current repo — version skew, missing or stale files, hook wiring, log invariants. Read-only.
---

Check worklog health in the current repo:

1. From the repo root, run:

   ```
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.sh"
   ```

2. Report the findings to the user: version match or skew, file presence and staleness, `core.hooksPath` wiring, and whether the invariant checks pass.

3. Fix NOTHING. Doctor is read-only. If it reports skew or stale files, suggest `/worklog:init` (the upgrade path) — but only run it if the user asks.
