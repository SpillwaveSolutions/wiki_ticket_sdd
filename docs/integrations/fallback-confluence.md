# Integration: Confluence

## When to use

You want `wiki_ticket_sdd` docs (roadmap, plans, status reports, ADRs) to
publish to a Confluence space instead of (or in addition to) a GitHub
wiki, and/or you're deciding whether Confluence is the right `wiki.system`
for this project.

## One-command setup

None. There is no shipped Confluence adapter binary — set
`wiki.system: confluence` in `.work/config.yml` with a space key and
parent page id under `options:`; the `wiki-publish` skill resolves the
actual tooling at runtime.

## Adapter configuration

`wiki.system: confluence` is an advisory enum value — there is no
`adapters/confluence/adapter`. `wiki-publish/SKILL.md` already documents
the shape: needs `options.space_key` and `options.parent_page_id`, page
identity is the content id (store as `page_id` in `.work/published.json`),
and the version number increments on every update (store as `rev`).

## Recommended workflow

**Reuse rule — do this before anything else:** before making any raw
Confluence REST call (`/wiki/rest/api/content`), check whether the global
`confluence` skill (or an Atlassian MCP server) is available and use it.
It already owns authentication, storage-format conversion, and
attachment/comment handling — do not re-derive any of that here.

1. Convert the markdown source to Confluence storage format using
   whatever converter the `confluence` skill provides — if none exists
   and no other conversion tooling is available, say so and ask rather
   than publishing mangled markup (this is the existing `wiki-publish`
   precedent for Confluence, carried forward here).
2. Publish/update the page via the `confluence` skill or MCP server, then
   record the ledger entry (`page_id` = content id, `rev` = version
   number) exactly as `wiki-publish/SKILL.md` §5 specifies.
3. YAML frontmatter does **not** need stripping for Confluence the way it
   does for Gollum-style wikis (GitHub/GitLab) — Confluence can be given
   or ignore it either way; keep it in the source-to-storage conversion if
   the converter supports it.

## Mapping events

Same as any other wiki target: a doc's `wiki_key` maps to one Confluence
page, tracked by `page_id` in the ledger. No Confluence-specific event
type exists.

## Pulling changes

Not applicable to wiki publishing generally (wiki-publish is push-only in
this repo's model) — there's no mechanism, Confluence or otherwise, that
pulls wiki edits back into `.work/todo.jsonl`. If a page is hand-edited in
Confluence, that edit only matters if someone notices it before the next
publish overwrites it — `wiki-publish/SKILL.md` §7 covers the analogous
"pull before push" caution for git-backed wikis; Confluence has no
equivalent safety net today, so check the page's current version number
before assuming your update is safe to push.

## Rendering support

**Diagram compatibility rule — required, not optional:** Confluence
storage format does not reliably render Mermaid or PlantUML fenced code
blocks the way Gollum-style wikis do. Any doc going to Confluence that
contains a Mermaid or PlantUML diagram must have that diagram converted to
an image first:

1. Generate the diagram via the `design-doc-mermaid` skill (Mermaid) or
   the `plantuml` skill (PlantUML).
2. Convert it to PNG or SVG using the same skill's image-conversion step —
   do not leave it as a fenced code block.
3. Upload the image as a Confluence attachment, then reference it from
   the page body (Confluence macro or standard image markup, per whatever
   the `confluence` skill/converter expects).

All diagram generation and upload routes through these two existing
skills — do not write new Mermaid/PlantUML rendering or upload logic here.

## Example links

None inside this repo (Confluence is external, licensed, per-org
software) — see the `confluence`/`mastering-confluence` skills' own
documentation for connection and space examples.

## Gotchas & troubleshooting

- If tooling is missing (no Confluence skill, no MCP server, no markdown
  converter), research it and tell the human what to install — never
  guess blindly and publish mangled storage-format markup.
- Version conflicts: Confluence's version number increments on every
  update, including manual web-UI edits — a push using a stale cached
  version can silently create a conflict; re-fetch the current version
  before pushing if there's any chance the page was touched since the
  last sync.
- Diagrams are the single most common Confluence gotcha in practice: a
  page that looks fine in the GitHub wiki (rendered Mermaid) will show raw
  fenced code text in Confluence if the image-conversion step above is
  skipped.

## Last updated

2026-07-25 — [edit this page](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki/Integration-Confluence/_edit)
