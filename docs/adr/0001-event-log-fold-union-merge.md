---
id: 1
slug: event-log-fold-union-merge
title: Append-only event log with fold-derived state and git union merge
date: 2026-07-19
status: accepted
deciders: [rick, claude]
tags: [core, git]
supersedes: null
superseded_by: null
wiki_key: adr/0001-event-log-fold-union-merge
truth_state: current
---

## Context

Work tracking here is multi-writer by design: several developers and several
AI agents append work items concurrently, on separate branches, in separate
clones. Any state-file representation (a YAML tree, a TODO.md, a SQLite file)
turns every merge into a conflict and every conflict into a chance to clobber
a teammate's change. We needed a representation where concurrent writes
compose instead of collide, using nothing beyond git.

## Decision

The log (`.work/todo.jsonl`) is an append-only sequence of immutable JSONL
events; state is never stored, it is a **fold** over the events (spec §6):
parse tolerantly, dedupe by `ev`, sort ascending by ULID, apply per-field
last-writer-wins. Git merges the files with the built-in **union** driver
(`.gitattributes`, spec §8.1), so both sides of any merge survive — the file
is a bag of lines, not a sequence, and the fold's sort/dedupe absorbs the
arbitrary ordering and duplicate lines union merge produces. Every write
terminates with `\n` (the trailing-newline invariant, spec §8.2), enforced in
four layers: self-healing `append()`, single `O_APPEND` write, pre-commit and
pre-merge-commit hooks, and CI. **Compaction is the only operation that
rewrites a file** (spec §7): main branch, CI only, its own commit, and it
aborts unless `fold(new) == fold(old)` — losing state in compaction is the
worst failure mode this system has, so it is gated by equality, not review.

## Consequences

- Concurrent branches never conflict on the log in a local merge. Proven in
  practice twice: the two-branch merge integration test, and the live
  collision where a nightly compaction and a release branch landed together
  and folded clean.
- Hosted platforms do not run merge drivers server-side — two PRs touching
  `todo.jsonl` still conflict in the GitHub UI (issue #25, found merging
  PR #24). We documented the recovery (merge base locally so union applies,
  re-render, push) in spec §8.1 rather than pretending the guarantee is
  global.
- LWW ties are decided by ULID order, which is wall-clock derived: a dev with
  a fast clock wins. Accepted for v1 (spec §16); `actor` and `ts` on every
  event keep "why did my priority flip back?" answerable from the log.
- A corrupt line can never block reading the rest of the log — the fold
  skips and reports it.

## Alternatives

- **State file with normal merge conflicts** — rejected: every concurrent
  edit becomes a manual conflict, and manual conflict resolution on
  generated data is where teammates' changes get clobbered.
- **CRDTs** — rejected: correct but heavy. A ULID-sorted LWW fold over an
  append-only bag gives us the convergence we need with a shell-debuggable
  file format and zero library dependencies.
