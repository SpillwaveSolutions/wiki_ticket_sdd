# Integration: Azure DevOps

## When to use

You want `wiki_ticket_sdd` work items synced to Azure Boards, and/or docs
published to an Azure DevOps wiki, and you're deciding whether ADO is the
right `ticketing.system`/`wiki.system` for this project.

## One-command setup

None fixed. `az` (Azure CLI, with the `azure-devops` extension) is the
natural tool if installed; `ticket-sync`/`wiki-publish` resolve the actual
tooling at runtime.

## Adapter configuration

`ticketing.system: ado` and `wiki.system: ado-wiki` are advisory enum
values — there is no `adapters/ado/adapter` yet. This page carries the
field-tested caveats that would inform building one, and the hints for
driving ADO by hand until then.

## Recommended workflow

1. `bin/worklog adapter check` — reports "no adapter" for `ado`; expected,
   not an error.
2. Work items: `az boards work-item create/update`. **Migrating existing
   tickets**: create-vs-update is decided purely by whether the local item
   carries `external` — pre-seed it with `worklog link <ulid> --system ado
   --key <AB#id>` for every imported item so the first sync treats all of
   them as updates, never duplicates. Pilot one epic first; the
   acceptance gate is `worklog sync --dry-run` reporting **0 creates**.
3. Wiki: two kinds exist. A **project wiki** is backed by a hidden git
   repo — clone its git URL and push like any git-backed wiki. A **code
   wiki** publishes a folder on a branch — if the team already uses one
   over `docs/`, committing docs *is* publishing; still record a ledger
   entry. Via REST: `az devops wiki page create/update --wiki --path
   --content`; paths are hierarchical (`/Parent/Child`).

## Mapping events

No dispatcher-enforced mapping exists for ADO yet. The one hard-won rule:
**the marker must be a tag, not an HTML comment.** ADO silently strips
HTML comments from a work item's Description, so `<!-- worklog:<ulid> -->`
vanishes. Store the marker as a work-item tag (`worklog:<ulid>` — ADO
preserves colons and case exactly) and search by tag. A future adapter's
`capabilities.marker` should be `{"style": "tag", "template":
"worklog:{ulid}"}`.

## Pulling changes

No automatic pull path. `worklog ingest` is the mechanism that would carry
remote ADO edits back into `.work/todo.jsonl`; nothing wires it up for ADO
today.

## Rendering support

Ticket/PR/release pages render identically regardless of ticketing
system. ADO-specific behavior is confined to the push steps above.

## Example links

None inside this repo — ADO organizations are per-tenant; see `az
boards`/`az devops wiki` documentation for connection examples.

## Gotchas & troubleshooting

- **No adapter ships yet — hints for building/driving one**: updates
  merge, never overwrite. When updating an existing work item, merge tags
  and write title/state only when they actually changed — existing
  Description/content in Azure Boards is never replaced, since teams
  adopt worklog onto boards full of real content.
- Marker-as-tag (above) is the single most important gotcha — an HTML
  comment marker will silently disappear and break idempotency on the
  next sync.
- Nothing irreversible happens before the first real push — always pilot
  with `worklog sync --dry-run` first.

## Last updated

2026-07-25 — [edit this page](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki/Integration-AzureDevOps/_edit)
