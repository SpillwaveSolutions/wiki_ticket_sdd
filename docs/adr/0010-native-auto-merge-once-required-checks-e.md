---
id: 10
slug: native-auto-merge-once-required-checks-e
title: Native auto-merge once required checks exist
date: 2026-08-30
status: accepted
git_hash: "d5bff2bb7cb341fcf479f6f4d95c256c127a8d16"
deciders: [rick, grok]
tags: [ci, process]
wiki_key: adr/0010-native-auto-merge-once-required-checks-e
truth_state: current
---

# ADR-0010: Native auto-merge once required checks exist

<!-- body is written once; only status/superseded_by change after acceptance -->

## Context

ADR-0003 decided that a PR merges only when every quality gate is green,
and rejected GitHub's native auto-merge for two reasons: it was bypassable
through branch-protection gaps (main had none), and it gave the local
agent loop no completion signal.

Both objections aged out. `merge-when-green.sh` already arms
`gh pr merge --auto --merge` (never squash: ADR-0008) and polls at 60s as
a fallback reporter. That arm is a no-op until the repository allows
auto-merge *and* required status checks exist — GitHub will not queue
auto-merge against an unprotected default branch. Meanwhile the poll loop
still blocks an agent session for up to one CI cycle, and post-merge
chores (roadmap, IA index, sync --report) still run in that session
instead of on main.

## Decision

1. **Required checks on `main`.** A repository ruleset requires the
   `invariants` and `coverage` jobs, with "require branches up to date".
   Allowed merge method is merge-commit only. GitHub Actions is a bypass
   actor so `worklog-compact` and `worklog-post-merge` can still push
   derived files to main — the same sanctioned path compact.yml already
   uses.
2. **Auto-merge is a repo setting, not a hope.** `allow_auto_merge` is
   on; `allow_squash_merge` and `allow_rebase_merge` are off. Squash
   would make every `git_hash` unresolvable (ADR-0008).
3. **Post-merge chores run on main.** `worklog-post-merge` fires on a
   merged PR to `main`, regenerates roadmap + IA inventory/manifest,
   posts `worklog sync --report` on the PR, self-checks, and pushes.
   `worklog-invariants` listens on that workflow the same way it listens
   on compact (#361).
4. **The poll loop is fallback.** `/worklog:merge` still arms auto-merge
   up front. It only has to wait when the platform cannot (no ruleset,
   auto-merge disabled, non-GitHub host). Default interval stays 60s.

ADR-0003's core decision is unchanged: pending means wait, failing means
fix, never `--admin`. This ADR adopts the alternative ADR-0003 rejected,
now that the gaps it named are closed.

## Consequences

- Opening a PR and arming `--auto --merge` is the whole local merge
  ceremony. The session pulls main after GitHub merges; it does not poll
  for 2 hours.
- Compact.yml and post-merge.yml remain the only writers that push to
  main without a PR. A ruleset without the Actions bypass would break
  nightly compact.
- Ceremony PRs (release stamp, provenance-backfill, item-close) that
  each pay a full CI cycle should land as one PR. That is a release-skill
  rule, not a new workflow.

## Alternatives

- **Keep client-side polling as the merge mechanism.** Works without
  repo settings. Rejected: it is the thing this change exists to stop
  paying. The loop stays as fallback.
- **Require reviews on main.** Wrong shape for a repo whose agents open
  and land their own PRs. Required checks are the gate; reviews are not.
- **Merge queue.** Right when concurrent agent PRs become the bottleneck.
  Not yet. History is serial small PRs, each waiting on one CI cycle.
