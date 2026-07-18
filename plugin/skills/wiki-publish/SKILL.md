---
name: wiki-publish
description: Publish docs (roadmap, plans, user guide, status) to the team's configured wiki. Use when asked to publish/sync docs to the wiki, after cutting a roadmap snapshot, or when a plan/status report should be visible outside the repo.
version: 0.4.0
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

- **github-wiki** — `gh`/`git`: clone `<origin>.wiki.git` into the gitignored
  `.work/wiki-checkout/`, copy page files in, commit, push. Page namespace is
  flat: the filename IS the page name (`User-Guide.md` → "User Guide").
- **gitlab-wiki** — `glab` or `git` against the project's `.wiki.git`.
- **ado-wiki** — `az devops` / `az repos` wiki commands.
- **confluence** — an MCP server or Confluence skill if installed; otherwise
  the REST API.

If tooling is missing, RESEARCH it (docs/web) and tell the human what to
install — do not guess blindly. These are mainstream systems; rely on model
knowledge plus live exploration, not shipped integration code.

## 3. Maintain the ledger

`.work/published.json` maps logical keys to what was published:

    {"<logical-key>": {"source": "repo/path.md", "url": ..., "rev": ..., "source_hash": "sha256[:12] of source file"}}

Entries carry a `source` field (the repo path of the file) so the publish
set is self-describing. The DEFAULT publish set is always: the live roadmap
(`docs/roadmap.md`), every plan in `docs/plans/`, every roadmap snapshot in
`docs/roadmap/`, plus anything registered via `worklog wiki-add`. Plans and
snapshots publish once (frozen); the roadmap re-publishes on hash change.
To opt an arbitrary file in, register it:
`worklog wiki-add <file> --key K --title T`.

Before publishing a file, hash it (`sha256`, first 12 hex chars). If the
ledger entry's `source_hash` matches, skip it — already published. After
publishing, update the entry with the page url, the wiki revision (e.g. wiki
commit sha), and the new hash. Commit `published.json` together with the
docs it describes.

## 4. Page naming

Derive the wiki page name from the doc title. Keep the title stable per
logical key — renaming a page breaks inbound links.

## 5. One-time init

Surface one-time setup steps to the human; never work around them silently.
Example: a GitHub wiki's `.wiki.git` does not exist until someone clicks
"Create the first page" in the repo's wiki tab — if the clone/push fails
with not-found, ask the human to do that once, then retry.

## 6. Frozen rules

Snapshots, plans, and status reports publish once and are never re-published.
The live Roadmap page is the exception: re-publish it whenever its source
hash changes.
