# Integration: GitHub

## When to use

You want `wiki_ticket_sdd` work items synced to GitHub Issues and docs
published to the repo's built-in GitHub wiki — this is the system this
repo itself uses, and the only one with a real, shipped adapter today.

## One-command setup

    bin/worklog adapter check

with `.work/config.yml` set to `ticketing.system: github` and
`wiki.system: github-wiki`. No further install step — `gh` (the GitHub
CLI) is the only external dependency, and it's what the adapter shells
out to.

## Adapter configuration

`adapters/github/adapter` is real, shipped code (~350 lines) — a
translator between the dispatcher's typed contract and `gh` CLI calls
(issues, labels, milestones, close). `ticketing.project` in
`.work/config.yml` is `owner/repo`. Credentials flow through however `gh`
itself is authenticated (`gh auth login`) — nothing repo-specific to
configure beyond that.

## Recommended workflow

This is the fully-wired path — no runtime research needed:

1. `bin/worklog adapter check` — validates the adapter against the
   contract.
2. `bin/worklog sync` — the dispatcher handles scope, hash-skip,
   create-vs-update, echo suppression, and conflict detection; `gh` does
   the actual API calls.
3. For the wiki: `wiki.system: github-wiki` — `wiki-publish` clones
   `<origin>.wiki.git`, copies rendered pages in flat (filename is the
   page name), strips leading frontmatter (Gollum renders it as raw text
   otherwise), commits, and pushes to `master`.

## Mapping events

Fully dispatcher-enforced (`bin/sync_dispatch.py`) — canonical hash decides
what's pushed, the item ULID travels as an idempotency marker in the issue
body, and closing an item (`done`/`cancelled`) closes the GitHub issue
with a resolution comment. See `ticket-sync/SKILL.md` §4 for the
invariants; nothing here overrides them.

## Pulling changes

Remote edits enter via `worklog ingest` with deterministic event IDs,
echo-suppressed so a push doesn't re-trigger itself, and conflict-checked
against local edits — fully automatic as part of `bin/worklog sync`.

## Rendering support

Ticket pages (`docs/.index/rendered/tickets/<ULID>.md`), release pages,
and PR pages (`docs/.index/rendered/prs/<num>.md`) all render from this
repo's own event log via `bin/ia_render.py`, independent of GitHub — the
GitHub-specific step is only the wiki push and the issue sync described
above.

## Example links

This repo's own issue tracker and wiki are the live example:
[SpillwaveSolutions/wiki_ticket_sdd issues](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues),
[wiki](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki).

## Gotchas & troubleshooting

- One-time init: a GitHub wiki's `.wiki.git` does not exist until someone
  clicks "Create the first page" in the repo's wiki tab — if clone/push
  fails not-found, that's the fix, not a bug.
- Rate limits: `gh` respects GitHub's normal API rate limits; heavy sync
  runs across many items can hit secondary rate limits — back off and
  retry rather than parallelizing pushes.
- Pull before push on the wiki checkout — it's a cache
  (`.work/wiki-checkout/`), and pages may have been hand-edited in the web
  UI since the last pull.

## Last updated

2026-07-25 — [edit this page](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki/Integration-GitHub/_edit)
