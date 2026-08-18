---
name: cursor-worklog
description: Bind a Cursor agent (including Grok Bot cloud sessions) to the worklog ContentPack.
---

# Cursor / worklog

Follow `docs/CURSOR.md` and `docs/GROK_BOT.md`.

1. Identity: `grok-bot/worklog` (or the operator-registered actor for this role).
2. Local Cursor may `/plugin install worklog` from the Spillwave marketplace.
3. Cloud Cursor on a knowledge tree: pack first, write only via pack scripts, isolate with `brain_session.py`.
4. Never document a private remote. Never write raw Markdown into the tree.
