---
id: 11
slug: bot-prs-land-through-the-merge-gate-with
title: Bot PRs land through the merge gate with a PAT identity
date: 2026-09-19
status: accepted
git_hash: "7715566a600fa1530fad07660fbf80a43fe8e0ca"
deciders: [rick, claude]
tags: [ci, process]
supersedes: 10
wiki_key: adr/0011-bot-prs-land-through-the-merge-gate-with
truth_state: current
---

# ADR-0011: Bot PRs land through the merge gate with a PAT identity

<!-- body is written once; only status/superseded_by change after acceptance -->

## Context

ADR-0010 decided that GitHub Actions is a bypass actor so `worklog-compact`
and `worklog-post-merge` can push derived files to `main` directly. That
never worked. A repository ruleset lists `github-actions[bot]` as a `User`
(id 41898282), and GitHub does not treat the Actions installation token as
that user, so every direct push failed with GH013 (#401). Pinning the
required checks to the Actions app (`integration_id` 15368) returns 422
(CHANGELOG 0.24.10). Both bot jobs therefore moved to opening a PR, and
v0.24.10 landed those PRs by dispatching `worklog-invariants` on the branch
tip and posting commit statuses named `invariants` and `coverage` from
`plugin/scripts/associate-pr-checks.sh`.

The v0.24.10 review found that this bridge moved the gate's trust anchor
from GitHub into a shell script. The ruleset accepts a status with the
required context from any actor that holds `statuses: write`;
`worklog-invariants` inherited repo-default write permissions; the mirrored
run was a branch-tip run, not the PR merge ref, and skipped the
`pull_request`-only commit-message step; the native `pull_request` run on
the same SHA ended as `failure` while the posted statuses said `success`;
and bot merge commits on `main` got no `push` run at all.

## Decision

1. **Bot PRs use a fine-grained PAT, not `GITHUB_TOKEN`.** The secret
   `WORKLOG_BOT_PAT` belongs to a maintainer account (a new machine user
   would hit the first-time-contributor gate that stalls
   `github-actions[bot]` today, #403), with contents, pull-requests, and
   issues read and write, and a one-year expiry recorded in the CHANGELOG.
   Pushes and PRs made with it trigger `pull_request` and `push` workflows
   natively, so the ruleset's required checks come from the event-native
   run and nothing else.
2. **The status bridge is deleted.** `associate-pr-checks.sh`, the
   `workflow_dispatch` wait, `actions: write`, and `statuses: write` go
   away once the PAT is in place. `worklog-invariants` runs with
   `permissions: contents: read` from this ADR on.
3. **No bypass actor.** The dead `User 41898282` entry leaves the ruleset.
   Every writer to `main`, human or bot, goes through a PR and the same
   two required checks.
4. **Bot PRs supersede, never rebase.** Under
   `strict_required_status_checks_policy`, a second open bot PR goes stale
   the moment the first merges, and nothing updates a bot branch. Each bot
   job closes every open `chore/compact-*` and `chore/post-merge-*` PR
   before it regenerates from `main`.
5. **Post-merge guards its own PRs by branch prefix.** With a real
   identity, a merged bot PR fires `pull_request: closed`; the loop
   terminator is explicit, and idempotent rendering from the log's `git`
   field is what makes a second run a no-op.

ADR-0010 items 2 and 4 stand: auto-merge is a repo setting, merge-commit
only (ADR-0008), and the poll loop is fallback.

## Consequences

- The merge gate's trust anchor is GitHub's own check rollup again. A
  green bot PR means the same thing as a green human PR.
- One secret to rotate yearly. A missing secret fails the bot job loudly
  at its first step; there is no fallback to the bridge.
- Bot merge commits on `main` get a native `push` run, so
  `worklog-invariants` no longer needs the `workflow_run` listener.
- The interim hardening (read-only permissions, no bypass actor, this ADR)
  ships first; the PAT cut-over ships as its own PR once the secret exists.

## Alternatives

- **GitHub App installation token.** Short-lived, not tied to a person,
  and the token the review preferred. Two secrets and an extra action for
  one repository; rejected for now on setup cost, revisit if PAT rotation
  becomes a burden.
- **Keep the bridge and pin `integration_id`.** GitHub refuses the pin
  (422), so the bridge cannot be made trustworthy from the ruleset side.
- **Shared concurrency group plus rebase before arming auto-merge.**
  Serializes job runs, not PR lifetimes, and a rebase-and-force-push loop
  can destroy a valid bot PR. Superseding is two lines and loses nothing.
