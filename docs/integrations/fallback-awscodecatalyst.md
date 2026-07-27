# Integration: AWS CodeCatalyst

## When to use

Your team already has an AWS CodeCatalyst space (issue tracking per
project) and wants `wiki_ticket_sdd` work items to show up there.
**Check this first**: CodeCatalyst has been closed to new customers since
2025-11-07 — existing spaces keep working, but this is not a system to
newly adopt. If you don't already have a space, use GitHub, GitLab, or
Jira instead.

## One-command setup

None fixed. The `aws codecatalyst` CLI is the natural tool if installed;
`ticket-sync` resolves the actual tooling at runtime.

## Adapter configuration

`ticketing.system: codecatalyst` is an advisory enum value — there is no
`adapters/codecatalyst/adapter`; nothing has been built from the
`adapters/github/adapter` template for it. There is no
`wiki.system: codecatalyst-wiki` option — CodeCatalyst has no separate
wiki concept; pair it with `wiki.system: github-wiki`/`other` if you need
published docs.

## Recommended workflow

1. `bin/worklog adapter check` — reports "no adapter" for `codecatalyst`;
   expected, not an error.
2. Use the `aws codecatalyst` CLI to create/update issues in the relevant
   project, keying off the worklog item's ULID as an idempotency marker in
   the issue description.
3. Record the mapping via `worklog link <ulid> --system codecatalyst --key
   <issue-id>` so re-runs update rather than duplicate.

## Mapping events

No dispatcher-enforced mapping exists. Map by hand: worklog `title` →
issue title, `body` → description. CodeCatalyst's issue model is
comparatively thin (similar to ADO's, per `ticket-sync/SKILL.md`'s
comparison) — don't expect rich custom-field mapping.

## Pulling changes

No automatic pull path. `worklog ingest` would carry remote edits back in;
nothing wires it up for CodeCatalyst today.

## Rendering support

Ticket/PR/release pages render identically regardless of ticketing
system — nothing CodeCatalyst-specific in rendering.

## Example links

None inside this repo — CodeCatalyst spaces are private per-organization;
see AWS's own CodeCatalyst CLI documentation for connection examples.

## Gotchas & troubleshooting

- **Closed to new customers since 2025-11-07.** Confirm your team already
  has a space before investing effort here — this page assumes you do.
- No adapter ships yet — same caveat as the other unshipped systems: pilot
  one epic and confirm `worklog sync --dry-run` shows 0 creates before a
  real push, especially since there's no dispatcher-enforced idempotency
  check for CodeCatalyst yet.
- Marker durability hasn't been field-tested for CodeCatalyst the way it
  has for ADO — verify whatever marker convention you pick actually
  survives before relying on it.

## Last updated

2026-07-25 — [edit this page](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki/Integration-AWSCodeCatalyst/_edit)
