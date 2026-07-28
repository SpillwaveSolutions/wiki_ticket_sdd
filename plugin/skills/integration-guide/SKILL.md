---
name: integration-guide
description: Look up how wiki_ticket_sdd integrates with a specific SDD tool or ticket/wiki system — Superpowers, GSD, SpecKit, OpenSpec, Jira, Confluence, GitHub, GitLab, Azure DevOps (ADO), AWS CodeCatalyst, or Google Cloud DevOps (GCP). Use when asked how to set up, configure, or use one of these, or when ticket-sync/wiki-publish need runtime guidance for a system with no shipped adapter.
version: 0.17.1
---

# Integration guide

Eleven systems each have a dedicated integration guide, published on the
wiki and mirrored locally. This skill's job is to find the right one and
follow it — not to carry integration knowledge itself.

## 1. Match the name to a canonical key

| Canonical key | Aliases | Wiki page | Local fallback file |
|---|---|---|---|
| `superpowers` | Superpowers | `Integration-Superpowers` | `docs/integrations/fallback-superpowers.md` |
| `gsd` | GSD, Get Shit Done | `Integration-GSD` | `docs/integrations/fallback-gsd.md` |
| `speckit` | SpecKit, Spec Kit | `Integration-SpecKit` | `docs/integrations/fallback-speckit.md` |
| `openspec` | OpenSpec | `Integration-OpenSpec` | `docs/integrations/fallback-openspec.md` |
| `jira` | Jira, Atlassian Jira | `Integration-Jira` | `docs/integrations/fallback-jira.md` |
| `confluence` | Confluence, Atlassian Confluence | `Integration-Confluence` | `docs/integrations/fallback-confluence.md` |
| `github` | GitHub, GitHub Issues | `Integration-GitHub` | `docs/integrations/fallback-github.md` |
| `gitlab` | GitLab | `Integration-GitLab` | `docs/integrations/fallback-gitlab.md` |
| `azuredevops` | Azure DevOps, ADO, Azure Boards | `Integration-AzureDevOps` | `docs/integrations/fallback-azuredevops.md` |
| `awscodecatalyst` | AWS CodeCatalyst, CodeCatalyst | `Integration-AWSCodeCatalyst` | `docs/integrations/fallback-awscodecatalyst.md` |
| `googleclouddevops` | Google Cloud DevOps, GCP, Google Cloud | `Integration-GoogleCloudDevOps` | `docs/integrations/fallback-googleclouddevops.md` |

If the request names something not in this table (e.g. Linear, Notion),
say so and stop rather than guessing a page that doesn't exist — offer to
add one (edit `docs/integrations/README.md` and register a new fallback
file the same way as the eleven above).

## 2. Try the live wiki page first

Build the URL from `wiki.root_url` in `.work/config.yml` (currently
`https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki`) plus
`/<Wiki page>` from the table above. `WebFetch` it. The wiki copy is the
freshest source — per `wiki-publish/SKILL.md`, pages can be hand-edited
directly in the web UI, so it can be ahead of what's committed here.

**Verify the fetch actually returned that page before trusting it.** A
GitHub wiki does not 404 on a missing page slug — it silently redirects to
the wiki's Home page with a normal 200 response. Confirm the fetched
content contains a `## Recommended workflow` heading and looks like the
requested system's page (not the Home page's "What is this project?"
sections) before treating it as a real hit. If it doesn't match, treat
this exactly like a fetch failure (§3) — do not follow the Home page as if
it were the integration guide.

On a confirmed hit: say "Referring to the official integration guide for
`<System>`, published at `<url>`." Then follow that page's **Recommended
workflow** section exactly — do not improvise around it.

## 3. Fall back to the local copy on fetch failure

If the fetch fails outright, or succeeds but doesn't verify per §2 (network
error, 404, wrong-page redirect, wiki not yet created), read the local
fallback file instead and say so explicitly: "Wiki page unavailable — using
the bundled local copy (`<path>`), which may lag the published page." Same
instruction applies: follow its Recommended workflow section.

## 4. Soft version-staleness check

If the retrieved page states a minimum tool version, and the system has a
real, probeable CLI (`gh --version`, `glab --version`, `az --version`,
`aws --version`), run it and compare. Warn if older — never block. The
four SDD tools (Superpowers, GSD, SpecKit, OpenSpec) are Claude Code
skills, not installed binaries: there is nothing to introspect, so say
plainly that no version check applies rather than fabricating one.

## 5. Compose, don't reinvent

For Jira or Confluence specifically: before doing anything with a raw
REST call or CLI, check whether the global `jira` or `confluence` skill
(or an Atlassian MCP server) is available and use it instead — it already
owns auth, pagination, and markup conversion. The full instruction lives
in `Integration-Jira` / `Integration-Confluence` themselves (Recommended
workflow section); this is only a pointer so you don't skip straight to
raw API calls when a better tool is sitting right there.

## 6. Maintaining these pages

After editing a file under `docs/integrations/`, register it (or refresh
its ledger entry) and let the existing publish pipeline carry it, exactly
like any other opted-in doc:

    bin/worklog wiki-add docs/integrations/fallback-<key>.md --key integrations/<key> --title "Integration-<Name>"

Then run the `wiki-publish` skill as usual — its hash-compare skip logic
picks up the change on the next run. There is no separate publish path for
these files and none should be built; `wiki-add` plus the ordinary
`wiki-publish` flow is the whole mechanism (see `wiki-publish/SKILL.md`
§4). Adding a twelfth system means the same two steps: a new row in the
table above, a new fallback file, one `wiki-add` call.
