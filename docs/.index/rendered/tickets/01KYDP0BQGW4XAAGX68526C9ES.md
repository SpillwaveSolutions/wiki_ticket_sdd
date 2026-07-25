# Wiki-Driven Integration Guides for SDD tools and ticket/wiki systems

`01KYDP0BQGW4XAAGX68526C9ES` · epic/feature · **open**

Add a new integration-guide skill plus 11 markdown wiki pages (fallback copies committed to the repo) so wiki_ticket_sdd can point users at living setup guides for Superpowers, GSD, SpecKit, OpenSpec, Jira, Confluence, GitHub, GitLab, Azure DevOps, AWS CodeCatalyst, and Google Cloud DevOps, without hard-coding any of that guidance into the shipped skill set.

## Children

- [[Ticket-01KYDP0BQG59M8QGCQY72SC0G1]] Create the integration-guide skill — Add a new Claude Code skill that recognizes when someone mentions one of 11
supported tools/systems (Superpowers, GSD, SpecKit, OpenSpec, Jira,
Confluence, GitHub, GitLab, Azure DevOps, AWS CodeCatalyst, Google Cloud
DevOps) and looks up the right integration guide before giving instructions. (open)
- [[Ticket-01KYDP0BQGC8N7K1TE571K74JF]] Write the 11 fallback integration pages — Author one markdown guide per supported tool/system, each following the
same 10-section outline so the skill can navigate them predictably. (open)
- [[Ticket-01KYDP0BQH33AMR5ETPDF4V1M6]] Register and publish the new pages — Register all 12 new files with the existing wiki-add mechanism and run a
normal wiki-publish pass to push them to the GitHub wiki, then confirm the
publish ledger recorded all 12 entries correctly. (open)
- [[Ticket-01KYDP0BQHAMP5AC6AP7854N9H]] Write the Integrations meta index page — Create a single index page listing all 11 systems with a one-sentence
description and a link to each, so someone browsing the wiki can find the
right guide without knowing the skill exists. (open)
- [[Ticket-01KYDP0BQHZAPBZPSSY38J33ZZ]] End-to-end verification — Exercise the new skill for a live-page fetch and confirm it states which
guide it's using and follows its recommended workflow, then simulate a
fetch failure and confirm it falls back to the local copy and says so. (open)

Progress: 0/5 done
