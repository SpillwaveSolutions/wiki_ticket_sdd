# Migration 0001: `type` → `level` + `kind` (+ `milestone`)

**Lands in:** worklog-spec v1.7 (`feature/work-taxonomy`)
**Plan:** `docs/plans/2026-07-18-work-taxonomy.md`

## Why

v0.5's single `type` enum collapsed two orthogonal questions — *how big is
this* and *what kind of work is it* — into one field, which is why `bug` sat
awkwardly beside `epic`/`story`/`task`/`subtask`: a bug is not a size. The
split gives each axis its own field, plus the release axis that was missing
entirely:

- `level` — `epic|story|task|subtask` — place in the parent tree (decomposition)
- `kind` — `feature|bug|ops|triage` — nature of the work (`triage` = deliberately unclassified, the default)
- `milestone` — string|null — what ships together (GitHub milestone / Jira fixVersion)

## The mapping

Old `type` values migrate deterministically:

| old `type` | `level` | `kind` |
|---|---|---|
| `epic` | `epic` | `feature` |
| `story` | `story` | `feature` |
| `task` | `task` | `feature` |
| `subtask` | `subtask` | `feature` |
| `bug` | `task` | `bug` |

`milestone` starts null everywhere; nothing is inferred.

## Alias mechanics

The event log is append-only, so history is not rewritten ad hoc:

- **The fold normalizes on load.** Any event carrying `type` is read as the
  (`level`, `kind`) pair above. State derived from old logs is
  indistinguishable from state written with the new fields.
- **Compaction migrates physically.** The next compaction (main branch, CI
  only) writes snapshots in the new shape; after it, the alias no longer
  appears in the files.
- **The CLI accepts `--type`, deprecated.** It maps per the table and prints
  a deprecation warning on stderr. Prefer `--level`/`--kind`.
- **Adapters tolerate old tickets.** A ticket pushed under the old `type:*`
  label scheme still round-trips: pull falls back to `type:*` labels when no
  `level:*` label is present (`type:bug` → `level:task`, `kind:bug`).

## Hash-churn consequence

The canonical sync hash (spec §10.3) now covers
`{title, body, level, kind, milestone, status, priority, parent, labels,
assignee}` instead of `type`. Every in-scope item's hash therefore changes on
upgrade, so **the first sync after upgrading re-pushes everything once**.
Pushes are idempotent by ULID marker — existing tickets are updated, never
duplicated — and hashes converge on that first run. Expect one noisy sync,
then quiet.

## What teams must do

**Nothing.** The fold normalizes old events automatically, compaction
migrates the files on its normal schedule, and the one-time re-push happens
on the next routine sync.
