# Traceability

_The evidence chain: plan → item → ticket → code → release, forward and backward. Generated from `docs/.index/_graph.json`; do not edit._

### Add MIT LICENSE (repo was public with no license)
`01KY69K4ZJMYJ1HWMWXMQ4J7BA` · status: done

### ia.classify treats README.md inside docs/plans|status|adr dirs as a doc of that type — generic repos with folder READMEs fail inventory
`01KY6037BN94086PR1QP0CM7XC` · status: done

### init.sh copy list missing IA modules (ia.py, ia_render.py, ia_graph.py, canonical.py, sync_dispatch.py) — fresh repos get worklog with broken ia-* commands
`01KY5ZY3ZX2Z4F73Y0BT0M0NR5` · status: done

### Panels wave 1: Overview, Board, Roadmap (Mermaid), Activity feed
`01KY5VY0TEWBMZK5W6YJN5FQ9D` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#117](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/117)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Server: Hono JSON API over any worklog repo — fold, events, docs, index plane, git, gh, ledger, sync state
`01KY5VY0TEW87KK6AW6FQTYGZ9` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#115](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/115)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Panels wave 2: Releases, Docs browser (inventory-driven), Publish plane (3-way drift), Sync health, Charts
`01KY5VY0TEKXBXK91S9ZFZTJZ5` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#118](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/118)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Web shell: Vite + React + Tailwind dark dashboard chrome with repo picker
`01KY5VY0TEK8XSGP2SG57GF0KT` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#116](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/116)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Traceability panel: interactive _graph.json explorer with trace-check integrity checklist
`01KY5VY0TE8EZPWNZPZWSPTSAR` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#119](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/119)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Polish pass to the visually-stunning bar; README screenshots; tag v0.1.0
`01KY5VY0TE8B6RXVX1MQYJZ0TH` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#120](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/120)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Tauri 2 desktop shell wrapping the same frontend
`01KY5VY0TE7G7ZC5W20T3KAXJ7` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#121](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/121)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Scaffold public repo wiki_ticket_sdd_ui: README, LICENSE, npm workspaces, CI
`01KY5VY0TDTD7PQDT6EVD5AG9N` · status: cancelled
- belongs-to: WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
- references: [github#114](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/114)
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui)
`01KY5VY0TDSWJE6W80CNCWA8QA` · status: cancelled
- references: [github#113](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/113)
- contains: Scaffold public repo wiki_ticket_sdd_ui: README, LICENSE, npm workspaces, CI
- contains: Tauri 2 desktop shell wrapping the same frontend
- contains: Polish pass to the visually-stunning bar; README screenshots; tag v0.1.0
- contains: Traceability panel: interactive _graph.json explorer with trace-check integrity checklist
- contains: Web shell: Vite + React + Tailwind dark dashboard chrome with repo picker
- contains: Panels wave 2: Releases, Docs browser (inventory-driven), Publish plane (3-way drift), Sync health, Charts
- contains: Server: Hono JSON API over any worklog repo — fold, events, docs, index plane, git, gh, ledger, sync state
- contains: Panels wave 1: Overview, Board, Roadmap (Mermaid), Activity feed
- produced-by: [[Plan-wiki-ticket-ui-ia]]

### Author superseding UI plan: re-base wiki_ticket_sdd_ui design on the shipped IA & content model (manifest, wiki_key, truth_state, graph, sidecars)
`01KY5VRR3R4JEFSV3S9J6PFD7N` · status: done

### Schema boundary: split doc.schema.json (documents) from entity schema (items, releases, code-changes) — defer until a second graph entity needs validation
`01KY5QV5G05V77TKESCJVY62S3` · status: done
- references: [github#111](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/111)

### Add schema drift test: schema/doc.schema.json must stay equivalent to bin/ia.py validator constants
`01KY5QJAY8C8G5C4FEBMRFKM51` · status: done
- references: [github#110](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/110)

### Repair frozen-plan drift: restore grok-compat-and-mermaid-viz to published version, move background-subagent rule to amendment doc
`01KY5QJARJ0S9QHGRPAV8SFV9H` · status: done
- references: [github#109](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/109)
- produced-by: [[Plan-grok-viz-background-execution]]

### pre-commit hook pollutes worktree with bin/__pycache__ after git add — merge aborts on tracked-vs-untracked pyc collision
`01KY5P9V0CMM86G43HH4Q28ZDD` · status: done
- references: [github#107](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/107)

### Configurable work-item field model: optional fields (estimate, risk, effort, value, confidence, owner, due_date, acceptance_criteria, blocked_by/blocks) behind work_item_fields config
`01KY5NE0ZYGBWG44N0KPEBFCZ8` · status: todo
- references: [github#108](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/108)

### issue-description skill + rich ticket bodies in ticket-sync (summary/context/outcome/scope/acceptance/traceability from the item graph)
`01KY5N7DF2YMR9E11G4W3HF6PY` · status: done
- references: [github#106](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/106)

### PR-description skill: 10-section high-context PR body spec (big picture, runtime context, scope, flow, testing honesty, out-of-scope, ticket glossary)
`01KY5N447CK55EXFHTQGWA9JZ9` · status: done
- references: [github#105](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/105)

### GitHub Wiki shows raw YAML frontmatter on published pages — strip at publish time
`01KY5JB9F9XKKD1RNS66J6DXHZ` · status: done

### Compaction aborts on closed orphan item — snapshot must not inject taxonomy defaults
`01KY5HW7KSBAYS1RE95ZT8BYM4` · status: done
- references: [github#101](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/101)

### Tickets unreadable: no junior-dev/PM description — add --body to add/update, plan-capture task descriptions, skill rule, backfill open items
`01KY5HGKCBKJA5A3ZJGMPASP3X` · status: done

### Phase 4: ia-graph typed-edge taxonomy + link-pr + trace-check + Traceability Index; propose-only edge seeding via suggestions.jsonl
`01KY5G9ZW0Z6JFMVTAFC54RM36` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- references: [github#100](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/100)
- produced-by: [[Plan-ia-content-model]]

### Phase 2: worklog ia-render + ia-manifest — generated Home, Sidebar, publish-time truth banners in docs/.index/rendered/
`01KY5G9ZW0X5F3K7KHP1SXFM3Q` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- references: [github#99](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/99)
- produced-by: [[Plan-ia-content-model]]

### Phase 5: promote gates to hard fail; platform render adapters (GitLab/ADO/Confluence); /worklog:find + glossary
`01KY5G9ZW0RABXWHEMEP1FAV2G` · status: todo
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- references: [github#98](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/98)
- produced-by: [[Plan-ia-content-model]]

### Phase 1: CI gates — wiki_key present/unique, schema-valid frontmatter (warn one cycle, then hard)
`01KY5G9ZW0PNKDDEK5TM8GS2J6` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- references: [github#97](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/97)
- produced-by: [[Plan-ia-content-model]]

### Phase 2: extend wiki-publish to consume publish-manifest.json; replace hand-maintained wiki-home.md with generated Home
`01KY5G9ZW0PEZK9PTM3NG0PYX7` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- references: [github#96](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/96)
- produced-by: [[Plan-ia-content-model]]

### Phase 0: schema/doc.schema.json unified frontmatter schema + stdlib validator (adr.schema.json pattern)
`01KY5G9ZW0PBXTBKRJJ70QHR5P` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- references: [github#95](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/95)
- produced-by: [[Plan-ia-content-model]]

### Phase 3: generated indexes — Decisions, Releases, Status Archive; wire ia-index into release + plan-capture skills
`01KY5G9ZW0MQD9335S641DC7ZG` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- references: [github#94](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/94)
- produced-by: [[Plan-ia-content-model]]

### IA & content model (supersedes wiki-information-architecture)
`01KY5G9ZW0H2YMNWDFJYGRPYE5` · status: todo
- references: [github#93](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/93)
- contains: Phase 0: worklog wiki-key + worklog ia-inventory (read-only) + migration record docs/migrations/0002-ia-content-model.md
- contains: Phase 1: worklog ia-normalize — sidecars for frozen docs, in-place for sanctioned-live; backfill wiki_key (ledger-seeded) + truth_state
- contains: Phase 3: generated indexes — Decisions, Releases, Status Archive; wire ia-index into release + plan-capture skills
- contains: Phase 0: schema/doc.schema.json unified frontmatter schema + stdlib validator (adr.schema.json pattern)
- contains: Phase 2: extend wiki-publish to consume publish-manifest.json; replace hand-maintained wiki-home.md with generated Home
- contains: Phase 1: CI gates — wiki_key present/unique, schema-valid frontmatter (warn one cycle, then hard)
- contains: Phase 5: promote gates to hard fail; platform render adapters (GitLab/ADO/Confluence); /worklog:find + glossary
- contains: Phase 2: worklog ia-render + ia-manifest — generated Home, Sidebar, publish-time truth banners in docs/.index/rendered/
- contains: Phase 4: ia-graph typed-edge taxonomy + link-pr + trace-check + Traceability Index; propose-only edge seeding via suggestions.jsonl
- produced-by: [[Plan-ia-content-model]]

### Phase 1: worklog ia-normalize — sidecars for frozen docs, in-place for sanctioned-live; backfill wiki_key (ledger-seeded) + truth_state
`01KY5G9ZW0EYQ5T83RP46Z7952` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- references: [github#92](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/92)
- produced-by: [[Plan-ia-content-model]]

### Phase 0: worklog wiki-key + worklog ia-inventory (read-only) + migration record docs/migrations/0002-ia-content-model.md
`01KY5G9ZW025TRGTHFAFSVEXSX` · status: done
- belongs-to: IA & content model (supersedes wiki-information-architecture)
- references: [github#91](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/91)
- produced-by: [[Plan-ia-content-model]]

### Phase 1: content inventory — classify every existing doc and wiki page into the model
`01KY5F6QA4YVHE4ESMT3E2KYK9` · status: done
- belongs-to: Wiki information architecture
- references: [github#90](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/90)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 3 (coarse): traceability graph, worklog docs validate/index/health/trace, CI gates — explode via superseding plan
`01KY5F6QA4WWSSZVKE0YJ7YHXZ` · status: done
- belongs-to: Wiki information architecture
- references: [github#89](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/89)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 2 (coarse): frontmatter normalization + generated indexes incl. Traceability Index — explode via superseding plan
`01KY5F6QA43HN4CAMFBBD6MKSA` · status: done
- belongs-to: Wiki information architecture
- references: [github#88](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/88)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 0: _Sidebar.md mapped to the 9 target sections
`01KY5F6QA3YAAWKF4PC5VPM90A` · status: done
- belongs-to: Wiki information architecture
- references: [github#87](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/87)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 0: current-vs-historical banners + Wiki-Structure conventions page
`01KY5F6QA3Y05F7S3ZMWEQ5BB2` · status: done
- belongs-to: Wiki information architecture
- references: [github#86](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/86)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 0: redesign Home as question-oriented orientation hub with current-vs-history zones
`01KY5F6QA3G8VWG73VVD3AWDGE` · status: done
- belongs-to: Wiki information architecture
- references: [github#85](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/85)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 1: docs/navigation.yml + docs/publishing.yml publish manifest
`01KY5F6QA3AV0B9NGBBKTMJS7J` · status: done
- belongs-to: Wiki information architecture
- references: [github#84](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/84)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 0: index pages — Plans-Index, ADR-Index, Status-Index, Release-History
`01KY5F6QA35SKWEN7YGMVR16XS` · status: done
- belongs-to: Wiki information architecture
- references: [github#83](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/83)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 1: document templates (plan, adr, status, design) with required frontmatter
`01KY5F6QA32MWBKTYPVPTBPKQ7` · status: done
- belongs-to: Wiki information architecture
- references: [github#82](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/82)
- produced-by: [[Plan-wiki-information-architecture]]

### Phase 1: docs/information-architecture.md + docs/content-model.md
`01KY5F6QA32GH5RWA1BH42EVSQ` · status: done
- belongs-to: Wiki information architecture
- references: [github#81](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/81)
- produced-by: [[Plan-wiki-information-architecture]]

### Wiki information architecture
`01KY5F6QA220S0K7RRK2Q80XR8` · status: done
- references: [github#80](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/80)
- contains: Phase 1: docs/information-architecture.md + docs/content-model.md
- contains: Phase 1: document templates (plan, adr, status, design) with required frontmatter
- contains: Phase 0: index pages — Plans-Index, ADR-Index, Status-Index, Release-History
- contains: Phase 1: docs/navigation.yml + docs/publishing.yml publish manifest
- contains: Phase 0: redesign Home as question-oriented orientation hub with current-vs-history zones
- contains: Phase 0: current-vs-historical banners + Wiki-Structure conventions page
- contains: Phase 0: _Sidebar.md mapped to the 9 target sections
- contains: Phase 2 (coarse): frontmatter normalization + generated indexes incl. Traceability Index — explode via superseding plan
- contains: Phase 3 (coarse): traceability graph, worklog docs validate/index/health/trace, CI gates — explode via superseding plan
- contains: Phase 1: content inventory — classify every existing doc and wiki page into the model
- produced-by: [[Plan-wiki-information-architecture]]

### Ignore tmp/ scratch dir in .gitignore (onboarding notes live there untracked)
`01KY5D79CY0DPSDAQ09QZFW694` · status: done

### Scrub inputs/ from main history (drop d538d15 + revert f97626a via rebase, force-with-lease) and delete local copies
`01KY2KHHF43KAZ54F57BQW71TD` · status: todo
- references: [github#79](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/79)

### Cut v0.12.1: stamp CHANGELOG, snapshot roadmap, tag, GitHub release, publish
`01KY2J9WN6WN6A8TVMR1TNS6ZX` · status: done
- targets: release/v0.12.1

### Close verb leaves remote taxonomy labels stale; next pull re-ingests them, reverting local reclassify-then-close (LWW on remote rev)
`01KY129SGV3DEX5NVAP34VV9G2` · status: done
- references: [github#76](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/76)
- targets: release/v0.12.1

### Cut v0.12.0: stamp CHANGELOG, snapshot roadmap, tag, GitHub release, publish (first release exercising design-docs doc-sync)
`01KY11HDR3A5SR342DHG1BH5AZ` · status: done
- references: [github#74](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/74)
- targets: release/v0.12.0

### Panels wave 1: Overview, Board, Roadmap (Mermaid), Activity feed
`01KY111BC8QJAS9KH7N368N6RF` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#72](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/72)
- produced-by: [[Plan-wiki-ticket-ui]]

### Polish pass to the visually-stunning bar; README screenshots; tag v0.1.0
`01KY111BC8F9BH0T3TERYEFC3C` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#71](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/71)
- produced-by: [[Plan-wiki-ticket-ui]]

### Panels wave 2: Releases, Docs browser, Wiki drift, Sync health, Charts
`01KY111BC88FS6QD49JADZ9CJ5` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#70](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/70)
- produced-by: [[Plan-wiki-ticket-ui]]

### Tauri 2 desktop shell wrapping the same frontend
`01KY111BC842N3J7Y7H85NHSEG` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#69](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/69)
- produced-by: [[Plan-wiki-ticket-ui]]

### WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
`01KY111BC7PABV8W6SDNVQACSN` · status: cancelled
- references: [github#68](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/68)
- contains: Server: Hono JSON API over any worklog repo (fold, events, docs, git, gh, wiki ledger, sync state)
- contains: Web shell: Vite + React + Tailwind dark dashboard chrome with repo picker
- contains: Scaffold public repo wiki_ticket_sdd_ui: README, LICENSE, npm workspaces, CI
- contains: Tauri 2 desktop shell wrapping the same frontend
- contains: Panels wave 2: Releases, Docs browser, Wiki drift, Sync health, Charts
- contains: Polish pass to the visually-stunning bar; README screenshots; tag v0.1.0
- contains: Panels wave 1: Overview, Board, Roadmap (Mermaid), Activity feed
- produced-by: [[Plan-wiki-ticket-ui]]

### Scaffold public repo wiki_ticket_sdd_ui: README, LICENSE, npm workspaces, CI
`01KY111BC7NJ4BE7JBDK2P6Y56` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#67](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/67)
- produced-by: [[Plan-wiki-ticket-ui]]

### Web shell: Vite + React + Tailwind dark dashboard chrome with repo picker
`01KY111BC7B70C7M2RF1E57G17` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#66](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/66)
- produced-by: [[Plan-wiki-ticket-ui]]

### Server: Hono JSON API over any worklog repo (fold, events, docs, git, gh, wiki ledger, sync state)
`01KY111BC71KJGNH55CB2DWMKN` · status: cancelled
- belongs-to: WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui)
- references: [github#65](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/65)
- produced-by: [[Plan-wiki-ticket-ui]]

### sync.conflict_policy local-wins/remote-wins documented in config but never read by dispatcher — implement or descope
`01KXY8V686YPK4ET2XFB2KW2RX` · status: done
- references: [github#64](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/64)
- targets: release/v0.12.0

### No reopen CLI: fold supports reopen but worklog has no subcommand; update --status todo leaks stale resolution
`01KXY8V62QH1H1V70M0Y08ARXX` · status: done
- references: [github#63](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/63)
- targets: release/v0.12.0

### Pull sync drops taxonomy: sync_dispatch INGEST_FIELDS lacks level/kind/milestone — remote taxonomy edits silently not ingested
`01KXY8V5WZJ4E76B3D39KW5DCE` · status: done
- references: [github#62](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/62)
- targets: release/v0.12.0

### Packaging guard matches 'docs/' as substring — skills/design-docs/ false-positive; match path segments
`01KXY85EAS6YSEH2EDFW3PXN22` · status: done

### wiki: Design-Doc + Code-Walkthrough live pages, frozen dated pages, Home links, published.json ledger keys
`01KXY7X0QJY4JZWYYF2CA46B9G` · status: done
- belongs-to: Design docs + code walkthroughs with release-time doc sync
- references: [github#60](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/60)
- produced-by: [[Plan-design-docs-release-sync]]

### dogfood generation: current_design_doc + current_code_walkthrough + dated v0.11.0-release pair under docs/designs/ (background agent, grounded in actual repo, frontmatter tag/hash/branch/roadmap)
`01KXY7X0QJQHZBCSCR438RFFMM` · status: done
- belongs-to: Design docs + code walkthroughs with release-time doc sync
- references: [github#59](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/59)
- produced-by: [[Plan-design-docs-release-sync]]

### design-docs skill: SKILL.md + references/design-doc-prompt.md (Rick's 35-section prompt, improved) + references/code-walkthrough-prompt.md; plugin mirror with version frontmatter
`01KXY7X0QJCEHRDABCXF6QKXF7` · status: done
- belongs-to: Design docs + code walkthroughs with release-time doc sync
- references: [github#58](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/58)
- produced-by: [[Plan-design-docs-release-sync]]

### release skill gains background-agents doc-sync step (both copies); release.sync_docs list in .work/config.yml + init.sh scaffold
`01KXY7X0QJAE0QH2W30JKK39TA` · status: done
- belongs-to: Design docs + code walkthroughs with release-time doc sync
- references: [github#57](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/57)
- produced-by: [[Plan-design-docs-release-sync]]

### suites green; PR; green-gates merge; item closeout
`01KXY7X0QJ79852RFK5Q8F6FZM` · status: done
- belongs-to: Design docs + code walkthroughs with release-time doc sync
- references: [github#56](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/56)
- produced-by: [[Plan-design-docs-release-sync]]

### docs: user guide + plugin guide + README document design artifacts; CLAUDE.md policy bullet; wiki-publish default set gains designs
`01KXY7X0QJ2SBY6KTQ30AKASP7` · status: done
- belongs-to: Design docs + code walkthroughs with release-time doc sync
- references: [github#55](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/55)
- produced-by: [[Plan-design-docs-release-sync]]

### Design docs + code walkthroughs with release-time doc sync
`01KXY7X0QH47Z6B5QZD5G052FJ` · status: done
- references: [github#54](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/54)
- contains: docs: user guide + plugin guide + README document design artifacts; CLAUDE.md policy bullet; wiki-publish default set gains designs
- contains: suites green; PR; green-gates merge; item closeout
- contains: release skill gains background-agents doc-sync step (both copies); release.sync_docs list in .work/config.yml + init.sh scaffold
- contains: design-docs skill: SKILL.md + references/design-doc-prompt.md (Rick's 35-section prompt, improved) + references/code-walkthrough-prompt.md; plugin mirror with version frontmatter
- contains: dogfood generation: current_design_doc + current_code_walkthrough + dated v0.11.0-release pair under docs/designs/ (background agent, grounded in actual repo, frontmatter tag/hash/branch/roadmap)
- contains: wiki: Design-Doc + Code-Walkthrough live pages, frozen dated pages, Home links, published.json ledger keys
- produced-by: [[Plan-design-docs-release-sync]]

### Cut v0.11.0: stamp lockstep versions + CHANGELOG, snapshot roadmap, tag, GitHub release, publish
`01KXY449A7CEKMJXTQPZRC2WX9` · status: done
- targets: release/v0.11.0

### Widen system enums: linear, gitlab, codecatalyst (AWS), explicit other; GCP no-native-tracker note; enum-is-advisory semantics
`01KXY3CQY87WFM35ZECK5TMR4S` · status: done

### Daily status report 2026-07-19
`01KXY2N7XC0BWB2AFWDD9VAECJ` · status: done
- targets: release/v0.10.0

### Migration guide: adopting worklog with existing tickets — pre-seed external via worklog link (create-vs-update keys purely on external presence), pilot one epic, sync --dry-run acceptance gate = 0 creates
`01KXXY4QW2MR804KTV4RQ952DW` · status: done
- belongs-to: ADO migration feedback: tag markers, update-merge safety, link-first import

### Adapter update-merge safety rule: updates merge tags and touch only changed fields — never overwrite existing remote content; add to adapters/README authoring rules + fake adapter behavior + dumbness-compatible test
`01KXXY4QPE8RHA7D0TYN3VS0MY` · status: done
- belongs-to: ADO migration feedback: tag markers, update-merge safety, link-first import

### Marker style per system end-to-end: ADO strips HTML comments from Description — marker must be a tag (worklog:<ulid>); verify dispatcher honors capabilities.marker.style/template beyond html_comment; document in ticket-sync skill + adapters/README
`01KXXY4QH87BAJ0M7XBJH3Y0P7` · status: done
- belongs-to: ADO migration feedback: tag markers, update-merge safety, link-first import

### ADO migration feedback: tag markers, update-merge safety, link-first import
`01KXXY4QBSGEX3HPMPSENYFA5A` · status: done
- references: [github#49](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/49)
- contains: Marker style per system end-to-end: ADO strips HTML comments from Description — marker must be a tag (worklog:<ulid>); verify dispatcher honors capabilities.marker.style/template beyond html_comment; document in ticket-sync skill + adapters/README
- contains: Adapter update-merge safety rule: updates merge tags and touch only changed fields — never overwrite existing remote content; add to adapters/README authoring rules + fake adapter behavior + dumbness-compatible test
- contains: Migration guide: adopting worklog with existing tickets — pre-seed external via worklog link (create-vs-update keys purely on external presence), pilot one epic, sync --dry-run acceptance gate = 0 creates

### Cut v0.10.0
`01KXXT3XSWDX75JFJJ7DRPMX1Z` · status: done
- targets: release/v0.10.0

### Stop hook root cause was untracked files (inputs/) counted as dirty — race diagnosis in #46 was wrong; use status -uno
`01KXXRQVRNAC61JC4RPYRWH6R2` · status: done

### Stop hook false-positives during background merge-chain branch handoffs (2x on 2026-07-19): gate reads transient tree state
`01KXXPCNQDQG9YQSEJGFRHNE12` · status: done

### Cut v0.9.0
`01KXXP6PBPXCNHAQF6Z774VAHR` · status: done
- targets: release/v0.9.0

### CLI accepts empty item id: update/close/link/ingest append orphan events for ''
`01KXXMCG418TSDDKCEZ61ZSFMH` · status: done

### Feature flag for auto-merge-on-green (default on)
`01KXXM7MD5SRRZ19EM2QGWNBHJ` · status: done
- references: [github#39](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/39)

### Grok Build native compat statement + Mermaid roadmap viz (deps/hierarchy default, event-dated gantt)
`01KXXM1Z13NPYK1XBJ1EQFEKGT` · status: done
- produced-by: [[Plan-grok-compat-and-mermaid-viz]]

### Cut v0.8.0
`01KXXKWMV2Y6YGW2GY24YFZ9HY` · status: done
- targets: release/v0.8.0

### test_adr ran repo bin/ from sandbox cwd — invisible to subprocess coverage (caught by the green-gates loop refusing PR #36)
`01KXXKPNAHYJD2143G5VAB843C` · status: done

### Seed ADRs 0001-0003 from real decisions; wiki-publish default set gains ADRs; docs + Home section
`01KXXJYKGPV41JK02KX0X67Q0G` · status: done
- belongs-to: Architecture Decision Records: schema-validated docs/adr/, worklog adr new|list|check, wiki-synced
- produced-by: [[Plan-adr]]

### worklog adr subcommands + schema/adr.schema.json + pre-commit check + tests
`01KXXJYKB1B12WEXTS6FZZ7QH2` · status: done
- belongs-to: Architecture Decision Records: schema-validated docs/adr/, worklog adr new|list|check, wiki-synced
- produced-by: [[Plan-adr]]

### Architecture Decision Records: schema-validated docs/adr/, worklog adr new|list|check, wiki-synced
`01KXXJYK5KS3MQWRPGZ3WNA790` · status: done
- contains: worklog adr subcommands + schema/adr.schema.json + pre-commit check + tests
- contains: Seed ADRs 0001-0003 from real decisions; wiki-publish default set gains ADRs; docs + Home section
- produced-by: [[Plan-adr]]

### Dispatcher pushes orphan/untitled items: scope must skip _orphan and titleless items, drift-report instead
`01KXXJDW8XQ8S5MPST369MJQZT` · status: done

### Cut v0.7.0: stamp CHANGELOG, snapshot roadmap, tag, GitHub release, publish
`01KXXHXHFY3RV0X4M92PQ3PCBZ` · status: done
- targets: release/v0.7.0

### Hook gap: pre-commit schema check does not enforce taxonomy §2 rules (spec §3.3) — CLI-only enforcement
`01KXXGET7PTBERR80PHA2XM7RN` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)

### Docs refresh: README + user guide cover taxonomy, classifier, promote, adapter contract, green-gates merge, coverage gate
`01KXXG2QPCE09N0V2Y1DKZDNSG` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
- produced-by: [[Plan-work-taxonomy]]

### v0.7.0 CHANGELOG, full-suite + coverage verification, dogfood sync with new fields
`01KXXFKHVTZQZ371DF7Z5HQB8M` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
- produced-by: [[Plan-work-taxonomy]]

### Roadmap: Needs-classification section, kind-mix per epic, milestone grouping (derived epic milestone), tests
`01KXXFKHPHDANP7S4GKC20G8EV` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
- produced-by: [[Plan-work-taxonomy]]

### Edges+spec: dispatcher/adapters map kind+milestone, spec v1.7 field/hash updates, migration doc, work-track/plan-capture skill updates
`01KXXFKHH0VP73C2X6P9EX4616` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
- produced-by: [[Plan-work-taxonomy]]

### Policy: CLAUDE.md taxonomy block (markers, permissioned init step), classifier graduates Stop hook, classify skill, config block, tests
`01KXXFKHBMR218J218RNN7C07N` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
- produced-by: [[Plan-work-taxonomy]]

### Core: fold/canonical/CLI level+kind+milestone, triage default, type-alias migration, promote subcommand, tests
`01KXXFKH6438M5ZV8ZKM0CH9QN` · status: done
- belongs-to: Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
- produced-by: [[Plan-work-taxonomy]]

### Cut v0.6.0: stamp CHANGELOG, snapshot roadmap, tag, GitHub release, publish
`01KXXF29E1WHP41QPNX469DVDM` · status: done

### Work taxonomy: level/kind/milestone axes + CLAUDE.md block + flag-gated classifier (propose-only)
`01KXV61H5BDS7TD99H0FF9FE11` · status: done
- references: [github#29](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/29)
- contains: Core: fold/canonical/CLI level+kind+milestone, triage default, type-alias migration, promote subcommand, tests
- contains: Policy: CLAUDE.md taxonomy block (markers, permissioned init step), classifier graduates Stop hook, classify skill, config block, tests
- contains: Edges+spec: dispatcher/adapters map kind+milestone, spec v1.7 field/hash updates, migration doc, work-track/plan-capture skill updates
- contains: Roadmap: Needs-classification section, kind-mix per epic, milestone grouping (derived epic milestone), tests
- contains: v0.7.0 CHANGELOG, full-suite + coverage verification, dogfood sync with new fields
- contains: Docs refresh: README + user guide cover taxonomy, classifier, promote, adapter contract, green-gates merge, coverage gate
- contains: Hook gap: pre-commit schema check does not enforce taxonomy §2 rules (spec §3.3) — CLI-only enforcement
- produced-by: [[Plan-work-taxonomy]]

### /worklog:merge command + merge-green skill + CLAUDE.md policy bullet
`01KXV5DQPRDD2W1QKCXRQ02A58` · status: done
- belongs-to: Green-gates merge policy: PRs merge only when all checks pass; /worklog:merge polls every 5 min until green

### plugin/scripts/merge-when-green.sh poll loop + fake-gh test suite
`01KXV5DQHGQ6EQZDRVR2MV92KZ` · status: done
- belongs-to: Green-gates merge policy: PRs merge only when all checks pass; /worklog:merge polls every 5 min until green

### Green-gates merge policy: PRs merge only when all checks pass; /worklog:merge polls every 5 min until green
`01KXV5DQC9M70PN3A4AS0VCBQH` · status: done
- contains: plugin/scripts/merge-when-green.sh poll loop + fake-gh test suite
- contains: /worklog:merge command + merge-green skill + CLAUDE.md policy bullet

### Coverage gate blind to subprocess-exercised modules: sync_dispatch tanks total to 54%; wire subprocess coverage + path aliasing
`01KXV2KQRXZBKE2V6ADNGMZX62` · status: done

### PR gate: test coverage >=80% enforced in CI (bin/ modules), target 95% stated in CLAUDE.md
`01KXV1TTAW8G80DWS7ZMNJX3XE` · status: done

### v0.6.0 + dogfood: adapter check green against fake and github example
`01KXV1J05APQR0DBP1840ZPVRM` · status: done
- belongs-to: Typed adapter contract for ticket-sync: dispatcher owns invariants, generated adapters, fake for CI
- produced-by: [[Plan-typed-adapter-contract]]

### adapters/github worked example over gh + ticket-sync skill delegates invariants to dispatcher + CI wiring
`01KXV1J0179NHDTP9K8FRVZGYP` · status: done
- belongs-to: Typed adapter contract for ticket-sync: dispatcher owns invariants, generated adapters, fake for CI
- produced-by: [[Plan-typed-adapter-contract]]

### sync_dispatch.py: dispatcher owns §4 invariants; worklog sync/adapter-check wiring (last stub falls); dispatch tests
`01KXV1HZX2B49T1PB0GA4H0YMS` · status: done
- belongs-to: Typed adapter contract for ticket-sync: dispatcher owns invariants, generated adapters, fake for CI
- produced-by: [[Plan-typed-adapter-contract]]

### spec v1.6: §8.1 GitHub-UI merge caveat + §9 typed-contract reconciliation; user-guide recovery section
`01KXV1HZS08M62Z5EZF4HTVB6G` · status: done
- belongs-to: Typed adapter contract for ticket-sync: dispatcher owns invariants, generated adapters, fake for CI
- produced-by: [[Plan-typed-adapter-contract]]

### canonical.py + capabilities/adapter-io schemas + fake adapter + contract tests
`01KXV1HZMTKQGJHX0VSETZJX4Z` · status: done
- belongs-to: Typed adapter contract for ticket-sync: dispatcher owns invariants, generated adapters, fake for CI
- produced-by: [[Plan-typed-adapter-contract]]

### GitHub server-side merges ignore merge=union — log/roadmap conflicts in PR UI
`01KXV1B3RY3G25WR0K2ZGYEH73` · status: done
- references: [github#25](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/25)

### Typed adapter contract for ticket-sync: dispatcher owns invariants, generated adapters, fake for CI
`01KXV0NQPPPK2K948CK20QJSS1` · status: done
- references: [github#23](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/23)
- contains: canonical.py + capabilities/adapter-io schemas + fake adapter + contract tests
- contains: spec v1.6: §8.1 GitHub-UI merge caveat + §9 typed-contract reconciliation; user-guide recovery section
- contains: sync_dispatch.py: dispatcher owns §4 invariants; worklog sync/adapter-check wiring (last stub falls); dispatch tests
- contains: adapters/github worked example over gh + ticket-sync skill delegates invariants to dispatcher + CI wiring
- contains: v0.6.0 + dogfood: adapter check green against fake and github example
- produced-by: [[Plan-typed-adapter-contract]]

### Fix: plugin release-skill copy missing version frontmatter (silent str.replace miss broke version-sync test)
`01KXTZ8134TGKGC1YC2PXYRV29` · status: done
- belongs-to: release skill: cutting a release is a wiki-ticket capability

### Cut v0.5.0: stamp CHANGELOG, snapshot roadmap, tag, GitHub release, publish + sync
`01KXTZ5TEQV2J99CHPQNHJ1NA1` · status: done
- belongs-to: release skill: cutting a release is a wiki-ticket capability

### release skill: cutting a release is a wiki-ticket capability
`01KXTZ5TAPZBC06AG50KDJKEYF` · status: done
- contains: Cut v0.5.0: stamp CHANGELOG, snapshot roadmap, tag, GitHub release, publish + sync
- contains: Fix: plugin release-skill copy missing version frontmatter (silent str.replace miss broke version-sync test)

### Timecard status kind — narrative only per Rick: a sentence or two per day (spec §17 Q4 closed)
`01KXT9W0Y40SDTZBB93XY5YXNT` · status: done
- references: [github#17](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/17)

### Spec cleanup: purge remaining adapter references (§4.2 config keys, §5.3, §13.3, §15.5, §15.10)
`01KXT9B43GA5B8AAT26W8A1VPJ` · status: done
- references: [github#16](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/16)

### Push-only sync: close the linked ticket when a local item closes (skill scope gap)
`01KXT8JG3RNE2YZVCYEBXW9EX6` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- references: [github#14](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/14)
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### Version 0.3.0 + CHANGELOG
`01KXT88N4W1E78NY17DW65PJPX` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### Rewrite /worklog:init command: detect systems, yes/no confirm or multi-select pick-and-mix, write config
`01KXT88N0Z4EHR2HKMHGAM0WB3` · status: done
- belongs-to: /worklog:init detects ticket/PR/wiki systems from repo; confirm yes/no, else multi-select pick-and-mix per area
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### Pull + echo suppression + conflicts (spec 10.3-10.6), after living with push-only
`01KXT88MWVW63PA5698TFNYZ5E` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- references: [github#13](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/13)
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### Dogfood: push open items to GitHub Issues; roadmap shows issue links
`01KXT88MRST1ZZSBFMFCXYEDA1` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- references: [github#12](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/12)
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### Config: ticketing block -> github, project SpillwaveSolutions/wiki_ticket_sdd
`01KXT88MMR65W3CX1C37ECEEXG` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### ticket-sync skill (push-only): ULID idempotency marker, sync-state hash skip; gh for GitHub, others vague
`01KXT88MGRJB0ARA9CN7QX29GY` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### worklog link subcommand: record external identity after successful push (spec 5.3)
`01KXT88MCBB82VT84JT0PB53PG` · status: done
- belongs-to: Ticket sync — skill-based, GitHub Issues first
- produced-by: [[Plan-ticket-sync-and-init-detection]]

### worklog wiki-add <file>: register a file in .work/published.json for wiki publishing
`01KXSQJ3Z40QHSXEN6B4Y238AZ` · status: done
- belongs-to: /worklog:init detects ticket/PR/wiki systems from repo; confirm yes/no, else multi-select pick-and-mix per area

### wiki-publish always includes plans and roadmaps by default
`01KXSQJ3SGWWEHDNK83CDNPT4S` · status: done
- belongs-to: /worklog:init detects ticket/PR/wiki systems from repo; confirm yes/no, else multi-select pick-and-mix per area

### /worklog:init detects ticket/PR/wiki systems from repo; confirm yes/no, else multi-select pick-and-mix per area
`01KXSQJ3K19QWBDX482FRT7ETR` · status: done
- contains: wiki-publish always includes plans and roadmaps by default
- contains: worklog wiki-add <file>: register a file in .work/published.json for wiki publishing
- contains: Rewrite /worklog:init command: detect systems, yes/no confirm or multi-select pick-and-mix, write config

### Background plan-publish: on plan-capture, subagent syncs tickets and publishes plan to wiki, non-blocking
`01KXSQ4JH8SCHQ94DYQ7YJ872P` · status: done
- references: [github#11](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/11)

### Multi-tracker: sync one worklog to two systems at once (external as array)
`01KXSP277AE68GPTJHC1QJV1NX` · status: done
- references: [github#10](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/10)

### 01KXSP277AE68GPTHC1QJV1NX
`01KXSP277AE68GPTHC1QJV1NX` · status: cancelled
- references: [github#34](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/34)

### Harness ports — OpenCode and Codex (Claude plugin format is canonical)
`01KXSP273B1649RGJ841PVSCF3` · status: done
- references: [github#9](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/9)

### Status reports (daily/weekly) + plan-next (spec §13.3)
`01KXSP26Z674RTTB6D8GQCM2A8` · status: done
- references: [github#8](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/8)

### Compaction + nightly CI job (spec §7)
`01KXSP26V19JX6VTH0EYGDV2Z0` · status: done
- references: [github#7](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/7)

### Wiki publish breadth — Confluence, ADO, GitLab via skills
`01KXSP26PS6A0WDHQ65Y4B1X94` · status: done
- references: [github#6](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/6)

### Spec v1.4 — revise §9 adapter contract to skill-based edges
`01KXSP26JP91E4508YST2WXPTD` · status: done
- references: [github#5](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/5)

### Ticket sync — skill-based, GitHub Issues first
`01KXSP26ENPKCT4APD4YE93MMV` · status: done
- references: [github#4](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/4)
- contains: worklog link subcommand: record external identity after successful push (spec 5.3)
- contains: ticket-sync skill (push-only): ULID idempotency marker, sync-state hash skip; gh for GitHub, others vague
- contains: Config: ticketing block -> github, project SpillwaveSolutions/wiki_ticket_sdd
- contains: Dogfood: push open items to GitHub Issues; roadmap shows issue links
- contains: Pull + echo suppression + conflicts (spec 10.3-10.6), after living with push-only
- contains: Version 0.3.0 + CHANGELOG
- contains: Push-only sync: close the linked ticket when a local item closes (skill scope gap)

### Bump version 0.2.0 (plugin.json, worklog VERSION, skills frontmatter incl. new skill) + CHANGELOG entry
`01KXSNNSWKTJX2QWW4PYFDEZHS` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Packaging guard in tests/test_plugin.py — plugin/ contains no docs/user_guide content; canon list still passes
`01KXSNNSWKPDG9Q4404RPTWZY9` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Render roadmap, snapshot as docs/roadmap/<date>_v0.2-roadmap.md
`01KXSNNSWKC64M1XX0Y7WVT67Z` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Plugin installer/uninstaller at repo root — install-plugin.sh (claude plugin marketplace add + install, graceful message if claude CLI absent), uninstall-plugin.sh (reverse)
`01KXSNNSWK2PPBHVJ21MBT65ER` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Publish wiki: Home, User-Guide, CLI-Reference, Plugin-Guide, Roadmap (current), dated snapshot page; record in .work/published.json; add .work/wiki-checkout/ to .gitignore
`01KXSNNSWK0HC96WQ3HV98DHT8` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Seed roadmap: future epics via worklog add (ticket-sync skill-based w/ GitHub Issues first P1; spec v1.4 skill-based edges P2; wiki breadth Confluence/ADO/GitLab P2; compaction+nightly CI P2; status reports + plan-next P2; OpenCode/Codex ports P2; multi-tracker simultaneous P3)
`01KXSNNSWJZMQQH7H68XVB654Y` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### SessionStart hook — doctor-lite on session open: verify CLAUDE.md carries the worklog policy block (marker or heading), core.hooksPath=hooks, and installed: version vs plugin version; emit additionalContext naming what's missing and pointing at /worklog:init or /worklog:doctor; silent when repo has no bin/worklog
`01KXSNNSWJWK58BS457Y2NG3JA` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Stop hook — if the working tree has non-.work changes but .work/todo.jsonl is unchanged vs HEAD, block once with "record the work items or explain" (honor stop_hook_active from stdin JSON to prevent loops)
`01KXSNNSWJVJW87EPCZXE6QDCA` · status: done
- belongs-to: Enforcement hooks for the dogfood policy (plugin/hooks + repo mirror, silent outside worklog repos)
- produced-by: [[Plan-docs-wiki-dogfood]]

### Docs, wiki publishing & dogfood discipline
`01KXSNNSWJV2H5QS5CSTYASS6M` · status: done
- contains: Rewrite README.md — what/why: WikiTicket SDD ("wicked ticket"), fishbowled AI development, spec-driven (plans are the spec, tickets are the WIP), multi-team, system-agnostic edges (GitHub/GitLab/ADO/Jira/Confluence — they pick), epics/stories/tasks/bugs/subtasks, event-log history, generated roadmap/status. Keep quick-start + plugin sections, tightened.
- contains: Comprehensive user guide under docs/user_guide/ (excluded from plugin by construction; add packaging test)
- contains: worklog roadmap-snapshot [--name] subcommand — copy docs/roadmap.md to docs/roadmap/<YYYY-MM-DD>_<name>.md, frozen (refuse overwrite), + tests; re-copy worklog to plugin/scripts (canon sync)
- contains: Enforcement hooks for the dogfood policy (plugin/hooks + repo mirror, silent outside worklog repos)
- contains: wiki-publish skill (repo + plugin canonical copy) — system-vague: read .work/config.yml wiki block, publish named files using available tooling for that system (gh/git for GitHub wiki, MCP/CLI for Confluence/ADO/GitLab), research missing tooling, maintain .work/published.json ledger {key: {url, rev, source_hash}}, skip unchanged hashes, surface one-time init steps (e.g. GitHub wiki first page) to the human
- contains: Dogfood policy in CLAUDE.md — every request is broken into worklog items via work-track BEFORE work starts; mirror line in work-track skill
- contains: SessionStart hook — doctor-lite on session open: verify CLAUDE.md carries the worklog policy block (marker or heading), core.hooksPath=hooks, and installed: version vs plugin version; emit additionalContext naming what's missing and pointing at /worklog:init or /worklog:doctor; silent when repo has no bin/worklog
- contains: Seed roadmap: future epics via worklog add (ticket-sync skill-based w/ GitHub Issues first P1; spec v1.4 skill-based edges P2; wiki breadth Confluence/ADO/GitLab P2; compaction+nightly CI P2; status reports + plan-next P2; OpenCode/Codex ports P2; multi-tracker simultaneous P3)
- contains: Publish wiki: Home, User-Guide, CLI-Reference, Plugin-Guide, Roadmap (current), dated snapshot page; record in .work/published.json; add .work/wiki-checkout/ to .gitignore
- contains: Plugin installer/uninstaller at repo root — install-plugin.sh (claude plugin marketplace add + install, graceful message if claude CLI absent), uninstall-plugin.sh (reverse)
- contains: Render roadmap, snapshot as docs/roadmap/<date>_v0.2-roadmap.md
- contains: Packaging guard in tests/test_plugin.py — plugin/ contains no docs/user_guide content; canon list still passes
- contains: Bump version 0.2.0 (plugin.json, worklog VERSION, skills frontmatter incl. new skill) + CHANGELOG entry
- produced-by: [[Plan-docs-wiki-dogfood]]

### Write docs/user_guide/cli-reference.md — every worklog subcommand with examples, hooks, invariants
`01KXSNNSWJQ91JPN4QRVMJQ296` · status: done
- belongs-to: Comprehensive user guide under docs/user_guide/ (excluded from plugin by construction; add packaging test)
- produced-by: [[Plan-docs-wiki-dogfood]]

### Dogfood policy in CLAUDE.md — every request is broken into worklog items via work-track BEFORE work starts; mirror line in work-track skill
`01KXSNNSWJN9C584RF3NNJK0W9` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### wiki-publish skill (repo + plugin canonical copy) — system-vague: read .work/config.yml wiki block, publish named files using available tooling for that system (gh/git for GitHub wiki, MCP/CLI for Confluence/ADO/GitLab), research missing tooling, maintain .work/published.json ledger {key: {url, rev, source_hash}}, skip unchanged hashes, surface one-time init steps (e.g. GitHub wiki first page) to the human
`01KXSNNSWJMS2914A0JJYX3KEZ` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Enforcement hooks for the dogfood policy (plugin/hooks + repo mirror, silent outside worklog repos)
`01KXSNNSWJKRR3BF33CBK3E4Q7` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- contains: UserPromptSubmit hook — inject a one-line reminder: requests that produce work get worklog items first (work-track), keep statuses moving
- contains: Stop hook — if the working tree has non-.work changes but .work/todo.jsonl is unchanged vs HEAD, block once with "record the work items or explain" (honor stop_hook_active from stdin JSON to prevent loops)
- produced-by: [[Plan-docs-wiki-dogfood]]

### worklog roadmap-snapshot [--name] subcommand — copy docs/roadmap.md to docs/roadmap/<YYYY-MM-DD>_<name>.md, frozen (refuse overwrite), + tests; re-copy worklog to plugin/scripts (canon sync)
`01KXSNNSWJEP1V1JMSXH2MQWYV` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### Comprehensive user guide under docs/user_guide/ (excluded from plugin by construction; add packaging test)
`01KXSNNSWJDK16TMR50CNR3T3V` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- contains: Write docs/user_guide/plugin-guide.md — plugin vs repo install levels, /worklog:* commands, skills, version/doctor, harness notes (Claude Code + Grok build now; OpenCode/Codex ports on roadmap)
- contains: Write docs/user_guide/user-guide.md — concepts (event log, fold, visible WIP), core workflows (plan→capture→work→close→sync, unplanned work, PR flow incl. roadmap merge recovery)
- contains: Write docs/user_guide/cli-reference.md — every worklog subcommand with examples, hooks, invariants
- produced-by: [[Plan-docs-wiki-dogfood]]

### Write docs/user_guide/user-guide.md — concepts (event log, fold, visible WIP), core workflows (plan→capture→work→close→sync, unplanned work, PR flow incl. roadmap merge recovery)
`01KXSNNSWJ8RHP53Z2VQJH4D9J` · status: done
- belongs-to: Comprehensive user guide under docs/user_guide/ (excluded from plugin by construction; add packaging test)
- produced-by: [[Plan-docs-wiki-dogfood]]

### Write docs/user_guide/plugin-guide.md — plugin vs repo install levels, /worklog:* commands, skills, version/doctor, harness notes (Claude Code + Grok build now; OpenCode/Codex ports on roadmap)
`01KXSNNSWJ72MM7XHEJBHM6A1Y` · status: done
- belongs-to: Comprehensive user guide under docs/user_guide/ (excluded from plugin by construction; add packaging test)
- produced-by: [[Plan-docs-wiki-dogfood]]

### Rewrite README.md — what/why: WikiTicket SDD ("wicked ticket"), fishbowled AI development, spec-driven (plans are the spec, tickets are the WIP), multi-team, system-agnostic edges (GitHub/GitLab/ADO/Jira/Confluence — they pick), epics/stories/tasks/bugs/subtasks, event-log history, generated roadmap/status. Keep quick-start + plugin sections, tightened.
`01KXSNNSWJ3QKFCRBB3A12H5GT` · status: done
- belongs-to: Docs, wiki publishing & dogfood discipline
- produced-by: [[Plan-docs-wiki-dogfood]]

### UserPromptSubmit hook — inject a one-line reminder: requests that produce work get worklog items first (work-track), keep statuses moving
`01KXSNNSWJ0P23QC3SYXRQ01WA` · status: done
- belongs-to: Enforcement hooks for the dogfood policy (plugin/hooks + repo mirror, silent outside worklog repos)
- produced-by: [[Plan-docs-wiki-dogfood]]

### /worklog:init command — scaffold bin, hooks, .work, .gitattributes, CI into the current repo
`01KXSFEWNDZ55K8AQJBCN9MRD6` · status: done
- belongs-to: Worklog Claude plugin
- contains: Record installed plugin version in .work/config.yml
- produced-by: [[Plan-claude-plugin]]

### Scaffold plugin/ with .claude-plugin/plugin.json manifest v0.1.0
`01KXSFEWNDT1B5D0PRK16NX14T` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### Record installed plugin version in .work/config.yml
`01KXSFEWNDR0ZDTHHGQVN3PG9Z` · status: done
- belongs-to: /worklog:init command — scaffold bin, hooks, .work, .gitattributes, CI into the current repo
- produced-by: [[Plan-claude-plugin]]

### /worklog:uninstall command — remove scaffolding, always preserve .work data and docs
`01KXSFEWNDM44B8A8RV30PF6X1` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### bin/worklog --version + plugin CHANGELOG.md
`01KXSFEWNDBM4RHBFMNYJWR9CE` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### Plugin hooks.json ExitPlanMode hook with uninitialized-repo guard
`01KXSFEWND595MAFB1GMB9KECF` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### Integration test: init, track, uninstall in a sandbox repo
`01KXSFEWND4TYQ2V26KRPFHW9M` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### Marketplace manifest + README install docs
`01KXSFEWND3DGDF12DSWJEKVDF` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### /worklog:doctor — version skew report + invariant checks
`01KXSFEWND2PG3PQW8GMZ9B319` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### Move the three skills into plugin/skills, canonical copies
`01KXSFEWND18ATDAPCWJXKV8C1` · status: done
- belongs-to: Worklog Claude plugin
- produced-by: [[Plan-claude-plugin]]

### Worklog Claude plugin
`01KXSFEWNCJMXPZDNT7RNYTG8X` · status: done
- contains: Move the three skills into plugin/skills, canonical copies
- contains: /worklog:doctor — version skew report + invariant checks
- contains: Marketplace manifest + README install docs
- contains: Integration test: init, track, uninstall in a sandbox repo
- contains: Plugin hooks.json ExitPlanMode hook with uninitialized-repo guard
- contains: bin/worklog --version + plugin CHANGELOG.md
- contains: /worklog:uninstall command — remove scaffolding, always preserve .work data and docs
- contains: Scaffold plugin/ with .claude-plugin/plugin.json manifest v0.1.0
- contains: /worklog:init command — scaffold bin, hooks, .work, .gitattributes, CI into the current repo
- produced-by: [[Plan-claude-plugin]]

### Smoke test item
`01KXS7W15SHYS5PSGGWHYMFKYM` · status: cancelled

