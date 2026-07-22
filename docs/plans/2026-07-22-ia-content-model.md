---
date: 2026-07-22
slug: ia-content-model
title: IA & content model (supersedes wiki-information-architecture)
epic: 01KY5G9ZW0H2YMNWDFJYGRPYE5
items: [01KY5G9ZW0PBXTBKRJJ70QHR5P, 01KY5G9ZW025TRGTHFAFSVEXSX, 01KY5G9ZW0EYQ5T83RP46Z7952, 01KY5G9ZW0PNKDDEK5TM8GS2J6, 01KY5G9ZW0X5F3K7KHP1SXFM3Q, 01KY5G9ZW0PEZK9PTM3NG0PYX7, 01KY5G9ZW0MQD9335S641DC7ZG, 01KY5G9ZW0Z6JFMVTAFC54RM36, 01KY5G9ZW0RABXWHEMEP1FAV2G]
---

# IA & content model (supersedes wiki-information-architecture)

> **Supersedes:** `2026-07-22-wiki-information-architecture` (epic `01KY5F6QA220S0K7RRK2Q80XR8`;
> its 10 items were cancelled in favor of this plan's items). That plan captured a lighter
> synthesis of the same goals. Review against the repo invariants found four collisions it
> would have hit: (1) its Phase 0 banners and Phase 2 normalization implied editing frozen
> docs, violating §15.8/§15.9 — fixed here by sidecar metadata plus publish-time banner
> rendering; (2) it claimed the publish ledger "already keys pages this way" — it doesn't
> (bare keys, mixed snapshot shapes) — fixed by seeding `wiki_key` verbatim from legacy
> ledger keys with `canonical_key` + `aliases[]`; (3) its frontmatter example keyed
> relationships on external ticket numbers, violating §5.4 — fixed with typed edges anchored
> on ULIDs; (4) it conflated lifecycle `status` with `truth_state` — separated here so
> current-vs-history banners are machine-derivable. Sequencing is foundations-first
> (identity and schema before the reader plane). The full corrected design follows verbatim;
> the tracked tasks are at the end.

---

# WikiTicket SDD — Information Architecture & Content Model Design

**Project:** `SpillwaveSolutions/wiki_ticket_sdd` ("wicked ticket")
**Scope:** A question-driven Information Architecture (IA), a formal content model, a metadata schema, a current-truth vs. historical-evidence strategy, a navigation/publishing model, and a bidirectional traceability design — all realizable through Grok/Claude plugins, agent skills, slash commands, hooks, and the existing `worklog` CLI.
**Status:** Design plan, ready for implementation by an agent or the team.
**Date:** 2026-07-22

---

## 0. Executive summary

The repository already has a strong **canonical storage plane** (frozen plans, generated roadmap, frozen status reports, dated design-doc pairs, append-only event log, ADRs, and a committed publication ledger). What it lacks is a **reader navigation plane** — a stable, question-driven way to find the right document, know whether it is current or historical, and follow the evidence chain from a requirement to a released tag. The fix is not to reorganize storage; it is to **add a generated layer on top of existing storage**, produced entirely by agent-executable skills and `worklog` extensions, with a single stable identity (`wiki_key`) carried in normalized frontmatter.

The design rests on five moves:

1. **A question-driven top-level IA** ("What is this?", "What are we working on?", "Why was X chosen?", "What shipped?", "How do I use it?", "Where is the evidence?") rendered as a generated Home and a per-platform Sidebar, on top of the unchanged storage paths.
2. **A formal content model** with eight document types, explicit mutability rules (frozen / generated-live / supersede-only), lifecycle states, and owners — mapping the semantics already in `docs/worklog-spec.md` §13 and §15 into one table.
3. **A unified frontmatter schema** with a stable `wiki_key` (the logical key that `published.json` already uses), relationship fields (`epic`, `items`, `plan`, `milestone`, `release`, `supersedes`, `relates_to`), and provenance (`git_hash`, `generated_at`, `through`). Frozen docs get a sidecar-normalized frontmatter where editing them is forbidden; the normalizer is idempotent and additive only.
4. **Current Truth vs. Historical Evidence** expressed as a `truth_state` field (`current` / `snapshot` / `superseded` / `archived`) plus a reader-visible banner, so every page declares what kind of truth it is.
5. **A bidirectional Traceability Index** generated from frontmatter + the folded work log, linking requirements (plans) → specifications (spec/ADRs) → plans → work items → external tickets → PRs/commits → tests → releases, with defined edge types and a CI-checked "unlinked evidence" report.

Nothing here requires manual wiki editing beyond optional landing copy. Indexes, the sidebar, the Home page, the traceability graph, and the publication manifest are all **generated and CI-guarded**, extending the existing ledger-driven publish model rather than replacing it.

---

## 1. Current repository findings (evidence base)

These are facts read from a shallow clone of `main` (HEAD `5e90c89`, committed 2026-07-21; spec v1.8), inspected 2026-07-22. They are the invariants the design must preserve.

### 1.1 Storage layout (actual)

| Path | What lives there | Mutability (per spec) |
|---|---|---|
| `.work/todo.jsonl`, `.work/done.jsonl` | Append-only event log; state is a fold | Append-only; only `worklog` writes; compactor is the only rewriter (§7, §15.1–15.4) |
| `.work/config.yml` | All settings (ticketing, wiki, paths, features, classifier) | Edited; harness-independent (§4.1–4.2) |
| `.work/published.json` | Publication ledger: logical key → `{source, title, url, rev, source_hash}` | Updated by publish flow (§9.3) |
| `docs/plans/<YYYY-MM-DD>-<slug>.md` | Captured plans (the "why") | **Written once, never regenerated**; designs change by superseding (§13.2, §15.8) |
| `docs/roadmap.md` | Generated roadmap | **Generated, never hand-edited**, CI hash-checked (§13.1, §15.7) |
| `docs/roadmap/<date>_<name>.md` | Roadmap snapshots per release | **Frozen once written** (§15.8-class) |
| `docs/status/<date>-<kind>.md` | Status reports (daily/weekly/timecard) | **Frozen once published**; corrections go in the next report (§13.3, §15.9) |
| `docs/designs/current_*.md` | Live design doc + code walkthrough | **Regenerated each release**, in-place rewrite sanctioned (like roadmap) |
| `docs/designs/<date>_<name>_*.md` | Dated frozen design-doc/walkthrough pairs | **Frozen** (publish once) |
| `docs/adr/<NNNN>-<slug>.md` | Architecture Decision Records | ADR schema-validated; supersede-by-link, status flips republish (schema: `id, slug, title, date, status, deciders, tags, supersedes, superseded_by`) |
| `docs/user_guide/*.md` | user-guide, cli-reference, plugin-guide | Edited; refreshed against diff at release |
| `docs/wiki-home.md` | The wiki Home page | Hand-maintained today (the one manual page) |
| `docs/migrations/*.md` | Migration records | Append-only narrative |
| `docs/worklog-spec.md` | The spec itself | Edited; versioned in a header block |
| `bin/worklog` + `bin/*.py` | CLI: `add/update/close/reopen/link/show/list/fold/plan-capture/roadmap-render/roadmap-snapshot/wiki-add/compact/status/ingest/conflict/resolve/sync/adapter/adr/promote` | Code |
| `schema/*.json` | `adr.schema.json`, `adapter-io.schema.json`, `capabilities.schema.json` | Code |
| `plugin/skills/*`, `plugin/commands/*`, `plugin/hooks/*` | Skills, slash commands, hooks | Code |

### 1.2 Frontmatter today (inconsistent — the core gap)

The repo has **four different frontmatter dialects** and one doc type with none:

- **ADRs** (`docs/adr/`): rich, schema-validated — `id, slug, title, date, status, deciders, tags, supersedes, superseded_by`.
- **Plans** (`docs/plans/`): `date, slug, title, epic, items[]`, optional `status`, free-form `origin`. No `supersedes` link in frontmatter today (the spec mentions it at §13.2 but plan files don't consistently carry it).
- **Status reports** (`docs/status/`): `kind, date, window, through, generated_at`. Reproducibility is strong (the `through` watermark).
- **Design docs** (`docs/designs/`): dated files carry `date, name, tag, git_hash, branch, roadmap_snapshot`; live files carry `generated_at, git_hash, branch, tag, roadmap`.
- **Roadmap + roadmap snapshots** (`docs/roadmap*.md`): **no YAML frontmatter** — only HTML comment headers (`<!-- GENERATED ... -->`, `<!-- source-hash: ... -->`).
- **User guide / spec / wiki-home**: ad hoc or none.

There is **no stable cross-cutting identity field**. The closest thing that exists is the **logical key in `published.json`** (`plan/<slug>`, `adr/0001-…`, `design/current-design-doc`, `roadmap-snapshot/…`, `status/…`, `home`, `spec`, `cli-reference`, `plugin-guide`, `roadmap`). That key is the natural `wiki_key` — the design adopts it formally.

### 1.3 Existing strengths to preserve (from the spec and README)

- Append-only event log + four-axis work taxonomy (`level` × `kind` × `milestone` × planned/discovered) — `.work/todo.jsonl` is a bag of events folded by ULID, union-merged by git (§6, §8.1, ADR-0001).
- Plans are permanent design records that emit tracked tickets (`plan-capture` parses `## Tasks` → `create` events; `plan` field on items back-links to the doc) — §13.2, ADR-0002.
- Generated roadmap, design docs, code walkthroughs (§13.1, design-docs skill).
- ADRs with schema + supersede semantics (ADR-0002, `schema/adr.schema.json`).
- Publication ledger + system-agnostic edge skills (`wiki-publish`, `ticket-sync`) — §9, §9.3.
- Strong frozen-vs-live semantics already partly present (§13.3, §15.7–15.9).
- Hooks enforce invariants, not hope: `ExitPlanMode`→plan-capture, `Stop`→worklog-check, `SessionStart`→doctor-lite, `pre-commit`/`pre-merge-commit`→newline+schema+roadmap-freshness (§12).
- Work items already carry `plan` (→doc), `parent` (→epic), `external` (→ticket), `milestone` (→release axis), `unplanned`/`discovered_during` (→interruption). The traceability graph is largely **already encoded in the log**; it just isn't rendered or validated.

### 1.4 What's missing (the IA gaps this design fills)

1. No question-driven navigation; the wiki Home is hand-curated and will rot as snapshots accumulate (already 10 roadmap snapshots, 6 design pairs, 6 plans, 3 ADRs, and growing).
2. No uniform identity/metadata; frontmatter dialects differ; roadmap has no frontmatter at all.
3. No formal lifecycle/`truth_state` field; "is this current?" is inferred from path conventions only.
4. No traceability index and no traceability validation; the requirement→spec→plan→ticket→code→test→release chain exists implicitly but is never materialized or checked.
5. No generated indexes (by epic, by milestone/release, by ADR tag, by status-report window).
6. No link-preservation/redirect story for renames or moves.
7. No content inventory or health check that flags orphaned, unlinked, or stale-truth docs.

---

## 2. Design principles

These principles constrain every recommendation below. They are derived from classic IA practice (the **four systems of IA**: organization, labeling, navigation, and search) ([IA frameworks & models](https://informationarchitectureauthority.com/ia-frameworks-and-models/); [Leadersloop: organise content so people can find it](https://leadersloop.com/toolkit/information-architecture/)) and from docs-as-code conventions.

1. **Storage is organized by how it's produced; navigation is organized by the question being asked.** Two planes, one source of truth. Never reorganize storage to fix navigation.
2. **Every page is page one.** Each page must be self-describing (what it is, current or historical, where it sits in the chain) because a reader may land on it from a search or a deep link. This is topic-based authoring / "every page is page one" applied to generated artifacts ([Every Page is Page One](https://everypageispageone.com/the-book/)).
3. **Generated over hand-maintained.** If a human must edit it for it to stay correct, it will rot. Indexes, sidebars, Home, traceability, and banners are generated and CI-guarded. The single permitted hand-maintained page is optional Home landing copy; even that can be generated.
4. **Stable identity separate from path, slug, title, and URL.** `wiki_key` is the immutable identity; everything else (filename, wiki page name, title, generated URL) is a rendering of it. This is the same separation the spec already enforces for item ULIDs vs. external ticket keys (§5.4: "Never key on `external.key`").
5. **Frozen means frozen — normalize by sidecar, not by rewrite.** Frozen docs (plans, snapshots, status reports, dated designs) must not be edited to add metadata. Where frontmatter is missing or inconsistent, the normalizer writes an **additive sidecar** (`docs/.index/<wiki_key>.yml`) rather than mutating the artifact, preserving invariant §15.8/§15.9. (Edit-in-place is permitted only for the explicitly sanctioned live docs: `docs/roadmap.md`, `docs/designs/current_*.md`.)
6. **Provenance is first-class.** Every generated/current doc carries `git_hash`/`generated_at`/`through` so it can be reproduced and so the traceability graph has anchors. This mirrors the W3C PROV data model, which models the world as **entities, activities, and agents** with derivation and attribution links ([W3C PROV-DM](https://www.w3.org/TR/prov-dm/)).
7. **Best-effort with visible drift beats silent perfection.** Inherited directly from spec §2 and §10.6. Traceability that can't be resolved is reported, not hidden.
8. **Skills orchestrate; the CLI enforces; CI guards.** Same layered discipline as the typed adapter contract (ADR-0002, §9.5). New IA capabilities are skills/commands; invariants become `worklog` checks and CI gates.

---

## 3. Recommended top-level IA (question / job-to-be-done driven)

The top level is **six reader questions**, each mapping to a generated landing view and a set of source documents. This is the organization and labeling system; navigation (§7) renders it per platform.

| # | Reader question | JTBD audience | Landing view (generated) | Primary sources |
|---|---|---|---|---|
| Q1 | **What is this project?** | New contributor, stakeholder | `Home` (generated) | README, spec §1–2, `current_design_doc`, latest roadmap |
| Q2 | **What are we working on now?** | PM, stakeholder, team | `Current-Work` hub | `docs/roadmap.md` (live), open items (fold), latest status report |
| Q3 | **Why was X chosen?** (design rationale) | Future maintainer, new dev | `Decisions` index | `docs/adr/`, `docs/plans/`, supersede chains |
| Q4 | **What has shipped?** (history) | Stakeholder, auditor | `Releases` index | `docs/roadmap/` snapshots, `docs/designs/<date>_*`, release tags, closed items |
| Q5 | **How do I use / operate it?** | Developer, PM, operator | `Guide` (Diátaxis-organized) | `docs/user_guide/*`, CLI reference, plugin guide |
| Q6 | **Where is the evidence?** (traceability) | Auditor, maintainer | `Traceability` index | All of the above, joined |

This deliberately borrows the **Diátaxis** framing for Q5: documentation splits into *tutorials* (learning), *how-to guides* (doing), *reference* (information), and *explanation* (understanding) ([Diátaxis: start here](https://diataxis.fr/start-here/)). The existing `docs/user_guide/` already separates `user-guide.md` (explanation+how-to), `cli-reference.md` (reference), and `plugin-guide.md` (how-to); Q5 formalizes this and adds an explicit tutorial slot.

### 3.1 Two planes, reconciled

- **Canonical storage plane** (unchanged paths, unchanged mutability): the actual files in §1.1.
- **Reader navigation plane** (generated): `Home`, `Current-Work`, `Decisions`, `Releases`, `Guide`, `Traceability`, plus generated indexes and the sidebar. These are **views over storage**, produced by the `ia-index` skill and `worklog ia-*` commands (§10, §11), published through the existing `wiki-publish` ledger.

This reconciles the current tool-produced layout with the desired human-facing IA without moving any frozen file.

---

## 4. Formal content model

Eight document types. Each has a defined source of truth, mutability rule, lifecycle, owner, relationships, and publishing behavior. This table is the normative reference; the frontmatter schema in §5 encodes it.

| Doc type | `wiki_key` form | Source of truth | Mutability | Lifecycle states | Owner | Key relationships | Publish behavior |
|---|---|---|---|---|---|---|---|
| **Plan** | `plan/<slug>` | `docs/plans/<date>-<slug>.md` | Frozen; supersede-only | `planned` → `active` → `superseded`/`completed` | authoring agent + human | `epic`, `items[]`, optional `supersedes`/`superseded_by`, `relates_to` ADRs | Publish once (frozen) |
| **Work item** | `item/<ULID>` | `.work/todo.jsonl`+`done.jsonl` (fold) | Mutable (event-sourced) | `todo`→`in_progress`→`blocked`→`done`/`cancelled`; reopen | the actor/agent | `parent` (epic), `plan`, `milestone`, `external` (ticket), `discovered_during` | Synced (not published to wiki directly) |
| **Roadmap (live)** | `roadmap` | `docs/roadmap.md` | Generated-live (in-place rewrite) | always `current` | `roadmap-render` | derived from items; `supersedes` snapshot chain | Republish on hash change |
| **Roadmap snapshot** | `roadmap-snapshot/<date>_<name>` | `docs/roadmap/<date>_<name>.md` | Frozen | `snapshot` (immutable) | release skill | `release` tag, `supersedes` prior snapshot | Publish once |
| **Status report** | `status/<date>-<kind>` | `docs/status/<date>-<kind>.md` | Frozen | `current`→`archived` (by age) | `status-report` skill | `through` watermark, items in window | Publish once |
| **Design doc / walkthrough** | `design/<name>` (live) / `design/<date>_<name>-{design-doc\|code-walkthrough}` (dated) | `docs/designs/…` | Live pair: generated-live; dated pair: frozen | live: `current`; dated: `snapshot` | `design-docs` skill | `git_hash`, `tag`, `roadmap`/`roadmap_snapshot`, `release` | Live republish on hash; dated publish once |
| **ADR** | `adr/<NNNN>-<slug>` | `docs/adr/<NNNN>-<slug>.md` | Frozen; supersede-only | `proposed`→`accepted`→`deprecated`/`superseded` | deciders | `supersedes`, `superseded_by`, `relates_to` plans/items | Republish on status flip / hash change |
| **Reference guide** | `guide/<slug>` (e.g. `guide/cli-reference`, `guide/plugin-guide`, `guide/user-guide`, `guide/tutorial-*`) | `docs/user_guide/*.md`, README | Edited (refreshed at release) | `current` | docs owner | `relates_to` spec sections, commands | Republish on hash change |

### 4.1 Lifecycle state taxonomy (the `status`/`truth_state` field)

Two orthogonal concepts, both expressed in frontmatter:

- **Lifecycle `status`** — the document's place in its own workflow (e.g. ADR `proposed/accepted/deprecated/superseded`; plan `planned/active/superseded/completed`).
- **`truth_state`** — what kind of truth the page is for a reader (the Current-Truth-vs-History axis, §6): `current` | `snapshot` | `superseded` | `archived`.

A roadmap snapshot has `truth_state: snapshot` and no lifecycle status. A live roadmap has `truth_state: current`. A superseded plan has `truth_state: superseded` and `status: superseded`. Keeping these orthogonal means a reader banner (§6) and a lifecycle filter (§7) can be rendered independently.

---

## 5. Metadata / frontmatter schema

### 5.1 Goals

- One **superset schema** every doc type can validate against (with per-type required subsets), replacing the four dialects in §1.2.
- A stable **`wiki_key`** identity, separate from path/slug/title/URL.
- Relationship fields that materialize the traceability graph (§9).
- Provenance fields for reproducibility.
- A `truth_state` + lifecycle `status` for reader orientation.
- **Additive normalization only** for frozen docs (sidecar files), edit-in-place only for sanctioned live docs.

### 5.2 The unified schema (YAML frontmatter)

```yaml
---
# --- identity (required on all) ---
wiki_key: plan/auth-refactor        # stable logical key; == published.json key
doc_type: plan                       # plan|item|roadmap|roadmap-snapshot|status|design|adr|guide
title: "Auth refactor"                # human title (display)
slug: auth-refactor                  # kebab; stable across renames

# --- lifecycle / truth (required on all) ---
truth_state: current                 # current|snapshot|superseded|archived
status: active                       # type-specific enum (see §5.4)

# --- provenance (required on generated/current; recommended on all) ---
date: 2026-07-16                     # authoring or snapshot date (ISO)
generated_at: 2026-07-16T16:00:00Z  # for generated docs
git_hash: 04cf8e8111bd...            # repo sha the doc was generated against
through: 01J8XA4K20                  # max ev included (status reports, reproducible folds)

# --- relationships (the traceability edges; optional per type) ---
epic: 01J8WZZ100                     # ULID of parent epic
items: [01J8X0M2QQ, 01J8X0M3RR]      # ULIDs this doc produced/covered
plan: docs/plans/2026-07-16-auth.md  # back-link from item/guide to plan
milestone: v0.7.0                     # release axis
release: v0.12.1                     # tag a snapshot/design is tied to
roadmap: docs/roadmap.md             # live design doc pointer
roadmap_snapshot: docs/roadmap/2026-07-21_v0.12.1-release.md
supersedes: plan/auth-refactor-v1     # wiki_key of predecessor
superseded_by: plan/auth-refactor-v2  # wiki_key of successor (written on supersede)
relates_to:                          # free-form typed links (the graph edges)
  - {type: decides, target: adr/0001-event-log-fold-union-merge}
  - {type: implements, target: spec#13.2}
  - {type: verified-by, target: tests/test_fold.py}

# --- ownership / taxonomy ---
owner: rick                          # accountable human/role
actors: [rick, claude]               # deciders/contributors (ADRs: deciders)
tags: [core, git]                    # free labels (ADRs already use this)

# --- publishing (managed by the ledger; mirrored here for self-description) ---
wiki: https://github.com/.../wiki/Plan-auth-refactor
source_hash: 021701a74deb            # sha256[:12] of source file (== published.json)
---
```

### 5.3 The `wiki_key` contract (normative)

- `wiki_key` is **the** stable identity. It MUST be unique across the repo. For **legacy** docs it is **seeded verbatim from the existing `published.json` key** so that no published link changes; today's ledger keys are intentionally uneven (bare keys `home`, `spec`, `cli-reference`, `plugin-guide`, `user-guide`; roadmap snapshots split across `roadmap-snapshot/…` and legacy `roadmap/…`) and the migration adopts them as-is rather than renaming. A normalized **`canonical_key`** and an **`aliases[]`** list are recorded alongside for future rendering and renames.
- `wiki_key` is **path-independent**: renaming a file or changing a wiki page name never changes the key.
- For **new** docs, `wiki_key` is **derived deterministically** from the doc's type + natural identifier (see §5.5) so the normalizer can compute it without a human — the same way `worklog` derives item ULIDs.
- The publication ledger (`published.json`) gains explicit `wiki_key`, `doc_type`, `truth_state`, `canonical_key`, and `aliases[]` fields for self-description; existing entries are back-filled by the migrator (§14), with `wiki_key` set to the legacy ledger key to preserve links.

### 5.4 Per-type required subsets

| Type | Required fields |
|---|---|
| `plan` | `wiki_key, doc_type, title, slug, date, truth_state, status, epic, items` |
| `item` | (frontmatter lives in the **sidecar**, not the log; the item's `wiki_key` is `item/<ULID>`) `wiki_key, doc_type, title, status, epic, plan, milestone, external, truth_state` |
| `roadmap` | `wiki_key, doc_type, truth_state:current, generated_at, git_hash` (kept as YAML, migrating today's HTML-comment header) |
| `roadmap-snapshot` | `wiki_key, doc_type, truth_state:snapshot, date, release, supersedes, generated_at, git_hash` |
| `status` | `wiki_key, doc_type, kind, date, window, through, generated_at, truth_state` (== today, +`wiki_key`+`truth_state`) |
| `design` (dated) | `wiki_key, doc_type, date, name, tag, git_hash, branch, roadmap_snapshot, release, truth_state:snapshot` (== today, +`wiki_key`+`truth_state`+`release`) |
| `design` (live) | `wiki_key, doc_type, generated_at, git_hash, branch, tag, roadmap, truth_state:current` |
| `adr` | unchanged rich set + `wiki_key` (= `adr/<NNNN>-<slug>`) + `truth_state` |
| `guide` | `wiki_key, doc_type, title, slug, truth_state:current, owner, tags, relates_to` |

### 5.5 `wiki_key` derivation rules (deterministic)

```
plan (new)        -> plan/<date>-<slug>               # date+slug is globally unique and supersede-safe
item              -> item/<ULID>                       # the item's primary key
roadmap (live)    -> roadmap
roadmap-snapshot  -> roadmap-snapshot/<date>_<name>    # target; legacy roadmap/<…> kept as alias
status            -> status/<date>-<kind>
design dated      -> design/<date>_<name>-{design-doc|code-walkthrough}
design live       -> design/current-{design-doc|code-walkthrough}
adr               -> adr/<NNNN>-<slug>
guide             -> guide/<slug>                       # target; legacy bare keys kept as aliases
```

For **legacy** docs, `wiki_key` is **seeded verbatim from the existing `published.json` key** — including today's bare keys (`home`, `spec`, `cli-reference`, `plugin-guide`, `user-guide`) and the mixed snapshot key shapes (`roadmap-snapshot/…` vs legacy `roadmap/…`). Preserving every published link matters more than uniformity, so the migrator records each legacy key as `wiki_key` and writes a normalized `canonical_key` + `aliases[]` alongside for future use. New frozen plans use `plan/<date>-<slug>` (matching the already-unique `<date>-<slug>` filename) so a superseding plan can never collide with its predecessor; legacy plans keep `plan/<slug>` with `canonical_key = plan/<date>-<slug>`. The migrator (§14) writes each doc's `wiki_key` into its frontmatter (or sidecar for frozen docs) and asserts it matches the ledger.

### 5.6 Sidecar normalization for frozen docs

To respect invariant §15.8/§15.9 (never edit a frozen doc), the normalizer writes missing/inconsistent metadata to **sidecar files**:

```
docs/.index/<wiki_key>.yml     # one per doc; the canonical metadata record
docs/.index/_graph.json        # the materialized traceability graph (generated)
docs/.index/_inventory.json    # the content inventory (generated)
```

Rules:
- For **sanctioned-edit** docs — the live roadmap (`docs/roadmap.md`), live designs (`docs/designs/current_*.md`), user guides (`docs/user_guide/*`), and ADRs (whose `status` flips are an explicit sanctioned change per the `wiki-publish` frozen rules) — the normalizer may **edit frontmatter in place**.
- For **frozen** docs — dated snapshots, dated designs, status reports, and **all plans** (including successor state such as `superseded_by` and `truth_state: superseded`) — the normalizer writes only to the **sidecar**; the artifact itself is never touched. New plans may carry richer frontmatter at capture time, but once a plan is written, its successor state is rendered from the sidecar/graph, never by editing the old plan (invariant §15.8).
- The normalizer is **idempotent and additive**: it never removes fields; it only fills `wiki_key`, `canonical_key`, `truth_state`, computed relationships, and provenance. Re-running it is a no-op on already-normalized docs.
- The sidecar dir is committed (it's metadata the team shares, like `published.json`) and CI-guarded for freshness (§12).
- **Internal metadata is never published.** `docs/.index/*.json`, `docs/.index/*.yml`, and raw per-doc sidecars (`docs/.index/<wiki_key>.yml`) are internal join data; only `docs/.index/rendered/*.md` and manifest-listed source docs reach the wiki.

---

## 6. Current Truth vs. Historical Evidence

### 6.1 The model

Every published page carries a `truth_state`, and the reader sees a banner generated from it:

| `truth_state` | Meaning | Banner (generated) |
|---|---|---|
| `current` | The living, regenerated-as-needed truth | "Current — regenerated at <generated_at> from <git_hash>." |
| `snapshot` | A point-in-time freeze tied to a release | "Snapshot of release <release> (<date>). The current version is [[Roadmap]]." |
| `superseded` | Replaced by a successor | "Superseded by [[<superseded_by>]]. Kept as the record of a rejected/old approach." |
| `archived` | Old status report / no longer active | "Archived report. Corrections went in later reports; do not act on this." |

### 6.2 How truth_state is assigned

- **Generated-live docs** (`roadmap`, `current_design_doc`, `current_code_walkthrough`): `current`, always.
- **Snapshots** (roadmap snapshots, dated designs): `snapshot`, always; `release` ties them to a tag.
- **Plans**: `current` while `status: active/planned` and not superseded; `superseded` once a successor exists (`superseded_by` set by `plan-capture` on supersede).
- **Status reports**: `current` for the latest of each kind within the active window; `archived` once a newer report of the same kind exists or after `status.archive_after_days` (default 30). Archived reports stay published (spec §17 Q7: don't unpublish history) but carry the archived banner.
- **ADRs**: `current` while `accepted`; `superseded`/`archived` mirror the ADR `status` enum (`deprecated`→`archived`, `superseded`→`superseded`).

### 6.3 Communicating it to readers

- **Banner** at the top of every wiki page (generated; part of the publish render, not hand-written).
- **Color/icon chips** in indexes (a "frozen" badge, already suggested in the `wiki-ticket-ui` plan's Docs panel).
- **Sidebar grouping**: `Current Truth` vs `History` sections (§7).
- **Home page** surfaces only `current` docs in the primary navigation; history is one click away under Releases/Snapshots.

This makes the spec's existing frozen-vs-regenerated distinction (§13.1 vs §13.3) **reader-visible** rather than path-convention-only.

---

## 7. Navigation approach

### 7.1 Navigation system (the third IA system)

Navigation is generated from the content inventory (`docs/.index/_inventory.json`) + the truth-state model, by the `ia-index` skill. It has three parts:

1. **Home** (`wiki_key: home`) — generated, question-driven. Six tiles mapping to Q1–Q6, each linking to its hub. Replaces the hand-maintained `docs/wiki-home.md` with a generated page (hand-edit permitted only for a one-paragraph intro).
2. **Sidebar** — generated per platform (§7.2), grouped:
   - **Current Truth**: Roadmap, Current Work, Design Doc, Code Walkthrough, Decisions (current ADRs + active plans), Guides.
   - **History**: Releases (snapshots), Status reports (archived), Superseded ADRs/plans.
   - **Reference**: Spec, CLI Reference, Plugin Guide, Traceability Index.
3. **In-page cross-links** — the `relates_to` edges rendered as "Related" / "Evidence" footers on every page, and supersede banners linking predecessors/successors.

### 7.2 Platform differences (the rendering adapter problem)

The logical IA is platform-agnostic; each platform is an **output adapter** (same philosophy as the ticket-sync edges, ADR-0002). The `ia-render` skill renders the same inventory differently:

| Platform | Hierarchy? | Sidebar? | Link syntax | Rendering |
|---|---|---|---|---|
| **GitHub Wiki** (primary) | Flat (no dirs) | Yes (via `_Sidebar.md` page) | `[[Page-Name]]` | Pages are flat files; the sidebar `_Sidebar.md` is **generated** and lists the two-plane groups with flat page links. Hierarchy is faked by page-name prefixes (`Plan-…`, `ADR-…`, `Roadmap-…-snapshot`). |
| **GitLab Wiki** | Yes (dirs) | Yes | `[[Page Name]]` or path | Render into nested dirs mirroring the logical groups. |
| **ADO Wiki** | Yes (hierarchical paths) | Yes (built-in tree) | `/Parent/Child` | Render into the path tree. |
| **Confluence** | Yes (space + page tree) | Yes (space sidebar) | link to content id | Render into the page tree under a root page; store `page_id` in ledger. |

This is exactly the "design hierarchy logically, render differently per platform" framing. The `wiki-publish` skill already has per-system tooling notes (§2 of that skill); `ia-render` reuses them and adds the sidebar/home generation step.

### 7.3 Search (the fourth IA system)

GitHub Wiki search is weak; the design compensates with **generated indexes** (§8) that are themselves searchable pages, and by making every `wiki_key`/title/slug stable so external search (and the future `wiki_ticket_sdd_ui` dashboard) can deep-link reliably. The traceability index (§8.5) is the high-value "search by evidence" entry point.

---

## 8. Generated indexes

All generated by `worklog ia-index` (§10), committed, CI-freshness-checked, and published through the existing ledger. Each is a markdown page with a stable `wiki_key`.

### 8.1 Content Inventory (`index/inventory`)
Every doc: `wiki_key, doc_type, title, truth_state, status, date, owner, source, wiki_url`. The master table; backs the sidebar and search.

### 8.2 Decisions Index (`index/decisions`)
ADRs by status (proposed/accepted/deprecated/superseded) with supersede chains; active plans with their epic/items. Answers Q3.

### 8.3 Releases Index (`index/releases`)
One row per release tag: tag, date, roadmap snapshot, design-doc pair, walkthrough, items closed in that milestone, PRs merged, test status at tag. Answers Q4. Generated by joining `git tag`/`gh release` with `milestone` on items and `release` on snapshots.

### 8.4 Status Archive (`index/status`)
All status reports by kind and date, latest flagged `current`, older `archived`. Answers "what did we report and when."

### 8.5 Traceability Index (`index/traceability`) — the keystone
A generated page + a machine graph (`docs/.index/_graph.json`) showing, for every work item and every doc, the full evidence chain. Details in §9.

### 8.6 Glossary / Concepts (`index/glossary`) — optional
Auto-extracted term list (fishbowl, fold, union merge, taxonomy axes, frozen vs. generated). Low effort, high value for new contributors; derived from the spec headings.

---

## 9. Bidirectional traceability design

### 9.1 The chain

The full SDD chain the design must link:

```
requirements ──► specifications ──► plans ──► work items ──► external tickets
(plan intent)   (spec §, ADR)       (docs/plans) (fold)        (external.url)
                                                       │
                                                       ▼
                                                   PRs / commits ──► tests ──► releases
                                                   (git history)   (tests/)   (tags, snapshots)
```

### 9.2 What already exists (the graph is half-built)

- **Plan ↔ items**: `plan` field on items back-links to the doc; plan frontmatter `items[]` forward-links. (Already bidirectional.)
- **Item ↔ epic**: `parent` chain. (Already.)
- **Item ↔ external ticket**: `external.{system,key,url}` via `link` events. (Already.)
- **Item ↔ milestone/release**: `milestone` field; release tags exist in git. (Already, but unjoined.)
- **Snapshot ↔ release**: dated filenames encode `<date>_<name>`; `release` field in sidecar makes it explicit.
- **Design doc ↔ snapshot ↔ git_hash**: design frontmatter already carries `git_hash` and `roadmap_snapshot`. (Already.)
- **Status report ↔ items**: `through` watermark + fold reproduces the exact item set. (Already.)

### 9.3 The gaps the design closes

| Edge that's missing today | How the design adds it |
|---|---|
| Plan → ADR ("this plan decides/enacts ADR-N") | `relates_to: {type: decides, target: adr/…}` in plan sidecar; ADRs link back via `relates_to: {type: decided-by, target: plan/…}` |
| Plan/ADR → spec section | `relates_to: {type: implements, target: spec#13.2}` |
| Work item → PR/commit | new `worklog link-pr <item> --pr <num>` (or auto-derive from commit message `worklog: <item>` trailers) → `external`-style `code` block in sidecar |
| Work item → test | `relates_to: {type: verified-by, target: tests/test_fold.py::test_x}` (proposed by `trace-check`, confirmed by the agent) |
| Release → everything at that tag | the Releases Index joins tag + milestone + snapshot + design pair + closed items + merged PRs |
| ADR supersede chains (already in schema) | surfaced in the Decisions Index with back-links |

### 9.4 Edge taxonomy (normative)

A small, typed edge set keeps the graph queryable and CI-validatable. `relates_to` entries use `type` from this enum:

| Edge type | From → To | Meaning | Reverse (auto) |
|---|---|---|---|
| `produces` | plan → item | The plan emitted this work item | `produced-by` |
| `decides` | plan → adr | The plan enacts/decides this ADR | `decided-by` |
| `implements` | plan/adr/item → spec#section | Realizes a spec section | `implemented-by` |
| `supersedes` | plan/adr → plan/adr | Replaces a predecessor | `superseded-by` |
| `verified-by` | item/plan → tests/… | Covered by this test | `verifies` |
| `lands-in` | item → pr/commit | Delivered by this PR/commit | `delivers` |
| `belongs-to` | item → epic | Parent decomposition | `contains` |
| `targets` | item → milestone/release | Ships in this release | `includes` |
| `snapshot-of` | snapshot/design-dated → live doc | Frozen copy of a live doc | `snapshots` |
| `references` | any → any | Free-form cross-link | `referenced-by` |

The reverse edges are **derived**, not authored — the graph builder (`worklog ia-graph`) inverts `relates_to` and the existing fields (`parent`, `plan`, `external`, `milestone`, `supersedes`) to produce a bidirectional graph. This is bidirectional traceability as practiced in requirements management: forward traceability (requirement → design → code → test) and backward traceability (test → code → design → requirement) maintained as two views of one graph ([Jama Software: bidirectional traceability](https://www.jamasoftware.com/requirements-management-guide/requirements-traceability/bidirectional-traceability/)).

### 9.5 The Traceability Index page (`index/traceability`)

Generated from `docs/.index/_graph.json`. For each work item / plan / ADR / release, it renders a compact row with clickable forward and backward links, e.g.:

```
PROJ-412 Extract auth middleware
  ▸ produced-by: plan/auth-refactor        (why)
  ▸ decides:      ADR-0001 (fold/union)    (rationale)
  ▸ implements:   spec §6, §8.1            (spec)
  ▸ lands-in:     PR #7 (merge 04cf8e8)    (code)
  ▸ verified-by:  tests/test_fold.py       (tests)
  ▸ targets:      release v0.7.0          (release)
  ◂ contained in: epic Auth (PROJ-400)    (backward)
```

### 9.6 Provenance framing

The graph is modeled on **W3C PROV**: work items and docs are *entities*; plan-capture/sync/render/release are *activities*; actors/agents are *agents*; `wasDerivedFrom`/`wasGeneratedBy`/`wasAttributedTo` map onto the edge types above ([W3C PROV-DM](https://www.w3.org/TR/prov-dm/)). This isn't academic: it gives a vocabulary so the `trace-check` validator can ask "is every released entity attributed to a plan that is attributed to an ADR?" and fail CI when not.

---

## 10. Publishing model and manifest

### 10.1 The existing model (preserved)

Publication is **ledger-driven** (spec §9.3): `published.json` maps a logical key → `{source, title, url, rev, source_hash}`. The `wiki-publish` skill publishes the default set (live roadmap, all plans, all snapshots, all ADRs, registered files), with frozen rules (plans/snapshots/status publish once; roadmap/ADRs/current designs republish on hash change).

### 10.2 The manifest (new, additive)

Add a **publication manifest** `docs/.index/publish-manifest.json` (generated, committed) that declares the **full intended publish set** and how each page renders:

```json
{
  "version": 1,
  "generated_at": "2026-07-22T17:00:00Z",
  "pages": [
    {
      "wiki_key": "home",
      "source": "docs/.index/rendered/home.md",
      "title": "Home",
      "truth_state": "current",
      "render": "home",
      "frozen": false
    },
    {
      "wiki_key": "index/traceability",
      "source": "docs/.index/rendered/traceability.md",
      "title": "Traceability Index",
      "truth_state": "current",
      "render": "traceability",
      "frozen": false
    },
    {
      "wiki_key": "plan/auth-refactor",
      "source": "docs/plans/2026-07-16-auth.md",
      "title": "Plan: Auth refactor",
      "truth_state": "snapshot",
      "render": "doc+banner",
      "frozen": true
    }
  ],
  "sidebar": { "source": "docs/.index/rendered/_Sidebar.md" }
}
```

- The manifest is the **single source of truth for what should be on the wiki**. The `wiki-publish` skill consumes it instead of (or in addition to) the implicit default set.
- `frozen` pages are published once and never republished (asserted by the ledger's existing hash-skip + a `frozen: true` guard).
- `render` declares which renderer applies (`home`, `sidebar`, `traceability`, `doc+banner`, `index/decisions`, …), so banners/sidebars are generated at publish time.
- Drift between manifest and ledger is a CI failure (§12): every manifest page must have a ledger entry and vice versa.

### 10.3 Render-then-publish pipeline

```
worklog ia-inventory   → _inventory.json
worklog ia-graph       → _graph.json
worklog ia-render      → rendered/*.md  (home, sidebar, indexes, doc+banner overlays)
worklog ia-manifest    → publish-manifest.json
wiki-publish (skill)   → pushes rendered pages via the existing per-platform flow
```

Each step is idempotent and keyed by `wiki_key`; retries are no-ops (same invariant as sync, §15.5). The release skill and the existing sync Phase 2 (`wiki-publish` subagent, §11) invoke this pipeline so a release cut republishes Home/Indexes automatically.

---

## 11. Repository layout enhancements

### 11.1 New directory: `docs/.index/`

```
docs/.index/
  _inventory.json          # content inventory (generated; INTERNAL — not published)
  _graph.json              # traceability graph (generated; INTERNAL)
  publish-manifest.json    # publish set + render rules (generated; INTERNAL)
  aliases.json             # legacy-key -> wiki_key/canonical_key redirect map (INTERNAL)
  rendered/                # generated pages ready to publish (the ONLY .index contents published)
    home.md
    _Sidebar.md
    traceability.md
    decisions.md
    releases.md
    status.md
  <wiki_key>.yml           # per-doc sidecar metadata for frozen docs (INTERNAL)
```

This is the **only structural addition**. It is generated, committed (shared metadata, like `published.json`), and CI-guarded. Only `rendered/*.md` and manifest-listed source docs are publishable; every other file in `docs/.index/` is internal join data excluded from the wiki. The directory does not move or rename any existing frozen artifact, so no link breaks (§14).

### 11.2 Why not reorganize `docs/`?

The current `docs/{plans,status,designs,roadmap,adr,user_guide,migrations}` layout is already organized by **producer + mutability**, which is correct for storage. Reorganizing it (e.g. into `current/` vs `history/`) would break every `published.json` URL, every `plan`/`roadmap_snapshot` path reference, and the wiki page namespace — high cost, no benefit, because the reader plane is generated. The design therefore **keeps storage as-is** and adds only `docs/.index/`.

### 11.3 One sanctioned storage tweak

Add `docs/user_guide/tutorial-*.md` (or `docs/tutorials/`) as the home for Diátaxis *tutorials*, which the repo currently lacks. This is additive and low-risk.

---

## 12. Skills, commands, and hooks to add or extend

Everything below is an agent-executable skill, a `worklog` subcommand, or a hook — consistent with the spec's "skills orchestrate; the CLI enforces; hooks guarantee" layering (§12).

### 12.1 New `worklog` subcommands (CLI extensions)

| Command | Purpose |
|---|---|
| `worklog ia-inventory` | Walk `docs/`, fold the log, produce `_inventory.json` with `wiki_key, doc_type, truth_state, status, relationships, provenance` per doc. |
| `worklog ia-normalize` | Additively normalize frontmatter (in-place for live docs, sidecar for frozen). Idempotent. Asserts `wiki_key` matches the ledger. |
| `worklog ia-graph` | Build `_graph.json` by inverting `relates_to` + existing fields into the typed edge taxonomy (§9.4). |
| `worklog ia-render` | Render Home, Sidebar, indexes, doc banners into `docs/.index/rendered/`. |
| `worklog ia-manifest` | Emit `publish-manifest.json`. |
| `worklog ia-index` | Convenience wrapper: inventory → normalize → graph → render → manifest. |
| `worklog trace-check` | Validate traceability: every released item has a plan + an ADR link + a test link + a PR link (configurable strictness). Emits "unlinked evidence" report. |
| `worklog link-pr <item> --pr <n>` | Record a code edge (PR/commit) on an item (extends the `external`-style provenance; new `code` block in sidecar). |
| `worklog wiki-key <path>` | Print the computed `wiki_key` for a doc (derivation rules §5.5) — used by normalizer and for link-preservation. |

These extend the existing `worklog` CLI the same way `adr` and `adapter` subcommands were added (single argparse tree in `bin/worklog`, thin wrappers over modules in `bin/`).

### 12.2 New / extended skills (`.claude/skills/` + `plugin/skills/`)

| Skill | Trigger | Behavior |
|---|---|---|
| `ia-index` (new) | "regenerate the docs index"; after a release; after plan-capture | Runs `worklog ia-index`; commits `docs/.index/`; reports counts. |
| `ia-render` / `wiki-publish` (extend) | publish-to-wiki | `wiki-publish` consumes `publish-manifest.json` to drive the default publish set and to render banners/sidebars per platform. |
| `trace-check` (new) | "check traceability"; nightly; before release | Runs `worklog trace-check`; surfaces unlinked-evidence as a needs-attention list. |
| `plan-capture` (extend) | plan mode exits | On supersede, write `superseded_by` on the predecessor and set `truth_state: superseded`; also seed `relates_to: {decides, implements}` from the plan's referenced ADRs/spec sections. |
| `release` (extend) | a release is cut | After tagging, run `ia-index` + republish Home/Indexes/Releases; stamp `release` on the dated snapshot/design sidecars; ensure the Releases Index row is complete. |
| `status-report` (extend) | status generated | Set `truth_state` (current/archived) on write; the inventory reclassifies prior same-kind reports as archived. |

### 12.3 Hooks

| Hook | Action |
|---|---|
| `pre-commit` (extend) | Existing newline/schema/roadmap-freshness checks **plus**: `docs/.index/` freshness (regenerate, diff, fail if stale) and `trace-check` at warn level. |
| `PostToolUse` on `ExitPlanMode` (extend) | Existing plan-capture **plus**: `ia-normalize` for the new plan + `ia-index` refresh. |
| `Stop` (extend) | Existing worklog-check **plus**: if any doc's `truth_state`/`wiki_key` is missing, warn. |
| New `PreRelease` (release skill) | Fail the release if `trace-check --strict` reports unlinked evidence for in-scope items. |

### 12.4 Slash commands

| Command | Behavior |
|---|---|
| `/worklog:ia` | Run `worklog ia-index` and report. |
| `/worklog:trace` | Run `worklog trace-check` and show the unlinked-evidence report. |
| `/worklog:find <term>` | Search the inventory by title/slug/wiki_key/tag and print matching pages with their truth_state — a CLI "search" that compensates for weak wiki search. |

---

## 13. Validation, health checks, and CI

Extend the existing CI table (spec §14) with IA-specific gates. The discipline matches the spec's "use prose for judgment, hooks for invariants" (§12) and the green-gates policy (ADR-0003).

| Check | When | Failure | Implemented by |
|---|---|---|---|
| `docs/.index/` freshness (regenerate, diff) | pre-commit, PR | hard fail | `pre-commit` + `worklog ia-index --check` |
| Every doc has a `wiki_key` matching the ledger | PR | hard fail | `ia-normalize --check` |
| Frontmatter validates against the unified schema (per-type subsets) | PR | hard fail | new `schema/doc.schema.json` + stdlib mini-validator (same pattern as `adr.schema.json`) |
| No two docs share a `wiki_key` | PR | hard fail | inventory check |
| `truth_state` set on every published page | PR | hard fail | inventory check |
| Traceability: released items have plan+ADR+test+PR links | nightly (warn), pre-release (strict) | warn / hard | `worklog trace-check` |
| Manifest ↔ ledger consistency (no orphan pages/entries) | PR | hard fail | manifest check |
| Snapshot `supersedes` chains are acyclic | PR | hard fail | graph check |
| Broken-link check across rendered wiki pages | PR | warn (then hard) | `worklog ia-render --check-links` |
| Sidebar/Home generated (not hand-edited drift) | PR | hard fail | hash check on rendered files |
| Coverage floor on new `bin/*.py` (incl. `ia-*`) | PR | hard fail (≥80%) | existing coverage gate (ADR-0003) |

### 13.1 Health check: `/worklog:doctor` extension

`worklog doctor` (read-only, never blocks) gains an IA section reporting: docs missing `wiki_key`, frozen docs whose frontmatter drifted from sidecar, orphaned docs (no `relates_to`, not referenced anywhere), stale `truth_state` (a `current` plan that's been superseded without the field flipping), and unlinked-evidence counts.

---

## 14. Migration strategy (preserves content and links)

The migration is **additive and agent-executable**, mirroring the repo's own precedent: the `type → level/kind` migration (`docs/migrations/0001-type-split.md`) was carried by fold-normalization + compaction, not by rewriting history. The IA migration follows the same pattern and is recorded as `docs/migrations/0002-ia-content-model.md`.

### 14.1 Migration record (`0002-ia-content-model.md`)

Document: why (the four frontmatter dialects + missing traceability), the `wiki_key` formalization (== existing ledger keys), the sidecar rule for frozen docs, and "what teams must do: nothing beyond running `worklog ia-normalize`."

### 14.2 Steps (executable by an agent)

1. **Add schemas** (`schema/doc.schema.json`) and the `ia-*` modules/commands (§12.1). Land behind the existing coverage gate.
2. **Backfill `wiki_key` (legacy-seeded)**: `worklog ia-normalize` sets each legacy doc's `wiki_key` **verbatim from its existing `published.json` key** — including bare keys (`home`, `spec`, `cli-reference`, …) and the mixed snapshot shapes (`roadmap-snapshot/…` and legacy `roadmap/…`). It writes `wiki_key` in-place for sanctioned-edit docs and to sidecars for frozen docs, and records a normalized `canonical_key` + `aliases[]` alongside. **No URL, no path, no page name changes** — every existing wiki link and `published.json` URL is preserved. New frozen plans use `plan/<date>-<slug>` going forward.
3. **Backfill `truth_state`**: computed from §6.2 rules; written to sidecar (frozen) or live frontmatter.
4. **Seed relationships**: derive `produces/belongs-to/targets/snapshot-of` from existing fields (`items`, `parent`, `milestone`, `roadmap_snapshot`, `supersedes`). Propose (not auto-write) `decides/implements/verified-by/lands-in` edges into `.work/suggestions.jsonl` (reuse the classifier's propose-only channel, spec §12) for the agent/human to confirm — propose-only, never silent.
5. **Generate the first index set**: `worklog ia-index` → `_inventory.json`, `_graph.json`, `publish-manifest.json`, `aliases.json`, rendered Home/Sidebar/indexes.
6. **Extend `wiki-publish`** to consume the manifest; do a one-time publish of the new generated pages (Home, Sidebar, indexes). Existing pages republish only if their `source_hash` changed (ledger hash-skip, §9.3) — so this is quiet for unchanged docs. Only `docs/.index/rendered/*.md` and manifest-listed sources are published; raw `.index` JSON/YAML/sidecars are excluded.
7. **Add CI gates** (§13) as warn-only for one release cycle, then promote to hard fail.
8. **Cut a release** with the release skill; the extended release flow republishes Home/Indexes and stamps `release` on snapshot/design sidecars.

### 14.3 Link-preservation guarantees

- **No frozen file is moved or renamed.** All `published.json` URLs remain valid.
- **`wiki_key` is seeded from the existing ledger key**, so the identity readers already implicitly use becomes explicit — no redirect table needed for the formalization itself.
- **A legacy-alias map** (`docs/.index/aliases.json`, internal) records each legacy key → `wiki_key`/`canonical_key` so any *future* rename is redirect-safe: if a `wiki_key` or page name ever changes, the old key maps to the new one and `ia-render` emits a redirect page (GitHub Wiki supports this as a stub page with a link; Confluence/ADO support native moves). This is forward-looking insurance, not required for the initial migration.
- **Broken-link check** (§13) catches any drift between rendered pages and the ledger during the migration window.

---

## 15. Phased implementation roadmap

Phased so each phase is independently useful and ships behind the green-gates loop (ADR-0003). Each phase is a captured plan (`docs/plans/<date>-<slug>.md`) with its own items, exactly as the repo already works.

### Phase 0 — Foundations (no behavior change)
- `schema/doc.schema.json` (unified frontmatter, per-type subsets) + stdlib validator.
- `worklog wiki-key <path>` + `worklog ia-inventory` (read-only).
- Migration record `0002-ia-content-model.md`.
- **Outcome:** a content inventory exists; nothing is published differently.

### Phase 1 — Identity & truth_state
- `worklog ia-normalize` (additive; sidecar for frozen, in-place for live).
- Backfill `wiki_key` + `truth_state` across all docs.
- CI gate: every doc has a `wiki_key`; no duplicates (warn → hard).
- **Outcome:** stable identity and current/history labeling everywhere; ADRs/plans/status/designs all self-describe.

### Phase 2 — The reader plane
- `worklog ia-render` (Home, Sidebar, banners) + `worklog ia-manifest`.
- Extend `wiki-publish` to consume the manifest; publish Home + Sidebar + doc banners.
- Replace hand-maintained `docs/wiki-home.md` with generated Home (keep an editable intro paragraph).
- **Outcome:** question-driven navigation on GitHub Wiki; readers see truth banners.

### Phase 3 — Indexes
- Decisions, Releases, Status Archive indexes.
- `worklog ia-index` wired into `release` and `plan-capture`.
- **Outcome:** Q3/Q4/Q-status answered by generated pages.

### Phase 4 — Traceability
- `worklog ia-graph` + edge taxonomy; `worklog link-pr`; `worklog trace-check`.
- Traceability Index page (`index/traceability`).
- Propose-only edge seeding via `.work/suggestions.jsonl`.
- CI: nightly warn, pre-release strict.
- **Outcome:** full bidirectional evidence chain, validated.

### Phase 5 — Hardening & cross-platform
- Promote all IA CI gates to hard fail.
- `ia-render` platform adapters for GitLab/ADO/Confluence sidebars.
- `/worklog:find` search; optional glossary index.
- **Outcome:** portable, CI-locked IA across wiki platforms.

---

## 16. Trade-offs, risks, and priorities

### 16.1 Trade-offs

| Decision | Trade-off accepted |
|---|---|
| **Sidecar metadata for frozen docs** (vs. editing them) | Two places to read a doc's metadata (artifact + sidecar). Chosen to honor invariant §15.8/§15.9 — editing a frozen status report to add a field is exactly the failure the spec exists to prevent. The inventory/validator join them. |
| **Generated Home/Sidebar** (vs. hand-curated) | Less editorial control on the landing page. Chosen because the hand-maintained `wiki-home.md` is already growing stale-prone (10 snapshots listed by hand). Generation is the only scalable answer; a one-paragraph editable intro preserves voice. |
| **Logical IA, rendered per platform** (vs. one native structure) | A rendering adapter layer to maintain. Chosen because the repo is already multi-platform (github-wiki now; ADO/GitLab/Confluence are "config away"); one logical model + adapters is the existing edge philosophy (ADR-0002). |
| **`wiki_key` == existing ledger key** (vs. a new UUID) | No new identity scheme to learn or migrate. Chosen because the ledger key is already the de facto identity and is path-independent; introducing a new ID would break the ledger without benefit. |
| **Propose-only edge seeding** (vs. auto-writing `relates_to`) | Slower traceability completeness. Chosen to match the `classify` skill's propose-only discipline (spec §12) — silent auto-linking of "verified-by" could fabricate false evidence; confirmation keeps the chain trustworthy. |
| **Keep `docs/` storage layout unchanged** (vs. `current/` vs `history/` split) | The reader's path doesn't literally say "current". Chosen because moving frozen files breaks every published URL and `plan`/`roadmap_snapshot` reference; the `truth_state` banner + generated sidebar deliver the current/history distinction without moving anything. |

### 16.2 Risks

- **Render drift on flat wikis.** GitHub Wiki is flat; prefix-based grouping can collide or become ugly as pages grow. *Mitigation:* the sidebar is generated and paginated; a naming convention (`Plan-…`, `ADR-…`, `Index-…`) is enforced by the validator.
- **Sidecar/ledger divergence.** Two sources of metadata could drift. *Mitigation:* `ia-normalize --check` and manifest↔ledger CI gates; the sidecar is the single writer for frozen-doc metadata and is itself freshness-checked.
- **Traceability false confidence.** A `verified-by` link that points at a test that doesn't actually cover the behavior is worse than no link. *Mitigation:* propose-only seeding + `trace-check` verifies the test file/symbol exists; behavior coverage stays a human judgment (and is flagged as such).
- **Scope creep into the UI dashboard.** The `wiki-ticket-ui` plan already envisions many of these panels. *Mitigation:* this design exposes everything as `worklog` commands + JSON artifacts, so the UI consumes the same generated data rather than reimplementing it — consistent with that plan's "never reimplement worklog semantics" rule.
- **Migration noise.** Backfilling could touch many files. *Mitigation:* frozen docs are touched only via sidecar (no artifact edits); live edits are additive only; the one-time publish is quiet because the ledger hash-skips unchanged pages.

### 16.3 Priorities (if shipping incrementally)

1. **Phase 0 + 1** (identity, `truth_state`, inventory) — highest value, lowest risk; immediately makes "is this current?" answerable and gives the UI/search a stable key. Do first.
2. **Phase 2 + 3** (reader plane + indexes) — the visible payoff; answers Q1–Q4 on the wiki.
3. **Phase 4** (traceability) — the differentiator for an SDD system; ships once identity is stable.
4. **Phase 5** (cross-platform hardening) — only when a second wiki platform is actually adopted.

The single highest-leverage action is **formalizing `wiki_key` and `truth_state`** (Phase 1): it is a pure formalization of what the ledger already does, it preserves every link, and every later phase depends on it.

---

## Appendix A — Mapping design goals → sections

| Design goal (from the brief) | Section |
|---|---|
| 1. Question/JTBD-driven IA | §3 |
| 2. Current Truth vs Historical Evidence | §6 |
| 3. Formal content model (types, lifecycle, ownership) | §4 |
| 4. Bidirectional traceability | §9 |
| 5. Scalability as artifacts accumulate | §7, §8, §15 |
| 6. Compatibility with existing invariants | §1.3, §2, §5.6, §14 |
| 7. Cross-wiki-platform support | §7.2, §10 |
| Implementation constraint (skills/CLI/hooks only) | §12, §15 |
| Existing strengths preserved | §1.3 (all) |

All external best-practice sources (IA four systems, Diátaxis, bidirectional traceability, W3C PROV-DM, ADR lifecycle) are cited inline where used in §2, §3, §9.4, and §9.6. Repo-internal references (spec sections, ADRs, skills, CLI, ledger) point to files in `SpillwaveSolutions/wiki_ticket_sdd` at `main`, inventoried in §1.

---

## Tasks

- [ ] (P1) Phase 0: schema/doc.schema.json unified frontmatter schema + stdlib validator (adr.schema.json pattern)
- [ ] (P1) Phase 0: worklog wiki-key + worklog ia-inventory (read-only) + migration record docs/migrations/0002-ia-content-model.md
- [ ] (P1) Phase 1: worklog ia-normalize — sidecars for frozen docs, in-place for sanctioned-live; backfill wiki_key (ledger-seeded) + truth_state
- [ ] (P1) Phase 1: CI gates — wiki_key present/unique, schema-valid frontmatter (warn one cycle, then hard)
- [ ] (P2) Phase 2: worklog ia-render + ia-manifest — generated Home, Sidebar, publish-time truth banners in docs/.index/rendered/
- [ ] (P2) Phase 2: extend wiki-publish to consume publish-manifest.json; replace hand-maintained wiki-home.md with generated Home
- [ ] (P2) Phase 3: generated indexes — Decisions, Releases, Status Archive; wire ia-index into release + plan-capture skills
- [ ] (P3) Phase 4: ia-graph typed-edge taxonomy + link-pr + trace-check + Traceability Index; propose-only edge seeding via suggestions.jsonl
- [ ] (P3) Phase 5: promote gates to hard fail; platform render adapters (GitLab/ADO/Confluence); /worklog:find + glossary
