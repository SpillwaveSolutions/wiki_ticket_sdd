---
doc_type: guide
slug: user-guide
title: WikiTicket SDD — User Guide
truth_state: current
wiki_key: user-guide
---
# WikiTicket SDD — User Guide

WikiTicket SDD (pronounced "wicked ticket") is a local-first, git-native work
tracking layer for teams doing AI-assisted development. This guide covers the
concepts and day-to-day workflows. See also the
[CLI Reference](cli-reference.md) for every command and flag, and the
[Plugin Guide](plugin-guide.md) for installing the Claude Code or Codex
plugin.

## What it is, and why

Three ideas drive everything:

1. **Visible WIP.** Everything in flight lives in the repo: the work items,
   the plans that produced them, the generated roadmap. When an AI agent does
   work in your codebase, that work is *fishbowled* — every plan becomes
   tracked items before the work starts, every status change is an event in
   the log, and the roadmap anyone can read is regenerated from those events.
   No hidden work, no "what did the agent do last week?"

2. **Spec-driven: plans are the spec.** A ticket says *what* and *when*; the
   plan says *why, and what we considered instead*. Plans are written once,
   committed to `docs/plans/`, and never edited — a changed design gets a NEW
   plan that supersedes the old one. Six months later, when someone asks why
   an approach was abandoned, the answer is in a dated document, not a closed
   ticket.

3. **Generic core, system-agnostic edges.** The core never knows the word
   "Jira." Your team keeps whatever tracker and wiki it already uses —
   GitHub, GitLab, Azure DevOps, Jira, Confluence — and `.work/config.yml`
   names it. Publishing and syncing are done by skills that instruct the AI
   agent to use whatever CLI or MCP tooling is available for that system.

## Concepts

### The event log

All work items live in `.work/todo.jsonl` — an append-only log where each
line is one immutable event:

```jsonl
{"ev":"01J8X2K4A0","ts":"2026-07-16T14:02:11Z","actor":"rick","git":"b446a6c","item":"01J8X0M2QQ","op":"create","set":{"level":"task","kind":"feature","title":"Extract auth middleware","status":"todo","priority":"P1"}}
{"ev":"01J8X2M900","ts":"2026-07-16T14:09:03Z","actor":"rick","git":"b446a6c","item":"01J8X0M2QQ","op":"update","set":{"status":"in_progress"}}
```

The `git` field is **provenance**: the short HEAD sha when the event was
written, so two agents in different worktrees or branches produce traceably
different events. It is a field and not part of the id, because an id is
minted once and could only ever name where the *item* was created, while a
field on every event names the origin of each one — and because entropy in an
id is not currency to spend on metadata. It is omitted outside a git repo, and
`WORKLOG_NO_GIT_PROVENANCE` turns it off.

You never edit this file by hand. Every change goes through `bin/worklog`,
which appends events. Current state is a **fold** over the events: parse,
dedupe, sort, apply in order. State is derived, never stored — which is what
makes the next two properties possible.

### ULIDs

Every event and every item gets a ULID — a sortable, timestamp-prefixed
unique ID like `01J8X0M2QQ...`. Sorting events by ULID sorts them by time, so
the fold is a plain string sort, deterministic on every machine. The ULID is
the item's primary key forever; external ticket keys (like `PROJ-412`) are
just linked identity — and that link runs one way only: **one remote ticket
has exactly one local owner.** `link` refuses a key another item already
holds (even a cancelled one), and `unlink` is the supported undo.

You rarely type all 26 characters. Every command that names an existing item
(`update`, `close`, `link`, `unlink`, `reopen`, `resolve`, `show`) takes any
unambiguous prefix — paste the short id `worklog list` and `worklog show` print. A prefix
that matches two items is refused and the candidates are named; a prefix that
matches nothing is refused and nothing is written.

### Union merge: concurrent teammates don't conflict

`.gitattributes` marks the log files `merge=union`: a merge takes both sides,
always. Two teammates (or two AI agents on two branches) can edit the *same
item* concurrently and the merge produces zero conflicts — the fold dedupes
and sorts, so both changes survive:

```
$ git checkout -b alice && bin/worklog update $A --add-label backend --status in_progress
$ git checkout -b bob   && bin/worklog update $A --add-label urgent --priority P0
$ git merge alice && git merge bob     # no conflict
$ bin/worklog show $A
  status:   in_progress    <- alice's
  priority: P0             <- bob's
  labels:   [backend, urgent]   <- both
```

The one thing that would break this — a missing trailing newline fusing two
events into one corrupt line — is enforced away by the CLI's writer and by
the git hooks (see [CLI Reference](cli-reference.md)).

## The work taxonomy

Every work item sits on four independent axes (this replaces the single
`type` enum of v0.5 — see
[the migration note](../migrations/0001-type-split.md); `--type` survives as
a deprecated alias):

| Axis | Field | Values | Answers |
|---|---|---|---|
| Level | `level` | epic / story / task / subtask | size & place in the parent tree |
| Kind | `kind` | feature / bug / ops / triage | nature of the work |
| Milestone | `milestone` | free string (e.g. v0.6.0) or null | what ships together |
| Planned | `unplanned` + `discovered_during` | bool + ULID | deliberate vs discovered |

Level is pure decomposition — hierarchy is the `parent` chain, and an epic
is just an item with `level: epic`. Kind is the nature of the work,
independent of size: a bug is not a size, which is why it is no longer a
peer of `epic` in one enum.

Six rules (the validator enforces these):

1. Kind is free at story/task/subtask.
2. Epics are `feature` or `ops` only — a bug is never epic-sized.
3. `kind` defaults to `triage` when omitted — never silently default to
   feature.
4. `bug.parent` is optional; bugs may float free of any epic.
5. `milestone` lives on leaves (story and below); an epic's milestone
   derives from its children.
6. `triage` and `ops` both trend down: triage shrinks by classifying, ops
   by automating.

Two of these deserve a sentence. **Triage is the honest default:** an item
created without a deliberate kind *looks* unclassified — it lands in the
roadmap's Needs-classification queue instead of masquerading as a feature.
When unsure of the kind, `triage` plus a stated open question beats a
confident guess. **A milestone is a query, not an object:** a release is
simply the set of items where `milestone == v0.6.0` — GitHub milestone or
Jira fixVersion on the tracker side — and release-engineering work is
`kind:ops` tasks carrying that milestone. The roadmap surfaces all of this:
a Needs-classification section, the kind mix per epic, and milestone
grouping.

Fields you'll use daily:

| Field | Values | Notes |
|---|---|---|
| `status` | `todo`, `in_progress`, `blocked`, `done`, `cancelled` | `done`/`cancelled` are set by `close` |
| `level` | `epic`, `story`, `task`, `subtask` | Default `task` |
| `kind` | `feature`, `bug`, `ops`, `triage` | Omitted → folds to `triage` |
| `milestone` | free string or null | Leaves only; epics derive theirs |
| `priority` | `P0` (drop everything) … `P3` (someday) | Default `P2` |
| `depends_on` | list of item ULIDs | Blocks scheduling; distinct from `parent` |
| `labels` | free strings | Set-valued: adds from two branches merge, they don't clobber |
| `unplanned` | true/false | Discovered mid-flight, not in the plan |
| `discovered_during` | item ULID | What the unplanned work interrupted; required with `unplanned` |
| `plan` | path | The plan doc that produced this item |

### Optional fields: one log, two processes

Those are the **core** fields — fixed, never configurable, because the fold
keys on them, the roadmap renderer reads them, and sync maps them onto
tickets. On top of them sits a per-repo optional catalog, so a lightweight
team isn't carrying fields it never fills in and a heavyweight one has
somewhere to put risk, owner, or acceptance criteria without inventing
conventions inside the body text:

| Field | Default | What it's for |
|---|---|---|
| `estimate` (`XS`–`XL`) | **on** | Relative size, not time. Compare items; never sum into a schedule |
| `owner` | **on** | Who is accountable for the item moving — one name, not a team |
| `risk` (`low`/`medium`/`high`) | **on** | Chance it goes badly or blocks others. Drives planning order, not estimate size |
| `acceptance_criteria` | **on** | What must be observably true to close it |
| `value`, `confidence`, `due_date`, `severity` | off | Available, off by default — an unfilled field is worse than a missing one, because it looks like an answer |

```yaml
# .work/config.yml
work_item_fields:
  risk: off
  severity: on
```

A disabled field is **invisible, not rejected**: no flag is built for it, so
it never shows up in the CLI, in `--help`, or in anything an agent reads to
decide what to write. Run `bin/worklog fields` to see what this repo has
switched on and what each field means — the descriptions ship with the tool
so two people don't fill one field with two different meanings.

## Core workflow: plan → capture → work → close → render → commit

### 1. Plan, then capture the plan

Planning that doesn't emit tracked items is planning that evaporates. When a
plan is approved (in Claude Code, exiting plan mode triggers this
automatically via a hook), capture it:

```bash
bin/worklog plan-capture --slug auth-refactor --title "Auth refactor" --file plan.md
```

The plan file needs a `## Tasks` section with checkbox tasks:

```markdown
## Tasks

- [ ] (P1) Extract auth middleware
  - [ ] Add tests for session handling
- [ ] (P2) Migrate session store
```

This writes `docs/plans/<date>-auth-refactor.md` (front matter links it to
its items), creates an epic plus one item per task, and prints the epic's
ULID. Plans are frozen: a second capture with the same slug is refused
regardless of date — the guard scans every existing plan file for that slug,
not just today's. Design changed? Write a new plan that supersedes the old
one.

A plan's wiki banner names its state — *completed plan*, *plan in flight*,
*plan not yet started*. Normally you get this for free: `ia-normalize` derives
the plan's `status` from its items (planned until work starts, active while
open, completed when all are closed). A hand-written `status:` in the plan's
front matter overrides that derivation, and because plan status is free prose
rather than an enum, only its **leading word** is read — `completed`,
`active`, or `planned`. Prose starting with anything else renders the plain
"the current plan" banner rather than a guessed label, so if you write your
own status and want the state shown, lead with one of those three words.

### 2. Start work

```bash
bin/worklog list                              # see open items
bin/worklog update <ulid> --status in_progress
```

### 3. Close when done

```bash
bin/worklog close <ulid> --status done --resolution "merged in PR #7"
```

### 4. Regenerate the roadmap and commit together

```bash
bin/worklog roadmap-render
git add .work/todo.jsonl docs/roadmap.md
git commit -m "auth: middleware extracted"
```

Always commit the log and the roadmap **together** — the pre-commit hook
rejects a stale roadmap, so this isn't optional, it's enforced.

## Unplanned work: record it BEFORE doing it

You're mid-task and discover a bug, a missing migration, a "we also need
to…". Do not silently absorb it. Record it first, then do it:

```bash
bin/worklog add "Session table missing index" --kind bug \
    --unplanned --discovered-during <current-item-ulid>
```

`--unplanned` requires `--discovered-during` — attribution to what it
interrupted is the point. "38% of last week's items were unplanned, mostly
interrupting the auth epic" is the most useful number a team can have, and it
falls out of this field for free.

## The PR flow

Work happens on branches, like everything else:

```bash
git checkout -b feature/auth-refactor
# ... plan-capture, update, close, roadmap-render, commit as above ...
git push -u origin feature/auth-refactor    # open the PR
```

On every commit, the git hooks check: trailing newline on the logs, event
schema, no unresolved conflict markers in any staged file, roadmap freshness,
the fold test suite, and — in repos that have a `docs/.index/` — the IA gates
(`wiki_key` present and unique, valid frontmatter, fresh inventory and
rendered pages), which are hard failures as of v0.19.0. CI runs the same
checks, so a `--no-verify` commit doesn't get far.

Two more checks enforce branch discipline. `pre-commit` rejects a commit
authored directly on `main`/`master` (`main`/`master` is pull-only — branch,
then merge via PR); a real reconciliation merge (`git merge origin/main`) is
exempt via `WORKLOG_MERGE_COMMIT`, set by `pre-merge-commit` before it
exec's into `pre-commit`. A separate `commit-msg` hook requires every commit
message to reference a worklog item (26-char Crockford ULID) or a ticket
(`#123`) — merge commits are exempt. CI runs a PR-scoped step validating
every commit message in the PR range, so a `--no-verify` local commit still
gets caught before merge.

### Merging: generated files stay out of the way

The event logs union-merge with **zero conflicts** — that's the guarantee.
`docs/roadmap.md` and `docs/.index/**` are generated, so they use git's
`ours` merge driver (`git config merge.ours.driver true`, installed by
init and by the commit hook): two branches that each added a work item
never conflict on a file nobody edited by hand. `pre-merge-commit` then
regenerates both from the union-merged log and stages the result before
the freshness gate runs, so the merge commit carries the combined picture
rather than whichever side happened to be checked out (#381).

If a merge still stops on a generated file (an older clone whose
`.gitattributes` is missing the `ours` lines, or a conflict from before
this driver landed), recovery is the same two steps it always was:

```bash
bin/worklog roadmap-render      # regenerate from the merged log
git add -A
git commit --no-edit            # finish the merge commit
```

The merge is parked, not lost — regenerate and finish. Never resolve a
roadmap conflict by hand-picking hunks; the log is the truth, the roadmap is
its rendering.

### Merging across a compaction: `worklog merge-rescue`

Compaction runs nightly in CI on `main`. If it lands while you're working,
your next `git merge main` can be refused with:

```
.work/todo.jsonl: 12 event(s) at/below their item's compact watermark are
back … Run: worklog merge-rescue
```

This is the one merge failure union merge cannot shrug off, and you *will*
hit it eventually. Compaction replaces an item's events with a snapshot plus
a watermark, and the fold drops any raw event at or below that item's
watermark. Union merge takes both sides — so the merge brings the compacted
lines back (harmless: the file just grows to its old size) *and* puts any
event **your branch** authored below that watermark underneath the snapshot,
where the next read silently discards it. That is the part that loses work.

```bash
bin/worklog merge-rescue        # from inside the blocked merge
bin/worklog roadmap-render
git add -A && git commit        # undo with: git merge --abort
```

Do not try to fix this by recompacting. `compact` verifies
`fold(new) == fold(old)`, and the fold has already discarded your branch's
sub-watermark events — the check passes while making the loss permanent
(ADR-0005, ADR-0006). `merge-rescue` keeps the compacted side's log and
re-applies your branch's own events *above* the watermark under fresh ids
(each tagged `rescued_from`), using the merge base to tell "already folded,
safe to drop" from "never folded, must be replayed". It verifies before it
writes and aborts with the logs untouched if anything would vanish.

Run it **from the blocked merge**, before `git merge --abort` — the merge
state is what makes the repair precise. Details and the exact guarantees:
[CLI Reference](cli-reference.md#merge-rescue). The watermark is per item, not
global, so an event for an item that was never snapshotted is never at risk
(ADR-0007).

**If you ran `merge-rescue` on 0.21.0 or earlier and an item looks reopened,
that is a bug, fixed in 0.22.0.** Re-issued events are stamped at *now*, so
they sorted above every event that kept its original id — including later
events of the *same item*, which sat above the watermark and were left alone.
An item whose create and update moved but whose close did not folded back to
its pre-close state: no event lost, every guard green, wrong answer. The close
event is still in your log, so **re-closing the item is a complete repair**.
From 0.22.0 re-issuing is contagious forward within an item — once one event
moves, every later event of that item moves with it — and a second,
independent check refuses the whole rescue unless sorting by the new ids gives
every item the same sequence its original ids did.

### Conflict markers never commit

The pre-commit hook rejects any staged file containing `<<<<<<<`, `=======`,
or `>>>>>>>` at the start of a line, and — unlike the branch guard — **there
is no merge exemption**. That looks harsh right up until you see why: a merge
is precisely when a missed hunk happens, and nothing else catches it.
`commit-msg` exempts merge commits from its item-reference rule, and no other
check parses `tests/` or `plugin/`, so a half-finished resolution used to
commit cleanly and only surface when someone ran the suite. An exemption here
would be an exemption exactly where the check earns its keep. Resolve the
file, re-stage, commit again.

### When GitHub reports merge conflicts

GitHub's server-side merge does not run merge drivers — the union merge that
makes the logs conflict-free only applies locally — so concurrent PRs can
conflict in the web UI on `docs/roadmap.md`, `.work/published.jsonl`, or even
`.work/todo.jsonl`. Recover on the PR branch locally:

1. `git merge main` — on the PR branch; union merge applies locally, so the
   logs merge clean.
2. `bin/worklog roadmap-render` — regenerate the roadmap from the merged log.
3. `.work/published.jsonl` is `merge=union` locally — fold it (`worklog wiki-get`) after merging the base branch; GitHub's server-side merge still will not run the driver, so recover locally the same way as the work log.
4. `git add -A && git commit` — finish the merge commit.
5. Push the branch.
6. Merge the PR in the UI — it's conflict-free now.

## One session per working directory

Two assistant sessions in one checkout is a specific, reproducible failure:
one switches branches out from under the other mid-operation, and both
independently "fix" the same problem in different ways. `worklog` now notices
and says so:

```
WARNING: 2 assistant sessions are active in this working directory
(branches: feature/auth, main). They share one checkout, so one can switch
branches under the other mid-operation and both can 'fix' the same thing
differently. Give each session its own git worktree.
```

Read that as a smoke alarm, not a fix. The warning is **advisory and arrives
after the fact** — it never blocks a write, and a missing or corrupt registry
is silently treated as "no opinion", because a bad advisory file must never be
the reason someone cannot record work. The actual fix is one `git worktree`
per session:

```bash
git worktree add ../repo-auth feature/auth-refactor
```

Why the detection lives where it does: `worklog` is a short-lived CLI with a
fresh pid on every invocation, so it cannot tell one session from another. The
harness is the only thing that knows, and it hands a stable session id to its
hooks — so the `UserPromptSubmit` hook heartbeats into `.work/.sessions` and
`SessionEnd` prunes on the way out (without that, a finished session cries
wolf at the next one for a full hour).

## Frozen artifacts: what never gets edited

| Artifact | Rule |
|---|---|
| `docs/plans/*.md` | Written once, never edited or regenerated. Designs change by **superseding**: a new dated plan, old one stays as the record of why |
| `docs/roadmap.md` | Generated, never hand-edited. To change the roadmap, change the work items and re-render |
| `docs/roadmap/*.md` | Dated snapshots (see `roadmap-snapshot`), frozen the moment they're written |
| `.work/*.jsonl` | Only `bin/worklog` writes them. No editors, no `echo >>` |

"Frozen" means the **prose** is frozen. Front matter is metadata about the
document, not the document, so the tooling may still stamp it — `wiki_key`
when the normalizer runs, `superseded_by` when a later ADR lands,
`merged_in` when `provenance-backfill` learns which merge carried the file.
Since 0.21.0 the publish manifest hashes each document below its front
matter, so none of those stamps look like an edit to the frozen-source guard.
A change to the body still does, and still stops the publisher.

### Architecture decisions

Significant decisions get an ADR in `docs/adr/NNNN-slug.md` (`worklog adr
new` scaffolds one; `worklog adr check` validates them all). ADRs follow
Nygard rules: the body (Context / Decision / Consequences / Alternatives) is
written once and never edited; only the `status` field mutates afterward
(`proposed` → `accepted` → `deprecated`/`superseded`). If a decision is
revisited, write a NEW ADR with `--supersedes N` — the tooling pairs
`supersedes`/`superseded_by` and flips the old ADR's status; the old file
stays as the record of why. ADRs are in the wiki-publish default set as
`ADR-NNNN-slug` pages, republished on change so a status flip reaches the
wiki.

## Design docs and code walkthroughs

Releases generate four artifacts under `docs/designs/`: a frozen dated pair —
`<date>_<name>_design_doc.md` plus `<date>_<name>_code_walkthrough.md`, front
matter tying them to the release's git tag and roadmap snapshot, published
once and never regenerated (same rule as roadmap snapshots) — and a live pair,
`current_design_doc.md` plus `current_code_walkthrough.md`, rewritten in place
at every release; besides `docs/roadmap.md` they are the only docs that are.
The design-docs skill generates them from the actual code; at tag time the
release skill spawns background agents to regenerate them and refresh the user
guide and README. `worklog triggers release` is the opt-in/out: what's
listed gets synced at release, what isn't doesn't. `release.sync_docs` is
the legacy fallback.

These are the documents that cite code by file and line, which is why 0.21.0
added a check for it — see below.

## Document provenance and citation checking

*(0.21.0)* A generated document that cites code as `<path> — <symbol>(),
lines N–M` is making a claim about a specific tree. Before 0.21.0 nothing
checked it, and a hand audit of the 0.20.0 design docs found **12 of 26 line
citations wrong**: each written by an agent that had the file open and copied
the previous edition's numbers forward. One wrong claim was introduced while
hand-fixing another — correcting citations by hand without a check relocates
the error instead of removing it.

Two fields make the check possible:

| Field | Meaning |
|---|---|
| `git_hash` | The commit the document was **written against**. Stamped at authoring time on plans, status reports, ADRs, `docs/roadmap.md` and its snapshots, and once per build on the publish manifest. At generation time that is the commit *before* the one the document lands in — a commit cannot know its own sha. |
| `merged_in` | The merge commit that brought a frozen document to the default branch. Filled in after the fact by `worklog provenance-backfill`. |

Neither is required. `merged_in` cannot be — a document on a branch has not
merged, so requiring it would reject the commit that creates any plan — and
`git_hash` is not, because documents written before 0.21.0 cannot be honestly
stamped, and backfilling a guessed commit is the exact error this exists to
prevent.

[`worklog doc-verify`](cli-reference.md#doc-verify) then resolves every
citation at that commit. It separates a **fabricated** citation (wrong
already in the tree the author had open — a defect) from **drift** (right
when written, the code moved since — expected in a frozen document, not a
defect), which nothing could tell apart before. It runs warn-level in
`pre-commit`, `--strict` at release, and — the placement that actually
prevents the bug — inside the design-docs skill, before an agent may report a
regeneration complete. That is the moment the error is made and the only
moment fixing it is free.

Expect findings on your existing documents, and expect most of them not to be
yours to fix: anything written before 0.21.0 reports `unstamped`, and
fabrications inside frozen files stay frozen. Fix them in live documents;
name them in prose for frozen ones.

`doc-verify` **never falls back to HEAD** — that fallback is the wrong-tree
assumption that caused the problem. ADR-0008 records the consequence: the
whole mechanism depends on this repository using merge commits, because under
squash-merge the authoring commit never reaches the default branch and `git
show <sha>:<path>` fails in a fresh clone. At that point the verifier reports
`unresolvable` and refuses, rather than degrading to a check it can pass.

## Information architecture & content model

Storage is organized by how docs are produced; **navigation is a generated
reader plane on top** (plugin 0.13.0, plan
`docs/plans/2026-07-22-ia-content-model.md`). Paths under `docs/` do not
move. What is added:

| Idea | Meaning |
|---|---|
| `wiki_key` | Stable logical identity for a doc (the same key the publish ledger uses). Path, title, and wiki page name can change; the key does not. |
| `truth_state` | What kind of truth the page is for a reader: `current`, `snapshot`, `superseded`, or `archived`. Orthogonal to lifecycle `status` on ADRs/plans. |
| Doc types | Unified frontmatter via `schema/doc.schema.json` — plans, roadmap, snapshots, status, design, ADR, guide, and related types share required fields (`wiki_key`, `doc_type`, `truth_state`, …). Work items use a separate entity schema. |
| Sidecars | Frozen docs are never rewritten to add metadata. `ia-normalize` writes `docs/.index/<wiki_key>.yml` sidecars instead. Live docs (`roadmap.md`, `current_*` designs) may get in-place frontmatter. |
| Reader plane | `worklog ia-render` generates Home, Sidebar, and indexes (Decisions, Releases, Status archive, Traceability) under `docs/.index/rendered/`, plus `publish-manifest.json`. |
| Artifact pages | `ia-render` also generates one page per **ticket** (`Ticket-<ULID>`), **release** (`Release-<tag>`), and **PR** (`PR-<num>`) — hierarchy, subtasks/progress, linked PRs, and release for tickets; a graph-derived Change Log and Release Tree for releases; linked tickets and related release for PRs. All derived from existing graph edges at render time, no new stored fields. Preview a ticket page with `worklog ia-ticket <ULID>` (plan `docs/plans/2026-07-24-artifact-pages.md`). PR pages carry real state — files changed, review decision, CI rollup, merge time — once `worklog pr-sync <N>` has fetched it into `docs/.index/pr/<N>.yml`; a PR never synced renders as `not tracked`. Fetch writes a committed file, render only reads it, which is what keeps `ia-render --check` byte-deterministic. |
| Traceability | `worklog ia-graph` builds a typed-edge graph; `link-pr` records PR/commit edges; `trace-check` reports closed items missing plan/ticket/PR links (warn by default, `--strict` pre-release) — scoped to closed items carrying a milestone, with `kind:ops` exempt outright and `unplanned` exempt from the plan check only. Upgrading to 0.20.0 makes that count drop sharply (401 → 16 here) because the scope is finally applied; no edges were removed. `worklog find` searches the inventory and graph — by text, `--type`, `--truth`, a node's `--links`, or every `--edge` of one type. |
| Provenance | Documents carry `git_hash` (the tree they were written against) and, once landed, `merged_in` (the merge that carried them, stamped by `worklog provenance-backfill`). `worklog doc-verify` resolves their code citations at that commit — never at HEAD. See [Document provenance](#document-provenance-and-citation-checking). |

Day-to-day: after plan-capture or a release doc set change, run
`bin/worklog ia-index` (normalize → inventory → render). Wiki publish
reads the **publish manifest**, not a hand-curated page list: each entry
has `source`, `page_name`, and either publish-as-is or doc-plus-banner
(banners are applied at publish time so frozen sources stay frozen). For
GitHub Wiki, frontmatter is stripped in the wiki copy only.

```bash
bin/worklog ia-index                 # refresh inventory + Home/Sidebar/indexes
bin/worklog ia-graph                 # rebuild traceability graph
bin/worklog link-pr <ulid> --pr 104  # attach code evidence
bin/worklog pr-sync 104              # fetch live PR state into the sidecar
bin/worklog ia-ticket <ulid>         # preview a generated ticket page
bin/worklog find watermark           # search the inventory and graph
bin/worklog trace-check              # unlinked-evidence report
bin/worklog doc-verify               # check citations at each doc's own commit
bin/worklog provenance-backfill      # stamp merged_in on frozen docs that landed
```

Full command flags: [CLI Reference](cli-reference.md#information-architecture-ia-commands).

## System-agnostic edges: your tracker, your wiki

`.work/config.yml` names your team's systems:

```yaml
ticketing:
  system: github               # github | gitlab | jira | ado | linear | codecatalyst | other | none
wiki:
  system: github-wiki          # github-wiki | gitlab-wiki | ado-wiki | confluence | other | none
```

The core never branches on these names. Publishing and syncing are done by
**skills** — instructions the AI agent follows using whatever tooling is
available for the configured system: `gh` and git for GitHub, a Confluence
MCP server or CLI for Confluence, the ADO CLI for Azure DevOps, and so on.
If the tooling isn't installed, the agent researches it at runtime and, when
a step needs a human (e.g. creating a GitHub wiki's first page in the web
UI), it says so. The wiki-publish skill keeps a ledger in
`.work/published.jsonl` so republishing updates pages instead of duplicating
them. When `docs/.index/publish-manifest.json` exists (from `ia-render`),
that file **is** the publish set — including generated Home/Sidebar,
indexes, and the per-ticket/release/PR artifact pages — and ledger skip
uses `render_hash` so a frozen page can still
republish when only its banner changed.

**Correction to what this guide said at 0.20.0:** a banner change does *not*
invalidate every frozen page at once. A page's `render_hash` moves only when
that page's **own** banner text changes, so the 0.20.0 plan-banner fix
republished 18 pages here, not the whole site. If you upgraded and saw a
small publish, nothing failed.

Since 0.21.0 both hashes in the manifest are taken **below the front
matter**. Publishing strips front matter for Gollum-style wikis, so two files
differing only there produce byte-identical pages; hashing the whole file
moved `render_hash` anyway and tripped the frozen-source guard on every
metadata stamp — the normalizer writing `wiki_key`, an ADR status flip, a
`provenance-backfill`. The guard now means **the prose changed**, which is
what it was always protecting. That is why stamping 73 documents with
provenance moved the republish backlog by two pages instead of by 89. The
publisher copies `source_hash` and `render_hash` from the manifest rather
than hashing files itself, so it cannot hash the wrong thing.

Per-system guidance (GitHub,
GitLab, ADO, Confluence) lives in the wiki-publish skill itself; the ledger
shape is identical everywhere — only how each system fills
`url`/`rev`/`page_id` differs. Missing tooling degrades to local-only; it
never fails a command.

## Sync in depth

Ticket sync (`bin/worklog sync`) runs through a typed adapter contract. The
dispatcher (`bin/sync_dispatch.py`) owns every invariant — scope, change
detection (the canonical hash *and* the ticket the item last pushed to),
one-owner-per-ticket, create-vs-update, idempotency markers, echo suppression
on pull, conflict detection — and a per-system adapter is a generated dumb
translator that just maps canonical JSON to the platform's API and back.
`worklog adapter check` gates any adapter: nothing activates until it
validates green against the contract, and a missing adapter means the
dispatcher runs local-only (a mode, not an error). Every run ends with the
drift report — counts plus anything a human should see (conflicts,
unsupported fields, deferred items). That report is the sync's voice; read
it. Conflicts it detects are resolved with
`bin/worklog resolve <item> --field <f> --take local|remote`.

`--push-only` still does not ingest remote title/body edits, but it does
observe the tracker for two gaps a log-as-source-of-truth run otherwise
cannot see (#385):

- **Unmarked remotes** (no worklog marker) print as their own block.
  Absorb one with `bin/worklog adopt --system github --key N`. Never
  `gh issue create` or `gh issue edit` on a worklog-managed tracker —
  child worktrees add via `worklog` or they file nothing.
- **Closed on remote, still open in the log.** Sync closes the log item
  and does not push the open state back. `--dry-run` names
  `worklog close <id>` instead of writing.

One thing does not go in the drift report: a ticket claimed by more than one
item. Sync refuses to push *those* items (corruption needs both of them
pushed), finishes the rest of the run, prints the claimants and the repair as
its own block, and **exits non-zero** — under `--dry-run` too. The repair
ends with `worklog sync --keys <key>`, because unlinking the impostor does not
by itself make the surviving owner dirty enough to re-push over the damage.
See the [CLI Reference](cli-reference.md#unlink).

Remote ticket **bodies** are composed from the local source via
`bin/worklog ticket-body <ulid>` (issue-description skill): summary,
epic/plan context, milestone, and traceability edges. Enrich items with
`worklog update --body "…"` and `worklog link-pr` rather than editing only
the remote description.

## The classifier (off by default)

The default path for keeping work tracked is inline: when trackable work
surfaces in conversation, the agent proposes an item as part of its normal
response and creates it only on your assent — with `kind:triage` and the
open question stated when unsure. For teams where work keeps escaping the
log anyway, a flag-gated classifier (`classifier:` in `.work/config.yml`)
can sweep conversations: it is propose-only, staging suggestions to
`.work/suggestions.jsonl` (gitignored, never the event log). A suggestion
becomes real only when promoted — `bin/worklog promote <suggestion-id>`
creates exactly one item and marks the suggestion consumed.

## Where to next

- [CLI Reference](cli-reference.md) — every `worklog` subcommand, the git
  hooks, and the invariants.
- [Plugin Guide](plugin-guide.md) — installing the Claude Code plugin,
  `/worklog:init`, the skills and hooks.
- `docs/worklog-spec.md` — the full specification, if you want the why
  behind every design decision.
