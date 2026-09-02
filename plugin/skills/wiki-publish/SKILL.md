---
name: wiki-publish
metadata:
  version: "0.24.10"
description: Publish docs (roadmap, plans, user guide, status) to the team's configured wiki. Use when asked to publish/sync docs to the wiki, after cutting a roadmap snapshot, or when a plan/status report should be visible outside the repo.
---

# Wiki publish

No per-system code ships with this skill. The dispatcher
(`worklog wiki-plan`) owns skip and the frozen guard. This skill's job is
to run it, push the pages it names, and `wiki-record` the result — not to
re-implement the rules.

## 0. Dispatcher owns skip and the frozen guard

1. If `docs/.index/publish-manifest.json` is missing or stale, run
   `worklog ia-index` (`worklog ia-render --check` tells you).
2. `bin/worklog wiki-plan` — reads the manifest and the folded ledger.
   Prints JSON `{publish, skip, frozen_violations}`.
3. If the command exits 1, `frozen_violations` is a frozen-doc **source**
   edit (body hash drifted). Stop and report. Do not publish.
4. Publish only the pages in `publish`. `skip` is already on the wiki
   (`render_hash` match). A frozen page whose **banner** moved has a new
   `render_hash` and a matching `source_hash` — those are in `publish`.
5. Copy `source_hash` and `render_hash` from the plan entry into
   `worklog wiki-record`. Never hash files yourself.

For each page in `publish`:

- `render: "as-is"` — publish the file (frontmatter-strip of §3 still applies).
- `render: "doc+banner"` — strip per §3, then prepend the page's `banner`
  line plus a blank line. Banners are publish-time renders; never write
  them into `docs/` sources.
- `page_name` `_Sidebar` publishes as `_Sidebar.md`.

Never publish `docs/.index/` internals: only manifest-listed sources
reach the wiki. The JSON/YAML files (inventory, graph, manifest, aliases,
sidecars) are internal join data.

## 1. Read the config

Read the `wiki:` block in `.work/config.yml`. `system` names the wiki:
`github-wiki`, `gitlab-wiki`, `ado-wiki`, `confluence`, `other`, or `none`.
If it is `none` or absent, say so and stop — there is nothing to publish to.
The enum is advisory — `other` is any wiki not listed (Notion, MediaWiki,
a docs site): set it, name the real system in `options:`, and resolve the
tooling at runtime like any other system below.

## 2. Pick the tooling

Use whatever is available for the configured system, in order of preference:
a CLI already installed, an MCP server, or an installed skill.

### github-wiki

`gh`/`git`: clone `<origin>.wiki.git` into the gitignored
`.work/wiki-checkout/`, copy page files in, commit, push. Page namespace is
flat — no directories: the filename IS the page name (`User-Guide.md` →
"User Guide"). The wiki repo's default branch is `master`. Cross-page links
use `[[Page-Name]]` syntax. Pull before pushing — the checkout is a cache;
pages may have been edited in the web UI.

### gitlab-wiki

Also a git repo: clone `<project>.wiki.git`, then copy/commit/push exactly
as for github-wiki. Or use REST via `glab api projects/:id/wikis`. The page
slug is the filename (minus `.md`). Unlike GitHub, GitLab wikis support
directories, so nested paths work.

### ado-wiki

Two kinds. A **project wiki** is backed by a hidden git repo — clone it via
the wiki's git URL and push like any git-backed wiki. A **code wiki**
publishes a folder on a branch — if the team uses one over `docs/`,
committing docs IS publishing; still record ledger entries. For the REST
path: `az devops wiki page create/update --wiki --path --content`. Page
paths are hierarchical (`/Parent/Child`).

### confluence

Needs a space key and parent page id — read them from `wiki.options` in the
config. Prefer an Atlassian MCP server or an installed Confluence skill;
otherwise use REST (`/wiki/rest/api/content`), which takes storage format —
convert the markdown, or use a converter the team already has. If no
conversion tooling exists, say so and ask rather than publishing mangled
markup. Page identity is the content id — store it as `page_id` in the
ledger entry. The version number increments on every update — store it as
`rev`.

If tooling is missing, RESEARCH it (docs/web) and tell the human what to
install — do not guess blindly. These are mainstream systems; rely on model
knowledge plus live exploration, not shipped integration code.

## 3. Strip frontmatter for Gollum-style wikis

Plans, ADRs, status reports, and design docs carry a YAML frontmatter block
(`---` ... `---`) as their machine-readable source of truth — never touch
that in `docs/`. But Gollum (GitHub wiki, and any other Gollum-style wiki)
renders it as raw text instead of parsing it, so the page opens with an ugly
`---` block up top. Fix it in the copy, not the source: for `github-wiki`
(and `other` systems that are Gollum-backed), when writing a page into the
wiki checkout, strip the leading frontmatter block first — only when the
file starts with a `---` line at byte 0, delete through the next line that
is exactly `---`, and write what remains. A doc with no frontmatter, or
where `---` appears later in the body, is untouched. `gitlab-wiki`,
`ado-wiki`, and `confluence` understand or can be given frontmatter, so keep
or adapt it per platform instead of stripping.

## 4. Maintain the ledger

`.work/published.jsonl` is an append-only event log, folded last-write-wins
per logical key, `merge=union` — the same story as the work log. **Never
hand-edit it.** The dispatcher owns the file:

- `worklog wiki-plan` — what to publish (skip + frozen guard)
- `worklog wiki-get [key]` — fold the ledger (one page, or the whole dict)
- `worklog wiki-add <file> --key K --title T` — register a file
- `worklog wiki-record --key K --url U --rev R --source-hash H --render-hash H ...`
  — record a successful publish, copying hashes from the plan entry

The folded shape of one key is still:

    {"source": "repo/path.md", "url": ..., "rev": ..., "source_hash": "...", "render_hash": "..."}

After publishing, `worklog wiki-record` the page url, the wiki revision
(e.g. wiki commit sha), and the hashes from the plan. Commit
`published.jsonl` together with the docs it describes.

## 5. Ledger fields across systems

The ledger shape is fixed by spec §9.3; systems just fill it differently.
`url` is always the page's browse URL.

- **git-backed wikis** (github-wiki, gitlab-wiki, ADO project wiki) —
  `rev` = wiki commit sha, `page_id` = filename stem (`User-Guide`).
- **confluence** — `rev` = page version number, `page_id` = content id.
- **ado-wiki via REST** — `rev` = the ETag/version from the response,
  `page_id` = the page path.

## 6. Page naming

Use `page_name` from the plan entry. Keep the title stable per logical
key — renaming a page breaks inbound links.

## 7. One-time init

Surface one-time setup steps to the human; never work around them silently.
Example: a GitHub wiki's `.wiki.git` does not exist until someone clicks
"Create the first page" in the repo's wiki tab — if the clone/push fails
with not-found, ask the human to do that once, then retry.

## 8. Frozen rules

Enforced by `wiki-plan`, not this procedure. A frozen violation is a stop.
Banner-only changes on a frozen page have a new `render_hash` and a
matching `source_hash` — those publish. Snapshots, plans, status reports,
freeze notes, and legacy dated design docs are frozen; the live Roadmap, ADRs, and
`current_design_doc` / `current_code_walkthrough` re-publish when the
source hash changes.

## 9. Diagram assets

GitHub wiki renders fenced `mermaid` blocks. It does not render PlantUML
source. Confluence does not reliably render either.

When a page under `docs/designs/` (or a requirements doc) links an image
in `docs/diagrams/`:

- **github-wiki**: copy the PNG or SVG into the wiki checkout next to the
  page (flat namespace) or keep a working relative link. A wiki page that
  points at a missing image is a publish defect.
- **confluence**: upload Mermaid and PlantUML images as attachments and
  replace source fences with the image. Do not ship a mermaid fence as
  the only Confluence view.
- Leave mermaid fences in the GitHub wiki copy. Leave PlantUML as an
  image plus the `.puml` source in the repo.

Missing `docs/diagrams/*.png` (or `.svg`) for a PlantUML leftover type
blocks publish. Same for Confluence mermaid images.
