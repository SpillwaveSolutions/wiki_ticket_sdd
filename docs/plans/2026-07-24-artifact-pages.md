---
date: 2026-07-24
slug: artifact-pages
title: Extend IA to tickets, PRs, and releases (artifact pages)
epic: 01KYABYEQP8ANXGYPBCV2T20D8
items: [01KYABYEQPXZAAY0VWF6Z8TQ27, 01KYABYEQP3YCB9AVHRPCTCMRS, 01KYABYEQPK6PV87WNZXEYRB12, 01KYABYEQP9FDY8THDV79F324G, 01KYABYEQPRM8308SYFPR8X437, 01KYABYEQPAFJM7WC3XZV6YY76, 01KYABYEQPP82DJEN19F43YRAE, 01KYABYEQPW8Q2RGGTNP71W88E, 01KYABYEQPF8N2K26ENRKREE0W, 01KYABYEQPNK7HHH5CMAR2V1JG, 01KYABYEQPDS2VFQKQ7B6YXZVR]
merged_in: 6ca181181fc8e00c57797e110c7260a8db905cba
---

# Extend IA to tickets, PRs, and releases (artifact pages)

## Context

The IA & content model epic (`docs/plans/2026-07-22-ia-content-model.md`, epic
#93, 8/9 done) gave wiki *documents* a stable `wiki_key`, `truth_state`,
sidecar metadata, and a typed-edge traceability graph — but only for docs
(plans/roadmap/status/design/adr/guide). Work items, PRs, and releases exist
only as bare stub nodes in the graph (`pr/<num>`, `release/<tag>`,
`item/<ULID>`) with no title, no dedicated page, and no attributes beyond
`doc_type`. `docs/.index/rendered/releases.md` and `traceability.md` are flat
shared indexes, not per-entity pages. The user (Rick) supplied a full PRD:
every ticket/PR/release should get its own generated page — reusing the same
wiki_key/truth_state/graph machinery — showing hierarchy, related artifacts,
and traceability in one place, so nobody has to hunt through indexes or logs.

This is a direct, sanctioned extension point, not new territory: `bin/ia.py:32`
already comments "release and code-change join [the entity enum] when they
need validation." Phase 5 of the original IA plan (issue #98, still `todo`)
is a **different**, unrelated scope (hard-fail gate promotion, GitLab/ADO/
Confluence render adapters, `/worklog:find`) — don't conflate the two, but
this plan continues from the same Phase 4 traceability foundation
(`docs/plans/2026-07-22-ia-content-model.md:680-685`).

Two design decisions confirmed with Rick before finalizing:
- **No new stored fields.** The PRD asked for `parent_wiki_key`/
  `child_wiki_keys[]`/`linked_pr_keys[]`/`release_key` as stored record
  fields. Rejected in favor of deriving all four at render time from the
  graph's existing edges (`belongs-to`/reverse, `lands-in`, `targets`) — the
  graph already has this data; a stored field would be a second, driftable
  source of truth, which `bin/ia_graph.py:8-12`'s own sidecar rule already
  forbids ("never title/status/external, which the fold owns").
- **Live PR metadata (files changed, review/CI status) is deferred.** No code
  in this repo fetches `gh pr view` data today — it's genuinely new GitHub
  API integration, separate risk profile from pure rendering. Phases 0-2 ship
  full ticket/PR/release pages from data that already exists (PR page shows
  linked tickets + release, "files changed" reads "not tracked"). The live
  sync becomes a filed follow-up item, not a silent drop.

## Design

### Phase 0 — Foundation (plumbing, no visible pages yet)
- `bin/ia_render.py`: add `item_page_name(iid, it)` / `release_page_name(tag)`
  next to `page_name()` (`:40-62`); extend `build_manifest()` (`:309-335`) to
  also loop `fold(...).items` and `release/` tags from `graph["nodes"]`.
- `bin/ia_graph.py`: add `item_links(iid, graph)` — one adjacency-projection
  helper (parent/children/PRs/release), reusing the `fwd`/`back` pattern
  already built in `render_traceability` (`ia_render.py:259-266`). Every
  later renderer calls this one helper — not three copies.
- No schema change. Verifiable via `tests/test_ia.py`'s existing
  `TestGraph`/manifest-shape assertions growing.

### Phase 1 — Ticket pages (Subtask/Task/Story/Feature/Epic)
- `render_item_page(iid, it, items, records, graph)` in `bin/ia_render.py`.
  Reuse `ia_graph.ticket_body()` (`:166-216`) as the own-description +
  traceability base; add level-branching (subtask/task vs story/feature/epic
  downward depth) inside one function, not four near-duplicates — uses
  `item_links()` from Phase 0.
- One-line summaries: derive from `body`'s first sentence at render time
  (mirrors the existing `first_heading()` pattern, `bin/ia.py:151,328`) — no
  stored/cached field, stays byte-deterministic like the rest of
  `ia_render.py` (module docstring, `:1-6`).
- Aggregate progress (Story/Feature/Epic) = inline status-count over
  `item_links()`'s children — no new stored field.
- `bin/worklog`: new `ia-ticket <ULID>` preview subcommand, wired like
  `ticket-body` (`:559-562`).
- Wire into `render_all()` (`:346-361`).

### Phase 2 — Release pages + PR pages (structured data only)
- `render_release_page(tag, records, items, graph)`: reuses the milestone→
  closed-items join already in `render_releases` (`:206-241`) plus PR edges
  via `item_links()`. Change Log section is graph-derived (closed items
  tagged with this milestone + their linked PRs), not a `CHANGELOG.md`
  parser — no code parses that file today and building one is a fragile new
  engine this project avoids. `CHANGELOG.md` itself stays untouched, human
  authored; the page's generated Change Log is a separate, always-accurate,
  mechanical list (say so in one line on the page).
- `render_pr_page(pr_num, graph, items, records)`: title/status from the
  stub node + reverse `lands-in` edges → linked tickets; `targets` → related
  release. "Changed files" / "Test/Review status" render as "not tracked"
  until Phase 3 (below) lands.
- Both wired into `build_manifest()`'s Phase-0 loop.

### Phase 3 — PR live metadata (follow-up item, not built here)
Do not implement in this epic. When Phases 0-2 land, file a separate
`kind:feature` child item describing `worklog pr-sync <num>` (one
`gh pr view` call, written via `ia.write_sidecar("pr/<num>", {...})`,
`ia.py:253-257`) — kept outside `render_all()` to preserve the network-free
render invariant (`ia_graph.py:7`).

### Phase 4 — Regeneration + tests
- Extend `tests/test_ia.py`'s existing fixture classes (`:137-262`,
  `:338+`) — page-shape test per ticket level, one PR-page test, one
  release-page test, one manifest-growth assertion.
- Regenerate via `worklog ia-render`, diffed by the existing CI mechanism.
- Maintain the ≥80%/95% coverage target on `bin/ia*.py`.

## Verification
- `pytest tests/test_ia.py` green, coverage gate holds on `bin/ia*.py`.
- `worklog ia-render` regenerates cleanly; manifest entry count grows to
  include one page per item + PR node + release tag.
- Manually inspect one rendered page per ticket level, one PR page, one
  release page — hierarchy links, one-line summaries, Change Log correct.
- `worklog trace-check` still passes/reports the same gaps as before.
- After merge: file the Phase 3 follow-up item so the deferral is tracked.

## Tasks

- [ ] (P1) Phase 0: add item/release page-name helpers and extend build_manifest()
  Add `item_page_name(iid, it)` and `release_page_name(tag)` to
  `bin/ia_render.py` next to `page_name()`, and extend `build_manifest()` to
  loop work items and release tags in addition to doc records, so every
  item/PR/release gets a manifest slot.
- [ ] (P1) Phase 0: add item_links() graph helper
  Add `item_links(iid, graph)` to `bin/ia_graph.py` — one shared
  parent/children/PR/release adjacency lookup, reusing the fwd/back pattern
  already in `render_traceability`, so ticket/PR/release renderers don't
  each reimplement graph traversal.
- [ ] (P1) Phase 1: render ticket pages for all four levels
  Add `render_item_page()` to `bin/ia_render.py`, reusing `ticket_body()` for
  the description/traceability base and branching by level (subtask/task vs
  story/feature/epic) for upward/downward hierarchy sections, wired into
  `render_all()`.
  - [ ] One-line summary derivation from body's first sentence (no cache)
  - [ ] Aggregate progress rollup for Story/Feature/Epic pages
  - [ ] `ia-ticket <ULID>` preview subcommand on `bin/worklog`
- [ ] (P1) Phase 2: render release pages with graph-derived Change Log
  Add `render_release_page()` — Change Log section built from milestone-
  tagged closed items and their linked PRs (not a CHANGELOG.md parser),
  plus Release Tree, Related PRs, Related Tickets, Dependencies sections.
- [ ] (P1) Phase 2: render PR pages
  Add `render_pr_page()` — title/status, linked tickets via reverse
  lands-in edges, related release via targets; files-changed/test-review
  status render as "not tracked" pending the Phase 3 follow-up.
- [ ] (P3) Phase 3: file PR live-metadata follow-up item
  After Phases 0-2 land, file a separate kind:feature child item for
  `worklog pr-sync` (gh pr view integration) — not implemented in this epic.
- [ ] (P1) Phase 4: extend tests/test_ia.py for the new page shapes
  Add page-shape tests per ticket level, a PR-page test, a release-page
  test, and a manifest-growth assertion to the existing test fixture
  classes — do not fork a new test file.
- [ ] (P2) Phase 4: regenerate all pages and confirm coverage gate holds
  Run `worklog ia-render`, verify CI diff-clean, confirm bin/ia*.py stays
  at or above the 80%/95% coverage target.
