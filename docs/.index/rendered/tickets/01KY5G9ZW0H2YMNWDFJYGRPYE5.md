# IA & content model (supersedes wiki-information-architecture)

`01KY5G9ZW0H2YMNWDFJYGRPYE5` · epic/feature · **done**

Reorganize the project wiki so anyone — a new developer, a PM, an auditor — can find the right page and know whether it is current or historical.

## Children

- [[Ticket-01KY5G9ZW025TRGTHFAFSVEXSX]] Phase 0: worklog wiki-key + worklog ia-inventory (read-only) + migration record docs/migrations/0002-ia-content-model.md — Add two read-only commands: one prints the stable identity key for any doc, the other walks docs/ and produces a machine-readable inventory of every document (type, state, relationships). (done)
- [[Ticket-01KY5G9ZW0EYQ5T83RP46Z7952]] Phase 1: worklog ia-normalize — sidecars for frozen docs, in-place for sanctioned-live; backfill wiki_key (ledger-seeded) + truth_state — Backfill every doc with its stable identity key and a current-vs-historical state. (done)
- [[Ticket-01KY5G9ZW0MQD9335S641DC7ZG]] Phase 3: generated indexes — Decisions, Releases, Status Archive; wire ia-index into release + plan-capture skills — Generate index pages so common questions have one landing spot: all decisions (ADRs and plans with supersede chains), all releases with what shipped in each, and an archive of status reports. (done)
- [[Ticket-01KY5G9ZW0PBXTBKRJJ70QHR5P]] Phase 0: schema/doc.schema.json unified frontmatter schema + stdlib validator (adr.schema.json pattern) — Define one frontmatter schema that every doc type validates against, with per-type required fields, plus a small validator. (done)
- [[Ticket-01KY5G9ZW0PEZK9PTM3NG0PYX7]] Phase 2: extend wiki-publish to consume publish-manifest.json; replace hand-maintained wiki-home.md with generated Home — The wiki publisher reads a generated manifest that says exactly which pages belong on the wiki and how each renders, replacing the implicit publish list. (done)
- [[Ticket-01KY5G9ZW0PNKDDEK5TM8GS2J6]] Phase 1: CI gates — wiki_key present/unique, schema-valid frontmatter (warn one cycle, then hard) — CI checks that every doc has an identity key, no two docs share one, and frontmatter matches the schema. (done)
- [[Ticket-01KY5G9ZW0RABXWHEMEP1FAV2G]] Phase 5: promote gates to hard fail; platform render adapters (GitLab/ADO/Confluence); /worklog:find + glossary — Turn the remaining warnings into hard CI failures, add sidebar/navigation rendering for GitLab, Azure DevOps, and Confluence wikis, and add a search command over the doc inventory. (done)
- [[Ticket-01KY5G9ZW0X5F3K7KHP1SXFM3Q]] Phase 2: worklog ia-render + ia-manifest — generated Home, Sidebar, publish-time truth banners in docs/.index/rendered/ — Generate the reader-facing wiki pages: a question-driven Home, a sidebar grouped into Current Truth vs History, and a banner on every page saying whether it is current, a snapshot, or superseded. (done)
- [[Ticket-01KY5G9ZW0Z6JFMVTAFC54RM36]] Phase 4: ia-graph typed-edge taxonomy + link-pr + trace-check + Traceability Index; propose-only edge seeding via suggestions.jsonl — Build the traceability graph linking plans to work items to tickets, code changes, tests, and releases — browsable as a wiki page and validated by a checker that reports released work missing its evidence links. (done)

Progress: 9/9 done

## Related tickets

- [github #93](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/93)
