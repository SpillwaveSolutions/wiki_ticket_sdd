---
name: worklog-deep-agents
description: Bind WikiTicket SDD for LangChain Deep Agents / Deep Agents Code.
---

# WikiTicket SDD for LangChain Deep Agents

Read `docs/ONBOARDING.md`, `docs/LANG_CHAIN_DEEP_AGENTS.md`, and `docs/ISOLATION.md`.

```bash
export SECOND_BRAIN_IDENTITY="deep-agents/wiki-ticket-sdd"
```

Point SkillsMiddleware at `plugin/skills/`. Append worklog events with `bin/worklog`. Isolate knowledge-tree writes with `plugin/scripts/brain_session.py`.
