# Integrations

Living setup guides for the SDD tools and ticket/wiki systems that pair
with `wiki_ticket_sdd`. Each page follows the same 10-section template
(When to use, One-command setup, Adapter configuration, Recommended
workflow, Mapping events, Pulling changes, Rendering support, Example
links, Gotchas & troubleshooting, Last updated) so the `integration-guide`
skill can navigate them predictably. See that skill
(`.claude/skills/integration-guide/SKILL.md`) for how a page gets fetched
and how these files serve as its offline fallback.

## SDD tools

- [[Integration-Superpowers]] — pairing Superpowers' brainstorm/plan/TDD
  loop with this repo's plan-capture and tracking.
- [[Integration-GSD]] — pairing GSD's phase-based roadmap with this
  repo's roadmap and ticket sync.
- [[Integration-SpecKit]] — turning a SpecKit `tasks.md` into tracked
  work items.
- [[Integration-OpenSpec]] — turning an OpenSpec change proposal's task
  list into tracked work items.

## Ticket / wiki systems

- [[Integration-GitHub]] — the one system with a real, shipped adapter;
  issues plus the GitHub wiki.
- [[Integration-GitLab]] — issues and wiki via `glab`, no shipped adapter
  yet.
- [[Integration-Jira]] — issue sync via the existing Jira skill, no
  shipped adapter yet.
- [[Integration-Confluence]] — doc publishing via the existing Confluence
  skill, including required diagram-to-image conversion.
- [[Integration-AzureDevOps]] — Azure Boards and ADO wiki, field-tested
  tag-marker caveats, no shipped adapter yet.
- [[Integration-AWSCodeCatalyst]] — AWS CodeCatalyst issue sync; closed to
  new customers since 2025-11-07.
- [[Integration-GoogleCloudDevOps]] — GCP has no native tracker; this page
  routes you to whichever real system you're actually using.

## Adding a twelfth system

1. Add a row to the alias table in
   `.claude/skills/integration-guide/SKILL.md`.
2. Write `docs/integrations/fallback-<key>.md` using the same 10-section
   template.
3. Add a line to this index.
4. Register and publish:

       bin/worklog wiki-add docs/integrations/fallback-<key>.md --key integrations/<key> --title "Integration-<Name>"

   then run the `wiki-publish` skill as usual.

## Last updated

2026-07-25 — [edit this page](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/wiki/Integrations/_edit)
