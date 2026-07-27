# Integration: Jira

## When to use

You want `wiki_ticket_sdd` work items to show up as Jira issues, and/or
you're deciding whether Jira is the right `ticketing.system` for this
project.

## One-command setup

None. There is no shipped Jira adapter binary — set
`ticketing.system: jira` in `.work/config.yml` and note the project key
under `options:`; the `ticket-sync` skill resolves the actual tooling
(CLI/MCP/REST) at runtime rather than running a fixed install command.

## Adapter configuration

`ticketing.system: jira` is an advisory enum value, not a capability
switch — `bin/worklog` only ever branches on `none`. There is no
`adapters/jira/adapter` (only `adapters/github/` is real code today; see
`adapters/README.md` for the contract a future Jira adapter would need to
satisfy). Until one exists, this page — not a shipped binary — is the
integration.

## Recommended workflow

**Reuse rule — do this before anything else:** before making any raw Jira
REST call or shelling out to a bare `curl`, check whether the global
`jira` skill (or an Atlassian MCP server) is available and use it. It
already owns authentication, pagination, field mapping, and comment/
attachment handling — do not re-derive any of that here. This skill's own
job in the Jira case is narrower than for GitHub: read work items from
`.work/todo.jsonl`/`worklog show`, and drive the `jira` skill (or MCP
server) to create/update the corresponding issue, rather than
implementing REST calls directly.

1. `bin/worklog adapter check` — will report "no adapter" for `jira`; that
   is an expected mode (local-only), not an error.
2. Use the `jira` skill to create or update the issue, keying off the
   worklog item's ULID as an idempotency marker (store it in a Jira
   custom field or in the description, whichever the `jira` skill
   supports — HTML-comment-style markers can get stripped by some rich
   text editors, so verify one survives a round-trip before relying on
   it).
3. Record the mapping via `worklog link <ulid> --system jira --key
   <ISSUE-KEY>` so future runs treat it as an update, not a duplicate.

## Mapping events

There's no dispatcher-enforced mapping for Jira today (that machinery —
canonical hash, idempotency, create-vs-update — only runs for systems with
a real adapter). Map fields by hand via the `jira` skill: worklog `title`
→ issue summary, `body` → description, `priority`/`kind` → whatever Jira
fields the project actually uses (these vary per Jira project
configuration — don't assume a fixed scheme).

## Pulling changes

No automatic pull path exists. `worklog ingest` is the mechanism that
would bring remote edits back into `.work/todo.jsonl`, but nothing
currently calls it for Jira. Until a real adapter exists, treat Jira as
one-way (push only) and note manually if something changed on the Jira
side that needs reconciling.

## Rendering support

Ticket/PR/release pages render the same regardless of ticketing system —
`bin/ia_render.py` doesn't know or care what `ticketing.system` is set to.
What's Jira-specific is only the push step above.

## Example links

None inside this repo (Jira is external, licensed, per-org software) — see
the `jira` skill's own documentation for connection examples.

## Gotchas & troubleshooting

- No adapter ships yet — hints for building/driving one: field mapping is
  the main friction point, since Jira issue types and custom fields vary
  per project; don't assume story points, epic links, or components map
  cleanly without checking the specific project's scheme first.
- Marker durability: verify whatever idempotency marker you choose
  actually survives Jira's editor round-trip before relying on it in
  production — some rich-text fields silently strip HTML comments.
- If the `jira` skill isn't installed or an MCP server isn't configured,
  say so and ask rather than guessing at raw REST calls — per the
  `wiki-publish` skill's own precedent for Confluence: research missing
  tooling, don't fabricate it.

## Last updated

2026-07-25 — [edit this page](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki/Integration-Jira/_edit)
