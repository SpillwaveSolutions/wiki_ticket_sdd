# Integration: GitLab

## When to use

You want `wiki_ticket_sdd` work items synced to GitLab Issues and/or docs
published to a GitLab wiki, and you're deciding whether GitLab is the
right `ticketing.system`/`wiki.system` for this project.

## One-command setup

None fixed. `glab` (the GitLab CLI) is the natural tool if installed;
`ticket-sync`/`wiki-publish` resolve the actual tooling at runtime rather
than running one canonical install command.

## Adapter configuration

`ticketing.system: gitlab` and `wiki.system: gitlab-wiki` are advisory
enum values — there is no `adapters/gitlab/adapter` yet (only
`adapters/github/` is real code today). Until one exists, this page is the
integration: set the enum, note the project path under `options:`, and
drive `glab` (or GitLab's REST API) directly.

## Recommended workflow

1. `bin/worklog adapter check` — reports "no adapter" for `gitlab`;
   expected (local-only mode), not an error.
2. Issues: use `glab issue create`/`glab issue update`, keying off the
   worklog item's ULID as a marker in the issue description (GitLab
   preserves markdown, so an HTML-comment marker survives, unlike some
   rich-text systems).
3. Wiki: a GitLab wiki is also a git repo — clone `<project>.wiki.git` and
   copy/commit/push exactly as for a GitHub wiki, or use REST via
   `glab api projects/:id/wikis`. Unlike GitHub, GitLab wikis support
   directories, so nested paths work if you want them.
4. Record the mapping via `worklog link <ulid> --system gitlab --key
   <issue-iid>` once created, so re-runs update rather than duplicate.

## Mapping events

No dispatcher-enforced mapping exists for GitLab yet. Map by hand: worklog
`title` → issue title, `body` → description, and use GitLab labels for
`kind`/`priority` if the project has a label scheme for them.

## Pulling changes

No automatic pull path. `worklog ingest` is the mechanism that would carry
remote GitLab edits back into `.work/todo.jsonl`, but nothing wires it up
for GitLab today — treat as push-only until a real adapter exists.

## Rendering support

Ticket/PR/release pages render identically regardless of ticketing
system. GitLab-specific behavior is confined to the push step above and,
for the wiki, the directory-nesting difference noted there.

## Example links

None inside this repo — GitLab instances are typically self-hosted or a
separate SaaS project; see `glab`'s own documentation for connection
examples.

## Gotchas & troubleshooting

- No adapter ships yet — same caveat as Jira/ADO: don't assume label
  schemes or milestone mappings without checking the specific project's
  configuration first.
- GitLab wikis support nested directories where GitHub's don't — if you're
  also running a GitHub wiki for the same content, keep the page-naming
  flat anyway for portability between the two.
- Self-hosted GitLab instances may have custom rate limits or auth setups
  (PAT vs OAuth) beyond what `glab`'s defaults assume — verify against the
  specific instance rather than this repo's GitHub-flavored assumptions.

## Last updated

2026-07-25 — [edit this page](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki/Integration-GitLab/_edit)
