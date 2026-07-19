---
date: 2026-07-19
slug: grok-compat-and-mermaid-viz
title: Grok Build compatibility statement + Mermaid roadmap visualization
epic: null
items: [01KXXM1Z13NPYK1XBJ1EQFEKGT]
status: planned — not yet scheduled
origin: authored by Rick with the claude.ai design session; gantt-date model corrected against the actual schema
---

# Grok Build compat + Mermaid roadmap visualization

## Part 1 — Grok Build compatibility (docs-only, small)

Per the xAI docs (Skills, Plugins & Marketplaces): "Grok is fully compatible
with Claude Code with zero configuration needed. Grok automatically reads
Claude Code marketplaces, plugins, skills, MCPs, agents, hooks, and
instruction files (CLAUDE.md, Claude.md, CLAUDE.local.md, and .claude/rules/)
alongside .grok/."

Consequence: our plugin (manifest, commands, skills, hooks) and the
/worklog:init scaffold work in Grok Build natively — the AGENTS.md-symlink +
config-only-settings design (spec §4.1) plus the shared plugin format means
there is nothing to port.

Tasks:
- Update plugin/PORTS.md: Grok Build moves from "reads the same format" to
  **full native compatibility, zero configuration**, quoting the xAI doc;
  matrix row updated (skills/hooks/commands/marketplaces all native).
- README "Other harnesses" + docs/user_guide/plugin-guide.md harness notes:
  same claim, one sentence each, cite the doc.
- Verification task: run /worklog:init + one /worklog:* command under Grok
  Build once available to us; record result in PORTS.md (claim is sourced
  from docs until then — say so).

## Part 2 — Mermaid visualization in the roadmap

Goal: docs/roadmap.md gains native Mermaid diagrams (GitHub/GitLab/Obsidian
render them; zero dependencies; still generated, deterministic, hash-gated).

### Corrected date model (the load-bearing fix to the draft)

The item schema has no start/due/duration — a gantt over invented dates was
rejected once before for exactly that reason. But the **event log has real
timestamps**: created (create ev), started (first in_progress ev), closed
(close ev), all ULID-derived and deterministic. So:
- **Gantt bars are historical fact, not plans**: bar = started→closed (or
  →max-ev "now" for in-flight). Items never started render as milestones-dots
  at creation date or are omitted (flag). No fabricated durations, ever.
- Wall clock never used — "now" = max ev timestamp (same rule as
  generated-at), keeping the CI hash check stable.

### Diagrams (new `## Visual roadmap` section)

1. **Dependency graph** (`graph TD`) — the previously-recommended one, fully
   derivable today: nodes = open items (kind emoji: 📦 feature 🐛 bug 🔧 ops
   ❓ triage), solid edges = parent, dashed = depends_on, node class by
   status. Cap at N=40 nodes with a "+K more" note (no silent truncation).
2. **Hierarchy** (`graph TD`, epic→story→task/subtask) for open items.
3. **Gantt** (per milestone section, event-derived dates as above; done=done
   tag, in_progress=active, blocked=crit; unplanned items suffixed ⚡).

### CLI

`worklog roadmap-render --viz=deps,hierarchy,gantt|all|none` — **default:
deps,hierarchy** (cheap, always renderable); gantt opt-in until we've lived
with it. `--no-viz` alias for none. Implementation: bin/viz_mermaid.py
(pure functions over the fold, imported by render_roadmap), canon + CANON +
init.sh list, deterministic-output tests (shuffle test extended), renderer
tests for each diagram, coverage sandbox convention respected.
`/worklog:viz` plugin command = run roadmap-render --viz=all and show it.

### Execution rule: always a background subagent

Viz work never blocks the main thread. Both the implementation waves and the
recurring runtime step (regenerate diagrams + republish the roadmap after log
changes) are delegated to ONE background subagent, run in parallel with other
tasks — the same non-blocking pattern plan-capture uses for ticket/wiki
publishing. The main session folds the result in when the notification
arrives; it never waits.

### Out of scope

- `--html` interactive dashboard (Mermaid.js standalone) — separate plan if
  wanted.
- Status pie/quadrant — the kind-mix line already carries those numbers.

## Verification

- Roadmap renders on GitHub with diagrams; hash gate stays green across
  regenerations; shuffle-determinism test covers viz output; all suites +
  coverage gate pass; wiki republish picks it up via existing ledger.
