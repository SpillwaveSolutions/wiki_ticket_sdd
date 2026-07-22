---
date: 2026-07-22
slug: wiki-information-architecture
title: Wiki information architecture
epic: 01KY5F6QA220S0K7RRK2Q80XR8
items: [01KY5F6QA3YAAWKF4PC5VPM90A, 01KY5F6QA3G8VWG73VVD3AWDGE, 01KY5F6QA35SKWEN7YGMVR16XS, 01KY5F6QA3Y05F7S3ZMWEQ5BB2, 01KY5F6QA32GH5RWA1BH42EVSQ, 01KY5F6QA32MWBKTYPVPTBPKQ7, 01KY5F6QA3AV0B9NGBBKTMJS7J, 01KY5F6QA4YVHE4ESMT3E2KYK9, 01KY5F6QA43HN4CAMFBBD6MKSA, 01KY5F6QA4WWSSZVKE0YJ7YHXZ]
---

# Wiki information architecture

## Context

The wiki has grown haphazard. The GitHub Wiki namespace is flat, `docs/wiki-home.md` is a
hand-curated link list that must be edited every time a page is added, there is no sidebar,
and snapshot-heavy listings put current truth (live roadmap, current design doc) side by side
with frozen history (dated snapshots, old status reports) with nothing telling the reader
which is which. Finding "what is the current architecture?" or "why did we do X?" requires
already knowing the naming conventions.

Two plans were compared: an earlier low-risk navigation plan (Sidebar, Home redesign, manual
indexes, current-vs-history separation) and a more ambitious question-driven architecture
(reader-question hierarchy, formal content model with frontmatter, generated navigation and
indexes, bidirectional traceability). The synthesis adopted here: the question-driven
architecture is the north star; the practical navigation tactics are Phase 0, executed first
so the wiki stops feeling haphazard while the heavier model is built.

**Status: plan only for now — do not implement.** This capture files the epic and items;
the Phase 0 build happens when Rick says go.

## Guiding principle

- **Repository** = canonical evidence (specs, plans, ADRs, designs, status, code).
- **Wiki** = curated, audience-oriented knowledge view — a *generated view over a knowledge
  graph*, not a raw mirror of `docs/`.
- **Tickets** (GitHub / Jira / ADO / ...) = execution and prioritization.
- **Plugins + CI** = integrity: generation, validation, publication.

All ongoing maintenance of the IA itself is performed by AI agents (Claude / Grok) through
skills, slash commands, and the `worklog` CLI. Everything stays harness-agnostic.

## Target information architecture (question-driven)

Organize the wiki around the questions readers actually ask, not around how the tooling
produces files:

```
WikiTicket SDD
│
├── 1. Start Here
│   ├── Project Overview
│   ├── How WikiTicket SDD Works
│   ├── Terminology (incl. 4-axis taxonomy)
│   └── Getting Started
│
├── 2. Product and Requirements
│   ├── Product Vision
│   ├── Capabilities
│   ├── Requirements
│   ├── Constraints and Non-Goals
│   └── Milestones
│
├── 3. Current Work
│   ├── Roadmap (live)
│   ├── Current Milestone
│   ├── Active Epics
│   ├── Needs Classification
│   └── Recently Discovered Work
│
├── 4. Specifications and Plans
│   ├── Active Specifications
│   ├── Approved Plans
│   ├── Superseded Plans
│   └── Specification Index
│
├── 5. Architecture and Decisions
│   ├── Current Architecture
│   ├── Architecture Decision Records
│   ├── Data Model
│   ├── Synchronization Model
│   ├── Security Model
│   └── Integration Architecture
│
├── 6. Implementation
│   ├── Codebase Map
│   ├── Module Walkthroughs (current + snapshots)
│   ├── CLI Reference
│   ├── Adapter Development
│   └── Testing Strategy
│
├── 7. Operations
│   ├── Installation
│   ├── Configuration
│   ├── Ticket Synchronization
│   ├── Wiki Publishing
│   ├── Troubleshooting
│   └── Recovery Procedures
│
├── 8. Releases and History
│   ├── Release Index
│   ├── Release Notes
│   ├── Roadmap Snapshots
│   ├── Design Snapshots
│   └── Completed Milestones
│
└── 9. Status and Reporting
    ├── Current Status
    ├── Weekly Reports
    ├── Daily Reports
    └── Timecards
```

**Current Truth** pages (mutable / republished on change) live in sections 1–7 plus the live
Roadmap. **Historical Evidence** pages (frozen, publish-once) live primarily in sections 8–9
plus the frozen plans, dated snapshots, and status reports. Page banners make the distinction
explicit on every page.

The GitHub Wiki namespace stays flat; the hierarchy is *logical*, realized through the
Sidebar, Home, and index pages — and rendered per-platform when other wikis (ADO, Confluence)
are in play.

## Content model

Every published document declares a type:

| Type              | Purpose                              | Mutable?          | Typical owner      |
|-------------------|--------------------------------------|-------------------|--------------------|
| Overview          | Project & boundaries                 | Yes               | Product / Arch     |
| Requirement       | What the system must do              | Versioned         | Product            |
| Specification     | Expected behavior                    | Versioned         | Product / Eng      |
| Plan              | How a change will be implemented     | Frozen            | Implementer        |
| ADR               | Architectural decision               | Status only       | Architecture       |
| Design            | Current system description           | Yes               | Engineering        |
| Design Snapshot   | Release-time architecture            | Frozen            | Release automation |
| Runbook           | Operational procedures               | Yes               | Operations         |
| User Guide        | How to use the system                | Yes               | Product / Eng      |
| Roadmap           | Current planned work                 | Generated         | Worklog            |
| Roadmap Snapshot  | Milestone view                       | Frozen            | Release automation |
| Status Report     | Activity in a period                 | Frozen            | Worklog            |
| Release Record    | What shipped + evidence              | Frozen            | Release automation |
| Code Walkthrough  | Implementation explanation           | Current + snaps   | Engineering        |

Required frontmatter (target shape; formalizes the per-type conventions already noted in the
wiki-ticket-ui plan's data contract):

```yaml
---
id: plan-2026-07-18-typed-adapter-contract
title: Typed Adapter Contract
document_type: plan
status: accepted
project: wiki-ticket-sdd
milestone: v0.13.0
owners: [rick]
created: 2026-07-18
last_reviewed: 2026-07-18
supersedes: null
superseded_by: null
related_items: [WTS-142, WTS-143]
related_adrs: [ADR-0007]
source_of_truth: repository
wiki_key: specs/typed-adapter-contract   # stable identity
tags: [synchronization, adapters, architecture]
---
```

The stable `wiki_key` becomes the canonical identity in the publish ledger
(`.work/published.json` already keys pages this way — `plan/<slug>`, `adr/NNNN-slug`,
`roadmap`, ...). Titles can evolve without breaking links.

## Phased roadmap

**Phase 0 — immediate usability (days).** Remove the haphazard feeling now, pure Markdown,
no new machinery: a `_Sidebar.md` mapped to the nine target sections; Home redesigned as a
question-oriented orientation hub with clear Current vs Historical zones; four practical
index pages (Plans-Index, ADR-Index, Status-Index, Release-History); short banners marking
current vs frozen; a Wiki-Structure page documenting the interim conventions.

**Phase 1 — define the model.** `docs/information-architecture.md` and
`docs/content-model.md`; document templates (plan, ADR, status, design) carrying the required
frontmatter; `docs/navigation.yml` (logical hierarchy) and `docs/publishing.yml` (formal
publish manifest, superseding the implicit publish set in the wiki-publish skill); a full
content inventory classifying every existing doc and wiki page into the model.

**Phase 2 — normalize metadata and generate indexes.** New documents are born with correct
frontmatter (extend plan-capture, design-docs, status-report, release, adr skills); high-value
existing docs normalized first (ADRs, recent plans, current design); indexes generated from
frontmatter — Specification Index, Decision Index, Milestone Index, Release Index,
**Traceability Index**, Document Health; wiki-publish consumes the manifest + frontmatter +
`wiki_key`.

**Phase 3 — traceability and enforcement.** Bidirectional references (requirement ↔ spec ↔
plan ↔ work item ↔ PR/test ↔ release); new commands `worklog docs validate | index | health |
trace` and `worklog wiki render-navigation`; CI gates for metadata validity, frozen-document
integrity, missing high-priority traceability, stale indexes; migration to the full hierarchy
using stable `wiki_key`s with redirects / alias ledger entries.

**Phase 4 — continuous operation.** Every future plan, ADR, design, status report, and
release is born with correct frontmatter and relations; indexes and navigation stay generated;
agents maintain the knowledge graph as a natural part of SDD work.

Phases 2 and 3 are captured here as single coarse items; each gets exploded by a superseding
plan when its turn comes — the detail above is direction, not commitment.

## Skill implications

- Extend existing skills (`plan-capture`, `design-docs`, `status-report`, `release`,
  `wiki-publish`, `adr`) to emit frontmatter and `related_*` links.
- New skills / commands for inventory, frontmatter normalization, index generation,
  validation, and navigation rendering.
- Keep everything harness-agnostic (Claude Code plugin + AGENTS.md / PORTS.md); the `worklog`
  CLI remains the stable scriptable interface for humans and agents alike.

## Pragmatic notes

- The 9-section hierarchy is rich; start slightly flatter while content volume is low and
  expand as sections fill.
- The 4-axis work taxonomy (level / kind / milestone / planned-vs-discovered) must be
  prominent in Terminology and Current Work.
- Full metadata normalization is real work; prioritize new documents and high-value existing
  ones over bulk backfill.

## Execution when Rick says go (NOT now)

Phase 0 first, as one small PR: Sidebar, Home, four indexes, banners, conventions page —
publish via the existing wiki-publish skill. Then Phase 1 artifacts. Phases 2–3 wait for
their superseding plans.

## Immediate execution (this approval)

Run `worklog plan-capture` for this file, `roadmap-render`, commit, publish the plan page and
sync tickets in the background — then stop. No Sidebar, no Home redesign, no index pages, no
new skills yet.

## Tasks

- [ ] (P1) Phase 0: _Sidebar.md mapped to the 9 target sections
- [ ] (P1) Phase 0: redesign Home as question-oriented orientation hub with current-vs-history zones
- [ ] (P1) Phase 0: index pages — Plans-Index, ADR-Index, Status-Index, Release-History
- [ ] (P1) Phase 0: current-vs-historical banners + Wiki-Structure conventions page
- [ ] (P2) Phase 1: docs/information-architecture.md + docs/content-model.md
- [ ] (P2) Phase 1: document templates (plan, adr, status, design) with required frontmatter
- [ ] (P2) Phase 1: docs/navigation.yml + docs/publishing.yml publish manifest
- [ ] (P2) Phase 1: content inventory — classify every existing doc and wiki page into the model
- [ ] (P3) Phase 2 (coarse): frontmatter normalization + generated indexes incl. Traceability Index — explode via superseding plan
- [ ] (P3) Phase 3 (coarse): traceability graph, worklog docs validate/index/health/trace, CI gates — explode via superseding plan
