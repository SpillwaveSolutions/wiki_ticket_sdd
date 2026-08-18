# Cursor — binding this ContentPack

Cursor is a first-class host. Grok Bot uses Cursor cloud agents for reads
and writes against the knowledge tree. Local Cursor can load this pack as
a plugin.

This is **not** a second copy of the skills. Same `skills/`, same scripts,
same isolation protocol.

## How Cursor loads this pack

Cursor has four layers. We use the first three. We do not ship per-pack MCP.

| Layer | What we ship | Where |
|-------|----------------|-------|
| Agent Skills | Existing `SKILL.md` files | `skills/` (also `.claude/skills/` on worklog) |
| Agent Plugins 1.0 | Root `plugin.json` | repo root |
| Cursor Plugins | Rules + skill pointer | `.cursor-plugin/plugin.json` |
| MCP | Not in this pack | deferred |

Cursor also reads `.claude/skills/` and `.codex/skills/` for compatibility.

## Install (local Cursor)

```text
/plugin marketplace add SpillwaveSolutions/second-brain-marketplace
/plugin install worklog
```

Or open this repo and load it as a local plugin (`--plugin-dir` / Customize).

Root `plugin.json` already declares the Agent Plugins 1.0 schema, so Cursor
loads skills without a rewrite.

## Cloud Cursor (the Grok Bot hole)

A Grok Bot coding session usually opens **the knowledge tree**, not this
plugin repo. The cloud agent sees `AGENTS.md` and pack scripts if they are
vendored there. It does **not** see your local Claude or Grok plugin cache.

Do this:

1. Claim identity (`SECOND_BRAIN_IDENTITY` or `--author`).
2. Pack first (2 hops). Do not dump the tree.
3. Write only through the pack script. No raw Markdown into `knowledge/`.
4. Isolate: `brain_session.py open` → write → `close` (PR).
5. Never invent a private remote.

The knowledge tree should carry `AGENTS.md` and, if you want skills without
a plugin install, `.agents/skills/` shims. That binding lives in the tree
the human already owns — not in this public pack.

## Rules

`.cursor/rules/second-brain.mdc` is always-on when this repo is the Cursor
workspace. It restates identity, pack-first, scripted writes, isolation,
and the privacy fence.

## Identity

Actor: `grok-bot/worklog`
Host flag on session open: `--host cursor`

Same owned types as [GROK_BOT.md](GROK_BOT.md). Same privacy fence.

## Related

- [GROK_BOT.md](GROK_BOT.md) — Grok Bot binding (now includes Cursor)
- [ISOLATION.md](ISOLATION.md) — worktree + PR
- [https://cursor.com/docs/plugins](https://cursor.com/docs/plugins)
- [https://agent-plugins.org](https://agent-plugins.org)
