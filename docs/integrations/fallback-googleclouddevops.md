# Integration: Google Cloud DevOps

## When to use

Your team is hosted on Google Cloud and looking for a native work tracker
or wiki equivalent to pair with `wiki_ticket_sdd`. Read this whole page
before configuring anything — the honest answer is mostly "there isn't
one."

## One-command setup

N/A — see Adapter configuration below.

## Adapter configuration

**GCP has no native work tracker, and there is no `gcp`/`codecatalyst`-style
value to configure for it** — `ticketing.system` in `.work/config.yml`
does not have a Google Cloud option, by design (confirmed in
`ticket-sync/SKILL.md`). A GCP-hosted team picks one of the systems that
does exist:

- `github` (if code already lives on GitHub) — the only system with a
  real, shipped adapter today; see `Integration-GitHub`.
- `gitlab`, `jira`, or `ado` — set `ticketing.system` accordingly and
  follow that system's own integration page.
- `other` — if you're using something not listed (e.g. a self-hosted
  tracker), set `ticketing.system: other`, name the real system in
  `options:`, and the `ticket-sync` skill researches the tooling at
  runtime, same as any other `other` value.

The nearest GCP-native building blocks — Cloud Source Repositories (a git
host) and Cloud Deploy — are infrastructure, not issue trackers; they
don't change this recommendation.

## Recommended workflow

Don't configure a `googleclouddevops`/`gcp` value — it doesn't exist and
won't be recognized. Instead:

1. Pick the real system you're actually using for issues (see above).
2. Follow that system's own `Integration-<Name>` page for setup, sync, and
   wiki behavior.
3. If genuinely nothing listed applies (a fully custom internal tracker),
   use `ticketing.system: other` and `wiki.system: other`, and expect the
   `ticket-sync`/`wiki-publish` skills to research your specific tooling
   live rather than following a pre-written runbook.

## Mapping events

Not applicable at this page's level — mapping is defined by whichever
real system you chose above; see that page.

## Pulling changes

Not applicable at this page's level — see the chosen system's own page.

## Rendering support

Ticket/PR/release pages render identically regardless of ticketing
system — nothing Google-Cloud-specific in rendering either way.

## Example links

None — there is no GCP-native system this page could point to.

## Gotchas & troubleshooting

- The most common mistake is looking for a `gcp` or `google` value in
  `ticketing.system` — it doesn't exist. Don't set an invented enum value;
  the config only validates the ones listed in `Integration-GitHub`,
  `Integration-GitLab`, `Integration-Jira`, `Integration-AzureDevOps`, or
  `other`.
- If your org later adopts a real GCP-native issue tracker, add it the
  same way any new system gets added here: a new `Integration-<Name>` page
  plus a `fallback-<key>.md` file — don't wedge it into this page.

## Last updated

2026-07-25 — [edit this page](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki/Integration-GoogleCloudDevOps/_edit)
