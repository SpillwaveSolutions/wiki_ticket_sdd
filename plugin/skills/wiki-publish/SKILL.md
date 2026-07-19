---
name: wiki-publish
description: Publish docs (roadmap, plans, user guide, status) to the team's configured wiki. Use when asked to publish/sync docs to the wiki, after cutting a roadmap snapshot, or when a plan/status report should be visible outside the repo.
version: 0.9.0
---

# Wiki publish

No per-system code ships with this skill. Read the config, then use whatever
tooling exists for that system — you already know these platforms.

## 1. Read the config

Read the `wiki:` block in `.work/config.yml`. `system` names the wiki:
`github-wiki`, `gitlab-wiki`, `ado-wiki`, `confluence`, or `none`. If it is
`none` or absent, say so and stop — there is nothing to publish to.

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

## 3. Maintain the ledger

`.work/published.json` maps logical keys to what was published:

    {"<logical-key>": {"source": "repo/path.md", "url": ..., "rev": ..., "source_hash": "sha256[:12] of source file"}}

Entries carry a `source` field (the repo path of the file) so the publish
set is self-describing. The DEFAULT publish set is always: the live roadmap
(`docs/roadmap.md`), every plan in `docs/plans/`, every roadmap snapshot in
`docs/roadmap/`, every ADR in `docs/adr/` — republish on hash change (status
flips must reach the wiki), page name `ADR-NNNN-slug`, ledger key
`adr/NNNN-slug` — plus anything registered via `worklog wiki-add`. Plans and
snapshots publish once (frozen); the roadmap and ADRs re-publish on hash
change.
To opt an arbitrary file in, register it:
`worklog wiki-add <file> --key K --title T`.

Before publishing a file, hash it (`sha256`, first 12 hex chars). If the
ledger entry's `source_hash` matches, skip it — already published. After
publishing, update the entry with the page url, the wiki revision (e.g. wiki
commit sha), and the new hash. Commit `published.json` together with the
docs it describes.

## 4. Ledger fields across systems

The ledger shape is fixed by spec §9.3; systems just fill it differently.
`url` is always the page's browse URL.

- **git-backed wikis** (github-wiki, gitlab-wiki, ADO project wiki) —
  `rev` = wiki commit sha, `page_id` = filename stem (`User-Guide`).
- **confluence** — `rev` = page version number, `page_id` = content id.
- **ado-wiki via REST** — `rev` = the ETag/version from the response,
  `page_id` = the page path.

## 5. Page naming

Derive the wiki page name from the doc title. Keep the title stable per
logical key — renaming a page breaks inbound links.

## 6. One-time init

Surface one-time setup steps to the human; never work around them silently.
Example: a GitHub wiki's `.wiki.git` does not exist until someone clicks
"Create the first page" in the repo's wiki tab — if the clone/push fails
with not-found, ask the human to do that once, then retry.

## 7. Frozen rules

Snapshots, plans, and status reports publish once and are never re-published.
The live Roadmap page and ADRs are the exceptions: re-publish whenever the
source hash changes — for an ADR, a status flip (proposed→accepted,
accepted→superseded) is exactly the change that must reach the wiki.
