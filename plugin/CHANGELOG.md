# Changelog

## 0.17.1 — unreleased

- **Fix** (`bin/worklog`): `close`, `update` and `link` wrote their event under
  whatever id string the caller passed. Handed the 8-character prefix that
  `worklog show` and `worklog list` themselves print — the form the docs
  recommend — they appended an event under that short id, which folds into a
  brand-new phantom item while the real one goes untouched. `update` was worse:
  its current-state lookup returned `{}` for a prefix, so the taxonomy rules ran
  against `level=None` and the "closed items need `reopen`" guard never fired.
  All three now resolve through one shared `_resolve()` — the same lookup
  `reopen`/`resolve`/`show` already used — and an ambiguous prefix errors with
  the candidate ids instead of silently taking the first match. This repo's own
  log carries the scar: `01KYA8MD` is a ghost item minted exactly this way, and
  `trace-check`/`sync` have been skipping it as orphan drift ever since.
- **Fix**: the session-start doctor compared `core.hooksPath` against the
  literal string `hooks`, so a repo wired with the absolute path — the form that
  actually works from a git worktree, where a relative path resolves against the
  wrong CWD — was reported broken at the top of every session. Both doctors now
  accept any path resolving to the repo's own `hooks/`.

## 0.17.0 — 2026-07-27

- **New**: `docs/graph-engineering.md` — declares and evidences (real
  file:line citations, not marketing copy) that this repo already has the
  four "graph engineering" primitives: ULID node identity, `ia_graph.py`'s
  typed edges, `fold.py`'s event-sourced persistent state, and a modest
  inventory/publish-manifest index. Two diagrams, a short forward-looking
  section, and a matching README callout.
- **Fix** (`bin/worklog plan-capture`): the overwrite guard checked only
  `docs/plans/<today-UTC>-<slug>.md`, so it enforced "plans are never
  rewritten" only when the dates happened to line up — a plan captured in
  the evening from a timezone behind UTC could silently duplicate under
  tomorrow's date. The guard is now slug-scoped across all dates. Found and
  fixed upstream from a real incident in a downstream repo (PR #198).
- **Fix**: the slug-scoped guard's first pass used a bare `*-<slug>.md`
  glob, which matched by suffix rather than field boundary (a search for
  slug `migration` would also match `database-migration`) — caught in
  review before merging PR #198, now anchored on the fixed date shape.
- **Fix**: generated wiki Home linked `[[Design-Doc]]` but not its
  `[[Code-Walkthrough]]` pair, leaving walkthroughs unreachable from Home.

## 0.16.1 — 2026-07-26

Post-tag doc sync and a real bug fix for v0.16.0, landed on `main` after the
tag per the release process (docs and fixes never block a tag, they follow
it):

- **Fix**: `bin/sync_dispatch.py` crashed with `KeyError: 'key'` when a
  closed item that was never pushed to the tracker got forced into sync
  scope via `--keys` — the closed-item branch assumed a remote key already
  existed. It now creates the ticket first, links it, then closes, mirroring
  how the open-item branch already handles create-vs-update.
- Design doc and code walkthrough regenerated and frozen for v0.16.0.
- `docs/user_guide/plugin-guide.md` and `README.md` updated for the new
  `integration-guide` skill.

## 0.16.0 — 2026-07-26

Wiki-driven integration guides (plan
`docs/plans/2026-07-25-wiki-driven-integration-guides.md`, epic #164): a new
`integration-guide` skill points users at living, wiki-hosted setup guides
for tools this repo doesn't ship adapter code for, instead of hard-coding
that knowledge into the skill set.

- **New skill** `integration-guide`: on mention of Superpowers, GSD,
  SpecKit, OpenSpec, Jira, Confluence, GitHub, GitLab, Azure DevOps, AWS
  CodeCatalyst, or Google Cloud DevOps, fetches the matching
  `Integration-<Name>` wiki page, verifies it's the real page (a GitHub
  wiki redirects a missing slug to Home instead of 404ing — a naive
  fetch-succeeded check would be fooled by this), and falls back to a
  local copy under `docs/integrations/` if the fetch fails or fails
  verification. No new adapter or fetch code — built on `WebFetch` plus
  the existing `worklog wiki-add`/`wiki-publish` mechanism.
- **11 integration pages** (`docs/integrations/fallback-*.md`, published to
  the wiki): one fixed 10-section template per system. Only GitHub has a
  real, shipped adapter — the other six ticket/wiki systems are documented
  honestly as agent-researched-at-runtime, matching `ticket-sync`'s
  existing ADO-caveats tone; the four SDD tools are framed as
  compositional guidance, not technical integration, since nothing in this
  repo wires to them today. Jira and Confluence require reusing the
  existing `jira`/`confluence` skills rather than raw REST calls;
  Confluence additionally requires converting Mermaid/PlantUML diagrams to
  images before upload.
- **Meta index** at `docs/integrations/README.md` / wiki page
  `Integrations`, linking all 11 pages.

## 0.15.1 — 2026-07-25

- Doc fix: user-guide miscounted branch-discipline hook checks ("two more
  pre-commit checks" → "two more checks" — one is `pre-commit`, the other
  is the separate `commit-msg` hook). Found by `/code-review` (#160).

## 0.15.0 — 2026-07-25

Branch-discipline hooks (plan `docs/plans/2026-07-25-branch-discipline-hooks.md`):
main is now pull-only, and every commit must be traceable to a worklog item
or ticket.

- **Branch guard** (`hooks/pre-commit`): rejects a commit authored directly
  on `main`/`master`. Exempt for a real reconciliation merge (`git merge
  origin/main`) via `WORKLOG_MERGE_COMMIT`, set by `pre-merge-commit` before
  it exec's into `pre-commit` — `MERGE_HEAD` is not yet on disk at the point
  git invokes `pre-merge-commit` (only appearing later, before `commit-msg`
  fires), so a MERGE_HEAD-only check would have missed this case.
  `WORKLOG_SKIP_BRANCH_GUARD` covers the handful of existing bare
  (non-commit) invocations of this script (`worklog doctor`, CI's
  `--no-verify` backstop) that would otherwise false-positive on `main`.
- **`hooks/commit-msg`** (new): requires a 26-char Crockford ULID or a
  `#123` ticket reference in every commit message; exempt for merge
  commits.
- Wired end-to-end: `worklog init`'s hook-copy loop and CI template,
  `worklog uninstall`, `worklog doctor`'s health check, and a new
  PR-scoped CI step validating every commit message in the PR range.
- `release` skill's "direct-commit repos" landing mode removed — dead once
  this ships; releases land as a PR like everything else now.

## 0.14.0 — 2026-07-24

Artifact-pages epic (plan `docs/plans/2026-07-24-artifact-pages.md`): the IA
content model now covers tickets, PRs, and releases, not just docs.

- **Ticket pages** (`worklog ia-render` → one page per work item under
  `docs/.index/rendered/tickets/`): own description/status, upward hierarchy
  to the epic, downward children with an aggregate progress rollup, linked
  PRs, linked release — `render_item_page()`, branching by level rather than
  four near-duplicate renderers. New `worklog ia-ticket <ULID>` preview
  command.
- **Release pages**: a Change Log section derived from the graph
  (milestone-tagged closed items plus their linked PRs), not a
  `CHANGELOG.md` parser — this file stays human-authored prose. Plus a
  Release Tree, Related PRs/Tickets, and Dependencies & Risks.
- **PR pages**: linked tickets, related release, traceability back to the
  root epic. Files-changed/review/CI status render as "not tracked" —
  fetching live PR metadata is scoped out to a separate follow-up
  (`worklog pr-sync`, not built in this release).
- Published-page manifest grew from 51 to 252 entries.
- Two bugs found while building this, filed but not yet fixed: `worklog
  close`/`update` don't resolve item-id prefixes the way `reopen` does
  (a short, valid prefix silently creates an orphan item instead of
  resolving to the real one); the reader-plane `banner()` mislabels every
  frozen "current" doc as a status report regardless of its actual
  `doc_type` (verified live on 12 of 14 published plan pages).

## 0.13.0 — 2026-07-23

IA & content model wave (plan `docs/plans/2026-07-22-ia-content-model.md`,
PR #104) plus follow-on schema and reliability fixes. Wiki-ticket UI tracking
moved to `wiki_ticket_sdd_ui` and is not shipped in this plugin.

- **Doc identity & schema (Phase 0):** unified `schema/doc.schema.json`,
  `worklog wiki-key`, `worklog ia-inventory`, migration helpers for stable
  `wiki_key` / `truth_state` frontmatter.
- **Normalize + warn gates (Phase 1):** `worklog ia-normalize` writes sidecars
  for frozen docs and in-place frontmatter for live ones; CI/hooks warn on
  missing/duplicate `wiki_key` and invalid frontmatter (hard-fail deferred to
  Phase 5).
- **Reader plane (Phase 2):** `worklog ia-render` + `ia-manifest` generate
  Home, Sidebar, and `publish-manifest.json`; wiki-publish consumes the
  manifest and strips YAML frontmatter at publish time so GitHub Wiki pages
  stay clean.
- **Indexes (Phase 3):** generated Decisions / Releases / Status Archive
  indexes wired into release and plan-capture flows.
- **Traceability (Phase 4):** typed-edge graph (`ia-graph`), `worklog link-pr`,
  `worklog trace-check` (warn by default, `--strict` pre-release), rich
  ticket bodies via `worklog ticket-body`.
- **Schema boundary (PR #112):** split document schema from entity/item
  schema — documents vs work items no longer share one overloaded schema.
- **Skills:** new `issue-description` and `pr-description` skills for
  durable ticket and PR prose.
- **Fixes:** pre-commit no longer dirties the tree with `bin/__pycache__`
  (`PYTHONDONTWRITEBYTECODE`); compaction snapshot writes folded state
  verbatim so closed orphans no longer abort verify; ticket bodies required
  and readable for junior devs/PMs (spec §13.4); `init.sh` installs IA
  modules; classify skips folder READMEs under plans/status/adr.

## 0.12.1 — 2026-07-21


- Dirty close syncs fields first: the dispatcher now pushes an `update`
  before the `close` verb when a closing item's hash is dirty, so remote
  labels/milestone/title match the final local state. Previously a
  reclassify-then-close left stale remote taxonomy labels that the next
  pull re-ingested over the local edit (#76).

## 0.12.0 — 2026-07-21

- Pull sync ingests taxonomy: the dispatcher's `INGEST_FIELDS` gains
  `level`/`kind`/`milestone`, so remote taxonomy edits (labels, milestone)
  land in the local log instead of being silently dropped. The GitHub
  adapter already round-tripped them; the dispatcher tuple was the gap.
- `worklog reopen <ulid>`: emits the `reopen` op the fold always supported —
  moves a closed item back to `todo` and drops the stale `resolution` in one
  event. `update --status` on a closed item is now refused with a pointer to
  `reopen` (the old path left the resolution behind).
- `sync.conflict_policy` descoped to `report` only: `local-wins` /
  `remote-wins` were documented but never read by the dispatcher, and
  `report` + `worklog resolve` covers the need without silent overwrites.
  Config and spec updated; auto-resolve returns only via a new plan.
- First release exercising the design-docs release-time doc sync
  (`release.sync_docs`) end to end.

## 0.11.0 — 2026-07-19

- System enums widened and documented as advisory (spec v1.8): ticketing
  `github | gitlab | jira | ado | linear | codecatalyst | other | none`, wiki
  gains `gitlab-wiki` and `other`. `bin/worklog` branches only on `none`;
  every other value is a name the edge skills resolve to available tooling,
  and `other` is the sanctioned value for unlisted systems (real name in
  `options:`).
- Caveats ride with the names in ticket-sync: AWS CodeCatalyst (ADO's AWS
  equivalent) closed to new customers 2025-11-07; Linear detected via
  CLI/MCP, not git remotes; GCP has no native tracker — no `gcp` value.
- Azure DevOps field-tested caveats in ticket-sync + adapters/README: tag
  markers (ADO strips HTML comments), merge-never-overwrite updates,
  link-first migration with the `sync --dry-run` 0-creates gate.
- /worklog:init: detection knows codecatalyst.aws and CLI/MCP-only trackers;
  pick-and-mix lists gain Linear, CodeCatalyst, and `other`.

## 0.10.0 — 2026-07-19

- Stop hook: untracked files no longer count as unrecorded work (-uno) — the
  actual root cause of the false blocks; #46's settle guard kept as hardening.
- Stop hook: settle-and-recheck + branch-stability guard — no more false blocks
  when a background merge chain flips branches mid-invocation (observed 3x).

## 0.9.0 — 2026-07-19

- Mermaid visual roadmap: `roadmap-render --viz=deps,hierarchy,gantt|all|none`
  (default deps,hierarchy; `--no-viz` alias) appends a generated
  "## Visual roadmap" section — dependency graph, hierarchy, and an
  event-dated gantt whose bars come from create/first-in_progress/close ULID
  timestamps (historical fact, no invented dates; "now" = max event, never
  wall clock). `/worklog:viz` regenerates with `--viz=all` in a background
  subagent and republishes the roadmap.
- Grok Build: PORTS.md/README/plugin-guide upgraded to full native
  compatibility, zero configuration, per the xAI docs (verification under
  Grok Build pending).
- features.auto_merge_on_green flag (default ON): advisory mode polls, reports
  green, and leaves the merge to a human; --auto/--advisory and
  WORKLOG_AUTO_MERGE override per run; doctor reports it.
- CLI rejects empty item ids (update/close/link/ingest/conflict/resolve/show).

## 0.8.0 — 2026-07-19

- Architecture Decision Records: schema-validated docs/adr/ (worklog adr
  new|list|check, pre-commit/CI guard), write-once bodies with sanctioned
  status/superseded_by mutation, wiki-synced with republish-on-change.
  Seeded with ADR-0001..0003 from the project's real decisions.
- Dispatcher: orphan/untitled items are drift-reported, never pushed.

## 0.7.0 — 2026-07-19

- Work taxonomy (plan 2026-07-18): four orthogonal axes — level (epic/story/task/
  subtask), kind (feature/bug/ops/triage, triage is the visible default), milestone
  (the release axis), planned/unplanned. Legacy `type` is a deprecated alias the
  fold normalizes and compaction migrates physically. Canonical hash gains the new
  fields (one-time sync churn).
- CLAUDE.md taxonomy block (marker-idempotent, consented at /worklog:init; AGENTS.md
  symlink carries it to every harness). Inline item proposals are the default path.
- Flag-gated classifier (off by default): Stop hook gains a propose-only mode, the
  classify skill stages suggestions in .work/suggestions.jsonl, `worklog promote`
  is the only path from suggestion to log.
- Roadmap: Needs-classification queue, kind mix per epic, milestone grouping with
  derived epic milestones. Adapters map kind→labels and milestone→GitHub milestones.
- Spec v1.7; migration doc; pre-commit/CI enforce taxonomy rules; README + user
  guide fully refreshed (no stub-era language remains).

## 0.6.0 — 2026-07-19

- Green-gates merge policy: /worklog:merge + merge-green skill + merge-when-green.sh
  poll loop (5-min default) — PRs merge only when every check passes; never bypass.
- Typed adapter contract (plan 2026-07-18): bin/sync_dispatch.py owns every sync
  invariant (capabilities gate, scope, create-vs-update, marker idempotency, echo
  suppression, §3.6 exit-code handling, conflicts, drift report); adapters are dumb
  translators — shipped fake (CI double) + github worked example; worklog adapter
  init|check; worklog sync is real — no stubs remain.
- Spec v1.6: §8.1 hosted-platform merge caveat + recovery; §9.5 typed contract layer.
- CI coverage gate: >=80% enforced on bin/*.py, target 95% (CLAUDE.md policy).
- ticket-sync skill delegates invariants to the dispatcher; per-system notes moved
  to adapters/README.md.

## 0.5.0 — 2026-07-18

- release skill: cutting a release is a wiki-ticket capability (stamp,
  snapshot, tag, platform release, publish, sync).
- Pull sync: `worklog ingest` (deterministic ev per spec §10.2 — identical polls
  dedupe across clones), `worklog conflict`, `worklog resolve --take local|remote`;
  fold clears conflicts when a later event writes the field. ticket-sync is now
  push AND pull with §10.3 echo suppression.
- Spec v1.5: adapter strays purged; pull CLI documented; §18 step 8 done.
- wiki-publish: per-system guidance (GitHub/GitLab/ADO/Confluence) + ledger field
  semantics across systems.
- Harness ports: /worklog:init scaffolds the AGENTS.md symlink; plugin/PORTS.md
  matrix — Codex/OpenCode work today with zero port.

## 0.4.0 — unreleased

- Compaction (`bin/compact.py`, `worklog compact --yes`) per spec §7 with fold-equality
  verification; nightly CI job commits `chore(worklog): compact through <watermark>`.
- `worklog status --kind daily|weekly` (`--emit-facts` / `--write`, frozen reports) +
  status-report skill. Timecard deferred on spec §17 open question 4.
- ticket-sync closes remote tickets when local items close (external.dirty scope).
- plan-capture publishes tickets + wiki via a background subagent — never blocks.
- Spec v1.4: §9 rewritten to skill-based edges.

## 0.3.0 — unreleased

- `worklog link`: attach external identities to work items via §5.3 link events.
- `worklog wiki-add`: register documents in the wiki publish set.
- ticket-sync skill: push-only sync to external trackers with ULID-marker
  idempotency; GitHub via `gh`, system-vague guidance elsewhere.
- /worklog:init system detection: confident yes/no path, multi-select
  pick-and-mix, upgrade skip.
- wiki-publish: default publish set + `source` field in the ledger.

## 0.2.0 — unreleased

- `worklog roadmap-snapshot` subcommand.
- `wiki-publish` skill: system-agnostic wiki publishing with a `published.json` ledger.
- Dogfood enforcement hooks: UserPromptSubmit reminder, Stop worklog check,
  SessionStart doctor-lite.
- Plugin installer/uninstaller scripts.
- User guide + README; docs live in the repo/wiki, deliberately NOT packaged
  in the plugin.

## 0.1.0 — unreleased

- Plugin scaffold: manifest, design captured as tracked work items
  (`docs/plans/2026-07-18-claude-plugin.md` in the source repo).
- `worklog --version`; version recorded in scaffolded repos and checked by `/worklog:doctor`.
