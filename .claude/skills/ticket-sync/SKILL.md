---
name: ticket-sync
description: Push work items to the team's configured ticketing system (GitHub Issues, Jira, Azure DevOps, GitLab...). Use when asked to sync tickets, after closing out a plan, or when items should be visible in the tracker. Push-only for now.
---

# Ticket sync

No per-system code ships with this skill. Read the config, then use whatever
tooling exists for that system — you already know these platforms. Push-only:
local items become tickets; nothing is pulled back.

## 1. Read the config

Read the `ticketing:` block in `.work/config.yml`. `system` names the
tracker: `github`, `jira`, `ado`, `gitlab`, or `none`. If it is `none` or
absent, say so and stop — there is nothing to push to.

## 2. Scope

Open items only: status `todo`, `in_progress`, or `blocked`, taken from
`bin/worklog fold`. Closed items never reconcile — skip them entirely.

## 3. Skip unchanged items

For each item in scope, compute the canonical hash (spec §10.3):

    hash = sha256(canonical_json({title, body, type, status, priority, parent, labels, assignee}))[:16]

Canonical JSON = sorted keys, no whitespace, arrays sorted for set-valued
fields. Compare with `items.<ulid>.last_pushed_hash` in
`.work/sync-state.json` (gitignored, per-clone). Equal → skip; nothing has
changed since the last push.

## 4. Idempotency — the critical rule

The item ULID is the external idempotency key. Every ticket body embeds the
marker:

    <!-- worklog:<ULID> -->

BEFORE creating a ticket, search the tracker for that marker (GitHub:
`gh search issues` / `gh issue list --search`). Found → update that ticket
instead of creating. A retried push must find, never duplicate.

## 5. Tooling per system

- **github** — `gh issue create/edit/list` against the origin repo (or
  `ticketing.project` if set). Map type and priority to labels (`type:epic`,
  `P1`); create missing labels first with `gh label create ... || true`.
  Title = the item title; parent and plan are referenced as lines in the
  body.
- **jira / ado / gitlab** — use their CLI (`jira`, `az boards`, `glab`) or an
  MCP server if present; same marker idempotency (a hidden comment or a
  tagged field). If tooling is missing, RESEARCH it (docs/web) and tell the
  human what to install — do not guess blindly.

## 6. Record the link

After each successful push:

    bin/worklog link <ulid> --system <system> --key <issue#> --url <url> --hash <canonical-hash>

This appends the link event — the ONLY way external identity enters the log.
Then update the item's `last_pushed_hash` in `.work/sync-state.json`.

## 7. Report

Finish with counts: pushed / updated / skipped, and anything deferred or
needing human action.
