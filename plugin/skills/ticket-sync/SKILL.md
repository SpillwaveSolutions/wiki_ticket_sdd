---
name: ticket-sync
description: Push work items to the team's configured ticketing system (GitHub Issues, Jira, Azure DevOps, GitLab...). Use when asked to sync tickets, after closing out a plan, or when items should be visible in the tracker. Push and pull.
version: 0.9.0
---

# Ticket sync

Sync runs through a typed adapter contract: the dispatcher
(`bin/sync_dispatch.py`) owns every invariant; a per-system adapter is a
dumb translator. This skill's job is to run it and read the report — not
to re-implement the rules. Contract:
`docs/plans/2026-07-18-typed-adapter-contract.md`.

## 1. Read the config

Read the `ticketing:` block in `.work/config.yml`. `system` names the
tracker: `github`, `jira`, `ado`, `gitlab`, or `none`. If it is `none` or
absent, say so and stop — there is nothing to push to.

## 2. Scope

Open items plus externally-linked items whose canonical hash differs from
the last pushed one; closed and in-sync items are inert (spec §10.5 — the
dispatcher computes this, see the contract doc).

## 3. Flow

1. `bin/worklog adapter check` — activates and validates the adapter for
   the configured system against the contract. Missing adapter → the
   dispatcher runs local-only; that is a mode, not an error.
2. `bin/worklog sync` — the dispatcher handles scope, hash-skip,
   create-vs-update, echo suppression, conflict detection, and
   `worklog ingest` of pulled changes.
3. Read the drift report and surface anything that needs a human
   (conflicts, unsupported fields, degraded type mappings, auth failures).

## 4. Invariants — dispatcher-enforced, context only

Each of these is code in `bin/sync_dispatch.py` now, not procedure for you
to follow — see `docs/plans/2026-07-18-typed-adapter-contract.md`:

- **Canonical hash / skip-unchanged** (spec §10.3): an item is pushed only
  when its canonical hash differs from `last_pushed_hash` — the dispatcher
  enforces this.
- **Idempotency** (spec §10.5): the item ULID travels as a marker in the
  ticket body and a retried push finds rather than duplicates — the
  dispatcher enforces this.
- **Pull mechanics** (spec §10.1–10.3, §10.6): remote edits enter the log
  via `worklog ingest` with deterministic event IDs, echo-suppressed and
  conflict-checked — the dispatcher enforces this.

## 5. Closing

When a scoped item's status is `done` or `cancelled`, the sync closes the
remote ticket (adapter `close` verb) with a short comment naming the
resolution. After that push the item is inert: hashes match, so it is
never rescanned.

## 6. Per-system tooling

Lives in the adapters, not here. Authoring rules and shipped
implementations: `adapters/README.md`, `adapters/<system>/adapter`.

## 7. Report

Finish with counts: pushed / updated / closed / skipped, plus conflicts
and anything deferred or needing human action.

Conflicts surface in `worklog list` (stderr), `worklog show`, and the
status report's Needs-attention section. Resolve with:

    bin/worklog resolve <item> --field <f> --take local|remote
