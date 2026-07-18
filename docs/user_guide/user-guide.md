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
{"ev":"01J8X2K4A0","ts":"2026-07-16T14:02:11Z","actor":"rick","item":"01J8X0M2QQ","op":"create","set":{"type":"task","title":"Extract auth middleware","status":"todo","priority":"P1"}}
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

## Item types and fields

| Type | Use for |
|---|---|
| `epic` | A body of work; the roadmap groups by it |
| `story` | A user-facing chunk of an epic |
| `task` | A unit of work (the default) |
| `subtask` | A child of a task |
| `bug` | A defect |

Hierarchy is the `parent` chain — an epic is just an item with `type: epic`.

Fields you'll use daily:

| Field | Values | Notes |
|---|---|---|
| `status` | `todo`, `in_progress`, `blocked`, `done`, `cancelled` | `done`/`cancelled` are set by `close` |
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
bin/worklog add "Session table missing index" --type bug \
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

## Frozen artifacts: what never gets edited

| Artifact | Rule |
|---|---|
| `docs/plans/*.md` | Written once, never edited or regenerated. Designs change by **superseding**: a new dated plan, old one stays as the record of why |
| `docs/roadmap.md` | Generated, never hand-edited. To change the roadmap, change the work items and re-render |
| `docs/roadmap/*.md` | Dated snapshots (see `roadmap-snapshot`), frozen the moment they're written |
| `.work/*.jsonl` | Only `bin/worklog` writes them. No editors, no `echo >>` |

## System-agnostic edges: your tracker, your wiki

`.work/config.yml` names your team's systems:

```yaml
ticketing:
  system: github               # jira | ado | github | none
wiki:
  system: github-wiki          # confluence | github-wiki | ado-wiki | none
```

The core never branches on these names. Publishing and syncing are done by
**skills** — instructions the AI agent follows using whatever tooling is
available for the configured system: `gh` and git for GitHub, a Confluence
MCP server or CLI for Confluence, the ADO CLI for Azure DevOps, and so on.
If the tooling isn't installed, the agent researches it at runtime and, when
a step needs a human (e.g. creating a GitHub wiki's first page in the web
UI), it says so. The wiki-publish skill keeps a ledger in
`.work/published.json` so republishing updates pages instead of duplicating
them. Missing tooling degrades to local-only; it never fails a command.

## Where to next

- [CLI Reference](cli-reference.md) — every `worklog` subcommand, the git
  hooks, and the invariants.
- [Plugin Guide](plugin-guide.md) — installing the Claude Code plugin,
  `/worklog:init`, the skills and hooks.
- `docs/worklog-spec.md` — the full specification, if you want the why
  behind every design decision.
