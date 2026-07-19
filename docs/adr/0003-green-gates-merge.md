---
id: 3
slug: green-gates-merge
title: PRs merge only when every quality gate is green
date: 2026-07-19
status: accepted
deciders: [rick, claude]
tags: [ci, process]
supersedes: null
superseded_by: null
---

## Context

Before v0.6.0, merges happened on request: when a human (or an agent
finishing a task) said "merge it", the PR merged, regardless of what the
checks were doing. Pending checks were treated as probably-fine and failing
ones as somebody-else's-flake. In a repo where AI agents open and land their
own PRs, that habit scales into broken main faster than a human team's
would — nobody is watching the checks after the merge button is pressed.

## Decision

A PR merges only when **every** quality gate reports green (CLAUDE.md
policy, shipped in v0.6.0 as the merge-green skill plus
`merge-when-green.sh`):

- The merge loop polls check status, 5-minute default interval, instead of
  merging on request. Pending means wait; failing means fix.
- **No gates reporting is not gates passing.** A PR whose checks never
  report times the loop out — it does not merge on the absence of failure.
- Never `gh pr merge --admin`, never bypass branch protection, never merge
  blind. A red gate is a stop, not an obstacle.

## Consequences

- The loop merged its own PR first — the v0.6.0 PR that introduced
  merge-when-green.sh was the first PR landed by it, which was the honest
  smoke test.
- A red gate now stops the line: the fix happens on the branch before merge,
  not on main after.
- Every merge costs roughly one CI cycle of latency while the loop waits for
  green. Accepted: it is bounded, predictable, and cheaper than any broken
  main incident.
- The policy is only as good as the gates. It raised the incentive to keep
  gates meaningful — the >=80% coverage floor on `bin/*.py` landed in the
  same release for exactly that reason.

## Alternatives

- **GitHub auto-merge** — rejected at the time: it was bypassable through
  branch-protection gaps in this repo's setup, and it gives the local agent
  loop no signal — the agent needs to know whether the merge happened to
  continue its own workflow, so the poll loop lives locally.
- **Merge on request, blind** — the previous state; the thing this decision
  exists to end.
