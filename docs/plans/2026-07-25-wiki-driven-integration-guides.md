---
date: 2026-07-25
slug: wiki-driven-integration-guides
title: Wiki-Driven Integration Guides for SDD tools and ticket/wiki systems
epic: 01KYDP0BQGW4XAAGX68526C9ES
items: [01KYDP0BQG59M8QGCQY72SC0G1, 01KYDP0BQGC8N7K1TE571K74JF, 01KYDP0BQHXGEBEY40SC1Q4ST3, 01KYDP0BQHAE38H6VPDNVXV8JA, 01KYDP0BQH6389PTNGKXHSN2KR, 01KYDP0BQHDBJ50D8HZHWN3G4H, 01KYDP0BQHW1A3235YSF16ZZAQ, 01KYDP0BQHANV652NZVV8N7VX5, 01KYDP0BQHPP0JZRK856QHN76S, 01KYDP0BQHZHYH9CKM3D0ZM803, 01KYDP0BQHRM2Q3C5727FAZ7RD, 01KYDP0BQHXZCGTTM5PAV262RM, 01KYDP0BQHV6MW1XX7H7JC1EN4, 01KYDP0BQHAMP5AC6AP7854N9H, 01KYDP0BQH33AMR5ETPDF4V1M6, 01KYDP0BQHZAPBZPSSY38J33ZZ]
---

# Wiki-Driven Integration Guides for wiki_ticket_sdd (SDD tools + ticket/wiki systems)

## Context

Three PRDs were submitted in this conversation, each revising the last. The final ask: let `wiki_ticket_sdd` point users at *living* integration guides — for four SDD tools (Superpowers, GSD, SpecKit, OpenSpec) and seven ticket/wiki systems (Jira, Confluence, GitHub, GitLab, Azure DevOps, AWS CodeCatalyst, Google Cloud DevOps) — without hard-coding any of that guidance into the shipped skill set. Content should live in this repo and its GitHub wiki, be fetched at runtime, and fall back to a local copy offline.

Research surfaced two things that reshape the plan from what the PRDs assumed:

1. **The PRDs' core premise is false.** They claim adapters "already" exist for Jira/Confluence/GitLab/ADO/CodeCatalyst. In reality only `adapters/github/adapter` is real code — everything else is an advisory enum value in `.work/config.yml` plus prose telling the agent to research the system at runtime (`ticket-sync/SKILL.md` already says this outright for ADO/Linear/CodeCatalyst/GCP). The user confirmed (via the honesty-framing question below): write these pages accordingly — no invented adapter/credential machinery.
2. **There's no "core skill" to attach a trigger rule to.** This repo ships 12 independent `SKILL.md` files; triggering is purely `description`-field matching. So "one shared trigger rule" means one new skill whose description lists the 11 names — not a change to some central prompt that doesn't exist.

The upshot is that this whole feature needs **zero new Python/`bin/` code**. `WebFetch` (already available to any Claude Code agent) covers "fetch a wiki page at runtime," and `worklog wiki-add` (already shipped, `bin/worklog`) covers "get an arbitrary file into the wiki-publish pipeline." The work is one new skill plus markdown content.

Decisions locked with the user before this plan was written:
- **Scope**: all 11 pages now, not phased.
- **Honesty framing**: for the 7 non-GitHub systems, pages state plainly there's no shipped adapter and give agent-researched CLI/MCP/REST guidance, matching the existing `ticket-sync` ADO-caveats tone.
- **Architecture**: one new skill (`integration-guide`) owns the trigger, lookup, and fallback logic. `ticket-sync` and `wiki-publish` are not edited.

## Design

### 1. New skill: `integration-guide`

Create, mirroring the existing 12-skill pattern:
- `.claude/skills/integration-guide/SKILL.md`
- `plugin/skills/integration-guide/SKILL.md` (identical body; check how other skills' plugin mirrors get their trailing `version:` line synced — e.g. as part of the `release` skill — and hook into that instead of hand-maintaining a second copy).

Frontmatter (trigger is the `description` field alone, per this repo's actual triggering model — no other mechanism exists):

```yaml
name: integration-guide
description: Look up how wiki_ticket_sdd integrates with a specific SDD tool or ticket/wiki system — Superpowers, GSD, SpecKit, OpenSpec, Jira, Confluence, GitHub, GitLab, Azure DevOps (ADO), AWS CodeCatalyst, or Google Cloud DevOps (GCP). Use when asked how to set up, configure, or use one of these, or when ticket-sync/wiki-publish need runtime guidance for a system with no shipped adapter.
```

Body procedure (numbered prose, same register as `ticket-sync`/`wiki-publish` — no invented tooling):

1. **Match the mentioned name to a canonical key** via a fixed alias table in the skill body (table below) — resolves without any network call.
2. **Resolve the wiki page and local fallback path** from the canonical key: wiki page title `Integration-<Name>` (exact PascalCase form below, matching the PRD's literal requirement), URL = `wiki.root_url` (read from `.work/config.yml`) + `/Integration-<Name>`; local file `docs/integrations/fallback-<key>.md`.
3. **Try `WebFetch` on the wiki URL first** — the wiki copy is the freshest (per `wiki-publish`, pages can be hand-edited in the web UI). On success, say "Referring to the official integration guide for `<System>`, published at `<url>`," then follow that page's **Recommended workflow** section exactly.
4. **On fetch failure, read the local fallback file** and say so explicitly ("wiki page unavailable — using the bundled local copy, which may lag the published page"). Same "follow Recommended workflow" instruction applies.
5. **Soft version-staleness check** (see below) — best-effort, never a hard block.
6. **Compose, don't reinvent** — one pointer paragraph: for Jira/Confluence, check for the global `jira`/`confluence` skills (and `design-doc-mermaid`/`plantuml` for diagrams) before doing anything raw. The authoritative, detailed version of this instruction lives in the Jira/Confluence fallback pages themselves (§2), not duplicated at length here.
7. **Maintenance note**: after editing a page under `docs/integrations/`, run `worklog wiki-add docs/integrations/fallback-<key>.md --key integrations/<key> --title "Integration-<Name>"` — `wiki-publish`'s existing hash-compare skip logic picks it up on the next publish run automatically. No new publish code, no "frozen vs live" flag needed (a registered file simply re-publishes whenever its hash changes).

Alias table (drives step 1 — literal wiki page names match the PRD's requirement exactly):

| Canonical key | Aliases | Wiki page | Local fallback file |
|---|---|---|---|
| `superpowers` | Superpowers | `Integration-Superpowers` | `fallback-superpowers.md` |
| `gsd` | GSD, Get Shit Done | `Integration-GSD` | `fallback-gsd.md` |
| `speckit` | SpecKit, Spec Kit | `Integration-SpecKit` | `fallback-speckit.md` |
| `openspec` | OpenSpec | `Integration-OpenSpec` | `fallback-openspec.md` |
| `jira` | Jira, Atlassian Jira | `Integration-Jira` | `fallback-jira.md` |
| `confluence` | Confluence, Atlassian Confluence | `Integration-Confluence` | `fallback-confluence.md` |
| `github` | GitHub, GitHub Issues | `Integration-GitHub` | `fallback-github.md` |
| `gitlab` | GitLab | `Integration-GitLab` | `fallback-gitlab.md` |
| `azuredevops` | Azure DevOps, ADO, Azure Boards | `Integration-AzureDevOps` | `fallback-azuredevops.md` |
| `awscodecatalyst` | AWS CodeCatalyst, CodeCatalyst | `Integration-AWSCodeCatalyst` | `fallback-awscodecatalyst.md` |
| `googleclouddevops` | Google Cloud DevOps, GCP, Google Cloud | `Integration-GoogleCloudDevOps` | `fallback-googleclouddevops.md` |

### 2. Content template — 10 sections, applied verbatim to all 11 pages

Fixed heading skeleton (per the final PRD's short-form headings): **When to use, One-command setup, Adapter configuration, Recommended workflow, Mapping events, Pulling changes, Rendering support, Example links, Gotchas & troubleshooting, Last updated.**

Keep the skeleton fixed across all 11 pages even where a section is thin (e.g. Google Cloud DevOps has almost nothing under "Adapter configuration" — write "N/A — no native tracker; see the GitHub/GitLab/Jira pages" rather than omitting the heading). The skill's own lookup procedure (step 3/4 above) depends on every page having the same section names.

Two placements are load-bearing and appear in exactly one page each — no duplication elsewhere:
- **Jira/Confluence mandatory skill-reuse paragraph** → lives under **Recommended workflow**, in `fallback-jira.md` and `fallback-confluence.md` only: instructs checking for the global `jira`/`confluence` skill (or an Atlassian MCP server) before any raw REST/CLI call — it already owns auth, pagination, and markup conversion.
- **Confluence diagram-to-image paragraph** → lives under **Rendering support**, in `fallback-confluence.md` only: Confluence storage format doesn't render Mermaid/PlantUML fences, so convert via the `design-doc-mermaid`/`plantuml` skills to PNG/SVG, attach as an image, then reference it.

For the 7 ticket/wiki systems, **Gotchas & troubleshooting** is where the honest "no adapter ships — here's how to research and drive it at runtime" framing goes, matching `ticket-sync/SKILL.md`'s existing ADO-caveats section in tone. For the 4 SDD tools (no wiring into this repo today, confirmed by grep), set expectations honestly: these read as compositional guidance between two independent skill-sets, not technical integration docs — don't dress them up as more wired-in than they are.

**Last updated** (section 10) is the only metadata — a single `Last updated: YYYY-MM-DD` line, visible identically on the raw file and the published wiki page. No YAML frontmatter block on these files: nothing in this repo parses generic `docs/` frontmatter (`ia_render.py`'s manifest builder only covers its own rendered pages plus a fixed plans/ADRs set) — adding one here would only exist to be stripped again by `wiki-publish`'s Gollum-strip rule. Skip it (nothing consumes it).

### 3. File layout and registration

```
docs/integrations/README.md                       (meta index, wiki page "Integrations")
docs/integrations/fallback-superpowers.md
docs/integrations/fallback-gsd.md
docs/integrations/fallback-speckit.md
docs/integrations/fallback-openspec.md
docs/integrations/fallback-jira.md
docs/integrations/fallback-confluence.md
docs/integrations/fallback-github.md
docs/integrations/fallback-gitlab.md
docs/integrations/fallback-azuredevops.md
docs/integrations/fallback-awscodecatalyst.md
docs/integrations/fallback-googleclouddevops.md
```

`docs/integrations/README.md` is a hand-maintained list of `[[Integration-<Name>]]` wiki links, one per system, one-sentence description each, same 11-row order as the alias table.

Register each file with the existing mechanism — no new publish code:
```
worklog wiki-add docs/integrations/fallback-jira.md --key integrations/jira --title "Integration-Jira"
...
worklog wiki-add docs/integrations/README.md --key integrations/index --title "Integrations"
```
This is the exact path `wiki-publish/SKILL.md` §4 already documents ("plus anything registered via `worklog wiki-add`"). After registering, a normal `wiki-publish` run pushes all 12 pages (11 + index) to the GitHub wiki via its existing github-wiki flow (clone `.wiki.git`, copy flat, commit, push) — nothing new to build there.

### 4. Version-staleness check — plain instruction, explicit limit

Phrase as best-effort, not a gate: if a page states a minimum tool version *and* the system has a real, probeable CLI (`gh --version`, `glab --version`, `az --version`, `aws --version`), run it and warn (don't block) if older. For the 4 SDD tools — they're Claude Code skills, not installed binaries — state plainly that no version check applies; don't fabricate one.

### Explicitly out of scope (don't build)

- Any new `bin/*.py` module, adapter, or fetch helper — `WebFetch` + `wiki-add` already cover this. (Also means the repo's 80%-coverage gate on `bin/*.py` doesn't apply to this change — nothing new lands there.)
- Any edit to `ticket-sync/SKILL.md` or `wiki-publish/SKILL.md` bodies.
- Any real adapter/credential code for Jira, Confluence, GitLab, ADO, CodeCatalyst, or GCP — these remain agent-researched-at-runtime by design, honestly documented as such.
- Wiki-vs-local-copy reconciliation tooling — independent editability is accepted drift, not a bug to solve now.

## Critical files

- `.claude/skills/integration-guide/SKILL.md` (new)
- `plugin/skills/integration-guide/SKILL.md` (new mirror)
- `docs/integrations/README.md` + 11 `fallback-*.md` files (new)
- `.claude/skills/wiki-publish/SKILL.md` (reference only — defines the `wiki-add`/publish contract this relies on)
- `.claude/skills/ticket-sync/SKILL.md` (reference only — source of the honest-runbook tone to match)
- `bin/worklog` (reference only — `cmd_wiki_add`, the exact registration command)
- `.work/config.yml` (reference only — `wiki.root_url` for the WebFetch URL)

## Verification

1. `worklog wiki-add` each of the 12 new files, then run the `wiki-publish` skill's flow and confirm all 12 pages appear in `.work/wiki-checkout/` and push cleanly to the GitHub wiki (check `.work/published.json` gained 12 new entries with matching `source_hash`).
2. Manually exercise the new skill end-to-end for one system with a live page (e.g. "integrate wiki_ticket_sdd with Jira") and confirm it fetches the wiki page, states the "Referring to..." line, and follows that page's Recommended workflow section.
3. Temporarily rename/hide the wiki page (or point at a bad URL) and re-run the same prompt — confirm it falls back to `docs/integrations/fallback-jira.md` and says so explicitly.
4. Spot-check the Confluence page includes the diagram-to-image paragraph under Rendering support, and the Jira/Confluence pages both include the skill-reuse paragraph under Recommended workflow — nowhere else.
5. Confirm `docs/integrations/README.md` (Integrations wiki page) links all 11 pages and matches the alias table's names exactly.

## Tasks

- [ ] (P1) Create the integration-guide skill
  Add a new Claude Code skill that recognizes when someone mentions one of 11
  supported tools/systems (Superpowers, GSD, SpecKit, OpenSpec, Jira,
  Confluence, GitHub, GitLab, Azure DevOps, AWS CodeCatalyst, Google Cloud
  DevOps) and looks up the right integration guide before giving instructions.
  Mirror the same file into the plugin package so both copies stay in sync.

- [ ] (P2) Write the 11 fallback integration pages
  Author one markdown guide per supported tool/system, each following the
  same 10-section outline so the skill can navigate them predictably. Pages
  for systems with no real adapter must say so plainly and explain how an
  agent should research and drive that system at runtime instead.
  - [ ] (P2) fallback-superpowers.md
    Guide covering when and how to combine this repo's spec-driven workflow
    with the Superpowers skill set.
  - [ ] (P2) fallback-gsd.md
    Guide covering when and how to combine this repo's spec-driven workflow
    with the GSD (Get Shit Done) skill set.
  - [ ] (P2) fallback-speckit.md
    Guide covering when and how to combine this repo's spec-driven workflow
    with SpecKit.
  - [ ] (P2) fallback-openspec.md
    Guide covering when and how to combine this repo's spec-driven workflow
    with OpenSpec.
  - [ ] (P2) fallback-jira.md
    Guide for syncing work items to Jira, honestly noting no adapter ships
    yet, and instructing the agent to reuse the existing Jira skill for any
    real API calls rather than improvising raw REST calls.
  - [ ] (P2) fallback-confluence.md
    Guide for publishing docs to Confluence, honestly noting no adapter
    ships yet, instructing reuse of the existing Confluence skill, and
    requiring diagrams to be converted to PNG/SVG images (via the Mermaid
    and PlantUML skills) before upload since Confluence can't render them
    natively.
  - [ ] (P2) fallback-github.md
    Guide for the one system with a real, shipped adapter today — GitHub
    Issues plus the GitHub wiki.
  - [ ] (P2) fallback-gitlab.md
    Guide for syncing to GitLab issues/wiki, honestly noting no adapter
    ships yet and giving CLI/REST research pointers.
  - [ ] (P2) fallback-azuredevops.md
    Guide for syncing to Azure DevOps boards/wiki, honestly noting no
    adapter ships yet and carrying forward the existing field-tested
    caveats (tag-based markers, merge-not-overwrite updates).
  - [ ] (P2) fallback-awscodecatalyst.md
    Guide for syncing to AWS CodeCatalyst, honestly noting no adapter ships
    yet and that the service is closed to new customers.
  - [ ] (P2) fallback-googleclouddevops.md
    Guide covering Google Cloud's lack of a native work tracker and how a
    GCP-hosted team should pick a different supported system instead.

- [ ] (P2) Write the Integrations meta index page
  Create a single index page listing all 11 systems with a one-sentence
  description and a link to each, so someone browsing the wiki can find the
  right guide without knowing the skill exists.

- [ ] (P2) Register and publish the new pages
  Register all 12 new files with the existing wiki-add mechanism and run a
  normal wiki-publish pass to push them to the GitHub wiki, then confirm the
  publish ledger recorded all 12 entries correctly.

- [ ] (P3) End-to-end verification
  Exercise the new skill for a live-page fetch and confirm it states which
  guide it's using and follows its recommended workflow, then simulate a
  fetch failure and confirm it falls back to the local copy and says so.
