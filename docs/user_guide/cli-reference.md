---
doc_type: guide
slug: cli-reference
title: WikiTicket SDD — CLI Reference
truth_state: current
wiki_key: cli-reference
---
# WikiTicket SDD — CLI Reference

Complete reference for `bin/worklog`. For concepts and workflows, start with
the [User Guide](user-guide.md); for the Claude Code plugin, see the
[Plugin Guide](plugin-guide.md).

## Global flags

| Flag | Meaning |
|---|---|
| `--actor <name>` | Who caused the event (defaults to `$USER`). Recorded on every event; goes **before** the subcommand: `bin/worklog --actor alice update …` |
| `--version` | Print the CLI version and exit |

## Item ids

Every command that names an existing item — `update`, `close`, `link`,
`unlink`, `reopen`, `resolve`, `show` — accepts either the full 26-char ULID or any
**unambiguous prefix**, such as the short id `list` and `show` print. The
prefix is resolved to the real item before anything is written: an ambiguous
prefix is refused and the matching ids are named
(`worklog: 01KY is ambiguous — matches …`), and a prefix that matches nothing
is refused (`worklog: no item matching …`) with no event appended.

The machine-facing `ingest` and `conflict` subcommands still take the full
ULID — the sync dispatcher passes ids it already resolved.

## Subcommands

### add

Create a work item. Prints the new item's ULID.

```bash
bin/worklog add "Extract auth middleware" --level task --kind feature \
    --milestone v0.7.0 --priority P1 --parent 01J8WZZ100 --labels backend,auth
```

| Flag | Values | Default |
|---|---|---|
| `<title>` | positional, required | — |
| `--level` | `epic` `story` `task` `subtask` | `task` |
| `--kind` | `feature` `bug` `ops` `triage` | omitted — the item folds to `triage` |
| `--milestone <m>` | free string (e.g. `v0.7.0`) | none |
| `--type` | **deprecated** alias for `--level`/`--kind` | — |
| `--priority` | `P0` `P1` `P2` `P3` | `P2` |
| `--parent <ulid>` | parent item (bugs may float free of any epic) | none |
| `--plan <path>` | plan doc that produced it | none |
| `--labels a,b` | comma-separated | none |
| `--unplanned` | flag; requires `--discovered-during` | — |
| `--discovered-during <ulid>` | what the unplanned work interrupted | — |

Taxonomy rules are checked at write time
(see [the work taxonomy](user-guide.md#the-work-taxonomy)):

- Omitting `--kind` is deliberate: the fold classifies the item `triage` —
  it never silently becomes `feature`.
- `--level epic --kind bug` (or `triage`) fails:
  `worklog: an epic cannot be kind:bug — epics are feature or ops (taxonomy §2.2)`
- `--level epic --milestone …` fails:
  `worklog: milestone lives on leaves; epic milestones are derived (taxonomy §2.5)`
- `--unplanned` without `--discovered-during` fails:
  `worklog: --unplanned requires --discovered-during (section 5.4)`
- `--type` still works — it maps to the same (`level`, `kind`) pair the fold
  applies to old events (`bug` → `task`/`bug`, the rest → `feature`) and
  prints on stderr: `worklog: --type is deprecated; use --level/--kind`.
  See [the migration note](../migrations/0001-type-split.md).

### update

Change status, priority, title, kind, milestone, body, or labels on an open
item.

```bash
bin/worklog update 01J8X0M2QQ --status in_progress --kind bug --add-label urgent
bin/worklog update 01J8X0M2QQ --body "What and why a junior dev/PM can read"
```

| Flag | Values |
|---|---|
| `<item>` | positional ULID or unambiguous prefix, required |
| `--status` | `todo` `in_progress` `blocked` |
| `--priority` | `P0`–`P3` |
| `--title` | new title |
| `--kind` | `feature` `bug` `ops` `triage` |
| `--milestone <m>` | free string |
| `--body` | human-readable description (what/why; no ULIDs — spec §13.4) |
| `--add-label a,b` / `--del-label a,b` | comma-separated |

At least one change flag is required. `--kind`/`--milestone` are validated
against the item's current level with the same taxonomy rules (and error
messages) as `add` — you cannot update an epic to `kind:bug` or put a
milestone on it. `--status` on a closed item is refused — it would leave
the stale resolution behind; use `reopen`. `--body` is the durable prose
source that `ticket-body` and ticket-sync push to the remote tracker.

### close

Close an item as done or cancelled.

```bash
bin/worklog close 01J8X0M2QQ --status done --resolution "merged in PR #7"
```

`--status` is `done` (default) or `cancelled`; `--resolution` is optional
free text. Closing is just an event — nothing moves files at runtime.

### reopen

Reopen a closed item: moves it back to `todo` and drops the stale
`resolution` in one event. Prints the full ULID. Refuses items that aren't
closed.

```bash
bin/worklog reopen 01J8X0M2QQ
```

### link

Attach an external identity (ticket key, URL) to an item as a link event.
Sync calls this for you; it's here for manual wiring.

```bash
bin/worklog link 01J8X0M2QQ --system github --key "owner/repo#412" --url <url>
```

`--system` and `--key` are required; `--url`, `--rev`, `--hash` optional.

**One item per ticket.** `link` refuses a key another item already owns, and
names that item so you can see which one is real:

```
worklog: ado:294 already belongs to 01KYA99TVCGX79HFNHN1DVT7Y6
  ('T1.4 Mike MVP page list') — two items owning one ticket makes every sync
  overwrite it with whichever changed last (github#226).
```

The check ignores status: a *cancelled* owner still counts, because sync pushes
a full update against its key and then closes the ticket — that is how a
duplicate marked a live ticket Done. Re-linking an item to the key it already
owns is fine (that is how you add a `--url` later).

`--force` skips the check. Prefer `unlink` then `link` for a deliberate move:
after `--force` the previous owner still holds the key, so sync will skip both
until you unlink it.

### unlink

Retract a link. Use it when an item was pointed at the wrong ticket — this is
the supported undo for `link`.

```bash
bin/worklog unlink 01J8X0M2QQ
```

The item stops owning the ticket, which frees the key for another item. What
happens on the next sync:

| The unlinked item is… | Next sync |
|---|---|
| open | files a **new** ticket for it — it genuinely owns none now |
| closed or cancelled | inert; never pushed, never re-created |

Repairing the log does not repair the tracker. Two things to do by hand:

- the ticket may still carry the `worklog:<ulid>` marker (trackers that merge
  tags rather than overwrite keep both), so remove it there;
- run `bin/worklog sync --keys <key>` to push the surviving owner back over the
  damage. Nothing else will: an item's change detection is content-based, and
  the surviving owner's content never changed.

### ingest

Record a remote-originated change (pull side). The event ID is
deterministic — built from `--system/--key/--rev` — so identical polls
dedupe across clones. Accepts `level`, `kind`, and `milestone` (plus
status, priority, title, …) in `--set FIELD=VALUE`. Normally the sync
dispatcher runs this, not you.

```bash
bin/worklog ingest 01J8X0M2QQ --system github --key "owner/repo#412" \
    --rev 2026-07-18T16:02:11Z --rev-ts-ms 1789142531000 --set status=in_progress
```

### conflict

Record a sync conflict on a field (the dispatcher emits these when local
and remote both changed). The fold files it under `_conflicts` until a
later write clears it. Flags: `--field`, `--local`, `--remote`,
`--remote-rev`, all required.

### resolve

Resolve the last open conflict on a field:

```bash
bin/worklog resolve 01J8X0M2QQ --field status --take local
```

`--take local` re-asserts the local value; `--take remote` accepts the
remote one. Either way it's a normal update event that outsorts the
conflict, so the fold clears it. Open conflicts surface in `worklog list`
(stderr warning), `worklog show`, and the status report.

### wiki-add

Register a document in the wiki publish set used by the wiki-publish skill.

```bash
bin/worklog wiki-add docs/plans/2026-07-18-work-taxonomy.md \
    --key work-taxonomy --title "Work taxonomy plan"
```

### list

List open items, sorted by priority. `--all` includes closed ones.

```bash
bin/worklog list --all
```

Output: short id, priority, status, external key (or `-`), title. Prints a
warning to stderr if any items carry unresolved sync conflicts.

### show

Print one item's full folded state as JSON.

```bash
bin/worklog show 01J8X0M2
```

### fold

Print the full folded state of every item (open and closed) as JSON. The
read-only building block other tooling (like the plan-next skill) consumes.

```bash
bin/worklog fold
```

### promote

Promote a classifier suggestion from `.work/suggestions.jsonl` into exactly
one `create` event, then mark the suggestion consumed so it is never
re-proposed. The proposed `level`/`kind`/`milestone` are honored as
proposed (including `triage`) and pass the same taxonomy checks as `add`.

```bash
bin/worklog promote <suggestion-id>
```

See [the classifier](user-guide.md#the-classifier-off-by-default) — the
classifier is propose-only and off by default; `promote` is the only path
from a suggestion to the event log.

### plan-capture

Turn an approved plan into a frozen plan doc plus tracked items: one epic,
one item per `- [ ]` task under a `## Tasks` heading (indented checkboxes
become subtasks; a `(P0)`–`(P3)` token sets priority). Writes
`docs/plans/<YYYY-MM-DD>-<slug>.md` and prints the path and the epic ULID.

```bash
bin/worklog plan-capture --slug auth-refactor --title "Auth refactor" --file plan.md
```

| Flag | Meaning |
|---|---|
| `--slug` | required; kebab-case, becomes the filename |
| `--title` | required; the epic's title |
| `--file` | plan markdown (reads stdin if omitted) |
| `--priority` | epic priority, default `P1` |

Refuses if any `docs/plans/*-<slug>.md` already exists, for any date — plans
are never rewritten; pick a new slug to supersede.

### roadmap-render

Regenerate `docs/roadmap.md` from the log. Run it after any item change and
commit the roadmap together with the log.

```bash
bin/worklog roadmap-render
```

### roadmap-snapshot

Freeze the current roadmap as a dated snapshot:
copies `docs/roadmap.md` to `docs/roadmap/<YYYY-MM-DD>_<name>.md`.

```bash
bin/worklog roadmap-snapshot --name v0.2-roadmap
```

Snapshots are frozen — the command refuses to overwrite an existing snapshot
file. `docs/roadmap.md` stays the live, regenerated view; snapshots are the
"what did the roadmap say at release time" record.

### sync

Run ticket sync through the typed adapter contract. The dispatcher
(`bin/sync_dispatch.py`) owns every invariant — scope, canonical hash-skip,
create-vs-update, idempotency markers, echo suppression on pull, conflict
detection; the per-system adapter is a dumb translator (see `adapter`
below). No adapter configured → the run is local-only, which is a mode,
not an error.

```bash
bin/worklog sync --dry-run
```

| Flag | Meaning |
|---|---|
| `--dry-run` | Report what would happen; write nothing |
| `--keys k1,k2` | Restrict the run to specific external keys |
| `--push-only` / `--pull-only` | One direction only (mutually exclusive) |
| `--retry-base-delay <s>` | Base backoff for transient adapter failures |

Every run ends with the drift report — one counts line plus a `drift:` list
of anything a human should see (conflicts, unsupported fields on the
platform, deferred items, degraded mappings):

```
sync report: created=1 updated=2 closed=1 skipped=14 pulled=1 conflicts=0 deferred=0
drift:
  - fields not synced on github: depends_on
```

**Contested tickets are never pushed.** If more than one item claims the same
ticket, sync skips *those items* — the corruption needs both of them pushed —
finishes the rest of the run, and exits non-zero. It prints as its own block,
not a `drift:` line, and `--dry-run` fails the same way:

```
sync: 1 ticket(s) claimed by more than one item — NOT pushed (github#226)
  ado:294
    <- 01KYA99TVCGX79HFNHN1DVT7Y6  T1.4 Mike MVP page list
    <- 01KYMYTNJAWW89RB418CVSE049  AB#294 — MVP page-list sign-off
  the later link is usually the mistake:
    worklog unlink 01KYMYTNJAWW89RB418CVSE049
    worklog sync --keys 294   # re-push the surviving owner over the damage
```

Do run that last command. Unlinking the impostor does not by itself repair the
ticket: change detection is content-based and the surviving owner's content
never changed, so it stays out of scope until `--keys` forces it in.

### adapter

`bin/worklog adapter init` prints the authoring path for a new adapter:
adapters are *adapted* from the shipped worked example
(`adapters/github/adapter`), never written from scratch — read
`adapters/README.md`, have the model generate one for your
`ticketing.system`, then validate it. `bin/worklog adapter check [path]`
validates an adapter against the contract (`schema/*.schema.json`) in a
throwaway sandbox; nothing activates until `adapter check` is green. With
no path it checks the adapter for the configured system, falling back to
the shipped fake (the CI test double).

### adr

Architecture Decision Records in `docs/adr/NNNN-slug.md`, schema-validated
front matter (`schema/adr.schema.json`).

```bash
bin/worklog adr new "Green-gates merge policy" --status proposed \
  --deciders rick,claude --tags ci,process --supersedes 2
bin/worklog adr list
bin/worklog adr check
```

`adr new <title>` picks the next 4-digit number, scaffolds the file
(front matter plus Context / Decision / Consequences sections), registers it
in the wiki-publish ledger (key `adr/NNNN-slug`, page `ADR-NNNN-slug`,
republish-on-change), and prints the path. Flags: `--status` (default
`proposed`), `--deciders a,b`, `--tags x,y`, `--supersedes N`. `adr list`
prints an id / status / title table. `adr check` validates every ADR —
schema, unique ids, filename↔front-matter agreement, consistent
`supersedes`/`superseded_by` pairs, required body sections — and exits
nonzero naming each problem; the pre-commit hook runs it whenever
`docs/adr/` exists.

### status

Generate a status report from the log.

```bash
bin/worklog status --kind weekly --write
```

`--kind` is `daily`, `weekly`, or `timecard`. By default it prints;
`--write` saves `docs/status/<date>-<kind>.md` (frozen once published —
corrections go in the next report), `--emit-facts` prints the underlying
JSON facts, `--since`/`--until` override the window, `--dry-run` previews,
`--force` overwrites an unpublished draft.

### compact

Compact the event log per spec §7, verifying `fold(new) == fold(old)`
before writing. Requires `--yes`. Meant for CI (a nightly job on the main
branch), not day-to-day use — compaction is also what physically migrates
old `type` events to `level`/`kind`.

## Information architecture (IA) commands

These implement the IA & content model (plan
`docs/plans/2026-07-22-ia-content-model.md`, plugin 0.13.0) plus artifact
pages (plan `docs/plans/2026-07-24-artifact-pages.md`, plugin 0.14.0).
Storage paths stay the same; the commands add a **reader plane** — stable
`wiki_key` identity, `truth_state`, generated Home/Sidebar/indexes, a
generated page per ticket/PR/release, a publish manifest, and a typed-edge
traceability graph. Concepts are covered in
the [User Guide](user-guide.md#information-architecture--content-model).

### wiki-key

Print the stable `wiki_key` for a document path (legacy keys are seeded
from the publish ledger; new docs use the §5.5 derivation rules).

```bash
bin/worklog wiki-key docs/plans/2026-07-22-ia-content-model.md
```

`-v` / `--verbose` adds derivation detail.

### ia-normalize

Backfill `wiki_key` + `truth_state`: **sidecars** under `docs/.index/` for
frozen docs (never edits the frozen file), **in-place frontmatter** for
sanctioned-live docs, and self-description on the publish ledger.
Idempotent.

```bash
bin/worklog ia-normalize
bin/worklog ia-normalize --check   # report pending normalizations only
```

### ia-inventory

Generate `docs/.index/_inventory.json` — one metadata record per doc
(`wiki_key`, `doc_type`, `truth_state`, relationships).

```bash
bin/worklog ia-inventory
bin/worklog ia-inventory --check   # validate + freshness only
```

### ia-render / ia-manifest

Render the reader plane into `docs/.index/rendered/` (Home, Sidebar,
Decisions / Releases / Status / Traceability indexes) plus
`publish-manifest.json` and `aliases.json`. Deterministic.
`ia-manifest` is an alias of `ia-render`.

```bash
bin/worklog ia-render
bin/worklog ia-render --check      # report stale files instead of writing
```

The wiki-publish skill consumes `publish-manifest.json`: each page has a
`source`, `page_name`, and either `render: as-is` or `render: doc+banner`
(banner prepended at publish time, never written into frozen sources). For
GitHub Wiki, YAML frontmatter is stripped in the wiki copy so Gollum does
not show the `---` block.

### ia-index

Convenience wrapper: `ia-normalize` → `ia-inventory` → `ia-render`. Run
after plan-capture, release, or any doc set change that should refresh
navigation.

```bash
bin/worklog ia-index
```

### ia-graph

Build `docs/.index/_graph.json` — the typed-edge traceability graph
(plan → item → ticket → PR/commit → release, plus ADR/design edges).

```bash
bin/worklog ia-graph
bin/worklog ia-graph --seed   # propose decides/implements edges into
                             # .work/suggestions.jsonl (propose-only)
```

### link-pr

Record a PR or commit code edge on an item as a **sidecar overlay** (the
event log still owns item state). Prefer this over hand-editing richness
only on the remote ticket.

```bash
bin/worklog link-pr 01J8X0M2QQ --pr 104
bin/worklog link-pr 01J8X0M2QQ --commit abcdef1
```

### pr-sync

Fetch live PR metadata — state, review decision, a one-word check rollup,
merge time, and the changed-file list — into `docs/.index/pr/<N>.yml`, which
`ia-render` then reads when it writes the PR page. A PR that has never been
synced still renders, saying `not tracked`.

This is the **only** network step in the IA pipeline, and that is deliberate.
`ia-render --check` regenerates every page and byte-compares it, so a
renderer that called GitHub would flap against whatever the remote said that
minute. Fetch writes a committed file; render reads it.

```bash
bin/worklog pr-sync 104
bin/worklog ia-render          # the page now carries real state
```

Re-running overwrites the sidecar, so sync again after a PR merges to
capture its final state. The `--json` fields come straight from `gh pr view`,
so `gh` must be authenticated.

### ticket-body

Print the rich issue body for an item — summary, epic/plan/milestone
context, and traceability — for ticket-sync / the issue-description skill
to push. Enrich the **source** (`update --body`, `link-pr`, relationships)
and let sync carry it out.

```bash
bin/worklog ticket-body 01J8X0M2QQ
```

### ia-ticket

Preview the generated **ticket page** for an item — the same page
`ia-render` writes to `docs/.index/rendered/tickets/<ULID>.md` and publishes
as wiki page `Ticket-<ULID>`: own description/status, upward hierarchy to
the epic, downward children/subtasks with a progress rollup, linked PRs
(`PR-<num>`), and the linked release (`Release-<tag>`). Releases and PRs get
matching generated pages (`releases/<tag>.md`, `prs/<num>.md`) — there's no
separate preview subcommand for those, only for tickets.

```bash
bin/worklog ia-ticket 01J8X0M2QQ
```

### trace-check

Unlinked-evidence report: closed items missing plan / ticket / PR links.
Warns by default; `--strict` exits 1 (use pre-release).

```bash
bin/worklog trace-check
bin/worklog trace-check --strict
```

## Git hooks

Installed via `git config core.hooksPath hooks` (done for you by
`/worklog:init`). An absolute path to the same directory is equally valid and
is what a **git worktree** needs — a relative `hooks` resolves against the
worktree's own root. The session doctor accepts either form.

- **`hooks/pre-commit`** — on every commit:
  1. Every `.work/*.jsonl` file ends with a trailing newline (the invariant
     that keeps union merge safe).
  2. Every log line parses as JSON and carries the required event fields
     (`ev`, `ts`, `actor`, `op`, and `item` except on `compact` events).
  3. `docs/roadmap.md` is fresh: the hook regenerates it and diffs — a stale
     or hand-edited roadmap blocks the commit
     (`Run: worklog roadmap-render`).
  4. The fold test suite passes (only in repos that carry `tests/`).
  5. **Branch guard**: rejects a commit authored directly on `main`/`master`
     — those branches are pull-only, land work via a PR instead. A real
     reconciliation merge (`git merge origin/main`) is exempt via
     `WORKLOG_MERGE_COMMIT`, set by `pre-merge-commit` before it exec's into
     `pre-commit` (`MERGE_HEAD` isn't on disk yet at that point in git's
     merge sequence). `WORKLOG_SKIP_BRANCH_GUARD` covers the tool's own bare,
     non-commit invocations (`worklog doctor`, CI's `--no-verify` backstop)
     that would otherwise false-positive on `main`.
- **`hooks/commit-msg`** — every commit message must reference a worklog
  item (26-char Crockford ULID) or a ticket (`#123`); merge commits are
  exempt (detected via `MERGE_HEAD`, reliably present by this point in the
  sequence).
- **`hooks/pre-merge-commit`** — runs `pre-commit`'s checks (1–4) with
  `WORKLOG_MERGE_COMMIT` set. Git does *not* run `pre-commit` for merge
  auto-commits, so without this a merge could silently land a stale roadmap
  or a smuggled corrupt line. If it blocks your merge: `bin/worklog
  roadmap-render && git add -A && git commit --no-edit`.

CI runs the same checks — including a PR-scoped step that validates every
commit message in the PR range — on every push and PR, so bypassing a local
hook with `--no-verify` only defers the failure.

## Invariants worth knowing

- **Merging is gated by `merge-when-green.sh`**, and auto-merge on green is
  on by default; teams that want a human on the trigger set
  `features.auto_merge_on_green: false` in `.work/config.yml` (advisory
  mode: the script reports green, a human merges).
- **Never hand-edit `.work/*.jsonl`** — no editors, no `echo >>`. The CLI's
  `append()` is the only writer; it does a single atomic newline-terminated
  write and self-heals a missing trailing newline left by a hand edit.
- **Never hand-edit `docs/roadmap.md`.** It's generated; change the work
  items and re-render.
- **Every `.jsonl` write is newline-terminated.** A missing final newline is
  how two events fuse into one corrupt, unparseable line.
- **Item bodies are capped at 2 KB** in the log (keeps appends atomic under
  `PIPE_BUF`). Longer prose belongs in the plan doc.
- **`--type` is deprecated.** It maps to `level`/`kind` and warns on
  stderr; prefer the new flags. Old events in the log stay valid — the fold
  normalizes them on load.
