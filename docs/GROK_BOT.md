# Grok Bot — binding WikiTicket SDD

You are operating as a **Grok Bot** agent that records work in WikiTicket
SDD: append-only events, generated roadmap, frozen plans, wiki publish.

Read [ONBOARDING.md](ONBOARDING.md) first.

This file is the binding contract. It does **not** install a Claude-style
plugin. Grok Bot skills are workflows. Enable the skill that matches the
task and follow the rules below.

> Knowledge-tree writes used to ship here (`okf_write.py`,
> `brain_session.py`). They do not anymore. That product lives in
> [okf-plugin](https://github.com/SpillwaveSolutions/okf-plugin) and
> [second-brain-core](https://github.com/SpillwaveSolutions/second-brain-core).
> See [ISOLATION.md](ISOLATION.md).

## Identity

- Actor string: `grok-bot/wiki-ticket-sdd`
- Claim per process with `SECOND_BRAIN_IDENTITY=grok-bot/wiki-ticket-sdd`
  (worklog `--actor` / `--author` also accept this)
- Chat prefix: `Grok Bot: WikiTicket SDD`

## What this plugin owns

The append-only work log (`.work/todo.jsonl`), generated roadmap / plans /
status, wiki publish, and ticket sync. Union merge, event fold, hook-enforced
policy. `bin/worklog` is the only writer of the log.

```bash
export SECOND_BRAIN_IDENTITY="grok-bot/wiki-ticket-sdd"
bin/worklog --actor "$SECOND_BRAIN_IDENTITY" add --level story --kind feature "…"
```

Worklog appends do not require a knowledge worktree.

## Isolation (this checkout)

Multiple agents on multiple machines may share this repo. Give each session
its own `git worktree`. Do not share one working directory. See
[ISOLATION.md](ISOLATION.md).

## Skill binding

Grok Bot does not run `/plugin marketplace add`. Enable the relevant skills
from this repo (`plugin/skills/*/SKILL.md`). Thin host wrapper:
`plugin/hosts/grok-bot/SKILL.md`.

## Cursor (Grok Bot coding host)

Grok Bot often opens a **Cursor cloud agent** against a checkout.

- Local Cursor: add the marketplace, then install this plugin. See
  [CURSOR.md](CURSOR.md).
- Cloud Cursor: follow this file plus `AGENTS.md` / `CLAUDE.md` in the
  checkout. Plugin install is optional. Recording work in the log is not.
- This pack ships `.cursor-plugin/plugin.json` (Cursor Plugins) and a root
  `plugin.json` (Agent Plugins 1.0). Cursor loads both. Skills stay in
  `plugin/skills/` (mirrored at `.claude/skills/`).

## Related public packages

Knowledge-tree / OKF work is a different product:

- [okf-plugin](https://github.com/SpillwaveSolutions/okf-plugin)
- [second-brain-core](https://github.com/SpillwaveSolutions/second-brain-core)
- [second-brain-marketplace](https://github.com/SpillwaveSolutions/second-brain-marketplace)
