---
name: ticket-sync
description: Push work items to the team's configured ticketing system (GitHub Issues, Jira, Azure DevOps, GitLab...). Use when asked to sync tickets, after closing out a plan, or when items should be visible in the tracker. Push and pull.
version: 0.5.0
---

# Ticket sync

No per-system code ships with this skill. Read the config, then use whatever
tooling exists for that system — you already know these platforms. Push local
items as tickets (sections 2–7), then pull remote edits back (section 8).

## 1. Read the config

Read the `ticketing:` block in `.work/config.yml`. `system` names the
tracker: `github`, `jira`, `ado`, `gitlab`, or `none`. If it is `none` or
absent, say so and stop — there is nothing to push to.

## 2. Scope

Open items (status `todo`, `in_progress`, or `blocked`, taken from
`bin/worklog fold`) PLUS any item carrying `external` identity whose
canonical hash differs from its `last_pushed_hash` — spec §10.5's
`external.dirty`. A closed item with external identity stays in scope
exactly until its closure is pushed; once hashes match it is inert and
never rescanned.

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

**Closing:** when a scoped item's status is `done` or `cancelled`, close the
remote ticket with a short comment naming the resolution (GitHub:
`gh issue close <n> -c "<resolution or status>"`), then update
`last_pushed_hash` in `.work/sync-state.json`. Do NOT run `bin/worklog link`
again — the item already has external identity. After that push the item is
inert: hashes match, so it is never rescanned.

## 7. Report

Finish with counts: pushed / updated / closed / skipped, and anything
deferred or needing human action.

## 8. Pull

Still one code path (spec §10.1): the remote is just another writer. Pulled
changes enter the log through `bin/worklog ingest`; the existing fold merges
them.

1. **Cursor.** Read `cursors.<system>` from `.work/sync-state.json`
   (RFC3339). Absent → the epoch.
2. **Fetch** tickets updated since the cursor that carry the worklog marker.
   GitHub:

       gh issue list --search "worklog: in:body updated:><cursor>" \
         --state all --json number,title,body,state,labels,updatedAt

   Extract the item ULID from each body's `<!-- worklog:<ULID> -->` marker.
3. **Map** remote fields to canonical: `title` as-is; state `open` → leave
   status alone, `closed` → `status=done`; priority from the `P*` label.
4. **Echo suppression** (spec §10.3). Compute the section-3 canonical hash
   of the mapped synced fields. Equal to the item's `last_pushed_hash` →
   skip: that is our own push coming back.
5. **Conflict check** (spec §10.6). If the LOCAL item also changed since the
   last push (local canonical hash ≠ `last_pushed_hash`) AND a synced field
   differs between local and remote, record instead of applying — state does
   not change (report policy):

       bin/worklog conflict <ulid> --field <f> --local <lv> --remote <rv> \
         --remote-rev <updatedAt>

6. **Ingest** otherwise, one `--set field=value` per changed field:

       bin/worklog ingest <ulid> --system github --key <n> --rev <updatedAt> \
         --rev-ts-ms <ms-of-updatedAt> --set field=value

   The event ID is deterministic (spec §10.2), so two devs pulling the same
   change append byte-identical lines and the fold keeps one.
7. **Advance the cursor** to the max `updatedAt` seen and write it back to
   `cursors.<system>`.

**Fresh clone** (spec §10.3): no `.work/sync-state.json` makes everything
look remote-changed. If remote hash == local hash, record it as
`last_pushed_hash` and ingest nothing — only genuine differences produce
events.

Conflicts surface in `worklog list` (stderr), `worklog show`, and the status
report's Needs-attention section. Resolve with:

    bin/worklog resolve <item> --field <f> --take local|remote
