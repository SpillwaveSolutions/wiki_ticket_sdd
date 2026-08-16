# Grok Bot — binding WikiTicket SDD

You are operating as a **Grok Bot** agent that writes WikiTicket SDD knowledge into the same shared institutional second brain used by local agents (Claude Code, Grok Build, Codex, OpenCode).

Read [ONBOARDING.md](ONBOARDING.md) first.

This file is the binding contract. It does **not** install a Claude-style plugin. Grok Bot skills are workflows. Enable the skill that matches the task and follow the rules below.

## Privacy (non-negotiable)

- The working second brain is private. This public plugin never documents its remote URL, org/repo slug, or clone command.
- Knowledge root is always a path the human already has, or `SECOND_BRAIN_ROOT`.
- Never copy live nodes, real client names, contacts, or production facts into public repos or samples.
- Public samples remain the in-repo sample fiction only.

## Identity

- Actor string: `grok-bot/wiki-ticket-sdd`
- Claim per process with `SECOND_BRAIN_IDENTITY=grok-bot/wiki-ticket-sdd`
- Do **not** use a single shared `knowledge/.identity.json` for a fleet.
- Chat prefix: `Grok Bot: WikiTicket SDD`

## Isolation

Multiple agents on multiple machines share one private remote. Example (fiction only): one session works **lumenfield-detector**, another works **northstar-console**. Both read `main`. Both write only in `brain/<actor>/<session-id>`.

1. Read shared truth from `main` (fast-forward pull).
2. Before writing, open a session worktree (see [ISOLATION.md](ISOLATION.md)).
3. Write only inside that worktree via this plugin's scripts.
4. Close the session to commit and open a PR against **whatever remote the checkout already has**. Never force-push. Never invent a remote.

If you have no local worktree (cloud box not mounted), propose structured writes or create a branch via GitHub. Same actor string. Same owned types.

## Knowledge root

```bash
export SECOND_BRAIN_ROOT="${SECOND_BRAIN_ROOT:-knowledge}"
export SECOND_BRAIN_IDENTITY="grok-bot/wiki-ticket-sdd"
```

## Deterministic write boundary

The model proposes structure. Scripts materialize Markdown + YAML.

```bash
bin/worklog show --help
# Knowledge-tree writes only, after opening a session:
# write TicketLink / work-item Markdown into $SECOND_BRAIN_ROOT
```

**Forbidden:** silent raw dumps into the knowledge tree without type, provenance, or validation.

**Required:** type ownership. This plugin owns the append-only worklog (`.work/todo.jsonl`) and generated roadmap / status / plan artifacts. When it materializes TicketLink / Epic / Story / Task / Subtask / Bug into an OKF knowledge tree, those knowledge writes use the isolation protocol. Refuse nouns owned by another plugin unless co-authoring is explicit.

## Progressive disclosure

Default ContextPack: **2 hops / ~20 nodes**.

Pack before answering or writing. Do not dump the entire tree.

## Skill binding

Grok Bot does not run `/plugin marketplace add`. Enable the relevant skills from this repo (`skills/*/SKILL.md`). Set identity and knowledge root. Report path + validation result, not a dumped graph.

Thin host wrapper: `plugin/hosts/grok-bot/SKILL.md`.

Worklog appends do not require a knowledge worktree. Knowledge-tree writes do.

## Three memory planes

| Plane | Location |
|-------|----------|
| Procedural | Skills, this file, [ONBOARDING.md](ONBOARDING.md), harness rules |
| Working | Current turn + packed context |
| Institutional | The private OKF Markdown tree |

## Related public packages

### Foundation layer

- [okf-plugin](https://github.com/SpillwaveSolutions/okf-plugin)
- [project-knowledge-capture](https://github.com/SpillwaveSolutions/project-knowledge-capture)
- [system-architecture-capture](https://github.com/SpillwaveSolutions/system-architecture-capture)
- [data-engineering-knowledge-capture](https://github.com/SpillwaveSolutions/data-engineering-knowledge-capture)
- [wiki_ticket_sdd](https://github.com/SpillwaveSolutions/wiki_ticket_sdd)
- [okf-agent-graph](https://github.com/SpillwaveSolutions/okf-agent-graph)

### ContentPack suite

- [second-brain-core](https://github.com/SpillwaveSolutions/second-brain-core)
- [executive-coordination](https://github.com/SpillwaveSolutions/executive-coordination)
- [account-management](https://github.com/SpillwaveSolutions/account-management)
- [sales-pipeline](https://github.com/SpillwaveSolutions/sales-pipeline)
- [executive-job-search](https://github.com/SpillwaveSolutions/executive-job-search)
- [consulting-leads](https://github.com/SpillwaveSolutions/consulting-leads)
- [content-media](https://github.com/SpillwaveSolutions/content-media)
- [news-digest](https://github.com/SpillwaveSolutions/news-digest)
- [gtm-positioning](https://github.com/SpillwaveSolutions/gtm-positioning)
- [second-brain-marketplace](https://github.com/SpillwaveSolutions/second-brain-marketplace)
- [second-brain-starter](https://github.com/SpillwaveSolutions/second-brain-starter)
