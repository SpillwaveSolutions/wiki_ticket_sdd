---
name: grok-bot-wiki-ticket-sdd
description: Bind a Grok Bot agent to WikiTicket SDD. Worklog appends; knowledge-tree writes live in okf-plugin.
---

# Grok Bot / WikiTicket SDD

Read `docs/ONBOARDING.md` first, then follow `docs/GROK_BOT.md` and `docs/ISOLATION.md`.

1. Identity: `grok-bot/wiki-ticket-sdd`
2. Worklog appends (`.work/todo.jsonl`) use `bin/worklog`. One session per worktree.
3. Knowledge-tree (OKF) writes do not ship in this plugin. Use [okf-plugin](https://github.com/SpillwaveSolutions/okf-plugin) and [second-brain-core](https://github.com/SpillwaveSolutions/second-brain-core).
4. Never document a private remote. Never invent a remote URL. Never force-push. Never squash (ADR-0008). Merge when green (`/worklog:merge`).
