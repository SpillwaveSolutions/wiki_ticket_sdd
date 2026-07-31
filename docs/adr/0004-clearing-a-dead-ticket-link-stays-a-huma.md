---
id: 4
slug: clearing-a-dead-ticket-link-stays-a-huma
title: Clearing a dead ticket link stays a human action
date: 2026-07-31
status: accepted
deciders: [rick, claude]
tags: [sync, adapters]
wiki_key: adr/0004-clearing-a-dead-ticket-link-stays-a-huma
truth_state: current
---

# ADR-0004: Clearing a dead ticket link stays a human action

<!-- body is written once; only status/superseded_by change after acceptance -->

## Context

The adapter contract assigns exit code 3 to a definite not-found: the ticket
an item is linked to no longer exists. The contract's stated remedy is to
clear the item's `external` link so the item files afresh on the next sync.

Issue #241 shipped half of that deliberately. Sync records a `gone_key`,
stops retrying the item every run, and prints the remedy — but leaves the
actual unlink to a person. The ticket asked for a policy call on whether that
last step should ever be automatic. This record makes it.

The question turns entirely on how much exit code 3 actually knows. In the
GitHub adapter, `classify()` derives it from a substring match against the
`gh` CLI's stderr: `"not found"`, `"404"`, `"could not resolve"`. That is the
whole signal.

## Decision

Clearing a dead ticket link is always a human action. `worklog sync` will
never unlink automatically, at any confirmation count.

The signal cannot support it. A single rc 3 conflates at least four distinct
situations:

- the issue was genuinely deleted;
- the repository exists but the caller cannot see it — GitHub returns 404
  rather than 403 for a private repository, precisely so it does not confirm
  the repository's existence to someone unauthorised;
- the repository was renamed or transferred;
- DNS or a proxy failed, producing "could not resolve host".

Only the first warrants unlinking. The other three are transient or
configuration faults where unlinking destroys a correct link.

No confirmation threshold rescues this. "Unlink after N consecutive rc 3s"
assumes the failure modes differ in persistence, and they do not: a revoked
token, a renamed repository, and a mistyped project setting each produce an
identical rc 3 on every attempt, forever. The threshold would fire on exactly
the cases it was meant to exclude.

A second hazard makes automation worse than merely wrong. `worklog unlink`
clears the local `external` field but does not touch the remote — it prints a
warning saying so. The `worklog:<ULID>` marker stays on the ticket. If the
ticket was never really gone, the next sync files a *second* ticket for the
item, and a later pull can re-attribute the original to the same ULID. That is
the duplicate-filing path the original report warned about, reached
automatically and at scale.

## Consequences

- **The two cases cannot be told apart, and this record says so rather than
  implying a precision the signal does not have.** `gh` does not distinguish a
  missing issue from a forbidden repository in its exit status or its message,
  because GitHub's API deliberately does not. Sharpening `classify()` was
  considered and does not help: there is no additional signal to read.

- An operator who sees the gone notice must decide. The remedy is printed on
  every sync run that encounters the item, so it cannot be silently forgotten,
  and it names the exact command.

- Two changes are worth making alongside this decision, because they reduce
  real risk without requiring the distinction we cannot draw:

  **A run that has proved nothing may condemn only a bounded number of
  items.** The adapter runs once per item, and resolving the repository is
  part of every invocation — explicitly via `gh repo view` when the project is
  unset, implicitly inside each issue call when it is set. Either way an
  unreachable repository produces rc 3 for every item in the run, and would
  mark every one gone. One mistyped `WORKLOG_TICKET_PROJECT` therefore
  condemns the entire log in a single pass.

  The guard is on scale rather than on any per-ticket judgement, because scale
  is the part the signal can support. Once a run reaches three not-founds
  without a single successful adapter call, it aborts the way an auth failure
  does — having changed nothing. Any successful call, push or pull, disarms
  the threshold, so a healthy run may legitimately mark any number of tickets
  gone.

  Requiring proof of reachability *before recording anything* was tried and
  rejected: a one-item, push-only repository can never produce a success, so a
  genuinely deleted ticket there would be retried forever. The threshold
  already bounds the damage that rule was meant to prevent — below it at most
  two items can be wrongly marked, and beyond it nothing is written at all.
  Marks are buffered until the push loop ends purely so the abort leaves
  nothing behind.

  **A `gone_key` must be forgettable.** Today it is written once and never
  cleared; it is only outgrown when the key itself changes, which happens only
  through a manual unlink. A ticket restored from the tracker's trash stays
  skipped forever, with no way back except unlinking the link that is now
  correct again. Clear it when a later push to the same key succeeds.

- The conservative default has a cost, and it is the right cost: a genuinely
  deleted ticket leaves its item stuck until someone unlinks it. An item that
  syncs to nothing is visible and inert. A duplicate ticket is neither.

## Alternatives

- **Auto-unlink on rc 3** — rejected: the contract's remedy applied to a
  signal that cannot carry it. Correct for deletions, destructive for the
  three other situations that produce the same code.

- **Auto-unlink after N consecutive rc 3s** — rejected: the excluded failure
  modes are exactly the persistent ones, so the threshold selects for them.

- **Probe the repository before trusting a per-issue 404** — rejected as
  insufficient rather than wrong. It correctly separates "repository
  unreachable" from "issue missing", and that part is adopted above as the
  abort rule. It still cannot separate a deleted issue from one in a
  repository the caller can reach but whose issue they may not read.

- **Unlink locally *and* strip the remote marker** — rejected: it closes the
  duplicate-attribution path, but only by having an automated process mutate a
  ticket it has just concluded does not exist. On the permissions-failure case
  that is a write to someone else's live ticket.
