---
name: grok-bot-wiki-ticket-sdd
description: Bind a Grok Bot agent to WikiTicket SDD. Worklog append vs knowledge-tree isolation.
---

# Grok Bot / WikiTicket SDD

Read `docs/ONBOARDING.md` first, then follow `docs/GROK_BOT.md` and `docs/ISOLATION.md`.

1. Identity: `grok-bot/wiki-ticket-sdd`
2. Worklog appends (`.work/todo.jsonl`) do **not** need a knowledge worktree. Use `bin/worklog`.
3. Before writing TicketLink / work items into an OKF tree, open `plugin/scripts/brain_session.py`, then `bin/okf_write.py write --author "$SECOND_BRAIN_IDENTITY"`.
4. Never document a private remote. Never invent a remote URL. Never force-push.
