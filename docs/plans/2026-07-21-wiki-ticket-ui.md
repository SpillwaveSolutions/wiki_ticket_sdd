---
date: 2026-07-21
slug: wiki-ticket-ui
title: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
epic: 01KY111BC7PABV8W6SDNVQACSN
items: [01KY111BC7NJ4BE7JBDK2P6Y56, 01KY111BC71KJGNH55CB2DWMKN, 01KY111BC7B70C7M2RF1E57G17, 01KY111BC8QJAS9KH7N368N6RF, 01KY111BC88FS6QD49JADZ9CJ5, 01KY111BC8F9BH0T3TERYEFC3C, 01KY111BC842N3J7Y7H85NHSEG]
---

# WikiTicket UI — project status dashboard (new repo `../wiki_ticket_sdd_ui`)

## Context

WikiTicket SDD stores everything as files in the tracked repo: the event log
(`.work/todo.jsonl` / `done.jsonl`), generated roadmap, frozen plans/status/designs/ADRs,
the wiki ledger, and GitHub issues/releases. There is no way to *see* it all at once.
Rick wants a new public repo, `wiki_ticket_sdd_ui`, containing a locally-runnable app
(possibly desktop later) that visualizes the whole project status — visually stunning,
a complete dashboard. **Constraint (Rick, mid-plan): it must work with ANY GitHub repo
that uses wiki_ticket_sdd, not just this one.** Status: **plan only for now — do not
implement** (Rick, mid-plan). On approval, this plan is captured and published; the
build happens when Rick says go.

## Core design decisions

1. **Generic by construction — the target repo is runtime input, not config baked in.**
   The app opens any local checkout whose root has `.work/config.yml` (the marker that
   worklog is installed). Repo path comes from CLI arg / env / a repo-picker in the UI;
   recent repos remembered. Everything else is derived from that repo:
   - GitHub coords from `ticketing.project` in `.work/config.yml` (e.g.
     `SpillwaveSolutions/wiki_ticket_sdd`), falling back to `git remote get-url origin`.
   - Wiki URL from `wiki.root_url`.
   - Doc paths from `paths:` (plans/status/roadmap) — never hardcoded.
2. **Never reimplement worklog semantics — shell out to the target repo's own tools.**
   Every worklog-initialized repo ships `bin/worklog` (Python, stdlib-only). The server
   runs `python3 bin/worklog fold` in the target repo for the folded item list, reads
   the generated `docs/roadmap.md` for roadmap + Mermaid, and uses `git`/`gh` for
   history and releases. Fold logic stays in one place (the spec's), so the UI can
   never drift from the tracker. Raw JSONL is read directly only for the *activity
   feed* (events are the timeline; `ev` ULIDs carry timestamps).
3. **Tech: local web app first, desktop shell later.**
   - **Frontend:** Vite + React + TypeScript + Tailwind CSS, shadcn/ui components,
     Recharts (charts), `mermaid` (render roadmap diagrams), `react-markdown` +
     `gray-matter` (docs with frontmatter chips), framer-motion (polish).
   - **Backend:** a small Node server (Hono) exposing a JSON API over the target repo:
     file reads, `worklog fold`, `git log`, `gh api` (releases/issues). One process,
     `npm start -- --repo /path/to/repo` (or auto-detect cwd/parent).
   - **Desktop:** Tauri 2 wrap of the same frontend is a later, separate work item —
     the API layer is designed so Tauri's Rust side can replace the Node server
     without touching the UI. Not in the first build.
4. **GitHub data via `gh` CLI when available, unauthenticated REST fallback.** Releases,
   issue states, and PR checks come from `gh api repos/<owner>/<repo>/...`; if `gh` is
   missing, fall back to fetch against api.github.com (public repos work unauthenticated,
   rate-limited). Degrade gracefully — the file-based panels work fully offline.

## The dashboard (what "complete" means)

Dark, glassy, information-dense but calm. Left nav, top bar showing repo name +
current branch + latest tag + drift indicators. Panels:

1. **Overview** — headline stats (open/blocked/in-progress counts, epics in flight,
   latest release, days since last status report), a milestone progress ring per
   milestone, and a compact activity sparkline. All derived from `worklog fold` +
   event timestamps.
2. **Board** — kanban by status (`todo` / `in_progress` / `blocked` / recently `done`),
   cards showing level/kind badges (epic/story/task/subtask × feature/bug/ops/triage),
   priority, milestone chip, epic grouping (via `parent`), `unplanned` flag, and the
   linked GitHub issue number/URL from the item's `external` field. Click → item
   detail drawer with full event history for that ULID.
3. **Roadmap** — rendered `docs/roadmap.md` including its Mermaid blocks (dependency
   graph, hierarchy, event-dated gantt) rendered live with mermaid.js; sections
   Now/Next/Later/Needs-classification/Needs-attention preserved.
4. **Activity** — unified reverse-chron feed merging: worklog events (from both JSONL
   files, timestamps from `ev` ULIDs), git commits (`git log`), releases, and status
   reports. Filter by actor/kind/op.
5. **Releases** — GitHub releases timeline (tag, date, notes rendered), linked to the
   matching frozen roadmap snapshot `docs/roadmap/<date>_<tag>-release.md` and design
   doc pair when present.
6. **Docs** — browser for plans / ADRs / status reports / designs / user guide, with
   frontmatter rendered as metadata chips (e.g. ADR status accepted/superseded, plan's
   epic + items, design doc's git_hash/tag). Frozen docs get a "frozen" badge.
7. **Wiki** — the `.work/published.json` ledger as a table: page, source file, wiki
   URL (external link), and **drift status** (re-hash source vs `source_hash` — green
   in-sync / amber stale), mirroring the publish skill's own hash-skip logic.
8. **Sync health** — `.work/sync-state.json` cursors + per-item push state joined
   against fold output: which open items have issues, which are unpushed, orphans and
   `_conflicts` surfaced loudly.
9. **Charts** — burnup (created vs closed over time from event ULIDs), kind mix
   (triage/ops trending down per the taxonomy's rule 6), velocity by week, unplanned
   ratio (the estimate-honesty metric).

## New repo layout

```
wiki_ticket_sdd_ui/
├── README.md            # what it is, screenshot, quickstart: npx/npm start --repo <path>
├── LICENSE              # match wiki_ticket_sdd
├── package.json         # workspaces: server, web
├── server/              # Hono API: /api/repo, /api/items, /api/events, /api/roadmap,
│                        #   /api/docs/*, /api/releases, /api/wiki-ledger, /api/sync,
│                        #   /api/git/log — all scoped to the selected repo path
├── web/                 # Vite React app (panels above)
└── .github/workflows/ci.yml   # typecheck + build + vitest
```

Read-only guarantee: the app never writes to the target repo — it is a viewer.
(Mutations, if ever, go through `bin/worklog` — later item, not this plan.)

## Execution when Rick says go (NOT now)

- Wave 1: scaffold repo (`gh repo create SpillwaveSolutions/wiki_ticket_sdd_ui --public`),
  server API against the data contract above, dogfood target = `../wiki_ticket_sdd`.
- Wave 2 (parallel subagents): panels, each file-disjoint.
- Wave 3: polish pass (the "visually stunning" bar), README with screenshots, CI, tag v0.1.0.
- Work is tracked in the *main* repo's worklog (this plan's items); the UI repo is a
  deliverable, not a second tracker.

## Immediate execution (this approval)

Per Rick: **store the plan only.** Run `worklog plan-capture` (writes
`docs/plans/<date>-wiki-ticket-ui.md`, files the epic + story items on the board,
background-publishes to wiki). Then stop — no repo creation, no code.

## Verification (for the future build)

- Point the app at `../wiki_ticket_sdd` → all 9 panels populate from real data;
  fold output matches `python3 bin/worklog fold` byte-for-byte upstream.
- Point it at a *fresh* `init.sh`-scaffolded throwaway repo → app works with one item
  and no releases (the generic-repo proof).
- Wiki drift indicator flips amber when a source doc is edited without republish.
- Offline (no `gh`, no network): file-based panels still render; GitHub panels show
  a graceful "offline" state.

## Data contract (verified against the real repo this session)

- Fold output fields: `id,title,status,priority,level,kind,parent,milestone,plan,
  resolution,depends_on,labels,unplanned,external` (+ `_orphan`, `_conflicts` markers);
  open statuses `todo|in_progress|blocked`; defaults level=task, kind=triage.
- Event envelope: `ev,item,op(create|close|link|snapshot|compact),set,ts,actor`
  (+`through` on compact); ULID `ev` encodes the event timestamp.
- `published.json`: `{slug: {rev, source, source_hash(12-hex), url, title?}}`.
- `sync-state.json`: `{adapter_path, cursors:{github:ts}, items:{ulid:{last_push,
  last_pushed_hash}}}`.
- Frontmatter: plans `date/slug/title/epic/items`; status `kind/date/window/through/
  generated_at`; designs `generated_at/git_hash/branch/tag/roadmap`; ADRs
  `id/slug/title/date/status/deciders/tags/supersedes/superseded_by`.
- `docs/roadmap.md` is generated with embedded Mermaid (deps/hierarchy default,
  gantt opt-in), header comment carries `source-hash`/`generated-at`.

## Tasks

- [ ] (P2) Scaffold public repo wiki_ticket_sdd_ui: README, LICENSE, npm workspaces, CI
- [ ] (P2) Server: Hono JSON API over any worklog repo (fold, events, docs, git, gh, wiki ledger, sync state)
- [ ] (P2) Web shell: Vite + React + Tailwind dark dashboard chrome with repo picker
- [ ] (P2) Panels wave 1: Overview, Board, Roadmap (Mermaid), Activity feed
- [ ] (P2) Panels wave 2: Releases, Docs browser, Wiki drift, Sync health, Charts
- [ ] (P3) Polish pass to the visually-stunning bar; README screenshots; tag v0.1.0
- [ ] (P3) Tauri 2 desktop shell wrapping the same frontend
