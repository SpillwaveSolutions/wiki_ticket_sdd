---
name: cursor-worklog
description: Bind a Cursor agent (including Grok Bot cloud sessions) to the worklog ContentPack.
---

# Cursor / worklog

Follow `docs/CURSOR.md` and `docs/GROK_BOT.md`.

1. Identity: `grok-bot/worklog` (or the operator-registered actor for this role).
2. Local Cursor may `/plugin install worklog` from the Spillwave marketplace.
3. Cloud Cursor: record work with `bin/worklog`. One session per worktree. Knowledge-tree isolation lives in [second-brain-core](https://github.com/SpillwaveSolutions/second-brain-core).
4. Never document a private remote. Never squash (ADR-0008). Merge when green.
