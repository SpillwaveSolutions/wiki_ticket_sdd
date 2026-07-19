# WikiTicket SDD — User Guide

WikiTicket SDD (pronounced "wicked ticket") is a local-first, git-native work
tracking layer for teams doing AI-assisted development. This guide covers the
concepts and day-to-day workflows. See also the
[CLI Reference](cli-reference.md) for every command and flag, and the
[Plugin Guide](plugin-guide.md) for installing the Claude Code plugin.

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
{"ev":"01J8X2K4A0","ts":"2026-07-16T14:02:11Z","actor":"rick","item":"01J8X0M2QQ","op":"create","set":{"level":"task","kind":"feature","title":"Extract auth middleware","status":"todo","priority":"P1"}}
{"ev":"01J8X2M900","ts":"2026-07-16T14:09:03Z","actor":"rick","item":"01J8X0M2QQ","op":"update","set":{"status":"in_progress"}}
```

You never edit this file by hand. Every change goes through `bin/worklog`,
which appends events. Current state is a **fold** over the events: parse,
dedupe, sort, apply in order. State is derived, never stored — which is what
makes the next two properties possible.

### ULIDs

Every event and every item gets a ULID — a sortable, timestamp-prefixed
unique ID like `01J8X0M2QQ...`. Sorting events by ULID sorts them by time, so
the fold is a plain string sort, deterministic on every machine. The ULID is
the item's primary key forever; external ticket keys (like `PROJ-412`) are
just linked identity.

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
ULID. Plans are frozen: a second capture with the same date and slug is
refused. Design changed? Write a new plan that supersedes the old one.

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
schema, roadmap freshness, and the fold test suite. CI runs the same checks,
so a `--no-verify` commit doesn't get far.

### Merging: the roadmap-conflict recovery

The event logs union-merge with **zero conflicts** — that's the guarantee.
But `docs/roadmap.md` is a generated file, and if both sides regenerated it,
the merge can conflict on it or land a stale copy. The
`pre-merge-commit` hook (git runs it, not `pre-commit`, on merge
auto-commits) blocks any merge that would land a stale roadmap. Recovery is
always the same two steps:

```bash
bin/worklog roadmap-render      # regenerate from the merged log
git add -A
git commit --no-edit            # finish the merge commit
```

The merge is parked, not lost — regenerate and finish. Never resolve a
roadmap conflict by hand-picking hunks; the log is the truth, the roadmap is
its rendering.

### When GitHub reports merge conflicts

GitHub's server-side merge does not run merge drivers — the union merge that
makes the logs conflict-free only applies locally — so concurrent PRs can
conflict in the web UI on `docs/roadmap.md`, `.work/published.json`, or even
`.work/todo.jsonl`. Recover on the PR branch locally:

1. `git merge main` — on the PR branch; union merge applies locally, so the
   logs merge clean.
2. `bin/worklog roadmap-render` — regenerate the roadmap from the merged log.
3. Resolve `.work/published.json` by taking the union of both sides' keys.
4. `git add -A && git commit` — finish the merge commit.
5. Push the branch.
6. Merge the PR in the UI — it's conflict-free now.

## Frozen artifacts: what never gets edited

| Artifact | Rule |
|---|---|
| `docs/plans/*.md` | Written once, never edited or regenerated. Designs change by **superseding**: a new dated plan, old one stays as the record of why |
| `docs/roadmap.md` | Generated, never hand-edited. To change the roadmap, change the work items and re-render |
| `docs/roadmap/*.md` | Dated snapshots (see `roadmap-snapshot`), frozen the moment they're written |
| `.work/*.jsonl` | Only `bin/worklog` writes them. No editors, no `echo >>` |

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
guide and README. The `release.sync_docs` list in `.work/config.yml` is the
opt-in/out: what's listed gets synced at release, what isn't doesn't.

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
`.work/published.json` so republishing updates pages instead of duplicating
them. Per-system guidance (GitHub, GitLab, ADO, Confluence) lives in the
wiki-publish skill itself; the ledger shape is identical everywhere — only
how each system fills `url`/`rev`/`page_id` differs. Missing tooling
degrades to local-only; it never fails a command.

## Sync in depth

Ticket sync (`bin/worklog sync`) runs through a typed adapter contract. The
dispatcher (`bin/sync_dispatch.py`) owns every invariant — scope, canonical
hash-skip, create-vs-update, idempotency markers, echo suppression on pull,
conflict detection — and a per-system adapter is a generated dumb
translator that just maps canonical JSON to the platform's API and back.
`worklog adapter check` gates any adapter: nothing activates until it
validates green against the contract, and a missing adapter means the
dispatcher runs local-only (a mode, not an error). Every run ends with the
drift report — counts plus anything a human should see (conflicts,
unsupported fields, deferred items). That report is the sync's voice; read
it. Conflicts it detects are resolved with
`bin/worklog resolve <item> --field <f> --take local|remote`.

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
