---
date: 2026-08-30
slug: retention
title: Compaction archives old closed items; never deletes
items: [01M19XRRZ2894K7XE59RX1EAY1]
status: accepted
---

# Compaction archives old closed items; never deletes

## Context

`done.jsonl` grows forever. Compaction already snapshots closed items and
prunes reopened ones; it does not drop closed history. After the merge
pipeline can land compact commits (#401–#403), eviction can live inside
compaction with the same verify-or-abort rule.

## Decision

Evict inside `bin/compact.py`, after the existing todo/done rewrite and
before verify.

- **Archive, never delete.** Moved snapshots go to `.work/archive.jsonl`
  (`merge=union`). Missing file is empty.
- **Per-level ages** (from last snapshot `ts` on the closed item):
  epic 730d, story 180d, task 90d, subtask 90d.
- **FIFO cap 1000** on remaining closed items in `done.jsonl` after age
  eviction (oldest snapshot `ts` first).
- **Unparseable `ts` is not evicted** (fail closed).
- **Verify** is `fold(todo+done+archive) before == after`. Abort leaves
  all three files untouched.
- **Reopen** still works: a later `reopen` in `todo.jsonl` outsorts the
  archived snapshot; compact also prunes currently-open items from
  `archive.jsonl` the same way it prunes `done.jsonl`.
- **`worklog show` / `list --all` fold archive.** The roadmap does not
  (working set = todo+done).
- **Defaults live in code.** `.work/config.yml` `retention:` may override
  `epic_days` / `story_days` / `task_days` / `subtask_days` / `cap`.

## Why snapshot `ts`, not ULID create time

Create time would archive an epic closed yesterday if it was filed two
years ago. After compact, close events are gone; the snapshot `ts` is the
first compact after close, which is the close clock we still have.

## Out of scope

Rewriting historical events. MIGRATE_MS. Changing the 11-item review PLAN.
PAT for bot-created PRs (filed separately).
