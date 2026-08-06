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
| `--body <text>` | description a junior dev/PM can read: what and why, no ULIDs (spec §13.4) | none |
| `--unplanned` | flag; requires `--discovered-during` | — |
| `--discovered-during <ulid>` | what the unplanned work interrupted | — |
| `--depends-on a,b` | comma-separated ULIDs that block this item | none |

Plus one flag per **enabled optional field** — by default `--estimate`,
`--owner`, `--risk`, `--acceptance-criteria`. See
[fields](#fields) for the catalog and how to switch them on and off; a
disabled field has no flag at all.

`--depends-on` is scheduling, not hierarchy — use `--parent` for the tree. The
roadmap renders these in its **Blocked by** column and counts the item as
blocked. ULID shape is validated but existence is not: an append-only log has
to stay writable when the blocker is filed a minute later. An item may not
depend on itself.

A `#123` in the **title** prints a warning (never a refusal): the item's own
ticket number is minted by the tracker at the next sync, so a number typed
into the title is either a reference to some *other* ticket or a guess that
will be wrong. Cite the ULID if you meant this item. `plan-capture` warns the
same way on task titles.

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

Change status, priority, title, kind, milestone, body, estimate, labels, or
dependencies on an open item.

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
| `--add-depends-on a,b` / `--del-depends-on a,b` | comma-separated ULIDs |

`update` carries the same optional-field flags as `add` — by default
`--estimate`, `--owner`, `--risk`, `--acceptance-criteria` (see
[fields](#fields)).

Dependencies take the same add/remove shape as labels rather than whole-field
replacement, and for the same reason: the fold treats both as set-valued, so
two branches that each add a blocker both survive a union merge.

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

### fields

Print the item field model: the fixed core, then every optional field with
`[on ]`/`[off]` and what it means. Read this before writing a field you
haven't used — the descriptions ship with the tool so two people don't fill
the same field with two different meanings.

```bash
bin/worklog fields
```

The **core** is not configurable, ever: `id`, `title`, `status`, `level`,
`kind`, `priority`, `milestone`, `labels`, `parent`, `body`, `plan`,
`depends_on`, `unplanned`, `discovered_during`, `external`, `resolution`. The
fold keys on them, the roadmap renderer reads them, sync maps them onto
tickets — a knob that could switch `priority` off is a knob that can break the
roadmap.

The **optional** catalog, switched per repo in `.work/config.yml`:

| Field | Values | Default | Meaning |
|---|---|---|---|
| `estimate` | `XS` `S` `M` `L` `XL` | **on** | Relative size, not time. Compare items; never sum into a schedule |
| `owner` | free text | **on** | Who is accountable for the item moving — one name, not a team. Not who does the work |
| `risk` | `low` `medium` `high` | **on** | Chance this goes badly or blocks others. Drives what gets planned first, not what gets estimated bigger |
| `acceptance_criteria` | free text | **on** | What must be observably true to close this. Written before the work, checked at close |
| `value` | free text | off | Expected benefit. Off by default so it doesn't become a field everyone fills with "high" |
| `confidence` | `low` `medium` `high` | off | How much to trust this item's estimate and value. Meaningless alone |
| `due_date` | `YYYY-MM-DD` | off | External hard date — a conference, an audit, a contract. Not a wish, not a substitute for a milestone |
| `severity` | `sev1`–`sev4` | off | For bugs: production impact, independent of priority. Off unless the team runs an incident process |

```yaml
# .work/config.yml
work_item_fields:
  risk: off
  severity: on
```

A disabled field is **invisible, not rejected**: its flag is never built, so
it never appears in the CLI, in `--help`, or in anything an agent reads to
decide what to write. `worklog add --risk high` in a repo with `risk: off` is
an argparse error naming an unrecognised option. An unreadable value in
config falls back to the documented default rather than failing every
command.

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

Every run ends with the drift report — one counts line, then the fields it
overwrote on live tickets, then a `drift:` list of anything else a human
should see (conflicts, unsupported fields on the platform, deferred items,
degraded mappings):

```
sync report: created=1 updated=2 closed=1 skipped=14 pulled=1 conflicts=0 deferred=0
overwrote live ticket fields:
  - owner/repo#412 (01KYA99T): title: 'Old title' -> 'New title'; status: 'todo' -> 'in_progress'
  (read 2 tickets in 0.31s to report the above)
drift:
  - fields not synced on github: depends_on
```

The overwrite block comes **before** drift on purpose: `updated=2` is not the
line that catches damage — naming the field a push replaced on a live ticket
is. It costs one read per pushed ticket, and the report says how much that
cost.

*(0.22.0)* `--dry-run` reports the overwrites a **close** would cause too. A
close is not always only a close: an item with unsynced field changes pushes
its final shape before closing, and that push can rewrite a ticket somebody
else filed. The dry run used to return early on the close path and print only
`would close #123` — silent in exactly the case where a field write is least
expected. It now predicts what the real run does on both paths.

A ticket the adapter reports **gone** (definitely not found, not a transient
failure) is marked and not retried on later runs; re-`link`ing the item to a
new key clears the mark and puts it back in scope. If several tickets report
gone and *nothing* in the run succeeded, sync aborts rather than condemning
the backlog — that pattern is a bad token or a wrong project, not a deleted
ticket (ADR-0004).

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

`kind` is required on a status record by the document schema, and since 0.20.0
rendering one without it raises `KeyError: 'kind'` instead of quietly printing
"status report" in the banner. A publish that fails this way is reporting a
record that was already malformed — fix the record's frontmatter or its
sidecar, do not restore a default.

### compact

Compact the event log per spec §7, verifying `fold(new) == fold(old)`
before writing. Requires `--yes`. Meant for CI (a nightly job on the main
branch — `.github/workflows/compact.yml`), not day-to-day use — compaction is
also what physically migrates old `type` events to `level`/`kind`.

Compaction replaces an item's events with a **snapshot** plus a watermark
(`{"op":"compact","through":<ulid>}`), and the fold drops any raw event at or
below its own item's watermark. That watermark is per item, not global
(ADR-0007): an event for an item that was never snapshotted is never dropped.

### merge-rescue

Resolve a merge the **resurrection guard** blocked, without losing events.

```bash
bin/worklog merge-rescue
```

Reach for this in exactly one situation: the nightly compaction landed on
`main` while you were working, you merged `main` into your branch, and the
merge was refused with *"N event(s) at/below their item's compact watermark
are back … Run: worklog merge-rescue"*. Union merge takes both sides, so the
merge brought back lines compaction had already folded into a snapshot — and,
worse, any event **your branch** authored below that watermark now sorts under
the snapshot and would be silently discarded on the next read.

Recompacting does not fix this and is not safe: `compact` verifies
`fold(new) == fold(old)`, and the fold has *already* discarded your branch's
sub-watermark events, so the check passes while making the loss permanent
(ADR-0005, ADR-0006). `merge-rescue` instead keeps the compacted side's log
and re-applies your branch's own events above the watermark under fresh ids
(each carrying `rescued_from: <old ev>`), using the merge base to tell "already
folded, safe to drop" from "never folded, must be replayed". It verifies before
it writes: the guard must now pass, and every item either side knew about must
still fold to a state — otherwise it aborts and leaves the logs untouched.

*(0.22.0)* Re-issuing is **contagious forward within an item**: once one of an
item's events is re-issued, every later event of that item is re-issued too.
Fresh ids are stamped at *now*, so a partially re-stamped item inverted its
own history — its create and update sorted above a close that kept its
original id, and the item folded back to its pre-close state. Losing nothing
is necessary and not sufficient, so a third check now verifies the whole log:
sorting by the new ids must give each item the same sequence its original ids
did, or the rescue refuses and writes nothing. **Ran `merge-rescue` on 0.21.0
or earlier and an item looks reopened? That is this bug** — the close event is
still in the log, so re-closing the item is a complete repair.

Run it **from the blocked merge**, before `git merge --abort`; the merge state
is what makes the repair precise. It exits 1 with an explanation if no merge
is in progress, or if neither side has ever been compacted. It prints what it
did, then:

```bash
bin/worklog roadmap-render
git add -A && git commit          # undo with: git merge --abort
```

The same guard runs a second time in CI (`bin/compact.py --merge-check`),
standalone, because the hook's copy only fires with a merge in flight and a CI
checkout has none.

### changelog-draft

Draft the unreleased CHANGELOG section from `git log` since the last tag,
grouped by commit type, with log/index-only commits excluded. Markdown on
stdout, the exclusion list on stderr.

```bash
bin/worklog changelog-draft --version 0.20.0 >> /tmp/draft.md
bin/worklog changelog-draft --since v0.18.0
```

| Flag | Meaning |
|---|---|
| `--version <v>` | version for the heading (default: the literal `X.Y.Z`) |
| `--since <ref>` | default: the last tag |

A starting point for release notes, not the release notes. The release skill
uses it as the first draft and a human edits what ships.

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

**Scope** — the check covers items that are evidence for a release, and only
those:

| Item | In scope? |
|---|---|
| Closed, has a `milestone` | yes |
| Open, or `cancelled` | no |
| No `milestone` | no — it shipped in nothing named |
| `kind:ops` | no — release cuts, status reports, compactions and worktree cleanup have no plan, ticket or PR by design |
| `unplanned` | yes, but exempt from the **plan** check only — being discovered mid-flight excuses the plan, not the ticket and the PR |

Before 0.20.0 the scope was computed, printed in every message, and then
filtered on nothing, so the gate swept every closed item in the log. Applying
it took this repo from 401 gaps to 16. **Nothing was removed** — the graph and
its edges are untouched; the gate stopped asking about items it was never
scoped to ask about. A large drop after upgrading is the fix, not data loss.

### doc-verify

*(0.21.0)* Resolve every code citation in `docs/` — `path — symbol(), lines
N–M` and its variants — **at the commit that document was written against**,
read from its `git_hash` front matter. Warns by default; `--strict` exits 1
(used pre-release and inside the design-docs skill).

```bash
bin/worklog doc-verify
bin/worklog doc-verify --strict
```

Five verdicts, and the whole point is the first two:

| Verdict | Meaning |
|---|---|
| `ok` | the citation resolves in the author's tree |
| `fabricated` | wrong **already** in the tree the author had open — a defect, fix it |
| `drift` | right when written, the code has moved since — **not** a defect in a frozen document |
| `unstamped` | no `git_hash` (anything written before 0.21.0) — unverifiable, skipped |
| `unresolvable` | the stamped commit is not in this clone (squash-merge, shallow checkout) — skipped |

`--strict` fails on **any** fabrication, and on drift only in
`current_design_doc.md` / `current_code_walkthrough.md` — the only two
documents that claim to describe the tree as it is now. A frozen document is
allowed to age; failing on that would make the gate un-passable by design.

**It never falls back to HEAD.** An unstamped or unresolvable document is
reported and skipped, never re-checked against the current tree — that
fallback is the exact assumption that produced the bad citations (#294): it
reports drift as fabrication and re-introduces the wrong-tree failure. The
same reasoning is why the pre-commit hook skips it outright on a shallow
clone, where `git show <sha>:<path>` can resolve nothing. ADR-0008 records
the consequence: under squash-merge the authoring commit never reaches the
default branch, so the verifier must report `unresolvable` and refuse.

Fix fabrications in **live** documents. In a frozen one (a plan, an ADR, a
dated design pair) the fabrication stays — a frozen document records what
someone believed at a point in time, and editing it to silence a gate both
destroys the record and trips the publish ledger's frozen-source guard. Name
the correction in the current document instead.

### provenance-backfill

*(0.21.0)* Stamp `merged_in` — the merge commit that brought a document to
the default branch — on frozen documents that have landed. A document cannot
know the merge that will carry it, so this runs afterwards, from the release
skill's post-release step. `--check` reports what would be stamped and exits
1, writing nothing.

```bash
bin/worklog provenance-backfill
bin/worklog provenance-backfill --check
```

Frozen documents only, and that is the whole judgement: a live document
(`docs/roadmap.md`, the `current_*` pair, an ADR whose status flips) has been
edited many times since it landed, so the merge that *first* carried it names
a version of the file that no longer exists. Safe to re-run — anything
already stamped is skipped. Run `worklog ia-index` and commit its output in
the **same** commit as the stamps, or the freshness gate rejects the result.

It is not a git hook because `post-merge` fires on the default branch, where
the branch guard forbids committing.

### find

Search the generated inventory and graph: documents by text / type /
truth-state, one node's edges in both directions, or every edge of one type.
Read-only, no network — it reads `docs/.index/_inventory.json` and
`_graph.json`, so run `ia-index` / `ia-graph` first if they're stale.

```bash
bin/worklog find compaction                 # substring, case-insensitive
bin/worklog find --type plan watermark      # narrow by doc_type
bin/worklog find --links item/01KYZ5CY9P    # edges in and out of one node
bin/worklog find --edge supersedes          # every edge of one type
bin/worklog find --type adr --json          # machine-readable
```

| Flag | Meaning |
|---|---|
| `<query>` | positional; case-insensitive substring |
| `--type <t>` | `doc_type` filter — `plan`, `adr`, `item`, `pr`, … |
| `--truth <t>` | `truth_state` filter — `current`, `frozen`, … |
| `--links <key>` | edges into and out of one node |
| `--edge <type>` | list every edge of one type, e.g. `supersedes` |
| `--json` | JSON instead of the text table |

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
  3. **Conflict-marker guard**: no staged file may contain `<<<<<<<`,
     `=======`, or `>>>>>>>` at the start of a line. **There is no merge
     exemption, deliberately** — a merge is exactly when this happens, and
     nothing else catches it: `commit-msg` exempts merge commits from its
     item-reference rule, and no other check parses `tests/` or `plugin/`, so
     a resolution that missed one hunk used to commit cleanly and only turn
     up when someone ran the suite. Staged content only; an unstaged conflict
     elsewhere in the tree is not this commit's problem. Resolve, re-stage,
     commit again.
  4. `docs/roadmap.md` is fresh: the hook regenerates it and diffs — a stale
     or hand-edited roadmap blocks the commit
     (`Run: worklog roadmap-render`).
  5. The fold test suite passes (only in repos that carry `tests/`).
  6. **Merge integrity** (only with a merge in flight): the resurrection
     guard — a union merge that brought back events a compaction already
     folded into a snapshot, repaired with
     [`worklog merge-rescue`](#merge-rescue) — and duplicate ticket
     ownership, two merged branches each claiming one external key
     (`worklog unlink <id-to-drop>`). CI re-runs both standalone.
  7. **IA gates** (only in repos that have a `docs/.index/`): `wiki_key`
     present and unique, schema-valid frontmatter, fresh inventory, fresh
     rendered pages and manifest. These are **hard failures** as of v0.19.0 —
     the warn-only cycle is over. `trace-check` stays warn-level here
     forever; `--strict` runs at release time. [`doc-verify`](#doc-verify)
     joined it at that same tier in 0.21.0, for the same reason — it reports
     on documents this commit may not touch, so blocking here would punish
     the wrong commit — and is skipped outright on a shallow clone, where
     every answer would be `unresolvable`. A freshly scaffolded repo has
     no `docs/.index/` and so is never blocked from its first commit.
  8. **Branch guard**: rejects a commit authored directly on `main`/`master`
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
- **`hooks/pre-merge-commit`** — exec's into `pre-commit` with
  `WORKLOG_MERGE_COMMIT` set, so every check above runs and only the branch
  guard is exempted. Git does *not* run `pre-commit` for merge auto-commits,
  so without this a merge could silently land a stale roadmap, a smuggled
  corrupt line, or an unresolved conflict marker. If it blocks your merge on
  the roadmap: `bin/worklog roadmap-render && git add -A && git commit
  --no-edit`. If it blocks on resurrected events: `bin/worklog merge-rescue`.

CI runs the same checks — including a PR-scoped step that validates every
commit message in the PR range — on every push and PR, so bypassing a local
hook with `--no-verify` only defers the failure.

## Environment variables

| Variable | Effect |
|---|---|
| `WORKLOG_NO_GIT_PROVENANCE` | Set to anything to stop stamping the `git` field on new events (see below) |
| `WORKLOG_MERGE_COMMIT` | Set by `pre-merge-commit`; tells `pre-commit` this is a merge, not authored work |
| `WORKLOG_SKIP_BRANCH_GUARD` | Skips only the `main`/`master` branch guard — for the tool's own bare invocations (`worklog doctor`, CI's backstop) |

## Invariants worth knowing

- **Every event carries its origin commit.** Each new event gets a `git`
  field holding the short HEAD sha at the moment it was written, so two
  agents in different worktrees or branches produce traceably different
  events. It is a separate field on purpose: the **id keeps its full 80 bits
  of entropy** (v0.19.0 briefly spent five characters of it on the hash;
  v0.19.1 reverted that), and an item's id is minted once, so only a
  per-event field can name where each event actually came from. The sha is
  omitted entirely — not written empty — outside a git repo or before the
  first commit, and `WORKLOG_NO_GIT_PROVENANCE` suppresses it.
- **Every generated document carries the tree it was written against.**
  Plans, status reports, ADRs, `docs/roadmap.md` and its snapshots get a
  `git_hash` in front matter as they are written (0.21.0), and the publish
  manifest carries one build-level `git_hash` rather than stamping every
  rendered page with the same fact. It means *the commit this was written
  against*, which at generation time is the commit **before** the one the
  document lands in — a commit cannot know its own sha. The roadmap takes
  the value from the newest event's `git` field instead of shelling out,
  because it is regenerate-and-diffed in CI and a HEAD-derived value would
  differ on the very next run. `merged_in` — the merge commit that landed a
  frozen document — is filled in afterwards by
  [`provenance-backfill`](#provenance-backfill).
  Neither field is required by `schema/doc.schema.json`, deliberately:
  `merged_in` cannot be (a document on a branch has not merged, so requiring
  it would reject the commit that creates any plan) and `git_hash` is not
  (documents predating 0.21.0 cannot be honestly stamped, and guessing one
  is the very error class the verifier exists to catch). Both are always
  written **quoted** — an all-digit short sha would otherwise be read back as
  an int — and omitted entirely rather than written empty, because an empty
  value opens a block list in the front-matter parser and swallows the
  closing fence.
- **One session per working directory.** `worklog` warns when more than one
  assistant session is active in the same checkout: they share one worktree,
  so one can switch branches under the other mid-operation and both can "fix"
  the same thing differently. The warning is **advisory and after the fact** —
  it never blocks a write, and a missing or corrupt registry is silently
  treated as empty. The actual fix is a `git worktree` per session. The
  registry (`.work/.sessions`) is heartbeated by the `UserPromptSubmit` hook
  and pruned by `SessionEnd`, because the harness is the only thing that knows
  a session is one session — a short-lived CLI cannot tell.
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
