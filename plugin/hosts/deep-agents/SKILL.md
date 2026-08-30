---
name: worklog-deep-agents
description: Bind WikiTicket SDD for LangChain Deep Agents / Deep Agents Code.
---

# WikiTicket SDD for LangChain Deep Agents

Read `docs/ONBOARDING.md`, `docs/LANG_CHAIN_DEEP_AGENTS.md`, and `docs/ISOLATION.md`.

```bash
export SECOND_BRAIN_IDENTITY="deep-agents/wiki-ticket-sdd"
```

Point SkillsMiddleware at `plugin/skills/`. Append worklog events with `bin/worklog --actor "$SECOND_BRAIN_IDENTITY"`. Knowledge-tree writes do not ship here; use [okf-plugin](https://github.com/SpillwaveSolutions/okf-plugin).
