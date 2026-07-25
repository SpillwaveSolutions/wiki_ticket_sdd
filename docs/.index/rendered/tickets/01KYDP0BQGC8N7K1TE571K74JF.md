# Write the 11 fallback integration pages

`01KYDP0BQGC8N7K1TE571K74JF` · task/feature · **done**

Author one markdown guide per supported tool/system, each following the
same 10-section outline so the skill can navigate them predictably.

## Hierarchy

- epic: [[Ticket-01KYDP0BQGW4XAAGX68526C9ES]] Wiki-Driven Integration Guides for SDD tools and ticket/wiki systems — Add a new integration-guide skill plus 11 markdown wiki pages (fallback copies committed to the repo) so wiki_ticket_sdd can point users at living setup guides for Superpowers, GSD, SpecKit, OpenSpec, Jira, Confluence, GitHub, GitLab, Azure DevOps, AWS CodeCatalyst, and Google Cloud DevOps, without hard-coding any of that guidance into the shipped skill set.

## Subtasks

- [[Ticket-01KYDP0BQH6389PTNGKXHSN2KR]] fallback-speckit.md — Guide covering when and how to combine this repo's spec-driven workflow
with SpecKit. (done)
- [[Ticket-01KYDP0BQHAE38H6VPDNVXV8JA]] fallback-gsd.md — Guide covering when and how to combine this repo's spec-driven workflow
with the GSD (Get Shit Done) skill set. (done)
- [[Ticket-01KYDP0BQHANV652NZVV8N7VX5]] fallback-confluence.md — Guide for publishing docs to Confluence, honestly noting no adapter
ships yet, instructing reuse of the existing Confluence skill, and
requiring diagrams to be converted to PNG/SVG images (via the Mermaid
and PlantUML skills) before upload since Confluence can't render them
natively. (done)
- [[Ticket-01KYDP0BQHDBJ50D8HZHWN3G4H]] fallback-openspec.md — Guide covering when and how to combine this repo's spec-driven workflow
with OpenSpec. (done)
- [[Ticket-01KYDP0BQHPP0JZRK856QHN76S]] fallback-github.md — Guide for the one system with a real, shipped adapter today — GitHub
Issues plus the GitHub wiki. (done)
- [[Ticket-01KYDP0BQHRM2Q3C5727FAZ7RD]] fallback-azuredevops.md — Guide for syncing to Azure DevOps boards/wiki, honestly noting no
adapter ships yet and carrying forward the existing field-tested
caveats (tag-based markers, merge-not-overwrite updates). (done)
- [[Ticket-01KYDP0BQHV6MW1XX7H7JC1EN4]] fallback-googleclouddevops.md — Guide covering Google Cloud's lack of a native work tracker and how a
GCP-hosted team should pick a different supported system instead. (done)
- [[Ticket-01KYDP0BQHW1A3235YSF16ZZAQ]] fallback-jira.md — Guide for syncing work items to Jira, honestly noting no adapter ships
yet, and instructing the agent to reuse the existing Jira skill for any
real API calls rather than improvising raw REST calls. (done)
- [[Ticket-01KYDP0BQHXGEBEY40SC1Q4ST3]] fallback-superpowers.md — Guide covering when and how to combine this repo's spec-driven workflow
with the Superpowers skill set. (done)
- [[Ticket-01KYDP0BQHXZCGTTM5PAV262RM]] fallback-awscodecatalyst.md — Guide for syncing to AWS CodeCatalyst, honestly noting no adapter ships
yet and that the service is closed to new customers. (done)
- [[Ticket-01KYDP0BQHZHYH9CKM3D0ZM803]] fallback-gitlab.md — Guide for syncing to GitLab issues/wiki, honestly noting no adapter
ships yet and giving CLI/REST research pointers. (done)

Progress: 11/11 done

## Related tickets

- [github #163](https://github.com/SpillwaveSolutions/wiki_ticket_sdd/issues/163)
