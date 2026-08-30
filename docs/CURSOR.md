# Cursor — binding this ContentPack

Cursor is a first-class host. Grok Bot uses Cursor cloud agents for reads
and writes. Local Cursor can load this pack as a plugin.

This is **not** a second copy of the skills. Same `plugin/skills/`, same
scripts, same worklog protocol.

> Knowledge-tree (OKF) isolation used to be documented here. It lives in
> [second-brain-core](https://github.com/SpillwaveSolutions/second-brain-core)
> and [okf-plugin](https://github.com/SpillwaveSolutions/okf-plugin).
> `brain_session.py` is gone from this repo.

## How Cursor loads this pack

Cursor has four layers. We use the first three. We do not ship per-pack MCP.

| Layer | What we ship | Where |
|-------|----------------|-------|
| Agent Skills | Existing `SKILL.md` files | `plugin/skills/` (also `.claude/skills/`) |
| Agent Plugins 1.0 | Root `plugin.json` | repo root |
| Cursor Plugins | Rules + skill pointer | `.cursor-plugin/plugin.json` |
| MCP | Not in this pack | deferred |

Cursor also reads `.claude/skills/` and `.codex/skills/` for compatibility.

## Install (local Cursor)

```text
/plugin marketplace add SpillwaveSolutions/wiki_ticket_sdd
/plugin install worklog
```

Or open this repo and load it as a local plugin (`--plugin-dir` / Customize).

Root `plugin.json` already declares the Agent Plugins 1.0 schema, so Cursor
loads skills without a rewrite.

## Cloud Cursor (the Grok Bot hole)

A Grok Bot coding session usually opens **a product checkout**, not this
plugin repo. The cloud agent sees `AGENTS.md` / `CLAUDE.md` and `bin/worklog`
if they are vendored there. It does **not** see your local Claude or Grok
plugin cache.

Do this:

1. Claim identity (`--actor` / `SECOND_BRAIN_IDENTITY`).
2. File the work in the log before doing it (`bin/worklog add`).
3. One session per worktree. See [ISOLATION.md](ISOLATION.md).
4. Merge when green. Never squash (ADR-0008).
5. Never invent a private remote.

If the checkout is a knowledge tree rather than a WikiTicket repo, stop and
use okf-plugin / second-brain-core. Do not invent a write path here.

## Rules

`.cursor/rules/second-brain.mdc` is always-on when this repo is the Cursor
workspace. It restates identity, worklog-first, one session per worktree,
and the privacy fence. Knowledge-tree protocol is a pointer, not a writer.

## Identity

Actor: `grok-bot/worklog`
Host flag: Cursor

Same privacy fence as [GROK_BOT.md](GROK_BOT.md).

## Related

- [GROK_BOT.md](GROK_BOT.md) — Grok Bot binding
- [ISOLATION.md](ISOLATION.md) — one session per worktree
- [https://cursor.com/docs/plugins](https://cursor.com/docs/plugins)
- [https://agent-plugins.org](https://agent-plugins.org)
