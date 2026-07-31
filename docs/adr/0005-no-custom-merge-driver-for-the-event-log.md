---
id: 5
slug: no-custom-merge-driver-for-the-event-log
title: No custom merge driver for the event log
date: 2026-07-31
status: accepted
deciders: [rick, claude]
tags: [core, git]
wiki_key: adr/0005-no-custom-merge-driver-for-the-event-log
truth_state: current
---

# ADR-0005: No custom merge driver for the event log

<!-- body is written once; only status/superseded_by change after acceptance -->

## Context

ADR-0001 chose git's built-in `union` merge driver for the event logs. Union
keeps every line from both sides, which is exactly right for an append-only
bag of events — but it does not understand the one operation that removes
lines. Compaction (spec §7) rewrites the log to a snapshot plus a watermark;
a branch that forked before a compaction still carries the removed events, so
merging it back reintroduces them. Issue #243 reported this class, and the
response shipped a detector rather than a fix: `check_resurrection` in the
pre-commit hook, comparing the merged file against the watermark.

The open question that report left behind was whether to replace union with a
purpose-built driver — one that dedupes by `ev` and honours watermarks —
making the class impossible instead of merely detectable.

This record settles that question. It does NOT supersede ADR-0001: union
merge and the fold-derived log stand exactly as decided there, and marking
that record superseded would tell a reader the opposite of what was
decided here.

On 2026-07-31 the scenario occurred live, for the second time, which settled
the question with evidence rather than argument. The nightly compaction landed
on main while PR #268 was in CI. Both merge paths were exercised.

## Decision

No custom merge driver. `union` stays, and the detector stays.

Three findings, each independently sufficient:

**The hosted path never runs a driver, and fails closed anyway.** GitHub
refused the merge outright — "not mergeable: the merge commit cannot be
cleanly created." Because no driver runs server-side, git saw a real textual
conflict and stopped. A custom driver would not have been consulted, so it
could not have changed this outcome. The merge button is the most common merge
path in this repo, and it is already safe by refusal.

**The local path is already covered.** `git merge origin/main` succeeded
textually under union, and the guard caught 55 resurrected events, named the
watermark, and blocked the commit. A driver would replace a working detector
on the one path that already has one.

**Driver registration does not travel with the repository.** `.gitattributes`
is versioned; `merge.<name>.driver` is per-clone configuration. A contributor
who has not run an installer gets git's *default text merge* on JSONL — real
conflict markers written into a file that must stay machine-readable. That is
strictly worse than union, and it fails silently rather than loudly. The
driver would therefore introduce a new failure mode to close one that is
already detected.

A fourth reason makes the driver redundant even where it would run: the fold
already dedupes by `ev` before sorting (`dedupe_and_sort`), and applies the
watermark on read. A driver deduping by `ev` would be re-implementing a
guarantee the reader already provides.

## Consequences

- The two merge guards are not equally important, and conflating them would
  be a mistake. `check_resurrection` is a **hygiene** guard: the fold discards
  resurrected events on read, so no state is ever corrupted — only the size
  win from compaction is lost. `check_duplicate_ownership` is a **correctness**
  guard: two branches each claiming the same external ticket is real
  divergence the fold cannot repair. Anyone reading the hook should not mistake
  the first for data protection.

- The guard currently runs only where a merge is in flight, which in practice
  means a developer's machine. Continuous integration checks out a merge
  result, not a merge in progress, so the guard never fires there. That gap is
  tracked separately and is worth more than the driver would have been.

- The remedy the guard prints cannot be executed from the state the guard
  creates. It advises recompacting, but compaction refuses while the logs have
  uncommitted changes — and the blocked merge is that uncommitted change. The
  only exits are `--no-verify` or `--abort`. Discovered on 2026-07-31 and
  filed; the working resolution is to abort, restore the logs from the
  compacted branch, and re-apply the branch's own events on top.

- Compaction remains the only operation that rewrites a log, and it remains
  gated on `fold(new) == fold(old)`. That equality check, not the merge
  strategy, is what makes compaction safe.

- If a future platform runs merge drivers server-side, or if the fold ever
  gains a non-idempotent operation, this decision should be revisited. Neither
  is true today.

## Alternatives

- **Event-aware merge driver (dedupe by `ev`, honour watermarks)** — rejected
  for the three reasons above. It cannot run where merges most often happen,
  it is silently optional where it can run, and it duplicates a guarantee the
  reader already gives.

- **Abandon union for `ours`/`theirs`** — rejected outright: either one
  discards a teammate's events, which is the exact failure the append-only log
  exists to prevent.

- **Rebase-only workflow, no merges** — rejected: it moves the problem rather
  than solving it. A rebase replays each commit's full log content, so a
  branch that forked before a compaction reintroduces the same events commit
  by commit, and does so without a single merge for the guard to inspect.
