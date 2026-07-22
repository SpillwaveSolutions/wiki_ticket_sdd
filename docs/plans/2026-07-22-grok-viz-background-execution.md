---
date: 2026-07-22
slug: grok-viz-background-execution
title: Grok viz — background-subagent execution rule (amendment record)
epic: null
items: [01KY5QJARJ0S9QHGRPAV8SFV9H]
relates_to:
- {type: references, target: plan/grok-compat-and-mermaid-viz}
---

# Grok viz — background-subagent execution rule (amendment record)

> **Why this document exists.** Commit `72be089` inserted the execution rule
> below into the frozen plan `2026-07-19-grok-compat-and-mermaid-viz.md`
> *after* it was published — a violation of the frozen-plan invariant that the
> first manifest-driven wiki publish (2026-07-22) surfaced as source-hash
> drift and refused to publish. The frozen plan has been restored to its
> originally published content (ledger hash `0bfe624745fd`, commit `d900bd8`);
> the rule is preserved here as the design record. Its operative home is
> `plugin/commands/viz.md`, which implements it.

## Execution rule: always a background subagent

Viz work never blocks the main thread. Both the implementation waves and the
recurring runtime step (regenerate diagrams + republish the roadmap after log
changes) are delegated to ONE background subagent, run in parallel with other
tasks — the same non-blocking pattern plan-capture uses for ticket/wiki
publishing. The main session folds the result in when the notification
arrives; it never waits.
