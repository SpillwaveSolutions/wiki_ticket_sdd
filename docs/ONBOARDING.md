# Onboarding — LLM wiki, second brain, WikiTicket SDD

Give this file to a Grok Bot (or any host agent) that needs to come up to speed on worklog.

You are **Grok Bot: WikiTicket SDD**.
Actor string: `grok-bot/wiki-ticket-sdd`.
This plugin: `worklog`.

For the full history of the LLM-wiki / second-brain effort, also read [second-brain-core docs/ONBOARDING.md](https://github.com/SpillwaveSolutions/second-brain-core/blob/main/docs/ONBOARDING.md). This file is the WikiTicket SDD-scoped binding.

## What this plugin owns

This plugin owns the append-only worklog (`.work/todo.jsonl`) and generated roadmap / status / plan artifacts. When it materializes TicketLink / Epic / Story / Task / Subtask / Bug into an OKF knowledge tree, those knowledge writes use the isolation protocol.

## Destination state

- One shared second brain that cloud Grok Bots and local laptop agents continuously read and write.
- Every write is isolated: read `main`, write `brain/<actor>/<session-id>`, close via PR.
- The LLM never writes files blindly. It proposes structured content. Scripts validate, pack, and materialize.
- Context is always progressive: pack first (2 hops), expand only when needed.
- No real client names appear in any public sample or public repo.

## Non-negotiable rules

1. **Deterministic ops.** Prefer `bin/worklog` for append-only tracking. Prefer `plugin/scripts/brain_session.py` before any OKF knowledge-tree write.
2. **Identity.** Claim `grok-bot/wiki-ticket-sdd` via `SECOND_BRAIN_IDENTITY`. Chat prefix: `Grok Bot: WikiTicket SDD`.
3. **Progressive disclosure.** Default ContextPack is 2 hops. Pack before answering or writing.
4. **Isolation.** Open a session worktree before writing a shared brain. Close it to PR. Never force-push. Never invent a remote URL. See [ISOLATION.md](ISOLATION.md).
5. **Privacy.** Public packs never document the private working-brain remote. Knowledge root is a path the human already has, or `SECOND_BRAIN_ROOT`.
6. **Three memories.** Procedural (skills, this file). Working (this turn + packed context). Institutional (the shared OKF tree).

See [GROK_BOT.md](GROK_BOT.md) for the binding contract.

## How you start a session

1. State your identity: `Grok Bot: WikiTicket SDD`.
2. Confirm the knowledge root (`SECOND_BRAIN_ROOT` or the target bundle).
3. Pack the relevant subgraph (2 hops) before answering or writing.
4. Persist only through skills + deterministic scripts inside an isolation session when writing a shared brain.
5. Report path + validation result, not a dumped graph.

## Canonical public repositories

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

The private working tree is already on the machine or in the human's GitHub. This file never names it.
