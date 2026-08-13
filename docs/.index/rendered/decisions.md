# Decisions

_Why things are the way they are: ADRs (rules adopted) and plans (designs executed). Generated; do not edit._

## Architecture Decision Records

| ADR | Status | Date | Supersedes |
|---|---|---|---|
| [[ADR-0001-event-log-fold-union-merge]] Append-only event log with fold-derived state and git union merge | accepted | 2026-07-19 | — |
| [[ADR-0002-skill-based-edges-typed-contract]] Edge integration as skills, hardened by a typed adapter contract | accepted | 2026-07-19 | — |
| [[ADR-0003-green-gates-merge]] PRs merge only when every quality gate is green | accepted | 2026-07-19 | — |
| [[ADR-0004-clearing-a-dead-ticket-link-stays-a-huma]] Clearing a dead ticket link stays a human action | accepted | 2026-07-31 | — |
| [[ADR-0005-no-custom-merge-driver-for-the-event-log]] No custom merge driver for the event log | accepted | 2026-07-31 | — |
| [[ADR-0006-resurrected-events-are-not-always-cosmet]] Resurrected events are not always cosmetic | accepted | 2026-08-01 | — |
| [[ADR-0007-the-compaction-watermark-is-per-item]] The compaction watermark is per item | accepted | 2026-08-01 | — |
| [[ADR-0008-document-provenance-depends-on-merge-com]] Document provenance depends on merge commits | accepted | 2026-08-03 | — |
| [[ADR-0009-a-frozen-document-s-fabricated-citations]] A frozen document's fabricated citations are reported, never gated | accepted | 2026-08-13 | — |

## Plans

| Plan | Lifecycle | Truth | Date |
|---|---|---|---|
| [[Plan-doc-provenance-and-verification]] Git provenance on generated docs, and the verifier it enables | completed | current | 2026-08-03 |
| [[Plan-trace-check-scope]] Scope the traceability gate to the claim it actually makes | completed | current | 2026-08-02 |
| [[Plan-plan-banner-state]] A plan's banner should say which plan it is | completed | current | 2026-08-02 |
| [[Plan-configurable-item-fields]] Configurable optional fields on the work item | completed | current | 2026-08-01 |
| [[Plan-close-p1-epics-and-settle-merge-and-gone-questions]] Close both P1 epics, settle the merge-strategy and GONE questions | completed | current | 2026-07-30 |
| [[Plan-one-owner-per-external-key]] One local owner per remote ticket (#226) | completed | current | 2026-07-28 |
| [[Plan-post-v017-drift-and-prefix-resolution]] Clear post-v0.17.0 drift and fix the prefix-ULID log corruption | completed | current | 2026-07-27 |
| [[Plan-declare-graph-engineering]] Declare wiki_ticket_sdd as a Graph Engineering system | completed | current | 2026-07-26 |
| [[Plan-wiki-driven-integration-guides]] Wiki-Driven Integration Guides for SDD tools and ticket/wiki systems | completed | current | 2026-07-25 |
| [[Plan-branch-discipline-hooks]] Branch-discipline hooks: never commit on main, always reference work | completed | current | 2026-07-25 |
| [[Plan-artifact-pages]] Extend IA to tickets, PRs, and releases (artifact pages) | completed | current | 2026-07-24 |
| [[Plan-wiki-ticket-ui-ia]] WikiTicket UI — IA-aware dashboard (supersedes wiki-ticket-ui) | completed | current | 2026-07-22 |
| [[Plan-wiki-information-architecture]] Wiki information architecture | superseded → superseded by [[Plan-ia-content-model]] | superseded | 2026-07-22 |
| [[Plan-ia-content-model]] IA & content model (supersedes wiki-information-architecture) | completed | current | 2026-07-22 |
| [[Plan-grok-viz-background-execution]] Grok viz — background-subagent execution rule (amendment record) | completed | current | 2026-07-22 |
| [[Plan-wiki-ticket-ui]] WikiTicket UI — project status dashboard (wiki_ticket_sdd_ui) | superseded → superseded by [[Plan-wiki-ticket-ui-ia]] | superseded | 2026-07-21 |
| [[Plan-grok-compat-and-mermaid-viz]] Grok Build compatibility statement + Mermaid roadmap visualization | planned — not yet scheduled | current | 2026-07-19 |
| [[Plan-design-docs-release-sync]] Design docs + code walkthroughs with release-time doc sync | completed | current | 2026-07-19 |
| [[Plan-adr]] Architecture Decision Records — schema-validated, wiki-synced | completed | current | 2026-07-19 |
| [[Plan-work-taxonomy]] Work Taxonomy + Flag-Gated Classifier | planned — not yet scheduled; implementation tasks attach to the epic when work starts | current | 2026-07-18 |
| [[Plan-typed-adapter-contract]] Typed Adapter Contract for ticket-sync | planned — not yet scheduled; implementation tasks attach to the epic when work starts | current | 2026-07-18 |
| [[Plan-ticket-sync-and-init-detection]] Ticket sync (push-only, GitHub Issues) + /worklog:init system detection | planned | current | 2026-07-18 |
| [[Plan-docs-wiki-dogfood]] Docs, wiki publishing & dogfood discipline | completed | current | 2026-07-18 |
| [[Plan-claude-plugin]] Worklog Claude plugin | completed | current | 2026-07-18 |
| [[Plan-2026-07-17_worklog-core_plan]] Worklog Core (Spec §18 Steps 3–4 + CI) Implementation Plan | completed | current | 2026-07-17 |
