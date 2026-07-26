---
date: 2026-07-26
slug: declare-graph-engineering
title: Declare wiki_ticket_sdd as a Graph Engineering system
epic: 01KYFSRNDMYCTQ1XTMXFWEVBWT
items: [01KYFSRNDMYBVMWXJFEK2AJWJJ, 01KYFSRNDMMPY0E54PQ9QSWJWK, 01KYFSRNDMSMEXKT7PV0F9X54M]
---

# Declare wiki_ticket_sdd as a Graph Engineering system

## Context

"Graph engineering" — building systems as explicit nodes + typed edges + persistent state + an index/router, instead of one long agent loop — is a real, currently-viral July 2026 framing (Peter Steinberger's post, Carlos E. Perez's follow-up, TrueFoundry/AI Builder Club write-ups; confirmed via two independent searches). A PRD arrived asking to document `wiki_ticket_sdd` (and a sibling UI repo) as an example of this pattern, citing "Boris Cherny's Graph Engineering: Opus 5 Edition."

Before writing anything, that citation was checked and does **not** hold up (confirmed independently via WebSearch and Perplexity — likely a misattributed or fabricated third-party claim, not a real Cherny/Anthropic publication). It will not be cited.

What *does* hold up, verified against real code (not vibes): this repo genuinely has the claimed primitives.
- **Nodes**: ULIDs (`bin/ulid.py:35-58`, including a deterministic variant for cross-machine ingest) identify every work item; hierarchy is real (`CLAUDE.md`'s Work taxonomy, folded in `bin/fold.py:39-72`).
- **Typed edges**: `bin/ia_graph.py:27-31` defines real edge types (`produces`, `lands-in`, `references`, `snapshot-of`, `targets`, etc.); `build_graph()` (lines 42-106) actually walks records into `docs/.index/_graph.json`, and `trace_check()` genuinely traverses it. Not a metaphor.
- **Persistent state**: `bin/fold.py` is textbook event-sourcing — append-only JSONL, dedupe-by-event-id, per-field last-writer-wins — specifically so concurrent git merges compose (`docs/adr/0001-event-log-fold-union-merge.md`).
- **Index/router**: real but modest — `bin/ia.py`/`bin/ia_render.py` produce an inventory + publish manifest (fast lookup + staleness check), not a sophisticated routing engine. Describe it honestly, don't oversell it.

The sibling `wiki_ticket_sdd_ui` repo doesn't exist as real code yet (only `docs/plans/2026-07-21-wiki-ticket-ui.md`, "plan only for now — do not implement") and isn't accessible in this session. Per team decision: **skip it entirely** — no claims about it, no edits to it.

Per team steer: don't write a defensive, hedge-everything audit. This repo already organically uses this vocabulary (README already says "typed-edge graph," "event fold"). The doc should **declare the identity** — this project already *is* graph engineering, made visible the same way it already makes work-in-progress visible — backed by real evidence, not apologetic about it.

## Design

### 1. `docs/graph-engineering.md` (new) — the main deliverable

Confident, declarative opening (not "here's how we resemble X"): this repo *is* a graph engineering system, and always has been — "graph engineering" just gave a name to what `ia_graph.py`, the event log, and the taxonomy were already doing. Ties explicitly to the repo's existing "visible WIP" philosophy from `docs/user_guide/user-guide.md`: same instinct, one more layer made visible — the graph itself.

Sections:
1. **The declaration** — one confident paragraph, no hedging.
2. **The four primitives, mapped to real code** — a table: primitive → what it is here → file:line. Nodes/edges/state stated plainly as fact; index/router described modestly (inventory + publish manifest).
3. **Diagram 1 — architecture overview**: Mermaid graph showing the four primitives and their real components (ULIDs → fold → `.work/*.jsonl` → `ia_graph.py` → `_graph.json` → `ia_render.py`/manifest → wiki/tickets).
4. **Diagram 2 — the event-sourcing flow**: Mermaid sequence/flow diagram of an item's lifecycle (create → fold → typed edges → trace-check → publish), grounded in `bin/fold.py`/`bin/ia_graph.py`'s actual functions.
5. **Where this is heading** — short, clearly-labeled proposals, not commitments: a `/graph:explore` skill built on `ia_graph.py`'s existing adjacency data (`build_adjacency()`), an Obsidian-compatible export of `_graph.json` (nodes/edges already exist, just needs a format shim), and an honest one-line mention that a dedicated visualization layer is planned in a future sibling repo (link the existing plan doc, framed as planned — not description of a shipped product).
6. **Further reading** — real, verifiable external links only (Steinberger's post if linkable, Perez's essay, one or two of the credible 2026 write-ups found via research). No fabricated citations.

### 2. `README.md` — one confident callout, not a rewrite

Add a short paragraph (near the top, matching the existing bolded-lead-phrase style already used for "typed-edge graph" etc.) declaring the graph-engineering framing and linking to `docs/graph-engineering.md`. Reuses vocabulary already present in the file — this is tightening/cross-linking an identity that's already there, not bolting on new claims.

### Explicitly out of scope

- `CLAUDE.md` — untouched. It explicitly self-describes as "policy only... do not add harness-specific notes here"; conceptual/identity framing doesn't belong there, and nothing about this request overrides that stated scope.
- `wiki_ticket_sdd_ui` — no edits, no claims about its current capabilities (it isn't real code yet).
- The fabricated "Boris Cherny" citation — not used anywhere.
- No new code, no schema changes, no adapter/dispatcher touches.

## Critical files

- `docs/graph-engineering.md` (new — the main deliverable)
- `README.md` (small addition near the top)
- Reference-only (evidence sources, not edited): `bin/ia_graph.py`, `bin/fold.py`, `bin/ulid.py`, `docs/adr/0001-event-log-fold-union-merge.md`

## Verification

1. Read `docs/graph-engineering.md` end-to-end and confirm every factual claim has a real file:line citation matching actual code — no invented capabilities, no oversold index/router language.
2. Confirm the "Where this is heading" section reads as proposals, not shipped features, and that the UI-repo mention is honestly framed as planned/future with a link to the real plan doc.
3. Render both Mermaid diagrams (or eyeball syntax) to confirm they're valid and match the real functions/files they claim to represent.
4. Confirm `README.md`'s new paragraph links correctly and doesn't duplicate content already in the new doc.
5. Confirm `CLAUDE.md` and any `wiki_ticket_sdd_ui` path are untouched.

## Tasks

- [ ] (P2) Write docs/graph-engineering.md
  Author the main deliverable: a confident declaration that this project is
  a graph engineering system, a table mapping the four primitives (nodes,
  typed edges, persistent state, index/router) to real code with file:line
  citations, two Mermaid diagrams (architecture overview and the
  event-sourcing lifecycle flow), a short forward-looking section with 2-3
  clearly-labeled proposals, and a further-reading list of real, verifiable
  external sources only.

- [ ] (P2) Add a graph-engineering callout to README.md
  Add one short paragraph near the top of the README declaring the
  graph-engineering framing and linking to the new doc, matching the
  README's existing bolded-lead-phrase style and vocabulary it already uses.

- [ ] (P3) Verify accuracy and scope boundaries
  Confirm every claim in the new doc has real code evidence, the future
  UI-repo mention is honestly framed as planned rather than shipped, both
  Mermaid diagrams are syntactically valid, and that CLAUDE.md and the
  wiki_ticket_sdd_ui repo were not touched.
