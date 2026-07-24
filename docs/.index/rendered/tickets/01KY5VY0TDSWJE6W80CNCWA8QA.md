# WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)

`01KY5VY0TDSWJE6W80CNCWA8QA` · epic/feature · **done**

Local read-only dashboard app (new public repo wiki_ticket_sdd_ui) visualizing any worklog repo: board, roadmap, activity, releases, docs, publish plane, sync health, charts, and an interactive traceability graph.

## Children

- [[Ticket-01KY5VY0TDTD7PQDT6EVD5AG9N]] Scaffold public repo wiki_ticket_sdd_ui: README, LICENSE, npm workspaces, CI — Create the public repo with npm workspaces (server, web), CI running typecheck,
build, and vitest. (done)
- [[Ticket-01KY5VY0TE7G7ZC5W20T3KAXJ7]] Tauri 2 desktop shell wrapping the same frontend — Unchanged from the superseded plan; the API layer stays swappable for Tauri's Rust
side without touching the UI. (done)
- [[Ticket-01KY5VY0TE8B6RXVX1MQYJZ0TH]] Polish pass to the visually-stunning bar; README screenshots; tag v0.1.0 — Unchanged from the superseded plan. (done)
- [[Ticket-01KY5VY0TE8EZPWNZPZWSPTSAR]] Traceability panel: interactive _graph.json explorer with trace-check integrity checklist — Pick any node and walk plan → item → ticket → PR → release in both directions;
supersede chains; trace-check gaps surfaced as an integrity checklist. (done)
- [[Ticket-01KY5VY0TEK8XSGP2SG57GF0KT]] Web shell: Vite + React + Tailwind dark dashboard chrome with repo picker — Dark glassy shell, left nav, top bar with repo/branch/tag/drift indicators, recent
repos remembered. (done)
- [[Ticket-01KY5VY0TEKXBXK91S9ZFZTJZ5]] Panels wave 2: Releases, Docs browser (inventory-driven), Publish plane (3-way drift), Sync health, Charts — Docs browser consumes _inventory.json with truth-state badges and supersede chains. (done)
- [[Ticket-01KY5VY0TEW87KK6AW6FQTYGZ9]] Server: Hono JSON API over any worklog repo — fold, events, docs, index plane, git, gh, ledger, sync state — The original API surface plus thin reads of docs/.index/_inventory.json, _graph.json,
publish-manifest.json and a trace-check endpoint. (done)
- [[Ticket-01KY5VY0TEWBMZK5W6YJN5FQ9D]] Panels wave 1: Overview, Board, Roadmap (Mermaid), Activity feed — As in the superseded plan; Roadmap panel reads the YAML frontmatter header the IA
work gave docs/roadmap.md instead of HTML comments. (done)

Progress: 8/8 done

## Related tickets

- [github #113](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/113)
